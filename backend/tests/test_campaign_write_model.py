from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from campaignos.campaigns import (
    CampaignUpdate,
    CampaignWriteConflict,
    SqlAlchemyCampaignWriter,
)
from campaignos.data.database import Database, TenantSession
from campaignos.data.models import AuditEvent, Base, Campaign, OutboxEvent, Principal, Tenant

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
PRINCIPAL_ID = UUID("33333333-3333-4333-8333-333333333333")
GRANT_ID = UUID("44444444-4444-4444-8444-444444444444")


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
        session.add_all(
            [
                Tenant(id=TENANT_ID, slug="tenant", name="Tenant", status="ACTIVE"),
                Principal(
                    id=PRINCIPAL_ID,
                    issuer="https://identity.example.test/",
                    subject="writer",
                ),
                Campaign(
                    id=CAMPAIGN_ID,
                    tenant_id=TENANT_ID,
                    slug="campaign",
                    name="Before",
                    jurisdiction="Antigua Guatemala",
                    stage="PRECAMPAIGN",
                    status="DRAFT",
                    version=1,
                ),
            ]
        )
    try:
        yield database
    finally:
        database.dispose()


def _update(database: Database, *, expected_version: int = 1):
    return SqlAlchemyCampaignWriter(database).update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=expected_version,
        changes=CampaignUpdate(name="After", status="ACTIVE"),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-1",
        correlation_id="correlation-1",
    )


def test_update_commits_campaign_audit_and_outbox_atomically(database: Database) -> None:
    evidence = _update(database)

    assert evidence.campaign.name == "After"
    assert evidence.campaign.status == "ACTIVE"
    assert evidence.campaign.version == 2
    with database.tenant_transaction(TENANT_ID) as session:
        campaign = session.get(Campaign, CAMPAIGN_ID)
        audit = session.scalar(select(AuditEvent))
        outbox = session.scalar(select(OutboxEvent))
        assert campaign is not None and campaign.version == 2
        assert audit is not None
        assert audit.id == evidence.audit_event_id
        assert audit.previous_hash == "GENESIS"
        assert len(audit.event_hash) == 64
        assert audit.payload["authorization_grant_id"] == str(GRANT_ID)
        assert outbox is not None
        assert outbox.id == evidence.outbox_event_id
        assert outbox.status == "PENDING"
        assert outbox.payload["version"] == 2


def test_stale_version_rolls_back_without_evidence(database: Database) -> None:
    with pytest.raises(CampaignWriteConflict):
        _update(database, expected_version=99)

    with database.tenant_transaction(TENANT_ID) as session:
        campaign = session.get(Campaign, CAMPAIGN_ID)
        assert campaign is not None and campaign.version == 1 and campaign.name == "Before"
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0


def test_second_update_links_audit_hash_chain(database: Database) -> None:
    first = _update(database)
    second = SqlAlchemyCampaignWriter(database).update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=2,
        changes=CampaignUpdate(stage="ACTIVE_CAMPAIGN"),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-1",
        correlation_id="correlation-2",
    )

    with database.tenant_transaction(TENANT_ID) as session:
        events = list(
            session.scalars(select(AuditEvent).order_by(AuditEvent.occurred_at, AuditEvent.id))
        )
    assert len(events) == 2
    assert events[0].id == first.audit_event_id
    assert events[1].id == second.audit_event_id
    assert events[1].previous_hash == events[0].event_hash
