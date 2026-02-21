"""Feature extraction for anomaly detection. Same schema for training and inference."""
import hashlib
import numpy as np
from datetime import datetime
from typing import Any


def _hash_bucket(s: str, n: int = 1000) -> int:
    return int(hashlib.sha256(s.encode()).hexdigest(), 16) % n


def extract_features(event: dict[str, Any], payload: dict | None = None) -> np.ndarray:
    """
    Build a fixed-size feature vector from an event.
    Returns 1d array: [hour, dow, command_hash_bucket, process_name_bucket, auth_action_bucket, ...]
    """
    payload = payload or event.get("payload") or {}
    ts = event.get("timestamp")
    if isinstance(ts, str):
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            dt = datetime.utcnow()
    elif hasattr(ts, "hour"):
        dt = ts
    else:
        dt = datetime.utcnow()
    hour = dt.hour / 24.0
    dow = dt.weekday() / 7.0
    source = event.get("source", "")
    source_enc = {"auth": 0.0, "command": 0.33, "process": 0.66}.get(source, 0.5)
    cmd_hash_bucket = _hash_bucket(payload.get("command_hash") or "none", 500) / 500.0
    exe_bucket = _hash_bucket(payload.get("exe") or "none", 200) / 200.0
    action_bucket = _hash_bucket(str(payload.get("action", "none")), 20) / 20.0
    user_bucket = _hash_bucket(event.get("user", "unknown"), 100) / 100.0
    machine_bucket = _hash_bucket(event.get("machine_id", "unknown"), 50) / 50.0
    cmd_len = min((payload.get("command_length") or 0) / 500.0, 1.0)
    return np.array([
        hour, dow, source_enc, cmd_hash_bucket, exe_bucket,
        action_bucket, user_bucket, machine_bucket, cmd_len,
    ], dtype=np.float64)


def get_feature_names() -> list[str]:
    return [
        "hour", "dow", "source", "command_hash_bucket", "exe_bucket",
        "auth_action_bucket", "user_bucket", "machine_bucket", "command_length_norm",
    ]


def raw_event_to_dict(raw: Any) -> dict:
    """Convert RawEvent OR dict to event dict for feature extraction."""
    if hasattr(raw, "event_type"):
        return {
            "event_type": getattr(raw, "event_type", ""),
            "machine_id": getattr(raw, "machine_id", ""),
            "user": getattr(raw, "user", ""),
            "timestamp": getattr(raw, "timestamp", None),
            "source": getattr(raw, "source", ""),
            "payload": getattr(raw, "payload") or {},
        }
    return dict(raw)
