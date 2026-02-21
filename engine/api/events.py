from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from engine.api.schemas import EventIn, EventsIngestResponse
from engine.db.session import get_db_session
from engine.models.raw_event import RawEvent
from engine.api.auth import require_api_key
from engine.pipeline import get_psi_checker, process_raw_event

router = APIRouter(prefix="/events", tags=["events"], dependencies=[Depends(require_api_key)])


@router.post("", response_model=EventsIngestResponse)
def ingest_events(events: list[EventIn], db: Session = Depends(get_db_session)):
    """Accept a batch of activity events. Store raw events, run PSI, write processed_events and alerts."""
    accepted = 0
    rejected = 0
    now = datetime.now(timezone.utc)
    psi = get_psi_checker(db)
    for ev in events:
        try:
            raw = RawEvent(
                event_type=ev.event_type,
                machine_id=ev.machine_id,
                user=ev.user,
                timestamp=ev.timestamp,
                source=ev.source,
                payload=ev.payload,
                received_at=now,
            )
            db.add(raw)
            db.flush()
            process_raw_event(db, raw, psi)
            accepted += 1
        except Exception:
            rejected += 1
    db.commit()
    return EventsIngestResponse(
        accepted=accepted,
        rejected=rejected,
        message=f"Accepted {accepted}, rejected {rejected}",
    )


@router.get("")
def list_events(db: Session = Depends(get_db_session), limit: int = 50):
    """List recent raw events. Prefer /activity for processed data with risk scores."""
    from engine.models.raw_event import RawEvent
    from sqlalchemy import desc
    rows = db.query(RawEvent).order_by(desc(RawEvent.received_at)).limit(limit).all()
    return {
        "events": [
            {
                "id": r.id,
                "event_type": r.event_type,
                "machine_id": r.machine_id,
                "user": r.user,
                "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                "source": r.source,
            }
            for r in rows
        ],
        "limit": limit,
    }
