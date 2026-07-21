from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from campaignos.data import Database
from campaignos.data.models import (
    AuditEvent,
    Campaign,
    CandidateWorkspace,
    IdempotencyRecord,
    OutboxEvent,
    PermissionGrant,
    Principal,
    RoleAssignment,
    TeamWorkspace,
    Tenant,
)
from campaignos.teams import TeamWorkspaceCreate, TeamWorkspaceUpdate
from campaignos.teams.service import (
    SqlAlchemyTeamWorkspaceService,
    TeamWorkspaceConflict,
    TeamWorkspaceCreateEvidence,
    TeamWorkspaceVersionConflict,
)

CREATE_PURPOSE = "Create campaign team workspace"
UPDATE_PURPOSE = "Maintain campaign team workspace"


def _postgres_test_url() -> str:
    value = os.environ.get("CAMPAIGNOS_TEST_DATABASE_URL", "")
    if not value:
        pytest.skip("CAMPAIGNOS_TEST_DATABASE_URL is not configured")
    parsed = make_url(value)
    if parsed.drivername != "postgresql+psycopg" or not (
        parsed.database and parsed.database.endswith("_test")
    ):
        pytest.fail("PostgreSQL integration tests require an isolated *_test database")
    return value


def _drop_role(admin_engine: object, role_name: str) -> None:
    with admin_engine.begin() as connection:  # type: ignore[union-attr]
        exists = bool(
            connection.scalar(
                text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :name)"),
                {"name": role_name},
            )
        )
        if exists:
            connection.execute(text(f'DROP OWNED BY "{role_name}"'))
            connection.execute(text(f'DROP ROLE "{role_name}"'))


def _candidate(tenant_id: UUID, campaign_id: UUID) -> CandidateWorkspace:
    return CandidateWorkspace(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        candidate_id=uuid4(),
        display_name="Synthetic candidate",
        evidence=[],
        version=1,
    )


def _complete_update(campaign_id: UUID, principal_id: UUID) -> TeamWorkspaceUpdate:
    director_id = uuid4()
    researcher_id = uuid4()
    return TeamWorkspaceUpdate.model_validate(
        {
            "roles": [
                {
                    "id": director_id,
                    "title": "Campaign direction",
                    "area": "Direction",
                    "purpose": "Coordinate accountable human decisions.",
                    "responsibilities": ["Coordinate priorities"],
                    "status": "FILLED",
                    "principal_id": principal_id,
                    "availability_status": "AVAILABLE",
                    "weekly_capacity_hours": 40,
                    "onboarding_status": "COMPLETE",
                    "vacancy_plan": None,
                },
                {
                    "id": researcher_id,
                    "title": "Research",
                    "area": "Evidence",
                    "purpose": "Maintain verifiable evidence.",
                    "responsibilities": ["Validate sources"],
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
                    "name": "Initial diagnosis",
                    "description": "Organize evidence and required decisions.",
                    "status": "ACTIVE",
                    "assignments": [
                        {"role_id": director_id, "responsibility": "ACCOUNTABLE"},
                        {"role_id": researcher_id, "responsibility": "RESPONSIBLE"},
                    ],
                }
            ],
            "training_requirements": [],
            "access_recommendations": [
                {
                    "id": uuid4(),
                    "role_id": researcher_id,
                    "campaign_id": campaign_id,
                    "workspace_id": None,
                    "action": "read",
                    "resource_type": "candidate_workspace",
                    "resource_id": str(campaign_id),
                    "purpose": "Review candidate evidence workspace",
                    "status": "REVIEWED",
                    "authority_effect": "NONE",
                }
            ],
        }
    )


