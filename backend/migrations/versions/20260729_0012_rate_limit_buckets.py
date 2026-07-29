"""Add tenant/principal fixed-window rate-limit buckets.

Revision ID: 20260729_0012
Revises: 20260721_0011
Create Date: 2026-07-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260729_0012"
down_revision: str | None = "20260721_0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLE = "rate_limit_buckets"


def upgrade() -> None:
    op.create_table(
        TABLE,
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("policy_class", sa.String(length=40), nullable=False),
        sa.Column("policy_version", sa.Integer(), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_seconds", sa.Integer(), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("transaction_timestamp()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "policy_class IN ('read', 'mutation', 'expensive_read', "
            "'identity_lifecycle', 'governed_agent_execution')",
            name="ck_rate_limit_buckets_policy_class",
        ),
        sa.CheckConstraint("policy_version >= 1", name="ck_rate_limit_buckets_policy_version"),
        sa.CheckConstraint(
            "window_seconds BETWEEN 1 AND 86400",
            name="ck_rate_limit_buckets_window_seconds",
        ),
        sa.CheckConstraint("request_count >= 1", name="ck_rate_limit_buckets_request_count"),
        sa.PrimaryKeyConstraint(
            "tenant_id",
            "principal_id",
            "policy_class",
            "policy_version",
            "window_start",
            name="pk_rate_limit_buckets",
        ),
    )
    op.create_index(
        "ix_rate_limit_buckets_tenant_window",
        TABLE,
        ["tenant_id", "window_start"],
    )
    tenant_setting = "NULLIF(current_setting('campaignos.tenant_id', true), '')::uuid"
    op.execute(sa.text(f'ALTER TABLE "{TABLE}" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text(f'ALTER TABLE "{TABLE}" FORCE ROW LEVEL SECURITY'))
    op.execute(
        sa.text(
            f'CREATE POLICY tenant_isolation ON "{TABLE}" '
            f"USING (tenant_id = {tenant_setting}) "
            f"WITH CHECK (tenant_id = {tenant_setting})"
        )
    )


def downgrade() -> None:
    op.execute(sa.text(f'DROP POLICY IF EXISTS tenant_isolation ON "{TABLE}"'))
    op.execute(sa.text(f'ALTER TABLE "{TABLE}" NO FORCE ROW LEVEL SECURITY'))
    op.execute(sa.text(f'ALTER TABLE "{TABLE}" DISABLE ROW LEVEL SECURITY'))
    op.drop_index("ix_rate_limit_buckets_tenant_window", table_name=TABLE)
    op.drop_table(TABLE)
