"""Event schema and command hash normalization (must match engine/shared for PSI)."""
import hashlib
from datetime import datetime, timezone
from typing import Any


def normalize_command(cmd: str) -> str:
    """Normalize command string before hashing. Must match engine PSI normalization."""
    return " ".join(cmd.strip().lower().split())


def command_hash(cmd: str) -> str:
    """SHA-256 of normalized command (UTF-8)."""
    return hashlib.sha256(normalize_command(cmd).encode()).hexdigest()


def build_event(
    event_type: str,
    machine_id: str,
    user: str,
    source: str,
    payload: dict[str, Any] | None = None,
    ts: datetime | None = None,
) -> dict[str, Any]:
    t = ts or datetime.now(timezone.utc)
    return {
        "event_type": event_type,
        "machine_id": machine_id,
        "user": user,
        "timestamp": t.isoformat(),
        "source": source,
        "payload": payload or {},
    }
