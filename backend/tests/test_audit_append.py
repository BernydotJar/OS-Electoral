from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from campaignos.data.audit import (
    AuditAppendEvidence,
    AuditScopeUnavailable,
    TenantAuditStreamLock,
    append_audit_event,
    lock_tenant_audit_stream,
)
from campaignos.data.database import Database, TenantSession
from campaignos.data.models import AuditEvent, Base, Tenant

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
FIRST_EVENT_ID = UUID("ffffffff-ffff-4fff-8fff-ffffffffffff")
SECOND_EVENT_ID = UUID("00000000-0000-4000-8000-000000000001")
THIRD_EVENT_ID = UUID("22222222-2222-4222-8222-222222222222")


@pytest.fixture
def database() -> Iterator[Database]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(
        bind=engine,
        class_=TenantSession,
        autoflush=False,
        expire_on_commit=False,
    )
    database = Database(engine=engine, _sessions=sessions)
    with database.tenant_transaction(TENANT_ID) as session:
        session.add(Tenant(id=TENANT_ID, slug="tenant-a", name="Tenant A", status="ACTIVE"))
    try:
        yield database
    finally:
        database.dispose()


def append_tenant_event(
    session: TenantSession,
    audit_lock: TenantAuditStreamLock,
    event_id: UUID,
    value: int,
) -> AuditAppendEvidence:
    return append_audit_event(
        session,
        audit_lock=audit_lock,
        campaign_id=None,
        workspace_id=None,
        principal_id=None,
        event_type="tenant.audit_tested",
        resource_type="tenant",
        resource_id=str(TENANT_ID),
        payload={"value": value},
        event_id=event_id,
    )


def test_audit_appends_are_monotonic_and_keep_the_latest_head(database: Database) -> None:
    with database.tenant_transaction(TENANT_ID) as session:
        audit_lock = lock_tenant_audit_stream(session, TENANT_ID)
        first = append_tenant_event(session, audit_lock, FIRST_EVENT_ID, 1)
        second = append_tenant_event(session, audit_lock, SECOND_EVENT_ID, 2)

    assert second.occurred_at > first.occurred_at
    assert first.previous_hash == "GENESIS"
    assert second.previous_hash == first.event_hash

    with database.tenant_transaction(TENANT_ID) as session:
        audit_lock = lock_tenant_audit_stream(session, TENANT_ID)
        third = append_tenant_event(session, audit_lock, THIRD_EVENT_ID, 3)
        events = list(
            session.scalars(select(AuditEvent).order_by(AuditEvent.occurred_at, AuditEvent.id))
        )

    assert third.occurred_at > second.occurred_at
    assert third.previous_hash == second.event_hash
    assert [event.id for event in events] == [FIRST_EVENT_ID, SECOND_EVENT_ID, THIRD_EVENT_ID]
    assert [event.payload["value"] for event in events] == [1, 2, 3]


def test_audit_lock_cannot_be_reused_by_another_session(database: Database) -> None:
    with database.tenant_transaction(TENANT_ID) as session:
        stale_lock = lock_tenant_audit_stream(session, TENANT_ID)

    with database.tenant_transaction(TENANT_ID) as session:
        with pytest.raises(AuditScopeUnavailable):
            append_tenant_event(session, stale_lock, FIRST_EVENT_ID, 1)
        assert list(session.scalars(select(AuditEvent.id))) == []


def test_workspace_audit_requires_campaign_scope(database: Database) -> None:
    with database.tenant_transaction(TENANT_ID) as session:
        audit_lock = lock_tenant_audit_stream(session, TENANT_ID)
        with pytest.raises(ValueError, match="require campaign scope"):
            append_audit_event(
                session,
                audit_lock=audit_lock,
                campaign_id=None,
                workspace_id=UUID(int=7),
                principal_id=None,
                event_type="workspace.invalid",
                resource_type="workspace",
                resource_id="7",
                payload={},
            )


def test_audit_state_corruption_and_missing_tenant_fail_closed(database: Database) -> None:
    with database.tenant_transaction(TENANT_ID) as session:
        session.info["campaignos.audit_stream_locks"] = "invalid"
        with pytest.raises(AuditScopeUnavailable, match="lock state"):
            lock_tenant_audit_stream(session, TENANT_ID)

    with database.tenant_transaction(TENANT_ID) as session:
        audit_lock = lock_tenant_audit_stream(session, TENANT_ID)
        session.info["campaignos.audit_stream_last_timestamp"] = "invalid"
        with pytest.raises(AuditScopeUnavailable, match="timestamp state"):
            append_tenant_event(session, audit_lock, FIRST_EVENT_ID, 1)

    missing_tenant = UUID("99999999-9999-4999-8999-999999999999")
    with database.tenant_transaction(missing_tenant) as session:
        with pytest.raises(AuditScopeUnavailable, match="scope is unavailable"):
            lock_tenant_audit_stream(session, missing_tenant)
