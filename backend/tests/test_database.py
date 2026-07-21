from __future__ import annotations

import os
import re
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from campaignos.campaigns import (
    CampaignReadinessNotFound,
    SqlAlchemyCampaignReadinessReader,
)
from campaignos.data import Base, Database, MissingTenantScope
from campaignos.data.database import TenantSession
from campaignos.data.models import (
    AuditEvent,
    Campaign,
    Membership,
    OutboxEvent,
    PermissionGrant,
    Principal,
    RoleAssignment,
    Tenant,
    Workspace,
)
from campaignos.identity.authorization import (
    SqlAlchemyMembershipDirectory,
    TenantAccessDenied,
)
from campaignos.identity.models import AuthenticatedPrincipal

TENANT_TABLES = {
    "campaigns",
    "workspaces",
    "memberships",
    "role_assignments",
    "permission_grants",
    "audit_events",
    "outbox_events",
    "idempotency_records",
    "guided_intakes",
    "candidate_workspaces",
    "candidate_section_approvals",
    "identity_invitations",
    "application_sessions",
    "support_access_requests",
}


def test_initial_metadata_has_explicit_tenant_ownership() -> None:
    assert set(Base.metadata.tables) == {"tenants", "principals", *TENANT_TABLES}
    for table_name in TENANT_TABLES:
        assert "tenant_id" in Base.metadata.tables[table_name].columns


