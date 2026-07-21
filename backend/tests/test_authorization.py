from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from campaignos.data import Base, Database
from campaignos.data.models import (
    Campaign,
    Membership,
    PermissionGrant,
    Principal,
    RoleAssignment,
    Tenant,
    Workspace,
)
from campaignos.identity.authorization import (
    AuthorizationDataError,
    AuthorizationDirectoryUnavailable,
    EffectiveMembership,
    EffectivePermissionGrant,
    SqlAlchemyMembershipDirectory,
    TenantAccessDenied,
    TenantAuthorizationContext,
    UnavailableMembershipDirectory,
)
from campaignos.identity.models import AuthenticatedPrincipal

EVALUATED_AT = datetime(2026, 7, 19, 12, tzinfo=UTC)
ISSUER = "https://identity.example.test/"
SUBJECT = "authorization-test-user"


@pytest.fixture
def database() -> Iterator[Database]:
    runtime = Database.from_url("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(runtime.engine)
    try:
        yield runtime
    finally:
        runtime.dispose()


def authenticated_principal(
    *,
    issuer: str = ISSUER,
    subject: str = SUBJECT,
) -> AuthenticatedPrincipal:
    return AuthenticatedPrincipal(
        subject=subject,
        issuer=issuer,
        audience="campaignos-test",
        authenticated_at=EVALUATED_AT,
    )


def seed_active_authorization(
    database: Database,
    *,
    tenant_status: str = "ACTIVE",
    principal_disabled_at: datetime | None = None,
    membership_status: str = "ACTIVE",
) -> tuple[UUID, UUID, UUID, UUID, UUID]:
    tenant_id = uuid4()
    principal_id = uuid4()
    campaign_id = uuid4()
    membership_id = uuid4()
    grant_id = uuid4()
    with database.tenant_transaction(tenant_id) as session:
        session.add(
            Tenant(
                id=tenant_id,
                slug=f"tenant-{tenant_id}",
                name="Authorization Test Tenant",
                status=tenant_status,
            )
        )
        session.add(
            Principal(
                id=principal_id,
                issuer=ISSUER,
                subject=SUBJECT,
                disabled_at=principal_disabled_at,
            )
        )
        session.flush()
        session.add(
            Campaign(
                id=campaign_id,
                tenant_id=tenant_id,
                slug="campaign-a",
                name="Campaign A",
                jurisdiction="Test",
                stage="TEST",
                status="ACTIVE",
            )
        )
        session.flush()
        session.add(
            Membership(
                id=membership_id,
                tenant_id=tenant_id,
                principal_id=principal_id,
                campaign_id=campaign_id,
                status=membership_status,
                valid_from=EVALUATED_AT - timedelta(days=1),
            )
        )
        session.flush()
        session.add_all(
            [
                RoleAssignment(
                    tenant_id=tenant_id,
                    membership_id=membership_id,
                    role="viewer",
                    assigned_by_principal_id=principal_id,
                ),
                RoleAssignment(
                    tenant_id=tenant_id,
                    membership_id=membership_id,
                    role="admin",
                    assigned_by_principal_id=principal_id,
                ),
                PermissionGrant(
                    id=grant_id,
                    tenant_id=tenant_id,
                    membership_id=membership_id,
                    campaign_id=campaign_id,
                    action="read",
                    resource_type="campaign",
                    resource_id=str(campaign_id),
                    purpose="Operate assigned campaign",
                    valid_from=EVALUATED_AT - timedelta(hours=1),
                    granted_by_principal_id=principal_id,
                    approval_receipt_id="approval-123",
                ),
            ]
        )
    return tenant_id, principal_id, campaign_id, membership_id, grant_id


def test_loads_only_server_owned_memberships_and_exact_grants(database: Database) -> None:
    tenant_id, principal_id, campaign_id, membership_id, grant_id = seed_active_authorization(
        database
    )

    context = SqlAlchemyMembershipDirectory(database).load(
        tenant_id,
        authenticated_principal(),
        evaluated_at=EVALUATED_AT,
    )

    assert context.principal_id == principal_id
    assert context.tenant_id == tenant_id
    assert context.evaluated_at == EVALUATED_AT
    assert len(context.memberships) == 1
    membership = context.memberships[0]
    assert membership.membership_id == membership_id
    assert membership.campaign_id == campaign_id
    assert membership.roles == ("admin", "viewer")
    assert len(membership.grants) == 1
    assert membership.grants[0].grant_id == grant_id
    assert context.permits(
        action="read",
        resource_type="campaign",
        resource_id=str(campaign_id),
        purpose="Operate assigned campaign",
        campaign_id=campaign_id,
    )

    assert not context.permits(
        action="write",
        resource_type="campaign",
        resource_id=str(campaign_id),
        purpose="Operate assigned campaign",
        campaign_id=campaign_id,
    )
    assert not context.permits(
        action="read",
        resource_type="campaign",
        resource_id=str(campaign_id),
        purpose="Operate assigned campaign",
        campaign_id=None,
    )
    assert not context.permits(
        action="read",
        resource_type="campaign",
        resource_id="different-resource",
        purpose="Operate assigned campaign",
        campaign_id=campaign_id,
    )
    assert not context.permits(
        action="read",
        resource_type="campaign",
        resource_id=str(campaign_id),
        purpose="Different purpose",
        campaign_id=campaign_id,
    )


def test_authorization_models_reject_malformed_scope_and_time() -> None:
    campaign_a = uuid4()
    campaign_b = uuid4()
    workspace_id = uuid4()
    grant_fields = {
        "grant_id": uuid4(),
        "action": "read",
        "resource_type": "campaign",
        "resource_id": str(campaign_a),
        "purpose": "Operate assigned campaign",
        "approval_receipt_id": "approval-123",
    }

    with pytest.raises(ValidationError, match="workspace-scoped grants require campaign"):
        EffectivePermissionGrant(
            **grant_fields,
            campaign_id=None,
            workspace_id=workspace_id,
        )

    cross_campaign_grant = EffectivePermissionGrant(
        **grant_fields,
        campaign_id=campaign_b,
        workspace_id=None,
    )
    with pytest.raises(ValidationError, match="must remain in campaign scope"):
        EffectiveMembership(
            membership_id=uuid4(),
            campaign_id=campaign_a,
            roles=("operator",),
            grants=(cross_campaign_grant,),
        )

    membership = EffectiveMembership(
        membership_id=uuid4(),
        campaign_id=campaign_b,
        roles=("operator",),
        grants=(cross_campaign_grant,),
    )
    with pytest.raises(ValidationError, match="at least 1 item"):
        TenantAuthorizationContext(
            principal_id=uuid4(),
            tenant_id=uuid4(),
            evaluated_at=EVALUATED_AT,
            memberships=(),
        )
    with pytest.raises(ValidationError, match="must include a timezone"):
        TenantAuthorizationContext(
            principal_id=uuid4(),
            tenant_id=uuid4(),
            evaluated_at=datetime(2026, 7, 19, 12),
            memberships=(membership,),
        )


def test_directory_rejects_naive_evaluation_time(database: Database) -> None:
    tenant_id, *_ = seed_active_authorization(database)

    with pytest.raises(AuthorizationDataError, match="must include a timezone"):
        SqlAlchemyMembershipDirectory(database).load(
            tenant_id,
            authenticated_principal(),
            evaluated_at=datetime(2026, 7, 19, 12),
        )


@pytest.mark.parametrize(
    ("tenant_status", "disabled_at", "membership_status"),
    [
        ("SUSPENDED", None, "ACTIVE"),
        ("ACTIVE", EVALUATED_AT - timedelta(minutes=1), "ACTIVE"),
        ("ACTIVE", None, "SUSPENDED"),
    ],
)
def test_denies_inactive_tenant_principal_or_membership(
    database: Database,
    tenant_status: str,
    disabled_at: datetime | None,
    membership_status: str,
) -> None:
    tenant_id, *_ = seed_active_authorization(
        database,
        tenant_status=tenant_status,
        principal_disabled_at=disabled_at,
        membership_status=membership_status,
    )

    with pytest.raises(TenantAccessDenied, match="not authorized"):
        SqlAlchemyMembershipDirectory(database).load(
            tenant_id,
            authenticated_principal(),
            evaluated_at=EVALUATED_AT,
        )


def test_denies_unknown_identity_or_tenant_without_revealing_which_is_missing(
    database: Database,
) -> None:
    tenant_id, *_ = seed_active_authorization(database)
    directory = SqlAlchemyMembershipDirectory(database)

    with pytest.raises(TenantAccessDenied, match="Tenant access is not authorized"):
        directory.load(
            tenant_id,
            authenticated_principal(subject="unknown"),
            evaluated_at=EVALUATED_AT,
        )
    with pytest.raises(TenantAccessDenied, match="Tenant access is not authorized"):
        directory.load(
            uuid4(),
            authenticated_principal(),
            evaluated_at=EVALUATED_AT,
        )


def test_excludes_expired_roles_and_inactive_grants(database: Database) -> None:
    tenant_id, principal_id, campaign_id, membership_id, _ = seed_active_authorization(database)
    with database.tenant_transaction(tenant_id) as session:
        session.add(
            RoleAssignment(
                tenant_id=tenant_id,
                membership_id=membership_id,
                role="expired-role",
                assigned_by_principal_id=principal_id,
                expires_at=EVALUATED_AT,
            )
        )
        session.add_all(
            [
                PermissionGrant(
                    tenant_id=tenant_id,
                    membership_id=membership_id,
                    campaign_id=campaign_id,
                    action="write",
                    resource_type="campaign",
                    resource_id=str(campaign_id),
                    purpose="Expired permission",
                    status="ACTIVE",
                    valid_from=EVALUATED_AT - timedelta(days=1),
                    expires_at=EVALUATED_AT,
                    granted_by_principal_id=principal_id,
                    approval_receipt_id="approval-expired",
                ),
                PermissionGrant(
                    tenant_id=tenant_id,
                    membership_id=membership_id,
                    campaign_id=campaign_id,
                    action="delete",
                    resource_type="campaign",
                    resource_id=str(campaign_id),
                    purpose="Revoked permission",
                    status="REVOKED",
                    valid_from=EVALUATED_AT - timedelta(days=1),
                    granted_by_principal_id=principal_id,
                    approval_receipt_id="approval-revoked",
                ),
                PermissionGrant(
                    tenant_id=tenant_id,
                    membership_id=membership_id,
                    campaign_id=campaign_id,
                    action="publish",
                    resource_type="campaign",
                    resource_id=str(campaign_id),
                    purpose="Future permission",
                    status="ACTIVE",
                    valid_from=EVALUATED_AT + timedelta(minutes=1),
                    granted_by_principal_id=principal_id,
                    approval_receipt_id="approval-future",
                ),
            ]
        )

    context = SqlAlchemyMembershipDirectory(database).load(
        tenant_id,
        authenticated_principal(),
        evaluated_at=EVALUATED_AT,
    )

    assert context.memberships[0].roles == ("admin", "viewer")
    assert [grant.action for grant in context.memberships[0].grants] == ["read"]


def test_tenant_membership_excludes_archived_campaign_and_workspace_grants(
    database: Database,
) -> None:
    tenant_id, _, campaign_id, membership_id, grant_id = seed_active_authorization(database)
    workspace_id = uuid4()
    with database.tenant_transaction(tenant_id) as session:
        membership = session.get(Membership, membership_id)
        campaign = session.get(Campaign, campaign_id)
        assert membership is not None
        assert campaign is not None
        membership.campaign_id = None
        campaign.status = "ARCHIVED"

    directory = SqlAlchemyMembershipDirectory(database)
    context = directory.load(
        tenant_id,
        authenticated_principal(),
        evaluated_at=EVALUATED_AT,
    )
    assert context.memberships[0].grants == ()

    with database.tenant_transaction(tenant_id) as session:
        campaign = session.get(Campaign, campaign_id)
        grant = session.get(PermissionGrant, grant_id)
        assert campaign is not None
        assert grant is not None
        campaign.status = "ACTIVE"
        session.add(
            Workspace(
                id=workspace_id,
                tenant_id=tenant_id,
                campaign_id=campaign_id,
                slug="archived-workspace",
                name="Archived workspace",
                status="ARCHIVED",
            )
        )
        grant.workspace_id = workspace_id

    context = directory.load(
        tenant_id,
        authenticated_principal(),
        evaluated_at=EVALUATED_AT,
    )
    assert context.memberships[0].grants == ()


def test_denies_expired_membership(database: Database) -> None:
    tenant_id, _, _, membership_id, _ = seed_active_authorization(database)
    with database.tenant_transaction(tenant_id) as session:
        membership = session.get(Membership, membership_id)
        assert membership is not None
        membership.expires_at = EVALUATED_AT

    with pytest.raises(TenantAccessDenied):
        SqlAlchemyMembershipDirectory(database).load(
            tenant_id,
            authenticated_principal(),
            evaluated_at=EVALUATED_AT,
        )


def test_rejects_cross_campaign_grant_corruption(database: Database) -> None:
    tenant_id, principal_id, _, membership_id, grant_id = seed_active_authorization(database)
    second_campaign_id = uuid4()
    with database.tenant_transaction(tenant_id) as session:
        session.add(
            Campaign(
                id=second_campaign_id,
                tenant_id=tenant_id,
                slug="campaign-b",
                name="Campaign B",
                jurisdiction="Test",
                stage="TEST",
                status="ACTIVE",
            )
        )
        grant = session.get(PermissionGrant, grant_id)
        assert grant is not None
        grant.campaign_id = second_campaign_id
        grant.granted_by_principal_id = principal_id

    with pytest.raises(AuthorizationDataError, match="out-of-scope"):
        SqlAlchemyMembershipDirectory(database).load(
            tenant_id,
            authenticated_principal(),
            evaluated_at=EVALUATED_AT,
        )


def test_persistence_failure_and_unconfigured_directory_fail_closed(database: Database) -> None:
    tenant_id, *_ = seed_active_authorization(database)
    directory = SqlAlchemyMembershipDirectory(database)
    database.dispose()

    with pytest.raises(AuthorizationDirectoryUnavailable, match="unavailable"):
        directory.load(
            tenant_id,
            authenticated_principal(),
            evaluated_at=EVALUATED_AT,
        )
    with pytest.raises(AuthorizationDirectoryUnavailable, match="unavailable"):
        UnavailableMembershipDirectory().load(tenant_id, authenticated_principal())
