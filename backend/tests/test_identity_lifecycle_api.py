from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from campaignos.api.app import create_app
from campaignos.config import Environment, Settings
from campaignos.identity.authorization import (
    EffectiveMembership,
    EffectivePermissionGrant,
    TenantAccessDenied,
    TenantAuthorizationContext,
)
from campaignos.identity.lifecycle import (
    IdentityLifecycleConflict,
    IdentityLifecycleIdempotencyConflict,
    IdentityLifecycleUnavailable,
    IdentityLifecycleVersionConflict,
)
from campaignos.identity.lifecycle_contracts import (
    InvitationAcceptanceEvidence,
    InvitationCreate,
    InvitationCreateEvidence,
    InvitationDeliveryPlan,
    InvitationMutationEvidence,
    InvitationProjection,
    MembershipProjection,
    MembershipRevocationEvidence,
    SessionEvidence,
    SessionProjection,
    SupportAccessEvidence,
    SupportAccessProjection,
)
from campaignos.identity.models import AuthenticatedPrincipal

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
FOREIGN_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
PRINCIPAL_ID = UUID("33333333-3333-4333-8333-333333333333")
TARGET_PRINCIPAL_ID = UUID("44444444-4444-4444-8444-444444444444")
MEMBERSHIP_ID = UUID("55555555-5555-4555-8555-555555555555")
INVITATION_ID = UUID("66666666-6666-4666-8666-666666666666")
SESSION_ID = UUID("77777777-7777-4777-8777-777777777777")
SUPPORT_REQUEST_ID = UUID("88888888-8888-4888-8888-888888888888")
CAMPAIGN_ID = UUID("99999999-9999-4999-8999-999999999999")
WORKSPACE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
GRANT_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
AUDIT_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
OUTBOX_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
ROLE_ID = UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")
PERMISSION_ID = UUID("ffffffff-ffff-4fff-8fff-ffffffffffff")
NOW = datetime(2026, 7, 21, 12, tzinfo=UTC)


def settings() -> Settings:
    return Settings(environment=Environment.TEST, expose_api_docs=True)


class Verifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        assert token == "valid-token"  # noqa: S105 - deterministic fixture.
        return AuthenticatedPrincipal(
            subject="identity-operator",
            issuer="https://identity.example.test/",
            audience="campaignos-test",
            display_name="Identity Operator",
            email="operator@example.test",
            email_verified=True,
            session_id="session-provider-id",
            authenticated_at=NOW,
            expires_at=NOW + timedelta(hours=1),
        )

    def readiness(self) -> tuple[bool, str]:
        return True, "ready"


def grant(
    *,
    action: str,
    resource_type: str,
    resource_id: str,
    purpose: str,
    campaign_id: UUID | None = None,
    workspace_id: UUID | None = None,
) -> EffectivePermissionGrant:
    return EffectivePermissionGrant(
        grant_id=GRANT_ID,
        campaign_id=campaign_id,
        workspace_id=workspace_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        purpose=purpose,
        approval_receipt_id="approval-identity-lifecycle",
    )


class Directory:
    def __init__(
        self,
        grants: tuple[EffectivePermissionGrant, ...] = (),
        *,
        fail_if_called: bool = False,
    ) -> None:
        self.grants = grants
        self.fail_if_called = fail_if_called
        self.calls = 0

    def load(
        self,
        tenant_id: UUID,
        principal: AuthenticatedPrincipal,
        *,
        evaluated_at: datetime | None = None,
    ) -> TenantAuthorizationContext:
        del principal, evaluated_at
        self.calls += 1
        if self.fail_if_called:
            raise AssertionError("membership directory must not be called")
        if tenant_id != TENANT_ID:
            raise TenantAccessDenied("foreign tenant")
        return TenantAuthorizationContext(
            principal_id=PRINCIPAL_ID,
            tenant_id=tenant_id,
            evaluated_at=NOW,
            memberships=(
                EffectiveMembership(
                    membership_id=MEMBERSHIP_ID,
                    campaign_id=None,
                    roles=("administrator-label-only",),
                    grants=self.grants,
                ),
            ),
        )


