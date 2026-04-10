#!/usr/bin/env python3
"""
Retrain the global anomaly model (data/models/global_model.joblib) on clean normal data.

The Isolation Forest learns what "normal" looks like from its training data.
This script sends a large batch of purely normal events — matching the same
templates used by demo_agents.py — so the model learns the correct baseline.
After this runs, normal events score near 0 and real threats score high.

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

# Send enough events so the Isolation Forest gets a solid normal baseline.
# More samples = tighter boundary = clearer separation between normal and threat.
NUM_EVENTS = 200
BATCH_SIZE = 50  # send in batches to avoid timeout

# ── Normal templates (must stay in sync with demo_agents.py NORMAL_* pools) ──

NORMAL_AUTH = [
    {"action": "login",  "service": "sshd",  "success": True},
    {"action": "login",  "service": "sudo",  "success": True},
    {"action": "login",  "service": "pam",   "success": True},
    {"action": "logout", "service": "sshd",  "success": True},
    {"action": "logout", "service": "sudo",  "success": True},
    {"action": "logout", "service": "pam",   "success": True},
]

# Short lengths keep cmd_len feature (÷500) near 0
NORMAL_COMMAND_LENGTHS = [5, 8, 12, 18, 25, 30]

NORMAL_PROCESS_EXES = [
    ("/usr/bin/bash",    ["bash"]),
    ("/usr/bin/python3", ["python3", "-m", "agent.main"]),
    ("/usr/bin/git",     ["git", "pull"]),
    ("/usr/bin/ls",      ["ls", "-la"]),
    ("/usr/bin/curl",    ["curl", "https://example.com"]),
    ("/usr/bin/systemd", ["systemd", "--user"]),
    ("/usr/bin/vim",     ["vim", "config.yaml"]),
    ("/usr/bin/ssh",     ["ssh", "deploy@prod"]),
]

MACHINES = ["demo-laptop-01", "demo-server-02", "demo-workstation-03",
            "train-host-01", "train-host-02"]
USERS = ["alice", "bob", "ops", "deploy", "root", "monitor", "jordan", "marcus", "dev"]


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


def generate_normal_events(n: int) -> list[dict]:
    """Generate n purely normal events matching the demo_agents NORMAL_* templates."""
    events = []
    for i in range(n):
        machine_id = random.choice(MACHINES)
        user = random.choice(USERS)
        kind = random.choice(["auth", "command", "process"])

        if kind == "auth":
            pl = dict(random.choice(NORMAL_AUTH))

        elif kind == "command":
            pl = {
                "command_hash": random_hex_hash(),
                "command_length": random.choice(NORMAL_COMMAND_LENGTHS),
            }

        else:
            exe, argv = random.choice(NORMAL_PROCESS_EXES)
            pl = {
                "pid": 1000 + i,
                "exe": exe,
                "argv": argv,
                "parent_pid": random.choice([1, 1000]),
                "start_time": time.time() - random.randint(0, 3600),
            }

        events.append(build_event(machine_id, user, kind, pl))
    return events


def main() -> int:
    print(f"Retraining anomaly model on {NUM_EVENTS} normal events → {EVENTS_ENDPOINT}")
    print("This teaches the Isolation Forest what normal looks like so threats stand out.\n")

    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"

    all_events = generate_normal_events(NUM_EVENTS)
    total_accepted = 0

    for start in range(0, len(all_events), BATCH_SIZE):
        batch = all_events[start:start + BATCH_SIZE]
        try:
            r = requests.post(EVENTS_ENDPOINT, json=batch, headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json()
            accepted = data.get("accepted", len(batch))
            total_accepted += accepted
            print(f"  Batch {start // BATCH_SIZE + 1}: sent {len(batch)}, accepted {accepted}")
        except requests.RequestException as e:
            print(f"  Batch failed: {e}", file=sys.stderr)
            return 1

    print(f"\nTotal accepted: {total_accepted} / {NUM_EVENTS}")
    print("Model retrained. Normal events should now score near 0; threats will score high.")
    print("Saved to: data/models/global_model.joblib")
    return 0


if __name__ == "__main__":
    sys.exit(main())
