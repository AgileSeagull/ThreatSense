#!/usr/bin/env python3
"""Delete all sensor events (raw_events, processed_events, alerts) from the database."""

import argparse
import psycopg2

DEFAULT_DB_URL = "postgresql://postgres:postgres@localhost:5432/threat_detection"


def clear_sensors(db_url: str, dry_run: bool = False):
    conn = psycopg2.connect(db_url)
    conn.autocommit = False
    cur = conn.cursor()

    try:
        # Count before delete
        cur.execute("SELECT COUNT(*) FROM raw_events WHERE event_type = 'sensor'")
        raw_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM processed_events WHERE event_type = 'sensor'")
        proc_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM alerts WHERE event_type = 'sensor'")
        alert_count = cur.fetchone()[0]

        print(f"Found: {raw_count} raw, {proc_count} processed, {alert_count} alerts")

        if raw_count == 0 and proc_count == 0 and alert_count == 0:
            print("Nothing to delete.")
            return

        if dry_run:
            print("Dry run — no data deleted.")
            return

        # Delete in order: alerts → processed → raw (FK deps)
        cur.execute("DELETE FROM alerts WHERE event_type = 'sensor'")
        cur.execute("DELETE FROM processed_events WHERE event_type = 'sensor'")
        cur.execute("DELETE FROM raw_events WHERE event_type = 'sensor'")

        conn.commit()
        print(f"Deleted: {alert_count} alerts, {proc_count} processed, {raw_count} raw events")

    except Exception as e:
        conn.rollback()
        print(f"Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete all sensor readings from the database")
    parser.add_argument("--db-url", default=DEFAULT_DB_URL, help="PostgreSQL connection URL")
    parser.add_argument("--dry-run", action="store_true", help="Show counts without deleting")
    args = parser.parse_args()

    clear_sensors(args.db_url, args.dry_run)
