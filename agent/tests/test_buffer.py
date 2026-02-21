"""Tests for agent event buffer."""
import json
import tempfile
from pathlib import Path

import pytest

from agent.buffer import EventBuffer


def test_buffer_push_pop():
    buf = EventBuffer()
    assert len(buf) == 0
    buf.push({"a": 1})
    buf.push({"b": 2})
    assert len(buf) == 2
    batch = buf.pop_batch(1)
    assert batch == [{"a": 1}]
    assert len(buf) == 1
    batch = buf.pop_batch(10)
    assert batch == [{"b": 2}]
    assert len(buf) == 0


def test_buffer_push_many():
    buf = EventBuffer()
    buf.push_many([{"id": 1}, {"id": 2}, {"id": 3}])
    assert len(buf) == 3
    batch = buf.pop_batch(2)
    assert len(batch) == 2
    assert batch[0]["id"] == 1
    assert batch[1]["id"] == 2
    assert len(buf) == 1


def test_buffer_max_size():
    buf = EventBuffer(max_size=3)
    buf.push({"n": 1})
    buf.push({"n": 2})
    buf.push({"n": 3})
    buf.push({"n": 4})  # should drop first
    assert len(buf) == 3
    batch = buf.pop_batch(3)
    assert [b["n"] for b in batch] == [2, 3, 4]


def test_buffer_persist_load():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as f:
        path = f.name
    try:
        buf = EventBuffer(persist_path=path)
        buf.push({"x": 1})
        buf.push({"x": 2})
        # New buffer loads from file
        buf2 = EventBuffer(persist_path=path)
        assert len(buf2) == 2
        batch = buf2.pop_batch(2)
        assert batch[0]["x"] == 1
        assert batch[1]["x"] == 2
    finally:
        Path(path).unlink(missing_ok=True)
