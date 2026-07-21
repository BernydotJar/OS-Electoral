from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from campaignos.data.audit import AuditScopeUnavailable
from campaignos.data.database import Database, TenantSession
from campaignos.data.models import (
    ApplicationSession,
    AuditEvent,
    Base,
    Campaign,
    IdempotencyRecord,
    IdentityInvitation,
    Membership,
    OutboxEvent,
    PermissionGrant,
    Principal,
    RoleAssignment,
    SupportAccessRequest,
    Tenant,
    Workspace,
)
from campaignos.identity.authorization import SqlAlchemyMembershipDirectory
from campaignos.identity.lifecycle import (
    IdentityLifecycleConflict,
    IdentityLifecycleDenied,
    IdentityLifecycleIdempotencyConflict,
    IdentityLifecycleUnavailable,
    IdentityLifecycleVersionConflict,
    SqlAlchemyIdentityLifecycle,
)
from campaignos.identity.lifecycle_contracts import (
    InvitationCreate,
    SessionRevoke,
    SupportAccessApprove,
    SupportAccessCreate,
    SupportAccessRevoke,
)
from campaignos.identity.models import AuthenticatedPrincipal

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")
WORKSPACE_ID = UUID("44444444-4444-4444-8444-444444444444")
ACTOR_ID = UUID("55555555-5555-4555-8555-555555555555")
APPROVER_ID = UUID("66666666-6666-4666-8666-666666666666")
SUPPORT_ID = UUID("77777777-7777-4777-8777-777777777777")
GRANT_ID = UUID("88888888-8888-4888-8888-888888888888")
NOW = datetime(2026, 7, 21, 12, tzinfo=UTC)
ISSUER = "https://identity.example.test/"


def as_utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


@pytest.fixture
def database() -> Iterator[Database]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(
        bind=engine,
        class_=TenantSession,
        autoflush=False,
        expire_on_commit=False,
    )
    runtime = Database(engine=engine, _sessions=sessions)
    with runtime.tenant_transaction(TENANT_ID) as session:
        session.add_all(
            [
                Tenant(
                    id=TENANT_ID,
                    slug="tenant",
                    name="Identity Lifecycle Tenant",
                    status="ACTIVE",
                ),
                Principal(
                    id=ACTOR_ID,
                    issuer=ISSUER,
                    subject="actor",
                    display_name="Tenant Operator",
                    email="actor@example.test",
                ),
                Principal(
                    id=APPROVER_ID,
                    issuer=ISSUER,
                    subject="approver",
                    display_name="Tenant Approver",
                    email="approver@example.test",
                ),
                Principal(
                    id=SUPPORT_ID,
                    issuer=ISSUER,
                    subject="support-agent",
                    display_name="Support Agent",
                    email="support@example.test",
                ),
            ]
        )
        session.flush()
        session.add(
            Campaign(
                id=CAMPAIGN_ID,
                tenant_id=TENANT_ID,
                slug="campaign",
                name="Campaign",
                jurisdiction="Antigua Guatemala",
                stage="PRECAMPAIGN",
                status="ACTIVE",
                version=1,
            )
        )
        session.flush()
        session.add(
            Workspace(
                id=WORKSPACE_ID,
                tenant_id=TENANT_ID,
                campaign_id=CAMPAIGN_ID,
                slug="governance",
                name="Governance",
                status="ACTIVE",
                version=1,
            )
        )
    with runtime.tenant_transaction(OTHER_TENANT_ID) as session:
        session.add(
            Tenant(
                id=OTHER_TENANT_ID,
                slug="other",
                name="Other Tenant",
                status="ACTIVE",
            )
        )
    try:
        yield runtime
    finally:
        runtime.dispose()


def authenticated(
    subject: str,
    email: str,
    *,
    session_id: str | None = None,
) -> AuthenticatedPrincipal:
    authenticated_at = datetime.now(UTC)
    return AuthenticatedPrincipal(
        subject=subject,
        issuer=ISSUER,
        audience="campaignos-test",
        display_name=subject.title(),
        email=email,
        email_verified=True,
        session_id=session_id,
        authenticated_at=authenticated_at,
        expires_at=(authenticated_at + timedelta(hours=1) if session_id is not None else None),
    )


