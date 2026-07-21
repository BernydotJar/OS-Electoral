"""Tenant-scoped identity lifecycle transitions with no external provider effects."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ValidationError
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement

from campaignos.data.audit import (
    AuditScopeUnavailable,
    TenantAuditStreamLock,
    append_audit_event,
    canonical_hash,
    lock_tenant_audit_stream,
)
from campaignos.data.database import Database
from campaignos.data.idempotency import lock_idempotency_key
from campaignos.data.models import (
    ApplicationSession,
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
from campaignos.identity.lifecycle_contracts import (
    InvitationAcceptanceEvidence,
    InvitationCreate,
    InvitationCreateEvidence,
    InvitationMutationEvidence,
    InvitationPlanner,
    InvitationProjection,
    LocalInvitationPlanner,
    MembershipProjection,
    MembershipRevocationEvidence,
    SessionEvidence,
    SessionProjection,
    SessionRevoke,
    SupportAccessApprove,
    SupportAccessCreate,
    SupportAccessEvidence,
    SupportAccessProjection,
    SupportAccessRevoke,
    normalize_email,
)
from campaignos.identity.models import AuthenticatedPrincipal

INVITATION_CREATE_OPERATION = "identity.invitation.create"
INVITATION_ACCEPT_OPERATION = "identity.invitation.accept"
SUPPORT_REQUEST_OPERATION = "identity.support_access.request"
SUPPORT_ROLE_PREFIX = "time_bound_support:"


class IdentityLifecycleNotFound(LookupError):
    """The exact tenant-scoped lifecycle resource was not found."""


class IdentityLifecycleConflict(RuntimeError):
    """A lifecycle state transition conflicts with current durable state."""


class IdentityLifecycleIdempotencyConflict(IdentityLifecycleConflict):
    """An idempotency key was reused for a different bound intent."""


class IdentityLifecycleVersionConflict(IdentityLifecycleConflict):
    """The caller's aggregate version is stale."""


class IdentityLifecycleDenied(PermissionError):
    """The verified identity cannot perform the requested lifecycle transition."""


class IdentityLifecycleUnavailable(RuntimeError):
    """The lifecycle boundary cannot safely complete."""


class _InvitationExpired(RuntimeError):
    def __init__(self, invitation_id: UUID) -> None:
        super().__init__("Invitation has expired")
        self.invitation_id = invitation_id


class _SessionExpired(RuntimeError):
    def __init__(self, session_id: UUID) -> None:
        super().__init__("Application session has expired")
        self.session_id = session_id


class _SupportAccessExpired(RuntimeError):
    def __init__(self, request_id: UUID) -> None:
        super().__init__("Support access request has expired")
        self.request_id = request_id


