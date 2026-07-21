from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from threading import Barrier
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from campaignos.data import Database
from campaignos.data.models import (
    ApplicationSession,
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
from campaignos.identity.authorization import SqlAlchemyMembershipDirectory
from campaignos.identity.lifecycle import (
    IdentityLifecycleConflict,
    SqlAlchemyIdentityLifecycle,
)
from campaignos.identity.lifecycle_contracts import (
    InvitationAcceptanceEvidence,
    InvitationCreate,
    SupportAccessApprove,
    SupportAccessCreate,
    SupportAccessRevoke,
)
from campaignos.identity.models import AuthenticatedPrincipal

ISSUER = "https://identity.example.test/"


def _postgres_test_url() -> str:
    value = os.environ.get("CAMPAIGNOS_TEST_DATABASE_URL", "")
    if not value:
        pytest.skip("CAMPAIGNOS_TEST_DATABASE_URL is not configured")
    parsed = make_url(value)
    if parsed.drivername != "postgresql+psycopg" or not (
        parsed.database and parsed.database.endswith("_test")
    ):
        pytest.fail("PostgreSQL integration tests require an isolated *_test database")
    return value


def _identity(subject: str, email: str, *, session_id: str | None = None) -> AuthenticatedPrincipal:
    authenticated_at = datetime.now(UTC)
    return AuthenticatedPrincipal(
        issuer=ISSUER,
        subject=subject,
        audience="campaignos-test",
        display_name=subject.replace("-", " ").title(),
        email=email,
        email_verified=True,
        session_id=session_id,
        authenticated_at=authenticated_at,
        expires_at=(authenticated_at + timedelta(hours=1) if session_id is not None else None),
    )


def _drop_role_if_present(admin_engine: object, role_name: str) -> None:
    with admin_engine.begin() as connection:  # type: ignore[union-attr]
        exists = bool(
            connection.scalar(
                text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :role_name)"),
                {"role_name": role_name},
            )
        )
        if exists:
            connection.execute(text(f'DROP OWNED BY "{role_name}"'))
            connection.execute(text(f'DROP ROLE "{role_name}"'))


