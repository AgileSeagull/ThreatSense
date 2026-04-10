from datetime import datetime
from pydantic import BaseModel, Field


class EventPayload(BaseModel):
    """Type-specific payload; validation relaxed for flexibility."""
    # auth
    action: str | None = None
    service: str | None = None
    remote_host: str | None = None
    success: bool | None = None
    # command
    command_hash: str | None = None
    command_length: int | None = None
    # process
    pid: int | None = None
    exe: str | None = None
    argv: list[str] | None = None
    parent_pid: int | None = None
    start_time: float | None = None
    # sensor (IoT) — common
    sensor_id: str | None = None    # unique sensor identifier
    sensor_type: str | None = None  # "gyro" | "sound" | "magnetic"
    # MPU-6050 gyro: 3-axis accelerometer + 3-axis gyroscope
    ax: float | None = None
    ay: float | None = None
    az: float | None = None
    gx: float | None = None
    gy: float | None = None
    gz: float | None = None
    # HW-485 (sound) / HW-509 (magnetic): binary trigger
    triggered: bool | None = None


class EventIn(BaseModel):
    event_type: str = Field(..., pattern="^(auth|command|process|sensor)$")
    machine_id: str = Field(..., min_length=1)
    user: str = Field(..., min_length=1)
    timestamp: datetime
    source: str = Field(..., pattern="^(auth|command|process|sensor)$")
    payload: dict | None = None


class EventsIngestResponse(BaseModel):
    accepted: int
    rejected: int
    message: str


class AlertOut(BaseModel):
    id: int
    processed_event_id: int
    event_type: str
    machine_id: str
    user: str
    timestamp: datetime
    risk_score: float
    explanation: str | None
    contributing_factors: list | None
    created_at: datetime

    class Config:
        from_attributes = True


class ProcessedEventOut(BaseModel):
    id: int
    raw_event_id: int
    event_type: str
    machine_id: str
    user: str
    timestamp: datetime
    source: str
    payload: dict | None
    risk_score: float
    in_threat_set: bool
    explanation: str | None
    contributing_factors: list | None
    processed_at: datetime

    class Config:
        from_attributes = True


class ActivityQuery(BaseModel):
    machine_id: str | None = None
    user: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    risk_min: float | None = None
    limit: int = Field(default=100, ge=1, le=1000)


class AlertsQuery(BaseModel):
    machine_id: str | None = None
    user: str | None = None
    since: datetime | None = None
    until: datetime | None = None
    risk_min: float | None = None
    limit: int = Field(default=50, ge=1, le=500)
