"""Protected identity, membership, session, and support lifecycle endpoints."""

from __future__ import annotations

from typing import Annotated, NoReturn, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from campaignos.api.dependencies import CurrentPrincipal, CurrentTenantAuthorization
from campaignos.api.errors import ProblemException
from campaignos.identity.authorization import (
    EffectivePermissionGrant,
    TenantAuthorizationContext,
)
from campaignos.identity.lifecycle import (
    IdentityLifecycle,
    IdentityLifecycleConflict,
    IdentityLifecycleDenied,
    IdentityLifecycleIdempotencyConflict,
    IdentityLifecycleNotFound,
    IdentityLifecycleUnavailable,
    IdentityLifecycleVersionConflict,
)
from campaignos.identity.lifecycle_contracts import (
    InvitationAcceptanceEvidence,
    InvitationCreate,
    InvitationCreateEvidence,
    InvitationMutationEvidence,
    MembershipRevocationEvidence,
    MembershipRevoke,
    SessionEvidence,
    SessionRevoke,
    SupportAccessApprove,
    SupportAccessCreate,
    SupportAccessEvidence,
    SupportAccessRevoke,
)

router = APIRouter(tags=["identity lifecycle"])

INVITE_MEMBER_PURPOSE = "Invite tenant member"
REVOKE_INVITATION_PURPOSE = "Revoke tenant invitation"
REVOKE_MEMBERSHIP_PURPOSE = "Revoke tenant membership"
REVOKE_SESSION_PURPOSE = "Revoke tenant application session"
REQUEST_SUPPORT_PURPOSE = "Request time-bound support access"
APPROVE_SUPPORT_PURPOSE = "Approve time-bound support access"
REVOKE_SUPPORT_PURPOSE = "Revoke time-bound support access"


def lifecycle_manager(request: Request) -> IdentityLifecycle:
    return cast(IdentityLifecycle, request.app.state.identity_lifecycle)


LifecycleDependency = Annotated[IdentityLifecycle, Depends(lifecycle_manager)]


def _exact_grant(
    authorization: TenantAuthorizationContext,
    *,
    action: str,
    resource_type: str,
    resource_id: str,
    purpose: str,
) -> EffectivePermissionGrant | None:
    for membership in authorization.memberships:
        for grant in membership.grants:
            if grant.permits(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                purpose=purpose,
                campaign_id=None,
                workspace_id=None,
            ):
                return grant
    return None


def _required_idempotency_key(request: Request, value: str | None) -> str:
    values = request.headers.getlist("idempotency-key")
    if len(values) != 1 or value is None or not value.strip():
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail="Exactly one non-empty Idempotency-Key is required",
        )
    normalized = value.strip()
    if len(normalized) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key must not exceed 255 characters",
        )
    return normalized


def _expected_version(if_match: str | None, resource: str) -> int:
    if if_match is None:
        raise HTTPException(
            status_code=status.HTTP_428_PRECONDITION_REQUIRED,
            detail=f"If-Match with the current {resource} version is required",
        )
    value = if_match.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        value = value[1:-1]
    if not value.isdigit() or int(value) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"If-Match must contain a positive {resource} version",
        )
    return int(value)


def _raise_lifecycle_error(exc: Exception) -> NoReturn:
    if isinstance(exc, IdentityLifecycleIdempotencyConflict):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency key conflicts with a previous request",
        ) from exc
    if isinstance(exc, IdentityLifecycleVersionConflict):
        raise HTTPException(
            status_code=status.HTTP_412_PRECONDITION_FAILED,
            detail="Identity lifecycle version has changed",
        ) from exc
    if isinstance(exc, IdentityLifecycleNotFound):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Identity lifecycle resource was not found",
        ) from exc
    if isinstance(exc, IdentityLifecycleDenied):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Identity lifecycle operation is not authorized",
        ) from exc
    if isinstance(exc, IdentityLifecycleConflict):
        raise ProblemException(
            status=status.HTTP_409_CONFLICT,
            title="Identity lifecycle conflict",
            detail="Identity lifecycle state conflicts with this operation",
            code="IDENTITY_LIFECYCLE_CONFLICT",
        ) from exc
    if isinstance(exc, IdentityLifecycleUnavailable):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity lifecycle is temporarily unavailable",
        ) from exc
    raise exc


