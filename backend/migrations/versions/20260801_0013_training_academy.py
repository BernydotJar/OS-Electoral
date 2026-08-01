"""Add the tenant-scoped governed Training Academy.

Revision ID: 20260801_0013
Revises: 20260729_0012
Create Date: 2026-08-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260801_0013"
down_revision: str | None = "20260729_0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

RLS_TABLES = (
    "training_assignments",
    "training_module_progress",
    "training_completion_receipts",
)
TRIGGER_NAME = "campaignos_append_only_guard"
FUNCTION_NAME = "campaignos_reject_append_only_mutation"


def _enable_rls(table: str) -> None:
    tenant_setting = "NULLIF(current_setting('campaignos.tenant_id', true), '')::uuid"
    op.execute(sa.text(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY'))
    op.execute(sa.text(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY'))
    op.execute(
        sa.text(
            f'CREATE POLICY tenant_isolation ON "{table}" '
            f"USING (tenant_id = {tenant_setting}) "
            f"WITH CHECK (tenant_id = {tenant_setting})"
        )
    )


def upgrade() -> None:
    op.create_table(
        "training_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("assigned_by_principal_id", sa.Uuid(), nullable=False),
        sa.Column("path_id", sa.String(length=80), nullable=False),
        sa.Column("path_version", sa.String(length=20), nullable=False),
        sa.Column("role_slug", sa.String(length=80), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("catalog_digest", sa.String(length=64), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('ASSIGNED', 'IN_PROGRESS', 'COMPLETED')",
            name="ck_training_assignments_status",
        ),
        sa.CheckConstraint("version >= 1", name="ck_training_assignments_version"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_training_assignments_tenant_campaign",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["principal_id"],
            ["principals.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["assigned_by_principal_id"],
            ["principals.id"],
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "campaign_id",
            "id",
            name="uq_training_assignments_scope_id",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "campaign_id",
            "principal_id",
            "path_id",
            "path_version",
            name="uq_training_assignments_principal_path",
        ),
    )
    op.create_index(
        "ix_training_assignments_tenant_campaign_principal",
        "training_assignments",
        ["tenant_id", "campaign_id", "principal_id", "status"],
    )

    op.create_table(
        "training_module_progress",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("module_id", sa.String(length=80), nullable=False),
        sa.Column("module_version", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("latest_result", sa.String(length=16), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('NOT_STARTED', 'IN_PROGRESS', 'COMPLETED')",
            name="ck_training_progress_status",
        ),
        sa.CheckConstraint(
            "latest_result IS NULL OR latest_result IN ('PASS', 'FAIL')",
            name="ck_training_progress_result",
        ),
        sa.CheckConstraint(
            "attempt_count BETWEEN 0 AND 10",
            name="ck_training_progress_attempt_count",
        ),
        sa.CheckConstraint("version >= 1", name="ck_training_progress_version"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id", "assignment_id"],
            [
                "training_assignments.tenant_id",
                "training_assignments.campaign_id",
                "training_assignments.id",
            ],
            name="fk_training_progress_assignment_scope",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "campaign_id",
            "id",
            name="uq_training_progress_scope_id",
        ),
        sa.UniqueConstraint(
            "tenant_id",
            "campaign_id",
            "assignment_id",
            "module_id",
            "module_version",
            name="uq_training_progress_assignment_module",
        ),
    )
    op.create_index(
        "ix_training_progress_assignment_status",
        "training_module_progress",
        ["tenant_id", "campaign_id", "assignment_id", "status"],
    )

    op.create_table(
        "training_completion_receipts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("assignment_id", sa.Uuid(), nullable=False),
        sa.Column("module_progress_id", sa.Uuid(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("module_id", sa.String(length=80), nullable=False),
        sa.Column("module_version", sa.String(length=20), nullable=False),
        sa.Column("result", sa.String(length=16), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("catalog_digest", sa.String(length=64), nullable=False),
        sa.Column("audit_event_id", sa.Uuid(), nullable=False),
        sa.Column("authority_effect", sa.String(length=16), nullable=False),
        sa.Column("external_effects", sa.String(length=16), nullable=False),
        sa.CheckConstraint("result = 'PASS'", name="ck_training_receipts_result_pass"),
        sa.CheckConstraint(
            "authority_effect = 'NONE'",
            name="ck_training_receipts_authority_none",
        ),
        sa.CheckConstraint(
            "external_effects = 'NONE'",
            name="ck_training_receipts_external_none",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id", "assignment_id"],
            [
                "training_assignments.tenant_id",
                "training_assignments.campaign_id",
                "training_assignments.id",
            ],
            name="fk_training_receipts_assignment_scope",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id", "module_progress_id"],
            [
                "training_module_progress.tenant_id",
                "training_module_progress.campaign_id",
                "training_module_progress.id",
            ],
            name="fk_training_receipts_progress_scope",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(["principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["audit_event_id"], ["audit_events.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "campaign_id",
            "module_progress_id",
            name="uq_training_receipts_progress",
        ),
    )
    op.create_index(
        "ix_training_receipts_tenant_principal_completed",
        "training_completion_receipts",
        ["tenant_id", "campaign_id", "principal_id", "completed_at"],
    )

    for table in RLS_TABLES:
        _enable_rls(table)
    op.execute(
        sa.text(
            f'CREATE TRIGGER "{TRIGGER_NAME}" '
            'BEFORE UPDATE OR DELETE ON "training_completion_receipts" '
            f"FOR EACH ROW EXECUTE FUNCTION public.{FUNCTION_NAME}()"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(f'DROP TRIGGER IF EXISTS "{TRIGGER_NAME}" ON "training_completion_receipts"')
    )
    for table in reversed(RLS_TABLES):
        op.execute(sa.text(f'DROP POLICY IF EXISTS tenant_isolation ON "{table}"'))
        op.execute(sa.text(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))
    op.drop_index(
        "ix_training_receipts_tenant_principal_completed",
        table_name="training_completion_receipts",
    )
    op.drop_table("training_completion_receipts")
    op.drop_index(
        "ix_training_progress_assignment_status",
        table_name="training_module_progress",
    )
    op.drop_table("training_module_progress")
    op.drop_index(
        "ix_training_assignments_tenant_campaign_principal",
        table_name="training_assignments",
    )
    op.drop_table("training_assignments")
