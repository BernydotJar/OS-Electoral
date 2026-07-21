"""Tenant-scoped campaign mutation with optimistic concurrency and transactional evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from campaignos.campaigns.read_model import CampaignProjection
from campaignos.data.database import Database
from campaignos.data.models import AuditEvent, Campaign, IdempotencyRecord, OutboxEvent


class CampaignWriteConflict(RuntimeError):
    """The supplied aggregate version is stale."""


class CampaignIdempotencyConflict(RuntimeError):
    """An idempotency key was reused for a different request."""


class CampaignWriteUnavailable(RuntimeError):
    """The campaign write boundary cannot currently complete."""


class CampaignMutationNotFound(LookupError):
    """The requested mutable campaign is unavailable in the selected tenant."""


class CampaignUpdate(BaseModel):
    """Bounded campaign fields that may be changed through the first write API."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=1, max_length=255)
    jurisdiction: str | None = Field(default=None, min_length=1, max_length=255)
    stage: str | None = Field(default=None, min_length=1, max_length=80)
    status: str | None = Field(default=None, pattern="^(DRAFT|ACTIVE)$")

    @model_validator(mode="after")
    def require_change(self) -> CampaignUpdate:
        if not self.model_fields_set:
            raise ValueError("at least one campaign field is required")
        return self


