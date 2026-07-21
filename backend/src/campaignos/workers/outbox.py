"""Tenant-scoped transactional outbox worker with recoverable leases."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError

from campaignos.data.database import Database
from campaignos.data.models import AuditEvent, Campaign, OutboxEvent


class OutboxWorkerUnavailable(RuntimeError):
    """The worker persistence boundary cannot currently complete."""


class UnsupportedOutboxTopic(RuntimeError):
    """No internal handler is registered for the event topic."""


class InvalidOutboxEvent(RuntimeError):
    """The event payload is inconsistent with its tenant/campaign scope."""


@dataclass(frozen=True, slots=True)
class ClaimedOutboxEvent:
    id: UUID
    tenant_id: UUID
    campaign_id: UUID | None
    topic: str
    payload: dict[str, object]
    attempts: int
    lease_owner: str
    lease_expires_at: datetime


@dataclass(frozen=True, slots=True)
class OutboxRunResult:
    claimed: int
    delivered: int
    retried: int
    dead_lettered: int


class OutboxHandler(Protocol):
    def handle(self, event: ClaimedOutboxEvent) -> None:
        """Handle one event without bypassing the worker's state machine."""


class InternalCampaignUpdatedHandler:
    """Validate the campaign update envelope without producing an external effect."""

    def handle(self, event: ClaimedOutboxEvent) -> None:
        if event.topic != "campaign.updated":
            raise UnsupportedOutboxTopic(event.topic)
        tenant_id = event.payload.get("tenant_id")
        campaign_id = event.payload.get("campaign_id")
        audit_event_id = event.payload.get("audit_event_id")
        version = event.payload.get("version")
        if (
            tenant_id != str(event.tenant_id)
            or event.campaign_id is None
            or campaign_id != str(event.campaign_id)
            or not isinstance(audit_event_id, str)
            or not isinstance(version, int)
            or version < 1
        ):
            raise InvalidOutboxEvent("campaign.updated payload does not match event scope")
        try:
            UUID(audit_event_id)
        except ValueError as exc:
            raise InvalidOutboxEvent("campaign.updated audit_event_id must be a UUID") from exc


