from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from threading import Barrier
from uuid import uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url

from campaignos.campaigns import (
    CampaignCreate,
    CampaignCreateConflict,
    CampaignCreateEvidence,
    SqlAlchemyCampaignCreator,
)
from campaignos.data import Database
from campaignos.data.models import (
    AuditEvent,
    Campaign,
    IdempotencyRecord,
    Membership,
    OutboxEvent,
    PermissionGrant,
    Principal,
    RoleAssignment,
    Tenant,
)
from campaignos.identity.authorization import SqlAlchemyMembershipDirectory
from campaignos.identity.models import AuthenticatedPrincipal

PURPOSE = "Create tenant campaign"


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


def _create_request(slug: str) -> CampaignCreate:
    return CampaignCreate(
        slug=slug,
        name=f"Campaign {slug}",
        jurisdiction="Antigua Guatemala",
        stage="PRECAMPAIGN",
    )


@pytest.mark.postgres
def test_postgresql_campaign_create_serializes_replay_and_slug_conflicts(
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
    role_name = "campaignos_campaign_create_test"
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
        pool_size=4,
        max_overflow=0,
    )
    tenant_id = uuid4()
    other_tenant_id = uuid4()
    principal_id = uuid4()
    membership_id = uuid4()
    grant_id = uuid4()
    try:
        with database.tenant_transaction(tenant_id) as session:
            session.add_all(
                [
                    Principal(
                        id=principal_id,
                        issuer="https://identity.example.test/",
                        subject=f"campaign-create-{principal_id}",
                    ),
                    Tenant(
                        id=tenant_id,
                        slug=f"tenant-{tenant_id}",
                        name="Campaign Create Tenant",
                    ),
                ]
            )
        with database.tenant_transaction(tenant_id) as session:
            session.add(
                Membership(
                    id=membership_id,
                    tenant_id=tenant_id,
                    principal_id=principal_id,
                    campaign_id=None,
                    status="ACTIVE",
                )
            )
            session.flush()
            session.add_all(
                [
                    RoleAssignment(
                        tenant_id=tenant_id,
                        membership_id=membership_id,
                        role="portfolio_administrator",
                        assigned_by_principal_id=principal_id,
                    ),
                    PermissionGrant(
                        id=grant_id,
                        tenant_id=tenant_id,
                        membership_id=membership_id,
                        campaign_id=None,
                        workspace_id=None,
                        action="create",
                        resource_type="campaign_collection",
                        resource_id=str(tenant_id),
                        purpose=PURPOSE,
                        granted_by_principal_id=principal_id,
                        approval_receipt_id="postgres-campaign-create-approval",
                    ),
                ]
            )

        identity = AuthenticatedPrincipal(
            issuer="https://identity.example.test/",
            subject=f"campaign-create-{principal_id}",
            audience="campaignos-test",
            authenticated_at=datetime.now(UTC),
        )
        authorization = SqlAlchemyMembershipDirectory(database).load(tenant_id, identity)
        create_grant = next(
            grant
            for membership in authorization.memberships
            for grant in membership.grants
            if grant.grant_id == grant_id
        )
        assert authorization.permits(
            action="create",
            resource_type="campaign_collection",
            resource_id=str(tenant_id),
            purpose=PURPOSE,
            campaign_id=None,
            workspace_id=None,
        )

        creator = SqlAlchemyCampaignCreator(database)

        def create(
            *,
            slug: str,
            key: str,
            correlation_id: str,
        ) -> CampaignCreateEvidence:
            return creator.create(
                tenant_id,
                request=_create_request(slug),
                principal_id=principal_id,
                authorization_grant_id=create_grant.grant_id,
                approval_receipt_id=create_grant.approval_receipt_id,
                authorization_purpose=create_grant.purpose,
                correlation_id=correlation_id,
                idempotency_key=key,
            )

        same_key_barrier = Barrier(2)

        def create_same_key(index: int) -> CampaignCreateEvidence:
            same_key_barrier.wait()
            return create(
                slug="same-key-campaign",
                key="postgres-same-key",
                correlation_id=f"same-key-{index}",
            )

        with ThreadPoolExecutor(max_workers=2) as executor:
            same_key_results = list(executor.map(create_same_key, (1, 2)))

        assert same_key_results[0] == same_key_results[1]
        first_evidence = same_key_results[0]
        with database.tenant_transaction(tenant_id) as session:
            assert session.scalar(select(func.count()).select_from(Campaign)) == 1
            assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
            assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
            assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1
            audit = session.get(AuditEvent, first_evidence.audit_event_id)
            assert audit is not None
            assert audit.payload["authorization_purpose"] == PURPOSE
            assert audit.payload["external_effects"] == "NONE"

        same_slug_barrier = Barrier(2)

        def create_same_slug(index: int) -> str:
            same_slug_barrier.wait()
            try:
                create(
                    slug="same-slug-campaign",
                    key=f"postgres-same-slug-{index}",
                    correlation_id=f"same-slug-{index}",
                )
            except CampaignCreateConflict:
                return "CONFLICT"
            return "CREATED"

        with ThreadPoolExecutor(max_workers=2) as executor:
            same_slug_results = sorted(executor.map(create_same_slug, (1, 2)))

        assert same_slug_results == ["CONFLICT", "CREATED"]
        with database.tenant_transaction(tenant_id) as session:
            assert session.scalar(select(func.count()).select_from(Campaign)) == 2
            assert session.scalar(select(func.count()).select_from(AuditEvent)) == 2
            assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 2
            assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 2

        with database.tenant_transaction(other_tenant_id) as session:
            session.add(
                Tenant(
                    id=other_tenant_id,
                    slug=f"tenant-{other_tenant_id}",
                    name="Other Campaign Create Tenant",
                )
            )
        other_evidence = SqlAlchemyCampaignCreator(database).create(
            other_tenant_id,
            request=_create_request("same-key-campaign"),
            principal_id=principal_id,
            authorization_grant_id=create_grant.grant_id,
            approval_receipt_id=create_grant.approval_receipt_id,
            authorization_purpose=create_grant.purpose,
            correlation_id="other-tenant-create",
            idempotency_key="postgres-same-key",
        )
        assert other_evidence.campaign.tenant_id == other_tenant_id
        with database.tenant_transaction(tenant_id) as session:
            visible_ids = set(session.scalars(select(Campaign.id)))
            assert other_evidence.campaign.id not in visible_ids
            assert len(visible_ids) == 2
        with database.tenant_transaction(other_tenant_id) as session:
            visible_ids = set(session.scalars(select(Campaign.id)))
            assert visible_ids == {other_evidence.campaign.id}
    finally:
        database.dispose()
        with admin_engine.begin() as connection:
            connection.execute(text(f'DROP OWNED BY "{role_name}"'))
            connection.execute(text(f'DROP ROLE IF EXISTS "{role_name}"'))
        admin_engine.dispose()