class IdentityLifecycle(Protocol):
    def create_invitation(
        self,
        tenant_id: UUID,
        *,
        request: InvitationCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> InvitationCreateEvidence: ...

    def accept_invitation(
        self,
        tenant_id: UUID,
        invitation_id: UUID,
        *,
        principal: AuthenticatedPrincipal,
        correlation_id: str,
        idempotency_key: str,
    ) -> InvitationAcceptanceEvidence: ...

    def revoke_invitation(
        self,
        tenant_id: UUID,
        invitation_id: UUID,
        *,
        expected_version: int,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> InvitationMutationEvidence: ...

    def register_session(
        self,
        tenant_id: UUID,
        *,
        principal: AuthenticatedPrincipal,
        application_principal_id: UUID,
        correlation_id: str,
    ) -> SessionEvidence: ...

    def revoke_session(
        self,
        tenant_id: UUID,
        session_id: UUID,
        *,
        request: SessionRevoke,
        principal_id: UUID,
        allow_cross_principal: bool,
        authorization_grant_id: UUID | None,
        approval_receipt_id: str | None,
        authorization_purpose: str,
        correlation_id: str,
    ) -> SessionEvidence: ...

    def revoke_membership(
        self,
        tenant_id: UUID,
        membership_id: UUID,
        *,
        expected_version: int,
        reason: str,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> MembershipRevocationEvidence: ...

    def request_support_access(
        self,
        tenant_id: UUID,
        *,
        request: SupportAccessCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> SupportAccessEvidence: ...

    def approve_support_access(
        self,
        tenant_id: UUID,
        request_id: UUID,
        *,
        request: SupportAccessApprove,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> SupportAccessEvidence: ...

    def revoke_support_access(
        self,
        tenant_id: UUID,
        request_id: UUID,
        *,
        request: SupportAccessRevoke,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> SupportAccessEvidence: ...


class UnavailableIdentityLifecycle:
    def __getattr__(self, name: str) -> object:
        del name
        raise IdentityLifecycleUnavailable("Identity lifecycle is unavailable")


def _as_utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _optional_utc(value: datetime | None) -> datetime | None:
    return _as_utc(value) if value is not None else None


def _campaign_predicate(
    column: InstrumentedAttribute[UUID | None],
    campaign_id: UUID | None,
) -> ColumnElement[bool]:
    if campaign_id is None:
        return column.is_(None)
    return column == campaign_id


def _scope_key(value: UUID | None, *, empty: str) -> str:
    return value.hex if value is not None else empty


def _invitation_projection(row: IdentityInvitation) -> InvitationProjection:
    return InvitationProjection.model_validate(
        {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "campaign_id": row.campaign_id,
            "email": row.email,
            "status": row.status,
            "provider": row.provider,
            "provider_reference": row.provider_reference,
            "expires_at": _as_utc(row.expires_at),
            "accepted_at": _optional_utc(row.accepted_at),
            "membership_id": row.membership_id,
            "revoked_at": _optional_utc(row.revoked_at),
            "version": row.version,
        }
    )


def _membership_projection(row: Membership) -> MembershipProjection:
    return MembershipProjection.model_validate(
        {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "principal_id": row.principal_id,
            "campaign_id": row.campaign_id,
            "status": row.status,
            "valid_from": _as_utc(row.valid_from),
            "expires_at": _optional_utc(row.expires_at),
            "revoked_at": _optional_utc(row.revoked_at),
            "version": row.version,
        }
    )


def _session_projection(row: ApplicationSession) -> SessionProjection:
    return SessionProjection.model_validate(
        {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "principal_id": row.principal_id,
            "status": row.status,
            "authenticated_at": _as_utc(row.authenticated_at),
            "last_seen_at": _as_utc(row.last_seen_at),
            "expires_at": _as_utc(row.expires_at),
            "revoked_at": _optional_utc(row.revoked_at),
            "revocation_reason": row.revocation_reason,
            "version": row.version,
        }
    )


def _support_projection(row: SupportAccessRequest) -> SupportAccessProjection:
    return SupportAccessProjection.model_validate(
        {
            "id": row.id,
            "tenant_id": row.tenant_id,
            "requested_by_principal_id": row.requested_by_principal_id,
            "target_principal_id": row.target_principal_id,
            "campaign_id": row.campaign_id,
            "workspace_id": row.workspace_id,
            "action": row.action,
            "resource_type": row.resource_type,
            "resource_id": row.resource_id,
            "purpose": row.purpose,
            "reason": row.reason,
            "status": row.status,
            "requested_at": _as_utc(row.requested_at),
            "expires_at": _as_utc(row.expires_at),
            "decided_at": _optional_utc(row.decided_at),
            "decided_by_principal_id": row.decided_by_principal_id,
            "approval_receipt_id": row.approval_receipt_id,
            "membership_id": row.membership_id,
            "role_assignment_id": row.role_assignment_id,
            "permission_grant_id": row.permission_grant_id,
            "created_membership": row.created_membership,
            "revoked_at": _optional_utc(row.revoked_at),
            "version": row.version,
        }
    )


def _replay[ModelT: BaseModel](
    session: Session,
    *,
    tenant_id: UUID,
    operation: str,
    idempotency_key: str,
    request_digest: str,
    response_model: type[ModelT],
) -> ModelT | None:
    existing = session.scalar(
        select(IdempotencyRecord)
        .where(
            IdempotencyRecord.tenant_id == tenant_id,
            IdempotencyRecord.operation == operation,
            IdempotencyRecord.idempotency_key == idempotency_key,
        )
        .with_for_update()
    )
    if existing is None:
        return None
    if existing.request_digest != request_digest:
        raise IdentityLifecycleIdempotencyConflict(
            "Idempotency key conflicts with a previous identity request"
        )
    return response_model.model_validate(existing.response_payload)


def _store_replay(
    session: Session,
    *,
    tenant_id: UUID,
    principal_id: UUID,
    operation: str,
    idempotency_key: str,
    request_digest: str,
    response: BaseModel,
    created_at: datetime,
) -> None:
    session.add(
        IdempotencyRecord(
            tenant_id=tenant_id,
            principal_id=principal_id,
            operation=operation,
            idempotency_key=idempotency_key,
            request_digest=request_digest,
            response_payload=response.model_dump(mode="json"),
            created_at=created_at,
        )
    )


def _require_active_scope(
    session: Session,
    *,
    tenant_id: UUID,
    campaign_id: UUID | None,
    workspace_id: UUID | None = None,
) -> None:
    active_tenant = session.scalar(
        select(Tenant.id).where(Tenant.id == tenant_id, Tenant.status == "ACTIVE")
    )
    if active_tenant is None:
        raise IdentityLifecycleNotFound("Identity lifecycle scope was not found")
    if campaign_id is not None:
        active_campaign = session.scalar(
            select(Campaign.id).where(
                Campaign.tenant_id == tenant_id,
                Campaign.id == campaign_id,
                Campaign.status.in_(("DRAFT", "ACTIVE")),
            )
        )
        if active_campaign is None:
            raise IdentityLifecycleNotFound("Identity lifecycle scope was not found")
    if workspace_id is not None:
        active_workspace = session.scalar(
            select(Workspace.id).where(
                Workspace.tenant_id == tenant_id,
                Workspace.campaign_id == campaign_id,
                Workspace.id == workspace_id,
                Workspace.status == "ACTIVE",
            )
        )
        if active_workspace is None:
            raise IdentityLifecycleNotFound("Identity lifecycle scope was not found")


def _require_application_principal(
    session: Session,
    principal_id: UUID,
) -> Principal:
    principal = session.scalar(
        select(Principal).where(Principal.id == principal_id, Principal.disabled_at.is_(None))
    )
    if principal is None:
        raise IdentityLifecycleDenied("Identity lifecycle is not authorized")
    return principal


def _integrity_constraint_name(exc: IntegrityError) -> str | None:
    diagnostic = getattr(exc.orig, "diag", None)
    value = getattr(diagnostic, "constraint_name", None)
    return value if isinstance(value, str) else None


def _is_integrity_conflict(exc: IntegrityError, constraint_name: str) -> bool:
    if _integrity_constraint_name(exc) == constraint_name:
        return True
    return constraint_name in str(exc.orig).lower()


def _expire_invitation_row(
    session: Session,
    *,
    audit_lock: TenantAuditStreamLock,
    invitation: IdentityInvitation,
    principal_id: UUID | None,
    correlation_id: str,
    observation: str,
) -> None:
    operation_at = audit_lock.acquired_at
    if invitation.status != "PENDING" or _as_utc(invitation.expires_at) > operation_at:
        return
    invitation.status = "EXPIRED"
    invitation.version += 1
    invitation.updated_at = operation_at
    append_audit_event(
        session,
        audit_lock=audit_lock,
        campaign_id=invitation.campaign_id,
        workspace_id=None,
        principal_id=principal_id,
        event_type="identity.invitation.expired",
        resource_type="membership_invitation",
        resource_id=str(invitation.id),
        payload={
            "observation": observation,
            "correlation_id": correlation_id,
            "external_effects": "NONE",
        },
    )


def _expire_session_row(
    session: Session,
    *,
    audit_lock: TenantAuditStreamLock,
    application_session: ApplicationSession,
    principal_id: UUID | None,
    correlation_id: str,
    observation: str,
) -> None:
    operation_at = audit_lock.acquired_at
    if application_session.status != "ACTIVE":
        return
    if _as_utc(application_session.expires_at) > operation_at:
        return
    application_session.status = "EXPIRED"
    application_session.version += 1
    application_session.updated_at = operation_at
    append_audit_event(
        session,
        audit_lock=audit_lock,
        campaign_id=None,
        workspace_id=None,
        principal_id=principal_id,
        event_type="identity.session.expired",
        resource_type="application_session",
        resource_id=str(application_session.id),
        payload={
            "target_principal_id": str(application_session.principal_id),
            "observation": observation,
            "correlation_id": correlation_id,
            "external_effects": "NONE",
        },
    )


def _expire_support_row(
    session: Session,
    *,
    audit_lock: TenantAuditStreamLock,
    support_request: SupportAccessRequest,
    principal_id: UUID | None,
    correlation_id: str,
    observation: str,
) -> None:
    operation_at = audit_lock.acquired_at
    if support_request.status not in {"PENDING", "APPROVED"}:
        return
    if _as_utc(support_request.expires_at) > operation_at:
        return
    expired_grant_id: UUID | None = None
    if support_request.permission_grant_id is not None:
        permission_grant = session.scalar(
            select(PermissionGrant)
            .where(
                PermissionGrant.tenant_id == support_request.tenant_id,
                PermissionGrant.id == support_request.permission_grant_id,
            )
            .with_for_update()
        )
        if permission_grant is not None and permission_grant.status == "ACTIVE":
            permission_grant.status = "EXPIRED"
            permission_grant.updated_at = operation_at
            expired_grant_id = permission_grant.id
    support_request.status = "EXPIRED"
    support_request.version += 1
    support_request.updated_at = operation_at
    append_audit_event(
        session,
        audit_lock=audit_lock,
        campaign_id=support_request.campaign_id,
        workspace_id=support_request.workspace_id,
        principal_id=principal_id,
        event_type="identity.support_access.expired",
        resource_type="support_access_request",
        resource_id=str(support_request.id),
        payload={
            "target_principal_id": str(support_request.target_principal_id),
            "expired_permission_grant_id": (
                str(expired_grant_id) if expired_grant_id is not None else None
            ),
            "observation": observation,
            "correlation_id": correlation_id,
            "external_effects": "NONE",
        },
    )


@dataclass(slots=True)
class SqlAlchemyIdentityLifecycle:
    database: Database
    invitation_planner: InvitationPlanner = field(default_factory=LocalInvitationPlanner)

    def _persist_invitation_expiry(
        self,
        tenant_id: UUID,
        invitation_id: UUID,
        *,
        principal_id: UUID | None,
        correlation_id: str,
        observation: str,
    ) -> None:
        with self.database.tenant_transaction(tenant_id) as session:
            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            invitation = session.scalar(
                select(IdentityInvitation)
                .where(
                    IdentityInvitation.tenant_id == tenant_id,
                    IdentityInvitation.id == invitation_id,
                )
                .with_for_update()
            )
            if invitation is None:
                raise IdentityLifecycleNotFound("Invitation was not found")
            _expire_invitation_row(
                session,
                audit_lock=audit_lock,
                invitation=invitation,
                principal_id=principal_id,
                correlation_id=correlation_id,
                observation=observation,
            )
            session.flush()

    def _persist_session_expiry(
        self,
        tenant_id: UUID,
        session_id: UUID,
        *,
        principal_id: UUID | None,
        correlation_id: str,
        observation: str,
    ) -> None:
        with self.database.tenant_transaction(tenant_id) as session:
            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            application_session = session.scalar(
                select(ApplicationSession)
                .where(
                    ApplicationSession.tenant_id == tenant_id,
                    ApplicationSession.id == session_id,
                )
                .with_for_update()
            )
            if application_session is None:
                raise IdentityLifecycleNotFound("Application session was not found")
            _expire_session_row(
                session,
                audit_lock=audit_lock,
                application_session=application_session,
                principal_id=principal_id,
                correlation_id=correlation_id,
                observation=observation,
            )
            session.flush()

    def _persist_support_expiry(
        self,
        tenant_id: UUID,
        request_id: UUID,
        *,
        principal_id: UUID | None,
        correlation_id: str,
        observation: str,
    ) -> None:
        with self.database.tenant_transaction(tenant_id) as session:
            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            support_request = session.scalar(
                select(SupportAccessRequest)
                .where(
                    SupportAccessRequest.tenant_id == tenant_id,
                    SupportAccessRequest.id == request_id,
                )
                .with_for_update()
            )
            if support_request is None:
                raise IdentityLifecycleNotFound("Support access request was not found")
            _expire_support_row(
                session,
                audit_lock=audit_lock,
                support_request=support_request,
                principal_id=principal_id,
                correlation_id=correlation_id,
                observation=observation,
            )
            session.flush()

    def create_invitation(
        self,
        tenant_id: UUID,
        *,
        request: InvitationCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> InvitationCreateEvidence:
        try:
            return self._create_invitation(
                tenant_id,
                request=request,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        except (
            IdentityLifecycleConflict,
            IdentityLifecycleDenied,
            IdentityLifecycleNotFound,
        ):
            raise
        except IntegrityError as exc:
            if _is_integrity_conflict(exc, "uq_identity_invitations_pending_target"):
                raise IdentityLifecycleConflict("A pending invitation already exists") from exc
            raise IdentityLifecycleUnavailable("Identity lifecycle is unavailable") from exc
        except (
            AuditScopeUnavailable,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise IdentityLifecycleUnavailable("Identity lifecycle is unavailable") from exc

    def _create_invitation(
        self,
        tenant_id: UUID,
        *,
        request: InvitationCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> InvitationCreateEvidence:
        digest = canonical_hash(
            {
                "tenant_id": str(tenant_id),
                "request": request.model_dump(mode="json"),
                "principal_id": str(principal_id),
                "authorization_grant_id": str(authorization_grant_id),
                "approval_receipt_id": approval_receipt_id,
                "authorization_purpose": authorization_purpose,
            }
        )
        invitation_id = uuid4()
        outbox_event_id = uuid4()
        with self.database.tenant_transaction(tenant_id) as session:
            lock_idempotency_key(
                session,
                tenant_id=tenant_id,
                operation=INVITATION_CREATE_OPERATION,
                idempotency_key=idempotency_key,
            )
            replay = _replay(
                session,
                tenant_id=tenant_id,
                operation=INVITATION_CREATE_OPERATION,
                idempotency_key=idempotency_key,
                request_digest=digest,
                response_model=InvitationCreateEvidence,
            )
            if replay is not None:
                return replay

            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            operation_at = audit_lock.acquired_at
            _require_active_scope(
                session,
                tenant_id=tenant_id,
                campaign_id=request.campaign_id,
            )
            _require_application_principal(session, principal_id)
            scope_key = _scope_key(request.campaign_id, empty="TENANT")
            stale_invitations = list(
                session.scalars(
                    select(IdentityInvitation)
                    .where(
                        IdentityInvitation.tenant_id == tenant_id,
                        IdentityInvitation.email == request.email,
                        IdentityInvitation.scope_key == scope_key,
                        IdentityInvitation.status == "PENDING",
                        IdentityInvitation.expires_at <= operation_at,
                    )
                    .with_for_update()
                )
            )
            for stale_invitation in stale_invitations:
                _expire_invitation_row(
                    session,
                    audit_lock=audit_lock,
                    invitation=stale_invitation,
                    principal_id=principal_id,
                    correlation_id=correlation_id,
                    observation="OBSERVED_DURING_INVITATION_CREATE",
                )
            duplicate = session.scalar(
                select(IdentityInvitation.id).where(
                    IdentityInvitation.tenant_id == tenant_id,
                    IdentityInvitation.email == request.email,
                    IdentityInvitation.scope_key == scope_key,
                    IdentityInvitation.status == "PENDING",
                    IdentityInvitation.expires_at > operation_at,
                )
            )
            if duplicate is not None:
                raise IdentityLifecycleConflict("A pending invitation already exists")

            expires_at = operation_at + timedelta(hours=request.expires_in_hours)
            delivery_plan = self.invitation_planner.plan(
                invitation_id=invitation_id,
                tenant_id=tenant_id,
                campaign_id=request.campaign_id,
                email=request.email,
                expires_at=expires_at,
            )
            invitation = IdentityInvitation(
                id=invitation_id,
                tenant_id=tenant_id,
                campaign_id=request.campaign_id,
                scope_key=scope_key,
                email=request.email,
                status="PENDING",
                purpose=authorization_purpose,
                invited_by_principal_id=principal_id,
                provider=delivery_plan.provider,
                provider_reference=delivery_plan.provider_reference,
                expires_at=expires_at,
                version=1,
                created_at=operation_at,
                updated_at=operation_at,
            )
            session.add(invitation)
            session.flush()
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=request.campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="identity.invitation.created",
                resource_type="membership_invitation",
                resource_id=str(invitation_id),
                payload={
                    "email": request.email,
                    "provider": delivery_plan.provider,
                    "provider_reference": delivery_plan.provider_reference,
                    "delivery_state": delivery_plan.delivery_state,
                    "expires_at": expires_at.isoformat(),
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "external_effects": "NONE",
                },
            )
            session.add(
                OutboxEvent(
                    id=outbox_event_id,
                    tenant_id=tenant_id,
                    campaign_id=request.campaign_id,
                    topic="identity.invitation.planned",
                    payload={
                        "invitation_id": str(invitation_id),
                        "audit_event_id": str(audit.event_id),
                        "provider": delivery_plan.provider,
                        "provider_reference": delivery_plan.provider_reference,
                        "delivery_state": "NOT_SENT",
                        "external_effects": "NONE",
                    },
                    status="PENDING",
                    attempts=0,
                    available_at=operation_at,
                    created_at=operation_at,
                )
            )
            evidence = InvitationCreateEvidence(
                invitation=_invitation_projection(invitation),
                delivery_plan=delivery_plan,
                audit_event_id=audit.event_id,
                outbox_event_id=outbox_event_id,
            )
            _store_replay(
                session,
                tenant_id=tenant_id,
                principal_id=principal_id,
                operation=INVITATION_CREATE_OPERATION,
                idempotency_key=idempotency_key,
                request_digest=digest,
                response=evidence,
                created_at=operation_at,
            )
            session.flush()
        return evidence

    def accept_invitation(
        self,
        tenant_id: UUID,
        invitation_id: UUID,
        *,
        principal: AuthenticatedPrincipal,
        correlation_id: str,
        idempotency_key: str,
    ) -> InvitationAcceptanceEvidence:
        try:
            return self._accept_invitation(
                tenant_id,
                invitation_id,
                principal=principal,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        except _InvitationExpired as exc:
            try:
                self._persist_invitation_expiry(
                    tenant_id,
                    exc.invitation_id,
                    principal_id=None,
                    correlation_id=correlation_id,
                    observation="OBSERVED_DURING_INVITATION_ACCEPT",
                )
            except (
                AuditScopeUnavailable,
                IdentityLifecycleNotFound,
                SQLAlchemyError,
                ValidationError,
                ValueError,
            ) as persist_exc:
                raise IdentityLifecycleUnavailable(
                    "Identity lifecycle is unavailable"
                ) from persist_exc
            raise IdentityLifecycleConflict("Invitation has expired") from exc
        except (
            IdentityLifecycleConflict,
            IdentityLifecycleDenied,
            IdentityLifecycleNotFound,
        ):
            raise
        except (
            AuditScopeUnavailable,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise IdentityLifecycleUnavailable("Identity lifecycle is unavailable") from exc

    def _accept_invitation(
        self,
        tenant_id: UUID,
        invitation_id: UUID,
        *,
        principal: AuthenticatedPrincipal,
        correlation_id: str,
        idempotency_key: str,
    ) -> InvitationAcceptanceEvidence:
        if principal.email is None or principal.email_verified is not True:
            raise IdentityLifecycleDenied("Invitation acceptance requires a verified email")
        email = normalize_email(principal.email)
        digest = canonical_hash(
            {
                "tenant_id": str(tenant_id),
                "invitation_id": str(invitation_id),
                "issuer": principal.issuer,
                "subject": principal.subject,
                "email": email,
            }
        )
        with self.database.tenant_transaction(tenant_id) as session:
            lock_idempotency_key(
                session,
                tenant_id=tenant_id,
                operation=INVITATION_ACCEPT_OPERATION,
                idempotency_key=idempotency_key,
            )
            replay = _replay(
                session,
                tenant_id=tenant_id,
                operation=INVITATION_ACCEPT_OPERATION,
                idempotency_key=idempotency_key,
                request_digest=digest,
                response_model=InvitationAcceptanceEvidence,
            )
            if replay is not None:
                return replay

            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            operation_at = audit_lock.acquired_at
            invitation = session.scalar(
                select(IdentityInvitation)
                .where(
                    IdentityInvitation.tenant_id == tenant_id,
                    IdentityInvitation.id == invitation_id,
                )
                .with_for_update()
            )
            if invitation is None:
                raise IdentityLifecycleNotFound("Invitation was not found")
            if invitation.status != "PENDING":
                raise IdentityLifecycleConflict("Invitation is not pending")
            if invitation.email != email:
                raise IdentityLifecycleDenied("Invitation identity does not match")
            if _as_utc(invitation.expires_at) <= operation_at:
                raise _InvitationExpired(invitation.id)
            _require_active_scope(
                session,
                tenant_id=tenant_id,
                campaign_id=invitation.campaign_id,
            )

            application_principal = session.scalar(
                select(Principal)
                .where(
                    Principal.issuer == principal.issuer,
                    Principal.subject == principal.subject,
                )
                .with_for_update()
            )
            if application_principal is None:
                application_principal = Principal(
                    id=uuid4(),
                    issuer=principal.issuer,
                    subject=principal.subject,
                    display_name=principal.display_name,
                    email=email,
                    created_at=operation_at,
                    updated_at=operation_at,
                )
                session.add(application_principal)
                session.flush()
            elif application_principal.disabled_at is not None:
                raise IdentityLifecycleDenied("Invitation identity does not match")
            else:
                application_principal.display_name = (
                    principal.display_name or application_principal.display_name
                )
                application_principal.email = email
                application_principal.updated_at = operation_at

            existing_membership = session.scalar(
                select(Membership)
                .where(
                    Membership.tenant_id == tenant_id,
                    Membership.principal_id == application_principal.id,
                    _campaign_predicate(Membership.campaign_id, invitation.campaign_id),
                )
                .with_for_update()
            )
            if existing_membership is not None:
                if existing_membership.status != "REVOKED":
                    raise IdentityLifecycleConflict("Membership already exists")
                existing_membership.status = "ACTIVE"
                existing_membership.valid_from = operation_at
                existing_membership.expires_at = None
                existing_membership.revoked_at = None
                existing_membership.version += 1
                existing_membership.updated_at = operation_at
                membership = existing_membership
            else:
                membership = Membership(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    principal_id=application_principal.id,
                    campaign_id=invitation.campaign_id,
                    status="ACTIVE",
                    valid_from=operation_at,
                    expires_at=None,
                    revoked_at=None,
                    version=1,
                    created_at=operation_at,
                    updated_at=operation_at,
                )
                session.add(membership)
            session.flush()

            invitation.status = "ACCEPTED"
            invitation.accepted_at = operation_at
            invitation.accepted_by_principal_id = application_principal.id
            invitation.membership_id = membership.id
            invitation.version += 1
            invitation.updated_at = operation_at
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=invitation.campaign_id,
                workspace_id=None,
                principal_id=application_principal.id,
                event_type="identity.invitation.accepted",
                resource_type="membership_invitation",
                resource_id=str(invitation.id),
                payload={
                    "membership_id": str(membership.id),
                    "principal_id": str(application_principal.id),
                    "correlation_id": correlation_id,
                    "implicit_roles": [],
                    "implicit_grants": [],
                    "external_effects": "NONE",
                },
            )
            evidence = InvitationAcceptanceEvidence(
                invitation=_invitation_projection(invitation),
                membership=_membership_projection(membership),
                principal_id=application_principal.id,
                audit_event_id=audit.event_id,
            )
            _store_replay(
                session,
                tenant_id=tenant_id,
                principal_id=application_principal.id,
                operation=INVITATION_ACCEPT_OPERATION,
                idempotency_key=idempotency_key,
                request_digest=digest,
                response=evidence,
                created_at=operation_at,
            )
            session.flush()
        return evidence

    def revoke_invitation(
        self,
        tenant_id: UUID,
        invitation_id: UUID,
        *,
        expected_version: int,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> InvitationMutationEvidence:
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                operation_at = audit_lock.acquired_at
                _require_application_principal(session, principal_id)
                invitation = session.scalar(
                    select(IdentityInvitation)
                    .where(
                        IdentityInvitation.tenant_id == tenant_id,
                        IdentityInvitation.id == invitation_id,
                    )
                    .with_for_update()
                )
                if invitation is None:
                    raise IdentityLifecycleNotFound("Invitation was not found")
                if invitation.version != expected_version:
                    raise IdentityLifecycleVersionConflict("Invitation version is stale")
                if invitation.status != "PENDING":
                    raise IdentityLifecycleConflict("Invitation is not pending")
                invitation.status = "REVOKED"
                invitation.revoked_at = operation_at
                invitation.revoked_by_principal_id = principal_id
                invitation.version += 1
                invitation.updated_at = operation_at
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=invitation.campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="identity.invitation.revoked",
                    resource_type="membership_invitation",
                    resource_id=str(invitation.id),
                    payload={
                        "authorization_grant_id": str(authorization_grant_id),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "external_effects": "NONE",
                    },
                )
                evidence = InvitationMutationEvidence(
                    invitation=_invitation_projection(invitation),
                    audit_event_id=audit.event_id,
                )
                session.flush()
            return evidence
        except (
            IdentityLifecycleConflict,
            IdentityLifecycleDenied,
            IdentityLifecycleNotFound,
        ):
            raise
        except (
            AuditScopeUnavailable,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise IdentityLifecycleUnavailable("Identity lifecycle is unavailable") from exc

    def register_session(
        self,
        tenant_id: UUID,
        *,
        principal: AuthenticatedPrincipal,
        application_principal_id: UUID,
        correlation_id: str,
    ) -> SessionEvidence:
        if principal.session_id is None or principal.expires_at is None:
            raise IdentityLifecycleDenied("A provider session identifier and expiry are required")
        provider_digest = canonical_hash(
            {
                "issuer": principal.issuer,
                "subject": principal.subject,
                "provider_session_id": principal.session_id,
            }
        )
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                operation_at = audit_lock.acquired_at
                _require_active_scope(
                    session,
                    tenant_id=tenant_id,
                    campaign_id=None,
                )
                application_principal = _require_application_principal(
                    session, application_principal_id
                )
                if (
                    application_principal.issuer != principal.issuer
                    or application_principal.subject != principal.subject
                ):
                    raise IdentityLifecycleDenied("Session identity does not match")
                expires_at = _as_utc(principal.expires_at)
                if expires_at <= operation_at:
                    raise IdentityLifecycleDenied("Provider session has expired")
                row = session.scalar(
                    select(ApplicationSession)
                    .where(
                        ApplicationSession.tenant_id == tenant_id,
                        ApplicationSession.provider_session_digest == provider_digest,
                    )
                    .with_for_update()
                )
                created = row is None
                if row is None:
                    row = ApplicationSession(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        principal_id=application_principal_id,
                        provider_session_digest=provider_digest,
                        status="ACTIVE",
                        authenticated_at=_as_utc(principal.authenticated_at),
                        last_seen_at=operation_at,
                        expires_at=expires_at,
                        version=1,
                        created_at=operation_at,
                        updated_at=operation_at,
                    )
                    session.add(row)
                else:
                    if row.principal_id != application_principal_id:
                        raise IdentityLifecycleUnavailable("Session scope is invalid")
                    if row.status == "REVOKED":
                        raise IdentityLifecycleConflict("Application session is revoked")
                    if _as_utc(row.expires_at) <= operation_at:
                        raise _SessionExpired(row.id)
                    row.last_seen_at = operation_at
                    row.expires_at = expires_at
                    row.version += 1
                    row.updated_at = operation_at
                session.flush()
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=None,
                    workspace_id=None,
                    principal_id=application_principal_id,
                    event_type=(
                        "identity.session.registered" if created else "identity.session.refreshed"
                    ),
                    resource_type="application_session",
                    resource_id=str(row.id),
                    payload={
                        "session_version": row.version,
                        "expires_at": expires_at.isoformat(),
                        "correlation_id": correlation_id,
                        "provider_session_digest_recorded": True,
                        "raw_provider_session_stored": False,
                        "external_effects": "NONE",
                    },
                )
                evidence = SessionEvidence(
                    session=_session_projection(row),
                    audit_event_id=audit.event_id,
                    created=created,
                )
                session.flush()
            return evidence
        except _SessionExpired as exc:
            try:
                self._persist_session_expiry(
                    tenant_id,
                    exc.session_id,
                    principal_id=application_principal_id,
                    correlation_id=correlation_id,
                    observation="OBSERVED_DURING_SESSION_REGISTER",
                )
            except (
                AuditScopeUnavailable,
                IdentityLifecycleNotFound,
                SQLAlchemyError,
                ValidationError,
                ValueError,
            ) as persist_exc:
                raise IdentityLifecycleUnavailable(
                    "Identity lifecycle is unavailable"
                ) from persist_exc
            raise IdentityLifecycleConflict("Application session is expired") from exc
        except (
            IdentityLifecycleConflict,
            IdentityLifecycleDenied,
            IdentityLifecycleNotFound,
        ):
            raise
        except (
            AuditScopeUnavailable,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise IdentityLifecycleUnavailable("Identity lifecycle is unavailable") from exc

    def revoke_session(
        self,
        tenant_id: UUID,
        session_id: UUID,
        *,
        request: SessionRevoke,
        principal_id: UUID,
        allow_cross_principal: bool,
        authorization_grant_id: UUID | None,
        approval_receipt_id: str | None,
        authorization_purpose: str,
        correlation_id: str,
    ) -> SessionEvidence:
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                operation_at = audit_lock.acquired_at
                _require_application_principal(session, principal_id)
                row = session.scalar(
                    select(ApplicationSession)
                    .where(
                        ApplicationSession.tenant_id == tenant_id,
                        ApplicationSession.id == session_id,
                    )
                    .with_for_update()
                )
                if row is None:
                    raise IdentityLifecycleNotFound("Application session was not found")
                if row.version != request.expected_version:
                    raise IdentityLifecycleVersionConflict("Application session version is stale")
                if row.principal_id != principal_id and not allow_cross_principal:
                    raise IdentityLifecycleDenied(
                        "Application session revocation is not authorized"
                    )
                if row.status != "ACTIVE":
                    raise IdentityLifecycleConflict("Application session is not active")
                row.status = "REVOKED"
                row.revoked_at = operation_at
                row.revoked_by_principal_id = principal_id
                row.revocation_reason = request.reason
                row.version += 1
                row.updated_at = operation_at
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=None,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="identity.session.revoked",
                    resource_type="application_session",
                    resource_id=str(row.id),
                    payload={
                        "target_principal_id": str(row.principal_id),
                        "reason": request.reason,
                        "authorization_grant_id": (
                            str(authorization_grant_id)
                            if authorization_grant_id is not None
                            else None
                        ),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "provider_revocation_state": "NOT_EXECUTED",
                        "external_effects": "NONE",
                    },
                )
                evidence = SessionEvidence(
                    session=_session_projection(row),
                    audit_event_id=audit.event_id,
                    created=False,
                )
                session.flush()
            return evidence
        except (
            IdentityLifecycleConflict,
            IdentityLifecycleDenied,
            IdentityLifecycleNotFound,
        ):
            raise
        except (
            AuditScopeUnavailable,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise IdentityLifecycleUnavailable("Identity lifecycle is unavailable") from exc

    def revoke_membership(
        self,
        tenant_id: UUID,
        membership_id: UUID,
        *,
        expected_version: int,
        reason: str,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> MembershipRevocationEvidence:
        normalized_reason = " ".join(reason.split())
        if len(normalized_reason) < 3 or len(normalized_reason) > 255:
            raise IdentityLifecycleConflict("Membership revocation reason is invalid")
        outbox_event_id = uuid4()
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                operation_at = audit_lock.acquired_at
                _require_application_principal(session, principal_id)
                membership = session.scalar(
                    select(Membership)
                    .where(
                        Membership.tenant_id == tenant_id,
                        Membership.id == membership_id,
                    )
                    .with_for_update()
                )
                if membership is None:
                    raise IdentityLifecycleNotFound("Membership was not found")
                if membership.version != expected_version:
                    raise IdentityLifecycleVersionConflict("Membership version is stale")
                if membership.status == "REVOKED":
                    raise IdentityLifecycleConflict("Membership is already revoked")

                grant_rows = list(
                    session.scalars(
                        select(PermissionGrant)
                        .where(
                            PermissionGrant.tenant_id == tenant_id,
                            PermissionGrant.membership_id == membership_id,
                            PermissionGrant.status == "ACTIVE",
                        )
                        .with_for_update()
                    )
                )
                role_rows = list(
                    session.scalars(
                        select(RoleAssignment)
                        .where(
                            RoleAssignment.tenant_id == tenant_id,
                            RoleAssignment.membership_id == membership_id,
                            or_(
                                RoleAssignment.expires_at.is_(None),
                                RoleAssignment.expires_at > operation_at,
                            ),
                        )
                        .with_for_update()
                    )
                )
                session_rows = list(
                    session.scalars(
                        select(ApplicationSession)
                        .where(
                            ApplicationSession.tenant_id == tenant_id,
                            ApplicationSession.principal_id == membership.principal_id,
                            ApplicationSession.status == "ACTIVE",
                        )
                        .with_for_update()
                    )
                )
                for grant in grant_rows:
                    grant.status = "REVOKED"
                    grant.updated_at = operation_at
                for role in role_rows:
                    role.expires_at = operation_at
                    role.updated_at = operation_at
                for application_session in session_rows:
                    application_session.status = "REVOKED"
                    application_session.revoked_at = operation_at
                    application_session.revoked_by_principal_id = principal_id
                    application_session.revocation_reason = "Membership revoked"
                    application_session.version += 1
                    application_session.updated_at = operation_at
                membership.status = "REVOKED"
                membership.revoked_at = operation_at
                membership.version += 1
                membership.updated_at = operation_at
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=membership.campaign_id,
                    workspace_id=None,
                    principal_id=principal_id,
                    event_type="identity.membership.revoked",
                    resource_type="membership",
                    resource_id=str(membership.id),
                    payload={
                        "target_principal_id": str(membership.principal_id),
                        "reason": normalized_reason,
                        "revoked_grant_count": len(grant_rows),
                        "expired_role_count": len(role_rows),
                        "revoked_session_count": len(session_rows),
                        "authorization_grant_id": str(authorization_grant_id),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "provider_revocation_state": "NOT_EXECUTED",
                        "external_effects": "NONE",
                    },
                )
                session.add(
                    OutboxEvent(
                        id=outbox_event_id,
                        tenant_id=tenant_id,
                        campaign_id=membership.campaign_id,
                        topic="identity.membership.revoked",
                        payload={
                            "membership_id": str(membership.id),
                            "principal_id": str(membership.principal_id),
                            "audit_event_id": str(audit.event_id),
                            "provider_revocation_state": "NOT_EXECUTED",
                            "external_effects": "NONE",
                        },
                        status="PENDING",
                        attempts=0,
                        available_at=operation_at,
                        created_at=operation_at,
                    )
                )
                evidence = MembershipRevocationEvidence(
                    membership=_membership_projection(membership),
                    revoked_grant_count=len(grant_rows),
                    expired_role_count=len(role_rows),
                    revoked_session_count=len(session_rows),
                    audit_event_id=audit.event_id,
                    outbox_event_id=outbox_event_id,
                )
                session.flush()
            return evidence
        except (
            IdentityLifecycleConflict,
            IdentityLifecycleDenied,
            IdentityLifecycleNotFound,
        ):
            raise
        except (
            AuditScopeUnavailable,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise IdentityLifecycleUnavailable("Identity lifecycle is unavailable") from exc

    def request_support_access(
        self,
        tenant_id: UUID,
        *,
        request: SupportAccessCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> SupportAccessEvidence:
        try:
            return self._request_support_access(
                tenant_id,
                request=request,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        except (
            IdentityLifecycleConflict,
            IdentityLifecycleDenied,
            IdentityLifecycleNotFound,
        ):
            raise
        except IntegrityError as exc:
            if _is_integrity_conflict(exc, "uq_support_access_requests_active_target"):
                raise IdentityLifecycleConflict("Active support access already exists") from exc
            raise IdentityLifecycleUnavailable("Identity lifecycle is unavailable") from exc
        except (
            AuditScopeUnavailable,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise IdentityLifecycleUnavailable("Identity lifecycle is unavailable") from exc

    def _request_support_access(
        self,
        tenant_id: UUID,
        *,
        request: SupportAccessCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> SupportAccessEvidence:
        digest = canonical_hash(
            {
                "tenant_id": str(tenant_id),
                "request": request.model_dump(mode="json"),
                "principal_id": str(principal_id),
                "authorization_grant_id": str(authorization_grant_id),
                "approval_receipt_id": approval_receipt_id,
                "authorization_purpose": authorization_purpose,
            }
        )
        request_id = uuid4()
        with self.database.tenant_transaction(tenant_id) as session:
            lock_idempotency_key(
                session,
                tenant_id=tenant_id,
                operation=SUPPORT_REQUEST_OPERATION,
                idempotency_key=idempotency_key,
            )
            replay = _replay(
                session,
                tenant_id=tenant_id,
                operation=SUPPORT_REQUEST_OPERATION,
                idempotency_key=idempotency_key,
                request_digest=digest,
                response_model=SupportAccessEvidence,
            )
            if replay is not None:
                return replay
            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            operation_at = audit_lock.acquired_at
            _require_active_scope(
                session,
                tenant_id=tenant_id,
                campaign_id=request.campaign_id,
                workspace_id=request.workspace_id,
            )
            _require_application_principal(session, principal_id)
            _require_application_principal(session, request.target_principal_id)
            expires_at = operation_at + timedelta(minutes=request.expires_in_minutes)
            campaign_scope_key = _scope_key(request.campaign_id, empty="TENANT")
            workspace_scope_key = _scope_key(request.workspace_id, empty="NONE")
            stale_requests = list(
                session.scalars(
                    select(SupportAccessRequest)
                    .where(
                        SupportAccessRequest.tenant_id == tenant_id,
                        SupportAccessRequest.target_principal_id == request.target_principal_id,
                        SupportAccessRequest.campaign_scope_key == campaign_scope_key,
                        SupportAccessRequest.workspace_scope_key == workspace_scope_key,
                        SupportAccessRequest.action == request.action,
                        SupportAccessRequest.resource_type == request.resource_type,
                        SupportAccessRequest.resource_id == request.resource_id,
                        SupportAccessRequest.status.in_(("PENDING", "APPROVED")),
                        SupportAccessRequest.expires_at <= operation_at,
                    )
                    .with_for_update()
                )
            )
            for stale_request in stale_requests:
                _expire_support_row(
                    session,
                    audit_lock=audit_lock,
                    support_request=stale_request,
                    principal_id=principal_id,
                    correlation_id=correlation_id,
                    observation="OBSERVED_DURING_SUPPORT_REQUEST",
                )
            duplicate = session.scalar(
                select(SupportAccessRequest.id).where(
                    SupportAccessRequest.tenant_id == tenant_id,
                    SupportAccessRequest.target_principal_id == request.target_principal_id,
                    SupportAccessRequest.campaign_scope_key == campaign_scope_key,
                    SupportAccessRequest.workspace_scope_key == workspace_scope_key,
                    SupportAccessRequest.action == request.action,
                    SupportAccessRequest.resource_type == request.resource_type,
                    SupportAccessRequest.resource_id == request.resource_id,
                    SupportAccessRequest.status.in_(("PENDING", "APPROVED")),
                    SupportAccessRequest.expires_at > operation_at,
                )
            )
            if duplicate is not None:
                raise IdentityLifecycleConflict("Active support access already exists")
            row = SupportAccessRequest(
                id=request_id,
                tenant_id=tenant_id,
                requested_by_principal_id=principal_id,
                target_principal_id=request.target_principal_id,
                campaign_id=request.campaign_id,
                workspace_id=request.workspace_id,
                campaign_scope_key=campaign_scope_key,
                workspace_scope_key=workspace_scope_key,
                action=request.action,
                resource_type=request.resource_type,
                resource_id=request.resource_id,
                purpose=request.purpose,
                reason=request.reason,
                status="PENDING",
                requested_at=operation_at,
                expires_at=expires_at,
                created_membership=False,
                version=1,
                created_at=operation_at,
                updated_at=operation_at,
            )
            session.add(row)
            session.flush()
            audit = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=request.campaign_id,
                workspace_id=request.workspace_id,
                principal_id=principal_id,
                event_type="identity.support_access.requested",
                resource_type="support_access_request",
                resource_id=str(row.id),
                payload={
                    "target_principal_id": str(request.target_principal_id),
                    "action": request.action,
                    "resource_type": request.resource_type,
                    "resource_id": request.resource_id,
                    "purpose": request.purpose,
                    "reason": request.reason,
                    "expires_at": expires_at.isoformat(),
                    "authorization_grant_id": str(authorization_grant_id),
                    "approval_receipt_id": approval_receipt_id,
                    "authorization_purpose": authorization_purpose,
                    "correlation_id": correlation_id,
                    "external_effects": "NONE",
                },
            )
            evidence = SupportAccessEvidence(
                request=_support_projection(row),
                audit_event_id=audit.event_id,
            )
            _store_replay(
                session,
                tenant_id=tenant_id,
                principal_id=principal_id,
                operation=SUPPORT_REQUEST_OPERATION,
                idempotency_key=idempotency_key,
                request_digest=digest,
                response=evidence,
                created_at=operation_at,
            )
            session.flush()
        return evidence

    def approve_support_access(
        self,
        tenant_id: UUID,
        request_id: UUID,
        *,
        request: SupportAccessApprove,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> SupportAccessEvidence:
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                operation_at = audit_lock.acquired_at
                _require_application_principal(session, principal_id)
                row = session.scalar(
                    select(SupportAccessRequest)
                    .where(
                        SupportAccessRequest.tenant_id == tenant_id,
                        SupportAccessRequest.id == request_id,
                    )
                    .with_for_update()
                )
                if row is None:
                    raise IdentityLifecycleNotFound("Support access request was not found")
                if row.version != request.expected_version:
                    raise IdentityLifecycleVersionConflict(
                        "Support access request version is stale"
                    )
                if row.status != "PENDING":
                    raise IdentityLifecycleConflict("Support access request is not pending")
                if _as_utc(row.expires_at) <= operation_at:
                    raise _SupportAccessExpired(row.id)
                if principal_id in {
                    row.requested_by_principal_id,
                    row.target_principal_id,
                }:
                    raise IdentityLifecycleDenied("Support access requires separation of duty")
                _require_active_scope(
                    session,
                    tenant_id=tenant_id,
                    campaign_id=row.campaign_id,
                    workspace_id=row.workspace_id,
                )
                _require_application_principal(session, row.target_principal_id)

                membership = session.scalar(
                    select(Membership)
                    .where(
                        Membership.tenant_id == tenant_id,
                        Membership.principal_id == row.target_principal_id,
                        _campaign_predicate(Membership.campaign_id, row.campaign_id),
                    )
                    .with_for_update()
                )
                support_owned_membership = False
                if membership is not None:
                    previous_support_request = session.scalar(
                        select(SupportAccessRequest.id)
                        .where(
                            SupportAccessRequest.tenant_id == tenant_id,
                            SupportAccessRequest.membership_id == membership.id,
                            SupportAccessRequest.created_membership.is_(True),
                            SupportAccessRequest.id != row.id,
                            or_(
                                SupportAccessRequest.status.in_(("REVOKED", "EXPIRED")),
                                and_(
                                    SupportAccessRequest.status == "APPROVED",
                                    SupportAccessRequest.expires_at <= operation_at,
                                ),
                            ),
                        )
                        .limit(1)
                    )
                    support_owned_membership = previous_support_request is not None

                created_membership = membership is None or support_owned_membership
                if membership is None:
                    membership = Membership(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        principal_id=row.target_principal_id,
                        campaign_id=row.campaign_id,
                        status="ACTIVE",
                        valid_from=operation_at,
                        expires_at=row.expires_at,
                        revoked_at=None,
                        version=1,
                        created_at=operation_at,
                        updated_at=operation_at,
                    )
                    session.add(membership)
                    session.flush()
                elif membership.status == "REVOKED" and support_owned_membership:
                    membership.status = "ACTIVE"
                    membership.valid_from = operation_at
                    membership.expires_at = row.expires_at
                    membership.revoked_at = None
                    membership.version += 1
                    membership.updated_at = operation_at
                elif membership.status != "ACTIVE":
                    raise IdentityLifecycleConflict("Support target membership is not active")
                elif membership.expires_at is not None and _as_utc(membership.expires_at) < _as_utc(
                    row.expires_at
                ):
                    if not support_owned_membership:
                        raise IdentityLifecycleConflict(
                            "Support access would outlive the target membership"
                        )
                    membership.expires_at = row.expires_at
                    membership.version += 1
                    membership.updated_at = operation_at

                active_role = session.scalar(
                    select(RoleAssignment.id).where(
                        RoleAssignment.tenant_id == tenant_id,
                        RoleAssignment.membership_id == membership.id,
                        RoleAssignment.role.like(f"{SUPPORT_ROLE_PREFIX}%"),
                        or_(
                            RoleAssignment.expires_at.is_(None),
                            RoleAssignment.expires_at > operation_at,
                        ),
                    )
                )
                if active_role is not None:
                    raise IdentityLifecycleConflict("Support role is already active")
                existing_grant = session.scalar(
                    select(PermissionGrant)
                    .where(
                        PermissionGrant.tenant_id == tenant_id,
                        PermissionGrant.membership_id == membership.id,
                        PermissionGrant.action == row.action,
                        PermissionGrant.resource_type == row.resource_type,
                        PermissionGrant.resource_id == row.resource_id,
                    )
                    .with_for_update()
                )
                reused_permission_grant = False
                if existing_grant is not None:
                    if (
                        existing_grant.campaign_id != row.campaign_id
                        or existing_grant.workspace_id != row.workspace_id
                        or existing_grant.purpose != row.purpose
                    ):
                        raise IdentityLifecycleConflict(
                            "Existing permission scope conflicts with support access"
                        )
                    if existing_grant.status == "ACTIVE" and (
                        existing_grant.expires_at is None
                        or _as_utc(existing_grant.expires_at) > operation_at
                    ):
                        raise IdentityLifecycleConflict(
                            "Exact support permission is already active"
                        )
                    prior_support_request = session.scalar(
                        select(SupportAccessRequest.id)
                        .where(
                            SupportAccessRequest.tenant_id == tenant_id,
                            SupportAccessRequest.permission_grant_id == existing_grant.id,
                            SupportAccessRequest.id != row.id,
                            or_(
                                SupportAccessRequest.status.in_(("REVOKED", "EXPIRED")),
                                and_(
                                    SupportAccessRequest.status == "APPROVED",
                                    SupportAccessRequest.expires_at <= operation_at,
                                ),
                            ),
                        )
                        .limit(1)
                    )
                    if prior_support_request is None:
                        raise IdentityLifecycleConflict(
                            "Existing permission is not owned by support lifecycle"
                        )
                    existing_grant.status = "ACTIVE"
                    existing_grant.valid_from = operation_at
                    existing_grant.expires_at = row.expires_at
                    existing_grant.granted_by_principal_id = principal_id
                    existing_grant.approval_receipt_id = approval_receipt_id
                    existing_grant.updated_at = operation_at
                    permission_grant = existing_grant
                    reused_permission_grant = True
                else:
                    permission_grant = PermissionGrant(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        membership_id=membership.id,
                        campaign_id=row.campaign_id,
                        workspace_id=row.workspace_id,
                        action=row.action,
                        resource_type=row.resource_type,
                        resource_id=row.resource_id,
                        purpose=row.purpose,
                        status="ACTIVE",
                        valid_from=operation_at,
                        expires_at=row.expires_at,
                        granted_by_principal_id=principal_id,
                        approval_receipt_id=approval_receipt_id,
                        created_at=operation_at,
                        updated_at=operation_at,
                    )
                    session.add(permission_grant)

                role_assignment = RoleAssignment(
                    id=uuid4(),
                    tenant_id=tenant_id,
                    membership_id=membership.id,
                    role=f"{SUPPORT_ROLE_PREFIX}{row.id}",
                    assigned_by_principal_id=principal_id,
                    expires_at=row.expires_at,
                    created_at=operation_at,
                    updated_at=operation_at,
                )
                session.add(role_assignment)
                session.flush()

                row.status = "APPROVED"
                row.decided_at = operation_at
                row.decided_by_principal_id = principal_id
                row.approval_receipt_id = approval_receipt_id
                row.membership_id = membership.id
                row.role_assignment_id = role_assignment.id
                row.permission_grant_id = permission_grant.id
                row.created_membership = created_membership
                row.version += 1
                row.updated_at = operation_at
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=row.campaign_id,
                    workspace_id=row.workspace_id,
                    principal_id=principal_id,
                    event_type="identity.support_access.approved",
                    resource_type="support_access_request",
                    resource_id=str(row.id),
                    payload={
                        "target_principal_id": str(row.target_principal_id),
                        "membership_id": str(membership.id),
                        "role_assignment_id": str(role_assignment.id),
                        "permission_grant_id": str(permission_grant.id),
                        "reused_permission_grant": reused_permission_grant,
                        "created_membership": created_membership,
                        "expires_at": _as_utc(row.expires_at).isoformat(),
                        "authorization_grant_id": str(authorization_grant_id),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "external_effects": "NONE",
                    },
                )
                evidence = SupportAccessEvidence(
                    request=_support_projection(row),
                    audit_event_id=audit.event_id,
                )
                session.flush()
            return evidence
        except _SupportAccessExpired as exc:
            try:
                self._persist_support_expiry(
                    tenant_id,
                    exc.request_id,
                    principal_id=principal_id,
                    correlation_id=correlation_id,
                    observation="OBSERVED_DURING_SUPPORT_APPROVAL",
                )
            except (
                AuditScopeUnavailable,
                IdentityLifecycleNotFound,
                SQLAlchemyError,
                ValidationError,
                ValueError,
            ) as persist_exc:
                raise IdentityLifecycleUnavailable(
                    "Identity lifecycle is unavailable"
                ) from persist_exc
            raise IdentityLifecycleConflict("Support access request has expired") from exc
        except (
            IdentityLifecycleConflict,
            IdentityLifecycleDenied,
            IdentityLifecycleNotFound,
        ):
            raise
        except (
            AuditScopeUnavailable,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise IdentityLifecycleUnavailable("Identity lifecycle is unavailable") from exc

    def revoke_support_access(
        self,
        tenant_id: UUID,
        request_id: UUID,
        *,
        request: SupportAccessRevoke,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
    ) -> SupportAccessEvidence:
        try:
            with self.database.tenant_transaction(tenant_id) as session:
                audit_lock = lock_tenant_audit_stream(session, tenant_id)
                operation_at = audit_lock.acquired_at
                _require_application_principal(session, principal_id)
                row = session.scalar(
                    select(SupportAccessRequest)
                    .where(
                        SupportAccessRequest.tenant_id == tenant_id,
                        SupportAccessRequest.id == request_id,
                    )
                    .with_for_update()
                )
                if row is None:
                    raise IdentityLifecycleNotFound("Support access request was not found")
                if row.version != request.expected_version:
                    raise IdentityLifecycleVersionConflict(
                        "Support access request version is stale"
                    )
                if row.status != "APPROVED":
                    raise IdentityLifecycleConflict("Support access request is not approved")
                if (
                    row.membership_id is None
                    or row.role_assignment_id is None
                    or row.permission_grant_id is None
                ):
                    raise IdentityLifecycleUnavailable("Support access evidence is incomplete")

                membership = session.scalar(
                    select(Membership)
                    .where(
                        Membership.tenant_id == tenant_id,
                        Membership.id == row.membership_id,
                    )
                    .with_for_update()
                )
                role = session.scalar(
                    select(RoleAssignment)
                    .where(
                        RoleAssignment.tenant_id == tenant_id,
                        RoleAssignment.id == row.role_assignment_id,
                    )
                    .with_for_update()
                )
                grant = session.scalar(
                    select(PermissionGrant)
                    .where(
                        PermissionGrant.tenant_id == tenant_id,
                        PermissionGrant.id == row.permission_grant_id,
                    )
                    .with_for_update()
                )
                if membership is None or role is None or grant is None:
                    raise IdentityLifecycleUnavailable("Support access evidence is incomplete")
                if grant.status == "ACTIVE":
                    grant.status = "REVOKED"
                    grant.updated_at = operation_at
                if role.expires_at is None or _as_utc(role.expires_at) > operation_at:
                    role.expires_at = operation_at
                    role.updated_at = operation_at
                if row.created_membership:
                    membership.status = "REVOKED"
                    membership.revoked_at = operation_at
                    membership.version += 1
                    membership.updated_at = operation_at

                row.status = "REVOKED"
                row.revoked_at = operation_at
                row.revoked_by_principal_id = principal_id
                row.version += 1
                row.updated_at = operation_at
                audit = append_audit_event(
                    session,
                    audit_lock=audit_lock,
                    campaign_id=row.campaign_id,
                    workspace_id=row.workspace_id,
                    principal_id=principal_id,
                    event_type="identity.support_access.revoked",
                    resource_type="support_access_request",
                    resource_id=str(row.id),
                    payload={
                        "target_principal_id": str(row.target_principal_id),
                        "reason": request.reason,
                        "membership_revoked": row.created_membership,
                        "authorization_grant_id": str(authorization_grant_id),
                        "approval_receipt_id": approval_receipt_id,
                        "authorization_purpose": authorization_purpose,
                        "correlation_id": correlation_id,
                        "external_effects": "NONE",
                    },
                )
                evidence = SupportAccessEvidence(
                    request=_support_projection(row),
                    audit_event_id=audit.event_id,
                )
                session.flush()
            return evidence
        except (
            IdentityLifecycleConflict,
            IdentityLifecycleDenied,
            IdentityLifecycleNotFound,
        ):
            raise
        except (
            AuditScopeUnavailable,
            IntegrityError,
            SQLAlchemyError,
            ValidationError,
            ValueError,
        ) as exc:
            raise IdentityLifecycleUnavailable("Identity lifecycle is unavailable") from exc
