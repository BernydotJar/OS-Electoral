"""Add recoverable outbox processing leases.

Revision ID: 20260721_0003
Revises: 20260721_0002
Create Date: 2026-07-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260721_0003"
down_revision: str | None = "20260721_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("outbox_events", sa.Column("lease_owner", sa.String(length=255)))
    op.add_column("outbox_events", sa.Column("lease_expires_at", sa.DateTime(timezone=True)))
    op.create_index(
        "ix_outbox_events_recoverable",
        "outbox_events",
        ["status", "lease_expires_at", "available_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_outbox_events_recoverable", table_name="outbox_events")
    op.drop_column("outbox_events", "lease_expires_at")
    op.drop_column("outbox_events", "lease_owner")
