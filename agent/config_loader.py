import os
from pathlib import Path
from typing import Any

import yaml


def load_config(config_path: str | None = None) -> dict[str, Any]:
    path = config_path or os.environ.get("AGENT_CONFIG", str(Path(__file__).parent / "config.yaml"))
    with open(path) as f:
        cfg = yaml.safe_load(f) or {}
    # Env overrides
    if url := os.environ.get("AGENT_ENDPOINT_URL"):
        cfg["endpoint_url"] = url
    if batch := os.environ.get("AGENT_BATCH_SIZE"):
        cfg["batch_size"] = int(batch)
    if interval := os.environ.get("AGENT_SEND_INTERVAL_SECONDS"):
        cfg["send_interval_seconds"] = int(interval)
    if level := os.environ.get("AGENT_LOG_LEVEL"):
        cfg["log_level"] = level
    return cfg
