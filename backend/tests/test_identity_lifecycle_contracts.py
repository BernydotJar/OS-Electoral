from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from campaignos.identity.lifecycle_contracts import (
    CognitoInvitationPlanner,
    InvitationCreate,
    LocalInvitationPlanner,
    SupportAccessCreate,
    normalize_email,
)

INVITATION_ID = UUID("11111111-1111-4111-8111-111111111111")
TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")
WORKSPACE_ID = UUID("44444444-4444-4444-8444-444444444444")
EXPIRES_AT = datetime(2026, 7, 22, 12, tzinfo=UTC)


def test_invitation_request_normalizes_email_and_bounds_expiry() -> None:
    request = InvitationCreate(
        email="  Operator@Example.Test ",
        campaign_id=CAMPAIGN_ID,
        expires_in_hours=24,
    )

    assert request.email == "operator@example.test"
    assert normalize_email(" OPERATOR@example.test ") == request.email
    for value in ("missing-at", "a @example.test", "@example.test"):
        with pytest.raises((ValidationError, ValueError)):
            InvitationCreate(email=value)
    with pytest.raises(ValidationError):
        InvitationCreate(email="operator@example.test", expires_in_hours=169)


def test_local_plan_is_inert_and_contains_no_secret() -> None:
    plan = LocalInvitationPlanner().plan(
        invitation_id=INVITATION_ID,
        tenant_id=TENANT_ID,
        campaign_id=CAMPAIGN_ID,
        email="operator@example.test",
        expires_at=EXPIRES_AT,
    )

    assert plan.provider == "LOCAL_NO_DELIVERY"
    assert plan.delivery_state == "NOT_SENT"
    assert plan.external_effects == "NONE"
    assert plan.request_payload["delivery"] == "DISABLED"
    rendered = plan.model_dump_json().lower()
    assert "password" not in rendered
    assert "token" not in rendered


def test_cognito_plan_is_admin_create_user_request_data_only() -> None:
    plan = CognitoInvitationPlanner("us-east-1_campaignosTest").plan(
        invitation_id=INVITATION_ID,
        tenant_id=TENANT_ID,
        campaign_id=None,
        email="operator@example.test",
        expires_at=EXPIRES_AT,
    )

    assert plan.provider == "AWS_COGNITO_PLAN_ONLY"
    assert plan.operation == "cognito-idp:AdminCreateUser"
    assert plan.delivery_state == "NOT_SENT"
    assert plan.external_effects == "NONE"
    assert plan.request_payload["MessageAction"] == "SUPPRESS"
    assert plan.request_payload["Username"] == "operator@example.test"
    assert plan.request_payload["ClientMetadata"]["campaignos_campaign_id"] == "TENANT"
    rendered = plan.model_dump_json().lower()
    assert "temporarypassword" not in rendered
    assert "secret" not in rendered


def test_support_request_normalizes_text_and_requires_complete_scope() -> None:
    request = SupportAccessCreate(
        target_principal_id=INVITATION_ID,
        campaign_id=CAMPAIGN_ID,
        workspace_id=WORKSPACE_ID,
        action="  read ",
        resource_type=" campaign_readiness ",
        resource_id=str(CAMPAIGN_ID),
        purpose="  Diagnose   assigned campaign ",
        reason="  Reproduce   a customer-reported authorization defect. ",
        expires_in_minutes=30,
    )

    assert request.action == "read"
    assert request.purpose == "Diagnose assigned campaign"
    assert request.reason == "Reproduce a customer-reported authorization defect."
    with pytest.raises(ValidationError, match="requires campaign scope"):
        SupportAccessCreate(
            target_principal_id=INVITATION_ID,
            workspace_id=WORKSPACE_ID,
            action="read",
            resource_type="campaign",
            resource_id=str(CAMPAIGN_ID),
            purpose="Diagnose assigned campaign",
            reason="Reproduce an authorized support defect.",
        )
