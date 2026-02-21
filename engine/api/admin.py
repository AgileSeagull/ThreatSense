"""Admin API: manage threat hashes (optional)."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from engine.api.auth import require_api_key
from engine.db.session import get_db_session
from engine.models.threat_hash import ThreatHash

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_api_key)])


class ThreatHashIn(BaseModel):
    command_hash: str
    category: str | None = None


@router.post("/threat-hashes", status_code=201)
def add_threat_hash(body: ThreatHashIn, db: Session = Depends(get_db_session)):
    """Add a command hash to the threat set (e.g. from normalized malicious command)."""
    row = ThreatHash(command_hash=body.command_hash.strip(), category=body.category)
    db.add(row)
    db.commit()
    return {"command_hash": body.command_hash, "category": body.category}


@router.get("/threat-hashes")
def list_threat_hashes(db: Session = Depends(get_db_session), limit: int = 500):
    """List stored threat hashes (hashes only, no raw commands)."""
    rows = db.query(ThreatHash).limit(limit).all()
    return [{"command_hash": r.command_hash, "category": r.category} for r in rows]
