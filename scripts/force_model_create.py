#!/usr/bin/env python3
"""
Force creation of the persisted global anomaly model (data/models/global_model.joblib).
Sends enough benign events to the engine so it fits the Isolation Forest and saves it to disk.
Requires: engine running, ENGINE_URL (default http://localhost:8000), optional ENGINE_API_KEY.
Usage: python scripts/force_model_create.py
"""
import os
import random
import sys
import time
from datetime import datetime, timezone
from hashlib import sha256

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

ENGINE_URL = os.environ.get("ENGINE_URL", "http://localhost:8000")
API_KEY = os.environ.get("ENGINE_API_KEY", "")
EVENTS_ENDPOINT = f"{ENGINE_URL.rstrip('/')}/api/v1/events"

# Need at least 30 events for fit_global(); send 45 so we're safely over.
NUM_EVENTS = 45


def random_hex_hash() -> str:
    return sha256(f"{random.random()}{time.time()}".encode()).hexdigest()


def build_event(machine_id: str, user: str, source: str, payload: dict) -> dict:
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    return {
        "event_type": source,
        "machine_id": machine_id,
        "user": user,
        "timestamp": now,
        "source": source,
        "payload": payload,
    }


def generate_benign_events(n: int) -> list[dict]:
    """Generate n events with only benign command hashes (no threat DB matches)."""
    machines = ["force-model-host-01", "force-model-host-02"]
    users = ["alice", "bob", "deploy", "ops"]
    events = []
    for i in range(n):
        machine_id = random.choice(machines)
        user = random.choice(users)
        kind = random.choice(["auth", "command", "process"])
        if kind == "auth":
            payload = {
                "action": random.choice(["login", "login", "failure"]),
                "service": "sshd",
                "success": random.random() > 0.3,
            }
        elif kind == "command":
            payload = {
                "command_hash": random_hex_hash(),
                "command_length": random.randint(5, 200),
            }
        else:
            payload = {
                "pid": 1000 + i,
                "exe": random.choice(["/usr/bin/bash", "/usr/bin/python3", "/usr/bin/git"]),
                "argv": ["cmd"],
                "parent_pid": 1,
                "start_time": time.time() - random.randint(0, 86400),
            }
        events.append(build_event(machine_id, user, kind, payload))
    return events


def main() -> int:
    print(f"Sending {NUM_EVENTS} benign events to {EVENTS_ENDPOINT} to force model fit and save...")
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    events = generate_benign_events(NUM_EVENTS)
    try:
        r = requests.post(EVENTS_ENDPOINT, json=events, headers=headers, timeout=30)
        r.raise_for_status()
        data = r.json()
        accepted = getattr(data, "accepted", data.get("accepted", 0))
        print(f"Accepted {accepted} events.")
        print("If the engine had at least 30 raw events (including these), it should have fitted and saved the model to data/models/global_model.joblib")
        return 0
    except requests.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
        if hasattr(e, "response") and e.response is not None:
            print(e.response.text[:500], file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