def create_invitation(
    database: Database,
    *,
    email: str = "invitee@example.test",
    campaign_id: UUID | None = CAMPAIGN_ID,
    key: str = "invite-create-1",
):
    return SqlAlchemyIdentityLifecycle(database).create_invitation(
        TENANT_ID,
        request=InvitationCreate(
            email=email,
            campaign_id=campaign_id,
            expires_in_hours=24,
        ),
        principal_id=ACTOR_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-invitation-create",
        authorization_purpose="Invite tenant member",
        correlation_id="invitation-create-correlation",
        idempotency_key=key,
    )


def test_create_invitation_is_atomic_inert_and_replayable(database: Database) -> None:
    first = create_invitation(database)
    replay = create_invitation(database)

    assert replay == first
    assert first.delivery_plan.delivery_state == "NOT_SENT"
    assert first.delivery_plan.external_effects == "NONE"
    with database.tenant_transaction(TENANT_ID) as session:
        invitation = session.get(IdentityInvitation, first.invitation.id)
        audit = session.get(AuditEvent, first.audit_event_id)
        outbox = session.get(OutboxEvent, first.outbox_event_id)
        assert invitation is not None
        assert invitation.status == "PENDING"
        assert invitation.email == "invitee@example.test"
        assert audit is not None
        assert audit.event_type == "identity.invitation.created"
        assert audit.payload["external_effects"] == "NONE"
        assert outbox is not None
        assert outbox.topic == "identity.invitation.planned"
        assert outbox.payload["delivery_state"] == "NOT_SENT"
        assert session.scalar(select(func.count()).select_from(IdentityInvitation)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1
        serialized = str(invitation.__dict__).lower()
        assert "password" not in serialized
        assert "token" not in serialized

    with pytest.raises(IdentityLifecycleIdempotencyConflict):
        create_invitation(database, email="different@example.test")
    with pytest.raises(IdentityLifecycleConflict, match="pending invitation"):
        create_invitation(database, key="invite-create-2")


def test_invitation_acceptance_creates_empty_membership_once(database: Database) -> None:
    invitation = create_invitation(database)
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    principal = authenticated("invitee", "INVITEE@example.test")

    first = lifecycle.accept_invitation(
        TENANT_ID,
        invitation.invitation.id,
        principal=principal,
        correlation_id="invitation-accept-correlation",
        idempotency_key="invite-accept-1",
    )
    replay = lifecycle.accept_invitation(
        TENANT_ID,
        invitation.invitation.id,
        principal=principal,
        correlation_id="ignored-replay-correlation",
        idempotency_key="invite-accept-1",
    )

    assert replay == first
    assert first.invitation.status == "ACCEPTED"
    assert first.membership.status == "ACTIVE"
    with database.tenant_transaction(TENANT_ID) as session:
        membership = session.get(Membership, first.membership.id)
        application_principal = session.get(Principal, first.principal_id)
        assert membership is not None
        assert membership.campaign_id == CAMPAIGN_ID
        assert application_principal is not None
        assert application_principal.subject == "invitee"
        assert session.scalar(select(func.count()).select_from(RoleAssignment)) == 0
        assert session.scalar(select(func.count()).select_from(PermissionGrant)) == 0
        audit = session.get(AuditEvent, first.audit_event_id)
        assert audit is not None
        assert audit.payload["implicit_roles"] == []
        assert audit.payload["implicit_grants"] == []
        assert session.scalar(select(func.count()).select_from(Membership)) == 1

    with pytest.raises(IdentityLifecycleConflict, match="not pending"):
        lifecycle.accept_invitation(
            TENANT_ID,
            invitation.invitation.id,
            principal=principal,
            correlation_id="different-key",
            idempotency_key="invite-accept-2",
        )


def test_invitation_acceptance_rejects_wrong_identity_and_expiry(database: Database) -> None:
    invitation = create_invitation(database)
    lifecycle = SqlAlchemyIdentityLifecycle(database)

    with pytest.raises(IdentityLifecycleDenied, match="does not match"):
        lifecycle.accept_invitation(
            TENANT_ID,
            invitation.invitation.id,
            principal=authenticated("attacker", "attacker@example.test"),
            correlation_id="wrong-identity",
            idempotency_key="wrong-identity-key",
        )
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(IdentityInvitation, invitation.invitation.id)
        assert row is not None and row.status == "PENDING"
        assert session.scalar(select(func.count()).select_from(Membership)) == 0
        row.expires_at = datetime.now(UTC) - timedelta(minutes=1)

    with pytest.raises(IdentityLifecycleConflict, match="expired"):
        lifecycle.accept_invitation(
            TENANT_ID,
            invitation.invitation.id,
            principal=authenticated("invitee", "invitee@example.test"),
            correlation_id="expired",
            idempotency_key="expired-key",
        )

    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(IdentityInvitation, invitation.invitation.id)
        assert row is not None
        assert row.status == "EXPIRED"
        assert row.version == 2
        assert (
            session.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(
                    AuditEvent.event_type == "identity.invitation.expired",
                    AuditEvent.resource_id == str(invitation.invitation.id),
                )
            )
            == 1
        )
        assert session.scalar(select(func.count()).select_from(Membership)) == 0

    replacement = create_invitation(database, key="invite-create-after-expiry")
    assert replacement.invitation.id != invitation.invitation.id
    with database.tenant_transaction(TENANT_ID) as session:
        statuses = dict(
            session.execute(
                select(IdentityInvitation.id, IdentityInvitation.status).order_by(
                    IdentityInvitation.created_at,
                    IdentityInvitation.id,
                )
            ).all()
        )
        assert statuses == {
            invitation.invitation.id: "EXPIRED",
            replacement.invitation.id: "PENDING",
        }


