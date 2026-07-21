"""Add evidence-first strategy workspaces and human decision receipts.

Revision ID: 20260721_0009
Revises: 20260721_0008
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260721_0009"
down_revision: str | None = "20260721_0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RLS_TABLES = ("strategy_workspaces", "strategy_decision_receipts")


def _enable_forced_rls(table: str) -> None:
    op.execute(sa.text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY'))
    op.execute(
        sa.text(
            f'CREATE POLICY tenant_isolation ON "{table}" '
            "USING (tenant_id = NULLIF(current_setting('campaignos.tenant_id', true), '')::uuid) "
            "WITH CHECK (tenant_id = NULLIF("
            "current_setting('campaignos.tenant_id', true), '')::uuid)"
        )
    )


def _disable_rls(table: str) -> None:
    op.execute(sa.text(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}"'))
    op.execute(sa.text(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY'))
    op.execute(sa.text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))


def upgrade() -> None:
    op.create_table(
        "strategy_workspaces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_version", sa.Integer(), nullable=False),
        sa.Column("candidate_workspace_version", sa.Integer(), nullable=False),
        sa.Column("team_workspace_version", sa.Integer(), nullable=False),
        sa.Column("known_role_ids", sa.JSON(), nullable=False),
        sa.Column("title", sa.String(length=180), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("assumptions", sa.JSON(), nullable=True),
        sa.Column("hypotheses", sa.JSON(), nullable=True),
        sa.Column("options", sa.JSON(), nullable=True),
        sa.Column("objectives", sa.JSON(), nullable=True),
        sa.Column("contradictions", sa.JSON(), nullable=True),
        sa.Column("red_team_findings", sa.JSON(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("campaign_version >= 1", name="ck_strategy_campaign_version"),
        sa.CheckConstraint(
            "candidate_workspace_version >= 1", name="ck_strategy_candidate_version"
        ),
        sa.CheckConstraint("team_workspace_version >= 1", name="ck_strategy_team_version"),
        sa.CheckConstraint("version >= 1", name="ck_strategy_workspace_version"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_strategy_workspaces_tenant_campaign",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["candidate_workspaces.tenant_id", "candidate_workspaces.campaign_id"],
            name="fk_strategy_workspaces_candidate_workspace",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["team_workspaces.tenant_id", "team_workspaces.campaign_id"],
            name="fk_strategy_workspaces_team_workspace",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id", "campaign_id", name="uq_strategy_workspaces_tenant_campaign"
        ),
        sa.UniqueConstraint("tenant_id", "id", name="uq_strategy_workspaces_tenant_id_id"),
    )
    op.create_index(
        "ix_strategy_workspaces_tenant_status",
        "strategy_workspaces",
        ["tenant_id", "campaign_id"],
        unique=False,
    )

    op.create_table(
        "strategy_decision_receipts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("strategy_workspace_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_version", sa.Integer(), nullable=False),
        sa.Column("selected_option_id", sa.Uuid(), nullable=False),
        sa.Column("human_role_id", sa.Uuid(), nullable=False),
        sa.Column("approval_receipt_id", sa.String(length=180), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint("workspace_version >= 1", name="ck_strategy_decision_version"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_strategy_decisions_tenant_campaign",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "strategy_workspace_id"],
            ["strategy_workspaces.tenant_id", "strategy_workspaces.id"],
            name="fk_strategy_decisions_workspace",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "strategy_workspace_id",
            "workspace_version",
            name="uq_strategy_decisions_workspace_version",
        ),
    )
    op.create_index(
        "ix_strategy_decisions_tenant_campaign_created",
        "strategy_decision_receipts",
        ["tenant_id", "campaign_id", "created_at"],
        unique=False,
    )

    for table in RLS_TABLES:
        _enable_forced_rls(table)


def downgrade() -> None:
    for table in reversed(RLS_TABLES):
        _disable_rls(table)
    op.drop_index(
        "ix_strategy_decisions_tenant_campaign_created",
        table_name="strategy_decision_receipts",
    )
    op.drop_table("strategy_decision_receipts")
    op.drop_index("ix_strategy_workspaces_tenant_status", table_name="strategy_workspaces")
    op.drop_table("strategy_workspaces")
