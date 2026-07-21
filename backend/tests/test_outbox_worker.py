from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from campaignos.data.database import Database, TenantSession
from campaignos.data.models import AuditEvent, Base, Campaign, OutboxEvent, Tenant
from campaignos.workers import (
    ClaimedOutboxEvent,
    InternalCampaignUpdatedHandler,
    OutboxWorker,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")
OTHER_CAMPAIGN_ID = UUID("44444444-4444-4444-8444-444444444444")
NOW = datetime(2026, 7, 21, 6, 0, tzinfo=UTC)


@pytest.fixture
def database() -> Database:
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
        session.add(Tenant(id=TENANT_ID, slug="tenant-a", name="Tenant A"))
        session.add(
            Campaign(
                id=CAMPAIGN_ID,
                tenant_id=TENANT_ID,
                slug="campaign-a",
                name="Campaign A",
                jurisdiction="Test",
                stage="TEST",
            )
        )
    with database.tenant_transaction(OTHER_TENANT_ID) as session:
        session.add(Tenant(id=OTHER_TENANT_ID, slug="tenant-b", name="Tenant B"))
        session.add(
            Campaign(
                id=OTHER_CAMPAIGN_ID,
                tenant_id=OTHER_TENANT_ID,
                slug="campaign-b",
                name="Campaign B",
                jurisdiction="Test",
                stage="TEST",
            )
        )
    try:
        yield database
    finally:
        database.dispose()


def add_event(
    database: Database,
    *,
    tenant_id: UUID = TENANT_ID,
    campaign_id: UUID = CAMPAIGN_ID,
    topic: str = "campaign.updated",
    status: str = "PENDING",
    attempts: int = 0,
    available_at: datetime = NOW,
    lease_owner: str | None = None,
    lease_expires_at: datetime | None = None,
) -> UUID:
    event_id = uuid4()
    audit_event_id = uuid4()
    with database.tenant_transaction(tenant_id) as session:
        session.add(
            AuditEvent(
                id=audit_event_id,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                principal_id=None,
                event_type="campaign.updated",
                resource_type="campaign",
                resource_id=str(campaign_id),
                payload={},
                occurred_at=NOW,
                previous_hash="GENESIS",
                event_hash=uuid4().hex + uuid4().hex,
            )
        )
        session.add(
            OutboxEvent(
                id=event_id,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                topic=topic,
                payload={
                    "audit_event_id": str(audit_event_id),
                    "campaign_id": str(campaign_id),
                    "tenant_id": str(tenant_id),
                    "version": 2,
                },
                status=status,
                attempts=attempts,
                available_at=available_at,
                created_at=NOW,
                lease_owner=lease_owner,
                lease_expires_at=lease_expires_at,
            )
        )
    return event_id


def get_event(database: Database, event_id: UUID, tenant_id: UUID = TENANT_ID) -> OutboxEvent:
    with database.tenant_transaction(tenant_id) as session:
        event = session.scalar(select(OutboxEvent).where(OutboxEvent.id == event_id))
        assert event is not None
        session.expunge(event)
        return event


def test_successful_internal_event_is_delivered_once(database: Database) -> None:
    event_id = add_event(database)
    worker = OutboxWorker(database, "worker-1", InternalCampaignUpdatedHandler())

    first = worker.run_once(TENANT_ID, now=NOW)
    second = worker.run_once(TENANT_ID, now=NOW + timedelta(minutes=1))

    assert first.claimed == first.delivered == 1
    assert first.retried == first.dead_lettered == 0
    assert second.claimed == 0
    event = get_event(database, event_id)
    assert event.status == "DELIVERED"
    assert event.attempts == 1
    assert event.processed_at is not None and event.processed_at.replace(tzinfo=UTC) == NOW
    assert event.lease_owner is None and event.lease_expires_at is None


def test_failure_is_retried_with_exponential_backoff(database: Database) -> None:
    event_id = add_event(database, topic="unsupported.topic")
    worker = OutboxWorker(
        database,
        "worker-1",
        InternalCampaignUpdatedHandler(),
        max_attempts=3,
        retry_base_seconds=10,
    )

    result = worker.run_once(TENANT_ID, now=NOW)

    assert result.retried == 1 and result.dead_lettered == 0
    event = get_event(database, event_id)
    assert event.status == "PENDING"
    assert event.attempts == 1
    assert event.available_at.replace(tzinfo=UTC) == NOW + timedelta(seconds=10)
    assert event.last_error is not None and "UnsupportedOutboxTopic" in event.last_error


def test_final_failure_moves_event_to_dead_letter(database: Database) -> None:
    event_id = add_event(database, topic="unsupported.topic", attempts=2)
    worker = OutboxWorker(
        database,
        "worker-1",
        InternalCampaignUpdatedHandler(),
        max_attempts=3,
    )

    result = worker.run_once(TENANT_ID, now=NOW)

    assert result.dead_lettered == 1 and result.retried == 0
    event = get_event(database, event_id)
    assert event.status == "DEAD_LETTER"
    assert event.attempts == 3
    assert event.processed_at is not None and event.processed_at.replace(tzinfo=UTC) == NOW


def test_missing_audit_evidence_is_retried_without_delivery(database: Database) -> None:
    event_id = add_event(database)
    with database.tenant_transaction(TENANT_ID) as session:
        event = session.get(OutboxEvent, event_id)
        assert event is not None
        audit_id = UUID(str(event.payload["audit_event_id"]))
        audit = session.get(AuditEvent, audit_id)
        assert audit is not None
        session.delete(audit)

    worker = OutboxWorker(database, "worker-1", InternalCampaignUpdatedHandler())
    result = worker.run_once(TENANT_ID, now=NOW)

    assert result.retried == 1 and result.delivered == 0
    event = get_event(database, event_id)
    assert event.status == "PENDING"
    assert event.last_error == "InvalidOutboxEvent"


def test_expired_processing_lease_is_recovered(database: Database) -> None:
    event_id = add_event(
        database,
        status="PROCESSING",
        attempts=1,
        lease_owner="crashed-worker",
        lease_expires_at=NOW - timedelta(seconds=1),
    )
    worker = OutboxWorker(database, "worker-2", InternalCampaignUpdatedHandler())

    result = worker.run_once(TENANT_ID, now=NOW)

    assert result.delivered == 1
    event = get_event(database, event_id)
    assert event.status == "DELIVERED" and event.attempts == 2


def test_active_lease_and_future_event_are_not_claimed(database: Database) -> None:
    active_id = add_event(
        database,
        status="PROCESSING",
        lease_owner="worker-1",
        lease_expires_at=NOW + timedelta(minutes=1),
    )
    future_id = add_event(database, available_at=NOW + timedelta(minutes=1))
    worker = OutboxWorker(database, "worker-2", InternalCampaignUpdatedHandler())

    result = worker.run_once(TENANT_ID, now=NOW)

    assert result.claimed == 0
    assert get_event(database, active_id).status == "PROCESSING"
    assert get_event(database, future_id).status == "PENDING"


def test_worker_claim_is_explicitly_tenant_scoped(database: Database) -> None:
    local_id = add_event(database)
    foreign_id = add_event(
        database,
        tenant_id=OTHER_TENANT_ID,
        campaign_id=OTHER_CAMPAIGN_ID,
    )
    worker = OutboxWorker(database, "worker-1", InternalCampaignUpdatedHandler())

    result = worker.run_once(TENANT_ID, now=NOW)

    assert result.delivered == 1
    assert get_event(database, local_id).status == "DELIVERED"
    assert get_event(database, foreign_id, OTHER_TENANT_ID).status == "PENDING"


def test_worker_configuration_fails_closed(database: Database) -> None:
    with pytest.raises(ValueError, match="worker_id"):
        OutboxWorker(database, " ", InternalCampaignUpdatedHandler())
    with pytest.raises(ValueError, match="lease_seconds"):
        OutboxWorker(database, "worker", InternalCampaignUpdatedHandler(), lease_seconds=0)
    with pytest.raises(ValueError, match="max_attempts"):
        OutboxWorker(database, "worker", InternalCampaignUpdatedHandler(), max_attempts=0)


def test_invalid_batch_size_is_rejected_before_database_access(database: Database) -> None:
    worker = OutboxWorker(database, "worker-1", InternalCampaignUpdatedHandler())

    with pytest.raises(ValueError):
        worker.run_once(TENANT_ID, batch_size=0, now=NOW)


def test_handler_rejects_scope_mismatch() -> None:
    event = ClaimedOutboxEvent(
        id=uuid4(),
        tenant_id=TENANT_ID,
        campaign_id=CAMPAIGN_ID,
        topic="campaign.updated",
        payload={
            "audit_event_id": str(uuid4()),
            "campaign_id": str(CAMPAIGN_ID),
            "tenant_id": str(OTHER_TENANT_ID),
            "version": 2,
        },
        attempts=1,
        lease_owner="worker-1",
        lease_expires_at=NOW + timedelta(minutes=1),
    )

    with pytest.raises(Exception, match="payload does not match"):
        InternalCampaignUpdatedHandler().handle(event)