@pytest.mark.parametrize("email_verified", [None, False])
def test_invitation_acceptance_requires_verified_email(
    database: Database,
    email_verified: bool | None,
) -> None:
    invitation = create_invitation(database)
    principal = authenticated("invitee", "invitee@example.test").model_copy(
        update={"email_verified": email_verified}
    )

    with pytest.raises(IdentityLifecycleDenied, match="verified email"):
        SqlAlchemyIdentityLifecycle(database).accept_invitation(
            TENANT_ID,
            invitation.invitation.id,
            principal=principal,
            correlation_id="unverified-invitation-acceptance",
            idempotency_key="unverified-invitation-acceptance",
        )

    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(IdentityInvitation, invitation.invitation.id)
        assert row is not None
        assert row.status == "PENDING"
        assert session.scalar(select(func.count()).select_from(Membership)) == 0


def test_invitation_revocation_uses_optimistic_version_and_audit(database: Database) -> None:
    invitation = create_invitation(database)
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    revoked = lifecycle.revoke_invitation(
        TENANT_ID,
        invitation.invitation.id,
        expected_version=1,
        principal_id=ACTOR_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-invitation-revoke",
        authorization_purpose="Revoke tenant invitation",
        correlation_id="invitation-revoke",
    )

    assert revoked.invitation.status == "REVOKED"
    assert revoked.invitation.version == 2
    with pytest.raises(IdentityLifecycleVersionConflict):
        lifecycle.revoke_invitation(
            TENANT_ID,
            invitation.invitation.id,
            expected_version=1,
            principal_id=ACTOR_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-invitation-revoke",
            authorization_purpose="Revoke tenant invitation",
            correlation_id="stale",
        )


def test_session_registry_stores_digest_refreshes_and_revokes_self(database: Database) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    principal = authenticated("actor", "actor@example.test", session_id="provider-session-raw")
    first = lifecycle.register_session(
        TENANT_ID,
        principal=principal,
        application_principal_id=ACTOR_ID,
        correlation_id="session-register",
    )
    refreshed = lifecycle.register_session(
        TENANT_ID,
        principal=principal,
        application_principal_id=ACTOR_ID,
        correlation_id="session-refresh",
    )

    assert first.created is True
    assert refreshed.created is False
    assert refreshed.session.id == first.session.id
    assert refreshed.session.version == 2
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(ApplicationSession, first.session.id)
        assert row is not None
        assert row.provider_session_digest != "provider-session-raw"
        assert "provider-session-raw" not in str(row.__dict__)

    revoked = lifecycle.revoke_session(
        TENANT_ID,
        first.session.id,
        request=SessionRevoke(reason="User requested sign out", expected_version=2),
        principal_id=ACTOR_ID,
        allow_cross_principal=False,
        authorization_grant_id=None,
        approval_receipt_id=None,
        authorization_purpose="Revoke own application session",
        correlation_id="session-revoke",
    )
    assert revoked.session.status == "REVOKED"
    assert revoked.provider_revocation_state == "NOT_EXECUTED"


