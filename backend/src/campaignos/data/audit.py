"""Append-only tenant audit helpers shared by domain boundaries."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from campaignos.data.models import AuditEvent, Tenant

GENESIS_HASH = "GENESIS"
_LOCKS_KEY = "campaignos.audit_stream_locks"
_LAST_TIMESTAMP_KEY = "campaignos.audit_stream_last_timestamp"


class AuditScopeUnavailable(RuntimeError):
    """The tenant audit stream cannot be locked or appended safely."""


@dataclass(frozen=True, slots=True)
class TenantAuditStreamLock:
    """Session-bound proof that one tenant audit stream is serialized."""

    tenant_id: UUID
    token: UUID
    acquired_at: datetime


@dataclass(frozen=True, slots=True)
class AuditAppendEvidence:
    """Identifiers and chain metadata produced by one append."""

    event_id: UUID
    occurred_at: datetime
    previous_hash: str
    event_hash: str


def _session_locks(session: Session) -> dict[UUID, UUID]:
    value = session.info.setdefault(_LOCKS_KEY, {})
    if not isinstance(value, dict):
        raise AuditScopeUnavailable("Tenant audit lock state is invalid")
    return cast(dict[UUID, UUID], value)


def _last_timestamps(session: Session) -> dict[UUID, datetime]:
    value = session.info.setdefault(_LAST_TIMESTAMP_KEY, {})
    if not isinstance(value, dict):
        raise AuditScopeUnavailable("Tenant audit timestamp state is invalid")
    return cast(dict[UUID, datetime], value)


def _as_utc(value: datetime) -> datetime:
    if value.utcoffset() is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def lock_tenant_audit_stream(session: Session, tenant_id: UUID) -> TenantAuditStreamLock:
    """Lock one stable tenant row and establish a monotonic audit clock."""
    locked_tenant_id = session.scalar(
        select(Tenant.id).where(Tenant.id == tenant_id).with_for_update()
    )
    if locked_tenant_id != tenant_id:
        raise AuditScopeUnavailable("Tenant audit scope is unavailable")
    token = uuid4()
    _session_locks(session)[tenant_id] = token
    return TenantAuditStreamLock(
        tenant_id=tenant_id,
        token=token,
        acquired_at=datetime.now(UTC),
    )


def canonical_hash(value: object) -> str:
    """Return a stable SHA-256 digest for JSON-compatible audit evidence."""
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def append_audit_event(
    session: Session,
    *,
    audit_lock: TenantAuditStreamLock,
    campaign_id: UUID | None,
    workspace_id: UUID | None,
    principal_id: UUID | None,
    event_type: str,
    resource_type: str,
    resource_id: str,
    payload: dict[str, Any],
    event_id: UUID | None = None,
) -> AuditAppendEvidence:
    """Append one monotonic hash-linked event under a session-bound tenant lock."""
    tenant_id = audit_lock.tenant_id
    if _session_locks(session).get(tenant_id) != audit_lock.token:
        raise AuditScopeUnavailable("Tenant audit lock is not valid for this session")
    if workspace_id is not None and campaign_id is None:
        raise ValueError("workspace-scoped audit events require campaign scope")

    previous = session.execute(
        select(AuditEvent.event_hash, AuditEvent.occurred_at)
        .where(AuditEvent.tenant_id == tenant_id)
        .order_by(AuditEvent.occurred_at.desc(), AuditEvent.id.desc())
        .limit(1)
        .with_for_update()
    ).first()
    previous_hash = previous.event_hash if previous is not None else GENESIS_HASH

    timestamp_floor = audit_lock.acquired_at
    if previous is not None:
        timestamp_floor = max(
            timestamp_floor, _as_utc(previous.occurred_at) + timedelta(microseconds=1)
        )
    last_timestamp = _last_timestamps(session).get(tenant_id)
    if last_timestamp is not None:
        timestamp_floor = max(timestamp_floor, last_timestamp + timedelta(microseconds=1))
    occurred_at = max(datetime.now(UTC), timestamp_floor)

    audit_event_id = event_id or uuid4()
    hash_input = {
        "id": str(audit_event_id),
        "tenant_id": str(tenant_id),
        "campaign_id": str(campaign_id) if campaign_id is not None else None,
        "workspace_id": str(workspace_id) if workspace_id is not None else None,
        "principal_id": str(principal_id) if principal_id is not None else None,
        "event_type": event_type,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "payload": payload,
        "occurred_at": occurred_at.isoformat(),
        "previous_hash": previous_hash,
    }
    event_hash = canonical_hash(hash_input)
    session.add(
        AuditEvent(
            id=audit_event_id,
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            workspace_id=workspace_id,
            principal_id=principal_id,
            event_type=event_type,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload,
            occurred_at=occurred_at,
            previous_hash=previous_hash,
            event_hash=event_hash,
        )
    )
    # A second append in the same transaction must observe this event as the head.
    # A later caller failure still rolls the entire surrounding transaction back.
    session.flush()
    _last_timestamps(session)[tenant_id] = occurred_at
    return AuditAppendEvidence(
        event_id=audit_event_id,
        occurred_at=occurred_at,
        previous_hash=previous_hash,
        event_hash=event_hash,
    )
