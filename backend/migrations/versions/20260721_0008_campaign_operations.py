"""Add campaign roadmap and append-only War Room snapshots.

Revision ID: 20260721_0008
Revises: 20260721_0007
Create Date: 2026-07-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260721_0008"
down_revision: str | None = "20260721_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _enable_rls(table_name: str) -> None:
    tenant_setting = "NULLIF(current_setting('campaignos.tenant_id', true), '')::uuid"
    op.execute(sa.text(f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text(f'ALTER TABLE "{table_name}" FORCE ROW LEVEL SECURITY'))
    op.execute(
        sa.text(
            f'CREATE POLICY tenant_isolation ON "{table_name}" '
            f"USING (tenant_id = {tenant_setting}) "
            f"WITH CHECK (tenant_id = {tenant_setting})"
        )
    )


def upgrade() -> None:
    op.create_table(
        "campaign_roadmaps",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("phases", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("workstreams", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("milestones", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("tasks", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("blockers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("decisions", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("follow_up_items", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("learning_notes", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_campaign_roadmaps_tenant_campaign",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "campaign_id", name="uq_campaign_roadmaps_tenant_campaign"
        ),
        sa.UniqueConstraint("tenant_id", "campaign_id", "id", name="uq_campaign_roadmaps_scope_id"),
    )
    op.create_index(
        "ix_campaign_roadmaps_tenant_updated",
        "campaign_roadmaps",
        ["tenant_id", "updated_at"],
    )
    _enable_rls("campaign_roadmaps")

    op.create_table(
        "war_room_snapshots",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("roadmap_id", sa.Uuid(), nullable=False),
        sa.Column("roadmap_version", sa.Integer(), nullable=False),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("priorities", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("ready_task_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("blocked_task_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "required_decision_ids",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("follow_up_notes", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("learning_note_ids", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id", "roadmap_id"],
            [
                "campaign_roadmaps.tenant_id",
                "campaign_roadmaps.campaign_id",
                "campaign_roadmaps.id",
            ],
            name="fk_war_room_snapshots_roadmap_scope",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "campaign_id",
            "snapshot_date",
            name="uq_war_room_snapshots_tenant_campaign_date",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "campaign_id",
            "id",
            name="uq_war_room_snapshots_scope_id",
        ),
    )
    op.create_index(
        "ix_war_room_snapshots_tenant_campaign_date",
        "war_room_snapshots",
        ["tenant_id", "campaign_id", "snapshot_date"],
    )
    _enable_rls("war_room_snapshots")


def downgrade() -> None:
    op.drop_index(
        "ix_war_room_snapshots_tenant_campaign_date",
        table_name="war_room_snapshots",
    )
    op.drop_table("war_room_snapshots")
    op.drop_index("ix_campaign_roadmaps_tenant_updated", table_name="campaign_roadmaps")
    op.drop_table("campaign_roadmaps")
