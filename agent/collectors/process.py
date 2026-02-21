"""Collect process execution events via psutil."""
from datetime import datetime, timezone
from typing import Iterator

import psutil

from agent.collectors.base import BaseCollector
from agent.schema import build_event


class ProcessCollector(BaseCollector):
    def __init__(self, sample_limit: int = 50):
        self.sample_limit = sample_limit

    def collect(self, machine_id: str) -> Iterator[dict]:
        try:
            procs = list(psutil.process_iter(["pid", "username", "name", "exe", "cmdline", "create_time", "ppid"]))
        except (psutil.Error, AttributeError):
            return
        count = 0
        for p in procs:
            if count >= self.sample_limit:
                break
            try:
                info = p.info
                username = info.get("username") or "unknown"
                exe = info.get("exe") or info.get("name") or ""
                cmdline = info.get("cmdline") or []
                argv = cmdline if isinstance(cmdline, list) else [str(cmdline)]
                create_time = info.get("create_time")
                ts = datetime.fromtimestamp(create_time, tz=timezone.utc) if create_time else datetime.now(timezone.utc)
                yield build_event("process", machine_id, username, "process", {
                    "pid": info.get("pid"),
                    "exe": exe,
                    "argv": argv[:20],
                    "parent_pid": info.get("ppid"),
                    "start_time": create_time,
                }, ts)
                count += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied, KeyError):
                continue
