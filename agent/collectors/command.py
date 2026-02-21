"""Collect command events from shell history (hash-only for PSI)."""
import glob
from pathlib import Path
from typing import Iterator

from agent.collectors.base import BaseCollector
from agent.schema import build_event, command_hash
from datetime import datetime, timezone


class CommandCollector(BaseCollector):
    def __init__(self, history_glob: str = "/home/*/.bash_history"):
        self.history_glob = history_glob
        self._seen: set[tuple[str, str, str]] = set()  # (machine_id, user, hash)

    def collect(self, machine_id: str) -> Iterator[dict]:
        for path in glob.glob(self.history_glob):
            try:
                user = Path(path).parent.name
                if user == "home" or not user:
                    continue
                lines = Path(path).read_text(errors="ignore").splitlines()
            except (OSError, IOError):
                continue
            # Last N lines to avoid re-sending same commands every run
            for line in lines[-200:]:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                h = command_hash(line)
                key = (machine_id, user, h)
                if key in self._seen:
                    continue
                self._seen.add(key)
                if len(self._seen) > 10000:
                    self._seen.clear()
                yield build_event("command", machine_id, user, "command", {
                    "command_hash": h,
                    "command_length": len(line),
                }, datetime.now(timezone.utc))
