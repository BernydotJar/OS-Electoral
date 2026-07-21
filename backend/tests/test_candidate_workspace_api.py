from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from campaignos.api.app import create_app
from campaignos.candidates import (
    CandidateSectionApproval,
    CandidateSectionApprovalRequest,
    CandidateWorkspaceApprovalEvidence,
    CandidateWorkspaceAssessmentInput,
    CandidateWorkspaceCreate,
    CandidateWorkspaceCreateEvidence,
    CandidateWorkspaceReadEvidence,
    CandidateWorkspaceUpdate,
    CandidateWorkspaceUpdateEvidence,
    assess_candidate_workspace,
)
from campaignos.candidates.service import (
    CandidateWorkspaceApprovalConflict,
    CandidateWorkspaceConflict,
    CandidateWorkspaceEvidenceConflict,
    CandidateWorkspaceIdempotencyConflict,
    CandidateWorkspaceNotFound,
    CandidateWorkspacePrerequisiteConflict,
    CandidateWorkspaceUnavailable,
    CandidateWorkspaceVersionConflict,
)
from campaignos.config import Environment, Settings
from campaignos.identity.authorization import (
    EffectiveMembership,
    EffectivePermissionGrant,
    TenantAuthorizationContext,
)
from campaignos.identity.models import AuthenticatedPrincipal

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
FOREIGN_CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")
PRINCIPAL_ID = UUID("44444444-4444-4444-8444-444444444444")
MEMBERSHIP_ID = UUID("55555555-5555-4555-8555-555555555555")
GRANT_ID = UUID("66666666-6666-4666-8666-666666666666")
WORKSPACE_ID = UUID("77777777-7777-4777-8777-777777777777")
CANDIDATE_ID = UUID("88888888-8888-4888-8888-888888888888")
AUDIT_ID = UUID("99999999-9999-4999-8999-999999999999")
OUTBOX_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
APPROVAL_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
CREATE_PURPOSE = "Create candidate evidence workspace"
READ_PURPOSE = "Review candidate evidence workspace"
UPDATE_PURPOSE = "Maintain candidate evidence workspace"
APPROVE_PURPOSE = "Approve candidate evidence section"


class Verifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        assert token == "valid-token"  # noqa: S105 - deterministic fixture.
        return AuthenticatedPrincipal(
            subject="candidate-workspace-reviewer",
            issuer="https://identity.example.test/",
            audience="campaignos-test",
            authenticated_at=datetime(2026, 7, 21, 22, tzinfo=UTC),
        )

    def readiness(self) -> tuple[bool, str]:
        return True, "ready"


class Database:
    def readiness(self) -> tuple[bool, str]:
        return True, "ready"

    def dispose(self) -> None:
        return None


class Directory:
    def __init__(
        self,
        *,
        include_grant: bool = True,
        action: str = "create",
        purpose: str = CREATE_PURPOSE,
        resource_type: str = "candidate_workspace",
        resource_id: str = str(CAMPAIGN_ID),
        campaign_id: UUID | None = CAMPAIGN_ID,
        workspace_id: UUID | None = None,
    ) -> None:
        self.include_grant = include_grant
        self.action = action
        self.purpose = purpose
        self.resource_type = resource_type
        self.resource_id = resource_id
        self.campaign_id = campaign_id
        self.workspace_id = workspace_id

    def load(
        self,
        tenant_id: UUID,
        principal: AuthenticatedPrincipal,
        *,
        evaluated_at: datetime | None = None,
    ) -> TenantAuthorizationContext:
        del principal, evaluated_at
        grants: tuple[EffectivePermissionGrant, ...] = ()
        if self.include_grant:
            grants = (
                EffectivePermissionGrant(
                    grant_id=GRANT_ID,
                    campaign_id=self.campaign_id,
                    workspace_id=self.workspace_id,
                    action=self.action,
                    resource_type=self.resource_type,
                    resource_id=self.resource_id,
                    purpose=self.purpose,
                    approval_receipt_id="approval-candidate-workspace",
                ),
            )
        return TenantAuthorizationContext(
            principal_id=PRINCIPAL_ID,
            tenant_id=tenant_id,
            evaluated_at=datetime(2026, 7, 21, 22, tzinfo=UTC),
            memberships=(
                EffectiveMembership(
                    membership_id=MEMBERSHIP_ID,
                    campaign_id=self.campaign_id,
                    roles=("candidate_reviewer_label_only",),
                    grants=grants,
                ),
            ),
        )