def invitation_projection(
    *,
    tenant_id: UUID = TENANT_ID,
    invitation_id: UUID = INVITATION_ID,
    status: str = "PENDING",
    campaign_id: UUID | None = CAMPAIGN_ID,
    membership_id: UUID | None = None,
    version: int = 1,
) -> InvitationProjection:
    return InvitationProjection.model_validate(
        {
            "id": invitation_id,
            "tenant_id": tenant_id,
            "campaign_id": campaign_id,
            "email": "invitee@example.test",
            "status": status,
            "provider": "LOCAL_NO_DELIVERY",
            "provider_reference": f"local:{invitation_id}",
            "expires_at": NOW + timedelta(hours=24),
            "accepted_at": NOW if status == "ACCEPTED" else None,
            "membership_id": membership_id,
            "revoked_at": NOW if status == "REVOKED" else None,
            "version": version,
        }
    )


def membership_projection(
    *,
    tenant_id: UUID = TENANT_ID,
    membership_id: UUID = MEMBERSHIP_ID,
    principal_id: UUID = PRINCIPAL_ID,
    status: str = "ACTIVE",
    version: int = 1,
) -> MembershipProjection:
    return MembershipProjection.model_validate(
        {
            "id": membership_id,
            "tenant_id": tenant_id,
            "principal_id": principal_id,
            "campaign_id": CAMPAIGN_ID,
            "status": status,
            "valid_from": NOW,
            "expires_at": None,
            "revoked_at": NOW if status == "REVOKED" else None,
            "version": version,
        }
    )


def session_projection(
    *,
    tenant_id: UUID = TENANT_ID,
    session_id: UUID = SESSION_ID,
    principal_id: UUID = PRINCIPAL_ID,
    status: str = "ACTIVE",
    version: int = 1,
) -> SessionProjection:
    return SessionProjection.model_validate(
        {
            "id": session_id,
            "tenant_id": tenant_id,
            "principal_id": principal_id,
            "status": status,
            "authenticated_at": NOW,
            "last_seen_at": NOW,
            "expires_at": NOW + timedelta(hours=1),
            "revoked_at": NOW if status == "REVOKED" else None,
            "revocation_reason": "Signed out" if status == "REVOKED" else None,
            "version": version,
        }
    )


def support_projection(
    *,
    tenant_id: UUID = TENANT_ID,
    request_id: UUID = SUPPORT_REQUEST_ID,
    status: str = "PENDING",
    version: int = 1,
) -> SupportAccessProjection:
    approved = status == "APPROVED"
    revoked = status == "REVOKED"
    return SupportAccessProjection.model_validate(
        {
            "id": request_id,
            "tenant_id": tenant_id,
            "requested_by_principal_id": PRINCIPAL_ID,
            "target_principal_id": TARGET_PRINCIPAL_ID,
            "campaign_id": CAMPAIGN_ID,
            "workspace_id": WORKSPACE_ID,
            "action": "read",
            "resource_type": "campaign_readiness",
            "resource_id": str(CAMPAIGN_ID),
            "purpose": "Diagnose assigned campaign",
            "reason": "Investigate a customer-authorized defect.",
            "status": status,
            "requested_at": NOW,
            "expires_at": NOW + timedelta(hours=1),
            "decided_at": NOW if approved or revoked else None,
            "decided_by_principal_id": PRINCIPAL_ID if approved or revoked else None,
            "approval_receipt_id": "approval-support" if approved or revoked else None,
            "membership_id": MEMBERSHIP_ID if approved or revoked else None,
            "role_assignment_id": ROLE_ID if approved or revoked else None,
            "permission_grant_id": PERMISSION_ID if approved or revoked else None,
            "created_membership": approved or revoked,
            "revoked_at": NOW if revoked else None,
            "version": version,
        }
    )


