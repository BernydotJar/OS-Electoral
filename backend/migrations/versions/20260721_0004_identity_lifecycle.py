"""Add tenant-scoped identity lifecycle records.

Revision ID: 20260721_0004
Revises: 20260721_0003
Create Date: 2026-07-21
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20260721_0004"
down_revision: str | None = "20260721_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_TABLES = (
    "identity_invitations",
    "application_sessions",
    "support_access_requests",
)


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
    op.add_column(
        "memberships",
        sa.Column("version", sa.Integer(), server_default=sa.text("1"), nullable=False),
    )
    op.alter_column("memberships", "version", server_default=None)

    op.create_table(
        "identity_invitations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=True),
        sa.Column("scope_key", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("purpose", sa.String(length=255), nullable=False),
        sa.Column("invited_by_principal_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("provider_reference", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("accepted_by_principal_id", sa.Uuid(), nullable=True),
        sa.Column("membership_id", sa.Uuid(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_principal_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('PENDING', 'ACCEPTED', 'REVOKED', 'EXPIRED')",
            name="ck_identity_invitations_status",
        ),
        sa.CheckConstraint(
            "scope_key = CASE WHEN campaign_id IS NULL THEN 'TENANT' "
            "ELSE replace(CAST(campaign_id AS TEXT), '-', '') END",
            name="ck_identity_invitations_scope_key",
        ),
        sa.ForeignKeyConstraint(
            ["accepted_by_principal_id"],
            ["principals.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["invited_by_principal_id"],
            ["principals.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["revoked_by_principal_id"],
            ["principals.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_identity_invitations_tenant_campaign",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
            name="fk_identity_invitations_tenant_membership",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "provider",
            "provider_reference",
            name="uq_identity_invitations_provider_reference",
        ),
    )
    op.create_index(
        "uq_identity_invitations_pending_target",
        "identity_invitations",
        ["tenant_id", "email", "scope_key"],
        unique=True,
        postgresql_where=sa.text("status = 'PENDING'"),
    )
    op.create_index(
        "ix_identity_invitations_tenant_expires",
        "identity_invitations",
        ["tenant_id", "expires_at"],
    )

    op.create_table(
        "application_sessions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("principal_id", sa.Uuid(), nullable=False),
        sa.Column("provider_session_digest", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("authenticated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_principal_id", sa.Uuid(), nullable=True),
        sa.Column("revocation_reason", sa.String(length=255), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "status IN ('ACTIVE', 'REVOKED', 'EXPIRED')",
            name="ck_application_sessions_status",
        ),
        sa.CheckConstraint(
            "expires_at > authenticated_at",
            name="ck_application_sessions_expiry_after_authentication",
        ),
        sa.ForeignKeyConstraint(
            ["principal_id"],
            ["principals.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["revoked_by_principal_id"],
            ["principals.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "provider_session_digest",
            name="uq_application_sessions_tenant_provider_digest",
        ),
    )
    op.create_index(
        "ix_application_sessions_tenant_principal_status",
        "application_sessions",
        ["tenant_id", "principal_id", "status"],
    )
    op.create_index(
        "ix_application_sessions_tenant_expires",
        "application_sessions",
        ["tenant_id", "expires_at"],
    )

    op.create_table(
        "support_access_requests",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("requested_by_principal_id", sa.Uuid(), nullable=False),
        sa.Column("target_principal_id", sa.Uuid(), nullable=False),
        sa.Column("campaign_id", sa.Uuid(), nullable=True),
        sa.Column("workspace_id", sa.Uuid(), nullable=True),
        sa.Column("campaign_scope_key", sa.String(length=36), nullable=False),
        sa.Column("workspace_scope_key", sa.String(length=36), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("resource_type", sa.String(length=100), nullable=False),
        sa.Column("resource_id", sa.String(length=255), nullable=False),
        sa.Column("purpose", sa.String(length=255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("decided_by_principal_id", sa.Uuid(), nullable=True),
        sa.Column("approval_receipt_id", sa.String(length=255), nullable=True),
        sa.Column("membership_id", sa.Uuid(), nullable=True),
        sa.Column("role_assignment_id", sa.Uuid(), nullable=True),
        sa.Column("permission_grant_id", sa.Uuid(), nullable=True),
        sa.Column("created_membership", sa.Boolean(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_by_principal_id", sa.Uuid(), nullable=True),
        sa.Column("version", sa.Integer(), nullable=False),
        *_timestamps(),
        sa.CheckConstraint(
            "workspace_id IS NULL OR campaign_id IS NOT NULL",
            name="ck_support_access_requests_workspace_requires_campaign",
        ),
        sa.CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED', 'REVOKED', 'EXPIRED')",
            name="ck_support_access_requests_status",
        ),
        sa.CheckConstraint(
            "expires_at > requested_at",
            name="ck_support_access_requests_expiry_after_request",
        ),
        sa.CheckConstraint(
            "campaign_scope_key = CASE WHEN campaign_id IS NULL THEN 'TENANT' "
            "ELSE replace(CAST(campaign_id AS TEXT), '-', '') END",
            name="ck_support_access_requests_campaign_scope_key",
        ),
        sa.CheckConstraint(
            "workspace_scope_key = CASE WHEN workspace_id IS NULL THEN 'NONE' "
            "ELSE replace(CAST(workspace_id AS TEXT), '-', '') END",
            name="ck_support_access_requests_workspace_scope_key",
        ),
        sa.ForeignKeyConstraint(
            ["decided_by_principal_id"],
            ["principals.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["permission_grant_id"],
            ["permission_grants.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by_principal_id"],
            ["principals.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["revoked_by_principal_id"],
            ["principals.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["role_assignment_id"],
            ["role_assignments.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["target_principal_id"],
            ["principals.id"],
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id"],
            ["tenants.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_support_access_requests_tenant_campaign",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "campaign_id", "workspace_id"],
            ["workspaces.tenant_id", "workspaces.campaign_id", "workspaces.id"],
            name="fk_support_access_requests_workspace_scope",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
            name="fk_support_access_requests_tenant_membership",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_support_access_requests_tenant_status",
        "support_access_requests",
        ["tenant_id", "status", "expires_at"],
    )
    op.create_index(
        "ix_support_access_requests_target",
        "support_access_requests",
        ["tenant_id", "target_principal_id", "status"],
    )
    op.create_index(
        "uq_support_access_requests_active_target",
        "support_access_requests",
        [
            "tenant_id",
            "target_principal_id",
            "campaign_scope_key",
            "workspace_scope_key",
            "action",
            "resource_type",
            "resource_id",
        ],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'APPROVED')"),
    )

    for table_name in TENANT_TABLES:
        _enable_tenant_rls(table_name)


def downgrade() -> None:
    op.drop_index(
        "uq_support_access_requests_active_target",
        table_name="support_access_requests",
    )
    op.drop_index(
        "ix_support_access_requests_target",
        table_name="support_access_requests",
    )
    op.drop_index(
        "ix_support_access_requests_tenant_status",
        table_name="support_access_requests",
    )
    op.drop_table("support_access_requests")

    op.drop_index(
        "ix_application_sessions_tenant_expires",
        table_name="application_sessions",
    )
    op.drop_index(
        "ix_application_sessions_tenant_principal_status",
        table_name="application_sessions",
    )
    op.drop_table("application_sessions")

    op.drop_index(
        "ix_identity_invitations_tenant_expires",
        table_name="identity_invitations",
    )
    op.drop_index(
        "uq_identity_invitations_pending_target",
        table_name="identity_invitations",
    )
    op.drop_table("identity_invitations")

    op.drop_column("memberships", "version")
