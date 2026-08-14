#!/usr/bin/env python3
"""Seed the bounded local operator journey into a localhost PostgreSQL database."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from urllib.parse import urlparse
from uuid import UUID

from sqlalchemy import Engine, create_engine, select, text
from sqlalchemy.orm import Session

from campaignos.data.models import (
    Campaign,
    Membership,
    PermissionGrant,
    Principal,
    RoleAssignment,
    Tenant,
    Workspace,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
MEMBERSHIP_ID = UUID("33333333-3333-4333-8333-333333333333")
ROLE_ASSIGNMENT_ID = UUID("44444444-4444-4444-8444-444444444444")
CAMPAIGN_READ_GRANT_ID = UUID("55555555-5555-4555-8555-555555555555")
READINESS_READ_GRANT_ID = UUID("66666666-6666-4666-8666-666666666666")
PRINCIPAL_ID = UUID("77777777-7777-4777-8777-777777777777")
INTAKE_CREATE_GRANT_ID = UUID("88888888-8888-4888-8888-888888888888")
INTAKE_READ_GRANT_ID = UUID("99999999-9999-4999-8999-999999999999")
INTAKE_UPDATE_GRANT_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
CANDIDATE_CREATE_GRANT_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
CANDIDATE_READ_GRANT_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
CANDIDATE_UPDATE_GRANT_ID = UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")
CANDIDATE_APPROVE_GRANT_ID = UUID("caaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
TEAM_CREATE_GRANT_ID = UUID("f1111111-1111-4111-8111-111111111111")
TEAM_READ_GRANT_ID = UUID("f2222222-2222-4222-8222-222222222222")
TEAM_UPDATE_GRANT_ID = UUID("f3333333-3333-4333-8333-333333333333")
CAMPAIGN_CREATE_GRANT_ID = UUID("f4444444-4444-4444-8444-444444444444")
TRAINING_CATALOG_READ_GRANT_ID = UUID("f5555555-5555-4555-8555-555555555555")
TRAINING_SELF_READ_GRANT_ID = UUID("f6666666-6666-4666-8666-666666666666")
TRAINING_SELF_COMPLETE_GRANT_ID = UUID("f7777777-7777-4777-8777-777777777777")
TRAINING_ASSIGNMENT_MANAGE_GRANT_ID = UUID("f8888888-8888-4888-8888-888888888888")
TRAINING_RECEIPT_READ_GRANT_ID = UUID("f9999999-9999-4999-8999-999999999999")
STRATEGY_CREATE_GRANT_ID = UUID("fa111111-1111-4111-8111-111111111111")
STRATEGY_READ_GRANT_ID = UUID("fa222222-2222-4222-8222-222222222222")
STRATEGY_UPDATE_GRANT_ID = UUID("fa333333-3333-4333-8333-333333333333")
STRATEGY_APPROVE_GRANT_ID = UUID("fa444444-4444-4444-8444-444444444444")
WORKSPACE_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")

DEVELOPMENT_ISSUER = "urn:campaignos:development"
DEVELOPMENT_SUBJECT = "local-operator"


@dataclass(frozen=True, slots=True)
class GrantSpec:
    id: UUID
    action: str
    resource_type: str
    resource_id: str
    purpose: str
    campaign_id: UUID | None = CAMPAIGN_ID


GRANTS = (
    GrantSpec(
        CAMPAIGN_READ_GRANT_ID,
        "read",
        "campaign",
        str(CAMPAIGN_ID),
        "Operate assigned campaign",
    ),
    GrantSpec(
        READINESS_READ_GRANT_ID,
        "read",
        "campaign_readiness",
        str(CAMPAIGN_ID),
        "Assess assigned campaign readiness",
    ),
    GrantSpec(
        INTAKE_CREATE_GRANT_ID,
        "create",
        "guided_intake",
        str(CAMPAIGN_ID),
        "Begin guided campaign intake",
    ),
    GrantSpec(
        INTAKE_READ_GRANT_ID,
        "read",
        "guided_intake",
        str(CAMPAIGN_ID),
        "Review guided campaign intake",
    ),
    GrantSpec(
        INTAKE_UPDATE_GRANT_ID,
        "update",
        "guided_intake",
        str(CAMPAIGN_ID),
        "Maintain guided campaign intake",
    ),
    GrantSpec(
        CANDIDATE_CREATE_GRANT_ID,
        "create",
        "candidate_workspace",
        str(CAMPAIGN_ID),
        "Create candidate evidence workspace",
    ),
    GrantSpec(
        CANDIDATE_READ_GRANT_ID,
        "read",
        "candidate_workspace",
        str(CAMPAIGN_ID),
        "Review candidate evidence workspace",
    ),
    GrantSpec(
        CANDIDATE_UPDATE_GRANT_ID,
        "update",
        "candidate_workspace",
        str(CAMPAIGN_ID),
        "Maintain candidate evidence workspace",
    ),
    GrantSpec(
        CANDIDATE_APPROVE_GRANT_ID,
        "approve",
        "candidate_workspace",
        str(CAMPAIGN_ID),
        "Approve candidate evidence section",
    ),
    GrantSpec(
        TEAM_CREATE_GRANT_ID,
        "create",
        "team_workspace",
        str(CAMPAIGN_ID),
        "Create campaign team workspace",
    ),
    GrantSpec(
        TEAM_READ_GRANT_ID,
        "read",
        "team_workspace",
        str(CAMPAIGN_ID),
        "Review campaign team workspace",
    ),
    GrantSpec(
        TEAM_UPDATE_GRANT_ID,
        "update",
        "team_workspace",
        str(CAMPAIGN_ID),
        "Maintain campaign team workspace",
    ),
    GrantSpec(
        TRAINING_CATALOG_READ_GRANT_ID,
        "training.catalog.read",
        "training_academy",
        str(CAMPAIGN_ID),
        "Review approved training catalog",
    ),
    GrantSpec(
        TRAINING_SELF_READ_GRANT_ID,
        "training.self.read",
        "training_academy",
        str(CAMPAIGN_ID),
        "Review own campaign training",
    ),
    GrantSpec(
        TRAINING_SELF_COMPLETE_GRANT_ID,
        "training.self.complete",
        "training_academy",
        str(CAMPAIGN_ID),
        "Complete assigned campaign training",
    ),
    GrantSpec(
        TRAINING_ASSIGNMENT_MANAGE_GRANT_ID,
        "training.assignment.manage",
        "training_academy",
        str(CAMPAIGN_ID),
        "Assign campaign learning path",
    ),
    GrantSpec(
        TRAINING_RECEIPT_READ_GRANT_ID,
        "training.receipt.read",
        "training_academy",
        str(CAMPAIGN_ID),
        "Review own campaign training",
    ),
    GrantSpec(
        STRATEGY_CREATE_GRANT_ID,
        "create",
        "strategy_workspace",
        str(CAMPAIGN_ID),
        "Create campaign strategy workspace",
    ),
    GrantSpec(
        STRATEGY_READ_GRANT_ID,
        "read",
        "strategy_workspace",
        str(CAMPAIGN_ID),
        "Review campaign strategy workspace",
    ),
    GrantSpec(
        STRATEGY_UPDATE_GRANT_ID,
        "update",
        "strategy_workspace",
        str(CAMPAIGN_ID),
        "Maintain campaign strategy workspace",
    ),
    GrantSpec(
        STRATEGY_APPROVE_GRANT_ID,
        "approve",
        "strategy_workspace",
        str(CAMPAIGN_ID),
        "Approve internal campaign strategy option",
    ),
)

FUNCTIONAL_CAMPAIGN_CREATE_GRANT = GrantSpec(
    CAMPAIGN_CREATE_GRANT_ID,
    "create",
    "campaign_collection",
    str(TENANT_ID),
    "Create tenant campaign",
    campaign_id=None,
)


def require_local_database_url(database_url: str) -> None:
    parsed = urlparse(database_url)
    if parsed.scheme != "postgresql+psycopg":
        raise ValueError("Local seed requires postgresql+psycopg")
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise ValueError("Local seed refuses non-local database hosts")
    if not (parsed.username and parsed.username.startswith("campaignos_admin")):
        raise ValueError("Local seed requires a campaignos development database owner")
    database_name = parsed.path.removeprefix("/")
    if database_name != "campaignos" and not database_name.endswith("_test"):
        raise ValueError("Local seed requires campaignos or an isolated *_test database")


def _ensure_identity(row: object, *, expected_id: UUID, label: str) -> None:
    if getattr(row, "id", None) != expected_id:
        raise RuntimeError(f"Existing {label} conflicts with the deterministic development seed")


def seed_local_operator(engine: Engine, *, include_campaign_create: bool = False) -> None:
    with Session(engine) as session, session.begin():
        if engine.dialect.name == "postgresql":
            session.execute(
                text("SELECT set_config('campaignos.tenant_id', :tenant_id, true)"),
                {"tenant_id": str(TENANT_ID)},
            )
        tenant = session.get(Tenant, TENANT_ID)
        if tenant is None:
            tenant = Tenant(
                id=TENANT_ID,
                slug="local-development",
                name="CampaignOS Local Development",
                status="ACTIVE",
                version=1,
            )
            session.add(tenant)
        else:
            _ensure_identity(tenant, expected_id=TENANT_ID, label="tenant")

        principal = session.scalar(
            select(Principal).where(
                Principal.issuer == DEVELOPMENT_ISSUER,
                Principal.subject == DEVELOPMENT_SUBJECT,
            )
        )
        if principal is None:
            principal = Principal(
                id=PRINCIPAL_ID,
                issuer=DEVELOPMENT_ISSUER,
                subject=DEVELOPMENT_SUBJECT,
                display_name="Operador local",
                email="operator@localhost",
            )
            session.add(principal)
        else:
            _ensure_identity(principal, expected_id=PRINCIPAL_ID, label="principal")

        campaign = session.get(Campaign, CAMPAIGN_ID)
        if campaign is None:
            session.add(
                Campaign(
                    id=CAMPAIGN_ID,
                    tenant_id=TENANT_ID,
                    slug="campana-local",
                    name="Campaña local de trabajo",
                    jurisdiction="Guatemala",
                    stage="PRECAMPAIGN",
                    status="DRAFT",
                    version=1,
                )
            )
        else:
            _ensure_identity(campaign, expected_id=CAMPAIGN_ID, label="campaign")

        workspace = session.get(Workspace, WORKSPACE_ID)
        if workspace is None:
            session.add(
                Workspace(
                    id=WORKSPACE_ID,
                    tenant_id=TENANT_ID,
                    campaign_id=CAMPAIGN_ID,
                    slug="operaciones",
                    name="Operaciones de campaña",
                    status="ACTIVE",
                    version=1,
                )
            )
        else:
            _ensure_identity(workspace, expected_id=WORKSPACE_ID, label="workspace")

        membership = session.get(Membership, MEMBERSHIP_ID)
        if membership is None:
            session.add(
                Membership(
                    id=MEMBERSHIP_ID,
                    tenant_id=TENANT_ID,
                    principal_id=PRINCIPAL_ID,
                    campaign_id=None,
                    status="ACTIVE",
                    version=1,
                )
            )
        else:
            _ensure_identity(membership, expected_id=MEMBERSHIP_ID, label="membership")

        role = session.get(RoleAssignment, ROLE_ASSIGNMENT_ID)
        if role is None:
            session.add(
                RoleAssignment(
                    id=ROLE_ASSIGNMENT_ID,
                    tenant_id=TENANT_ID,
                    membership_id=MEMBERSHIP_ID,
                    role="local_operator",
                    assigned_by_principal_id=PRINCIPAL_ID,
                )
            )
        else:
            _ensure_identity(role, expected_id=ROLE_ASSIGNMENT_ID, label="role assignment")

        grants = (*GRANTS, FUNCTIONAL_CAMPAIGN_CREATE_GRANT) if include_campaign_create else GRANTS
        for spec in grants:
            grant = session.get(PermissionGrant, spec.id)
            if grant is None:
                session.add(
                    PermissionGrant(
                        id=spec.id,
                        tenant_id=TENANT_ID,
                        membership_id=MEMBERSHIP_ID,
                        campaign_id=spec.campaign_id,
                        workspace_id=None,
                        action=spec.action,
                        resource_type=spec.resource_type,
                        resource_id=spec.resource_id,
                        purpose=spec.purpose,
                        status="ACTIVE",
                        granted_by_principal_id=PRINCIPAL_ID,
                        approval_receipt_id=f"development-seed:{spec.action}:{spec.resource_type}",
                    )
                )
                continue
            actual = (
                grant.tenant_id,
                grant.membership_id,
                grant.campaign_id,
                grant.workspace_id,
                grant.action,
                grant.resource_type,
                grant.resource_id,
                grant.purpose,
            )
            expected = (
                TENANT_ID,
                MEMBERSHIP_ID,
                spec.campaign_id,
                None,
                spec.action,
                spec.resource_type,
                spec.resource_id,
                spec.purpose,
            )
            if actual != expected:
                raise RuntimeError("Existing permission grant conflicts with development seed")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-url", required=True)
    parser.add_argument(
        "--include-campaign-create",
        action="store_true",
        help="Add the exact tenant campaign-create grant for isolated functional E2E only.",
    )
    args = parser.parse_args()
    require_local_database_url(args.database_url)
    engine = create_engine(args.database_url, pool_pre_ping=True)
    try:
        seed_local_operator(engine, include_campaign_create=args.include_campaign_create)
    finally:
        engine.dispose()
    print(
        "[OK] Local operator seeded; tenant=11111111-1111-4111-8111-111111111111; "
        "campaign=22222222-2222-4222-8222-222222222222; "
        f"exact_grants={len(GRANTS) + (1 if args.include_campaign_create else 0)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
