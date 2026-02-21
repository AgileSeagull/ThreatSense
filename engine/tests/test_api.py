"""Tests for engine API endpoints."""
from datetime import datetime, timezone

from fastapi.testclient import TestClient

from engine.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "Threat Detection Engine"
    assert "docs" in data
    assert "health" in data


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_events_ingest_empty():
    """Ingest empty list is accepted."""
    r = client.post("/api/v1/events", json=[])
    assert r.status_code == 200
    assert r.json()["accepted"] == 0
    assert r.json()["rejected"] == 0


def test_events_ingest_valid():
    """Ingest one valid event."""
    events = [
        {
            "event_type": "command",
            "machine_id": "test-machine",
            "user": "testuser",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "command",
            "payload": {"command_hash": "a" * 64, "command_length": 10},
        }
    ]
    r = client.post("/api/v1/events", json=events)
    assert r.status_code == 200
    data = r.json()
    assert data["accepted"] == 1
    assert data["rejected"] == 0


def test_events_ingest_invalid_rejected():
    """Invalid event (bad event_type) is rejected."""
    events = [
        {
            "event_type": "invalid_type",
            "machine_id": "m",
            "user": "u",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "command",
            "payload": {},
        }
    ]
    r = client.post("/api/v1/events", json=events)
    assert r.status_code == 422  # validation error


def test_events_ingest_mixed():
    """Two valid events in same batch."""
    events = [
        {
            "event_type": "auth",
            "machine_id": "m",
            "user": "u",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "auth",
            "payload": {},
        },
        {
            "event_type": "process",
            "machine_id": "m2",
            "user": "u2",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "process",
            "payload": {"exe": "/bin/bash"},
        },
    ]
    r = client.post("/api/v1/events", json=events)
    assert r.status_code == 200
    assert r.json()["accepted"] == 2
