"""Tests for engine config."""
import os
import pytest


def test_get_settings_defaults():
    from engine.config import get_settings
    get_settings.cache_clear()
    try:
        # Remove so we get default
        os.environ.pop("ENGINE_DATABASE_URL", None)
        s = get_settings()
        assert "postgresql" in s.database_url or "sqlite" in s.database_url
        assert s.alert_threshold == 50.0
        assert s.log_level == "INFO"
    finally:
        get_settings.cache_clear()
        os.environ.setdefault("ENGINE_DATABASE_URL", "sqlite:///:memory:")


def test_settings_env_prefix():
    from engine.config import get_settings
    get_settings.cache_clear()
    try:
        os.environ["ENGINE_ALERT_THRESHOLD"] = "75"
        s = get_settings()
        assert s.alert_threshold == 75.0
    finally:
        os.environ.pop("ENGINE_ALERT_THRESHOLD", None)
        get_settings.cache_clear()
        os.environ.setdefault("ENGINE_DATABASE_URL", "sqlite:///:memory:")
