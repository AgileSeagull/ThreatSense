#!/usr/bin/env python3
"""Delete agent-generated logs (auth/command/process events) from the database."""

import argparse
import psycopg2

DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5432/threat_detection"

AGENT_TYPES = ("auth", "command", "process")
PLACEHOLDERS = ", ".join(f"'{t}'" for t in AGENT_TYPES)


def clear_agent_logs(db_url: str, dry_run: bool = False, event_type: str | None = None):
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()

    types = (event_type,) if event_type else AGENT_TYPES
    ph = ", ".join(f"'{t}'" for t in types)

    try:
        cur.execute(f"SELECT COUNT(*) FROM raw_events WHERE event_type IN ({ph})")
        raw_count = cur.fetchone()[0]

        cur.execute(f"SELECT COUNT(*) FROM processed_events WHERE event_type IN ({ph})")
        proc_count = cur.fetchone()[0]

        cur.execute(f"SELECT COUNT(*) FROM alerts WHERE event_type IN ({ph})")
        alert_count = cur.fetchone()[0]

        print(f"Types   : {', '.join(types)}")
        print(f"Found   : {raw_count} raw, {proc_count} processed, {alert_count} alerts")

        if raw_count == 0 and proc_count == 0 and alert_count == 0:
            print("Nothing to delete.")
            return

        if dry_run:
            print("Dry run — no data deleted.")
            return

        # Delete in FK order: alerts → processed → raw
        cur.execute(f"DELETE FROM alerts WHERE event_type IN ({ph})")
        cur.execute(f"DELETE FROM processed_events WHERE event_type IN ({ph})")
        cur.execute(f"DELETE FROM raw_events WHERE event_type IN ({ph})")

        conn.commit()
        print(f"Deleted : {alert_count} alerts, {proc_count} processed, {raw_count} raw events")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete agent-generated logs from the database")
    parser.add_argument("--db-url", default=DEFAULT_DB_URL, help="PostgreSQL connection URL")
    parser.add_argument("--dry-run", action="store_true", help="Show counts without deleting")
    parser.add_argument(
        "--type",
        choices=list(AGENT_TYPES),
        dest="event_type",
        help="Delete only a specific event type (default: all agent types)",
    )
    args = parser.parse_args()

    clear_agent_logs(args.db_url, args.dry_run, args.event_type)
