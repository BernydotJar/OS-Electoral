from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import cast
from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from campaignos.campaigns.create_model import (
    CampaignCreate,
    CampaignCreateConflict,
    CampaignCreateEvidence,
    CampaignCreateIdempotencyConflict,
    CampaignCreateUnavailable,
    InMemoryCampaignCreator,
    SqlAlchemyCampaignCreator,
    UnavailableCampaignCreator,
)
from campaignos.data.audit import AuditScopeUnavailable
from campaignos.data.database import Database, TenantSession
from campaignos.data.models import (
    AuditEvent,
    Base,
    Campaign,
    IdempotencyRecord,
    OutboxEvent,
    Principal,
    Tenant,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
PRINCIPAL_ID = UUID("33333333-3333-4333-8333-333333333333")
GRANT_ID = UUID("44444444-4444-4444-8444-444444444444")
OTHER_GRANT_ID = UUID("55555555-5555-4555-8555-555555555555")
PURPOSE = "Create tenant campaign"


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
        session.add_all(
            [
                Tenant(id=TENANT_ID, slug="tenant", name="Tenant", status="ACTIVE"),
                Tenant(
                    id=OTHER_TENANT_ID,
                    slug="other-tenant",
                    name="Other Tenant",
                    status="ACTIVE",
                ),
                Principal(
                    id=PRINCIPAL_ID,
                    issuer="https://identity.example.test/",
                    subject="campaign-creator",
                ),
            ]
        )
    try:
        yield database
    finally:
        database.dispose()


def request(*, slug: str = "municipal-2028", name: str = "Municipal 2028") -> CampaignCreate:
    return CampaignCreate(
        slug=slug,
        name=name,
        jurisdiction="Antigua Guatemala",
        stage="PRECAMPAIGN",
    )


def create_campaign(
    database: Database,
    *,
    tenant_id: UUID = TENANT_ID,
    create_request: CampaignCreate | None = None,
    idempotency_key: str = "campaign-create-1",
    authorization_grant_id: UUID = GRANT_ID,
    approval_receipt_id: str = "approval-campaign-create",
    authorization_purpose: str = PURPOSE,
    correlation_id: str = "campaign-create-correlation-1",
) -> CampaignCreateEvidence:
    return SqlAlchemyCampaignCreator(database).create(
        tenant_id,
        request=create_request or request(),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=authorization_grant_id,
        approval_receipt_id=approval_receipt_id,
        authorization_purpose=authorization_purpose,
        correlation_id=correlation_id,
        idempotency_key=idempotency_key,
    )


def test_request_normalizes_bounded_metadata_and_rejects_blank_values() -> None:
    normalized = CampaignCreate(
        slug="  Municipal-2028  ",
        name="  Municipal   Campaign  2028 ",
        jurisdiction=" Antigua   Guatemala ",
        stage="  PRECAMPAIGN ",
    )

    assert normalized.model_dump() == {
        "slug": "municipal-2028",
        "name": "Municipal Campaign 2028",
        "jurisdiction": "Antigua Guatemala",
        "stage": "PRECAMPAIGN",
    }
    for field in ("slug", "name", "jurisdiction", "stage"):
        payload = normalized.model_dump()
        payload[field] = "   "
        with pytest.raises(ValidationError):
            CampaignCreate.model_validate(payload)


def test_create_commits_draft_campaign_audit_outbox_and_idempotency(
    database: Database,
) -> None:
    evidence = create_campaign(database)

    assert evidence.campaign.tenant_id == TENANT_ID
    assert evidence.campaign.status == "DRAFT"
    assert evidence.campaign.version == 1
    with database.tenant_transaction(TENANT_ID) as session:
        campaign = session.get(Campaign, evidence.campaign.id)
        audit = session.get(AuditEvent, evidence.audit_event_id)
        outbox = session.get(OutboxEvent, evidence.outbox_event_id)
        idempotency = session.scalar(select(IdempotencyRecord))

    assert campaign is not None
    assert campaign.slug == "municipal-2028"
    assert campaign.status == "DRAFT"
    assert campaign.version == 1
    assert audit is not None
    assert audit.event_type == "campaign.created"
    assert audit.resource_type == "campaign"
    assert audit.resource_id == str(campaign.id)
    assert audit.campaign_id == campaign.id
    assert audit.principal_id == PRINCIPAL_ID
    assert audit.payload["authorization_grant_id"] == str(GRANT_ID)
    assert audit.payload["approval_receipt_id"] == "approval-campaign-create"
    assert audit.payload["authorization_purpose"] == PURPOSE
    assert audit.payload["correlation_id"] == "campaign-create-correlation-1"
    assert audit.payload["external_effects"] == "NONE"
    assert outbox is not None
    assert outbox.topic == "campaign.created"
    assert outbox.campaign_id == campaign.id
    assert outbox.payload["external_effects"] == "NONE"
    assert idempotency is not None
    assert idempotency.operation == "campaign.create"
    assert idempotency.principal_id == PRINCIPAL_ID


def test_same_key_and_normalized_request_replays_exact_evidence_without_duplicates(
    database: Database,
) -> None:
    first = create_campaign(database)
    replay = create_campaign(
        database,
        create_request=request(slug=" MUNICIPAL-2028 ", name=" Municipal   2028 "),
        correlation_id="a-replay-correlation-is-not-new-evidence",
    )

    assert replay == first
    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(Campaign)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1
        audit = session.get(AuditEvent, first.audit_event_id)
        assert audit is not None
        assert audit.payload["correlation_id"] == "campaign-create-correlation-1"


@pytest.mark.parametrize(
    ("create_request", "grant_id", "approval_receipt_id", "authorization_purpose"),
    [
        (request(name="Different"), GRANT_ID, "approval-campaign-create", PURPOSE),
        (request(), OTHER_GRANT_ID, "approval-campaign-create", PURPOSE),
        (request(), GRANT_ID, "different-approval-receipt", PURPOSE),
        (request(), GRANT_ID, "approval-campaign-create", "Different purpose"),
    ],
    ids=[
        "different-request",
        "different-grant",
        "different-approval-receipt",
        "different-purpose",
    ],
)
def test_reused_key_with_different_request_or_authority_fails_closed(
    database: Database,
    create_request: CampaignCreate,
    grant_id: UUID,
    approval_receipt_id: str,
    authorization_purpose: str,
) -> None:
    first = create_campaign(database)

    with pytest.raises(CampaignCreateIdempotencyConflict):
        create_campaign(
            database,
            create_request=create_request,
            authorization_grant_id=grant_id,
            approval_receipt_id=approval_receipt_id,
            authorization_purpose=authorization_purpose,
        )

    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(Campaign)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1
        assert session.get(Campaign, first.campaign.id) is not None


def test_duplicate_slug_with_new_key_is_a_resource_conflict_without_new_evidence(
    database: Database,
) -> None:
    first = create_campaign(database)

    with pytest.raises(CampaignCreateConflict):
        create_campaign(database, idempotency_key="campaign-create-2")

    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(Campaign)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1
        assert session.get(Campaign, first.campaign.id) is not None


def test_same_slug_is_independent_across_tenants(database: Database) -> None:
    tenant_a = create_campaign(database)
    tenant_b = create_campaign(
        database,
        tenant_id=OTHER_TENANT_ID,
        idempotency_key="other-tenant-create-1",
    )

    assert tenant_a.campaign.slug == tenant_b.campaign.slug
    assert tenant_a.campaign.id != tenant_b.campaign.id
    with database.tenant_transaction(TENANT_ID) as session:
        assert list(
            session.scalars(select(Campaign.id).where(Campaign.tenant_id == TENANT_ID))
        ) == [tenant_a.campaign.id]
        assert list(
            session.scalars(select(Campaign.id).where(Campaign.tenant_id == OTHER_TENANT_ID))
        ) == [tenant_b.campaign.id]


def test_audit_failure_rolls_back_campaign_and_all_evidence(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_audit(*args: object, **kwargs: object) -> None:
        del args, kwargs
        raise AuditScopeUnavailable("synthetic audit failure")

    monkeypatch.setattr(
        "campaignos.campaigns.create_model.append_audit_event",
        fail_audit,
    )

    with pytest.raises(CampaignCreateUnavailable):
        create_campaign(database)

    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(Campaign)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 0


def test_in_memory_creator_preserves_replay_conflict_and_no_external_effects() -> None:
    creator = InMemoryCampaignCreator()
    first = creator.create(
        TENANT_ID,
        request=request(),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-campaign-create",
        authorization_purpose=PURPOSE,
        correlation_id="memory-1",
        idempotency_key="memory-create-1",
    )
    replay = creator.create(
        TENANT_ID,
        request=request(),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-campaign-create",
        authorization_purpose=PURPOSE,
        correlation_id="memory-replay",
        idempotency_key="memory-create-1",
    )

    assert replay == first
    assert len(creator.campaigns) == 1
    assert len(creator.audit_events) == 1
    assert len(creator.outbox_events) == 1
    assert creator.outbox_events[0].external_effects == "NONE"
    with pytest.raises(CampaignCreateIdempotencyConflict):
        creator.create(
            TENANT_ID,
            request=request(name="Different"),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-campaign-create",
            authorization_purpose=PURPOSE,
            correlation_id="memory-conflict",
            idempotency_key="memory-create-1",
        )
    with pytest.raises(CampaignCreateConflict):
        creator.create(
            TENANT_ID,
            request=request(),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-campaign-create",
            authorization_purpose=PURPOSE,
            correlation_id="memory-slug-conflict",
            idempotency_key="memory-create-2",
        )


def test_unavailable_creator_fails_closed() -> None:
    with pytest.raises(CampaignCreateUnavailable):
        UnavailableCampaignCreator().create(TENANT_ID, ignored="value")


class BrokenDatabase:
    @contextmanager
    def tenant_transaction(self, tenant_id: UUID) -> Iterator[None]:
        del tenant_id
        raise ValueError("synthetic transaction failure")
        yield  # pragma: no cover - context-manager typing only.


def test_sqlalchemy_creator_maps_internal_failure_to_unavailable() -> None:
    creator = SqlAlchemyCampaignCreator(cast(Database, BrokenDatabase()))

    with pytest.raises(CampaignCreateUnavailable, match="unavailable"):
        creator.create(
            TENANT_ID,
            request=request(),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-campaign-create",
            authorization_purpose=PURPOSE,
            correlation_id="broken-database",
            idempotency_key="broken-create-1",
        )