def test_expired_session_is_persisted_and_audited(database: Database) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    provider_session_id = "provider-session-that-must-not-be-stored"
    first = lifecycle.register_session(
        TENANT_ID,
        principal=authenticated(
            "actor",
            "actor@example.test",
            session_id=provider_session_id,
        ),
        application_principal_id=ACTOR_ID,
        correlation_id="session-expiry-register",
    )
    expired_at = datetime.now(UTC) - timedelta(hours=1)
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(ApplicationSession, first.session.id)
        assert row is not None
        row.authenticated_at = expired_at - timedelta(hours=1)
        row.last_seen_at = expired_at - timedelta(minutes=30)
        row.expires_at = expired_at

    with pytest.raises(IdentityLifecycleConflict, match="expired"):
        lifecycle.register_session(
            TENANT_ID,
            principal=authenticated(
                "actor",
                "actor@example.test",
                session_id=provider_session_id,
            ),
            application_principal_id=ACTOR_ID,
            correlation_id="session-expiry-observed",
        )

    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(ApplicationSession, first.session.id)
        assert row is not None
        assert row.status == "EXPIRED"
        assert row.version == 2
        expiry_audit = session.scalar(
            select(AuditEvent).where(
                AuditEvent.event_type == "identity.session.expired",
                AuditEvent.resource_id == str(first.session.id),
            )
        )
        assert expiry_audit is not None
        serialized = str((row.__dict__, expiry_audit.payload))
        assert provider_session_id not in serialized


def test_cross_principal_session_revocation_requires_explicit_authority(
    database: Database,
) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    target_session = lifecycle.register_session(
        TENANT_ID,
        principal=authenticated(
            "support-agent",
            "support@example.test",
            session_id="support-session",
        ),
        application_principal_id=SUPPORT_ID,
        correlation_id="support-session-register",
    )

    with pytest.raises(IdentityLifecycleDenied, match="not authorized"):
        lifecycle.revoke_session(
            TENANT_ID,
            target_session.session.id,
            request=SessionRevoke(reason="Administrative response", expected_version=1),
            principal_id=ACTOR_ID,
            allow_cross_principal=False,
            authorization_grant_id=None,
            approval_receipt_id=None,
            authorization_purpose="Revoke tenant application session",
            correlation_id="denied-session-revoke",
        )
    revoked = lifecycle.revoke_session(
        TENANT_ID,
        target_session.session.id,
        request=SessionRevoke(reason="Administrative response", expected_version=1),
        principal_id=ACTOR_ID,
        allow_cross_principal=True,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-session-revoke",
        authorization_purpose="Revoke tenant application session",
        correlation_id="authorized-session-revoke",
    )
    assert revoked.session.status == "REVOKED"


def test_membership_revocation_disables_grants_roles_and_sessions(database: Database) -> None:
    membership_id = UUID("99999999-9999-4999-8999-999999999999")
    session_id = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
    with database.tenant_transaction(TENANT_ID) as session:
        session.add(
            Membership(
                id=membership_id,
                tenant_id=TENANT_ID,
                principal_id=SUPPORT_ID,
                campaign_id=CAMPAIGN_ID,
                status="ACTIVE",
                valid_from=NOW,
                version=1,
            )
        )
        session.flush()
        session.add_all(
            [
                RoleAssignment(
                    tenant_id=TENANT_ID,
                    membership_id=membership_id,
                    role="operator",
                    assigned_by_principal_id=ACTOR_ID,
                ),
                PermissionGrant(
                    tenant_id=TENANT_ID,
                    membership_id=membership_id,
                    campaign_id=CAMPAIGN_ID,
                    action="read",
                    resource_type="campaign",
                    resource_id=str(CAMPAIGN_ID),
                    purpose="Operate assigned campaign",
                    granted_by_principal_id=ACTOR_ID,
                    approval_receipt_id="approval-membership",
                ),
                ApplicationSession(
                    id=session_id,
                    tenant_id=TENANT_ID,
                    principal_id=SUPPORT_ID,
                    provider_session_digest="b" * 64,
                    status="ACTIVE",
                    authenticated_at=NOW,
                    last_seen_at=NOW,
                    expires_at=NOW + timedelta(hours=1),
                    version=1,
                ),
            ]
        )

    evidence = SqlAlchemyIdentityLifecycle(database).revoke_membership(
        TENANT_ID,
        membership_id,
        expected_version=1,
        reason="Operator access is no longer required",
        principal_id=ACTOR_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-membership-revoke",
        authorization_purpose="Revoke tenant membership",
        correlation_id="membership-revoke",
    )

    assert evidence.membership.status == "REVOKED"
    assert evidence.revoked_grant_count == 1
    assert evidence.expired_role_count == 1
    assert evidence.revoked_session_count == 1
    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(PermissionGrant.status)) == "REVOKED"
        assert session.scalar(select(RoleAssignment.expires_at)) is not None
        assert session.get(ApplicationSession, session_id).status == "REVOKED"  # type: ignore[union-attr]
        outbox = session.get(OutboxEvent, evidence.outbox_event_id)
        assert outbox is not None
        assert outbox.payload["provider_revocation_state"] == "NOT_EXECUTED"