class Lifecycle:
    def __init__(
        self,
        *,
        failure: Exception | None = None,
        drift_tenant: UUID | None = None,
    ) -> None:
        self.failure = failure
        self.drift_tenant = drift_tenant
        self.calls: list[tuple[str, tuple[object, ...], dict[str, Any]]] = []

    def _call(self, name: str, args: tuple[object, ...], kwargs: dict[str, Any]) -> None:
        self.calls.append((name, args, kwargs))
        if self.failure is not None:
            raise self.failure

    def create_invitation(self, tenant_id: UUID, **kwargs: Any) -> InvitationCreateEvidence:
        self._call("create_invitation", (tenant_id,), kwargs)
        payload = kwargs["request"]
        assert isinstance(payload, InvitationCreate)
        projection = invitation_projection(
            tenant_id=self.drift_tenant or tenant_id,
            campaign_id=payload.campaign_id,
        ).model_copy(update={"email": payload.email})
        return InvitationCreateEvidence(
            invitation=projection,
            delivery_plan=InvitationDeliveryPlan(
                provider="LOCAL_NO_DELIVERY",
                operation="local:RecordInvitationIntent",
                provider_reference=f"local:{INVITATION_ID}",
                request_payload={"delivery": "DISABLED"},
            ),
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )

    def accept_invitation(
        self,
        tenant_id: UUID,
        invitation_id: UUID,
        **kwargs: Any,
    ) -> InvitationAcceptanceEvidence:
        self._call("accept_invitation", (tenant_id, invitation_id), kwargs)
        membership = membership_projection(tenant_id=self.drift_tenant or tenant_id)
        return InvitationAcceptanceEvidence(
            invitation=invitation_projection(
                tenant_id=self.drift_tenant or tenant_id,
                invitation_id=invitation_id,
                status="ACCEPTED",
                membership_id=membership.id,
                version=2,
            ),
            membership=membership,
            principal_id=membership.principal_id,
            audit_event_id=AUDIT_ID,
        )

    def revoke_invitation(
        self,
        tenant_id: UUID,
        invitation_id: UUID,
        **kwargs: Any,
    ) -> InvitationMutationEvidence:
        self._call("revoke_invitation", (tenant_id, invitation_id), kwargs)
        return InvitationMutationEvidence(
            invitation=invitation_projection(
                tenant_id=self.drift_tenant or tenant_id,
                invitation_id=invitation_id,
                status="REVOKED",
                version=2,
            ),
            audit_event_id=AUDIT_ID,
        )

    def register_session(self, tenant_id: UUID, **kwargs: Any) -> SessionEvidence:
        self._call("register_session", (tenant_id,), kwargs)
        return SessionEvidence(
            session=session_projection(tenant_id=self.drift_tenant or tenant_id),
            audit_event_id=AUDIT_ID,
            created=True,
        )

    def revoke_session(
        self,
        tenant_id: UUID,
        session_id: UUID,
        **kwargs: Any,
    ) -> SessionEvidence:
        self._call("revoke_session", (tenant_id, session_id), kwargs)
        return SessionEvidence(
            session=session_projection(
                tenant_id=self.drift_tenant or tenant_id,
                session_id=session_id,
                status="REVOKED",
                version=2,
            ),
            audit_event_id=AUDIT_ID,
            created=False,
        )

    def revoke_membership(
        self,
        tenant_id: UUID,
        membership_id: UUID,
        **kwargs: Any,
    ) -> MembershipRevocationEvidence:
        self._call("revoke_membership", (tenant_id, membership_id), kwargs)
        return MembershipRevocationEvidence(
            membership=membership_projection(
                tenant_id=self.drift_tenant or tenant_id,
                membership_id=membership_id,
                status="REVOKED",
                version=2,
            ),
            revoked_grant_count=1,
            expired_role_count=1,
            revoked_session_count=1,
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )

    def request_support_access(self, tenant_id: UUID, **kwargs: Any) -> SupportAccessEvidence:
        self._call("request_support_access", (tenant_id,), kwargs)
        return SupportAccessEvidence(
            request=support_projection(tenant_id=self.drift_tenant or tenant_id),
            audit_event_id=AUDIT_ID,
        )

    def approve_support_access(
        self,
        tenant_id: UUID,
        request_id: UUID,
        **kwargs: Any,
    ) -> SupportAccessEvidence:
        self._call("approve_support_access", (tenant_id, request_id), kwargs)
        return SupportAccessEvidence(
            request=support_projection(
                tenant_id=self.drift_tenant or tenant_id,
                request_id=request_id,
                status="APPROVED",
                version=2,
            ),
            audit_event_id=AUDIT_ID,
        )

    def revoke_support_access(
        self,
        tenant_id: UUID,
        request_id: UUID,
        **kwargs: Any,
    ) -> SupportAccessEvidence:
        self._call("revoke_support_access", (tenant_id, request_id), kwargs)
        return SupportAccessEvidence(
            request=support_projection(
                tenant_id=self.drift_tenant or tenant_id,
                request_id=request_id,
                status="REVOKED",
                version=3,
            ),
            audit_event_id=AUDIT_ID,
        )


def api_client(
    lifecycle: Lifecycle,
    *,
    grants: tuple[EffectivePermissionGrant, ...] = (),
    directory: Directory | None = None,
) -> TestClient:
    return TestClient(
        create_app(
            settings(),
            token_verifier=Verifier(),
            membership_directory=directory or Directory(grants),
            identity_lifecycle=lifecycle,
        )
    )


