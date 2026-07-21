from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
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
    CandidateWorkspace,
    IdempotencyRecord,
    OutboxEvent,
    PermissionGrant,
    Principal,
    RoleAssignment,
    TeamWorkspace,
    Tenant,
    Workspace,
)
from campaignos.teams import TeamWorkspaceCreate, TeamWorkspaceUpdate
from campaignos.teams.service import (
    SqlAlchemyTeamWorkspaceService,
    TeamWorkspaceEvidenceConflict,
    TeamWorkspaceIdempotencyConflict,
    TeamWorkspaceNotFound,
    TeamWorkspacePrerequisiteConflict,
    TeamWorkspaceUnavailable,
    TeamWorkspaceVersionConflict,
    UnavailableTeamWorkspaceService,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")
OTHER_CAMPAIGN_ID = UUID("44444444-4444-4444-8444-444444444444")
PRINCIPAL_ID = UUID("55555555-5555-4555-8555-555555555555")
GRANT_ID = UUID("66666666-6666-4666-8666-666666666666")
CREATE_PURPOSE = "Create campaign team workspace"
READ_PURPOSE = "Review campaign team workspace"
UPDATE_PURPOSE = "Maintain campaign team workspace"


@pytest.fixture
def database() -> Iterator[Database]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(
        bind=engine, class_=TenantSession, autoflush=False, expire_on_commit=False
    )
    runtime = Database(engine=engine, _sessions=sessions)
    now = datetime(2026, 7, 21, 23, 15, tzinfo=UTC)
    with runtime.tenant_transaction(TENANT_ID) as session:
        session.add_all(
            [
                Tenant(id=TENANT_ID, slug="tenant", name="Tenant", status="ACTIVE"),
                Tenant(id=OTHER_TENANT_ID, slug="other", name="Other", status="ACTIVE"),
                Principal(
                    id=PRINCIPAL_ID,
                    issuer="https://identity.example.test/",
                    subject="team-operator",
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
                    version=4,
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
        session.add_all(
            [
                CandidateWorkspace(
                    tenant_id=TENANT_ID,
                    campaign_id=CAMPAIGN_ID,
                    candidate_id=uuid4(),
                    display_name="Candidatura sintética",
                    evidence=[],
                    version=1,
                    created_at=now,
                    updated_at=now,
                ),
                Workspace(
                    tenant_id=TENANT_ID,
                    campaign_id=CAMPAIGN_ID,
                    slug="team-local",
                    name="Team Local",
                    status="ACTIVE",
                    version=1,
                ),
                Workspace(
                    tenant_id=OTHER_TENANT_ID,
                    campaign_id=OTHER_CAMPAIGN_ID,
                    slug="team-foreign",
                    name="Team Foreign",
                    status="ACTIVE",
                    version=1,
                ),
            ]
        )
    try:
        yield runtime
    finally:
        runtime.dispose()


def _create(database: Database, *, key: str = "team-create-1"):
    return SqlAlchemyTeamWorkspaceService(database).create(
        TENANT_ID,
        CAMPAIGN_ID,
        request=TeamWorkspaceCreate(organization_template="LEAN_CAMPAIGN"),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-team-create",
        authorization_purpose=CREATE_PURPOSE,
        correlation_id="team-create-correlation",
        idempotency_key=key,
    )


def _complete_update() -> TeamWorkspaceUpdate:
    director = uuid4()
    researcher = uuid4()
    return TeamWorkspaceUpdate.model_validate(
        {
            "roles": [
                {
                    "id": director,
                    "title": "Dirección de campaña",
                    "area": "Dirección",
                    "purpose": "Coordinar accountability y decisiones humanas.",
                    "responsibilities": ["Coordinar prioridades"],
                    "status": "FILLED",
                    "principal_id": PRINCIPAL_ID,
                    "availability_status": "AVAILABLE",
                    "weekly_capacity_hours": 40,
                    "onboarding_status": "COMPLETE",
                    "vacancy_plan": None,
                },
                {
                    "id": researcher,
                    "title": "Investigación",
                    "area": "Evidencia",
                    "purpose": "Mantener evidencia verificable.",
                    "responsibilities": ["Validar fuentes"],
                    "status": "FILLED",
                    "principal_id": uuid4(),
                    "availability_status": "LIMITED",
                    "weekly_capacity_hours": 20,
                    "onboarding_status": "COMPLETE",
                    "vacancy_plan": None,
                },
            ],
            "work_items": [
                {
                    "id": uuid4(),
                    "name": "Diagnóstico inicial",
                    "description": "Organizar evidencia y decisiones requeridas.",
                    "status": "ACTIVE",
                    "assignments": [
                        {"role_id": director, "responsibility": "ACCOUNTABLE"},
                        {"role_id": researcher, "responsibility": "RESPONSIBLE"},
                    ],
                }
            ],
            "training_requirements": [],
            "access_recommendations": [
                {
                    "id": uuid4(),
                    "role_id": researcher,
                    "campaign_id": CAMPAIGN_ID,
                    "workspace_id": None,
                    "action": "read",
                    "resource_type": "candidate_workspace",
                    "resource_id": str(CAMPAIGN_ID),
                    "purpose": "Review candidate evidence workspace",
                    "status": "REVIEWED",
                    "authority_effect": "NONE",
                }
            ],
        }
    )


def test_unavailable_team_service_fails_closed() -> None:
    with pytest.raises(TeamWorkspaceUnavailable):
        UnavailableTeamWorkspaceService().create(
            TENANT_ID,
            CAMPAIGN_ID,
            request=TeamWorkspaceCreate(organization_template="LEAN_CAMPAIGN"),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose=CREATE_PURPOSE,
            correlation_id="unavailable",
            idempotency_key="unavailable",
        )


def test_create_requires_candidate_workspace_and_rolls_back(database: Database) -> None:
    with database.tenant_transaction(TENANT_ID) as session:
        candidate = session.scalar(select(CandidateWorkspace))
        assert candidate is not None
        session.delete(candidate)

    with pytest.raises(TeamWorkspacePrerequisiteConflict):
        _create(database)

    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(TeamWorkspace)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 0


def test_create_replays_exactly_without_creating_authority(database: Database) -> None:
    created = _create(database)
    replay = _create(database)
    assert replay == created
    assert created.workspace.status == "SETUP_REQUIRED"
    assert created.workspace.authority_effect == "NONE"
    assert created.workspace.external_effects == "NONE"

    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(TeamWorkspace)) == 1
        assert session.scalar(select(func.count()).select_from(RoleAssignment)) == 0
        assert session.scalar(select(func.count()).select_from(PermissionGrant)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1


def test_update_is_versioned_and_replay_is_authority_bound(database: Database) -> None:
    _create(database)
    service = SqlAlchemyTeamWorkspaceService(database)
    changes = _complete_update()
    updated = service.update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=1,
        changes=changes,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-team-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="team-update",
        idempotency_key="team-update-1",
    )
    replay = service.update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=1,
        changes=changes,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-team-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="team-update",
        idempotency_key="team-update-1",
    )
    assert replay == updated
    assert updated.workspace.version == 2
    assert updated.workspace.status == "READY_FOR_HUMAN_REVIEW"

    with pytest.raises(TeamWorkspaceVersionConflict):
        service.update(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=1,
            changes=TeamWorkspaceUpdate(organization_template="FULL_CAMPAIGN"),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-team-update",
            authorization_purpose=UPDATE_PURPOSE,
            correlation_id="team-stale",
            idempotency_key="team-stale",
        )
    with pytest.raises(TeamWorkspaceIdempotencyConflict):
        service.create(
            TENANT_ID,
            CAMPAIGN_ID,
            request=TeamWorkspaceCreate(organization_template="LEAN_CAMPAIGN"),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=uuid4(),
            approval_receipt_id="approval-team-create",
            authorization_purpose=CREATE_PURPOSE,
            correlation_id="team-authority-drift",
            idempotency_key="team-create-1",
        )


def test_invalid_update_rolls_back_version_audit_outbox_and_replay(database: Database) -> None:
    created = _create(database)
    invalid = _complete_update().model_dump(mode="json", exclude_unset=True)
    invalid["work_items"][0]["assignments"] = [invalid["work_items"][0]["assignments"][0]]
    changes = TeamWorkspaceUpdate.model_validate(invalid)
    service = SqlAlchemyTeamWorkspaceService(database)
    with pytest.raises(TeamWorkspaceEvidenceConflict):
        service.update(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=1,
            changes=changes,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-team-update",
            authorization_purpose=UPDATE_PURPOSE,
            correlation_id="team-invalid",
            idempotency_key="team-invalid",
        )
    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(TeamWorkspace, created.workspace.id)
        assert row is not None and row.version == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1


def test_workspace_scoped_access_recommendation_must_belong_to_campaign(
    database: Database,
) -> None:
    created = _create(database)
    with database.tenant_transaction(TENANT_ID) as session:
        foreign_workspace = session.scalar(
            select(Workspace).where(Workspace.campaign_id == OTHER_CAMPAIGN_ID)
        )
        assert foreign_workspace is not None
    changes = _complete_update().model_dump(mode="json", exclude_unset=True)
    recommendation = changes["access_recommendations"][0]
    recommendation["workspace_id"] = str(foreign_workspace.id)
    recommendation["resource_id"] = str(foreign_workspace.id)
    with pytest.raises(TeamWorkspaceEvidenceConflict):
        SqlAlchemyTeamWorkspaceService(database).update(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=created.workspace.version,
            changes=TeamWorkspaceUpdate.model_validate(changes),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-team-update",
            authorization_purpose=UPDATE_PURPOSE,
            correlation_id="team-cross-campaign-workspace",
            idempotency_key="team-cross-campaign-workspace",
        )


def test_read_is_audited_and_cross_tenant_campaign_does_not_leak(database: Database) -> None:
    created = _create(database)
    service = SqlAlchemyTeamWorkspaceService(database)
    read = service.get(
        TENANT_ID,
        CAMPAIGN_ID,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-team-read",
        authorization_purpose=READ_PURPOSE,
        correlation_id="team-read",
    )
    assert read.workspace.id == created.workspace.id
    with pytest.raises(TeamWorkspaceNotFound):
        service.get(
            TENANT_ID,
            OTHER_CAMPAIGN_ID,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-team-read",
            authorization_purpose=READ_PURPOSE,
            correlation_id="team-cross-tenant",
        )


def test_audit_failure_rolls_back_team_creation(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_audit(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AuditScopeUnavailable("synthetic team audit failure")

    monkeypatch.setattr("campaignos.teams.service.append_audit_event", fail_audit)
    with pytest.raises(TeamWorkspaceUnavailable):
        _create(database)
    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(TeamWorkspace)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 0
