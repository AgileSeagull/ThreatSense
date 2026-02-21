from sqlalchemy import String, DateTime, Integer, Float, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from engine.models.base import Base


class ProcessedEvent(Base):
    __tablename__ = "processed_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    raw_event_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    machine_id: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    user: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    source: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    risk_score: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    in_threat_set: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    contributing_factors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