def _correlation_id(request: Request) -> str:
    return getattr(request.state, "correlation_id", "unknown")


@router.post(
    "/tenants/{tenant_id}/identity/invitations",
    response_model=InvitationCreateEvidence,
    status_code=status.HTTP_201_CREATED,
    summary="Plan a tenant membership invitation",
    description=(
        "Creates durable invitation, audit, internal outbox, and idempotency evidence. "
        "The provider plan is not executed and no email or Cognito mutation occurs."
    ),
)
def create_invitation(
    request: Request,
    tenant_id: UUID,
    payload: InvitationCreate,
    authorization: CurrentTenantAuthorization,
    lifecycle: LifecycleDependency,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> InvitationCreateEvidence:
    grant = _exact_grant(
        authorization,
        action="create",
        resource_type="membership_invitation_collection",
        resource_id=str(tenant_id),
        purpose=INVITE_MEMBER_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Membership invitation creation is not authorized",
        )
    try:
        evidence = lifecycle.create_invitation(
            tenant_id,
            request=payload,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
            idempotency_key=_required_idempotency_key(request, idempotency_key),
        )
    except (
        IdentityLifecycleConflict,
        IdentityLifecycleDenied,
        IdentityLifecycleNotFound,
        IdentityLifecycleUnavailable,
    ) as exc:
        _raise_lifecycle_error(exc)
    if (
        evidence.invitation.tenant_id != tenant_id
        or evidence.invitation.campaign_id != payload.campaign_id
        or evidence.invitation.email != payload.email
        or evidence.delivery_plan.external_effects != "NONE"
        or evidence.delivery_plan.delivery_state != "NOT_SENT"
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity lifecycle is temporarily unavailable",
        )
    return evidence


@router.post(
    "/tenants/{tenant_id}/identity/invitations/{invitation_id}/accept",
    response_model=InvitationAcceptanceEvidence,
    summary="Accept one invitation with the current verified identity",
)
def accept_invitation(
    request: Request,
    tenant_id: UUID,
    invitation_id: UUID,
    principal: CurrentPrincipal,
    lifecycle: LifecycleDependency,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> InvitationAcceptanceEvidence:
    try:
        evidence = lifecycle.accept_invitation(
            tenant_id,
            invitation_id,
            principal=principal,
            correlation_id=_correlation_id(request),
            idempotency_key=_required_idempotency_key(request, idempotency_key),
        )
    except (
        IdentityLifecycleConflict,
        IdentityLifecycleDenied,
        IdentityLifecycleNotFound,
        IdentityLifecycleUnavailable,
    ) as exc:
        _raise_lifecycle_error(exc)
    if (
        evidence.invitation.tenant_id != tenant_id
        or evidence.invitation.id != invitation_id
        or evidence.membership.tenant_id != tenant_id
        or evidence.membership.id != evidence.invitation.membership_id
        or evidence.principal_id != evidence.membership.principal_id
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity lifecycle is temporarily unavailable",
        )
    return evidence


@router.post(
    "/tenants/{tenant_id}/identity/invitations/{invitation_id}/revoke",
    response_model=InvitationMutationEvidence,
    summary="Revoke one pending invitation",
)
def revoke_invitation(
    request: Request,
    tenant_id: UUID,
    invitation_id: UUID,
    authorization: CurrentTenantAuthorization,
    lifecycle: LifecycleDependency,
    if_match: Annotated[str | None, Header(alias="If-Match")] = None,
) -> InvitationMutationEvidence:
    grant = _exact_grant(
        authorization,
        action="revoke",
        resource_type="membership_invitation",
        resource_id=str(invitation_id),
        purpose=REVOKE_INVITATION_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invitation revocation is not authorized",
        )
    try:
        evidence = lifecycle.revoke_invitation(
            tenant_id,
            invitation_id,
            expected_version=_expected_version(if_match, "invitation"),
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
        )
    except (
        IdentityLifecycleConflict,
        IdentityLifecycleDenied,
        IdentityLifecycleNotFound,
        IdentityLifecycleUnavailable,
    ) as exc:
        _raise_lifecycle_error(exc)
    if evidence.invitation.tenant_id != tenant_id or evidence.invitation.id != invitation_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity lifecycle is temporarily unavailable",
        )
    return evidence


@router.post(
    "/tenants/{tenant_id}/identity/sessions/current",
    response_model=SessionEvidence,
    summary="Register or refresh the current verified application session",
)
def register_current_session(
    request: Request,
    tenant_id: UUID,
    principal: CurrentPrincipal,
    authorization: CurrentTenantAuthorization,
    lifecycle: LifecycleDependency,
) -> SessionEvidence:
    try:
        evidence = lifecycle.register_session(
            tenant_id,
            principal=principal,
            application_principal_id=authorization.principal_id,
            correlation_id=_correlation_id(request),
        )
    except (
        IdentityLifecycleConflict,
        IdentityLifecycleDenied,
        IdentityLifecycleNotFound,
        IdentityLifecycleUnavailable,
    ) as exc:
        _raise_lifecycle_error(exc)
    if (
        evidence.session.tenant_id != tenant_id
        or evidence.session.principal_id != authorization.principal_id
        or evidence.provider_revocation_state != "NOT_EXECUTED"
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity lifecycle is temporarily unavailable",
        )
    return evidence


@router.post(
    "/tenants/{tenant_id}/identity/sessions/{session_id}/revoke",
    response_model=SessionEvidence,
    summary="Revoke an application session",
)
def revoke_session(
    request: Request,
    tenant_id: UUID,
    session_id: UUID,
    payload: SessionRevoke,
    authorization: CurrentTenantAuthorization,
    lifecycle: LifecycleDependency,
) -> SessionEvidence:
    grant = _exact_grant(
        authorization,
        action="revoke",
        resource_type="application_session",
        resource_id=str(session_id),
        purpose=REVOKE_SESSION_PURPOSE,
    )
    try:
        evidence = lifecycle.revoke_session(
            tenant_id,
            session_id,
            request=payload,
            principal_id=authorization.principal_id,
            allow_cross_principal=grant is not None,
            authorization_grant_id=grant.grant_id if grant is not None else None,
            approval_receipt_id=(grant.approval_receipt_id if grant is not None else None),
            authorization_purpose=(
                grant.purpose if grant is not None else "Revoke own application session"
            ),
            correlation_id=_correlation_id(request),
        )
    except (
        IdentityLifecycleConflict,
        IdentityLifecycleDenied,
        IdentityLifecycleNotFound,
        IdentityLifecycleUnavailable,
    ) as exc:
        _raise_lifecycle_error(exc)
    if evidence.session.tenant_id != tenant_id or evidence.session.id != session_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity lifecycle is temporarily unavailable",
        )
    return evidence


