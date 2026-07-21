"""Add tenant-scoped persisted guided campaign intake.

Revision ID: 20260721_0005
Revises: 20260721_0004
Create Date: 2026-07-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260721_0005"
down_revision: str | None = "20260721_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "guided_intakes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("office", sa.String(length=255), nullable=True),
        sa.Column("candidate_project", sa.Text(), nullable=True),
        sa.Column(
            "current_team",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "current_assets",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("budget_status", sa.String(length=32), nullable=False),
        sa.Column(
            "known_unknowns",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "evidence_requirements",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
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
        sa.CheckConstraint(
            "status IN ('IN_PROGRESS', 'READY_FOR_RESEARCH')",
            name="ck_guided_intakes_status",
        ),
        sa.CheckConstraint(
            "budget_status IN ('NOT_ASSESSED', 'NO_DOCUMENT', 'ROUGH_RANGE', 'DOCUMENTED')",
            name="ck_guided_intakes_budget_status",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_guided_intakes_tenant_campaign",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "campaign_id",
            name="uq_guided_intakes_tenant_campaign",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "id",
            name="uq_guided_intakes_tenant_id_id",
        ),
    )
    op.create_index(
        "ix_guided_intakes_tenant_status",
        "guided_intakes",
        ["tenant_id", "status"],
    )

    tenant_setting = "NULLIF(current_setting('campaignos.tenant_id', true), '')::uuid"
    op.execute(sa.text('ALTER TABLE "guided_intakes" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text('ALTER TABLE "guided_intakes" FORCE ROW LEVEL SECURITY'))
    op.execute(
        sa.text(
            'CREATE POLICY tenant_isolation ON "guided_intakes" '
            f"USING (tenant_id = {tenant_setting}) "
            f"WITH CHECK (tenant_id = {tenant_setting})"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_guided_intakes_tenant_status", table_name="guided_intakes")
    op.drop_table("guided_intakes")