def headers(**extra: str) -> dict[str, str]:
    return {
        "Authorization": "Bearer valid-token",
        "X-Correlation-ID": "identity-api-correlation",
        **extra,
    }


def invitation_payload() -> dict[str, object]:
    return {
        "email": " Invitee@Example.Test ",
        "campaign_id": str(CAMPAIGN_ID),
        "expires_in_hours": 24,
    }


def support_payload() -> dict[str, object]:
    return {
        "target_principal_id": str(TARGET_PRINCIPAL_ID),
        "campaign_id": str(CAMPAIGN_ID),
        "workspace_id": str(WORKSPACE_ID),
        "action": "read",
        "resource_type": "campaign_readiness",
        "resource_id": str(CAMPAIGN_ID),
        "purpose": "Diagnose assigned campaign",
        "reason": "Investigate a customer-authorized defect.",
        "expires_in_minutes": 60,
    }


def test_create_invitation_requires_exact_grant_and_forwards_binding() -> None:
    lifecycle = Lifecycle()
    exact = grant(
        action="create",
        resource_type="membership_invitation_collection",
        resource_id=str(TENANT_ID),
        purpose="Invite tenant member",
    )
    with api_client(lifecycle, grants=(exact,)) as client:
        response = client.post(
            f"/api/v1/tenants/{TENANT_ID}/identity/invitations",
            json=invitation_payload(),
            headers=headers(**{"Idempotency-Key": "invitation-create-1"}),
        )

    assert response.status_code == 201
    assert response.json()["invitation"]["email"] == "invitee@example.test"
    assert response.json()["delivery_plan"]["delivery_state"] == "NOT_SENT"
    assert len(lifecycle.calls) == 1
    name, args, kwargs = lifecycle.calls[0]
    assert name == "create_invitation"
    assert args == (TENANT_ID,)
    assert kwargs["principal_id"] == PRINCIPAL_ID
    assert kwargs["authorization_grant_id"] == GRANT_ID
    assert kwargs["approval_receipt_id"] == "approval-identity-lifecycle"
    assert kwargs["authorization_purpose"] == "Invite tenant member"
    assert kwargs["correlation_id"] == "identity-api-correlation"
    assert kwargs["idempotency_key"] == "invitation-create-1"
    assert kwargs["request"] == InvitationCreate.model_validate(invitation_payload())


@pytest.mark.parametrize(
    "bad_grant",
    [
        None,
        grant(
            action="read",
            resource_type="membership_invitation_collection",
            resource_id=str(TENANT_ID),
            purpose="Invite tenant member",
        ),
        grant(
            action="create",
            resource_type="membership_invitation",
            resource_id=str(TENANT_ID),
            purpose="Invite tenant member",
        ),
        grant(
            action="create",
            resource_type="membership_invitation_collection",
            resource_id=str(FOREIGN_TENANT_ID),
            purpose="Invite tenant member",
        ),
        grant(
            action="create",
            resource_type="membership_invitation_collection",
            resource_id=str(TENANT_ID),
            purpose="Similar invitation purpose",
        ),
        grant(
            action="create",
            resource_type="membership_invitation_collection",
            resource_id=str(TENANT_ID),
            purpose="Invite tenant member",
            campaign_id=CAMPAIGN_ID,
        ),
        grant(
            action="create",
            resource_type="membership_invitation_collection",
            resource_id=str(TENANT_ID),
            purpose="Invite tenant member",
            campaign_id=CAMPAIGN_ID,
            workspace_id=WORKSPACE_ID,
        ),
    ],
)
def test_create_invitation_denies_before_adapter(
    bad_grant: EffectivePermissionGrant | None,
) -> None:
    lifecycle = Lifecycle()
    with api_client(lifecycle, grants=((bad_grant,) if bad_grant is not None else ())) as client:
        response = client.post(
            f"/api/v1/tenants/{TENANT_ID}/identity/invitations",
            json=invitation_payload(),
            headers=headers(**{"Idempotency-Key": "invitation-create-1"}),
        )

    assert response.status_code == 403
    assert lifecycle.calls == []


