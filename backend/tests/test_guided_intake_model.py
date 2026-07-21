from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from campaignos.data.audit import AuditScopeUnavailable
from campaignos.data.database import Database, TenantSession
from campaignos.data.models import (
    AuditEvent,
    Base,
    Campaign,
    GuidedIntake,
    IdempotencyRecord,
    OutboxEvent,
    Principal,
    Tenant,
    Workspace,
)
from campaignos.onboarding import GuidedIntakeUpdate
from campaignos.onboarding.service import (
    GuidedIntakeIdempotencyConflict,
    GuidedIntakeNotFound,
    GuidedIntakePrerequisiteConflict,
    GuidedIntakeUnavailable,
    GuidedIntakeVersionConflict,
    SqlAlchemyGuidedIntakeService,
    UnavailableGuidedIntakeService,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")
OTHER_CAMPAIGN_ID = UUID("44444444-4444-4444-8444-444444444444")
WORKSPACE_ID = UUID("55555555-5555-4555-8555-555555555555")
PRINCIPAL_ID = UUID("66666666-6666-4666-8666-666666666666")
GRANT_ID = UUID("77777777-7777-4777-8777-777777777777")
START_PURPOSE = "Begin guided campaign intake"
READ_PURPOSE = "Review guided campaign intake"
UPDATE_PURPOSE = "Maintain guided campaign intake"


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
    runtime = Database(engine=engine, _sessions=sessions)
    with runtime.tenant_transaction(TENANT_ID) as session:
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
                    subject="guided-intake-operator",
                ),
            ]
        )
        session.flush()
        session.add_all(
            [
                Campaign(
                    id=CAMPAIGN_ID,
                    tenant_id=TENANT_ID,
                    slug="campaign",
                    name="Campaign",
                    jurisdiction="Antigua Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=2,
                ),
                Campaign(
                    id=OTHER_CAMPAIGN_ID,
                    tenant_id=OTHER_TENANT_ID,
                    slug="other-campaign",
                    name="Other Campaign",
                    jurisdiction="Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=1,
                ),
            ]
        )
        session.flush()
        session.add(
            Workspace(
                id=WORKSPACE_ID,
                tenant_id=TENANT_ID,
                campaign_id=CAMPAIGN_ID,
                slug="governance",
                name="Governance",
                status="ACTIVE",
                version=1,
            )
        )
    try:
        yield runtime
    finally:
        runtime.dispose()


def start(
    database: Database,
    *,
    tenant_id: UUID = TENANT_ID,
    campaign_id: UUID = CAMPAIGN_ID,
    key: str = "guided-intake-start-1",
    grant_id: UUID = GRANT_ID,
    receipt: str = "approval-guided-intake-start",
    purpose: str = START_PURPOSE,
):
    return SqlAlchemyGuidedIntakeService(database).start(
        tenant_id,
        campaign_id,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=grant_id,
        approval_receipt_id=receipt,
        authorization_purpose=purpose,
        correlation_id="guided-intake-start-correlation",
        idempotency_key=key,
    )


def complete_update() -> GuidedIntakeUpdate:
    return GuidedIntakeUpdate(
        office="Alcaldía Municipal",
        candidate_project="Proyecto ciudadano sujeto a evidencia y revisión humana.",
        current_team=["Directora de campaña"],
        current_assets=[],
        budget_status="DOCUMENTED",
        known_unknowns=["Requisitos de inscripción"],
        evidence_requirements=["Identidad", "Biografía verificable"],
    )


def test_unavailable_service_fails_closed() -> None:
    with pytest.raises(GuidedIntakeUnavailable):
        UnavailableGuidedIntakeService().start(
            TENANT_ID,
            CAMPAIGN_ID,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose=START_PURPOSE,
            correlation_id="unavailable",
            idempotency_key="unavailable",
        )


def test_start_requires_operational_campaign_setup_without_partial_evidence(
    database: Database,
) -> None:
    with database.tenant_transaction(TENANT_ID) as session:
        workspace = session.get(Workspace, WORKSPACE_ID)
        assert workspace is not None
        workspace.status = "ARCHIVED"

    with pytest.raises(GuidedIntakePrerequisiteConflict) as exc_info:
        start(database)

    assert exc_info.value.missing_requirements == ("active_workspace",)
    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(GuidedIntake)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 0


def test_start_commits_blank_intake_audit_outbox_and_replay(database: Database) -> None:
    evidence = start(database)

    assert evidence.created is True
    assert evidence.outbox_event_id is not None
    assert evidence.intake.status == "IN_PROGRESS"
    assert evidence.intake.version == 1
    assert evidence.intake.next_action == "DEFINE_TARGET_OFFICE"
    assert evidence.intake.campaign_version == 2
    assert evidence.intake.jurisdiction == "Antigua Guatemala"
    assert evidence.intake.limitation_codes[-1] == "NO_EXTERNAL_EFFECTS"

    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(GuidedIntake, evidence.intake.id)
        audit = session.get(AuditEvent, evidence.audit_event_id)
        outbox = session.get(OutboxEvent, evidence.outbox_event_id)
        replay = session.scalar(select(IdempotencyRecord))
        assert row is not None
        assert row.tenant_id == TENANT_ID
        assert row.campaign_id == CAMPAIGN_ID
        assert row.status == "IN_PROGRESS"
        assert audit is not None
        assert audit.event_type == "guided_intake.started"
        assert audit.payload["authorization_grant_id"] == str(GRANT_ID)
        assert audit.payload["authorization_purpose"] == START_PURPOSE
        assert audit.payload["external_effects"] == "NONE"
        assert outbox is not None
        assert outbox.topic == "guided_intake.started"
        assert outbox.payload["external_effects"] == "NONE"
        assert replay is not None
        assert replay.operation == "guided_intake.start"


