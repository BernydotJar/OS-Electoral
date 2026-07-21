"""Tenant-scoped campaign creation with durable idempotency and evidence."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from campaignos.campaigns.read_model import CampaignProjection
from campaignos.data.audit import (
    AuditScopeUnavailable,
    append_audit_event,
    canonical_hash,
    lock_tenant_audit_stream,
)
from campaignos.data.database import Database
from campaignos.data.idempotency import lock_idempotency_key
from campaignos.data.models import Campaign, IdempotencyRecord, OutboxEvent

CAMPAIGN_CREATE_OPERATION = "campaign.create"


class CampaignCreateConflict(RuntimeError):
    """The normalized tenant campaign slug is already reserved."""


class CampaignCreateIdempotencyConflict(RuntimeError):
    """An idempotency key was reused for different request or authority evidence."""


class CampaignCreateUnavailable(RuntimeError):
    """The campaign create boundary cannot currently complete."""


class CampaignCreate(BaseModel):
    """Human-supplied metadata for one server-owned draft campaign."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    slug: str = Field(
        min_length=1,
        max_length=100,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
    )
    name: str = Field(min_length=1, max_length=255)
    jurisdiction: str = Field(min_length=1, max_length=255)
    stage: str = Field(min_length=1, max_length=80)

    @field_validator("slug", mode="before")
    @classmethod
    def normalize_slug(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip().lower()
        return value

    @field_validator("name", "jurisdiction", "stage", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        if isinstance(value, str):
            return " ".join(value.split())
        return value


class CampaignCreateEvidence(BaseModel):
    """The draft campaign and atomic evidence identifiers committed with it."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    campaign: CampaignProjection
    audit_event_id: UUID
    outbox_event_id: UUID


class CampaignCreator(Protocol):
    """Create one authorized tenant campaign without implicit downstream effects."""

    def create(
        self,
        tenant_id: UUID,
        *,
        request: CampaignCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CampaignCreateEvidence:
        """Create or replay the exact committed draft campaign evidence."""


class UnavailableCampaignCreator:
    """Fail-closed creator used until persistence is configured."""

    def create(self, tenant_id: UUID, **kwargs: object) -> CampaignCreateEvidence:
        del tenant_id, kwargs
        raise CampaignCreateUnavailable("Campaign creator is unavailable")


def _request_digest(
    *,
    tenant_id: UUID,
    request: CampaignCreate,
    principal_id: UUID,
    authorization_grant_id: UUID,
    approval_receipt_id: str,
    authorization_purpose: str,
) -> str:
    return canonical_hash(
        {
            "tenant_id": str(tenant_id),
            "request": request.model_dump(),
            "principal_id": str(principal_id),
            "authorization_grant_id": str(authorization_grant_id),
            "approval_receipt_id": approval_receipt_id,
            "authorization_purpose": authorization_purpose,
        }
    )


@dataclass(frozen=True, slots=True)
class InMemoryCampaignCreateAudit:
    audit_event_id: UUID
    tenant_id: UUID
    campaign_id: UUID
    principal_id: UUID
    authorization_grant_id: UUID
    approval_receipt_id: str
    authorization_purpose: str
    correlation_id: str


@dataclass(frozen=True, slots=True)
class InMemoryCampaignCreateOutbox:
    outbox_event_id: UUID
    tenant_id: UUID
    campaign_id: UUID
    topic: str = "campaign.created"
    external_effects: str = "NONE"


@dataclass(slots=True)
class InMemoryCampaignCreator:
    """Deterministic local adapter preserving the durable creator contract."""

    campaigns: dict[tuple[UUID, str], CampaignProjection] = field(default_factory=dict)
    idempotency: dict[tuple[UUID, str], tuple[str, CampaignCreateEvidence]] = field(
        default_factory=dict
    )
    audit_events: list[InMemoryCampaignCreateAudit] = field(default_factory=list)
    outbox_events: list[InMemoryCampaignCreateOutbox] = field(default_factory=list)

    def create(
        self,
        tenant_id: UUID,
        *,
        request: CampaignCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CampaignCreateEvidence:
        digest = _request_digest(
            tenant_id=tenant_id,
            request=request,
            principal_id=principal_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id=approval_receipt_id,
            authorization_purpose=authorization_purpose,
        )
        key = (tenant_id, idempotency_key)
        existing = self.idempotency.get(key)
        if existing is not None:
            existing_digest, evidence = existing
            if existing_digest != digest:
                raise CampaignCreateIdempotencyConflict(
                    "Idempotency key conflicts with previous request"
                )
            return evidence
        campaign_key = (tenant_id, request.slug)
        if campaign_key in self.campaigns:
            raise CampaignCreateConflict("Campaign slug is already reserved")

        campaign_id, audit_event_id, outbox_event_id = uuid4(), uuid4(), uuid4()
        campaign = CampaignProjection(
            id=campaign_id,
            tenant_id=tenant_id,
            slug=request.slug,
            name=request.name,
            jurisdiction=request.jurisdiction,
            stage=request.stage,
            status="DRAFT",
            version=1,
        )
        evidence = CampaignCreateEvidence(
            campaign=campaign,
            audit_event_id=audit_event_id,
            outbox_event_id=outbox_event_id,
        )
        self.campaigns[campaign_key] = campaign
        self.idempotency[key] = (digest, evidence)
        self.audit_events.append(
            InMemoryCampaignCreateAudit(
                audit_event_id=audit_event_id,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
            )
        )
        self.outbox_events.append(
            InMemoryCampaignCreateOutbox(
                outbox_event_id=outbox_event_id,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
            )
        )
        return evidence


def _is_campaign_slug_conflict(exc: IntegrityError) -> bool:
    diagnostic = getattr(exc.orig, "diag", None)
    if getattr(diagnostic, "constraint_name", None) == "uq_campaigns_tenant_slug":
        return True
    message = str(exc.orig).lower()
    return (
        "uq_campaigns_tenant_slug" in message
        or "unique constraint failed: campaigns.tenant_id, campaigns.slug" in message
    )


@dataclass(slots=True)
class SqlAlchemyCampaignCreator:
    """Commit one draft campaign, audit, internal outbox, and replay receipt."""

    database: Database

    def create(
        self,
        tenant_id: UUID,
        *,
        request: CampaignCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CampaignCreateEvidence:
        try:
            return self._create(
                tenant_id,
                request=request,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                authorization_purpose=authorization_purpose,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        except (CampaignCreateConflict, CampaignCreateIdempotencyConflict):
            raise
        except IntegrityError as exc:
            if _is_campaign_slug_conflict(exc):
                raise CampaignCreateConflict("Campaign slug is already reserved") from exc
            raise CampaignCreateUnavailable("Campaign create is unavailable") from exc
        except (AuditScopeUnavailable, SQLAlchemyError, ValueError) as exc:
            raise CampaignCreateUnavailable("Campaign create is unavailable") from exc

    def _create(
        self,
        tenant_id: UUID,
        *,
        request: CampaignCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        authorization_purpose: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CampaignCreateEvidence:
        digest = _request_digest(
            tenant_id=tenant_id,
            request=request,
            principal_id=principal_id,
            authorization_grant_id=authorization_grant_id,
            approval_receipt_id=approval_receipt_id,
            authorization_purpose=authorization_purpose,
        )
        with self.database.tenant_transaction(tenant_id) as session:
            lock_idempotency_key(
                session,
                tenant_id=tenant_id,
                operation=CAMPAIGN_CREATE_OPERATION,
                idempotency_key=idempotency_key,
            )
            existing = session.scalar(
                select(IdempotencyRecord)
                .where(
                    IdempotencyRecord.tenant_id == tenant_id,
                    IdempotencyRecord.operation == CAMPAIGN_CREATE_OPERATION,
                    IdempotencyRecord.idempotency_key == idempotency_key,
                )
                .with_for_update()
            )
            if existing is not None:
                if existing.request_digest != digest:
                    raise CampaignCreateIdempotencyConflict(
                        "Idempotency key conflicts with previous request"
                    )
                return CampaignCreateEvidence.model_validate(existing.response_payload)

            audit_lock = lock_tenant_audit_stream(session, tenant_id)
            duplicate = session.scalar(
                select(Campaign.id).where(
                    Campaign.tenant_id == tenant_id,
                    Campaign.slug == request.slug,
                )
            )
            if duplicate is not None:
                raise CampaignCreateConflict("Campaign slug is already reserved")

            operation_at = audit_lock.acquired_at
            campaign_id, outbox_event_id = uuid4(), uuid4()
            campaign = Campaign(
                id=campaign_id,
                tenant_id=tenant_id,
                slug=request.slug,
                name=request.name,
                jurisdiction=request.jurisdiction,
                stage=request.stage,
                status="DRAFT",
                version=1,
                created_at=operation_at,
                updated_at=operation_at,
            )
            session.add(campaign)
            session.flush()
            audit_append = append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=campaign_id,
                workspace_id=None,
                principal_id=principal_id,
                event_type="campaign.created",
                resource_type="campaign",
                resource_id=str(campaign_id),
                payload={
                    "campaign": {
                        "slug": request.slug,
                        "name": request.name,
                        "jurisdiction": request.jurisdiction,
                        "stage": request.stage,
                        "status": "DRAFT",
                        "version": 1,
                    },
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
                    campaign_id=campaign_id,
                    topic="campaign.created",
                    payload={
                        "audit_event_id": str(audit_append.event_id),
                        "tenant_id": str(tenant_id),
                        "campaign_id": str(campaign_id),
                        "status": "DRAFT",
                        "version": 1,
                        "external_effects": "NONE",
                    },
                    status="PENDING",
                    attempts=0,
                    available_at=operation_at,
                    created_at=operation_at,
                )
            )
            evidence = CampaignCreateEvidence(
                campaign=CampaignProjection(
                    id=campaign_id,
                    tenant_id=tenant_id,
                    slug=request.slug,
                    name=request.name,
                    jurisdiction=request.jurisdiction,
                    stage=request.stage,
                    status="DRAFT",
                    version=1,
                ),
                audit_event_id=audit_append.event_id,
                outbox_event_id=outbox_event_id,
            )
            session.add(
                IdempotencyRecord(
                    tenant_id=tenant_id,
                    principal_id=principal_id,
                    operation=CAMPAIGN_CREATE_OPERATION,
                    idempotency_key=idempotency_key,
                    request_digest=digest,
                    response_payload=evidence.model_dump(mode="json"),
                    created_at=operation_at,
                )
            )
            session.flush()
        return evidence
