"""In-memory queue with optional file persistence for events."""
import json
import logging
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)


class EventBuffer:
    def __init__(self, persist_path: str | None = None, max_size: int = 10_000):
        self._queue: list[dict] = []
        self._max_size = max_size
        self._persist_path = Path(persist_path) if persist_path else None
        if self._persist_path:
            self._load()

    def _load(self) -> None:
        if not self._persist_path or not self._persist_path.exists():
            return
        try:
            with open(self._persist_path) as f:
                for line in f:
                    line = line.strip()
                    if line:
                        self._queue.append(json.loads(line))
            if self._queue:
                logger.info("Loaded %d events from persistence", len(self._queue))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Could not load persisted events: %s", e)

    def push(self, event: dict) -> None:
        if len(self._queue) >= self._max_size:
            self._queue.pop(0)
        self._queue.append(event)
        if self._persist_path:
            try:
                with open(self._persist_path, "a") as f:
                    f.write(json.dumps(event) + "\n")
            except OSError as e:
                logger.warning("Could not persist event: %s", e)

    def push_many(self, events: list[dict]) -> None:
        for e in events:
            self.push(e)

    def pop_batch(self, size: int) -> list[dict]:
        batch = self._queue[:size]
        self._queue = self._queue[size:]
        if self._persist_path and self._persist_path.exists():
            self._rewrite_persist()
        return batch

    def _rewrite_persist(self) -> None:
        try:
            with open(self._persist_path, "w") as f:
                for e in self._queue:
                    f.write(json.dumps(e) + "\n")
        except OSError as e:
            logger.warning("Could not rewrite persistence: %s", e)

    def __len__(self) -> int:
        return len(self._queue)