def test_invitation_idempotency_and_errors_are_structured() -> None:
    exact = grant(
        action="create",
        resource_type="membership_invitation_collection",
        resource_id=str(TENANT_ID),
        purpose="Invite tenant member",
    )
    lifecycle = Lifecycle()
    with api_client(lifecycle, grants=(exact,)) as client:
        missing = client.post(
            f"/api/v1/tenants/{TENANT_ID}/identity/invitations",
            json=invitation_payload(),
            headers=headers(),
        )
    assert missing.status_code == 428
    assert lifecycle.calls == []

    for failure, expected_code in [
        (IdentityLifecycleIdempotencyConflict("conflict"), "IDEMPOTENCY_CONFLICT"),
        (IdentityLifecycleConflict("state details"), "IDENTITY_LIFECYCLE_CONFLICT"),
        (IdentityLifecycleVersionConflict("version"), "VERSION_CONFLICT"),
        (IdentityLifecycleUnavailable("database internals"), "AUTHORIZATION_UNAVAILABLE"),
    ]:
        lifecycle = Lifecycle(failure=failure)
        with api_client(lifecycle, grants=(exact,)) as client:
            response = client.post(
                f"/api/v1/tenants/{TENANT_ID}/identity/invitations",
                json=invitation_payload(),
                headers=headers(**{"Idempotency-Key": "invitation-create-1"}),
            )
        assert response.json()["code"] == expected_code
        assert "database internals" not in response.text
        assert "state details" not in response.text


def test_invitation_acceptance_uses_identity_without_membership_directory() -> None:
    lifecycle = Lifecycle()
    directory = Directory(fail_if_called=True)
    with api_client(lifecycle, directory=directory) as client:
        response = client.post(
            f"/api/v1/tenants/{TENANT_ID}/identity/invitations/{INVITATION_ID}/accept",
            headers=headers(**{"Idempotency-Key": "invitation-accept-1"}),
        )

    assert response.status_code == 200
    assert directory.calls == 0
    assert lifecycle.calls[0][0] == "accept_invitation"
    principal = lifecycle.calls[0][2]["principal"]
    assert isinstance(principal, AuthenticatedPrincipal)
    assert principal.email == "operator@example.test"


def test_invitation_revoke_requires_exact_resource_and_if_match() -> None:
    exact = grant(
        action="revoke",
        resource_type="membership_invitation",
        resource_id=str(INVITATION_ID),
        purpose="Revoke tenant invitation",
    )
    lifecycle = Lifecycle()
    with api_client(lifecycle, grants=(exact,)) as client:
        missing_version = client.post(
            f"/api/v1/tenants/{TENANT_ID}/identity/invitations/{INVITATION_ID}/revoke",
            headers=headers(),
        )
        response = client.post(
            f"/api/v1/tenants/{TENANT_ID}/identity/invitations/{INVITATION_ID}/revoke",
            headers=headers(**{"If-Match": '"1"'}),
        )

    assert missing_version.status_code == 428
    assert response.status_code == 200
    assert lifecycle.calls[-1][2]["expected_version"] == 1

    wrong = grant(
        action="revoke",
        resource_type="membership_invitation",
        resource_id=str(UUID(int=0)),
        purpose="Revoke tenant invitation",
    )
    denied_lifecycle = Lifecycle()
    with api_client(denied_lifecycle, grants=(wrong,)) as client:
        denied = client.post(
            f"/api/v1/tenants/{TENANT_ID}/identity/invitations/{INVITATION_ID}/revoke",
            headers=headers(**{"If-Match": '"1"'}),
        )
    assert denied.status_code == 403
    assert denied_lifecycle.calls == []


def test_session_registration_and_self_or_exact_admin_revocation() -> None:
    lifecycle = Lifecycle()
    with api_client(lifecycle) as client:
        registered = client.post(
            f"/api/v1/tenants/{TENANT_ID}/identity/sessions/current",
            headers=headers(),
        )
        self_revoked = client.post(
            f"/api/v1/tenants/{TENANT_ID}/identity/sessions/{SESSION_ID}/revoke",
            json={"reason": "User requested sign out", "expected_version": 1},
            headers=headers(),
        )
    assert registered.status_code == 200
    assert self_revoked.status_code == 200
    assert lifecycle.calls[-1][2]["allow_cross_principal"] is False
    assert lifecycle.calls[-1][2]["authorization_grant_id"] is None

    exact = grant(
        action="revoke",
        resource_type="application_session",
        resource_id=str(SESSION_ID),
        purpose="Revoke tenant application session",
    )
    admin_lifecycle = Lifecycle()
    with api_client(admin_lifecycle, grants=(exact,)) as client:
        response = client.post(
            f"/api/v1/tenants/{TENANT_ID}/identity/sessions/{SESSION_ID}/revoke",
            json={"reason": "Administrative response", "expected_version": 1},
            headers=headers(),
        )
    assert response.status_code == 200
    assert admin_lifecycle.calls[0][2]["allow_cross_principal"] is True
    assert admin_lifecycle.calls[0][2]["authorization_grant_id"] == GRANT_ID


