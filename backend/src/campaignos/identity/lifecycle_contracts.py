"""Provider-neutral identity lifecycle contracts with no external execution."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Literal, Protocol, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

InvitationProviderName = Literal["LOCAL_NO_DELIVERY", "AWS_COGNITO_PLAN_ONLY"]
InvitationDeliveryState = Literal["NOT_SENT"]
InvitationStatus = Literal["PENDING", "ACCEPTED", "REVOKED", "EXPIRED"]
SessionStatus = Literal["ACTIVE", "REVOKED", "EXPIRED"]
SupportAccessStatus = Literal["PENDING", "APPROVED", "REJECTED", "REVOKED", "EXPIRED"]

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+$")
_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]*$")


def normalize_email(value: str) -> str:
    """Normalize an identity target without pretending to validate mailbox ownership."""
    normalized = value.strip().lower()
    if len(normalized) > 320 or not _EMAIL_PATTERN.fullmatch(normalized):
        raise ValueError("email must be a bounded address-like identifier")
    return normalized


def normalize_text(value: str) -> str:
    return " ".join(value.split())


class InvitationCreate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    email: str = Field(min_length=3, max_length=320)
    campaign_id: UUID | None = None
    expires_in_hours: int = Field(default=72, ge=1, le=168)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_target_email(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_email(value)
        return value


class InvitationDeliveryPlan(BaseModel):
    """A request plan only; consuming it is a separate human-gated integration."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    provider: InvitationProviderName
    operation: str = Field(min_length=1, max_length=160)
    provider_reference: str = Field(min_length=1, max_length=255)
    request_payload: dict[str, Any]
    delivery_state: InvitationDeliveryState = "NOT_SENT"
    external_effects: Literal["NONE"] = "NONE"

    @field_validator("operation", "provider_reference")
    @classmethod
    def validate_identifiers(cls, value: str) -> str:
        if not _IDENTIFIER_PATTERN.fullmatch(value):
            raise ValueError("provider plan identifiers contain unsupported characters")
        return value


class InvitationPlanner(Protocol):
    def plan(
        self,
        *,
        invitation_id: UUID,
        tenant_id: UUID,
        campaign_id: UUID | None,
        email: str,
        expires_at: datetime,
    ) -> InvitationDeliveryPlan:
        """Return a deterministic non-executing provider request plan."""


class LocalInvitationPlanner:
    def plan(
        self,
        *,
        invitation_id: UUID,
        tenant_id: UUID,
        campaign_id: UUID | None,
        email: str,
        expires_at: datetime,
    ) -> InvitationDeliveryPlan:
        return InvitationDeliveryPlan(
            provider="LOCAL_NO_DELIVERY",
            operation="local:RecordInvitationIntent",
            provider_reference=f"local:{invitation_id}",
            request_payload={
                "invitation_id": str(invitation_id),
                "tenant_id": str(tenant_id),
                "campaign_id": str(campaign_id) if campaign_id is not None else None,
                "email": normalize_email(email),
                "expires_at": expires_at.isoformat(),
                "delivery": "DISABLED",
            },
        )


class CognitoInvitationPlanner:
    """Plan AWS Cognito AdminCreateUser without importing or invoking an AWS SDK."""

    def __init__(self, user_pool_id: str) -> None:
        value = user_pool_id.strip()
        if not value or len(value) > 128 or not _IDENTIFIER_PATTERN.fullmatch(value):
            raise ValueError("Cognito user pool identifier is invalid")
        self.user_pool_id = value

    def plan(
        self,
        *,
        invitation_id: UUID,
        tenant_id: UUID,
        campaign_id: UUID | None,
        email: str,
        expires_at: datetime,
    ) -> InvitationDeliveryPlan:
        normalized_email = normalize_email(email)
        return InvitationDeliveryPlan(
            provider="AWS_COGNITO_PLAN_ONLY",
            operation="cognito-idp:AdminCreateUser",
            provider_reference=f"cognito:{invitation_id}",
            request_payload={
                "UserPoolId": self.user_pool_id,
                "Username": normalized_email,
                "UserAttributes": [
                    {"Name": "email", "Value": normalized_email},
                    {"Name": "email_verified", "Value": "false"},
                ],
                "MessageAction": "SUPPRESS",
                "ClientMetadata": {
                    "campaignos_invitation_id": str(invitation_id),
                    "campaignos_tenant_id": str(tenant_id),
                    "campaignos_campaign_id": (
                        str(campaign_id) if campaign_id is not None else "TENANT"
                    ),
                    "campaignos_expires_at": expires_at.isoformat(),
                },
            },
        )


class InvitationProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID | None
    email: str
    status: InvitationStatus
    provider: InvitationProviderName
    provider_reference: str
    expires_at: datetime
    accepted_at: datetime | None
    membership_id: UUID | None
    revoked_at: datetime | None
    version: int = Field(ge=1)


class MembershipProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    principal_id: UUID
    campaign_id: UUID | None
    status: Literal["INVITED", "ACTIVE", "SUSPENDED", "REVOKED"]
    valid_from: datetime
    expires_at: datetime | None
    revoked_at: datetime | None
    version: int = Field(ge=1)


class InvitationCreateEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    invitation: InvitationProjection
    delivery_plan: InvitationDeliveryPlan
    audit_event_id: UUID
    outbox_event_id: UUID


class InvitationAcceptanceEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    invitation: InvitationProjection
    membership: MembershipProjection
    principal_id: UUID
    audit_event_id: UUID


class InvitationMutationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    invitation: InvitationProjection
    audit_event_id: UUID


class SessionProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    principal_id: UUID
    status: SessionStatus
    authenticated_at: datetime
    last_seen_at: datetime
    expires_at: datetime
    revoked_at: datetime | None
    revocation_reason: str | None
    version: int = Field(ge=1)


class SessionEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    session: SessionProjection
    audit_event_id: UUID
    created: bool
    provider_revocation_state: Literal["NOT_EXECUTED"] = "NOT_EXECUTED"


class SessionRevoke(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    reason: str = Field(min_length=3, max_length=255)
    expected_version: int = Field(ge=1)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_text(value)
        return value


class MembershipRevoke(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    reason: str = Field(min_length=3, max_length=255)
    expected_version: int = Field(ge=1)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_text(value)
        return value


class MembershipRevocationEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    membership: MembershipProjection
    revoked_grant_count: int = Field(ge=0)
    expired_role_count: int = Field(ge=0)
    revoked_session_count: int = Field(ge=0)
    audit_event_id: UUID
    outbox_event_id: UUID
    provider_revocation_state: Literal["NOT_EXECUTED"] = "NOT_EXECUTED"


class SupportAccessCreate(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    target_principal_id: UUID
    campaign_id: UUID | None = None
    workspace_id: UUID | None = None
    action: str = Field(min_length=1, max_length=100)
    resource_type: str = Field(min_length=1, max_length=100)
    resource_id: str = Field(min_length=1, max_length=255)
    purpose: str = Field(min_length=3, max_length=255)
    reason: str = Field(min_length=8, max_length=2000)
    expires_in_minutes: int = Field(default=60, ge=15, le=480)

    @field_validator("action", "resource_type", "resource_id", "purpose", "reason", mode="before")
    @classmethod
    def normalize_bounded_text(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_text(value)
        return value

    @model_validator(mode="after")
    def validate_scope(self) -> Self:
        if self.workspace_id is not None and self.campaign_id is None:
            raise ValueError("workspace-scoped support access requires campaign scope")
        return self


class SupportAccessProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    requested_by_principal_id: UUID
    target_principal_id: UUID
    campaign_id: UUID | None
    workspace_id: UUID | None
    action: str
    resource_type: str
    resource_id: str
    purpose: str
    reason: str
    status: SupportAccessStatus
    requested_at: datetime
    expires_at: datetime
    decided_at: datetime | None
    decided_by_principal_id: UUID | None
    approval_receipt_id: str | None
    membership_id: UUID | None
    role_assignment_id: UUID | None
    permission_grant_id: UUID | None
    created_membership: bool
    revoked_at: datetime | None
    version: int = Field(ge=1)


class SupportAccessEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    request: SupportAccessProjection
    audit_event_id: UUID


class SupportAccessApprove(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    expected_version: int = Field(ge=1)


class SupportAccessRevoke(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    reason: str = Field(min_length=3, max_length=255)
    expected_version: int = Field(ge=1)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_text(value)
        return value
