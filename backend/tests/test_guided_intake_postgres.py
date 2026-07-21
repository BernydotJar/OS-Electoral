from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

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
    GuidedIntake,
    IdempotencyRecord,
    OutboxEvent,
    Principal,
    Tenant,
    Workspace,
)
from campaignos.onboarding import GuidedIntakeUpdate
from campaignos.onboarding.service import (
    GuidedIntakeStartEvidence,
    GuidedIntakeUpdateEvidence,
    GuidedIntakeVersionConflict,
    SqlAlchemyGuidedIntakeService,
)

START_PURPOSE = "Begin guided campaign intake"
UPDATE_PURPOSE = "Maintain guided campaign intake"


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


def _complete_update() -> GuidedIntakeUpdate:
    return GuidedIntakeUpdate(
        office="Alcaldía Municipal",
        candidate_project="Proyecto ciudadano sujeto a evidencia y revisión humana.",
        current_team=["Directora de campaña"],
        current_assets=[],
        budget_status="DOCUMENTED",
        known_unknowns=["Requisitos de inscripción"],
        evidence_requirements=["Identidad", "Biografía verificable"],
    )


@pytest.mark.postgres
def test_postgresql_guided_intake_replay_concurrency_and_tenant_isolation(
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
    role_name = "campaignos_guided_intake_test"
    role_password = f"test-{uuid4().hex}"
    with admin_engine.begin() as connection:
        connection.execute(text(f'DROP ROLE IF EXISTS "{role_name}"'))
        connection.execute(
            text(
                f"CREATE ROLE \"{role_name}\" LOGIN PASSWORD '{role_password}' "
                "NOSUPERUSER NOBYPASSRLS"
            )
        )
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
        pool_size=6,
        max_overflow=0,
    )
    tenant_id = uuid4()
    other_tenant_id = uuid4()
    principal_id = uuid4()
    campaign_id = uuid4()
    other_campaign_id = uuid4()
    workspace_id = uuid4()
    other_workspace_id = uuid4()
    grant_id = uuid4()
    try:
        with database.tenant_transaction(tenant_id) as session:
            session.add_all(
                [
                    Tenant(id=tenant_id, slug=f"tenant-{tenant_id}", name="Intake Tenant"),
                    Principal(
                        id=principal_id,
                        issuer="https://identity.example.test/",
                        subject=f"guided-intake-{principal_id}",
                    ),
                ]
            )
            session.flush()
            session.add(
                Campaign(
                    id=campaign_id,
                    tenant_id=tenant_id,
                    slug="guided-intake-campaign",
                    name="Guided Intake Campaign",
                    jurisdiction="Antigua Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=2,
                )
            )
            session.flush()
            session.add(
                Workspace(
                    id=workspace_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    slug="governance",
                    name="Governance",
                    status="ACTIVE",
                    version=1,
                )
            )
        with database.tenant_transaction(other_tenant_id) as session:
            session.add(Tenant(id=other_tenant_id, slug=f"tenant-{other_tenant_id}", name="Other"))
            session.flush()
            session.add(
                Campaign(
                    id=other_campaign_id,
                    tenant_id=other_tenant_id,
                    slug="other-guided-intake",
                    name="Other Guided Intake",
                    jurisdiction="Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=1,
                )
            )
            session.flush()
            session.add(
                Workspace(
                    id=other_workspace_id,
                    tenant_id=other_tenant_id,
                    campaign_id=other_campaign_id,
                    slug="governance",
                    name="Governance",
                    status="ACTIVE",
                    version=1,
                )
            )

        service = SqlAlchemyGuidedIntakeService(database)

        def start(
            *, tenant: object, campaign: object, key: str, correlation: str
        ) -> GuidedIntakeStartEvidence:
            return service.start(
                tenant,  # type: ignore[arg-type]
                campaign,  # type: ignore[arg-type]
                principal_id=principal_id,
                authorization_grant_id=grant_id,
                approval_receipt_id="approval-postgres-guided-intake",
                authorization_purpose=START_PURPOSE,
                correlation_id=correlation,
                idempotency_key=key,
            )

        same_key_barrier = Barrier(2)

        def start_same_key(index: int) -> GuidedIntakeStartEvidence:
            same_key_barrier.wait()
            return start(
                tenant=tenant_id,
                campaign=campaign_id,
                key="postgres-guided-intake-same-key",
                correlation=f"same-key-{index}",
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            same_key_results = list(executor.map(start_same_key, (1, 2)))

        assert same_key_results[0] == same_key_results[1]
        assert same_key_results[0].created is True
        intake_id = same_key_results[0].intake.id
        with database.tenant_transaction(tenant_id) as session:
            assert session.scalar(select(func.count()).select_from(GuidedIntake)) == 1
            assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
            assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
            assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1

        resume_barrier = Barrier(2)

        def resume_distinct_key(index: int) -> GuidedIntakeStartEvidence:
            resume_barrier.wait()
            return start(
                tenant=tenant_id,
                campaign=campaign_id,
                key=f"postgres-guided-intake-resume-{index}",
                correlation=f"resume-{index}",
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            resumes = list(executor.map(resume_distinct_key, (1, 2)))
        assert all(result.created is False for result in resumes)
        assert {result.intake.id for result in resumes} == {intake_id}
        with database.tenant_transaction(tenant_id) as session:
            assert session.scalar(select(func.count()).select_from(GuidedIntake)) == 1
            assert session.scalar(select(func.count()).select_from(AuditEvent)) == 3
            assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
            assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 3

        update_barrier = Barrier(2)

        def update(index: int) -> str:
            update_barrier.wait()
            try:
                result: GuidedIntakeUpdateEvidence = service.update(
                    tenant_id,
                    campaign_id,
                    expected_version=1,
                    changes=_complete_update().model_copy(
                        update={"office": f"Alcaldía Municipal {index}"}
                    ),
                    principal_id=principal_id,
                    authorization_grant_id=grant_id,
                    approval_receipt_id="approval-postgres-guided-intake-update",
                    authorization_purpose=UPDATE_PURPOSE,
                    correlation_id=f"update-{index}",
                    idempotency_key=f"postgres-guided-intake-update-{index}",
                )
            except GuidedIntakeVersionConflict:
                return "VERSION_CONFLICT"
            assert result.intake.status == "READY_FOR_RESEARCH"
            return "UPDATED"

        with ThreadPoolExecutor(max_workers=2) as executor:
            update_results = sorted(executor.map(update, (1, 2)))
        assert update_results == ["UPDATED", "VERSION_CONFLICT"]
        with database.tenant_transaction(tenant_id) as session:
            row = session.get(GuidedIntake, intake_id)
            assert row is not None
            assert row.version == 2
            assert row.status == "READY_FOR_RESEARCH"
            assert session.scalar(select(func.count()).select_from(AuditEvent)) == 4
            assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 2
            assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 4

        other = start(
            tenant=other_tenant_id,
            campaign=other_campaign_id,
            key="postgres-guided-intake-other-tenant",
            correlation="other-tenant",
        )
        assert other.intake.tenant_id == other_tenant_id
        with database.tenant_transaction(tenant_id) as session:
            visible = set(session.scalars(select(GuidedIntake.id)))
            assert visible == {intake_id}
            assert session.get(GuidedIntake, other.intake.id) is None
        with database.tenant_transaction(other_tenant_id) as session:
            visible = set(session.scalars(select(GuidedIntake.id)))
            assert visible == {other.intake.id}

        with pytest.raises(DBAPIError):
            with database.tenant_transaction(tenant_id) as session:
                session.add(
                    GuidedIntake(
                        id=uuid4(),
                        tenant_id=other_tenant_id,
                        campaign_id=other_campaign_id,
                        status="IN_PROGRESS",
                        budget_status="NOT_ASSESSED",
                        version=1,
                    )
                )
    finally:
        database.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP OWNED BY "{role_name}"'))
            connection.execute(text(f'DROP ROLE IF EXISTS "{role_name}"'))
        admin_engine.dispose()