def test_support_access_requires_separate_approver_and_expires_exact_grant(
    database: Database,
) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    requested = lifecycle.request_support_access(
        TENANT_ID,
        request=SupportAccessCreate(
            target_principal_id=SUPPORT_ID,
            campaign_id=CAMPAIGN_ID,
            workspace_id=WORKSPACE_ID,
            action="read",
            resource_type="campaign_readiness",
            resource_id=str(CAMPAIGN_ID),
            purpose="Diagnose assigned campaign",
            reason="Reproduce a customer-reported authorization defect.",
            expires_in_minutes=30,
        ),
        principal_id=ACTOR_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-support-request",
        authorization_purpose="Request time-bound support access",
        correlation_id="support-request",
        idempotency_key="support-request-1",
    )
    replay = lifecycle.request_support_access(
        TENANT_ID,
        request=SupportAccessCreate(
            target_principal_id=SUPPORT_ID,
            campaign_id=CAMPAIGN_ID,
            workspace_id=WORKSPACE_ID,
            action="read",
            resource_type="campaign_readiness",
            resource_id=str(CAMPAIGN_ID),
            purpose="Diagnose assigned campaign",
            reason="Reproduce a customer-reported authorization defect.",
            expires_in_minutes=30,
        ),
        principal_id=ACTOR_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-support-request",
        authorization_purpose="Request time-bound support access",
        correlation_id="support-request-replay",
        idempotency_key="support-request-1",
    )
    assert replay == requested

    with pytest.raises(IdentityLifecycleDenied, match="separation of duty"):
        lifecycle.approve_support_access(
            TENANT_ID,
            requested.request.id,
            request=SupportAccessApprove(expected_version=1),
            principal_id=ACTOR_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-support",
            authorization_purpose="Approve time-bound support access",
            correlation_id="self-approval",
        )
    approved = lifecycle.approve_support_access(
        TENANT_ID,
        requested.request.id,
        request=SupportAccessApprove(expected_version=1),
        principal_id=APPROVER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-support",
        authorization_purpose="Approve time-bound support access",
        correlation_id="support-approval",
    )

    assert approved.request.status == "APPROVED"
    assert approved.request.created_membership is True
    assert approved.request.permission_grant_id is not None
    with database.tenant_transaction(TENANT_ID) as session:
        membership = session.get(Membership, approved.request.membership_id)
        role = session.get(RoleAssignment, approved.request.role_assignment_id)
        grant = session.get(PermissionGrant, approved.request.permission_grant_id)
        assert (
            membership is not None and as_utc(membership.expires_at) == approved.request.expires_at
        )
        assert role is not None and role.role == f"time_bound_support:{requested.request.id}"
        assert as_utc(role.expires_at) == approved.request.expires_at
        assert grant is not None
        assert grant.action == "read"
        assert grant.resource_type == "campaign_readiness"
        assert grant.purpose == "Diagnose assigned campaign"
        assert as_utc(grant.expires_at) == approved.request.expires_at

    context = SqlAlchemyMembershipDirectory(database).load(
        TENANT_ID,
        authenticated("support-agent", "support@example.test"),
        evaluated_at=approved.request.requested_at + timedelta(minutes=1),
    )
    assert context.permits(
        action="read",
        resource_type="campaign_readiness",
        resource_id=str(CAMPAIGN_ID),
        purpose="Diagnose assigned campaign",
        campaign_id=CAMPAIGN_ID,
        workspace_id=WORKSPACE_ID,
    )

    revoked = lifecycle.revoke_support_access(
        TENANT_ID,
        requested.request.id,
        request=SupportAccessRevoke(
            reason="Customer support session completed",
            expected_version=2,
        ),
        principal_id=APPROVER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-support-revoke",
        authorization_purpose="Revoke time-bound support access",
        correlation_id="support-revoke",
    )
    assert revoked.request.status == "REVOKED"
    with database.tenant_transaction(TENANT_ID) as session:
        membership = session.get(Membership, revoked.request.membership_id)
        grant = session.get(PermissionGrant, revoked.request.permission_grant_id)
        role = session.get(RoleAssignment, revoked.request.role_assignment_id)
        assert membership is not None and membership.status == "REVOKED"
        assert grant is not None and grant.status == "REVOKED"
        assert role is not None and role.expires_at is not None

    requested_again = lifecycle.request_support_access(
        TENANT_ID,
        request=SupportAccessCreate(
            target_principal_id=SUPPORT_ID,
            campaign_id=CAMPAIGN_ID,
            workspace_id=WORKSPACE_ID,
            action="read",
            resource_type="campaign_readiness",
            resource_id=str(CAMPAIGN_ID),
            purpose="Diagnose assigned campaign",
            reason="Continue the same customer-authorized support investigation.",
            expires_in_minutes=30,
        ),
        principal_id=ACTOR_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-support-request-2",
        authorization_purpose="Request time-bound support access",
        correlation_id="support-request-2",
        idempotency_key="support-request-2",
    )
    approved_again = lifecycle.approve_support_access(
        TENANT_ID,
        requested_again.request.id,
        request=SupportAccessApprove(expected_version=1),
        principal_id=APPROVER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-support-2",
        authorization_purpose="Approve time-bound support access",
        correlation_id="support-approval-2",
    )
    assert approved_again.request.membership_id == approved.request.membership_id
    assert approved_again.request.role_assignment_id != approved.request.role_assignment_id
    assert approved_again.request.permission_grant_id == approved.request.permission_grant_id
    with database.tenant_transaction(TENANT_ID) as session:
        grants = list(
            session.scalars(
                select(PermissionGrant).where(
                    PermissionGrant.tenant_id == TENANT_ID,
                    PermissionGrant.membership_id == approved_again.request.membership_id,
                )
            )
        )
        assert len(grants) == 1
        assert grants[0].status == "ACTIVE"
        assert grants[0].approval_receipt_id == "approval-support-2"
        requests = list(
            session.scalars(
                select(SupportAccessRequest).where(
                    SupportAccessRequest.tenant_id == TENANT_ID,
                    SupportAccessRequest.membership_id == approved_again.request.membership_id,
                )
            )
        )
        assert len(requests) == 2
        assert sorted(request.status for request in requests) == ["APPROVED", "REVOKED"]
        roles = list(
            session.scalars(
                select(RoleAssignment).where(
                    RoleAssignment.tenant_id == TENANT_ID,
                    RoleAssignment.membership_id == approved_again.request.membership_id,
                )
            )
        )
        assert len(roles) == 2


