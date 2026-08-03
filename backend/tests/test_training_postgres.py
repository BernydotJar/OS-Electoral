from __future__ import annotations

# ruff: noqa: E501
import os
import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select, text, update
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import DBAPIError

from campaignos.data import Database
from campaignos.data.models import TrainingAssignment, TrainingCompletionReceipt
from campaignos.training.catalog import CATALOG_DIGEST, module_by_ref
from campaignos.training.contracts import (
    TrainingAnswerSubmission,
    TrainingAssignmentCreate,
    TrainingAttemptRequest,
    TrainingModuleStartRequest,
)
from campaignos.training.service import SqlAlchemyTrainingService

GRANT_ID = UUID("66666666-6666-4666-8666-666666666666")


def postgres_test_url() -> str:
    value = os.environ.get("CAMPAIGNOS_TEST_DATABASE_URL", "")
    if not value:
        pytest.skip("CAMPAIGNOS_TEST_DATABASE_URL is not configured")
    parsed = make_url(value)
    if parsed.drivername != "postgresql+psycopg" or not (
        parsed.database and parsed.database.endswith("_test")
    ):
        pytest.fail("PostgreSQL integration tests require an isolated *_test database")
    return value


def drop_role(engine: Engine, role_name: str) -> None:
    with engine.begin() as connection:
        exists = bool(
            connection.scalar(
                text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :name)"),
                {"name": role_name},
            )
        )
        if exists:
            connection.execute(text(f'DROP OWNED BY "{role_name}"'))
            connection.execute(text(f'DROP ROLE "{role_name}"'))