@pytest.mark.postgres
def test_postgresql_identity_lifecycle_concurrency_rls_and_regrant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin_url = _postgres_test_url()
    monkeypatch.setenv("CAMPAIGNOS_DATABASE_URL", admin_url)
    alembic = Config("alembic.ini")
    command.upgrade(alembic, "head")
    command.check(alembic)

    admin_engine = create_engine(admin_url)
    database_name = make_url(admin_url).database
    assert database_name is not None
    assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*_test", database_name)
    role_name = "campaignos_identity_lifecycle_test"
    role_password = f"test-{uuid4().hex}"
    _drop_role_if_present(admin_engine, role_name)
    with admin_engine.begin() as connection:
        connection.execute(
            text(
                f"CREATE ROLE \"{role_name}\" LOGIN PASSWORD '{role_password}' "
                "NOSUPERUSER NOBYPASSRLS"
            )
        )
        connection.execute(text(f'GRANT CONNECT ON DATABASE "{database_name}" TO "{role_name}"'))
        connection.execute(text(f'GRANT USAGE ON SCHEMA public TO "{role_name}"'))
        connection.execute(
            text(
                "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public "
                f'TO "{role_name}"'
            )
        )

    application_url = make_url(admin_url).set(username=role_name, password=role_password)
    database = Database.from_url(
        application_url.render_as_string(hide_password=False),
        pool_size=8,
        max_overflow=0,
    )
    tenant_id = uuid4()
    other_tenant_id = uuid4()
    campaign_id = uuid4()
    workspace_id = uuid4()
    actor_id = uuid4()
    approver_id = uuid4()
    support_id = uuid4()
    authorization_grant_id = uuid4()
    lifecycle = SqlAlchemyIdentityLifecycle(database)
    try:
        with database.tenant_transaction(tenant_id) as session:
            session.add_all(
                [
                    Tenant(
                        id=tenant_id,
                        slug=f"tenant-{tenant_id}",
                        name="Identity Lifecycle Tenant",
                    ),
                    Principal(
                        id=actor_id,
                        issuer=ISSUER,
                        subject=f"actor-{actor_id}",
                        email="actor@example.test",
                    ),
                    Principal(
                        id=approver_id,
                        issuer=ISSUER,
                        subject=f"approver-{approver_id}",
                        email="approver@example.test",
                    ),
                    Principal(
                        id=support_id,
                        issuer=ISSUER,
                        subject=f"support-{support_id}",
                        email="support@example.test",
                    ),
                ]
            )
        with database.tenant_transaction(tenant_id) as session:
            session.add(
                Campaign(
                    id=campaign_id,
                    tenant_id=tenant_id,
                    slug="identity-lifecycle",
                    name="Identity Lifecycle Campaign",
                    jurisdiction="Antigua Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=1,
                )
            )
        with database.tenant_transaction(tenant_id) as session:
            session.add(
                Workspace(
                    id=workspace_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    slug="governance",
                    name="Governance",
                    status="ACTIVE",
                    version=1,
                )
            )
        with database.tenant_transaction(other_tenant_id) as session:
            session.add(
                Tenant(
                    id=other_tenant_id,
                    slug=f"tenant-{other_tenant_id}",
                    name="Foreign Tenant",
                )
            )

        same_key_invitation = lifecycle.create_invitation(
            tenant_id,
            request=InvitationCreate(
                email="same-key@example.test",
                campaign_id=campaign_id,
                expires_in_hours=24,
            ),
            principal_id=actor_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id="approval-postgres-invitation",
            authorization_purpose="Invite tenant member",
            correlation_id="postgres-invitation-same-key-create",
            idempotency_key="postgres-invitation-same-key-create",
        )
        with pytest.raises(DBAPIError):
            with database.tenant_transaction(tenant_id) as session:
                session.add(
                    IdentityInvitation(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        campaign_id=campaign_id,
                        scope_key=campaign_id.hex,
                        email="same-key@example.test",
                        status="PENDING",
                        purpose="Duplicate pending invitation",
                        invited_by_principal_id=actor_id,
                        provider="LOCAL_NO_DELIVERY",
                        provider_reference=f"local:{uuid4()}",
                        expires_at=datetime.now(UTC) + timedelta(hours=1),
                        version=1,
                    )
                )

        same_key_identity = _identity("same-key-invitee", "same-key@example.test")
        same_key_barrier = Barrier(2)

        def accept_same_key(index: int) -> InvitationAcceptanceEvidence:
            same_key_barrier.wait()
            return lifecycle.accept_invitation(
                tenant_id,
                same_key_invitation.invitation.id,
                principal=same_key_identity,
                correlation_id=f"postgres-invitation-same-key-{index}",
                idempotency_key="postgres-invitation-same-key-accept",
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            same_key_results = list(executor.map(accept_same_key, (1, 2)))

        assert same_key_results[0] == same_key_results[1]
        same_key_membership_id = same_key_results[0].membership.id
        same_key_principal_id = same_key_results[0].principal_id

        distinct_key_invitation = lifecycle.create_invitation(
            tenant_id,
            request=InvitationCreate(
                email="distinct-key@example.test",
                campaign_id=campaign_id,
                expires_in_hours=24,
            ),
            principal_id=actor_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id="approval-postgres-invitation",
            authorization_purpose="Invite tenant member",
            correlation_id="postgres-invitation-distinct-create",
            idempotency_key="postgres-invitation-distinct-create",
        )
        distinct_key_identity = _identity("distinct-key-invitee", "distinct-key@example.test")
        distinct_key_barrier = Barrier(2)

        def accept_distinct_key(index: int) -> str:
            distinct_key_barrier.wait()
            try:
                lifecycle.accept_invitation(
                    tenant_id,
                    distinct_key_invitation.invitation.id,
                    principal=distinct_key_identity,
                    correlation_id=f"postgres-invitation-distinct-{index}",
                    idempotency_key=f"postgres-invitation-distinct-accept-{index}",
                )
            except IdentityLifecycleConflict:
                return "CONFLICT"
            return "ACCEPTED"

        with ThreadPoolExecutor(max_workers=2) as executor:
            distinct_key_results = sorted(executor.map(accept_distinct_key, (1, 2)))
        assert distinct_key_results == ["ACCEPTED", "CONFLICT"]

        with database.tenant_transaction(tenant_id) as session:
            assert session.scalar(select(func.count()).select_from(IdentityInvitation)) == 2
            assert session.scalar(select(func.count()).select_from(Membership)) == 2
            assert session.scalar(select(func.count()).select_from(RoleAssignment)) == 0
            assert session.scalar(select(func.count()).select_from(PermissionGrant)) == 0
            same_key_membership = session.get(Membership, same_key_membership_id)
            assert same_key_membership is not None
            assert same_key_membership.principal_id == same_key_principal_id
            assert same_key_membership.status == "ACTIVE"

        session_evidence = lifecycle.register_session(
            tenant_id,
            principal=_identity(
                "same-key-invitee",
                "same-key@example.test",
                session_id="raw-provider-session-id",
            ),
            application_principal_id=same_key_principal_id,
            correlation_id="postgres-session-register",
        )
        with database.tenant_transaction(tenant_id) as session:
            stored_session = session.get(ApplicationSession, session_evidence.session.id)
            assert stored_session is not None
            assert stored_session.provider_session_digest != "raw-provider-session-id"
            assert "raw-provider-session-id" not in str(stored_session.__dict__)

        support_request = lifecycle.request_support_access(
            tenant_id,
            request=SupportAccessCreate(
                target_principal_id=support_id,
                campaign_id=campaign_id,
                workspace_id=workspace_id,
                action="read",
                resource_type="campaign_readiness",
                resource_id=str(campaign_id),
                purpose="Diagnose assigned campaign",
                reason="Reproduce a customer-authorized support defect.",
                expires_in_minutes=30,
            ),
            principal_id=actor_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id="approval-postgres-support-request",
            authorization_purpose="Request time-bound support access",
            correlation_id="postgres-support-request",
            idempotency_key="postgres-support-request-1",
        )
        with pytest.raises(DBAPIError):
            with database.tenant_transaction(tenant_id) as session:
                operation_at = datetime.now(UTC)
                session.add(
                    SupportAccessRequest(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        requested_by_principal_id=actor_id,
                        target_principal_id=support_id,
                        campaign_id=campaign_id,
                        workspace_id=workspace_id,
                        campaign_scope_key=campaign_id.hex,
                        workspace_scope_key=workspace_id.hex,
                        action="read",
                        resource_type="campaign_readiness",
                        resource_id=str(campaign_id),
                        purpose="Diagnose assigned campaign",
                        reason="Duplicate active support request.",
                        status="PENDING",
                        requested_at=operation_at,
                        expires_at=operation_at + timedelta(minutes=30),
                        created_membership=False,
                        version=1,
                    )
                )

        approved = lifecycle.approve_support_access(
            tenant_id,
            support_request.request.id,
            request=SupportAccessApprove(expected_version=1),
            principal_id=approver_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id="approval-postgres-support",
            authorization_purpose="Approve time-bound support access",
            correlation_id="postgres-support-approve",
        )
        support_identity = _identity(f"support-{support_id}", "support@example.test")
        authorization = SqlAlchemyMembershipDirectory(database).load(
            tenant_id,
            support_identity,
            evaluated_at=approved.request.requested_at + timedelta(minutes=1),
        )
        assert authorization.permits(
            action="read",
            resource_type="campaign_readiness",
            resource_id=str(campaign_id),
            purpose="Diagnose assigned campaign",
            campaign_id=campaign_id,
            workspace_id=workspace_id,
        )
        revoked = lifecycle.revoke_support_access(
            tenant_id,
            support_request.request.id,
            request=SupportAccessRevoke(
                reason="Customer support session completed",
                expected_version=2,
            ),
            principal_id=approver_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id="approval-postgres-support-revoke",
            authorization_purpose="Revoke time-bound support access",
            correlation_id="postgres-support-revoke",
        )
        assert revoked.request.status == "REVOKED"

        second_support_request = lifecycle.request_support_access(
            tenant_id,
            request=SupportAccessCreate(
                target_principal_id=support_id,
                campaign_id=campaign_id,
                workspace_id=workspace_id,
                action="read",
                resource_type="campaign_readiness",
                resource_id=str(campaign_id),
                purpose="Diagnose assigned campaign",
                reason="Continue the customer-authorized support investigation.",
                expires_in_minutes=30,
            ),
            principal_id=actor_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id="approval-postgres-support-request-2",
            authorization_purpose="Request time-bound support access",
            correlation_id="postgres-support-request-2",
            idempotency_key="postgres-support-request-2",
        )
        approved_again = lifecycle.approve_support_access(
            tenant_id,
            second_support_request.request.id,
            request=SupportAccessApprove(expected_version=1),
            principal_id=approver_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id="approval-postgres-support-2",
            authorization_purpose="Approve time-bound support access",
            correlation_id="postgres-support-approve-2",
        )
        assert approved_again.request.membership_id == approved.request.membership_id
        assert approved_again.request.permission_grant_id == approved.request.permission_grant_id
        with database.tenant_transaction(tenant_id) as session:
            grants = list(
                session.scalars(
                    select(PermissionGrant).where(
                        PermissionGrant.membership_id == approved_again.request.membership_id
                    )
                )
            )
            assert len(grants) == 1
            assert grants[0].status == "ACTIVE"
            assert grants[0].approval_receipt_id == "approval-postgres-support-2"
            requests = list(
                session.scalars(
                    select(SupportAccessRequest).where(
                        SupportAccessRequest.membership_id == approved_again.request.membership_id
                    )
                )
            )
            assert len(requests) == 2
            assert sorted(request.status for request in requests) == ["APPROVED", "REVOKED"]
            roles = list(
                session.scalars(
                    select(RoleAssignment).where(
                        RoleAssignment.membership_id == approved_again.request.membership_id
                    )
                )
            )
            assert len(roles) == 2
            assert len({role.role for role in roles}) == 2

        with database.tenant_transaction(other_tenant_id) as session:
            assert session.scalar(select(func.count()).select_from(IdentityInvitation)) == 0
            assert session.scalar(select(func.count()).select_from(ApplicationSession)) == 0
            assert session.scalar(select(func.count()).select_from(SupportAccessRequest)) == 0
            assert session.scalar(select(func.count()).select_from(PermissionGrant)) == 0
            assert session.get(IdentityInvitation, same_key_invitation.invitation.id) is None
            assert session.get(ApplicationSession, session_evidence.session.id) is None
            assert session.get(SupportAccessRequest, support_request.request.id) is None

        with pytest.raises(DBAPIError):
            with database.tenant_transaction(tenant_id) as session:
                session.add(
                    IdentityInvitation(
                        id=uuid4(),
                        tenant_id=other_tenant_id,
                        campaign_id=None,
                        scope_key="TENANT",
                        email="cross-tenant@example.test",
                        status="PENDING",
                        purpose="Forbidden cross-tenant write",
                        invited_by_principal_id=actor_id,
                        provider="LOCAL_NO_DELIVERY",
                        provider_reference=f"local:{uuid4()}",
                        expires_at=datetime.now(UTC) + timedelta(hours=1),
                        version=1,
                    )
                )
    finally:
        database.dispose()
        _drop_role_if_present(admin_engine, role_name)
        admin_engine.dispose()