def test_support_revocation_preserves_preexisting_membership_and_access(
    database: Database,
) -> None:
    membership = Membership(
        tenant_id=TENANT_ID,
        principal_id=SUPPORT_ID,
        campaign_id=CAMPAIGN_ID,
        status="ACTIVE",
        valid_from=NOW,
        version=1,
    )
    with database.tenant_transaction(TENANT_ID) as session:
        session.add(membership)
        session.flush()
        unrelated_role = RoleAssignment(
            tenant_id=TENANT_ID,
            membership_id=membership.id,
            role="operator",
            assigned_by_principal_id=ACTOR_ID,
        )
        unrelated_grant = PermissionGrant(
            tenant_id=TENANT_ID,
            membership_id=membership.id,
            campaign_id=CAMPAIGN_ID,
            action="read",
            resource_type="campaign",
            resource_id=str(CAMPAIGN_ID),
            purpose="Operate assigned campaign",
            granted_by_principal_id=ACTOR_ID,
            approval_receipt_id="approval-preexisting-access",
        )
        session.add_all([unrelated_role, unrelated_grant])
        session.flush()
        unrelated_role_id = unrelated_role.id
        unrelated_grant_id = unrelated_grant.id

    lifecycle = SqlAlchemyIdentityLifecycle(database)
    requested = lifecycle.request_support_access(
        TENANT_ID,
        request=SupportAccessCreate(
            target_principal_id=SUPPORT_ID,
            campaign_id=CAMPAIGN_ID,
            workspace_id=WORKSPACE_ID,
            action="read",
            resource_type="campaign_readiness",
            resource_id=str(CAMPAIGN_ID),
            purpose="Diagnose assigned campaign",
            reason="Diagnose one customer-reported readiness defect.",
            expires_in_minutes=30,
        ),
        principal_id=ACTOR_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-support-request-existing-membership",
        authorization_purpose="Request time-bound support access",
        correlation_id="support-request-existing-membership",
        idempotency_key="support-request-existing-membership",
    )
    approved = lifecycle.approve_support_access(
        TENANT_ID,
        requested.request.id,
        request=SupportAccessApprove(expected_version=1),
        principal_id=APPROVER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-support-existing-membership",
        authorization_purpose="Approve time-bound support access",
        correlation_id="support-approve-existing-membership",
    )
    assert approved.request.created_membership is False
    assert approved.request.membership_id == membership.id

    revoked = lifecycle.revoke_support_access(
        TENANT_ID,
        requested.request.id,
        request=SupportAccessRevoke(
            reason="Support investigation completed",
            expected_version=2,
        ),
        principal_id=APPROVER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-support-revoke-existing-membership",
        authorization_purpose="Revoke time-bound support access",
        correlation_id="support-revoke-existing-membership",
    )

    with database.tenant_transaction(TENANT_ID) as session:
        persisted_membership = session.get(Membership, membership.id)
        persisted_unrelated_role = session.get(RoleAssignment, unrelated_role_id)
        persisted_unrelated_grant = session.get(PermissionGrant, unrelated_grant_id)
        support_role = session.get(RoleAssignment, revoked.request.role_assignment_id)
        support_grant = session.get(PermissionGrant, revoked.request.permission_grant_id)
        assert persisted_membership is not None
        assert persisted_membership.status == "ACTIVE"
        assert persisted_membership.revoked_at is None
        assert persisted_unrelated_role is not None
        assert persisted_unrelated_role.expires_at is None
        assert persisted_unrelated_grant is not None
        assert persisted_unrelated_grant.status == "ACTIVE"
        assert support_role is not None
        assert support_role.expires_at is not None
        assert support_grant is not None
        assert support_grant.status == "REVOKED"