def test_tenant_transaction_requires_uuid_scope_and_sets_session_identity() -> None:
    database = Database.from_url("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    tenant_id = uuid4()

    with pytest.raises(MissingTenantScope):
        with database.tenant_transaction("not-a-uuid"):  # type: ignore[arg-type]
            pass

    with database.tenant_transaction(tenant_id) as session:
        assert session.info["tenant_id"] == tenant_id
        session.add(Tenant(id=tenant_id, slug="tenant-a", name="Tenant A", status="ACTIVE"))

    with database.tenant_transaction(tenant_id) as session:
        assert session.scalar(select(Tenant.id)) == tenant_id

    database.dispose()


def test_unscoped_application_session_fails_before_query() -> None:
    database = Database.from_url("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(database.engine)
    with TenantSession(bind=database.engine) as session:
        with pytest.raises(MissingTenantScope):
            session.execute(select(Tenant.id))
    database.dispose()


def test_database_readiness_is_dependency_based() -> None:
    database = Database.from_url("sqlite+pysqlite:///:memory:")
    assert database.readiness() == (True, "Database connection is available")
    database.dispose()


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


@pytest.mark.postgres
def test_migration_and_rls_isolate_existing_foreign_tenant_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    admin_url = _postgres_test_url()
    monkeypatch.setenv("CAMPAIGNOS_DATABASE_URL", admin_url)
    alembic = Config("alembic.ini")
    command.downgrade(alembic, "base")
    command.upgrade(alembic, "head")
    command.check(alembic)

    admin_engine = create_engine(admin_url)
    database_name = make_url(admin_url).database
    assert database_name is not None
    assert re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*_test", database_name)
    role_name = "campaignos_app_test"
    role_password = "campaignos_app_test_password"  # noqa: S105 - isolated test role.
    with admin_engine.begin() as connection:
        tables = set(inspect(connection).get_table_names())
        assert set(Base.metadata.tables) <= tables
        revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        assert revision == "20260721_0006"
        policies = connection.execute(
            text(
                "SELECT tablename FROM pg_policies "
                "WHERE schemaname = 'public' AND policyname = 'tenant_isolation'"
            )
        ).scalars()
        assert set(policies) == {"tenants", *TENANT_TABLES}
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
    database = Database.from_url(application_url.render_as_string(hide_password=False))
    tenant_a = uuid4()
    tenant_b = uuid4()
    principal_id = uuid4()
    campaign_a = uuid4()
    campaign_b = uuid4()
    workspace_a = uuid4()
    membership_a = uuid4()
    try:
        with database.tenant_transaction(tenant_a) as session:
            session.add(
                Principal(
                    id=principal_id,
                    issuer="https://identity.example.test/",
                    subject="rls-test-user",
                )
            )
            session.add(Tenant(id=tenant_a, slug=f"tenant-{tenant_a}", name="Tenant A"))
            session.flush()
            session.add(
                Campaign(
                    id=campaign_a,
                    tenant_id=tenant_a,
                    slug="campaign-a",
                    name="Campaign A",
                    jurisdiction="Test",
                    stage="TEST",
                )
            )
            session.add(
                Workspace(
                    id=workspace_a,
                    tenant_id=tenant_a,
                    campaign_id=campaign_a,
                    slug="governance",
                    name="Governance",
                    status="ACTIVE",
                    version=1,
                )
            )
        with database.tenant_transaction(tenant_a) as session:
            session.add(
                Membership(
                    id=membership_a,
                    tenant_id=tenant_a,
                    principal_id=principal_id,
                    campaign_id=campaign_a,
                    status="ACTIVE",
                )
            )
            session.flush()
            session.add_all(
                [
                    RoleAssignment(
                        tenant_id=tenant_a,
                        membership_id=membership_a,
                        role="operator",
                        assigned_by_principal_id=principal_id,
                    ),
                    PermissionGrant(
                        tenant_id=tenant_a,
                        membership_id=membership_a,
                        campaign_id=campaign_a,
                        action="read",
                        resource_type="campaign",
                        resource_id=str(campaign_a),
                        purpose="RLS integration verification",
                        granted_by_principal_id=principal_id,
                        approval_receipt_id="rls-test-approval",
                    ),
                    PermissionGrant(
                        tenant_id=tenant_a,
                        membership_id=membership_a,
                        campaign_id=campaign_a,
                        action="read",
                        resource_type="campaign_readiness",
                        resource_id=str(campaign_a),
                        purpose="Assess assigned campaign readiness",
                        granted_by_principal_id=principal_id,
                        approval_receipt_id="readiness-test-approval",
                    ),
                ]
            )
        with database.tenant_transaction(tenant_b) as session:
            session.add(Tenant(id=tenant_b, slug=f"tenant-{tenant_b}", name="Tenant B"))
            session.flush()
            session.add(
                Campaign(
                    id=campaign_b,
                    tenant_id=tenant_b,
                    slug="campaign-b",
                    name="Campaign B",
                    jurisdiction="Test",
                    stage="TEST",
                )
            )

        with database.tenant_transaction(tenant_a) as session:
            visible = set(session.scalars(select(Campaign.id)))
            assert visible == {campaign_a}
            assert session.get(Campaign, campaign_b) is None

        verified_identity = AuthenticatedPrincipal(
            issuer="https://identity.example.test/",
            subject="rls-test-user",
            audience="campaignos-test",
            authenticated_at=datetime.now(UTC),
        )
        authorization = SqlAlchemyMembershipDirectory(database).load(
            tenant_a,
            verified_identity,
        )
        assert authorization.principal_id == principal_id
        assert authorization.memberships[0].roles == ("operator",)
        assert authorization.permits(
            action="read",
            resource_type="campaign",
            resource_id=str(campaign_a),
            purpose="RLS integration verification",
            campaign_id=campaign_a,
        )
        assert authorization.permits(
            action="read",
            resource_type="campaign_readiness",
            resource_id=str(campaign_a),
            purpose="Assess assigned campaign readiness",
            campaign_id=campaign_a,
        )
        readiness_grant = next(
            grant
            for membership in authorization.memberships
            for grant in membership.grants
            if grant.resource_type == "campaign_readiness"
        )
        readiness_reader = SqlAlchemyCampaignReadinessReader(database)
        readiness = readiness_reader.get(
            tenant_a,
            campaign_a,
            principal_id=principal_id,
            authorization_grant_id=readiness_grant.grant_id,
            approval_receipt_id=readiness_grant.approval_receipt_id,
            authorization_purpose=readiness_grant.purpose,
            correlation_id="postgres-readiness-proof",
        )
        assert readiness.readiness.status == "READY_FOR_GUIDED_INTAKE"
        assert readiness.readiness.active_workspace_count == 1
        with database.tenant_transaction(tenant_a) as session:
            audit = session.get(AuditEvent, readiness.audit_event_id)
            assert audit is not None
            assert audit.tenant_id == tenant_a
            assert audit.campaign_id == campaign_a
            assert audit.principal_id == principal_id
            assert audit.payload["authorization_grant_id"] == str(readiness_grant.grant_id)
            assert audit.payload["correlation_id"] == "postgres-readiness-proof"
            assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
        with pytest.raises(CampaignReadinessNotFound):
            readiness_reader.get(
                tenant_a,
                campaign_b,
                principal_id=principal_id,
                authorization_grant_id=readiness_grant.grant_id,
                approval_receipt_id=readiness_grant.approval_receipt_id,
                authorization_purpose=readiness_grant.purpose,
                correlation_id="postgres-cross-tenant-denial",
            )
        with database.tenant_transaction(tenant_a) as session:
            assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
        with pytest.raises(TenantAccessDenied):
            SqlAlchemyMembershipDirectory(database).load(
                tenant_b,
                verified_identity,
            )

        with pytest.raises(DBAPIError):
            with database.tenant_transaction(tenant_a) as session:
                session.add(
                    Campaign(
                        id=uuid4(),
                        tenant_id=tenant_b,
                        slug="cross-tenant-write",
                        name="Forbidden",
                        jurisdiction="Test",
                        stage="TEST",
                    )
                )
    finally:
        database.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP OWNED BY "{role_name}"'))
            connection.execute(text(f'DROP ROLE IF EXISTS "{role_name}"'))
        admin_engine.dispose()


def test_uuid_type_is_used_for_tenant_identifiers() -> None:
    assert Tenant.__table__.c.id.type.python_type is UUID
