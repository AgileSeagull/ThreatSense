"""Tests for XAI explainer."""
import pytest

from engine.xai import explain


def test_explain_threat_set():
    text = explain(100.0, in_threat_set=True, contributing_factors=[], event_source="command")
    assert "known malicious" in text or "threat" in text.lower()


def test_explain_high_risk():
    text = explain(85.0, in_threat_set=False, contributing_factors=["factor1"], event_source="command")
    assert "Unusual" in text or "anomaly" in text.lower()
    assert "factor1" in text or "factor" in text.lower()


def test_explain_moderate_risk():
    text = explain(55.0, in_threat_set=False, contributing_factors=[], event_source="auth")
    assert "Moderately" in text or "unusual" in text.lower()


def test_explain_low_risk():
    text = explain(25.0, in_threat_set=False, contributing_factors=[], event_source="process")
    assert "Slight" in text or "deviation" in text.lower()


def test_explain_normal():
    text = explain(5.0, in_threat_set=False, contributing_factors=[], event_source="command")
    assert "normal" in text.lower()
