"""Tenant-scoped workspace creation with durable idempotency and evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from campaignos.data.database import Database
from campaignos.data.models import AuditEvent, Campaign, IdempotencyRecord, OutboxEvent, Workspace


class WorkspaceIdempotencyConflict(RuntimeError):
    """An idempotency key was reused for a different workspace request."""


class WorkspaceMutationNotFound(LookupError):
    """The parent campaign is unavailable in the selected tenant."""


class WorkspaceWriteUnavailable(RuntimeError):
    """The workspace write boundary cannot currently complete."""


class WorkspaceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slug: str = Field(min_length=1, max_length=100, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
    name: str = Field(min_length=1, max_length=255)


class WorkspaceProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    slug: str
    name: str
    status: str
    version: int


class WorkspaceWriteEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace: WorkspaceProjection
    audit_event_id: UUID
    outbox_event_id: UUID


class WorkspaceWriter(Protocol):
    def create(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: WorkspaceCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> WorkspaceWriteEvidence: ...


class UnavailableWorkspaceWriter:
    def create(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: object
    ) -> WorkspaceWriteEvidence:
        del tenant_id, campaign_id, kwargs
        raise WorkspaceWriteUnavailable("Workspace writer is unavailable")


def _canonical_hash(value: object) -> str:
    encoded = json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str
    ).encode()
    return hashlib.sha256(encoded).hexdigest()


def _serialize_key(session: Session, tenant_id: UUID, operation: str, key: str) -> None:
    bind = session.get_bind()
    if bind.dialect.name != "postgresql":
        return
    digest = hashlib.sha256(f"{tenant_id}:{operation}:{key}".encode()).digest()
    lock_id = int.from_bytes(digest[:8], byteorder="big", signed=True)
    session.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": lock_id})


@dataclass(slots=True)
class SqlAlchemyWorkspaceWriter:
    database: Database

    def create(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: WorkspaceCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> WorkspaceWriteEvidence:
        try:
            return self._create(
                tenant_id,
                campaign_id,
                request=request,
                principal_id=principal_id,
                authorization_grant_id=authorization_grant_id,
                approval_receipt_id=approval_receipt_id,
                correlation_id=correlation_id,
                idempotency_key=idempotency_key,
            )
        except (WorkspaceIdempotencyConflict, WorkspaceMutationNotFound):
            raise
        except IntegrityError as exc:
            raise WorkspaceWriteUnavailable("Workspace slug is unavailable") from exc
        except SQLAlchemyError as exc:
            raise WorkspaceWriteUnavailable("Workspace write is unavailable") from exc

    def _create(
        self,
        tenant_id: UUID,
        campaign_id: UUID,
        *,
        request: WorkspaceCreate,
        principal_id: UUID,
        authorization_grant_id: UUID,
        approval_receipt_id: str,
        correlation_id: str,
        idempotency_key: str,
    ) -> WorkspaceWriteEvidence:
        operation = "workspace.create"
        digest = _canonical_hash(
            {
                "tenant_id": str(tenant_id),
                "campaign_id": str(campaign_id),
                "request": request.model_dump(),
                "principal_id": str(principal_id),
                "authorization_grant_id": str(authorization_grant_id),
                "approval_receipt_id": approval_receipt_id,
            }
        )
        occurred_at = datetime.now(UTC)
        workspace_id, audit_id, outbox_id = uuid4(), uuid4(), uuid4()
        with self.database.tenant_transaction(tenant_id) as session:
            _serialize_key(session, tenant_id, operation, idempotency_key)
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
                if existing.request_digest != digest:
                    raise WorkspaceIdempotencyConflict(
                        "Idempotency key conflicts with previous request"
                    )
                return WorkspaceWriteEvidence.model_validate(existing.response_payload)

            campaign_exists = session.scalar(
                select(Campaign.id).where(
                    Campaign.id == campaign_id,
                    Campaign.tenant_id == tenant_id,
                    Campaign.status.in_(("DRAFT", "ACTIVE")),
                )
            )
            if campaign_exists is None:
                raise WorkspaceMutationNotFound("Campaign was not found")

            workspace = Workspace(
                id=workspace_id,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                slug=request.slug,
                name=request.name,
                status="ACTIVE",
                version=1,
                created_at=occurred_at,
                updated_at=occurred_at,
            )
            session.add(workspace)
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
                "workspace": {"slug": request.slug, "name": request.name, "version": 1},
                "authorization_grant_id": str(authorization_grant_id),
                "approval_receipt_id": approval_receipt_id,
                "correlation_id": correlation_id,
            }
            event_hash = _canonical_hash(
                {
                    "id": str(audit_id),
                    "tenant_id": str(tenant_id),
                    "campaign_id": str(campaign_id),
                    "workspace_id": str(workspace_id),
                    "principal_id": str(principal_id),
                    "event_type": "workspace.created",
                    "payload": payload,
                    "occurred_at": occurred_at.isoformat(),
                    "previous_hash": previous_hash,
                }
            )
            session.add(
                AuditEvent(
                    id=audit_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    workspace_id=workspace_id,
                    principal_id=principal_id,
                    event_type="workspace.created",
                    resource_type="workspace",
                    resource_id=str(workspace_id),
                    payload=payload,
                    occurred_at=occurred_at,
                    previous_hash=previous_hash,
                    event_hash=event_hash,
                )
            )
            session.add(
                OutboxEvent(
                    id=outbox_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    topic="workspace.created",
                    payload={
                        "audit_event_id": str(audit_id),
                        "tenant_id": str(tenant_id),
                        "campaign_id": str(campaign_id),
                        "workspace_id": str(workspace_id),
                        "version": 1,
                    },
                    status="PENDING",
                    attempts=0,
                    available_at=occurred_at,
                    created_at=occurred_at,
                )
            )
            evidence = WorkspaceWriteEvidence(
                workspace=WorkspaceProjection(
                    id=workspace_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    slug=request.slug,
                    name=request.name,
                    status="ACTIVE",
                    version=1,
                ),
                audit_event_id=audit_id,
                outbox_event_id=outbox_id,
            )
            session.add(
                IdempotencyRecord(
                    tenant_id=tenant_id,
                    principal_id=principal_id,
                    operation=operation,
                    idempotency_key=idempotency_key,
                    request_digest=digest,
                    response_payload=evidence.model_dump(mode="json"),
                    created_at=occurred_at,
                )
            )
            session.flush()
        return evidence