@dataclass(slots=True)
class OutboxWorker:
    database: Database
    worker_id: str
    handler: OutboxHandler
    lease_seconds: int = 60
    max_attempts: int = 5
    retry_base_seconds: int = 30

    def __post_init__(self) -> None:
        self.worker_id = self.worker_id.strip()
        if not self.worker_id or len(self.worker_id) > 255:
            raise ValueError("worker_id must contain 1 to 255 characters")
        if not 1 <= self.lease_seconds <= 3600:
            raise ValueError("lease_seconds must be between 1 and 3600")
        if not 1 <= self.max_attempts <= 100:
            raise ValueError("max_attempts must be between 1 and 100")
        if not 1 <= self.retry_base_seconds <= 86400:
            raise ValueError("retry_base_seconds must be between 1 and 86400")

    def run_once(
        self,
        tenant_id: UUID,
        *,
        batch_size: int = 25,
        now: datetime | None = None,
    ) -> OutboxRunResult:
        if not 1 <= batch_size <= 100:
            raise ValueError("batch_size must be between 1 and 100")
        occurred_at = now or datetime.now(UTC)
        try:
            claimed = self._claim(tenant_id, batch_size=batch_size, now=occurred_at)
            delivered = retried = dead_lettered = 0
            for event in claimed:
                try:
                    self.handler.handle(event)
                    self._deliver(tenant_id, event, now=occurred_at)
                except Exception as exc:  # Handler/state failure becomes retry or dead letter.
                    if self._fail(tenant_id, event, exc, now=occurred_at):
                        dead_lettered += 1
                    else:
                        retried += 1
                else:
                    delivered += 1
            return OutboxRunResult(
                claimed=len(claimed),
                delivered=delivered,
                retried=retried,
                dead_lettered=dead_lettered,
            )
        except SQLAlchemyError as exc:
            raise OutboxWorkerUnavailable("Outbox worker is unavailable") from exc

    def _claim(
        self, tenant_id: UUID, *, batch_size: int, now: datetime
    ) -> tuple[ClaimedOutboxEvent, ...]:
        lease_expires_at = now + timedelta(seconds=self.lease_seconds)
        with self.database.tenant_transaction(tenant_id) as session:
            rows = list(
                session.scalars(
                    select(OutboxEvent)
                    .where(
                        OutboxEvent.tenant_id == tenant_id,
                        OutboxEvent.available_at <= now,
                        or_(
                            OutboxEvent.status == "PENDING",
                            (
                                (OutboxEvent.status == "PROCESSING")
                                & (OutboxEvent.lease_expires_at.is_not(None))
                                & (OutboxEvent.lease_expires_at <= now)
                            ),
                        ),
                    )
                    .order_by(OutboxEvent.available_at, OutboxEvent.created_at, OutboxEvent.id)
                    .limit(batch_size)
                    .with_for_update(skip_locked=True)
                )
            )
            claimed: list[ClaimedOutboxEvent] = []
            for row in rows:
                row.status = "PROCESSING"
                row.attempts += 1
                row.lease_owner = self.worker_id
                row.lease_expires_at = lease_expires_at
                row.last_error = None
                claimed.append(
                    ClaimedOutboxEvent(
                        id=row.id,
                        tenant_id=row.tenant_id,
                        campaign_id=row.campaign_id,
                        topic=row.topic,
                        payload=dict(row.payload),
                        attempts=row.attempts,
                        lease_owner=self.worker_id,
                        lease_expires_at=lease_expires_at,
                    )
                )
            session.flush()
            return tuple(claimed)

    def _deliver(self, tenant_id: UUID, event: ClaimedOutboxEvent, *, now: datetime) -> None:
        with self.database.tenant_transaction(tenant_id) as session:
            row = session.scalar(
                select(OutboxEvent)
                .where(
                    OutboxEvent.id == event.id,
                    OutboxEvent.tenant_id == tenant_id,
                    OutboxEvent.status == "PROCESSING",
                    OutboxEvent.lease_owner == self.worker_id,
                )
                .with_for_update()
            )
            if row is None:
                raise OutboxWorkerUnavailable("Outbox event lease is no longer owned")
            if row.campaign_id is not None:
                campaign_exists = session.scalar(
                    select(Campaign.id).where(
                        Campaign.id == row.campaign_id,
                        Campaign.tenant_id == tenant_id,
                    )
                )
                if campaign_exists is None:
                    raise InvalidOutboxEvent("Campaign no longer exists in tenant scope")
            audit_event_id = row.payload.get("audit_event_id")
            try:
                parsed_audit_event_id = UUID(str(audit_event_id))
            except ValueError as exc:
                raise InvalidOutboxEvent("Outbox audit_event_id is invalid") from exc
            audit_exists = session.scalar(
                select(AuditEvent.id).where(
                    AuditEvent.id == parsed_audit_event_id,
                    AuditEvent.tenant_id == tenant_id,
                    AuditEvent.campaign_id == row.campaign_id,
                )
            )
            if audit_exists is None:
                raise InvalidOutboxEvent("Audit event is unavailable in tenant scope")
            row.status = "DELIVERED"
            row.processed_at = now
            row.lease_owner = None
            row.lease_expires_at = None
            row.last_error = None

    def _fail(
        self,
        tenant_id: UUID,
        event: ClaimedOutboxEvent,
        error: Exception,
        *,
        now: datetime,
    ) -> bool:
        with self.database.tenant_transaction(tenant_id) as session:
            row = session.scalar(
                select(OutboxEvent)
                .where(
                    OutboxEvent.id == event.id,
                    OutboxEvent.tenant_id == tenant_id,
                    OutboxEvent.status == "PROCESSING",
                    OutboxEvent.lease_owner == self.worker_id,
                )
                .with_for_update()
            )
            if row is None:
                raise OutboxWorkerUnavailable("Outbox event lease is no longer owned")
            row.last_error = type(error).__name__
            row.lease_owner = None
            row.lease_expires_at = None
            if row.attempts >= self.max_attempts:
                row.status = "DEAD_LETTER"
                row.processed_at = now
                return True
            row.status = "PENDING"
            row.available_at = now + timedelta(
                seconds=self.retry_base_seconds * (2 ** (row.attempts - 1))
            )
            return False
