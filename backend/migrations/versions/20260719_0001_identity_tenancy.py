"""Create identity, tenancy, campaign, audit, outbox, and RLS foundation.

Revision ID: 20260719_0001
Revises: None
Create Date: 2026-07-19
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260719_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_POLICIES = {
    "tenants": "id",
    "campaigns": "tenant_id",
    "workspaces": "tenant_id",
    "memberships": "tenant_id",
    "role_assignments": "tenant_id",
    "permission_grants": "tenant_id",
    "audit_events": "tenant_id",
    "outbox_events": "tenant_id",
}


def _timestamps() -> tuple[sa.Column[object], sa.Column[object]]:
    return (
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
    )


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=80), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'SUSPENDED', 'OFFBOARDING', 'CLOSED')",
            name="ck_tenants_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_table(
        "principals",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("issuer", sa.String(length=2048), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=True),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("issuer", "subject", name="uq_principals_issuer_subject"),
    )
    op.create_table(
        "campaigns",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("jurisdiction", sa.String(length=255), nullable=False),
        sa.Column("stage", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'ACTIVE', 'ARCHIVED', 'CLOSED')",
            name="ck_campaigns_status",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_campaigns_tenant_id_id"),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_campaigns_tenant_slug"),
    )
    op.create_index("ix_campaigns_tenant_status", "campaigns", ["tenant_id", "status"])
    op.create_table(
        "workspaces",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="ck_workspaces_status"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_workspaces_tenant_campaign",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "campaign_id", "id", name="uq_workspaces_scope_id"),
        sa.UniqueConstraint("tenant_id", "campaign_id", "slug", name="uq_workspaces_scope_slug"),
    )
    op.create_table(
        "memberships",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "valid_from",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('INVITED', 'ACTIVE', 'SUSPENDED', 'REVOKED')",
            name="ck_memberships_status",
        ),
        sa.ForeignKeyConstraint(["principal_id"], ["principals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_memberships_tenant_campaign",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "id", name="uq_memberships_tenant_id_id"),
    )
    op.create_index(
        "uq_memberships_principal_campaign",
        "memberships",
        ["tenant_id", "principal_id", "campaign_id"],
        unique=True,
        postgresql_nulls_not_distinct=True,
    )
    op.create_index("ix_memberships_tenant_principal", "memberships", ["tenant_id", "principal_id"])
    op.create_table(
        "role_assignments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("membership_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=80), nullable=False),
        sa.Column("assigned_by_principal_id", sa.Uuid(), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        *_timestamps(),
        sa.ForeignKeyConstraint(
            ["assigned_by_principal_id"], ["principals.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
            name="fk_role_assignments_tenant_membership",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "membership_id", "role", name="uq_role_assignment"),
    )
    op.create_table(
        "permission_grants",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("membership_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=False),
        sa.Column("purpose", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "valid_from",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("granted_by_principal_id", sa.Uuid(), nullable=False),
        sa.Column("approval_receipt_id", sa.String(length=255), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'REVOKED', 'EXPIRED')",
            name="ck_permission_grants_status",
        ),
        sa.CheckConstraint(
            "workspace_id IS NULL OR campaign_id IS NOT NULL",
            name="ck_permission_grants_workspace_requires_campaign",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by_principal_id"], ["principals.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_permission_grants_tenant_campaign",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
            name="fk_permission_grants_tenant_membership",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id", "workspace_id"],
            ["workspaces.tenant_id", "workspaces.campaign_id", "workspaces.id"],
            name="fk_permission_grants_workspace_scope",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "membership_id",
            "action",
            "resource_type",
            "resource_id",
            name="uq_permission_grant_target",
        ),
    )
    op.create_index(
        "ix_permission_grants_lookup",
        "permission_grants",
        ["tenant_id", "membership_id", "action"],
    )
    op.create_table(
        "audit_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=True),
        sa.Column("principal_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "occurred_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("previous_hash", sa.String(length=64), nullable=False),
        sa.Column("event_hash", sa.String(length=64), nullable=False),
        sa.CheckConstraint(
            "workspace_id IS NULL OR campaign_id IS NOT NULL",
            name="ck_audit_events_workspace_requires_campaign",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_audit_events_tenant_campaign",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id", "workspace_id"],
            ["workspaces.tenant_id", "workspaces.campaign_id", "workspaces.id"],
            name="fk_audit_events_workspace_scope",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["principal_id"], ["principals.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("event_hash"),
    )
    op.create_index("ix_audit_events_tenant_occurred", "audit_events", ["tenant_id", "occurred_at"])
    op.create_table(
        "outbox_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=True),
        sa.Column("topic", sa.String(length=160), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column(
            "available_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'DELIVERED', 'DEAD_LETTER')",
            name="ck_outbox_events_status",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_outbox_events_tenant_campaign",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_outbox_events_pending", "outbox_events", ["status", "available_at"])
    op.create_index("ix_outbox_events_tenant_created", "outbox_events", ["tenant_id", "created_at"])

    tenant_setting = "NULLIF(current_setting('campaignos.tenant_id', true), '')::uuid"
    for table_name, tenant_column in TENANT_POLICIES.items():
        op.execute(sa.text(f'ALTER TABLE "{table_name}" ENABLE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table_name}" FORCE ROW LEVEL SECURITY'))
        op.execute(
            sa.text(
                f'CREATE POLICY tenant_isolation ON "{table_name}" '
                f"USING ({tenant_column} = {tenant_setting}) "
                f"WITH CHECK ({tenant_column} = {tenant_setting})"
            )
        )


def downgrade() -> None:
    op.drop_index("ix_outbox_events_tenant_created", table_name="outbox_events")
    op.drop_index("ix_outbox_events_pending", table_name="outbox_events")
    op.drop_table("outbox_events")
    op.drop_index("ix_audit_events_tenant_occurred", table_name="audit_events")
    op.drop_table("audit_events")
    op.drop_index("ix_permission_grants_lookup", table_name="permission_grants")
    op.drop_table("permission_grants")
    op.drop_table("role_assignments")
    op.drop_index("uq_memberships_principal_campaign", table_name="memberships")
    op.drop_index("ix_memberships_tenant_principal", table_name="memberships")
    op.drop_table("memberships")
    op.drop_table("workspaces")
    op.drop_index("ix_campaigns_tenant_status", table_name="campaigns")
    op.drop_table("campaigns")
    op.drop_table("principals")
    op.drop_table("tenants")
