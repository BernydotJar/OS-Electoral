from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import cast
from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from campaignos.campaigns import (
    CampaignReadinessInput,
    CampaignReadinessNotFound,
    CampaignReadinessProjection,
    CampaignReadinessUnavailable,
    InMemoryCampaignReadinessReader,
    SqlAlchemyCampaignReadinessReader,
    UnavailableCampaignReadinessReader,
    assess_campaign_readiness,
)
from campaignos.data.database import Database, TenantSession
from campaignos.data.models import (
    AuditEvent,
    Base,
    Campaign,
    OutboxEvent,
    Principal,
    Tenant,
    Workspace,
)

TENANT_A = UUID("11111111-1111-4111-8111-111111111111")
TENANT_B = UUID("22222222-2222-4222-8222-222222222222")
PRINCIPAL_ID = UUID("33333333-3333-4333-8333-333333333333")
CAMPAIGN_A = UUID("44444444-4444-4444-8444-444444444444")
CAMPAIGN_B = UUID("55555555-5555-4555-8555-555555555555")
WORKSPACE_ACTIVE = UUID("66666666-6666-4666-8666-666666666666")
WORKSPACE_ARCHIVED = UUID("77777777-7777-4777-8777-777777777777")
GRANT_ID = UUID("88888888-8888-4888-8888-888888888888")
PURPOSE = "Assess assigned campaign readiness"


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
    created_at = datetime(2026, 7, 21, tzinfo=UTC)
    with database.tenant_transaction(TENANT_A) as session:
        session.add_all(
            [
                Tenant(id=TENANT_A, slug="tenant-a", name="Tenant A", status="ACTIVE"),
                Tenant(id=TENANT_B, slug="tenant-b", name="Tenant B", status="ACTIVE"),
                Principal(
                    id=PRINCIPAL_ID,
                    issuer="https://identity.example.test/",
                    subject="readiness-user",
                ),
                Campaign(
                    id=CAMPAIGN_A,
                    tenant_id=TENANT_A,
                    slug="campaign-a",
                    name="Campaign A",
                    jurisdiction="Antigua Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=3,
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
                Workspace(
                    id=WORKSPACE_ACTIVE,
                    tenant_id=TENANT_A,
                    campaign_id=CAMPAIGN_A,
                    slug="governance",
                    name="Governance",
                    status="ACTIVE",
                    version=1,
                    created_at=created_at,
                    updated_at=created_at,
                ),
                Workspace(
                    id=WORKSPACE_ARCHIVED,
                    tenant_id=TENANT_A,
                    campaign_id=CAMPAIGN_A,
                    slug="archived",
                    name="Archived",
                    status="ARCHIVED",
                    version=1,
                    created_at=created_at,
                    updated_at=created_at,
                ),
            ]
        )
    try:
        yield database
    finally:
        database.dispose()


def readiness_input(
    *,
    name: str = "Campaign A",
    jurisdiction: str = "Antigua Guatemala",
    stage: str = "PRECAMPAIGN",
    active_workspace_count: int = 1,
) -> CampaignReadinessInput:
    return CampaignReadinessInput(
        tenant_id=TENANT_A,
        campaign_id=CAMPAIGN_A,
        campaign_version=3,
        campaign_status="ACTIVE",
        name=name,
        jurisdiction=jurisdiction,
        stage=stage,
        active_workspace_count=active_workspace_count,
    )


def test_policy_reports_metadata_workspace_and_ready_states_without_approval_claims() -> None:
    metadata_missing = assess_campaign_readiness(readiness_input(name="", stage=""))
    workspace_missing = assess_campaign_readiness(readiness_input(active_workspace_count=0))
    ready = assess_campaign_readiness(readiness_input())

    assert metadata_missing.status == "NEEDS_CAMPAIGN_METADATA"
    assert metadata_missing.next_action == "COMPLETE_CAMPAIGN_METADATA"
    assert metadata_missing.completed_checks == 2
    assert not metadata_missing.ready_for_guided_intake

    assert workspace_missing.status == "NEEDS_CAMPAIGN_WORKSPACE"
    assert workspace_missing.next_action == "CREATE_CAMPAIGN_WORKSPACE"
    assert workspace_missing.completed_checks == 3

    assert ready.status == "READY_FOR_GUIDED_INTAKE"
    assert ready.next_action == "BEGIN_GUIDED_INTAKE"
    assert ready.completed_checks == ready.total_checks == 4
    assert ready.ready_for_guided_intake
    assert ready.readiness_scope == "OPERATIONAL_SETUP_ONLY"
    assert ready.limitation_codes == (
        "NOT_A_HUMAN_APPROVAL",
        "NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT",
    )


def test_in_memory_adapter_keeps_scope_and_records_sensitive_read_audit() -> None:
    reader = InMemoryCampaignReadinessReader(snapshots={(TENANT_A, CAMPAIGN_A): readiness_input()})

    evidence = reader.get(
        TENANT_A,
        CAMPAIGN_A,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-readiness",
        authorization_purpose=PURPOSE,
        correlation_id="readiness-in-memory",
    )

    assert evidence.readiness.ready_for_guided_intake
    assert len(reader.audit_events) == 1
    audit = reader.audit_events[0]
    assert audit.audit_event_id == evidence.audit_event_id
    assert audit.tenant_id == TENANT_A
    assert audit.campaign_id == CAMPAIGN_A
    assert audit.authorization_grant_id == GRANT_ID
    assert audit.authorization_purpose == PURPOSE
    assert audit.correlation_id == "readiness-in-memory"

    with pytest.raises(CampaignReadinessNotFound):
        reader.get(
            TENANT_A,
            CAMPAIGN_B,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-readiness",
            authorization_purpose=PURPOSE,
            correlation_id="missing",
        )
    assert len(reader.audit_events) == 1


def test_sqlalchemy_reader_commits_hash_linked_audits_without_outbox(
    database: Database,
) -> None:
    reader = SqlAlchemyCampaignReadinessReader(database)

    first = reader.get(
        TENANT_A,
        CAMPAIGN_A,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-readiness",
        authorization_purpose=PURPOSE,
        correlation_id="readiness-1",
    )
    second = reader.get(
        TENANT_A,
        CAMPAIGN_A,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-readiness",
        authorization_purpose=PURPOSE,
        correlation_id="readiness-2",
    )

    assert first.readiness.status == "READY_FOR_GUIDED_INTAKE"
    assert first.readiness.active_workspace_count == 1
    assert second.readiness == first.readiness

    with database.tenant_transaction(TENANT_A) as session:
        events = list(
            session.scalars(select(AuditEvent).order_by(AuditEvent.occurred_at, AuditEvent.id))
        )
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0

    assert [event.id for event in events] == [first.audit_event_id, second.audit_event_id]
    assert events[0].previous_hash == "GENESIS"
    assert events[1].previous_hash == events[0].event_hash
    assert events[0].event_type == "campaign.readiness_viewed"
    assert events[0].resource_type == "campaign_readiness"
    assert events[0].resource_id == str(CAMPAIGN_A)
    assert events[0].payload["authorization_grant_id"] == str(GRANT_ID)
    assert events[0].payload["authorization_purpose"] == PURPOSE
    assert events[0].payload["correlation_id"] == "readiness-1"
    assert events[0].payload["external_effects"] == "NONE"


def test_sqlalchemy_reader_hides_foreign_or_archived_campaign_without_audit(
    database: Database,
) -> None:
    reader = SqlAlchemyCampaignReadinessReader(database)

    for campaign_id in (CAMPAIGN_B, UUID(int=9)):
        with pytest.raises(CampaignReadinessNotFound):
            reader.get(
                TENANT_A,
                campaign_id,
                principal_id=PRINCIPAL_ID,
                authorization_grant_id=GRANT_ID,
                approval_receipt_id="approval-readiness",
                authorization_purpose=PURPOSE,
                correlation_id="not-found",
            )

    with database.tenant_transaction(TENANT_A) as session:
        campaign = session.get(Campaign, CAMPAIGN_A)
        assert campaign is not None
        campaign.status = "ARCHIVED"

    with pytest.raises(CampaignReadinessNotFound):
        reader.get(
            TENANT_A,
            CAMPAIGN_A,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-readiness",
            authorization_purpose=PURPOSE,
            correlation_id="archived",
        )

    with database.tenant_transaction(TENANT_A) as session:
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0


def test_projection_rejects_internally_inconsistent_summaries() -> None:
    valid = assess_campaign_readiness(readiness_input())
    baseline = valid.model_dump(mode="python")

    invalid_payloads: list[dict[str, object]] = []
    wrong_total = dict(baseline)
    wrong_total["total_checks"] = 5
    invalid_payloads.append(wrong_total)

    wrong_completed = dict(baseline)
    wrong_completed["completed_checks"] = 3
    invalid_payloads.append(wrong_completed)

    wrong_order = dict(baseline)
    wrong_order["checks"] = tuple(reversed(valid.checks))
    invalid_payloads.append(wrong_order)

    wrong_ready = dict(baseline)
    wrong_ready["ready_for_guided_intake"] = False
    invalid_payloads.append(wrong_ready)

    wrong_status = dict(baseline)
    wrong_status["status"] = "NEEDS_CAMPAIGN_WORKSPACE"
    invalid_payloads.append(wrong_status)

    wrong_next_action = dict(baseline)
    wrong_next_action["next_action"] = "CREATE_CAMPAIGN_WORKSPACE"
    invalid_payloads.append(wrong_next_action)

    wrong_reason = dict(baseline)
    wrong_reason_checks = [check.model_dump() for check in valid.checks]
    wrong_reason_checks[0]["reason_code"] = "CAMPAIGN_NAME_MISSING"
    wrong_reason["checks"] = wrong_reason_checks
    invalid_payloads.append(wrong_reason)

    wrong_workspace_count = dict(baseline)
    wrong_workspace_count["active_workspace_count"] = 0
    invalid_payloads.append(wrong_workspace_count)

    missing_limitations = dict(baseline)
    missing_limitations["limitation_codes"] = ()
    invalid_payloads.append(missing_limitations)

    for payload in invalid_payloads:
        with pytest.raises(ValidationError):
            CampaignReadinessProjection.model_validate(payload)


def test_unavailable_and_scope_corrupt_adapters_fail_closed() -> None:
    unavailable = UnavailableCampaignReadinessReader()
    with pytest.raises(CampaignReadinessUnavailable):
        unavailable.get(TENANT_A, CAMPAIGN_A, ignored="value")

    corrupt_source = readiness_input().model_copy(update={"campaign_id": CAMPAIGN_B})
    reader = InMemoryCampaignReadinessReader(snapshots={(TENANT_A, CAMPAIGN_A): corrupt_source})
    with pytest.raises(CampaignReadinessUnavailable):
        reader.get(
            TENANT_A,
            CAMPAIGN_A,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-readiness",
            authorization_purpose=PURPOSE,
            correlation_id="scope-corrupt",
        )
    assert reader.audit_events == []


class BrokenReadinessDatabase:
    @contextmanager
    def tenant_transaction(self, tenant_id: UUID) -> Iterator[None]:
        del tenant_id
        raise ValueError("synthetic transaction failure")
        yield  # pragma: no cover - required only to type this as a context manager.


def test_sqlalchemy_reader_maps_internal_transaction_failure_to_unavailable() -> None:
    reader = SqlAlchemyCampaignReadinessReader(cast(Database, BrokenReadinessDatabase()))

    with pytest.raises(CampaignReadinessUnavailable, match="unavailable"):
        reader.get(
            TENANT_A,
            CAMPAIGN_A,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-readiness",
            authorization_purpose=PURPOSE,
            correlation_id="broken-database",
        )