def test_expired_support_access_is_persisted_and_replacement_is_allowed(
    database: Database,
) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    requested = lifecycle.request_support_access(
        TENANT_ID,
        request=SupportAccessCreate(
            target_principal_id=SUPPORT_ID,
            campaign_id=CAMPAIGN_ID,
            workspace_id=WORKSPACE_ID,
            action="read",
            resource_type="campaign_readiness",
            resource_id=str(CAMPAIGN_ID),
            purpose="Diagnose assigned campaign",
            reason="Investigate an expiring customer support incident.",
            expires_in_minutes=30,
        ),
        principal_id=ACTOR_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-support-expiry-request",
        authorization_purpose="Request time-bound support access",
        correlation_id="support-expiry-request",
        idempotency_key="support-expiry-request",
    )
    approved = lifecycle.approve_support_access(
        TENANT_ID,
        requested.request.id,
        request=SupportAccessApprove(expected_version=1),
        principal_id=APPROVER_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-support-expiry",
        authorization_purpose="Approve time-bound support access",
        correlation_id="support-expiry-approve",
    )
    expired_at = datetime.now(UTC) - timedelta(hours=1)
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(SupportAccessRequest, approved.request.id)
        membership = session.get(Membership, approved.request.membership_id)
        role = session.get(RoleAssignment, approved.request.role_assignment_id)
        grant = session.get(PermissionGrant, approved.request.permission_grant_id)
        assert row is not None
        assert membership is not None
        assert role is not None
        assert grant is not None
        row.requested_at = expired_at - timedelta(hours=1)
        row.expires_at = expired_at
        membership.valid_from = expired_at - timedelta(hours=1)
        membership.expires_at = expired_at
        role.expires_at = expired_at
        grant.valid_from = expired_at - timedelta(hours=1)
        grant.expires_at = expired_at

    replacement = lifecycle.request_support_access(
        TENANT_ID,
        request=SupportAccessCreate(
            target_principal_id=SUPPORT_ID,
            campaign_id=CAMPAIGN_ID,
            workspace_id=WORKSPACE_ID,
            action="read",
            resource_type="campaign_readiness",
            resource_id=str(CAMPAIGN_ID),
            purpose="Diagnose assigned campaign",
            reason="Continue the customer-authorized investigation after expiry.",
            expires_in_minutes=30,
        ),
        principal_id=ACTOR_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-support-expiry-replacement",
        authorization_purpose="Request time-bound support access",
        correlation_id="support-expiry-replacement",
        idempotency_key="support-expiry-replacement",
    )

    assert replacement.request.id != approved.request.id
    assert replacement.request.status == "PENDING"
    with database.tenant_transaction(TENANT_ID) as session:
        expired_request = session.get(SupportAccessRequest, approved.request.id)
        expired_grant = session.get(PermissionGrant, approved.request.permission_grant_id)
        assert expired_request is not None
        assert expired_request.status == "EXPIRED"
        assert expired_request.version == 3
        assert expired_grant is not None
        assert expired_grant.status == "EXPIRED"
        assert (
            session.scalar(
                select(func.count())
                .select_from(AuditEvent)
                .where(
                    AuditEvent.event_type == "identity.support_access.expired",
                    AuditEvent.resource_id == str(approved.request.id),
                )
            )
            == 1
        )