@router.post(
    "/tenants/{tenant_id}/identity/memberships/{membership_id}/revoke",
    response_model=MembershipRevocationEvidence,
    summary="Revoke a membership and its effective local access",
)
def revoke_membership(
    request: Request,
    tenant_id: UUID,
    membership_id: UUID,
    payload: MembershipRevoke,
    authorization: CurrentTenantAuthorization,
    lifecycle: LifecycleDependency,
) -> MembershipRevocationEvidence:
    grant = _exact_grant(
        authorization,
        action="revoke",
        resource_type="membership",
        resource_id=str(membership_id),
        purpose=REVOKE_MEMBERSHIP_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Membership revocation is not authorized",
        )
    try:
        evidence = lifecycle.revoke_membership(
            tenant_id,
            membership_id,
            expected_version=payload.expected_version,
            reason=payload.reason,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
        )
    except (
        IdentityLifecycleConflict,
        IdentityLifecycleDenied,
        IdentityLifecycleNotFound,
        IdentityLifecycleUnavailable,
    ) as exc:
        _raise_lifecycle_error(exc)
    if (
        evidence.membership.tenant_id != tenant_id
        or evidence.membership.id != membership_id
        or evidence.provider_revocation_state != "NOT_EXECUTED"
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity lifecycle is temporarily unavailable",
        )
    return evidence


