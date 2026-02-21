"""Send event batches to the Detection Engine with retry and backoff."""
import logging
import time
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_BACKOFF = [1, 2, 4, 8, 16]
MAX_BACKOFF = 60


def send_batch(url: str, events: list[dict], api_key: str | None = None) -> tuple[bool, int]:
    """
    POST events to url. Returns (success, status_code).
    On 4xx we do not retry; on 5xx/network we retry with exponential backoff.
    """
    headers: dict[str, str] = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    for attempt, delay in enumerate(DEFAULT_BACKOFF):
        try:
            r = httpx.post(url, json=events, headers=headers, timeout=30.0)
            if 200 <= r.status_code < 300:
                return True, r.status_code
            if 400 <= r.status_code < 500:
                logger.warning("Client error %s, not retrying", r.status_code)
                return False, r.status_code
            logger.warning("Server error %s, retry %s after %ss", r.status_code, attempt + 1, delay)
        except (httpx.HTTPError, OSError) as e:
            logger.warning("Request failed: %s, retry %s after %ss", e, attempt + 1, delay)
        time.sleep(min(delay, MAX_BACKOFF))
    return False, 0
