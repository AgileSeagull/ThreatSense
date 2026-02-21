"""Tests for agent event schema and command hash normalization (must match engine/shared for PSI)."""
from datetime import datetime, timezone

import pytest

from agent.schema import normalize_command, command_hash, build_event


def test_normalize_command():
    assert normalize_command("  rm -rf /  ") == "rm -rf /"
    assert normalize_command("RM   -RF   /") == "rm -rf /"
    assert normalize_command("  ") == ""
    assert normalize_command("single") == "single"


def test_command_hash_deterministic():
    h1 = command_hash("rm -rf /")
    h2 = command_hash("  RM   -RF   /  ")
    assert h1 == h2
    assert len(h1) == 64
    assert all(c in "0123456789abcdef" for c in h1)


def test_command_hash_matches_shared_spec():
    # From shared/README: strip, lowercase, collapse spaces, then SHA-256
    norm = " ".join("  rm -rf /  ".strip().lower().split())
    assert norm == "rm -rf /"
    import hashlib
    expected = hashlib.sha256(norm.encode()).hexdigest()
    assert command_hash("  rm -rf /  ") == expected


def test_build_event():
    ev = build_event(
        event_type="command",
        machine_id="m1",
        user="alice",
        source="command",
        payload={"command_hash": "abc"},
    )
    assert ev["event_type"] == "command"
    assert ev["machine_id"] == "m1"
    assert ev["user"] == "alice"
    assert ev["source"] == "command"
    assert ev["payload"] == {"command_hash": "abc"}
    assert "timestamp" in ev
    # timestamp is ISO format
    datetime.fromisoformat(ev["timestamp"].replace("Z", "+00:00"))


def test_build_event_with_explicit_timestamp():
    ts = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    ev = build_event(
        event_type="auth",
        machine_id="m2",
        user="bob",
        source="auth",
        ts=ts,
    )
    assert ev["timestamp"] == ts.isoformat()
