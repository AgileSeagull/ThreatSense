"""Tests for ML feature extraction."""
from datetime import datetime, timezone
import numpy as np

import pytest

from engine.ml.features import extract_features, get_feature_names, raw_event_to_dict


def test_get_feature_names():
    names = get_feature_names()
    assert len(names) == 9
    assert "hour" in names
    assert "dow" in names
    assert "source" in names
    assert "command_hash_bucket" in names


def test_extract_features_minimal():
    event = {
        "event_type": "command",
        "machine_id": "m1",
        "user": "alice",
        "timestamp": "2024-01-15T14:30:00Z",
        "source": "command",
        "payload": {},
    }
    vec = extract_features(event)
    assert vec.shape == (9,)
    assert vec.dtype == np.float64
    assert 0 <= vec[0] <= 1  # hour
    assert 0 <= vec[1] <= 1  # dow


def test_extract_features_with_payload():
    event = {
        "event_type": "command",
        "machine_id": "m1",
        "user": "bob",
        "timestamp": datetime(2024, 1, 15, 14, 30, 0, tzinfo=timezone.utc),
        "source": "process",
        "payload": {"command_hash": "abc", "exe": "/bin/bash", "command_length": 100},
    }
    vec = extract_features(event)
    assert vec.shape == (9,)
    assert 0 <= vec[8] <= 1  # command_length_norm


def test_raw_event_to_dict_from_dict():
    d = {"event_type": "auth", "machine_id": "m1", "user": "u", "timestamp": None, "source": "auth", "payload": {}}
    out = raw_event_to_dict(d)
    assert out == d


def test_raw_event_to_dict_from_object():
    class Raw:
        event_type = "command"
        machine_id = "m1"
        user = "u"
        timestamp = None
        source = "command"
        payload = {"x": 1}

    out = raw_event_to_dict(Raw())
    assert out["event_type"] == "command"
    assert out["payload"] == {"x": 1}
