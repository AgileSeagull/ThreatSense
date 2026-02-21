from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime

from engine.api.schemas import AlertOut
from engine.api.auth import require_api_key
from engine.db.session import get_db_session
from engine.models.alert import Alert

router = APIRouter(prefix="/alerts", tags=["alerts"], dependencies=[Depends(require_api_key)])


@router.get("", response_model=list[AlertOut])
def list_alerts(
    db: Session = Depends(get_db_session),
    machine_id: str | None = None,
    user: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
    risk_min: float | None = None,
    limit: int = Query(50, ge=1, le=500),
):
    """List alerts with optional filters. Returns processed high-risk events."""
    q = db.query(Alert).order_by(desc(Alert.created_at))
    if machine_id:
        q = q.filter(Alert.machine_id == machine_id)
    if user:
        q = q.filter(Alert.user == user)
    if since:
        q = q.filter(Alert.timestamp >= since)
    if until:
        q = q.filter(Alert.timestamp <= until)
    if risk_min is not None:
        q = q.filter(Alert.risk_score >= risk_min)
    rows = q.limit(limit).all()
    return [AlertOut.model_validate(r) for r in rows]