def test_invitation_audit_failure_rolls_back_all_rows(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_audit(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AuditScopeUnavailable("synthetic audit failure")

    monkeypatch.setattr("campaignos.identity.lifecycle.append_audit_event", fail_audit)
    with pytest.raises(IdentityLifecycleUnavailable):
        create_invitation(database)

    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(IdentityInvitation)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 0
        assert session.scalar(select(func.count()).select_from(SupportAccessRequest)) == 0


def test_scope_key_drift_is_rejected_by_database_constraints(database: Database) -> None:
    with pytest.raises(IntegrityError):
        with database.tenant_transaction(TENANT_ID) as session:
            session.add(
                IdentityInvitation(
                    tenant_id=TENANT_ID,
                    campaign_id=CAMPAIGN_ID,
                    scope_key="TENANT",
                    email="drift@example.test",
                    status="PENDING",
                    purpose="Invite tenant member",
                    invited_by_principal_id=ACTOR_ID,
                    provider="LOCAL_NO_DELIVERY",
                    provider_reference="local:scope-drift",
                    expires_at=datetime.now(UTC) + timedelta(hours=1),
                    version=1,
                )
            )

    now = datetime.now(UTC)
    with pytest.raises(IntegrityError):
        with database.tenant_transaction(TENANT_ID) as session:
            session.add(
                SupportAccessRequest(
                    tenant_id=TENANT_ID,
                    requested_by_principal_id=ACTOR_ID,
                    target_principal_id=SUPPORT_ID,
                    campaign_id=CAMPAIGN_ID,
                    workspace_id=WORKSPACE_ID,
                    campaign_scope_key="TENANT",
                    workspace_scope_key="NONE",
                    action="read",
                    resource_type="campaign_readiness",
                    resource_id=str(CAMPAIGN_ID),
                    purpose="Diagnose assigned campaign",
                    reason="Reject corrupt scope-key redundancy.",
                    status="PENDING",
                    requested_at=now,
                    expires_at=now + timedelta(minutes=30),
                    created_membership=False,
                    version=1,
                )
            )


def test_pending_invitation_integrity_conflict_is_sanitized(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_create(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise IntegrityError(
            "insert",
            {},
            RuntimeError("uq_identity_invitations_pending_target"),
        )

    monkeypatch.setattr(SqlAlchemyIdentityLifecycle, "_create_invitation", fail_create)
    with pytest.raises(IdentityLifecycleConflict, match="pending invitation"):
        create_invitation(database)


def test_active_support_integrity_conflict_is_sanitized(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_request(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise IntegrityError(
            "insert",
            {},
            RuntimeError("uq_support_access_requests_active_target"),
        )

    monkeypatch.setattr(SqlAlchemyIdentityLifecycle, "_request_support_access", fail_request)
    with pytest.raises(IdentityLifecycleConflict, match="Active support access"):
        SqlAlchemyIdentityLifecycle(database).request_support_access(
            TENANT_ID,
            request=SupportAccessCreate(
                target_principal_id=SUPPORT_ID,
                campaign_id=CAMPAIGN_ID,
                workspace_id=WORKSPACE_ID,
                action="read",
                resource_type="campaign_readiness",
                resource_id=str(CAMPAIGN_ID),
                purpose="Diagnose assigned campaign",
                reason="Reproduce a customer-authorized support defect.",
                expires_in_minutes=30,
            ),
            principal_id=ACTOR_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-support-request",
            authorization_purpose="Request time-bound support access",
            correlation_id="support-request",
            idempotency_key="support-request-integrity",
        )
