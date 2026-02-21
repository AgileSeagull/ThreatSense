"""Dashboard aggregation endpoints for stats and chart data."""
from datetime import datetime, timedelta, timezone
from collections import defaultdict

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from engine.api.auth import require_api_key
from engine.db.session import get_db_session
from engine.models.alert import Alert
from engine.models.processed_event import ProcessedEvent

router = APIRouter(prefix="/dashboard", tags=["dashboard"], dependencies=[Depends(require_api_key)])


def _level_from_risk(risk_score: float) -> int:
    """Map risk_score 0-100 to level 1-12."""
    return min(12, max(1, round(risk_score / (100 / 12))))


def _apply_date_filter(q, col, since, until):
    if since is not None:
        q = q.filter(col >= since)
    if until is not None:
        q = q.filter(col <= until)
    return q


@router.get("/stats")
def get_stats(
    db: Session = Depends(get_db_session),
    since: datetime | None = None,
    until: datetime | None = None,
):
    """KPIs: total events, total alerts, critical alerts, auth failure/success."""
    total = db.query(func.count(ProcessedEvent.id)).scalar() or 0

    alerts_q = _apply_date_filter(db.query(Alert), Alert.timestamp, since, until)
    all_alerts = alerts_q.all()
    total_alerts = len(all_alerts)
    level_12_plus = sum(1 for a in all_alerts if _level_from_risk(a.risk_score) >= 12)

    auth_q = db.query(ProcessedEvent).filter(ProcessedEvent.event_type == "auth")
    auth_q = _apply_date_filter(auth_q, ProcessedEvent.timestamp, since, until)
    auth_events = auth_q.all()
    auth_success = sum(1 for e in auth_events if e.payload and e.payload.get("success") is True)
    auth_failure = sum(1 for e in auth_events if e.payload and e.payload.get("success") is False)
    auth_failure += len(auth_events) - auth_success - auth_failure

    return {
        "total": total,
        "total_alerts": total_alerts,
        "level_12_plus_alerts": level_12_plus,
        "authentication_failure": auth_failure,
        "authentication_success": auth_success,
    }


@router.get("/alerts-over-time")
def get_alerts_over_time(
    db: Session = Depends(get_db_session),
    since: datetime | None = None,
    until: datetime | None = None,
    interval_minutes: int = Query(60, ge=5, le=1440),
):
    """Alert counts bucketed by time for area chart."""
    q = db.query(Alert.timestamp, Alert.risk_score).order_by(Alert.timestamp)
    q = _apply_date_filter(q, Alert.timestamp, since, until)
    rows = q.all()

    bucket_seconds = interval_minutes * 60
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for ts, risk in rows:
        bucket_ts = ts.replace(microsecond=0)
        if interval_minutes >= 60:
            bucket_ts = bucket_ts.replace(minute=0, second=0)
            if interval_minutes >= 1440:
                bucket_ts = bucket_ts.replace(hour=0)
        else:
            sec = bucket_ts.hour * 3600 + bucket_ts.minute * 60 + bucket_ts.second
            sec = (sec // bucket_seconds) * bucket_seconds
            bucket_ts = bucket_ts.replace(hour=sec // 3600, minute=(sec % 3600) // 60, second=sec % 60)
        key = bucket_ts.isoformat()
        level = min(12, max(3, _level_from_risk(risk)))
        buckets[key][f"level_{level}"] += 1

    series = [{"period": k, **buckets[k]} for k in sorted(buckets.keys())]
    return {"interval_minutes": interval_minutes, "series": series}


@router.get("/alerts-by-technique")
def get_alerts_by_technique(
    db: Session = Depends(get_db_session),
    since: datetime | None = None,
    until: datetime | None = None,
):
    """Alert counts by event type for pie chart."""
    q = db.query(Alert.event_type, func.count(Alert.id))
    q = _apply_date_filter(q, Alert.timestamp, since, until)
    rows = q.group_by(Alert.event_type).all()

    labels = {"auth": "Authentication", "command": "Command execution", "process": "Process execution"}
    return {"series": [{"name": labels.get(et, et), "value": count} for et, count in rows]}


@router.get("/top-agents")
def get_top_agents(
    db: Session = Depends(get_db_session),
    since: datetime | None = None,
    until: datetime | None = None,
    top_n: int = Query(5, ge=1, le=20),
):
    """Top N agents (machine_id) by alert count."""
    q = db.query(Alert.machine_id, func.count(Alert.id))
    q = _apply_date_filter(q, Alert.timestamp, since, until)
    rows = q.group_by(Alert.machine_id).order_by(desc(func.count(Alert.id))).limit(top_n).all()

    series = [{"name": mid, "value": count, "machine_id": mid} for mid, count in rows]
    return {"series": series, "machine_ids": [r[0] for r in rows]}


@router.get("/alerts-evolution-by-agent")
def get_alerts_evolution_by_agent(
    db: Session = Depends(get_db_session),
    since: datetime | None = None,
    until: datetime | None = None,
    interval_minutes: int = Query(30, ge=5, le=1440),
    top_n: int = Query(5, ge=1, le=20),
):
    """Time-bucketed alert counts per top agent."""
    top_q = db.query(Alert.machine_id, func.count(Alert.id))
    top_q = _apply_date_filter(top_q, Alert.timestamp, since, until)
    top_rows = top_q.group_by(Alert.machine_id).order_by(desc(func.count(Alert.id))).limit(top_n).all()
    top_ids = {r[0] for r in top_rows}

    if not top_ids:
        return {"interval_minutes": interval_minutes, "series": []}

    q = db.query(Alert.timestamp, Alert.machine_id).filter(Alert.machine_id.in_(top_ids))
    q = _apply_date_filter(q, Alert.timestamp, since, until)
    rows = q.all()

    bucket_seconds = interval_minutes * 60
    buckets: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for ts, machine_id in rows:
        bucket_ts = ts.replace(microsecond=0)
        if interval_minutes >= 60:
            bucket_ts = bucket_ts.replace(minute=0, second=0)
            if interval_minutes >= 1440:
                bucket_ts = bucket_ts.replace(hour=0)
        else:
            sec = bucket_ts.hour * 3600 + bucket_ts.minute * 60 + bucket_ts.second
            sec = (sec // bucket_seconds) * bucket_seconds
            bucket_ts = bucket_ts.replace(hour=sec // 3600, minute=(sec % 3600) // 60, second=sec % 60)
        buckets[bucket_ts.isoformat()][machine_id] += 1

    series = [{"period": k, **buckets[k]} for k in sorted(buckets.keys())]
    return {"interval_minutes": interval_minutes, "series": series}
