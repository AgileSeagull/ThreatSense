"""Initial schema: machines, users, raw_events, processed_events, alerts, threat_hashes.

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "machines",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("machine_id", sa.String(256), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_machines_machine_id"), "machines", ["machine_id"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(256), nullable=False),
        sa.Column("machine_id", sa.String(256), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_machine_id"), "users", ["machine_id"], unique=False)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=False)

    op.create_table(
        "raw_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("machine_id", sa.String(256), nullable=False),
        sa.Column("user", sa.String(256), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_raw_events_machine_id"), "raw_events", ["machine_id"], unique=False)
    op.create_index(op.f("ix_raw_events_timestamp"), "raw_events", ["timestamp"], unique=False)
    op.create_index(op.f("ix_raw_events_user"), "raw_events", ["user"], unique=False)
    op.create_index(op.f("ix_raw_events_source"), "raw_events", ["source"], unique=False)

    op.create_table(
        "threat_hashes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("command_hash", sa.String(64), nullable=False),
        sa.Column("category", sa.String(128), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_threat_hashes_command_hash"), "threat_hashes", ["command_hash"], unique=True)

    op.create_table(
        "processed_events",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("raw_event_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("machine_id", sa.String(256), nullable=False),
        sa.Column("user", sa.String(256), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=True),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("in_threat_set", sa.Boolean(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("contributing_factors", sa.JSON(), nullable=True),
        sa.Column("model_version", sa.String(64), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_processed_events_machine_id"), "processed_events", ["machine_id"], unique=False)
    op.create_index(op.f("ix_processed_events_risk_score"), "processed_events", ["risk_score"], unique=False)
    op.create_index(op.f("ix_processed_events_timestamp"), "processed_events", ["timestamp"], unique=False)
    op.create_index(op.f("ix_processed_events_user"), "processed_events", ["user"], unique=False)

    op.create_table(
        "alerts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("processed_event_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("machine_id", sa.String(256), nullable=False),
        sa.Column("user", sa.String(256), nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("explanation", sa.Text(), nullable=True),
        sa.Column("contributing_factors", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_alerts_machine_id"), "alerts", ["machine_id"], unique=False)
    op.create_index(op.f("ix_alerts_risk_score"), "alerts", ["risk_score"], unique=False)
    op.create_index(op.f("ix_alerts_timestamp"), "alerts", ["timestamp"], unique=False)
    op.create_index(op.f("ix_alerts_user"), "alerts", ["user"], unique=False)


def downgrade() -> None:
    op.drop_table("alerts")
    op.drop_table("processed_events")
    op.drop_table("threat_hashes")
    op.drop_table("raw_events")
    op.drop_table("users")
    op.drop_table("machines")
