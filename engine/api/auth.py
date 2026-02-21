"""Optional API key auth for /api/v1."""
from fastapi import Header, HTTPException, status

from engine.config import get_settings


def require_api_key(authorization: str | None = Header(None, alias="Authorization")) -> None:
    settings = get_settings()
    if not settings.api_key:
        return
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization[7:].strip()
    if token != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
