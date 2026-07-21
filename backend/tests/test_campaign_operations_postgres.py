from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import date
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
    CampaignRoadmapConflict,
    CampaignRoadmapVersionConflict,
    SqlAlchemyCampaignOperationsService,
    WarRoomSnapshotConflict,
)

CREATE_PURPOSE = "Create campaign operations roadmap"
UPDATE_PURPOSE = "Maintain campaign operations roadmap"
SNAPSHOT_PURPOSE = "Create daily campaign war room snapshot"


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


def _drop_role(engine: object, role_name: str) -> None:
    with engine.begin() as connection:  # type: ignore[union-attr]
        exists = bool(
            connection.scalar(
                text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :name)"),
                {"name": role_name},
            )
        )
        if exists:
            connection.execute(text(f'DROP OWNED BY "{role_name}"'))
            connection.execute(text(f'DROP ROLE "{role_name}"'))


def _team(
    tenant_id: UUID, campaign_id: UUID, director_id: UUID, principal_id: UUID
) -> TeamWorkspace:
    return TeamWorkspace(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        organization_template="LEAN_CAMPAIGN",
        roles=[
            {
                "id": str(director_id),
                "title": "Campaign direction",
                "area": "Direction",
                "purpose": "Own accountable human decisions.",
                "responsibilities": ["Decide"],
                "status": "FILLED",
                "principal_id": str(principal_id),
                "availability_status": "AVAILABLE",
                "weekly_capacity_hours": 40,
                "onboarding_status": "COMPLETE",
                "vacancy_plan": None,
            }
        ],
        work_items=[],
        training_requirements=[],
        access_recommendations=[],
        version=1,
    )


def _update(director_id: UUID) -> CampaignRoadmapUpdate:
    phase_id = uuid4()
    workstream_id = uuid4()
    first_id = uuid4()
    second_id = uuid4()
    return CampaignRoadmapUpdate.model_validate(
        {
            "phases": [
                {
                    "id": phase_id,
                    "name": "Foundation",
                    "sequence": 1,
                    "start_date": "2026-07-21",
                    "end_date": "2026-08-15",
                    "status": "ACTIVE",
                }
            ],
            "workstreams": [
                {
                    "id": workstream_id,
                    "name": "Evidence",
                    "purpose": "Build verified evidence.",
                    "accountable_role_id": director_id,
                    "status": "ACTIVE",
                }
            ],
            "milestones": [],
            "tasks": [
                {
                    "id": first_id,
                    "phase_id": phase_id,
                    "workstream_id": workstream_id,
                    "milestone_id": None,
                    "title": "Inventory evidence",
                    "owner_role_id": director_id,
                    "execution_status": "COMPLETE",
                    "dependency_ids": [],
                    "due_date": "2026-07-22",
                    "evidence_refs": [uuid4()],
                },
                {
                    "id": second_id,
                    "phase_id": phase_id,
                    "workstream_id": workstream_id,
                    "milestone_id": None,
                    "title": "Verify evidence",
                    "owner_role_id": director_id,
                    "execution_status": "PLANNED",
                    "dependency_ids": [first_id],
                    "due_date": "2026-07-24",
                    "evidence_refs": [],
                },
            ],
            "blockers": [],
            "decisions": [],
            "follow_up_items": [],
            "learning_notes": [],
        }
    )


