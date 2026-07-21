from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from campaignos.data.audit import canonical_hash
from campaignos.data.database import Database, TenantSession
from campaignos.data.models import (
    ApplicationSession,
    Base,
    Campaign,
    IdentityInvitation,
    Membership,
    PermissionGrant,
    Principal,
    RoleAssignment,
    SupportAccessRequest,
    Tenant,
    Workspace,
)
from campaignos.identity.lifecycle import (
    IdentityLifecycleConflict,
    IdentityLifecycleDenied,
    IdentityLifecycleNotFound,
    IdentityLifecycleUnavailable,
    IdentityLifecycleVersionConflict,
    SqlAlchemyIdentityLifecycle,
    UnavailableIdentityLifecycle,
)
from campaignos.identity.lifecycle_contracts import (
    InvitationCreate,
    InvitationCreateEvidence,
    SessionRevoke,
    SupportAccessApprove,
    SupportAccessCreate,
    SupportAccessEvidence,
    SupportAccessRevoke,
)
from campaignos.identity.models import AuthenticatedPrincipal

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")
WORKSPACE_ID = UUID("44444444-4444-4444-8444-444444444444")
ACTOR_ID = UUID("55555555-5555-4555-8555-555555555555")
APPROVER_ID = UUID("66666666-6666-4666-8666-666666666666")
TARGET_ID = UUID("77777777-7777-4777-8777-777777777777")
DISABLED_ID = UUID("88888888-8888-4888-8888-888888888888")
AUTHORIZATION_GRANT_ID = UUID("99999999-9999-4999-8999-999999999999")
ISSUER = "https://identity.example.test/"


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
    now = datetime.now(UTC)
    with runtime.tenant_transaction(TENANT_ID) as session:
        session.add_all(
            [
                Tenant(id=TENANT_ID, slug="tenant", name="Tenant", status="ACTIVE"),
                Principal(
                    id=ACTOR_ID,
                    issuer=ISSUER,
                    subject="actor",
                    email="actor@example.test",
                ),
                Principal(
                    id=APPROVER_ID,
                    issuer=ISSUER,
                    subject="approver",
                    email="approver@example.test",
                ),
                Principal(
                    id=TARGET_ID,
                    issuer=ISSUER,
                    subject="target",
                    email="target@example.test",
                ),
                Principal(
                    id=DISABLED_ID,
                    issuer=ISSUER,
                    subject="disabled",
                    email="disabled@example.test",
                    disabled_at=now,
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
                name="Other",
                status="SUSPENDED",
            )
        )
    try:
        yield runtime
    finally:
        runtime.dispose()


def identity(
    subject: str,
    email: str,
    *,
    session_id: str | None = None,
    expires_at: datetime | None = None,
) -> AuthenticatedPrincipal:
    authenticated_at = datetime.now(UTC) - timedelta(minutes=1)
    effective_expiry = expires_at
    if effective_expiry is None and session_id is not None:
        effective_expiry = authenticated_at + timedelta(hours=1)
    return AuthenticatedPrincipal(
        subject=subject,
        issuer=ISSUER,
        audience="campaignos-test",
        email=email,
        email_verified=True,
        session_id=session_id,
        authenticated_at=authenticated_at,
        expires_at=effective_expiry,
    )


def invitation_request(
    *,
    email: str = "invitee@example.test",
    campaign_id: UUID | None = CAMPAIGN_ID,
) -> InvitationCreate:
    return InvitationCreate(email=email, campaign_id=campaign_id, expires_in_hours=24)


def create_invitation(
    database: Database,
    *,
    email: str = "invitee@example.test",
    campaign_id: UUID | None = CAMPAIGN_ID,
    key: str | None = None,
) -> InvitationCreateEvidence:
    return SqlAlchemyIdentityLifecycle(database).create_invitation(
        TENANT_ID,
        request=invitation_request(email=email, campaign_id=campaign_id),
        principal_id=ACTOR_ID,
        authorization_grant_id=AUTHORIZATION_GRANT_ID,
        approval_receipt_id="approval-invitation",
        authorization_purpose="Invite tenant member",
        correlation_id="failure-suite-invitation",
        idempotency_key=key or f"invitation-{uuid4()}",
    )


def support_request(*, target_id: UUID = TARGET_ID) -> SupportAccessCreate:
    return SupportAccessCreate(
        target_principal_id=target_id,
        campaign_id=CAMPAIGN_ID,
        workspace_id=WORKSPACE_ID,
        action="read",
        resource_type="campaign_readiness",
        resource_id=str(CAMPAIGN_ID),
        purpose="Diagnose assigned campaign",
        reason="Investigate a customer-authorized support defect.",
        expires_in_minutes=30,
    )


def request_support(database: Database, *, key: str | None = None) -> SupportAccessEvidence:
    return SqlAlchemyIdentityLifecycle(database).request_support_access(
        TENANT_ID,
        request=support_request(),
        principal_id=ACTOR_ID,
        authorization_grant_id=AUTHORIZATION_GRANT_ID,
        approval_receipt_id="approval-support-request",
        authorization_purpose="Request time-bound support access",
        correlation_id="failure-suite-support-request",
        idempotency_key=key or f"support-{uuid4()}",
    )


def approve_support(database: Database, request_id: UUID) -> SupportAccessEvidence:
    return SqlAlchemyIdentityLifecycle(database).approve_support_access(
        TENANT_ID,
        request_id,
        request=SupportAccessApprove(expected_version=1),
        principal_id=APPROVER_ID,
        authorization_grant_id=AUTHORIZATION_GRANT_ID,
        approval_receipt_id="approval-support",
        authorization_purpose="Approve time-bound support access",
        correlation_id="failure-suite-support-approve",
    )


def seed_membership(
    database: Database,
    *,
    status: str = "ACTIVE",
    expires_at: datetime | None = None,
) -> UUID:
    membership_id = uuid4()
    with database.tenant_transaction(TENANT_ID) as session:
        session.add(
            Membership(
                id=membership_id,
                tenant_id=TENANT_ID,
                principal_id=TARGET_ID,
                campaign_id=CAMPAIGN_ID,
                status=status,
                valid_from=datetime.now(UTC) - timedelta(hours=1),
                expires_at=expires_at,
                revoked_at=(datetime.now(UTC) if status == "REVOKED" else None),
                version=1,
            )
        )
    return membership_id


def seed_invitation(
    database: Database,
    *,
    email: str = "invitee@example.test",
    status: str = "PENDING",
) -> UUID:
    invitation_id = uuid4()
    now = datetime.now(UTC)
    with database.tenant_transaction(TENANT_ID) as session:
        session.add(
            IdentityInvitation(
                id=invitation_id,
                tenant_id=TENANT_ID,
                campaign_id=CAMPAIGN_ID,
                scope_key=CAMPAIGN_ID.hex,
                email=email,
                status=status,
                purpose="Invite tenant member",
                invited_by_principal_id=ACTOR_ID,
                provider="LOCAL_NO_DELIVERY",
                provider_reference=f"local:{invitation_id}",
                expires_at=now + timedelta(hours=1),
                accepted_at=(now if status == "ACCEPTED" else None),
                version=1,
            )
        )
    return invitation_id


def test_unavailable_boundary_and_missing_scope_fail_closed(database: Database) -> None:
    missing_operation = "create_invitation"
    with pytest.raises(IdentityLifecycleUnavailable):
        getattr(UnavailableIdentityLifecycle(), missing_operation)

    lifecycle = SqlAlchemyIdentityLifecycle(database)
    with pytest.raises(IdentityLifecycleNotFound):
        lifecycle.create_invitation(
            OTHER_TENANT_ID,
            request=invitation_request(campaign_id=None),
            principal_id=ACTOR_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Invite tenant member",
            correlation_id="missing-tenant",
            idempotency_key="missing-tenant",
        )
    with pytest.raises(IdentityLifecycleNotFound):
        lifecycle.create_invitation(
            TENANT_ID,
            request=invitation_request(campaign_id=uuid4()),
            principal_id=ACTOR_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Invite tenant member",
            correlation_id="missing-campaign",
            idempotency_key="missing-campaign",
        )
    missing_workspace = support_request().model_copy(update={"workspace_id": uuid4()})
    with pytest.raises(IdentityLifecycleNotFound):
        lifecycle.request_support_access(
            TENANT_ID,
            request=missing_workspace,
            principal_id=ACTOR_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Request time-bound support access",
            correlation_id="missing-workspace",
            idempotency_key="missing-workspace",
        )
    with pytest.raises(IdentityLifecycleDenied):
        lifecycle.create_invitation(
            TENANT_ID,
            request=invitation_request(),
            principal_id=uuid4(),
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Invite tenant member",
            correlation_id="missing-principal",
            idempotency_key="missing-principal",
        )


def test_invitation_state_failures_and_revoked_membership_reactivation(database: Database) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    with pytest.raises(IdentityLifecycleNotFound):
        lifecycle.accept_invitation(
            TENANT_ID,
            uuid4(),
            principal=identity("invitee", "invitee@example.test"),
            correlation_id="missing-invitation",
            idempotency_key="missing-invitation",
        )
    with pytest.raises(IdentityLifecycleNotFound):
        lifecycle.revoke_invitation(
            TENANT_ID,
            uuid4(),
            expected_version=1,
            principal_id=ACTOR_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Revoke tenant invitation",
            correlation_id="missing-invitation-revoke",
        )

    accepted_id = seed_invitation(database, status="ACCEPTED")
    with pytest.raises(IdentityLifecycleConflict, match="not pending"):
        lifecycle.revoke_invitation(
            TENANT_ID,
            accepted_id,
            expected_version=1,
            principal_id=ACTOR_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Revoke tenant invitation",
            correlation_id="accepted-invitation-revoke",
        )

    active_membership_id = seed_membership(database)
    invitation = create_invitation(database, email="target@example.test")
    with pytest.raises(IdentityLifecycleConflict, match="Membership already exists"):
        lifecycle.accept_invitation(
            TENANT_ID,
            invitation.invitation.id,
            principal=identity("target", "target@example.test"),
            correlation_id="active-membership",
            idempotency_key="active-membership",
        )
    with database.tenant_transaction(TENANT_ID) as session:
        membership = session.get(Membership, active_membership_id)
        assert membership is not None
        membership.status = "REVOKED"
        membership.revoked_at = datetime.now(UTC)
    accepted = lifecycle.accept_invitation(
        TENANT_ID,
        invitation.invitation.id,
        principal=identity("target", "target@example.test"),
        correlation_id="reactivate-membership",
        idempotency_key="reactivate-membership",
    )
    assert accepted.membership.id == active_membership_id
    assert accepted.membership.status == "ACTIVE"
    assert accepted.membership.version == 2

    disabled_invitation = create_invitation(database, email="disabled@example.test")
    with pytest.raises(IdentityLifecycleDenied):
        lifecycle.accept_invitation(
            TENANT_ID,
            disabled_invitation.invitation.id,
            principal=identity("disabled", "disabled@example.test"),
            correlation_id="disabled-principal",
            idempotency_key="disabled-principal",
        )


def test_invitation_wrappers_sanitize_internal_failures(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)

    def unknown_integrity(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise IntegrityError("insert", {}, RuntimeError("unknown_constraint"))

    monkeypatch.setattr(SqlAlchemyIdentityLifecycle, "_create_invitation", unknown_integrity)
    with pytest.raises(IdentityLifecycleUnavailable):
        create_invitation(database)

    monkeypatch.undo()
    expired = seed_invitation(database)
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(IdentityInvitation, expired)
        assert row is not None
        row.expires_at = datetime.now(UTC) - timedelta(minutes=1)

    def fail_persist(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise ValueError("private persistence detail")

    monkeypatch.setattr(SqlAlchemyIdentityLifecycle, "_persist_invitation_expiry", fail_persist)
    with pytest.raises(IdentityLifecycleUnavailable):
        lifecycle.accept_invitation(
            TENANT_ID,
            expired,
            principal=identity("invitee", "invitee@example.test"),
            correlation_id="persist-failure",
            idempotency_key="persist-failure",
        )


def test_invitation_audit_failures_roll_back_accept_and_revoke(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    accept_id = seed_invitation(database)
    revoke_id = seed_invitation(database, email="revoke@example.test")

    def fail_audit(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise ValueError("private audit detail")

    monkeypatch.setattr("campaignos.identity.lifecycle.append_audit_event", fail_audit)
    with pytest.raises(IdentityLifecycleUnavailable):
        lifecycle.accept_invitation(
            TENANT_ID,
            accept_id,
            principal=identity("invitee", "invitee@example.test"),
            correlation_id="accept-audit-failure",
            idempotency_key="accept-audit-failure",
        )
    with pytest.raises(IdentityLifecycleUnavailable):
        lifecycle.revoke_invitation(
            TENANT_ID,
            revoke_id,
            expected_version=1,
            principal_id=ACTOR_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Revoke tenant invitation",
            correlation_id="revoke-audit-failure",
        )
    with database.tenant_transaction(TENANT_ID) as session:
        accepted_row = session.get(IdentityInvitation, accept_id)
        revoked_row = session.get(IdentityInvitation, revoke_id)
        assert accepted_row is not None and accepted_row.status == "PENDING"
        assert revoked_row is not None and revoked_row.status == "PENDING"


def test_expiry_persistence_helpers_reject_missing_rows(database: Database) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    with pytest.raises(IdentityLifecycleNotFound):
        lifecycle._persist_invitation_expiry(
            TENANT_ID,
            uuid4(),
            principal_id=ACTOR_ID,
            correlation_id="missing",
            observation="TEST",
        )
    with pytest.raises(IdentityLifecycleNotFound):
        lifecycle._persist_session_expiry(
            TENANT_ID,
            uuid4(),
            principal_id=ACTOR_ID,
            correlation_id="missing",
            observation="TEST",
        )
    with pytest.raises(IdentityLifecycleNotFound):
        lifecycle._persist_support_expiry(
            TENANT_ID,
            uuid4(),
            principal_id=ACTOR_ID,
            correlation_id="missing",
            observation="TEST",
        )


def test_session_registration_failure_states(database: Database) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    without_session = identity("actor", "actor@example.test")
    with pytest.raises(IdentityLifecycleDenied, match="identifier and expiry"):
        lifecycle.register_session(
            TENANT_ID,
            principal=without_session,
            application_principal_id=ACTOR_ID,
            correlation_id="missing-provider-session",
        )

    expired_at = datetime.now(UTC) - timedelta(seconds=1)
    expired = AuthenticatedPrincipal(
        subject="actor",
        issuer=ISSUER,
        audience="campaignos-test",
        email="actor@example.test",
        email_verified=True,
        session_id="expired-provider-session",
        authenticated_at=expired_at - timedelta(minutes=5),
        expires_at=expired_at,
    )
    with pytest.raises(IdentityLifecycleDenied, match="expired"):
        lifecycle.register_session(
            TENANT_ID,
            principal=expired,
            application_principal_id=ACTOR_ID,
            correlation_id="expired-provider-session",
        )

    with pytest.raises(IdentityLifecycleDenied, match="does not match"):
        lifecycle.register_session(
            TENANT_ID,
            principal=identity(
                "target",
                "target@example.test",
                session_id="mismatched-provider-session",
            ),
            application_principal_id=ACTOR_ID,
            correlation_id="mismatched-provider-session",
        )

    principal = identity("actor", "actor@example.test", session_id="collision")
    assert principal.expires_at is not None
    digest = canonical_hash(
        {
            "issuer": principal.issuer,
            "subject": principal.subject,
            "provider_session_id": principal.session_id,
        }
    )
    with database.tenant_transaction(TENANT_ID) as session:
        session.add(
            ApplicationSession(
                tenant_id=TENANT_ID,
                principal_id=TARGET_ID,
                provider_session_digest=digest,
                status="ACTIVE",
                authenticated_at=principal.authenticated_at,
                last_seen_at=datetime.now(UTC),
                expires_at=principal.expires_at,
                version=1,
            )
        )
    with pytest.raises(IdentityLifecycleUnavailable):
        lifecycle.register_session(
            TENANT_ID,
            principal=principal,
            application_principal_id=ACTOR_ID,
            correlation_id="digest-collision",
        )


def test_revoked_session_and_expiry_persistence_failure_fail_closed(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    principal = identity("actor", "actor@example.test", session_id="revoked-session")
    evidence = lifecycle.register_session(
        TENANT_ID,
        principal=principal,
        application_principal_id=ACTOR_ID,
        correlation_id="register-revoked-session",
    )
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(ApplicationSession, evidence.session.id)
        assert row is not None
        row.status = "REVOKED"
    with pytest.raises(IdentityLifecycleConflict, match="revoked"):
        lifecycle.register_session(
            TENANT_ID,
            principal=principal,
            application_principal_id=ACTOR_ID,
            correlation_id="observe-revoked-session",
        )

    expiring = identity("actor", "actor@example.test", session_id="expiry-failure")
    expiry_evidence = lifecycle.register_session(
        TENANT_ID,
        principal=expiring,
        application_principal_id=ACTOR_ID,
        correlation_id="register-expiry-failure",
    )
    expired_at = datetime.now(UTC) - timedelta(hours=1)
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(ApplicationSession, expiry_evidence.session.id)
        assert row is not None
        row.authenticated_at = expired_at - timedelta(hours=1)
        row.last_seen_at = expired_at
        row.expires_at = expired_at

    def fail_persist(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise ValueError("private persistence detail")

    monkeypatch.setattr(SqlAlchemyIdentityLifecycle, "_persist_session_expiry", fail_persist)
    with pytest.raises(IdentityLifecycleUnavailable):
        lifecycle.register_session(
            TENANT_ID,
            principal=expiring,
            application_principal_id=ACTOR_ID,
            correlation_id="persist-expiry-failure",
        )


def test_session_revoke_state_errors_and_audit_rollback(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    with pytest.raises(IdentityLifecycleNotFound):
        lifecycle.revoke_session(
            TENANT_ID,
            uuid4(),
            request=SessionRevoke(reason="Sign out", expected_version=1),
            principal_id=ACTOR_ID,
            allow_cross_principal=False,
            authorization_grant_id=None,
            approval_receipt_id=None,
            authorization_purpose="Revoke own application session",
            correlation_id="missing-session",
        )
    principal = identity("actor", "actor@example.test", session_id="revoke-errors")
    evidence = lifecycle.register_session(
        TENANT_ID,
        principal=principal,
        application_principal_id=ACTOR_ID,
        correlation_id="register-revoke-errors",
    )
    with pytest.raises(IdentityLifecycleVersionConflict):
        lifecycle.revoke_session(
            TENANT_ID,
            evidence.session.id,
            request=SessionRevoke(reason="Sign out", expected_version=2),
            principal_id=ACTOR_ID,
            allow_cross_principal=False,
            authorization_grant_id=None,
            approval_receipt_id=None,
            authorization_purpose="Revoke own application session",
            correlation_id="stale-session",
        )
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(ApplicationSession, evidence.session.id)
        assert row is not None
        row.status = "EXPIRED"
    with pytest.raises(IdentityLifecycleConflict, match="not active"):
        lifecycle.revoke_session(
            TENANT_ID,
            evidence.session.id,
            request=SessionRevoke(reason="Sign out", expected_version=1),
            principal_id=ACTOR_ID,
            allow_cross_principal=False,
            authorization_grant_id=None,
            approval_receipt_id=None,
            authorization_purpose="Revoke own application session",
            correlation_id="inactive-session",
        )

    rollback_principal = identity("actor", "actor@example.test", session_id="audit-rollback")
    rollback = lifecycle.register_session(
        TENANT_ID,
        principal=rollback_principal,
        application_principal_id=ACTOR_ID,
        correlation_id="register-audit-rollback",
    )

    def fail_audit(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise ValueError("private audit detail")

    monkeypatch.setattr("campaignos.identity.lifecycle.append_audit_event", fail_audit)
    with pytest.raises(IdentityLifecycleUnavailable):
        lifecycle.revoke_session(
            TENANT_ID,
            rollback.session.id,
            request=SessionRevoke(reason="Sign out", expected_version=1),
            principal_id=ACTOR_ID,
            allow_cross_principal=False,
            authorization_grant_id=None,
            approval_receipt_id=None,
            authorization_purpose="Revoke own application session",
            correlation_id="session-audit-failure",
        )
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(ApplicationSession, rollback.session.id)
        assert row is not None and row.status == "ACTIVE"


def test_membership_revoke_state_errors_and_audit_rollback(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    with pytest.raises(IdentityLifecycleConflict, match="reason"):
        lifecycle.revoke_membership(
            TENANT_ID,
            uuid4(),
            expected_version=1,
            reason="x",
            principal_id=ACTOR_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Revoke tenant membership",
            correlation_id="invalid-reason",
        )
    with pytest.raises(IdentityLifecycleNotFound):
        lifecycle.revoke_membership(
            TENANT_ID,
            uuid4(),
            expected_version=1,
            reason="No longer required",
            principal_id=ACTOR_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Revoke tenant membership",
            correlation_id="missing-membership",
        )
    membership_id = seed_membership(database)
    with pytest.raises(IdentityLifecycleVersionConflict):
        lifecycle.revoke_membership(
            TENANT_ID,
            membership_id,
            expected_version=2,
            reason="No longer required",
            principal_id=ACTOR_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Revoke tenant membership",
            correlation_id="stale-membership",
        )
    with database.tenant_transaction(TENANT_ID) as session:
        membership = session.get(Membership, membership_id)
        assert membership is not None
        membership.status = "REVOKED"
    with pytest.raises(IdentityLifecycleConflict, match="already revoked"):
        lifecycle.revoke_membership(
            TENANT_ID,
            membership_id,
            expected_version=1,
            reason="No longer required",
            principal_id=ACTOR_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Revoke tenant membership",
            correlation_id="already-revoked-membership",
        )

    rollback_id = membership_id
    with database.tenant_transaction(TENANT_ID) as session:
        membership = session.get(Membership, rollback_id)
        assert membership is not None
        membership.status = "ACTIVE"
        membership.revoked_at = None

    def fail_audit(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise ValueError("private audit detail")

    monkeypatch.setattr("campaignos.identity.lifecycle.append_audit_event", fail_audit)
    with pytest.raises(IdentityLifecycleUnavailable):
        lifecycle.revoke_membership(
            TENANT_ID,
            rollback_id,
            expected_version=1,
            reason="No longer required",
            principal_id=ACTOR_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Revoke tenant membership",
            correlation_id="membership-audit-failure",
        )
    with database.tenant_transaction(TENANT_ID) as session:
        membership = session.get(Membership, rollback_id)
        assert membership is not None and membership.status == "ACTIVE"


def test_support_request_duplicate_and_wrappers_fail_closed(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_support(database, key="support-original")
    with pytest.raises(IdentityLifecycleConflict, match="Active support access"):
        request_support(database, key="support-duplicate")

    def unknown_integrity(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise IntegrityError("insert", {}, RuntimeError("unknown_constraint"))

    monkeypatch.setattr(SqlAlchemyIdentityLifecycle, "_request_support_access", unknown_integrity)
    with pytest.raises(IdentityLifecycleUnavailable):
        request_support(database, key="support-unknown-integrity")


def test_support_approval_state_errors_and_expiry_persistence_failure(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    with pytest.raises(IdentityLifecycleNotFound):
        lifecycle.approve_support_access(
            TENANT_ID,
            uuid4(),
            request=SupportAccessApprove(expected_version=1),
            principal_id=APPROVER_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Approve time-bound support access",
            correlation_id="missing-support",
        )
    requested = request_support(database)
    with pytest.raises(IdentityLifecycleVersionConflict):
        lifecycle.approve_support_access(
            TENANT_ID,
            requested.request.id,
            request=SupportAccessApprove(expected_version=2),
            principal_id=APPROVER_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Approve time-bound support access",
            correlation_id="stale-support",
        )
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(SupportAccessRequest, requested.request.id)
        assert row is not None
        row.status = "REJECTED"
    with pytest.raises(IdentityLifecycleConflict, match="not pending"):
        lifecycle.approve_support_access(
            TENANT_ID,
            requested.request.id,
            request=SupportAccessApprove(expected_version=1),
            principal_id=APPROVER_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Approve time-bound support access",
            correlation_id="rejected-support",
        )

    expiring = request_support(database, key="support-expiring")
    expired_at = datetime.now(UTC) - timedelta(hours=1)
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(SupportAccessRequest, expiring.request.id)
        assert row is not None
        row.requested_at = expired_at - timedelta(hours=1)
        row.expires_at = expired_at

    def fail_persist(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise ValueError("private persistence detail")

    monkeypatch.setattr(SqlAlchemyIdentityLifecycle, "_persist_support_expiry", fail_persist)
    with pytest.raises(IdentityLifecycleUnavailable):
        lifecycle.approve_support_access(
            TENANT_ID,
            expiring.request.id,
            request=SupportAccessApprove(expected_version=1),
            principal_id=APPROVER_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Approve time-bound support access",
            correlation_id="support-expiry-persistence-failure",
        )


def test_support_approval_rejects_incompatible_preexisting_authority(database: Database) -> None:
    membership_id = seed_membership(database, status="SUSPENDED")
    requested = request_support(database)
    with pytest.raises(IdentityLifecycleConflict, match="membership is not active"):
        approve_support(database, requested.request.id)

    with database.tenant_transaction(TENANT_ID) as session:
        membership = session.get(Membership, membership_id)
        assert membership is not None
        membership.status = "ACTIVE"
        membership.expires_at = datetime.now(UTC) + timedelta(minutes=5)
    with pytest.raises(IdentityLifecycleConflict, match="outlive"):
        approve_support(database, requested.request.id)

    with database.tenant_transaction(TENANT_ID) as session:
        membership = session.get(Membership, membership_id)
        assert membership is not None
        membership.expires_at = None
        session.add(
            RoleAssignment(
                tenant_id=TENANT_ID,
                membership_id=membership_id,
                role=f"time_bound_support:{uuid4()}",
                assigned_by_principal_id=APPROVER_ID,
                expires_at=datetime.now(UTC) + timedelta(hours=1),
            )
        )
    with pytest.raises(IdentityLifecycleConflict, match="Support role is already active"):
        approve_support(database, requested.request.id)


def test_support_approval_rejects_conflicting_or_unowned_grant(database: Database) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    membership_id = seed_membership(database)
    requested = request_support(database)
    with database.tenant_transaction(TENANT_ID) as session:
        session.add(
            PermissionGrant(
                tenant_id=TENANT_ID,
                membership_id=membership_id,
                campaign_id=CAMPAIGN_ID,
                workspace_id=WORKSPACE_ID,
                action="read",
                resource_type="campaign_readiness",
                resource_id=str(CAMPAIGN_ID),
                purpose="Different purpose",
                status="REVOKED",
                valid_from=datetime.now(UTC) - timedelta(hours=1),
                expires_at=datetime.now(UTC) - timedelta(minutes=1),
                granted_by_principal_id=APPROVER_ID,
                approval_receipt_id="unowned-grant",
            )
        )
    with pytest.raises(IdentityLifecycleConflict, match="scope conflicts"):
        lifecycle.approve_support_access(
            TENANT_ID,
            requested.request.id,
            request=SupportAccessApprove(expected_version=1),
            principal_id=APPROVER_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Approve time-bound support access",
            correlation_id="conflicting-grant",
        )

    with database.tenant_transaction(TENANT_ID) as session:
        grant = session.scalar(select(PermissionGrant))
        assert grant is not None
        grant.purpose = "Diagnose assigned campaign"
    with pytest.raises(IdentityLifecycleConflict, match="not owned"):
        lifecycle.approve_support_access(
            TENANT_ID,
            requested.request.id,
            request=SupportAccessApprove(expected_version=1),
            principal_id=APPROVER_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Approve time-bound support access",
            correlation_id="unowned-grant",
        )

    with database.tenant_transaction(TENANT_ID) as session:
        grant = session.scalar(select(PermissionGrant))
        assert grant is not None
        grant.status = "ACTIVE"
        grant.expires_at = datetime.now(UTC) + timedelta(hours=1)
    with pytest.raises(IdentityLifecycleConflict, match="already active"):
        lifecycle.approve_support_access(
            TENANT_ID,
            requested.request.id,
            request=SupportAccessApprove(expected_version=1),
            principal_id=APPROVER_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Approve time-bound support access",
            correlation_id="active-grant",
        )


def test_support_approval_and_revoke_audit_failures_roll_back(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    requested = request_support(database)

    def fail_audit(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise ValueError("private audit detail")

    monkeypatch.setattr("campaignos.identity.lifecycle.append_audit_event", fail_audit)
    with pytest.raises(IdentityLifecycleUnavailable):
        approve_support(database, requested.request.id)
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(SupportAccessRequest, requested.request.id)
        assert row is not None and row.status == "PENDING"

    monkeypatch.undo()
    approved = approve_support(database, requested.request.id)
    monkeypatch.setattr("campaignos.identity.lifecycle.append_audit_event", fail_audit)
    with pytest.raises(IdentityLifecycleUnavailable):
        lifecycle.revoke_support_access(
            TENANT_ID,
            requested.request.id,
            request=SupportAccessRevoke(reason="Completed", expected_version=2),
            principal_id=APPROVER_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Revoke time-bound support access",
            correlation_id="support-revoke-audit-failure",
        )
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(SupportAccessRequest, requested.request.id)
        grant = session.get(PermissionGrant, approved.request.permission_grant_id)
        assert row is not None and row.status == "APPROVED"
        assert grant is not None and grant.status == "ACTIVE"


def test_support_revoke_state_and_incomplete_evidence_fail_closed(database: Database) -> None:
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    with pytest.raises(IdentityLifecycleNotFound):
        lifecycle.revoke_support_access(
            TENANT_ID,
            uuid4(),
            request=SupportAccessRevoke(reason="Completed", expected_version=2),
            principal_id=APPROVER_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Revoke time-bound support access",
            correlation_id="missing-support-revoke",
        )
    requested = request_support(database)
    with pytest.raises(IdentityLifecycleVersionConflict):
        lifecycle.revoke_support_access(
            TENANT_ID,
            requested.request.id,
            request=SupportAccessRevoke(reason="Completed", expected_version=2),
            principal_id=APPROVER_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Revoke time-bound support access",
            correlation_id="stale-support-revoke",
        )
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(SupportAccessRequest, requested.request.id)
        assert row is not None
        row.version = 2
    with pytest.raises(IdentityLifecycleConflict, match="not approved"):
        lifecycle.revoke_support_access(
            TENANT_ID,
            requested.request.id,
            request=SupportAccessRevoke(reason="Completed", expected_version=2),
            principal_id=APPROVER_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Revoke time-bound support access",
            correlation_id="pending-support-revoke",
        )
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(SupportAccessRequest, requested.request.id)
        assert row is not None
        row.status = "APPROVED"
    with pytest.raises(IdentityLifecycleUnavailable, match="incomplete"):
        lifecycle.revoke_support_access(
            TENANT_ID,
            requested.request.id,
            request=SupportAccessRevoke(reason="Completed", expected_version=2),
            principal_id=APPROVER_ID,
            authorization_grant_id=AUTHORIZATION_GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose="Revoke time-bound support access",
            correlation_id="incomplete-support-revoke",
        )
