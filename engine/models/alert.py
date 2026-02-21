from sqlalchemy import String, DateTime, Integer, Float, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from engine.models.base import Base


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    processed_event_id: Mapped[int] = mapped_column(Integer, index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    machine_id: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    user: Mapped[str] = mapped_column(String(256), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, index=True, nullable=False)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    contributing_factors: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
