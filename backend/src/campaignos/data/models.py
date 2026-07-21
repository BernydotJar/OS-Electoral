"""Initial identity, tenancy, campaign, audit, and outbox relational model."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

JSON_DOCUMENT = JSON().with_variant(JSONB(), "postgresql")


class Base(DeclarativeBase):
    """Declarative metadata root with UUID identifiers."""


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class Tenant(Base, TimestampMixin):
    __tablename__ = "tenants"
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'SUSPENDED', 'OFFBOARDING', 'CLOSED')", name="ck_tenants_status"
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    slug: Mapped[str] = mapped_column(String(80), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Principal(Base, TimestampMixin):
    __tablename__ = "principals"
    __table_args__ = (UniqueConstraint("issuer", "subject", name="uq_principals_issuer_subject"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    issuer: Mapped[str] = mapped_column(String(2048), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str | None] = mapped_column(String(255))
    email: Mapped[str | None] = mapped_column(String(320))
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Campaign(Base, TimestampMixin):
    __tablename__ = "campaigns"
    __table_args__ = (
        UniqueConstraint("tenant_id", "id", name="uq_campaigns_tenant_id_id"),
        UniqueConstraint("tenant_id", "slug", name="uq_campaigns_tenant_slug"),
        CheckConstraint(
            "status IN ('DRAFT', 'ACTIVE', 'ARCHIVED', 'CLOSED')", name="ck_campaigns_status"
        ),
        Index("ix_campaigns_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(255), nullable=False)
    stage: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="DRAFT")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Workspace(Base, TimestampMixin):
    __tablename__ = "workspaces"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_workspaces_tenant_campaign",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "campaign_id", "id", name="uq_workspaces_scope_id"),
        UniqueConstraint("tenant_id", "campaign_id", "slug", name="uq_workspaces_scope_slug"),
        CheckConstraint("status IN ('ACTIVE', 'ARCHIVED')", name="ck_workspaces_status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Membership(Base, TimestampMixin):
    __tablename__ = "memberships"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_memberships_tenant_campaign",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_memberships_tenant_id_id"),
        Index(
            "uq_memberships_principal_campaign",
            "tenant_id",
            "principal_id",
            "campaign_id",
            unique=True,
            postgresql_nulls_not_distinct=True,
        ),
        CheckConstraint(
            "status IN ('INVITED', 'ACTIVE', 'SUSPENDED', 'REVOKED')", name="ck_memberships_status"
        ),
        Index("ix_memberships_tenant_principal", "tenant_id", "principal_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    principal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[UUID | None] = mapped_column(Uuid)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="INVITED")
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class RoleAssignment(Base, TimestampMixin):
    __tablename__ = "role_assignments"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
            name="fk_role_assignments_tenant_membership",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "membership_id", "role", name="uq_role_assignment"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    membership_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    role: Mapped[str] = mapped_column(String(80), nullable=False)
    assigned_by_principal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PermissionGrant(Base, TimestampMixin):
    __tablename__ = "permission_grants"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
            name="fk_permission_grants_tenant_membership",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_permission_grants_tenant_campaign",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id", "workspace_id"],
            ["workspaces.tenant_id", "workspaces.campaign_id", "workspaces.id"],
            name="fk_permission_grants_workspace_scope",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "tenant_id",
            "membership_id",
            "action",
            "resource_type",
            "resource_id",
            name="uq_permission_grant_target",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'REVOKED', 'EXPIRED')", name="ck_permission_grants_status"
        ),
        CheckConstraint(
            "workspace_id IS NULL OR campaign_id IS NOT NULL",
            name="ck_permission_grants_workspace_requires_campaign",
        ),
        Index("ix_permission_grants_lookup", "tenant_id", "membership_id", "action"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    membership_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    campaign_id: Mapped[UUID | None] = mapped_column(Uuid)
    workspace_id: Mapped[UUID | None] = mapped_column(Uuid)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    granted_by_principal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    approval_receipt_id: Mapped[str] = mapped_column(String(255), nullable=False)


class IdentityInvitation(Base, TimestampMixin):
    __tablename__ = "identity_invitations"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_identity_invitations_tenant_campaign",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
            name="fk_identity_invitations_tenant_membership",
            ondelete="RESTRICT",
        ),
        UniqueConstraint(
            "tenant_id",
            "provider",
            "provider_reference",
            name="uq_identity_invitations_provider_reference",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'ACCEPTED', 'REVOKED', 'EXPIRED')",
            name="ck_identity_invitations_status",
        ),
        CheckConstraint(
            "scope_key = CASE WHEN campaign_id IS NULL THEN 'TENANT' "
            "ELSE replace(CAST(campaign_id AS TEXT), '-', '') END",
            name="ck_identity_invitations_scope_key",
        ),
        Index(
            "uq_identity_invitations_pending_target",
            "tenant_id",
            "email",
            "scope_key",
            unique=True,
            postgresql_where=text("status = 'PENDING'"),
            sqlite_where=text("status = 'PENDING'"),
        ),
        Index("ix_identity_invitations_tenant_expires", "tenant_id", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    campaign_id: Mapped[UUID | None] = mapped_column(Uuid)
    scope_key: Mapped[str] = mapped_column(String(36), nullable=False)
    email: Mapped[str] = mapped_column(String(320), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    invited_by_principal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    provider: Mapped[str] = mapped_column(String(80), nullable=False)
    provider_reference: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    accepted_by_principal_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="RESTRICT")
    )
    membership_id: Mapped[UUID | None] = mapped_column(Uuid)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_by_principal_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="RESTRICT")
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class ApplicationSession(Base, TimestampMixin):
    __tablename__ = "application_sessions"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "provider_session_digest",
            name="uq_application_sessions_tenant_provider_digest",
        ),
        CheckConstraint(
            "status IN ('ACTIVE', 'REVOKED', 'EXPIRED')",
            name="ck_application_sessions_status",
        ),
        CheckConstraint(
            "expires_at > authenticated_at",
            name="ck_application_sessions_expiry_after_authentication",
        ),
        Index(
            "ix_application_sessions_tenant_principal_status",
            "tenant_id",
            "principal_id",
            "status",
        ),
        Index("ix_application_sessions_tenant_expires", "tenant_id", "expires_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    principal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="CASCADE"), nullable=False
    )
    provider_session_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="ACTIVE")
    authenticated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_by_principal_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="RESTRICT")
    )
    revocation_reason: Mapped[str | None] = mapped_column(String(255))
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class SupportAccessRequest(Base, TimestampMixin):
    __tablename__ = "support_access_requests"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_support_access_requests_tenant_campaign",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id", "workspace_id"],
            ["workspaces.tenant_id", "workspaces.campaign_id", "workspaces.id"],
            name="fk_support_access_requests_workspace_scope",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "membership_id"],
            ["memberships.tenant_id", "memberships.id"],
            name="fk_support_access_requests_tenant_membership",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "workspace_id IS NULL OR campaign_id IS NOT NULL",
            name="ck_support_access_requests_workspace_requires_campaign",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'APPROVED', 'REJECTED', 'REVOKED', 'EXPIRED')",
            name="ck_support_access_requests_status",
        ),
        CheckConstraint(
            "expires_at > requested_at",
            name="ck_support_access_requests_expiry_after_request",
        ),
        CheckConstraint(
            "campaign_scope_key = CASE WHEN campaign_id IS NULL THEN 'TENANT' "
            "ELSE replace(CAST(campaign_id AS TEXT), '-', '') END",
            name="ck_support_access_requests_campaign_scope_key",
        ),
        CheckConstraint(
            "workspace_scope_key = CASE WHEN workspace_id IS NULL THEN 'NONE' "
            "ELSE replace(CAST(workspace_id AS TEXT), '-', '') END",
            name="ck_support_access_requests_workspace_scope_key",
        ),
        Index(
            "ix_support_access_requests_tenant_status",
            "tenant_id",
            "status",
            "expires_at",
        ),
        Index(
            "ix_support_access_requests_target",
            "tenant_id",
            "target_principal_id",
            "status",
        ),
        Index(
            "uq_support_access_requests_active_target",
            "tenant_id",
            "target_principal_id",
            "campaign_scope_key",
            "workspace_scope_key",
            "action",
            "resource_type",
            "resource_id",
            unique=True,
            postgresql_where=text("status IN ('PENDING', 'APPROVED')"),
            sqlite_where=text("status IN ('PENDING', 'APPROVED')"),
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False
    )
    requested_by_principal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    target_principal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    campaign_id: Mapped[UUID | None] = mapped_column(Uuid)
    workspace_id: Mapped[UUID | None] = mapped_column(Uuid)
    campaign_scope_key: Mapped[str] = mapped_column(String(36), nullable=False)
    workspace_scope_key: Mapped[str] = mapped_column(String(36), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    purpose: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    decided_by_principal_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="RESTRICT")
    )
    approval_receipt_id: Mapped[str | None] = mapped_column(String(255))
    membership_id: Mapped[UUID | None] = mapped_column(Uuid)
    role_assignment_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("role_assignments.id", ondelete="RESTRICT")
    )
    permission_grant_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("permission_grants.id", ondelete="RESTRICT")
    )
    created_membership: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_by_principal_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="RESTRICT")
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class CandidateWorkspace(Base, TimestampMixin):
    __tablename__ = "candidate_workspaces"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_candidate_workspaces_tenant_campaign",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "tenant_id",
            "campaign_id",
            name="uq_candidate_workspaces_tenant_campaign",
        ),
        UniqueConstraint(
            "tenant_id",
            "campaign_id",
            "id",
            name="uq_candidate_workspaces_scope_id",
        ),
        UniqueConstraint(
            "tenant_id",
            "candidate_id",
            name="uq_candidate_workspaces_tenant_candidate",
        ),
        Index("ix_candidate_workspaces_tenant_updated", "tenant_id", "updated_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    candidate_id: Mapped[UUID] = mapped_column(Uuid, nullable=False, default=uuid4)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    evidence: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON_DOCUMENT, nullable=False, default=list
    )
    identity: Mapped[dict[str, Any] | None] = mapped_column(JSON_DOCUMENT)
    biography: Mapped[dict[str, Any] | None] = mapped_column(JSON_DOCUMENT)
    purpose: Mapped[dict[str, Any] | None] = mapped_column(JSON_DOCUMENT)
    values: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    attributes: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    contradictions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    development_goals: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    reputation_risks: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class CandidateSectionApproval(Base):
    __tablename__ = "candidate_section_approvals"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_candidate_section_approvals_tenant_campaign",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id", "candidate_workspace_id"],
            [
                "candidate_workspaces.tenant_id",
                "candidate_workspaces.campaign_id",
                "candidate_workspaces.id",
            ],
            name="fk_candidate_section_approvals_workspace_scope",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "tenant_id",
            "candidate_workspace_id",
            "section",
            "approved_version",
            name="uq_candidate_section_approvals_version_section",
        ),
        CheckConstraint(
            "section IN ('identity', 'biography', 'purpose', 'values', "
            "'attributes', 'contradictions', 'development_goals', 'reputation')",
            name="ck_candidate_section_approvals_section",
        ),
        Index(
            "ix_candidate_section_approvals_workspace_version",
            "tenant_id",
            "candidate_workspace_id",
            "approved_version",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    candidate_workspace_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    section: Mapped[str] = mapped_column(String(64), nullable=False)
    approved_version: Mapped[int] = mapped_column(Integer, nullable=False)
    principal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    authorization_grant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    approval_receipt_id: Mapped[str] = mapped_column(String(255), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    approved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CampaignRoadmap(Base, TimestampMixin):
    __tablename__ = "campaign_roadmaps"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_campaign_roadmaps_tenant_campaign",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "campaign_id", name="uq_campaign_roadmaps_tenant_campaign"),
        UniqueConstraint(
            "tenant_id",
            "campaign_id",
            "id",
            name="uq_campaign_roadmaps_scope_id",
        ),
        Index("ix_campaign_roadmaps_tenant_updated", "tenant_id", "updated_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    phases: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    workstreams: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    milestones: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    tasks: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    blockers: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    decisions: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    follow_up_items: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    learning_notes: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class WarRoomSnapshot(Base, TimestampMixin):
    __tablename__ = "war_room_snapshots"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id", "roadmap_id"],
            [
                "campaign_roadmaps.tenant_id",
                "campaign_roadmaps.campaign_id",
                "campaign_roadmaps.id",
            ],
            name="fk_war_room_snapshots_roadmap_scope",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "tenant_id",
            "campaign_id",
            "snapshot_date",
            name="uq_war_room_snapshots_tenant_campaign_date",
        ),
        UniqueConstraint(
            "tenant_id",
            "campaign_id",
            "id",
            name="uq_war_room_snapshots_scope_id",
        ),
        Index(
            "ix_war_room_snapshots_tenant_campaign_date",
            "tenant_id",
            "campaign_id",
            "snapshot_date",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    roadmap_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    roadmap_version: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    priorities: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False)
    ready_task_ids: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False)
    blocked_task_ids: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False)
    required_decision_ids: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False)
    follow_up_notes: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False)
    learning_note_ids: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False)


class TeamWorkspace(Base, TimestampMixin):
    __tablename__ = "team_workspaces"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_team_workspaces_tenant_campaign",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "tenant_id",
            "campaign_id",
            name="uq_team_workspaces_tenant_campaign",
        ),
        UniqueConstraint(
            "tenant_id",
            "campaign_id",
            "id",
            name="uq_team_workspaces_scope_id",
        ),
        Index("ix_team_workspaces_tenant_updated", "tenant_id", "updated_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    organization_template: Mapped[str] = mapped_column(String(64), nullable=False)
    roles: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    work_items: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    training_requirements: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    access_recommendations: Mapped[list[dict[str, Any]] | None] = mapped_column(JSON_DOCUMENT)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class GuidedIntake(Base, TimestampMixin):
    __tablename__ = "guided_intakes"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_guided_intakes_tenant_campaign",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "campaign_id", name="uq_guided_intakes_tenant_campaign"),
        UniqueConstraint("tenant_id", "id", name="uq_guided_intakes_tenant_id_id"),
        CheckConstraint(
            "status IN ('IN_PROGRESS', 'READY_FOR_RESEARCH')",
            name="ck_guided_intakes_status",
        ),
        CheckConstraint(
            "budget_status IN ('NOT_ASSESSED', 'NO_DOCUMENT', 'ROUGH_RANGE', 'DOCUMENTED')",
            name="ck_guided_intakes_budget_status",
        ),
        Index("ix_guided_intakes_tenant_status", "tenant_id", "status"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(Uuid, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="IN_PROGRESS")
    office: Mapped[str | None] = mapped_column(String(255))
    candidate_project: Mapped[str | None] = mapped_column(Text)
    current_team: Mapped[list[str] | None] = mapped_column(JSON_DOCUMENT)
    current_assets: Mapped[list[str] | None] = mapped_column(JSON_DOCUMENT)
    budget_status: Mapped[str] = mapped_column(String(32), nullable=False, default="NOT_ASSESSED")
    known_unknowns: Mapped[list[str] | None] = mapped_column(JSON_DOCUMENT)
    evidence_requirements: Mapped[list[str] | None] = mapped_column(JSON_DOCUMENT)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_audit_events_tenant_campaign",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id", "workspace_id"],
            ["workspaces.tenant_id", "workspaces.campaign_id", "workspaces.id"],
            name="fk_audit_events_workspace_scope",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "workspace_id IS NULL OR campaign_id IS NOT NULL",
            name="ck_audit_events_workspace_requires_campaign",
        ),
        Index("ix_audit_events_tenant_occurred", "tenant_id", "occurred_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    campaign_id: Mapped[UUID | None] = mapped_column(Uuid)
    workspace_id: Mapped[UUID | None] = mapped_column(Uuid)
    principal_id: Mapped[UUID | None] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="RESTRICT")
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_id: Mapped[str] = mapped_column(String(255), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    previous_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "operation", "idempotency_key", name="uq_idempotency_scope_key"
        ),
        Index("ix_idempotency_records_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    principal_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    operation: Mapped[str] = mapped_column(String(160), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(255), nullable=False)
    request_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    response_payload: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_outbox_events_tenant_campaign",
            ondelete="RESTRICT",
        ),
        CheckConstraint(
            "status IN ('PENDING', 'PROCESSING', 'DELIVERED', 'DEAD_LETTER')",
            name="ck_outbox_events_status",
        ),
        Index("ix_outbox_events_pending", "status", "available_at"),
        Index(
            "ix_outbox_events_recoverable",
            "status",
            "lease_expires_at",
            "available_at",
        ),
        Index("ix_outbox_events_tenant_created", "tenant_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="RESTRICT"), nullable=False
    )
    campaign_id: Mapped[UUID | None] = mapped_column(Uuid)
    topic: Mapped[str] = mapped_column(String(160), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSON_DOCUMENT, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    lease_owner: Mapped[str | None] = mapped_column(String(255))
    lease_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(Text)


class StrategyWorkspace(Base, TimestampMixin):
    __tablename__ = "strategy_workspaces"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_strategy_workspaces_tenant_campaign",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["candidate_workspaces.tenant_id", "candidate_workspaces.campaign_id"],
            name="fk_strategy_workspaces_candidate_workspace",
            ondelete="RESTRICT",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["team_workspaces.tenant_id", "team_workspaces.campaign_id"],
            name="fk_strategy_workspaces_team_workspace",
            ondelete="RESTRICT",
        ),
        UniqueConstraint("tenant_id", "campaign_id", name="uq_strategy_workspaces_tenant_campaign"),
        UniqueConstraint("tenant_id", "id", name="uq_strategy_workspaces_tenant_id_id"),
        CheckConstraint("campaign_version >= 1", name="ck_strategy_campaign_version"),
        CheckConstraint("candidate_workspace_version >= 1", name="ck_strategy_candidate_version"),
        CheckConstraint("team_workspace_version >= 1", name="ck_strategy_team_version"),
        CheckConstraint("version >= 1", name="ck_strategy_workspace_version"),
        Index("ix_strategy_workspaces_tenant_status", "tenant_id", "campaign_id"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    campaign_version: Mapped[int] = mapped_column(Integer, nullable=False)
    candidate_workspace_version: Mapped[int] = mapped_column(Integer, nullable=False)
    team_workspace_version: Mapped[int] = mapped_column(Integer, nullable=False)
    known_role_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    evidence: Mapped[list[dict[str, object]] | None] = mapped_column(JSON, nullable=True)
    assumptions: Mapped[list[dict[str, object]] | None] = mapped_column(JSON, nullable=True)
    hypotheses: Mapped[list[dict[str, object]] | None] = mapped_column(JSON, nullable=True)
    options: Mapped[list[dict[str, object]] | None] = mapped_column(JSON, nullable=True)
    objectives: Mapped[list[dict[str, object]] | None] = mapped_column(JSON, nullable=True)
    contradictions: Mapped[list[dict[str, object]] | None] = mapped_column(JSON, nullable=True)
    red_team_findings: Mapped[list[dict[str, object]] | None] = mapped_column(JSON, nullable=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class StrategyDecisionReceipt(Base, TimestampMixin):
    __tablename__ = "strategy_decision_receipts"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_strategy_decisions_tenant_campaign",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "strategy_workspace_id"],
            ["strategy_workspaces.tenant_id", "strategy_workspaces.id"],
            name="fk_strategy_decisions_workspace",
            ondelete="CASCADE",
        ),
        UniqueConstraint(
            "tenant_id",
            "strategy_workspace_id",
            "workspace_version",
            name="uq_strategy_decisions_workspace_version",
        ),
        CheckConstraint("workspace_version >= 1", name="ck_strategy_decision_version"),
        Index(
            "ix_strategy_decisions_tenant_campaign_created",
            "tenant_id",
            "campaign_id",
            "created_at",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    strategy_workspace_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    workspace_version: Mapped[int] = mapped_column(Integer, nullable=False)
    selected_option_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    human_role_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    approval_receipt_id: Mapped[str] = mapped_column(String(180), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    __table_args__ = (
        ForeignKeyConstraint(
            ["tenant_id", "campaign_id"],
            ["campaigns.tenant_id", "campaigns.id"],
            name="fk_agent_runs_tenant_campaign",
            ondelete="CASCADE",
        ),
        ForeignKeyConstraint(
            ["tenant_id", "strategy_workspace_id"],
            ["strategy_workspaces.tenant_id", "strategy_workspaces.id"],
            name="fk_agent_runs_strategy_workspace",
            ondelete="CASCADE",
        ),
        UniqueConstraint("tenant_id", "id", name="uq_agent_runs_tenant_id_id"),
        CheckConstraint("strategy_workspace_version >= 1", name="ck_agent_runs_strategy_version"),
        CheckConstraint("status IN ('COMPLETED', 'REFUSED')", name="ck_agent_runs_status"),
        CheckConstraint("human_disposition = 'PENDING'", name="ck_agent_runs_human_pending"),
        CheckConstraint("authority_effect = 'NONE'", name="ck_agent_runs_authority_none"),
        CheckConstraint("external_effects = 'NONE'", name="ck_agent_runs_external_none"),
        CheckConstraint("prompt_tokens >= 0", name="ck_agent_runs_prompt_tokens"),
        CheckConstraint("output_tokens >= 0", name="ck_agent_runs_output_tokens"),
        CheckConstraint("latency_ms >= 0", name="ck_agent_runs_latency"),
        CheckConstraint("cost_micros >= 0", name="ck_agent_runs_cost"),
        Index("ix_agent_runs_tenant_campaign_created", "tenant_id", "campaign_id", "created_at"),
    )

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    campaign_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    strategy_workspace_id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), nullable=False)
    strategy_workspace_version: Mapped[int] = mapped_column(Integer, nullable=False)
    principal_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("principals.id", ondelete="RESTRICT"), nullable=False
    )
    purpose: Mapped[str] = mapped_column(String(80), nullable=False)
    instruction_digest: Mapped[str] = mapped_column(String(64), nullable=False)
    policy_id: Mapped[str] = mapped_column(String(160), nullable=False)
    policy_version: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_template_id: Mapped[str] = mapped_column(String(160), nullable=False)
    prompt_template_version: Mapped[str] = mapped_column(String(32), nullable=False)
    output_schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    prompt_digest: Mapped[str | None] = mapped_column(String(64))
    provider: Mapped[str | None] = mapped_column(String(80))
    model: Mapped[str | None] = mapped_column(String(160))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    refusal_code: Mapped[str | None] = mapped_column(String(100))
    refusal_detail: Mapped[str | None] = mapped_column(String(255))
    recommendation: Mapped[dict[str, object] | None] = mapped_column(JSON_DOCUMENT)
    evidence_refs: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False)
    option_refs: Mapped[list[str]] = mapped_column(JSON_DOCUMENT, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_micros: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    human_disposition: Mapped[str] = mapped_column(String(32), nullable=False, default="PENDING")
    authority_effect: Mapped[str] = mapped_column(String(32), nullable=False, default="NONE")
    external_effects: Mapped[str] = mapped_column(String(32), nullable=False, default="NONE")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
