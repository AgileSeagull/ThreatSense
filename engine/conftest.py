"""Pytest configuration and fixtures for engine tests."""
import os
import pytest

# Use in-memory SQLite for tests so we don't require PostgreSQL
os.environ.setdefault("ENGINE_DATABASE_URL", "sqlite:///:memory:")
# Clear settings cache so get_settings() picks up the env
from engine.config import get_settings
get_settings.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def ensure_db_tables():
    """Ensure all DB tables exist before any test runs (for API tests using TestClient)."""
    from engine.db import init_db
    init_db()


@pytest.fixture
def db_session():
    """Create DB tables and yield a session; rollback after each test."""
    from engine.db.session import SessionLocal, init_db
    init_db()
    session = SessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()
