"""Add tenant-scoped candidate evidence workspace and section approvals.

Revision ID: 20260721_0006
Revises: 20260721_0005
Create Date: 2026-07-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260721_0006"
down_revision: str | None = "20260721_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _jsonb() -> postgresql.JSONB:
    return postgresql.JSONB(astext_type=sa.Text())


def _enable_tenant_rls(table_name: str) -> None:
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
        "candidate_workspaces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_id", sa.Uuid(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("evidence", _jsonb(), nullable=False),
        sa.Column("identity", _jsonb(), nullable=True),
        sa.Column("biography", _jsonb(), nullable=True),
        sa.Column("purpose", _jsonb(), nullable=True),
        sa.Column("values", _jsonb(), nullable=True),
        sa.Column("attributes", _jsonb(), nullable=True),
        sa.Column("contradictions", _jsonb(), nullable=True),
        sa.Column("development_goals", _jsonb(), nullable=True),
        sa.Column("reputation_risks", _jsonb(), nullable=True),
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
            name="fk_candidate_workspaces_tenant_campaign",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "campaign_id",
            name="uq_candidate_workspaces_tenant_campaign",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "campaign_id",
            "id",
            name="uq_candidate_workspaces_scope_id",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "candidate_id",
            name="uq_candidate_workspaces_tenant_candidate",
        ),
    )
    op.create_index(
        "ix_candidate_workspaces_tenant_updated",
        "candidate_workspaces",
        ["tenant_id", "updated_at"],
    )

    op.create_table(
        "candidate_section_approvals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_workspace_id", sa.Uuid(), nullable=False),
        sa.Column("section", sa.String(length=64), nullable=False),
        sa.Column("approved_version", sa.Integer(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("authorization_grant_id", sa.Uuid(), nullable=False),
        sa.Column("approval_receipt_id", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "section IN ('identity', 'biography', 'purpose', 'values', "
            "'attributes', 'contradictions', 'development_goals', 'reputation')",
            name="ck_candidate_section_approvals_section",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_candidate_section_approvals_tenant_campaign",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id", "candidate_workspace_id"],
            [
                "candidate_workspaces.tenant_id",
                "candidate_workspaces.campaign_id",
                "candidate_workspaces.id",
            ],
            name="fk_candidate_section_approvals_workspace_scope",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["principal_id"],
            ["principals.id"],
            name="fk_candidate_section_approvals_principal",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "candidate_workspace_id",
            "section",
            "approved_version",
            name="uq_candidate_section_approvals_version_section",
        ),
    )
    op.create_index(
        "ix_candidate_section_approvals_workspace_version",
        "candidate_section_approvals",
        ["tenant_id", "candidate_workspace_id", "approved_version"],
    )

    _enable_tenant_rls("candidate_workspaces")
    _enable_tenant_rls("candidate_section_approvals")


def downgrade() -> None:
    op.drop_index(
        "ix_candidate_section_approvals_workspace_version",
        table_name="candidate_section_approvals",
    )
    op.drop_table("candidate_section_approvals")
    op.drop_index(
        "ix_candidate_workspaces_tenant_updated",
        table_name="candidate_workspaces",
    )
    op.drop_table("candidate_workspaces")
