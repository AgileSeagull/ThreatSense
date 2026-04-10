"""Process a raw event: PSI -> ML risk score -> XAI explanation -> store processed_event and optional alert."""
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc

from engine.config import get_settings
from engine.models.raw_event import RawEvent
from engine.models.processed_event import ProcessedEvent
from engine.models.alert import Alert
from engine.models.threat_hash import ThreatHash
from engine.psi import PSIChecker
from engine.ml.registry import ModelRegistry
from engine.ml.model import MODEL_VERSION
from engine.ml.features import raw_event_to_dict
from engine.xai import explain

# Global registry; lazy-fitted from DB when enough events exist
_registry: ModelRegistry | None = None


def get_registry() -> ModelRegistry:
    global _registry
    if _registry is None:
        _registry = ModelRegistry(model_dir="data/models", min_samples_to_fit=30)
    return _registry


def _ensure_global_model(db: Session) -> None:
    """Load persisted model from disk, or train global Isolation Forest if needed."""
    reg = get_registry()
    if reg._global_fitted:
        return
    if reg.load_global():
        return
    rows = db.query(RawEvent).order_by(desc(RawEvent.id)).limit(500).all()
    events = [raw_event_to_dict(r) for r in rows]
    if reg.fit_global(events):
        reg.save_global()


_SUSPICIOUS_EXE = ["/tmp/", "/var/tmp/", "/dev/shm/", "/usr/bin/nc", "/bin/nc",
                   "miner", "xmrig", "backdoor", "netcat", "reverse"]


def _rule_based_risk(raw: RawEvent) -> tuple[float, list[str]] | None:
    """
    Score events that match known threat patterns with explicit rules.
    Returns (risk_score, contributing_factors) or None if no rule matches.
    Rules complement the Isolation Forest: they catch patterns the unsupervised
    model can't reliably separate (auth failures, suspicious executables, etc.).
    """
    payload = raw.payload or {}

    # Auth failure
    if raw.source == "auth" and payload.get("success") is False:
        action = payload.get("action", "failure")
        service = payload.get("service", "unknown")
        return 75.0, [f"auth_failure ({action})", f"failed_service ({service})"]

    # Suspicious process executable
    if raw.source == "process":
        exe = payload.get("exe", "")
        if any(s in exe for s in _SUSPICIOUS_EXE):
            return 92.0, [f"suspicious_executable ({exe})", "known_threat_pattern"]

    # Unusually long command (obfuscated or encoded payload)
    if raw.source == "command":
        cmd_len = payload.get("command_length") or 0
        if cmd_len > 200:
            score = min(95.0, 50.0 + (cmd_len / 1024.0) * 45.0)
            return score, [f"unusual_command_length ({cmd_len} chars)", "possible_obfuscation"]

    return None


def get_psi_checker(db: Session) -> PSIChecker:
    """Build PSIChecker with hashes from DB and optional file."""
    settings = get_settings()
    rows = db.query(ThreatHash.command_hash).all()
    hashes = {r[0] for r in rows}
    return PSIChecker(threat_hashes=hashes, path=settings.threat_db_path)


def process_raw_event(db: Session, raw: RawEvent, psi: PSIChecker) -> None:
    """
    Run PSI; if not in threat set, run ML anomaly score. Build XAI explanation. Store and maybe alert.
    """
    now = datetime.now(timezone.utc)
    in_threat = False
    risk_score = 0.0
    explanation = None
    contributing_factors: list[str] = []
    model_version = "psi_v1"

    if raw.source == "command" and raw.payload:
        ch = raw.payload.get("command_hash")
        if ch:
            in_threat, category = psi.check(ch)
            if in_threat:
                risk_score = 100.0
                contributing_factors = ["known_malicious_command", category or "threat_db"]
                model_version = "psi_v1"

    if not in_threat:
        rule_result = _rule_based_risk(raw)
        if rule_result is not None:
            risk_score, contributing_factors = rule_result
            model_version = "rules_v1"
        else:
            _ensure_global_model(db)
            reg = get_registry()
            event_dict = raw_event_to_dict(raw)
            ml_risk, factors = reg.score_event(event_dict)
            risk_score = ml_risk
            contributing_factors = factors
            model_version = MODEL_VERSION

    event_context = {
        "event_type": raw.event_type,
        "machine_id": raw.machine_id,
        "user": raw.user,
        "timestamp": raw.timestamp,
        "source": raw.source,
        "payload": raw.payload or {},
    }
    explanation = explain(risk_score, in_threat, contributing_factors, raw.source, event_context)

    processed = ProcessedEvent(
        raw_event_id=raw.id,
        event_type=raw.event_type,
        machine_id=raw.machine_id,
        user=raw.user,
        timestamp=raw.timestamp,
        source=raw.source,
        payload=raw.payload,
        risk_score=risk_score,
        in_threat_set=in_threat,
        explanation=explanation,
        contributing_factors=contributing_factors if contributing_factors else None,
        model_version=model_version,
        processed_at=now,
    )
    db.add(processed)
    db.flush()

    threshold = get_settings().alert_threshold
    if risk_score >= threshold:
        alert = Alert(
            processed_event_id=processed.id,
            event_type=processed.event_type,
            machine_id=processed.machine_id,
            user=processed.user,
            timestamp=processed.timestamp,
            risk_score=processed.risk_score,
            explanation=processed.explanation,
            contributing_factors=processed.contributing_factors,
            created_at=now,
        )
        db.add(alert)