@pytest.mark.postgres
def test_postgresql_campaign_operations_concurrency_rls_and_immutable_snapshots(
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
    role_name = "campaignos_operations_test"
    role_password = f"test-{uuid4().hex}"
    _drop_role(admin_engine, role_name)
    with admin_engine.begin() as connection:
        connection.execute(
            text(
                f"CREATE ROLE \"{role_name}\" LOGIN PASSWORD '{role_password}' "
                "NOSUPERUSER NOBYPASSRLS"
            )
        )
        assert connection.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = :name"),
            {"name": role_name},
        ).one() == (False, False)
        connection.execute(text(f'GRANT CONNECT ON DATABASE "{database_name}" TO "{role_name}"'))
        connection.execute(text(f'GRANT USAGE ON SCHEMA public TO "{role_name}"'))
        connection.execute(
            text(
                "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public "
                f'TO "{role_name}"'
            )
        )

    app_url = make_url(admin_url).set(username=role_name, password=role_password)
    database = Database.from_url(
        app_url.render_as_string(hide_password=False), pool_size=8, max_overflow=0
    )
    tenant_id = uuid4()
    other_tenant_id = uuid4()
    principal_id = uuid4()
    director_id = uuid4()
    campaign_a = uuid4()
    campaign_b = uuid4()
    other_campaign = uuid4()
    grant_id = uuid4()
    try:
        with database.tenant_transaction(tenant_id) as session:
            session.add_all(
                [
                    Tenant(id=tenant_id, slug=f"tenant-{tenant_id}", name="Operations Tenant"),
                    Principal(
                        id=principal_id,
                        issuer="https://identity.example.test/",
                        subject=f"operations-{principal_id}",
                    ),
                ]
            )
            session.flush()
            for campaign_id, slug in ((campaign_a, "operations-a"), (campaign_b, "operations-b")):
                session.add(
                    Campaign(
                        id=campaign_id,
                        tenant_id=tenant_id,
                        slug=slug,
                        name=f"Campaign {slug}",
                        jurisdiction="Antigua Guatemala",
                        stage="PRECAMPAIGN",
                        status="ACTIVE",
                        version=5,
                    )
                )
                session.flush()
                session.add(_team(tenant_id, campaign_id, director_id, principal_id))
        with database.tenant_transaction(other_tenant_id) as session:
            session.add(
                Tenant(
                    id=other_tenant_id,
                    slug=f"tenant-{other_tenant_id}",
                    name="Foreign Operations Tenant",
                )
            )
            session.flush()
            session.add(
                Campaign(
                    id=other_campaign,
                    tenant_id=other_tenant_id,
                    slug="foreign-operations",
                    name="Foreign Operations",
                    jurisdiction="Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=1,
                )
            )
            session.flush()
            session.add(_team(other_tenant_id, other_campaign, uuid4(), principal_id))

        service = SqlAlchemyCampaignOperationsService(database)

        def create(campaign_id: UUID, key: str):
            return service.create_roadmap(
                tenant_id,
                campaign_id,
                request=CampaignRoadmapCreate(title="Campaign operations roadmap"),
                principal_id=principal_id,
                authorization_grant_id=grant_id,
                approval_receipt_id="approval-operations",
                authorization_purpose=CREATE_PURPOSE,
                correlation_id=key,
                idempotency_key=key,
            )

        same_key_barrier = Barrier(2)

        def same_key(_: int):
            same_key_barrier.wait()
            return create(campaign_a, "operations-same-key")

        with ThreadPoolExecutor(max_workers=2) as executor:
            replays = list(executor.map(same_key, (1, 2)))
        assert replays[0] == replays[1]
        roadmap_id = replays[0].roadmap.id

        distinct_barrier = Barrier(2)

        def distinct(index: int) -> str:
            distinct_barrier.wait()
            try:
                create(campaign_b, f"operations-distinct-{index}")
            except CampaignRoadmapConflict:
                return "CONFLICT"
            return "CREATED"

        with ThreadPoolExecutor(max_workers=2) as executor:
            assert sorted(executor.map(distinct, (1, 2))) == ["CONFLICT", "CREATED"]

        changes = _update(director_id)
        update_barrier = Barrier(2)

        def update(index: int) -> str:
            update_barrier.wait()
            try:
                service.update_roadmap(
                    tenant_id,
                    campaign_a,
                    expected_version=1,
                    changes=changes,
                    principal_id=principal_id,
                    authorization_grant_id=grant_id,
                    approval_receipt_id="approval-update",
                    authorization_purpose=UPDATE_PURPOSE,
                    correlation_id=f"update-{index}",
                    idempotency_key=f"update-{index}",
                )
            except CampaignRoadmapVersionConflict:
                return "VERSION_CONFLICT"
            return "UPDATED"

        with ThreadPoolExecutor(max_workers=2) as executor:
            assert sorted(executor.map(update, (1, 2))) == ["UPDATED", "VERSION_CONFLICT"]

        snapshot_barrier = Barrier(2)

        def snapshot(index: int) -> str:
            snapshot_barrier.wait()
            try:
                service.create_snapshot(
                    tenant_id,
                    campaign_a,
                    expected_roadmap_version=2,
                    request=WarRoomSnapshotCreate(
                        snapshot_date=date(2026, 7, 22),
                        priorities=[f"Priority {index}"],
                        follow_up_notes=[],
                    ),
                    principal_id=principal_id,
                    authorization_grant_id=grant_id,
                    approval_receipt_id="approval-snapshot",
                    authorization_purpose=SNAPSHOT_PURPOSE,
                    correlation_id=f"snapshot-{index}",
                    idempotency_key=f"snapshot-{index}",
                )
            except WarRoomSnapshotConflict:
                return "CONFLICT"
            return "CREATED"

        with ThreadPoolExecutor(max_workers=2) as executor:
            assert sorted(executor.map(snapshot, (1, 2))) == ["CONFLICT", "CREATED"]

        foreign = service.create_roadmap(
            other_tenant_id,
            other_campaign,
            request=CampaignRoadmapCreate(title="Foreign roadmap"),
            principal_id=principal_id,
            authorization_grant_id=grant_id,
            approval_receipt_id="approval-foreign",
            authorization_purpose=CREATE_PURPOSE,
            correlation_id="foreign",
            idempotency_key="foreign",
        )
        with database.tenant_transaction(tenant_id) as session:
            visible = set(session.scalars(select(CampaignRoadmap.id)))
            assert roadmap_id in visible
            assert foreign.roadmap.id not in visible
            assert session.get(CampaignRoadmap, foreign.roadmap.id) is None
            assert session.scalar(select(func.count()).select_from(WarRoomSnapshot)) == 1
        with database.tenant_transaction(other_tenant_id) as session:
            assert set(session.scalars(select(CampaignRoadmap.id))) == {foreign.roadmap.id}

        with pytest.raises(DBAPIError):
            with database.tenant_transaction(tenant_id) as session:
                session.add(
                    CampaignRoadmap(
                        tenant_id=other_tenant_id,
                        campaign_id=other_campaign,
                        title="Cross-tenant roadmap",
                        phases=None,
                        workstreams=None,
                        milestones=None,
                        tasks=None,
                        blockers=None,
                        decisions=None,
                        follow_up_items=None,
                        learning_notes=None,
                        version=1,
                    )
                )

        with database.tenant_transaction(tenant_id) as session:
            assert session.scalar(select(func.count()).select_from(CampaignRoadmap)) == 2
            assert session.scalar(select(func.count()).select_from(WarRoomSnapshot)) == 1
            assert session.scalar(select(func.count()).select_from(AuditEvent)) == 4
            assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 4
            assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 4
    finally:
        database.dispose()
        _drop_role(admin_engine, role_name)
        admin_engine.dispose()
