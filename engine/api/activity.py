from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from engine.api.schemas import ProcessedEventOut
from engine.api.auth import require_api_key
from engine.db.session import get_db_session
from engine.models.processed_event import ProcessedEvent

router = APIRouter(prefix="/activity", tags=["activity"], dependencies=[Depends(require_api_key)])


@router.get("", response_model=list[ProcessedEventOut])
def list_activity(
    db: Session = Depends(get_db_session),
    machine_id: str | None = None,
    user: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    risk_min: float | None = None,
    event_type: str | None = None,
    limit: int = Query(100, ge=1, le=1000),
):
    """Timeline of processed events (activity) with optional filters."""
    q = db.query(ProcessedEvent).order_by(desc(ProcessedEvent.timestamp))
    if machine_id:
        q = q.filter(ProcessedEvent.machine_id == machine_id)
    if user:
        q = q.filter(ProcessedEvent.user == user)
    if since:
        q = q.filter(ProcessedEvent.timestamp >= since)
    if until:
        q = q.filter(ProcessedEvent.timestamp <= until)
    if risk_min is not None:
        q = q.filter(ProcessedEvent.risk_score >= risk_min)
    if event_type:
        q = q.filter(ProcessedEvent.event_type == event_type)
    rows = q.limit(limit).all()
    return [ProcessedEventOut.model_validate(r) for r in rows]
