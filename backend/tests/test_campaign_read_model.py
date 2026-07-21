from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from campaignos.campaigns import CampaignNotFound, SqlAlchemyCampaignDirectory
from campaignos.data.database import Database, TenantSession
from campaignos.data.models import Base, Campaign, Tenant

TENANT_A = UUID("11111111-1111-4111-8111-111111111111")
TENANT_B = UUID("22222222-2222-4222-8222-222222222222")
CAMPAIGN_A = UUID("33333333-3333-4333-8333-333333333333")
CAMPAIGN_B = UUID("44444444-4444-4444-8444-444444444444")
CAMPAIGN_C = UUID("55555555-5555-4555-8555-555555555555")


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
    db = Database(engine=engine, _sessions=sessions)
    with db.tenant_transaction(TENANT_A) as session:
        session.add_all(
            [
                Tenant(id=TENANT_A, slug="tenant-a", name="Tenant A", status="ACTIVE"),
                Tenant(id=TENANT_B, slug="tenant-b", name="Tenant B", status="ACTIVE"),
                Campaign(
                    id=CAMPAIGN_A,
                    tenant_id=TENANT_A,
                    slug="campaign-a",
                    name="Campaign A",
                    jurisdiction="Antigua Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=2,
                ),
                Campaign(
                    id=CAMPAIGN_B,
                    tenant_id=TENANT_B,
                    slug="campaign-b",
                    name="Campaign B",
                    jurisdiction="Other",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=1,
                ),
                Campaign(
                    id=CAMPAIGN_C,
                    tenant_id=TENANT_A,
                    slug="campaign-c",
                    name="Campaign C",
                    jurisdiction="Antigua Guatemala",
                    stage="PRECAMPAIGN",
                    status="DRAFT",
                    version=1,
                ),
            ]
        )
    try:
        yield db
    finally:
        db.dispose()


def test_directory_returns_only_selected_tenant_campaign(database: Database) -> None:
    projection = SqlAlchemyCampaignDirectory(database).get(TENANT_A, CAMPAIGN_A)

    assert projection.id == CAMPAIGN_A
    assert projection.tenant_id == TENANT_A
    assert projection.version == 2

    with pytest.raises(CampaignNotFound):
        SqlAlchemyCampaignDirectory(database).get(TENANT_A, CAMPAIGN_B)


def test_directory_hides_archived_campaigns(database: Database) -> None:
    with database.tenant_transaction(TENANT_A) as session:
        campaign = session.get(Campaign, CAMPAIGN_A)
        assert campaign is not None
        campaign.status = "ARCHIVED"

    with pytest.raises(CampaignNotFound):
        SqlAlchemyCampaignDirectory(database).get(TENANT_A, CAMPAIGN_A)


def test_directory_uses_authorized_uuid_keyset_pagination(database: Database) -> None:
    directory = SqlAlchemyCampaignDirectory(database)

    first = directory.list_authorized(
        TENANT_A,
        (CAMPAIGN_A, CAMPAIGN_B, CAMPAIGN_C),
        limit=1,
        cursor=None,
    )
    second = directory.list_authorized(
        TENANT_A,
        (CAMPAIGN_A, CAMPAIGN_B, CAMPAIGN_C),
        limit=1,
        cursor=first.next_cursor,
    )

    assert [item.id for item in first.items] == [CAMPAIGN_A]
    assert first.next_cursor == CAMPAIGN_A
    assert [item.id for item in second.items] == [CAMPAIGN_C]
    assert second.next_cursor is None


def test_directory_returns_empty_page_without_authorized_ids(database: Database) -> None:
    page = SqlAlchemyCampaignDirectory(database).list_authorized(
        TENANT_A,
        (),
        limit=25,
        cursor=None,
    )

    assert page.items == ()
    assert page.next_cursor is None
