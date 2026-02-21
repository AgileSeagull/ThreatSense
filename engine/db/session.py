from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager

from engine.config import get_settings
from engine.models.base import Base
# Import all models so Base.metadata includes every table (for create_all)
import engine.models  # noqa: F401


def get_engine():
    settings = get_settings()
    url = settings.database_url
    # SQLite :memory: needs a single connection so all sessions see the same DB
    if url and "sqlite" in url and ":memory:" in url:
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False,
        )
    return create_engine(
        url,
        pool_pre_ping=True,
        echo=False,
    )


engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session():
    """FastAPI dependency: yield session and close (caller commits)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
