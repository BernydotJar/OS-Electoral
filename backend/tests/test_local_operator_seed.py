from __future__ import annotations

from scripts.dev.seed_local_operator import (
    CAMPAIGN_ID,
    DEVELOPMENT_ISSUER,
    DEVELOPMENT_SUBJECT,
    FUNCTIONAL_CAMPAIGN_CREATE_GRANT,
    GRANTS,
    TENANT_ID,
    require_local_database_url,
    seed_local_operator,
)
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from campaignos.data.models import (
    Base,
    Campaign,
    Membership,
    PermissionGrant,
    Principal,
    RoleAssignment,
    Tenant,
    Workspace,
)


def test_local_seed_is_idempotent_and_grants_only_the_bounded_journey() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    try:
        seed_local_operator(engine)
        seed_local_operator(engine)
        with Session(engine) as session:
            assert session.scalar(select(func.count()).select_from(Tenant)) == 1
            assert session.scalar(select(func.count()).select_from(Principal)) == 1
            assert session.scalar(select(func.count()).select_from(Campaign)) == 1
            assert session.scalar(select(func.count()).select_from(Workspace)) == 1
            assert session.scalar(select(func.count()).select_from(Membership)) == 1
            assert session.scalar(select(func.count()).select_from(RoleAssignment)) == 1
            grants = tuple(session.scalars(select(PermissionGrant).order_by(PermissionGrant.id)))

        assert len(grants) == len(GRANTS) == 26
        assert {(grant.action, grant.resource_type, grant.purpose) for grant in grants} == {
            (spec.action, spec.resource_type, spec.purpose) for spec in GRANTS
        }
        assert all(grant.tenant_id == TENANT_ID for grant in grants)
        assert all(grant.campaign_id == CAMPAIGN_ID for grant in grants)
        assert all(grant.workspace_id is None for grant in grants)
        assert all(grant.resource_type != "campaign_collection" for grant in grants)
        assert {
            (grant.action, grant.purpose)
            for grant in grants
            if grant.resource_type == "candidate_workspace"
        } == {
            ("create", "Create candidate evidence workspace"),
            ("read", "Review candidate evidence workspace"),
            ("update", "Maintain candidate evidence workspace"),
            ("approve", "Approve candidate evidence section"),
        }
        assert {
            (grant.action, grant.purpose)
            for grant in grants
            if grant.resource_type == "team_workspace"
        } == {
            ("create", "Create campaign team workspace"),
            ("read", "Review campaign team workspace"),
            ("update", "Maintain campaign team workspace"),
        }
        assert {
            (grant.action, grant.purpose)
            for grant in grants
            if grant.resource_type == "training_academy"
        } == {
            ("training.catalog.read", "Review approved training catalog"),
            ("training.self.read", "Review own campaign training"),
            ("training.self.complete", "Complete assigned campaign training"),
            ("training.assignment.manage", "Assign campaign learning path"),
            ("training.receipt.read", "Review own campaign training"),
        }
        assert {
            (grant.action, grant.purpose)
            for grant in grants
            if grant.resource_type == "strategy_workspace"
        } == {
            ("create", "Create campaign strategy workspace"),
            ("read", "Review campaign strategy workspace"),
            ("update", "Maintain campaign strategy workspace"),
            ("approve", "Approve internal campaign strategy option"),
        }
        assert session is not None
        with Session(engine) as session:
            principal = session.scalar(
                select(Principal).where(
                    Principal.issuer == DEVELOPMENT_ISSUER,
                    Principal.subject == DEVELOPMENT_SUBJECT,
                )
            )
            assert principal is not None
            assert principal.email == "operator@localhost"
    finally:
        engine.dispose()


def test_functional_seed_adds_only_the_exact_tenant_campaign_create_grant() -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    try:
        seed_local_operator(engine, include_campaign_create=True)
        seed_local_operator(engine, include_campaign_create=True)
        with Session(engine) as session:
            grants = tuple(session.scalars(select(PermissionGrant)))

        assert len(grants) == len(GRANTS) + 1
        create_grants = [grant for grant in grants if grant.resource_type == "campaign_collection"]
        assert len(create_grants) == 1
        grant = create_grants[0]
        assert grant.id == FUNCTIONAL_CAMPAIGN_CREATE_GRANT.id
        assert grant.tenant_id == TENANT_ID
        assert grant.campaign_id is None
        assert grant.workspace_id is None
        assert grant.action == "create"
        assert grant.resource_id == str(TENANT_ID)
        assert grant.purpose == "Create tenant campaign"
    finally:
        engine.dispose()


def test_local_seed_refuses_non_local_or_non_owner_database_urls() -> None:
    valid = "postgresql+psycopg://campaignos_admin:local@127.0.0.1:5432/campaignos"
    test_database = (
        "postgresql+psycopg://campaignos_admin_front002:local@localhost/campaignos_front002_test"
    )
    require_local_database_url(valid)
    require_local_database_url(test_database)

    invalid = (
        "postgresql+psycopg://campaignos_admin:local@db.example.test/campaignos",
        "postgresql+psycopg://campaignos_app:local@127.0.0.1/campaignos",
        "postgresql+psycopg://campaignos_admin:local@127.0.0.1/production",
        "sqlite:///campaignos.db",
    )
    for value in invalid:
        try:
            require_local_database_url(value)
        except ValueError:
            continue
        raise AssertionError(f"unsafe database URL was accepted: {value}")
