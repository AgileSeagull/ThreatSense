"""Tests for PSI (threat hash) checker."""
import tempfile
from pathlib import Path

import pytest

from engine.psi import PSIChecker


def test_psi_checker_empty():
    psi = PSIChecker()
    assert psi.check("") == (False, None)
    assert psi.check("abc123") == (False, None)


def test_psi_checker_with_hashes():
    hashes = {"deadbeef", "cafe1234"}
    psi = PSIChecker(threat_hashes=hashes)
    assert psi.check("deadbeef") == (True, None)
    assert psi.check("cafe1234") == (True, None)
    assert psi.check("unknown") == (False, None)


def test_psi_checker_load_file():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("hash1\n")
        f.write("hash2\n")
        f.write("# comment\n")
        f.write("  \n")
        path = f.name
    try:
        psi = PSIChecker(path=path)
        assert psi.check("hash1") == (True, None)
        assert psi.check("hash2") == (True, None)
        assert psi.check("other") == (False, None)
    finally:
        Path(path).unlink(missing_ok=True)


def test_psi_checker_reload_from_db():
    psi = PSIChecker(threat_hashes={"old"})
    assert psi.check("old") == (True, None)
    psi.reload_from_db({"new1", "new2"})
    assert psi.check("old") == (False, None)
    assert psi.check("new1") == (True, None)
    assert psi.check("new2") == (True, None)
