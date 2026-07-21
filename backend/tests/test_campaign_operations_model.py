from __future__ import annotations

from collections.abc import Iterator
from datetime import date
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
    CampaignRoadmap,
    IdempotencyRecord,
    OutboxEvent,
    Principal,
    TeamWorkspace,
    Tenant,
    WarRoomSnapshot,
)
from campaignos.operations import (
    CampaignRoadmapCreate,
    CampaignRoadmapUpdate,
    WarRoomSnapshotCreate,
)
from campaignos.operations.service import (
    CampaignRoadmapEvidenceConflict,
    CampaignRoadmapIdempotencyConflict,
    CampaignRoadmapNotFound,
    CampaignRoadmapPrerequisiteConflict,
    CampaignRoadmapUnavailable,
    CampaignRoadmapVersionConflict,
    SqlAlchemyCampaignOperationsService,
    UnavailableCampaignOperationsService,
    WarRoomSnapshotConflict,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")
OTHER_CAMPAIGN_ID = UUID("44444444-4444-4444-8444-444444444444")
PRINCIPAL_ID = UUID("55555555-5555-4555-8555-555555555555")
DIRECTOR_ID = UUID("66666666-6666-4666-8666-666666666666")
RESEARCH_ID = UUID("77777777-7777-4777-8777-777777777777")
GRANT_ID = UUID("88888888-8888-4888-8888-888888888888")
CREATE_PURPOSE = "Create campaign operations roadmap"
READ_PURPOSE = "Review campaign operations roadmap"
UPDATE_PURPOSE = "Maintain campaign operations roadmap"
SNAPSHOT_PURPOSE = "Create daily campaign war room snapshot"


@pytest.fixture
def database() -> Iterator[Database]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(
        bind=engine, class_=TenantSession, autoflush=False, expire_on_commit=False
    )
    runtime = Database(engine=engine, _sessions=sessions)
    with runtime.tenant_transaction(TENANT_ID) as session:
        session.add_all(
            [
                Tenant(id=TENANT_ID, slug="tenant", name="Tenant"),
                Tenant(id=OTHER_TENANT_ID, slug="other", name="Other"),
                Principal(
                    id=PRINCIPAL_ID,
                    issuer="https://identity.example.test/",
                    subject="operations-director",
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
                    version=5,
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
                TeamWorkspace(
                    tenant_id=TENANT_ID,
                    campaign_id=CAMPAIGN_ID,
                    organization_template="LEAN_CAMPAIGN",
                    roles=[
                        {
                            "id": str(DIRECTOR_ID),
                            "title": "Dirección",
                            "area": "Dirección",
                            "purpose": "Own human decisions.",
                            "responsibilities": ["Decide"],
                            "status": "FILLED",
                            "principal_id": str(PRINCIPAL_ID),
                            "availability_status": "AVAILABLE",
                            "weekly_capacity_hours": 40,
                            "onboarding_status": "COMPLETE",
                            "vacancy_plan": None,
                        },
                        {
                            "id": str(RESEARCH_ID),
                            "title": "Investigación",
                            "area": "Evidencia",
                            "purpose": "Maintain evidence.",
                            "responsibilities": ["Verify"],
                            "status": "FILLED",
                            "principal_id": str(uuid4()),
                            "availability_status": "LIMITED",
                            "weekly_capacity_hours": 20,
                            "onboarding_status": "COMPLETE",
                            "vacancy_plan": None,
                        },
                    ],
                    work_items=[],
                    training_requirements=[],
                    access_recommendations=[],
                    version=1,
                ),
            ]
        )
    try:
        yield runtime
    finally:
        runtime.dispose()


def _create(database: Database, key: str = "roadmap-create"):
    return SqlAlchemyCampaignOperationsService(database).create_roadmap(
        TENANT_ID,
        CAMPAIGN_ID,
        request=CampaignRoadmapCreate(title="Campaign roadmap"),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-roadmap-create",
        authorization_purpose=CREATE_PURPOSE,
        correlation_id="roadmap-create",
        idempotency_key=key,
    )


def _complete_update() -> CampaignRoadmapUpdate:
    phase = uuid4()
    workstream = uuid4()
    task_a = uuid4()
    task_b = uuid4()
    return CampaignRoadmapUpdate.model_validate(
        {
            "phases": [
                {
                    "id": phase,
                    "name": "Foundation",
                    "sequence": 1,
                    "start_date": "2026-07-21",
                    "end_date": "2026-08-15",
                    "status": "ACTIVE",
                }
            ],
            "workstreams": [
                {
                    "id": workstream,
                    "name": "Evidence",
                    "purpose": "Build verified evidence.",
                    "accountable_role_id": DIRECTOR_ID,
                    "status": "ACTIVE",
                }
            ],
            "milestones": [],
            "tasks": [
                {
                    "id": task_a,
                    "phase_id": phase,
                    "workstream_id": workstream,
                    "milestone_id": None,
                    "title": "Inventory evidence",
                    "owner_role_id": RESEARCH_ID,
                    "execution_status": "COMPLETE",
                    "dependency_ids": [],
                    "due_date": "2026-07-22",
                    "evidence_refs": [uuid4()],
                },
                {
                    "id": task_b,
                    "phase_id": phase,
                    "workstream_id": workstream,
                    "milestone_id": None,
                    "title": "Verify biography",
                    "owner_role_id": RESEARCH_ID,
                    "execution_status": "PLANNED",
                    "dependency_ids": [task_a],
                    "due_date": "2026-07-24",
                    "evidence_refs": [],
                },
            ],
            "blockers": [],
            "decisions": [
                {
                    "id": uuid4(),
                    "title": "Confirm scope",
                    "human_role_id": DIRECTOR_ID,
                    "options": ["Narrow record", "Request evidence"],
                    "due_date": "2026-07-23",
                    "status": "REQUIRED",
                    "decision": None,
                }
            ],
            "follow_up_items": [],
            "learning_notes": [],
        }
    )


def test_unavailable_service_fails_closed() -> None:
    with pytest.raises(CampaignRoadmapUnavailable):
        UnavailableCampaignOperationsService().create_roadmap(
            TENANT_ID,
            CAMPAIGN_ID,
            request=CampaignRoadmapCreate(title="Roadmap"),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose=CREATE_PURPOSE,
            correlation_id="unavailable",
            idempotency_key="unavailable",
        )


def test_create_requires_team_workspace_and_rolls_back(database: Database) -> None:
    with database.tenant_transaction(TENANT_ID) as session:
        team = session.scalar(select(TeamWorkspace))
        assert team is not None
        session.delete(team)
    with pytest.raises(CampaignRoadmapPrerequisiteConflict):
        _create(database)
    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(CampaignRoadmap)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 0


def test_create_replays_exactly_and_does_not_execute_tasks(database: Database) -> None:
    first = _create(database)
    replay = _create(database)
    assert replay == first
    assert first.roadmap.status == "SETUP_REQUIRED"
    assert first.roadmap.authority_effect == "NONE"
    assert first.roadmap.external_effects == "NONE"
    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(CampaignRoadmap)) == 1
        assert session.scalar(select(func.count()).select_from(WarRoomSnapshot)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1


def test_update_is_versioned_replayable_and_rejects_invalid_graph(database: Database) -> None:
    created = _create(database)
    service = SqlAlchemyCampaignOperationsService(database)
    changes = _complete_update()
    updated = service.update_roadmap(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=created.roadmap.version,
        changes=changes,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-roadmap-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="roadmap-update",
        idempotency_key="roadmap-update",
    )
    replay = service.update_roadmap(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=created.roadmap.version,
        changes=changes,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-roadmap-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="roadmap-update",
        idempotency_key="roadmap-update",
    )
    assert replay == updated
    assert updated.roadmap.version == 2
    assert len(updated.roadmap.ready_task_ids) == 1

    with pytest.raises(CampaignRoadmapVersionConflict):
        service.update_roadmap(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=1,
            changes=CampaignRoadmapUpdate(title="Stale"),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-roadmap-update",
            authorization_purpose=UPDATE_PURPOSE,
            correlation_id="roadmap-stale",
            idempotency_key="roadmap-stale",
        )
    with pytest.raises(CampaignRoadmapIdempotencyConflict):
        service.create_roadmap(
            TENANT_ID,
            CAMPAIGN_ID,
            request=CampaignRoadmapCreate(title="Campaign roadmap"),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=uuid4(),
            approval_receipt_id="approval-roadmap-create",
            authorization_purpose=CREATE_PURPOSE,
            correlation_id="roadmap-authority-drift",
            idempotency_key="roadmap-create",
        )

    invalid = changes.model_dump(mode="json", exclude_unset=True)
    invalid["tasks"][0]["dependency_ids"] = [invalid["tasks"][1]["id"]]
    with pytest.raises(CampaignRoadmapEvidenceConflict):
        service.update_roadmap(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=2,
            changes=CampaignRoadmapUpdate.model_validate(invalid),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-roadmap-update",
            authorization_purpose=UPDATE_PURPOSE,
            correlation_id="roadmap-cycle",
            idempotency_key="roadmap-cycle",
        )
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(CampaignRoadmap, created.roadmap.id)
        assert row is not None and row.version == 2


def test_snapshot_is_version_bound_append_only_and_exactly_replayed(database: Database) -> None:
    created = _create(database)
    service = SqlAlchemyCampaignOperationsService(database)
    updated = service.update_roadmap(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=created.roadmap.version,
        changes=_complete_update(),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-roadmap-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="roadmap-before-snapshot",
        idempotency_key="roadmap-before-snapshot",
    )
    request = WarRoomSnapshotCreate(
        snapshot_date=date(2026, 7, 22),
        priorities=["Verify biography"],
        follow_up_notes=["Human decision remains required."],
    )
    first = service.create_snapshot(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_roadmap_version=updated.roadmap.version,
        request=request,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-war-room",
        authorization_purpose=SNAPSHOT_PURPOSE,
        correlation_id="war-room",
        idempotency_key="war-room",
    )
    replay = service.create_snapshot(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_roadmap_version=updated.roadmap.version,
        request=request,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-war-room",
        authorization_purpose=SNAPSHOT_PURPOSE,
        correlation_id="war-room",
        idempotency_key="war-room",
    )
    assert replay == first
    assert first.snapshot.roadmap_version == 2
    assert first.snapshot.authority_effect == "NONE"
    with pytest.raises(WarRoomSnapshotConflict):
        service.create_snapshot(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_roadmap_version=2,
            request=WarRoomSnapshotCreate(
                snapshot_date=date(2026, 7, 22),
                priorities=["Different brief"],
                follow_up_notes=[],
            ),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-war-room",
            authorization_purpose=SNAPSHOT_PURPOSE,
            correlation_id="war-room-conflict",
            idempotency_key="war-room-conflict",
        )
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.scalar(select(WarRoomSnapshot))
        assert row is not None
        assert row.roadmap_version == 2
        assert session.scalar(select(func.count()).select_from(WarRoomSnapshot)) == 1


def test_read_is_audited_and_cross_tenant_campaign_does_not_leak(database: Database) -> None:
    created = _create(database)
    read = SqlAlchemyCampaignOperationsService(database).get_roadmap(
        TENANT_ID,
        CAMPAIGN_ID,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-roadmap-read",
        authorization_purpose=READ_PURPOSE,
        correlation_id="roadmap-read",
    )
    assert read.roadmap.id == created.roadmap.id
    with pytest.raises(CampaignRoadmapNotFound):
        SqlAlchemyCampaignOperationsService(database).get_roadmap(
            TENANT_ID,
            OTHER_CAMPAIGN_ID,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-roadmap-read",
            authorization_purpose=READ_PURPOSE,
            correlation_id="roadmap-cross-tenant",
        )


def test_audit_failure_rolls_back_roadmap_creation(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_audit(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AuditScopeUnavailable("synthetic roadmap audit failure")

    monkeypatch.setattr("campaignos.operations.service.append_audit_event", fail_audit)
    with pytest.raises(CampaignRoadmapUnavailable):
        _create(database)
    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(CampaignRoadmap)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 0