@pytest.mark.postgres
def test_training_rls_completion_and_append_only_receipt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin_url = postgres_test_url()
    monkeypatch.setenv("CAMPAIGNOS_DATABASE_URL", admin_url)
    alembic = Config("alembic.ini")
    command.upgrade(alembic, "head")
    command.check(alembic)

    admin_engine = create_engine(admin_url)
    database_name = make_url(admin_url).database
    assert database_name is not None
    assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*_test", database_name)
    role_name = f"campaignos_training_{uuid4().hex[:12]}"
    role_password = f"test-{uuid4().hex}"
    tenant_a, tenant_b = uuid4(), uuid4()
    campaign_a, campaign_b = uuid4(), uuid4()
    manager_id, learner_id = uuid4(), uuid4()
    now = datetime.now(UTC)
    drop_role(admin_engine, role_name)

    with admin_engine.begin() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "20260801_0013"
        )
        policies = set(
            connection.execute(
                text(
                    "SELECT tablename FROM pg_policies "
                    "WHERE schemaname = 'public' AND policyname = 'tenant_isolation' "
                    "AND tablename LIKE 'training_%'"
                )
            ).scalars()
        )
        assert policies == {
            "training_assignments",
            "training_module_progress",
            "training_completion_receipts",
        }
        force_rows = {
            row.relname: (row.relrowsecurity, row.relforcerowsecurity)
            for row in connection.execute(
                text(
                    "SELECT relname, relrowsecurity, relforcerowsecurity "
                    "FROM pg_class JOIN pg_namespace ON pg_namespace.oid = pg_class.relnamespace "
                    "WHERE pg_namespace.nspname = 'public' AND relkind = 'r' "
                    "AND relname LIKE 'training_%'"
                )
            )
        }
        assert force_rows == {
            "training_assignments": (True, True),
            "training_module_progress": (True, True),
            "training_completion_receipts": (True, True),
        }
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
        connection.execute(
            text(
                "INSERT INTO tenants (id, slug, name, status, version) VALUES "
                "(:tenant_a, :slug_a, 'Training A', 'ACTIVE', 1), "
                "(:tenant_b, :slug_b, 'Training B', 'ACTIVE', 1)"
            ),
            {
                "tenant_a": tenant_a,
                "tenant_b": tenant_b,
                "slug_a": f"training-{tenant_a}",
                "slug_b": f"training-{tenant_b}",
            },
        )
        connection.execute(
            text(
                "INSERT INTO principals (id, issuer, subject, created_at) VALUES "
                "(:manager, 'https://identity.example.test/', :manager_subject, :now), "
                "(:learner, 'https://identity.example.test/', :learner_subject, :now)"
            ),
            {
                "manager": manager_id,
                "learner": learner_id,
                "manager_subject": f"manager-{manager_id}",
                "learner_subject": f"learner-{learner_id}",
                "now": now,
            },
        )
        connection.execute(
            text(
                "INSERT INTO campaigns "
                "(id, tenant_id, slug, name, jurisdiction, stage, status, version, created_at, updated_at) "
                "VALUES "
                "(:campaign_a, :tenant_a, 'training-a', 'Training A', 'Test', 'TEST', 'ACTIVE', 1, :now, :now), "
                "(:campaign_b, :tenant_b, 'training-b', 'Training B', 'Test', 'TEST', 'ACTIVE', 1, :now, :now)"
            ),
            {
                "campaign_a": campaign_a,
                "campaign_b": campaign_b,
                "tenant_a": tenant_a,
                "tenant_b": tenant_b,
                "now": now,
            },
        )
        connection.execute(
            text(
                "INSERT INTO memberships "
                "(id, tenant_id, principal_id, campaign_id, status, valid_from, version, created_at, updated_at) "
                "VALUES (:id, :tenant, :principal, :campaign, 'ACTIVE', :now, 1, :now, :now)"
            ),
            {
                "id": uuid4(),
                "tenant": tenant_a,
                "principal": learner_id,
                "campaign": campaign_a,
                "now": now,
            },
        )

    application_url = make_url(admin_url).set(username=role_name, password=role_password)
    database = Database.from_url(application_url.render_as_string(hide_password=False))
    service = SqlAlchemyTrainingService(database)
    try:
        created = service.create_assignment(
            tenant_a,
            campaign_a,
            request=TrainingAssignmentCreate(
                principal_id=learner_id,
                path_id="research_foundations_path",
                path_version="1.0.0",
                catalog_digest=CATALOG_DIGEST,
                role_slug="electoral_research",
            ),
            principal_id=manager_id,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="training-postgres-manage",
            authorization_purpose="Assign campaign learning path",
            correlation_id="training-postgres-create",
            idempotency_key=f"create-{uuid4()}",
        )
        progress = created.assignment.modules[0]
        started = service.start_module(
            tenant_a,
            campaign_a,
            created.assignment.id,
            progress.module_id,
            request=TrainingModuleStartRequest(
                expected_assignment_version=1,
                expected_progress_version=1,
                catalog_digest=CATALOG_DIGEST,
            ),
            principal_id=learner_id,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="training-postgres-self",
            authorization_purpose="Complete assigned campaign training",
            correlation_id="training-postgres-start",
            idempotency_key=f"start-{uuid4()}",
        )
        module = module_by_ref(progress.module_id, progress.module_version)
        answers = tuple(
            TrainingAnswerSubmission(
                question_id=question.id,
                option_ids=question.correct_option_ids,
            )
            for question in module.localized("es").questions
        )
        completed = service.submit_attempt(
            tenant_a,
            campaign_a,
            created.assignment.id,
            progress.module_id,
            request=TrainingAttemptRequest(
                locale="es",
                expected_assignment_version=started.assignment.version,
                expected_progress_version=started.assignment.modules[0].version,
                catalog_digest=CATALOG_DIGEST,
                answers=answers,
            ),
            principal_id=learner_id,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="training-postgres-self",
            authorization_purpose="Complete assigned campaign training",
            correlation_id="training-postgres-attempt",
            idempotency_key=f"attempt-{uuid4()}",
        )
        assert completed.assignment.status == "COMPLETED"
        assert completed.receipt is not None
        receipt_id = completed.receipt.id

        with database.tenant_transaction(tenant_b) as session:
            assert (
                session.scalar(
                    select(TrainingAssignment.id).where(
                        TrainingAssignment.id == created.assignment.id
                    )
                )
                is None
            )

        with pytest.raises(DBAPIError) as update_error:
            with database.tenant_transaction(tenant_a) as session:
                session.execute(
                    update(TrainingCompletionReceipt)
                    .where(TrainingCompletionReceipt.id == receipt_id)
                    .values(catalog_digest="0" * 64)
                )
        assert getattr(update_error.value.orig, "sqlstate", None) == "42501"

        with pytest.raises(DBAPIError) as delete_error:
            with database.tenant_transaction(tenant_a) as session:
                receipt = session.get(TrainingCompletionReceipt, receipt_id)
                assert receipt is not None
                session.delete(receipt)
                session.flush()
        assert getattr(delete_error.value.orig, "sqlstate", None) == "42501"
    finally:
        database.dispose()
        drop_role(admin_engine, role_name)
        admin_engine.dispose()