class CampaignWriteEvidence(BaseModel):
    """Identifiers proving that mutation, audit, and outbox were committed together."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    campaign: CampaignProjection
    audit_event_id: UUID
    outbox_event_id: UUID


class CampaignWriter(Protocol):
    """Persist one authorized campaign mutation atomically."""

    def update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: CampaignUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CampaignWriteEvidence:
        """Update or fail closed without partial effects."""


class UnavailableCampaignWriter:
    """Fail-closed writer used before persistence is configured."""

    def update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: CampaignUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CampaignWriteEvidence:
        del (
            tenant_id,
            campaign_id,
            expected_version,
            changes,
            principal_id,
            authorization_grant_id,
            approval_receipt_id,
            correlation_id,
            idempotency_key,
        )
        raise CampaignWriteUnavailable("Campaign writer is unavailable")


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _serialize_idempotency_key(
    session: Session, tenant_id: UUID, operation: str, idempotency_key: str
) -> None:
    """Serialize equal PostgreSQL keys inside the current transaction."""
    bind = session.get_bind()
    if bind.dialect.name != "postgresql":
        return
    digest = hashlib.sha256(f"{tenant_id}:{operation}:{idempotency_key}".encode()).digest()
    lock_id = int.from_bytes(digest[:8], byteorder="big", signed=True)
    session.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": lock_id})


@dataclass(slots=True)
class SqlAlchemyCampaignWriter:
    """Perform a versioned campaign update plus audit/outbox append in one transaction."""

    database: Database

    def update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: CampaignUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CampaignWriteEvidence:
        try:
            return self._update(
                tenant_id,
                campaign_id,
                expected_version=expected_version,
                changes=changes,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        except (CampaignIdempotencyConflict, CampaignMutationNotFound, CampaignWriteConflict):
            raise
        except SQLAlchemyError as exc:
            raise CampaignWriteUnavailable("Campaign write is unavailable") from exc

    def _update(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        expected_version: int,
        changes: CampaignUpdate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> CampaignWriteEvidence:
        request_digest = _canonical_hash(
            {
                "tenant_id": str(tenant_id),
                "campaign_id": str(campaign_id),
                "expected_version": expected_version,
                "changes": changes.model_dump(exclude_unset=True),
                "principal_id": str(principal_id),
                "authorization_grant_id": str(authorization_grant_id),
                "approval_receipt_id": approval_receipt_id,
            }
        )
        operation = "campaign.update"
        occurred_at = datetime.now(UTC)
        audit_event_id = uuid4()
        outbox_event_id = uuid4()
        with self.database.tenant_transaction(tenant_id) as session:
            _serialize_idempotency_key(session, tenant_id, operation, idempotency_key)
            existing = session.scalar(
                select(IdempotencyRecord)
                .where(
                    IdempotencyRecord.tenant_id == tenant_id,
                    IdempotencyRecord.operation == operation,
                    IdempotencyRecord.idempotency_key == idempotency_key,
                )
                .with_for_update()
            )
            if existing is not None:
                if existing.request_digest != request_digest:
                    raise CampaignIdempotencyConflict(
                        "Idempotency key was already used for a different request"
                    )
                return CampaignWriteEvidence.model_validate(existing.response_payload)

            campaign = session.scalar(
                select(Campaign)
                .where(
                    Campaign.id == campaign_id,
                    Campaign.tenant_id == tenant_id,
                    Campaign.status.in_(("DRAFT", "ACTIVE")),
                )
                .with_for_update()
            )
            if campaign is None:
                raise CampaignMutationNotFound("Campaign was not found")
            if campaign.version != expected_version:
                raise CampaignWriteConflict("Campaign version is stale")

            changed = changes.model_dump(exclude_unset=True)
            before = {field: getattr(campaign, field) for field in changed}
            for field, value in changed.items():
                setattr(campaign, field, value)
            campaign.version += 1
            campaign.updated_at = occurred_at

            previous_hash = (
                session.scalar(
                    select(AuditEvent.event_hash)
                    .where(AuditEvent.tenant_id == tenant_id)
                    .order_by(AuditEvent.occurred_at.desc(), AuditEvent.id.desc())
                    .limit(1)
                    .with_for_update()
                )
                or "GENESIS"
            )
            payload = {
                "before": before,
                "after": changed,
                "version": campaign.version,
                "authorization_grant_id": str(authorization_grant_id),
                "approval_receipt_id": approval_receipt_id,
                "correlation_id": correlation_id,
            }
            hash_input = {
                "id": str(audit_event_id),
                "tenant_id": str(tenant_id),
                "campaign_id": str(campaign_id),
                "principal_id": str(principal_id),
                "event_type": "campaign.updated",
                "resource_type": "campaign",
                "resource_id": str(campaign_id),
                "payload": payload,
                "occurred_at": occurred_at.isoformat(),
                "previous_hash": previous_hash,
            }
            event_hash = _canonical_hash(hash_input)
            session.add(
                AuditEvent(
                    id=audit_event_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    principal_id=principal_id,
                    event_type="campaign.updated",
                    resource_type="campaign",
                    resource_id=str(campaign_id),
                    payload=payload,
                    occurred_at=occurred_at,
                    previous_hash=previous_hash,
                    event_hash=event_hash,
                )
            )
            session.add(
                OutboxEvent(
                    id=outbox_event_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    topic="campaign.updated",
                    payload={
                        "audit_event_id": str(audit_event_id),
                        "campaign_id": str(campaign_id),
                        "tenant_id": str(tenant_id),
                        "version": campaign.version,
                    },
                    status="PENDING",
                    attempts=0,
                    available_at=occurred_at,
                    created_at=occurred_at,
                )
            )
            projection = CampaignProjection(
                id=campaign.id,
                tenant_id=campaign.tenant_id,
                slug=campaign.slug,
                name=campaign.name,
                jurisdiction=campaign.jurisdiction,
                stage=campaign.stage,
                status=campaign.status,
                version=campaign.version,
            )
            evidence = CampaignWriteEvidence(
                campaign=projection,
                audit_event_id=audit_event_id,
                outbox_event_id=outbox_event_id,
            )
            session.add(
                IdempotencyRecord(
                    tenant_id=tenant_id,
                    principal_id=principal_id,
                    operation=operation,
                    idempotency_key=idempotency_key,
                    request_digest=request_digest,
                    response_payload=evidence.model_dump(mode="json"),
                    created_at=occurred_at,
                )
            )
            session.flush()

        return evidence
