from abc import ABC, abstractmethod
from typing import Iterator


class BaseCollector(ABC):
    """Base class for activity collectors."""

    @abstractmethod
    def collect(self, machine_id: str) -> Iterator[dict]:
        """Yield events (dicts matching shared event schema). machine_id is passed in."""
        pass