def test_membership_revoke_requires_exact_grant_and_preserves_no_provider_claim() -> None:
    exact = grant(
        action="revoke",
        resource_type="membership",
        resource_id=str(MEMBERSHIP_ID),
        purpose="Revoke tenant membership",
    )
    lifecycle = Lifecycle()
    with api_client(lifecycle, grants=(exact,)) as client:
        response = client.post(
            f"/api/v1/tenants/{TENANT_ID}/identity/memberships/{MEMBERSHIP_ID}/revoke",
            json={"reason": "Membership is no longer required", "expected_version": 1},
            headers=headers(),
        )
    assert response.status_code == 200
    assert response.json()["provider_revocation_state"] == "NOT_EXECUTED"
    assert lifecycle.calls[0][2]["authorization_purpose"] == "Revoke tenant membership"


def test_support_request_approve_and_revoke_require_exact_resources() -> None:
    create_grant = grant(
        action="create",
        resource_type="support_access_collection",
        resource_id=str(TENANT_ID),
        purpose="Request time-bound support access",
    )
    lifecycle = Lifecycle()
    with api_client(lifecycle, grants=(create_grant,)) as client:
        requested = client.post(
            f"/api/v1/tenants/{TENANT_ID}/identity/support-access",
            json=support_payload(),
            headers=headers(**{"Idempotency-Key": "support-request-1"}),
        )
    assert requested.status_code == 201
    assert lifecycle.calls[0][2]["idempotency_key"] == "support-request-1"

    for action, purpose, suffix, body in [
        (
            "approve",
            "Approve time-bound support access",
            "approve",
            {"expected_version": 1},
        ),
        (
            "revoke",
            "Revoke time-bound support access",
            "revoke",
            {"reason": "Support session completed", "expected_version": 2},
        ),
    ]:
        exact = grant(
            action=action,
            resource_type="support_access_request",
            resource_id=str(SUPPORT_REQUEST_ID),
            purpose=purpose,
        )
        lifecycle = Lifecycle()
        with api_client(lifecycle, grants=(exact,)) as client:
            response = client.post(
                f"/api/v1/tenants/{TENANT_ID}/identity/support-access/{SUPPORT_REQUEST_ID}/{suffix}",
                json=body,
                headers=headers(),
            )
        assert response.status_code == 200
        assert lifecycle.calls[0][0] == f"{suffix}_support_access"

        wrong = exact.model_copy(update={"resource_id": str(UUID(int=0))})
        denied_lifecycle = Lifecycle()
        with api_client(denied_lifecycle, grants=(wrong,)) as client:
            denied = client.post(
                f"/api/v1/tenants/{TENANT_ID}/identity/support-access/{SUPPORT_REQUEST_ID}/{suffix}",
                json=body,
                headers=headers(),
            )
        assert denied.status_code == 403
        assert denied_lifecycle.calls == []


def test_adapter_scope_drift_fails_closed() -> None:
    exact = grant(
        action="create",
        resource_type="membership_invitation_collection",
        resource_id=str(TENANT_ID),
        purpose="Invite tenant member",
    )
    lifecycle = Lifecycle(drift_tenant=FOREIGN_TENANT_ID)
    with api_client(lifecycle, grants=(exact,)) as client:
        response = client.post(
            f"/api/v1/tenants/{TENANT_ID}/identity/invitations",
            json=invitation_payload(),
            headers=headers(**{"Idempotency-Key": "invitation-create-1"}),
        )

    assert response.status_code == 503
    assert response.json()["code"] == "AUTHORIZATION_UNAVAILABLE"


def test_openapi_documents_identity_lifecycle_and_bearer_security() -> None:
    lifecycle = Lifecycle()
    with api_client(lifecycle) as client:
        schema = client.get("/api/v1/openapi.json").json()

    paths = schema["paths"]
    assert "/api/v1/tenants/{tenant_id}/identity/invitations" in paths
    assert "/api/v1/tenants/{tenant_id}/identity/sessions/current" in paths
    assert "/api/v1/tenants/{tenant_id}/identity/support-access" in paths
    operation = paths["/api/v1/tenants/{tenant_id}/identity/invitations"]["post"]
    assert operation["security"] == [{"OIDC bearer token": []}]
    assert operation["responses"]["201"]["content"]["application/json"]["schema"]
