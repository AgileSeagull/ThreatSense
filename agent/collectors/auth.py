"""Collect auth events from journalctl or /var/log/auth.log."""
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from agent.collectors.base import BaseCollector
from agent.schema import build_event

# Common auth log patterns (Debian/Ubuntu style)
AUTH_PATTERNS = [
    (re.compile(r"(\w{3}\s+\d+\s+[\d:]+).*Accepted (?:password|publickey) for (\w+) from ([\d.]+)"), "login"),
    (re.compile(r"(\w{3}\s+\d+\s+[\d:]+).*session opened for user (\w+)"), "login"),
    (re.compile(r"(\w{3}\s+\d+\s+[\d:]+).*session closed for user (\w+)"), "logout"),
    (re.compile(r"(\w{3}\s+\d+\s+[\d:]+).*(\w+) :.*SUCCESS.*TTY"), "sudo"),
    (re.compile(r"(\w{3}\s+\d+\s+[\d:]+).*Failed password for (\w+)"), "failure"),
]


def _parse_syslog_date(s: str, year: int | None = None) -> datetime:
    """Parse 'Mon DD HH:MM:SS' into datetime (assume current year if not given)."""
    from datetime import datetime as dt
    try:
        # e.g. "Jan  5 12:34:56"
        parts = s.split()
        if len(parts) < 3:
            return datetime.now(timezone.utc)
        month_str, day_str, time_str = parts[0], parts[1], parts[2]
        y = year or datetime.now().year
        t = dt.strptime(f"{y} {month_str} {day_str} {time_str}", "%Y %b %d %H:%M:%S")
        return t.replace(tzinfo=timezone.utc)
    except Exception:
        return datetime.now(timezone.utc)


class AuthCollector(BaseCollector):
    def __init__(self, use_journal: bool = True, log_path: str = "/var/log/auth.log"):
        self.use_journal = use_journal
        self.log_path = Path(log_path)
        self._last_line_count = 0

    def collect(self, machine_id: str) -> Iterator[dict]:
        if self.use_journal:
            yield from self._from_journal(machine_id)
        elif self.log_path.exists():
            yield from self._from_file(machine_id)

    def _from_journal(self, machine_id: str) -> Iterator[dict]:
        try:
            out = subprocess.run(
                ["journalctl", "-u", "sshd", "--no-pager", "-n", "100", "-o", "short-iso"],
                capture_output=True,
                text=True,
                timeout=10,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return
        if out.returncode != 0:
            return
        for line in out.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            # Format: "2024-01-05T12:34:56+00:00 hostname ..."
            parts = line.split(None, 2)
            if len(parts) < 3:
                continue
            ts_str, _host, msg = parts[0], parts[1], parts[2]
            try:
                ts = datetime.fromisoformat(ts_str.replace("+00:00", "").replace("Z", "+00:00"))
                if ts.tzinfo is None:
                    ts = ts.replace(tzinfo=timezone.utc)
            except Exception:
                ts = datetime.now(timezone.utc)
            user = "unknown"
            action = "login"
            if "Accepted" in msg or "session opened" in msg:
                for m in re.finditer(r"for (\w+)|user (\w+)", msg):
                    user = m.group(1) or m.group(2)
                    break
            elif "session closed" in msg:
                action = "logout"
                for m in re.finditer(r"user (\w+)", msg):
                    user = m.group(1)
                    break
            elif "Failed password" in msg:
                action = "failure"
                for m in re.finditer(r"for (\w+)", msg):
                    user = m.group(1)
                    break
            yield build_event("auth", machine_id, user, "auth", {
                "action": action,
                "service": "sshd",
                "success": action != "failure",
            }, ts)

    def _from_file(self, machine_id: str) -> Iterator[dict]:
        try:
            lines = self.log_path.read_text().splitlines()
        except (OSError, IOError):
            return
        # Only new lines (simple tail; in production use inotify or remember offset)
        start = max(0, len(lines) - 100)
        for line in lines[start:]:
            for pat, action in AUTH_PATTERNS:
                m = pat.search(line)
                if m:
                    date_str = m.group(1)
                    user = m.group(2) if m.lastindex >= 2 else "unknown"
                    ts = _parse_syslog_date(date_str)
                    yield build_event("auth", machine_id, user, "auth", {
                        "action": action,
                        "service": "sshd",
                        "success": action != "failure",
                    }, ts)
                    break