@router.post(
    "/tenants/{tenant_id}/identity/support-access",
    response_model=SupportAccessEvidence,
    status_code=status.HTTP_201_CREATED,
    summary="Request time-bound exact support access",
)
def request_support_access(
    request: Request,
    tenant_id: UUID,
    payload: SupportAccessCreate,
    authorization: CurrentTenantAuthorization,
    lifecycle: LifecycleDependency,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> SupportAccessEvidence:
    grant = _exact_grant(
        authorization,
        action="create",
        resource_type="support_access_collection",
        resource_id=str(tenant_id),
        purpose=REQUEST_SUPPORT_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Support access request is not authorized",
        )
    try:
        evidence = lifecycle.request_support_access(
            tenant_id,
            request=payload,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
            idempotency_key=_required_idempotency_key(request, idempotency_key),
        )
    except (
        IdentityLifecycleConflict,
        IdentityLifecycleDenied,
        IdentityLifecycleNotFound,
        IdentityLifecycleUnavailable,
    ) as exc:
        _raise_lifecycle_error(exc)
    if (
        evidence.request.tenant_id != tenant_id
        or evidence.request.target_principal_id != payload.target_principal_id
        or evidence.request.campaign_id != payload.campaign_id
        or evidence.request.workspace_id != payload.workspace_id
    ):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity lifecycle is temporarily unavailable",
        )
    return evidence


@router.post(
    "/tenants/{tenant_id}/identity/support-access/{support_request_id}/approve",
    response_model=SupportAccessEvidence,
    summary="Approve one time-bound support request",
)
def approve_support_access(
    request: Request,
    tenant_id: UUID,
    support_request_id: UUID,
    payload: SupportAccessApprove,
    authorization: CurrentTenantAuthorization,
    lifecycle: LifecycleDependency,
) -> SupportAccessEvidence:
    grant = _exact_grant(
        authorization,
        action="approve",
        resource_type="support_access_request",
        resource_id=str(support_request_id),
        purpose=APPROVE_SUPPORT_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Support access approval is not authorized",
        )
    try:
        evidence = lifecycle.approve_support_access(
            tenant_id,
            support_request_id,
            request=payload,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
        )
    except (
        IdentityLifecycleConflict,
        IdentityLifecycleDenied,
        IdentityLifecycleNotFound,
        IdentityLifecycleUnavailable,
    ) as exc:
        _raise_lifecycle_error(exc)
    if evidence.request.tenant_id != tenant_id or evidence.request.id != support_request_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity lifecycle is temporarily unavailable",
        )
    return evidence


@router.post(
    "/tenants/{tenant_id}/identity/support-access/{support_request_id}/revoke",
    response_model=SupportAccessEvidence,
    summary="Revoke one approved time-bound support request",
)
def revoke_support_access(
    request: Request,
    tenant_id: UUID,
    support_request_id: UUID,
    payload: SupportAccessRevoke,
    authorization: CurrentTenantAuthorization,
    lifecycle: LifecycleDependency,
) -> SupportAccessEvidence:
    grant = _exact_grant(
        authorization,
        action="revoke",
        resource_type="support_access_request",
        resource_id=str(support_request_id),
        purpose=REVOKE_SUPPORT_PURPOSE,
    )
    if grant is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Support access revocation is not authorized",
        )
    try:
        evidence = lifecycle.revoke_support_access(
            tenant_id,
            support_request_id,
            request=payload,
            principal_id=authorization.principal_id,
            authorization_grant_id=grant.grant_id,
            approval_receipt_id=grant.approval_receipt_id,
            authorization_purpose=grant.purpose,
            correlation_id=_correlation_id(request),
        )
    except (
        IdentityLifecycleConflict,
        IdentityLifecycleDenied,
        IdentityLifecycleNotFound,
        IdentityLifecycleUnavailable,
    ) as exc:
        _raise_lifecycle_error(exc)
    if evidence.request.tenant_id != tenant_id or evidence.request.id != support_request_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity lifecycle is temporarily unavailable",
        )
    return evidence
