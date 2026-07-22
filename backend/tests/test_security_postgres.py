from __future__ import annotations

import os
import re
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, select, text, update
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import DBAPIError

from campaignos.data import Database
from campaignos.data.models import AuditEvent, Campaign, Principal, Tenant

APPEND_ONLY_TABLES = {
    "audit_events",
    "idempotency_records",
    "candidate_section_approvals",
    "war_room_snapshots",
    "strategy_decision_receipts",
    "agent_runs",
}
TRIGGER_NAME = "campaignos_append_only_guard"
FUNCTION_NAME = "campaignos_reject_append_only_mutation"


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
def test_append_only_guards_deny_constrained_role_mutation(
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
    role_name = f"campaignos_security_{uuid4().hex[:12]}"
    role_password = f"test-{uuid4().hex}"
    drop_role(admin_engine, role_name)

    with admin_engine.begin() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "20260721_0011"
        )
        trigger_rows = set(
            connection.execute(
                text(
                    "SELECT relation.relname, trigger.tgenabled "
                    "FROM pg_catalog.pg_trigger AS trigger "
                    "JOIN pg_catalog.pg_class AS relation ON relation.oid = trigger.tgrelid "
                    "JOIN pg_catalog.pg_namespace AS namespace "
                    "ON namespace.oid = relation.relnamespace "
                    "WHERE namespace.nspname = 'public' "
                    "AND trigger.tgname = :trigger_name "
                    "AND NOT trigger.tgisinternal"
                ),
                {"trigger_name": TRIGGER_NAME},
            )
        )
        assert trigger_rows == {(table, "O") for table in APPEND_ONLY_TABLES}
        function_security = connection.execute(
            text(
                "SELECT routine.prosecdef, routine.proconfig, routine.proacl, "
                "pg_catalog.has_function_privilege('public', routine.oid, 'EXECUTE') "
                "AS public_execute "
                "FROM pg_catalog.pg_proc AS routine "
                "JOIN pg_catalog.pg_namespace AS namespace "
                "ON namespace.oid = routine.pronamespace "
                "WHERE namespace.nspname = 'public' AND routine.proname = :name"
            ),
            {"name": FUNCTION_NAME},
        ).one()
        assert function_security.prosecdef is True
        assert function_security.proconfig == ["search_path=pg_catalog"]
        assert function_security.proacl is not None
        assert function_security.public_execute is False

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

    application_url = make_url(admin_url).set(
        username=role_name,
        password=role_password,
    )
    database = Database.from_url(application_url.render_as_string(hide_password=False))
    tenant_id = uuid4()
    principal_id = uuid4()
    campaign_id = uuid4()
    event_id = uuid4()
    try:
        with database.tenant_transaction(tenant_id) as session:
            session.add_all(
                [
                    Tenant(
                        id=tenant_id,
                        slug=f"security-{tenant_id}",
                        name="Security tenant",
                    ),
                    Principal(
                        id=principal_id,
                        issuer="https://identity.example.test/",
                        subject=f"security-{principal_id}",
                    ),
                ]
            )
            session.flush()
            session.add(
                Campaign(
                    id=campaign_id,
                    tenant_id=tenant_id,
                    slug="security-campaign",
                    name="Security Campaign",
                    jurisdiction="Test",
                    stage="TEST",
                )
            )
            session.flush()
            session.add(
                AuditEvent(
                    id=event_id,
                    tenant_id=tenant_id,
                    campaign_id=campaign_id,
                    principal_id=principal_id,
                    event_type="security.append_only_tested",
                    resource_type="campaign",
                    resource_id=str(campaign_id),
                    payload={"state": "original"},
                    previous_hash="GENESIS",
                    event_hash=uuid4().hex + uuid4().hex,
                )
            )

        with pytest.raises(DBAPIError) as update_error:
            with database.tenant_transaction(tenant_id) as session:
                session.execute(text("SET LOCAL campaignos.audit_maintenance = 'authorized'"))
                session.execute(
                    update(AuditEvent)
                    .where(AuditEvent.id == event_id)
                    .values(payload={"state": "tampered"})
                )
        assert getattr(update_error.value.orig, "sqlstate", None) == "42501"
        assert "append-only relation" in str(update_error.value.orig)

        with pytest.raises(DBAPIError) as delete_error:
            with database.tenant_transaction(tenant_id) as session:
                row = session.get(AuditEvent, event_id)
                assert row is not None
                session.delete(row)
                session.flush()
        assert getattr(delete_error.value.orig, "sqlstate", None) == "42501"

        with database.tenant_transaction(tenant_id) as session:
            row = session.scalar(select(AuditEvent).where(AuditEvent.id == event_id))
            assert row is not None
            assert row.payload == {"state": "original"}

        with admin_engine.begin() as connection:
            connection.execute(
                text("UPDATE audit_events SET payload = :payload WHERE id = :id"),
                {"payload": '{"state":"owner_break_glass"}', "id": event_id},
            )
            assert (
                connection.scalar(
                    text("SELECT payload ->> 'state' FROM audit_events WHERE id = :id"),
                    {"id": event_id},
                )
                == "owner_break_glass"
            )
    finally:
        database.dispose()
        drop_role(admin_engine, role_name)
        admin_engine.dispose()