def test_same_start_key_replays_exact_evidence_and_new_key_resumes(database: Database) -> None:
    first = start(database)
    replay = start(database)
    resumed = start(database, key="guided-intake-resume-2")

    assert replay == first
    assert resumed.created is False
    assert resumed.outbox_event_id is None
    assert resumed.intake.id == first.intake.id
    assert resumed.audit_event_id != first.audit_event_id
    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(GuidedIntake)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 2
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 2
        events = list(session.scalars(select(AuditEvent).order_by(AuditEvent.occurred_at)))
        assert [event.event_type for event in events] == [
            "guided_intake.started",
            "guided_intake.resumed",
        ]


@pytest.mark.parametrize(
    ("grant_id", "receipt", "purpose"),
    [
        (uuid4(), "approval-guided-intake-start", START_PURPOSE),
        (GRANT_ID, "different-receipt", START_PURPOSE),
        (GRANT_ID, "approval-guided-intake-start", "Different purpose"),
    ],
)
def test_start_key_is_bound_to_exact_authority(
    database: Database,
    grant_id: UUID,
    receipt: str,
    purpose: str,
) -> None:
    start(database)
    with pytest.raises(GuidedIntakeIdempotencyConflict):
        start(database, grant_id=grant_id, receipt=receipt, purpose=purpose)


def test_update_reaches_ready_for_research_and_replays_without_duplicates(
    database: Database,
) -> None:
    started = start(database)
    service = SqlAlchemyGuidedIntakeService(database)
    updated = service.update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=1,
        changes=complete_update(),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-guided-intake-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="guided-intake-update-correlation",
        idempotency_key="guided-intake-update-1",
    )
    replay = service.update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=1,
        changes=complete_update(),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-guided-intake-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="different-correlation-is-not-new-evidence",
        idempotency_key="guided-intake-update-1",
    )

    assert replay == updated
    assert updated.intake.id == started.intake.id
    assert updated.intake.version == 2
    assert updated.intake.status == "READY_FOR_RESEARCH"
    assert updated.intake.ready_for_research is True
    assert updated.intake.next_action == "BEGIN_RESEARCH"
    assert updated.intake.completed_checks == updated.intake.total_checks == 8
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(GuidedIntake, started.intake.id)
        audit = session.get(AuditEvent, updated.audit_event_id)
        outbox = session.get(OutboxEvent, updated.outbox_event_id)
        assert row is not None
        assert row.current_team == ["Directora de campaña"]
        assert row.current_assets == []
        assert row.version == 2
        assert audit is not None
        assert audit.event_type == "guided_intake.updated"
        assert sorted(audit.payload["changed_fields"]) == sorted(complete_update().model_fields_set)
        assert outbox is not None
        assert outbox.topic == "guided_intake.updated"
        assert session.scalar(select(func.count()).select_from(GuidedIntake)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 2
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 2
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 2


def test_update_rejects_stale_version_and_changed_replay_intent(database: Database) -> None:
    start(database)
    service = SqlAlchemyGuidedIntakeService(database)
    service.update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=1,
        changes=GuidedIntakeUpdate(office="Alcaldía Municipal"),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="first-update",
        idempotency_key="update-key",
    )

    with pytest.raises(GuidedIntakeIdempotencyConflict):
        service.update(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=1,
            changes=GuidedIntakeUpdate(office="Concejo Municipal"),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-update",
            authorization_purpose=UPDATE_PURPOSE,
            correlation_id="changed-intent",
            idempotency_key="update-key",
        )
    with pytest.raises(GuidedIntakeVersionConflict):
        service.update(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=1,
            changes=GuidedIntakeUpdate(candidate_project="Proyecto actualizado"),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-update",
            authorization_purpose=UPDATE_PURPOSE,
            correlation_id="stale-version",
            idempotency_key="different-update-key",
        )


def test_read_appends_audit_without_outbox(database: Database) -> None:
    started = start(database)
    evidence = SqlAlchemyGuidedIntakeService(database).get(
        TENANT_ID,
        CAMPAIGN_ID,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-guided-intake-read",
        authorization_purpose=READ_PURPOSE,
        correlation_id="guided-intake-read-correlation",
    )

    assert evidence.intake.id == started.intake.id
    with database.tenant_transaction(TENANT_ID) as session:
        audit = session.get(AuditEvent, evidence.audit_event_id)
        assert audit is not None
        assert audit.event_type == "guided_intake.read"
        assert audit.payload["authorization_purpose"] == READ_PURPOSE
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 2
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1


def test_missing_and_cross_tenant_intake_do_not_leak_or_write_evidence(database: Database) -> None:
    service = SqlAlchemyGuidedIntakeService(database)
    with pytest.raises(GuidedIntakeNotFound):
        service.get(
            TENANT_ID,
            CAMPAIGN_ID,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-read",
            authorization_purpose=READ_PURPOSE,
            correlation_id="missing",
        )
    with pytest.raises(GuidedIntakeNotFound):
        start(database, tenant_id=TENANT_ID, campaign_id=OTHER_CAMPAIGN_ID)
    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(GuidedIntake)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0


def test_audit_failure_rolls_back_start_and_update(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_audit(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AuditScopeUnavailable("synthetic guided intake audit failure")

    monkeypatch.setattr("campaignos.onboarding.service.append_audit_event", fail_audit)
    with pytest.raises(GuidedIntakeUnavailable):
        start(database)
    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(GuidedIntake)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 0
