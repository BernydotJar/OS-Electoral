"""Add tenant-scoped campaign team workspace.

Revision ID: 20260721_0007
Revises: 20260721_0006
Create Date: 2026-07-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260721_0007"
down_revision: str | None = "20260721_0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "team_workspaces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("organization_template", sa.String(length=64), nullable=False),
        sa.Column("roles", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("work_items", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "training_requirements",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column(
            "access_recommendations",
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
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_team_workspaces_tenant_campaign",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "campaign_id", name="uq_team_workspaces_tenant_campaign"),
        sa.UniqueConstraint(
            "tenant_id",
            "campaign_id",
            "id",
            name="uq_team_workspaces_scope_id",
        ),
    )
    op.create_index(
        "ix_team_workspaces_tenant_updated",
        "team_workspaces",
        ["tenant_id", "updated_at"],
    )
    tenant_setting = "NULLIF(current_setting('campaignos.tenant_id', true), '')::uuid"
    op.execute(sa.text('ALTER TABLE "team_workspaces" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text('ALTER TABLE "team_workspaces" FORCE ROW LEVEL SECURITY'))
    op.execute(
        sa.text(
            'CREATE POLICY tenant_isolation ON "team_workspaces" '
            f"USING (tenant_id = {tenant_setting}) "
            f"WITH CHECK (tenant_id = {tenant_setting})"
        )
    )


def downgrade() -> None:
    op.drop_index("ix_team_workspaces_tenant_updated", table_name="team_workspaces")
    op.drop_table("team_workspaces")