def projection(
    *,
    version: int = 1,
    tenant_id: UUID = TENANT_ID,
    campaign_id: UUID = CAMPAIGN_ID,
):
    return assess_candidate_workspace(
        CandidateWorkspaceAssessmentInput(
            id=WORKSPACE_ID,
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            campaign_version=3,
            campaign_status="ACTIVE",
            campaign_name="Campaign",
            jurisdiction="Antigua Guatemala",
            candidate_id=CANDIDATE_ID,
            display_name="Candidatura sintética",
            evidence=(),
            identity=None,
            biography=None,
            purpose=None,
            values=None,
            attributes=None,
            contradictions=None,
            development_goals=None,
            reputation_risks=None,
            approvals=(),
            version=version,
            created_at=datetime(2026, 7, 21, 22, tzinfo=UTC),
            updated_at=datetime(2026, 7, 21, 22, tzinfo=UTC),
        )
    )


class Service:
    def __init__(
        self,
        *,
        failure: Exception | None = None,
        tenant_id: UUID = TENANT_ID,
        campaign_id: UUID = CAMPAIGN_ID,
    ) -> None:
        self.failure = failure
        self.tenant_id = tenant_id
        self.campaign_id = campaign_id
        self.calls: list[tuple[str, tuple[object, ...], dict[str, Any]]] = []

    def create(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> CandidateWorkspaceCreateEvidence:
        self.calls.append(("create", (tenant_id, campaign_id), kwargs))
        if self.failure is not None:
            raise self.failure
        return CandidateWorkspaceCreateEvidence(
            workspace=projection(tenant_id=self.tenant_id, campaign_id=self.campaign_id),
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )

    def get(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> CandidateWorkspaceReadEvidence:
        self.calls.append(("get", (tenant_id, campaign_id), kwargs))
        if self.failure is not None:
            raise self.failure
        return CandidateWorkspaceReadEvidence(
            workspace=projection(tenant_id=self.tenant_id, campaign_id=self.campaign_id),
            audit_event_id=AUDIT_ID,
        )

    def update(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> CandidateWorkspaceUpdateEvidence:
        self.calls.append(("update", (tenant_id, campaign_id), kwargs))
        if self.failure is not None:
            raise self.failure
        return CandidateWorkspaceUpdateEvidence(
            workspace=projection(
                version=int(kwargs["expected_version"]) + 1,
                tenant_id=self.tenant_id,
                campaign_id=self.campaign_id,
            ),
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )

    def approve_section(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> CandidateWorkspaceApprovalEvidence:
        self.calls.append(("approve_section", (tenant_id, campaign_id), kwargs))
        if self.failure is not None:
            raise self.failure
        return CandidateWorkspaceApprovalEvidence(
            workspace=projection(
                version=int(kwargs["expected_version"]),
                tenant_id=self.tenant_id,
                campaign_id=self.campaign_id,
            ),
            approval=CandidateSectionApproval(
                id=APPROVAL_ID,
                section=kwargs["request"].section,
                approved_version=int(kwargs["expected_version"]),
                principal_id=PRINCIPAL_ID,
                authorization_grant_id=GRANT_ID,
                approval_receipt_id="approval-candidate-workspace",
                reason=kwargs["request"].reason,
                approved_at=datetime(2026, 7, 21, 22, tzinfo=UTC),
            ),
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )


def settings() -> Settings:
    return Settings(environment=Environment.TEST, expose_api_docs=True)


def client(directory: Directory, service: Service) -> TestClient:
    return TestClient(
        create_app(
            settings(),
            token_verifier=Verifier(),
            database=Database(),
            membership_directory=directory,
            candidate_workspace_service=service,
        )
    )


def headers(*, idempotency_key: str | None = None, if_match: str | None = None) -> dict[str, str]:
    values = {
        "Authorization": "Bearer valid-token",
        "X-Correlation-ID": "candidate-workspace-api",
    }
    if idempotency_key is not None:
        values["Idempotency-Key"] = idempotency_key
    if if_match is not None:
        values["If-Match"] = if_match
    return values


def path() -> str:
    return f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/candidate-workspace"


def test_create_requires_exact_grant_and_forwards_authority() -> None:
    service = Service()
    with client(Directory(), service) as api:
        response = api.post(
            path(),
            headers=headers(idempotency_key="  candidate-create  "),
            json={"display_name": "  Candidatura   sintética  "},
        )

    assert response.status_code == 201
    assert response.headers["location"].endswith("/candidate-workspace")
    assert response.headers["etag"] == '"1"'
    assert response.json()["workspace"]["candidate_id"] == str(CANDIDATE_ID)
    assert len(service.calls) == 1
    operation, scope, kwargs = service.calls[0]
    assert operation == "create"
    assert scope == (TENANT_ID, CAMPAIGN_ID)
    assert kwargs == {
        "request": CandidateWorkspaceCreate(display_name="Candidatura sintética"),
        "principal_id": PRINCIPAL_ID,
        "authorization_grant_id": GRANT_ID,
        "approval_receipt_id": "approval-candidate-workspace",
        "authorization_purpose": CREATE_PURPOSE,
        "correlation_id": "candidate-workspace-api",
        "idempotency_key": "candidate-create",
    }


@pytest.mark.parametrize(
    "directory",
    [
        Directory(include_grant=False),
        Directory(action="read"),
        Directory(purpose="Different purpose"),
        Directory(resource_type="campaign"),
        Directory(resource_id=str(FOREIGN_CAMPAIGN_ID)),
        Directory(campaign_id=FOREIGN_CAMPAIGN_ID),
        Directory(workspace_id=UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")),
    ],
)
def test_create_denies_mismatched_grant_before_service(directory: Directory) -> None:
    service = Service()
    with client(directory, service) as api:
        response = api.post(
            path(),
            headers=headers(idempotency_key="candidate-denied"),
            json={"display_name": "Candidate"},
        )
    assert response.status_code == 403
    assert service.calls == []


def test_create_requires_one_bounded_idempotency_key() -> None:
    for request_headers, expected_status in (
        ([("Authorization", "Bearer valid-token")], 428),
        (
            [
                ("Authorization", "Bearer valid-token"),
                ("Idempotency-Key", "one"),
                ("Idempotency-Key", "two"),
            ],
            428,
        ),
        (
            [
                ("Authorization", "Bearer valid-token"),
                ("Idempotency-Key", "x" * 256),
            ],
            400,
        ),
    ):
        service = Service()
        with client(Directory(), service) as api:
            response = api.post(
                path(),
                headers=request_headers,
                json={"display_name": "Candidate"},
            )
        assert response.status_code == expected_status
        assert service.calls == []


def test_read_update_and_approval_use_separate_exact_purposes() -> None:
    read_service = Service()
    with client(Directory(action="read", purpose=READ_PURPOSE), read_service) as api:
        read = api.get(path(), headers=headers())
    assert read.status_code == 200
    assert read.headers["etag"] == '"1"'
    assert read_service.calls[0][0] == "get"
    assert read_service.calls[0][2]["authorization_purpose"] == READ_PURPOSE

    update_service = Service()
    with client(Directory(action="update", purpose=UPDATE_PURPOSE), update_service) as api:
        update = api.patch(
            path(),
            headers=headers(idempotency_key="candidate-update", if_match='"1"'),
            json={"display_name": "  Updated   candidate  ", "values": []},
        )
    assert update.status_code == 200
    assert update.headers["etag"] == '"2"'
    assert update_service.calls[0][2]["changes"] == CandidateWorkspaceUpdate(
        display_name="Updated candidate",
        values=[],
    )

    approval_service = Service()
    with client(Directory(action="approve", purpose=APPROVE_PURPOSE), approval_service) as api:
        approval = api.post(
            f"{path()}/section-approvals",
            headers=headers(idempotency_key="candidate-approve", if_match='"2"'),
            json={
                "section": "biography",
                "reason": "  Evidence reviewed for internal use only.  ",
            },
        )
    assert approval.status_code == 201
    assert approval.headers["etag"] == '"2"'
    kwargs = approval_service.calls[0][2]
    assert kwargs["request"] == CandidateSectionApprovalRequest(
        section="biography",
        reason="Evidence reviewed for internal use only.",
    )
    assert kwargs["authorization_purpose"] == APPROVE_PURPOSE


def test_update_and_approval_require_version_and_idempotency_preconditions() -> None:
    for method_path, directory, body in (
        (
            path(),
            Directory(action="update", purpose=UPDATE_PURPOSE),
            {"display_name": "Candidate"},
        ),
        (
            f"{path()}/section-approvals",
            Directory(action="approve", purpose=APPROVE_PURPOSE),
            {"section": "identity", "reason": "Reviewed."},
        ),
    ):
        for request_headers, expected_status in (
            ({"Idempotency-Key": "key"}, 428),
            ({"If-Match": '"1"'}, 428),
            ({"Idempotency-Key": "key", "If-Match": "invalid"}, 400),
        ):
            service = Service()
            merged = {"Authorization": "Bearer valid-token", **request_headers}
            with client(directory, service) as api:
                response = api.request(
                    "PATCH" if method_path == path() else "POST",
                    method_path,
                    headers=merged,
                    json=body,
                )
            assert response.status_code == expected_status
            assert service.calls == []


@pytest.mark.parametrize(
    ("failure", "status_code", "code"),
    [
        (CandidateWorkspaceIdempotencyConflict("private"), 409, "IDEMPOTENCY_CONFLICT"),
        (CandidateWorkspacePrerequisiteConflict("private"), 409, "CAMPAIGN_NOT_READY"),
        (CandidateWorkspaceConflict("private"), 409, "CANDIDATE_WORKSPACE_CONFLICT"),
        (CandidateWorkspaceEvidenceConflict("private"), 409, "CANDIDATE_WORKSPACE_CONFLICT"),
        (CandidateWorkspaceApprovalConflict("private"), 409, "CANDIDATE_WORKSPACE_CONFLICT"),
        (CandidateWorkspaceVersionConflict("private"), 412, "VERSION_CONFLICT"),
        (CandidateWorkspaceNotFound("private"), 404, "RESOURCE_NOT_FOUND"),
        (CandidateWorkspaceUnavailable("private"), 503, "AUTHORIZATION_UNAVAILABLE"),
    ],
)
def test_failures_are_sanitized(failure: Exception, status_code: int, code: str) -> None:
    directory = Directory()
    method = "POST"
    url = path()
    request_headers = headers(idempotency_key="candidate-failure")
    request_body: dict[str, object] = {"display_name": "Candidate"}
    if isinstance(
        failure,
        (CandidateWorkspaceEvidenceConflict, CandidateWorkspaceVersionConflict),
    ):
        directory = Directory(action="update", purpose=UPDATE_PURPOSE)
        method = "PATCH"
        request_headers = headers(idempotency_key="candidate-failure", if_match='"1"')
        request_body = {"display_name": "Updated"}
    elif isinstance(failure, CandidateWorkspaceApprovalConflict):
        directory = Directory(action="approve", purpose=APPROVE_PURPOSE)
        url = f"{path()}/section-approvals"
        request_headers = headers(idempotency_key="candidate-failure", if_match='"1"')
        request_body = {"section": "identity", "reason": "Reviewed."}
    with client(directory, Service(failure=failure)) as api:
        response = api.request(
            method,
            url,
            headers=request_headers,
            json=request_body,
        )
    assert response.status_code == status_code
    assert response.json()["code"] == code
    assert "private" not in response.text


@pytest.mark.parametrize("operation", ["create", "get", "update", "approve"])
def test_adapter_scope_drift_fails_closed(operation: str) -> None:
    service = Service(campaign_id=FOREIGN_CAMPAIGN_ID)
    if operation == "create":
        directory = Directory()
        method = "post"
        url = path()
        kwargs: dict[str, object] = {
            "headers": headers(idempotency_key="key"),
            "json": {"display_name": "Candidate"},
        }
    elif operation == "get":
        directory = Directory(action="read", purpose=READ_PURPOSE)
        method = "get"
        url = path()
        kwargs = {"headers": headers()}
    elif operation == "update":
        directory = Directory(action="update", purpose=UPDATE_PURPOSE)
        method = "patch"
        url = path()
        kwargs = {
            "headers": headers(idempotency_key="key", if_match='"1"'),
            "json": {"display_name": "Candidate"},
        }
    else:
        directory = Directory(action="approve", purpose=APPROVE_PURPOSE)
        method = "post"
        url = f"{path()}/section-approvals"
        kwargs = {
            "headers": headers(idempotency_key="key", if_match='"1"'),
            "json": {"section": "identity", "reason": "Reviewed."},
        }
    with client(directory, service) as api:
        response = getattr(api, method)(url, **kwargs)
    assert response.status_code == 503


def test_openapi_declares_bearer_security_and_precondition_headers() -> None:
    with client(Directory(), Service()) as api:
        schema = api.get("/api/v1/openapi.json").json()
    candidate = schema["paths"][
        "/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/candidate-workspace"
    ]
    approvals = schema["paths"][
        "/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/candidate-workspace/section-approvals"
    ]
    assert candidate["post"]["security"] == [{"OIDC bearer token": []}]
    assert candidate["get"]["security"] == [{"OIDC bearer token": []}]
    assert candidate["patch"]["security"] == [{"OIDC bearer token": []}]
    assert approvals["post"]["security"] == [{"OIDC bearer token": []}]
    assert "Idempotency-Key" in {item["name"] for item in candidate["post"]["parameters"]}
    assert {"Idempotency-Key", "If-Match"} <= {
        item["name"] for item in candidate["patch"]["parameters"]
    }
    assert {"Idempotency-Key", "If-Match"} <= {
        item["name"] for item in approvals["post"]["parameters"]
    }
