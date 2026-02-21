"""Hash-based PSI: check if command_hash is in threat set. No raw command on server."""
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class PSIChecker:
    """Load threat hashes from DB and optionally a file; answer membership queries."""

    def __init__(self, threat_hashes: set[str] | None = None, path: str | None = None):
        self._hashes: set[str] = set(threat_hashes or [])
        self._path = Path(path) if path else None
        if self._path and self._path.exists():
            self._load_file()

    def _load_file(self) -> None:
        try:
            for line in self._path.read_text().splitlines():
                line = line.strip()
                if line and not line.startswith("#"):
                    self._hashes.add(line)
            logger.info("Loaded %d threat hashes from %s", len(self._hashes), self._path)
        except OSError as e:
            logger.warning("Could not load threat file %s: %s", self._path, e)

    def reload_from_db(self, db_hashes: set[str]) -> None:
        """Replace in-memory set with hashes from DB (e.g. from threat_hashes table)."""
        self._hashes = set(db_hashes)
        if self._path and self._path.exists():
            self._load_file()

    def check(self, command_hash: str) -> tuple[bool, Optional[str]]:
        """
        Returns (in_threat_set, category).
        Category is None unless we extend to store category per hash (e.g. from DB).
        """
        if not command_hash:
            return False, None
        return (command_hash in self._hashes, None)