@pytest.mark.postgres
def test_postgresql_team_workspace_concurrency_rls_and_no_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin_url = _postgres_test_url()
    monkeypatch.setenv("CAMPAIGNOS_DATABASE_URL", admin_url)
    alembic = Config("alembic.ini")
    command.upgrade(alembic, "head")
    command.check(alembic)

    admin_engine = create_engine(admin_url)
    database_name = make_url(admin_url).database
    assert database_name is not None
    assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*_test", database_name)
    role_name = "campaignos_team_workspace_test"
    role_password = f"test-{uuid4().hex}"
    _drop_role(admin_engine, role_name)
    with admin_engine.begin() as connection:
        connection.execute(
            text(
                f"CREATE ROLE \"{role_name}\" LOGIN PASSWORD '{role_password}' "
                "NOSUPERUSER NOBYPASSRLS"
            )
        )
        role = connection.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = :role_name"),
            {"role_name": role_name},
        ).one()
        assert role == (False, False)
        connection.execute(text(f'GRANT CONNECT ON DATABASE "{database_name}" TO "{role_name}"'))
        connection.execute(text(f'GRANT USAGE ON SCHEMA public TO "{role_name}"'))
        connection.execute(
            text(
                "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public "
                f'TO "{role_name}"'
            )
        )

    application_url = make_url(admin_url).set(username=role_name, password=role_password)
    database = Database.from_url(
        application_url.render_as_string(hide_password=False),
        pool_size=8,
        max_overflow=0,
    )
    tenant_id = uuid4()
    other_tenant_id = uuid4()
    principal_id = uuid4()
    campaign_a = uuid4()
    campaign_b = uuid4()
    other_campaign = uuid4()
    grant_id = uuid4()
    try:
        with database.tenant_transaction(tenant_id) as session:
            session.add_all(
                [
                    Tenant(id=tenant_id, slug=f"tenant-{tenant_id}", name="Team Tenant"),
                    Principal(
                        id=principal_id,
                        issuer="https://identity.example.test/",
                        subject=f"team-{principal_id}",
                    ),
                ]
            )
            session.flush()
            for campaign_id, slug in ((campaign_a, "team-a"), (campaign_b, "team-b")):
                session.add(
                    Campaign(
                        id=campaign_id,
                        tenant_id=tenant_id,
                        slug=slug,
                        name=f"Campaign {slug}",
                        jurisdiction="Antigua Guatemala",
                        stage="PRECAMPAIGN",
                        status="ACTIVE",
                        version=4,
                    )
                )
                session.flush()
                session.add(_candidate(tenant_id, campaign_id))
        with database.tenant_transaction(other_tenant_id) as session:
            session.add(
                Tenant(
                    id=other_tenant_id,
                    slug=f"tenant-{other_tenant_id}",
                    name="Foreign Team Tenant",
                )
            )
            session.flush()
            session.add(
                Campaign(
                    id=other_campaign,
                    tenant_id=other_tenant_id,
                    slug="foreign-team",
                    name="Foreign Team",
                    jurisdiction="Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=1,
                )
            )
            session.flush()
            session.add(_candidate(other_tenant_id, other_campaign))

        service = SqlAlchemyTeamWorkspaceService(database)

        def create(campaign_id: UUID, key: str) -> TeamWorkspaceCreateEvidence:
            return service.create(
                tenant_id,
                campaign_id,
                request=TeamWorkspaceCreate(organization_template="LEAN_CAMPAIGN"),
                principal_id=principal_id,
                authorization_grant_id=grant_id,
                approval_receipt_id="approval-team-postgres",
                authorization_purpose=CREATE_PURPOSE,
                correlation_id=f"team-{key}",
                idempotency_key=key,
            )

        same_key_barrier = Barrier(2)

        def create_same_key(_: int) -> TeamWorkspaceCreateEvidence:
            same_key_barrier.wait()
            return create(campaign_a, "team-same-key")

        with ThreadPoolExecutor(max_workers=2) as executor:
            same_key = list(executor.map(create_same_key, (1, 2)))
        assert same_key[0] == same_key[1]
        team_a_id = same_key[0].workspace.id

        distinct_barrier = Barrier(2)

        def create_distinct(index: int) -> str:
            distinct_barrier.wait()
            try:
                create(campaign_b, f"team-distinct-{index}")
            except TeamWorkspaceConflict:
                return "CONFLICT"
            return "CREATED"

        with ThreadPoolExecutor(max_workers=2) as executor:
            distinct = sorted(executor.map(create_distinct, (1, 2)))
        assert distinct == ["CONFLICT", "CREATED"]

        changes = _complete_update(campaign_a, principal_id)
        update_barrier = Barrier(2)

        def update(index: int) -> str:
            update_barrier.wait()
            try:
                service.update(
                    tenant_id,
                    campaign_a,
                    expected_version=1,
                    changes=changes,
                    principal_id=principal_id,
                    authorization_grant_id=grant_id,
                    approval_receipt_id="approval-team-update",
                    authorization_purpose=UPDATE_PURPOSE,
                    correlation_id=f"team-update-{index}",
                    idempotency_key=f"team-update-{index}",
                )
            except TeamWorkspaceVersionConflict:
                return "VERSION_CONFLICT"
            return "UPDATED"

        with ThreadPoolExecutor(max_workers=2) as executor:
            updates = sorted(executor.map(update, (1, 2)))
        assert updates == ["UPDATED", "VERSION_CONFLICT"]

        other = service.create(
            other_tenant_id,
            other_campaign,
            request=TeamWorkspaceCreate(organization_template="LEAN_CAMPAIGN"),
            principal_id=principal_id,
            authorization_grant_id=grant_id,
            approval_receipt_id="approval-team-postgres",
            authorization_purpose=CREATE_PURPOSE,
            correlation_id="team-other-tenant",
            idempotency_key="team-other-tenant",
        )
        with database.tenant_transaction(tenant_id) as session:
            visible = set(session.scalars(select(TeamWorkspace.id)))
            assert team_a_id in visible
            assert other.workspace.id not in visible
            assert session.get(TeamWorkspace, other.workspace.id) is None
            assert session.scalar(select(func.count()).select_from(RoleAssignment)) == 0
            assert session.scalar(select(func.count()).select_from(PermissionGrant)) == 0
        with database.tenant_transaction(other_tenant_id) as session:
            assert set(session.scalars(select(TeamWorkspace.id))) == {other.workspace.id}

        with pytest.raises(DBAPIError):
            with database.tenant_transaction(tenant_id) as session:
                session.add(
                    TeamWorkspace(
                        tenant_id=other_tenant_id,
                        campaign_id=other_campaign,
                        organization_template="LEAN_CAMPAIGN",
                        roles=None,
                        work_items=None,
                        training_requirements=None,
                        access_recommendations=None,
                        version=1,
                    )
                )

        with database.tenant_transaction(tenant_id) as session:
            assert session.scalar(select(func.count()).select_from(TeamWorkspace)) == 2
            assert session.scalar(select(func.count()).select_from(AuditEvent)) == 3
            assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 3
            assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 3
    finally:
        database.dispose()
        _drop_role(admin_engine, role_name)
        admin_engine.dispose()
