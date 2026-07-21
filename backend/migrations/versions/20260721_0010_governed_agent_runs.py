"""Add governed provider-neutral agent run journal.

Revision ID: 20260721_0010
Revises: 20260721_0009
Create Date: 2026-07-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260721_0010"
down_revision: str | None = "20260721_0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("strategy_workspace_id", sa.Uuid(), nullable=False),
        sa.Column("strategy_workspace_version", sa.Integer(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("purpose", sa.String(length=80), nullable=False),
        sa.Column("instruction_digest", sa.String(length=64), nullable=False),
        sa.Column("policy_id", sa.String(length=160), nullable=False),
        sa.Column("policy_version", sa.String(length=32), nullable=False),
        sa.Column("prompt_template_id", sa.String(length=160), nullable=False),
        sa.Column("prompt_template_version", sa.String(length=32), nullable=False),
        sa.Column("output_schema_version", sa.String(length=32), nullable=False),
        sa.Column("prompt_digest", sa.String(length=64), nullable=True),
        sa.Column("provider", sa.String(length=80), nullable=True),
        sa.Column("model", sa.String(length=160), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("refusal_code", sa.String(length=100), nullable=True),
        sa.Column("refusal_detail", sa.String(length=255), nullable=True),
        sa.Column("recommendation", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("evidence_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("option_refs", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost_micros", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "human_disposition", sa.String(length=32), nullable=False, server_default="PENDING"
        ),
        sa.Column("authority_effect", sa.String(length=32), nullable=False, server_default="NONE"),
        sa.Column("external_effects", sa.String(length=32), nullable=False, server_default="NONE"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.CheckConstraint(
            "strategy_workspace_version >= 1", name="ck_agent_runs_strategy_version"
        ),
        sa.CheckConstraint("status IN ('COMPLETED', 'REFUSED')", name="ck_agent_runs_status"),
        sa.CheckConstraint("human_disposition = 'PENDING'", name="ck_agent_runs_human_pending"),
        sa.CheckConstraint("authority_effect = 'NONE'", name="ck_agent_runs_authority_none"),
        sa.CheckConstraint("external_effects = 'NONE'", name="ck_agent_runs_external_none"),
        sa.CheckConstraint("prompt_tokens >= 0", name="ck_agent_runs_prompt_tokens"),
        sa.CheckConstraint("output_tokens >= 0", name="ck_agent_runs_output_tokens"),
        sa.CheckConstraint("latency_ms >= 0", name="ck_agent_runs_latency"),
        sa.CheckConstraint("cost_micros >= 0", name="ck_agent_runs_cost"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_agent_runs_tenant_campaign",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "strategy_workspace_id"],
            ["strategy_workspaces.tenant_id", "strategy_workspaces.id"],
            name="fk_agent_runs_strategy_workspace",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_agent_runs_tenant_id_id"),
    )
    op.create_index(
        "ix_agent_runs_tenant_campaign_created",
        "agent_runs",
        ["tenant_id", "campaign_id", "created_at"],
        unique=False,
    )
    op.execute(sa.text('ALTER TABLE "agent_runs" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text('ALTER TABLE "agent_runs" FORCE ROW LEVEL SECURITY'))
    op.execute(
        sa.text(
            'CREATE POLICY tenant_isolation ON "agent_runs" '
            "USING (tenant_id = NULLIF(current_setting('campaignos.tenant_id', true), '')::uuid) "
            "WITH CHECK (tenant_id = NULLIF("
            "current_setting('campaignos.tenant_id', true), '')::uuid)"
        )
    )


def downgrade() -> None:
    op.execute(sa.text('DROP POLICY IF EXISTS tenant_isolation ON "agent_runs"'))
    op.execute(sa.text('ALTER TABLE "agent_runs" NO FORCE ROW LEVEL SECURITY'))
    op.execute(sa.text('ALTER TABLE "agent_runs" DISABLE ROW LEVEL SECURITY'))
    op.drop_index("ix_agent_runs_tenant_campaign_created", table_name="agent_runs")
    op.drop_table("agent_runs")
