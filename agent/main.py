"""Endpoint agent: collect activity, buffer, send to Detection Engine."""
import logging
import os
import signal
import sys
import time
from pathlib import Path

from agent.buffer import EventBuffer
from agent.config_loader import load_config
from agent.collectors import AuthCollector, CommandCollector, ProcessCollector
from agent.sender import send_batch

logger = logging.getLogger(__name__)


def get_machine_id() -> str:
    p = Path("/etc/machine-id")
    if p.exists():
        return p.read_text().strip() or "unknown"
    return os.environ.get("AGENT_MACHINE_ID", "unknown")


def main() -> None:
    cfg = load_config()
    logging.basicConfig(
        level=getattr(logging, cfg.get("log_level", "INFO").upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    url = cfg["endpoint_url"].rstrip("/")
    if not url.endswith("/events"):
        url = url + "/events" if url.endswith("/api/v1") else url + "/api/v1/events"
    batch_size = int(cfg.get("batch_size", 50))
    interval = int(cfg.get("send_interval_seconds", 30))
    persist_path = os.environ.get("AGENT_PERSIST_PATH")
    api_key = os.environ.get("AGENT_API_KEY")

    buffer = EventBuffer(persist_path=persist_path)
    machine_id = get_machine_id()
    auth = AuthCollector(
        use_journal=cfg.get("auth_source") != "file",
        log_path=cfg.get("auth_log_path", "/var/log/auth.log"),
    )
    command = CommandCollector(history_glob=cfg.get("history_glob", "/home/*/.bash_history"))
    process = ProcessCollector(sample_limit=50)
    collectors = [auth, command, process]

    running = True

    def stop(_sig: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    logger.info("Agent started; machine_id=%s, endpoint=%s", machine_id, url)
    last_send = time.monotonic()
    collect_interval = 10
    last_collect = 0.0

    while running:
        now = time.monotonic()
        if now - last_collect >= collect_interval:
            for collector in collectors:
                try:
                    for event in collector.collect(machine_id):
                        buffer.push(event)
                except Exception as e:
                    logger.exception("Collector %s failed: %s", type(collector).__name__, e)
            last_collect = now

        if len(buffer) > 0 and (len(buffer) >= batch_size or (now - last_send >= interval)):
            batch = buffer.pop_batch(batch_size)
            ok, status = send_batch(url, batch, api_key=api_key)
            if ok:
                last_send = now
                logger.debug("Sent %d events", len(batch))
            else:
                buffer.push_many(batch)

        time.sleep(1.0)

    logger.info("Agent stopping")
    sys.exit(0)


if __name__ == "__main__":
    main()
