from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from campaignos.api.app import create_app
from campaignos.config import Environment, Settings
from campaignos.identity.authorization import (
    EffectiveMembership,
    EffectivePermissionGrant,
    TenantAuthorizationContext,
)
from campaignos.identity.models import AuthenticatedPrincipal
from campaignos.training.catalog import CATALOG_DIGEST, project_catalog
from campaignos.training.contracts import (
    TrainingAssessmentOutcome,
    TrainingAssignmentCreateEvidence,
    TrainingAssignmentEvidence,
    TrainingAssignmentListEvidence,
    TrainingAssignmentProjection,
    TrainingAttemptEvidence,
    TrainingCompletionReceiptProjection,
    TrainingModuleProgressProjection,
    TrainingQuestionFeedback,
    TrainingReceiptListEvidence,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
PRINCIPAL_ID = UUID("33333333-3333-4333-8333-333333333333")
ASSIGNMENT_ID = UUID("44444444-4444-4444-8444-444444444444")
PROGRESS_ID = UUID("55555555-5555-4555-8555-555555555555")
GRANT_ID = UUID("66666666-6666-4666-8666-666666666666")
AUDIT_ID = UUID("77777777-7777-4777-8777-777777777777")
OUTBOX_ID = UUID("88888888-8888-4888-8888-888888888888")
RECEIPT_ID = UUID("99999999-9999-4999-8999-999999999999")


class Verifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        assert token == "valid-token"  # noqa: S105
        return AuthenticatedPrincipal(
            subject="training-user",
            issuer="https://identity.example.test/",
            audience="campaignos-test",
            authenticated_at=datetime(2026, 8, 1, 6, tzinfo=UTC),
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
        action: str,
        purpose: str,
        include_grant: bool = True,
        resource_type: str = "training_academy",
        campaign_id: UUID | None = CAMPAIGN_ID,
        workspace_id: UUID | None = None,
    ) -> None:
        self.action = action
        self.purpose = purpose
        self.include_grant = include_grant
        self.resource_type = resource_type
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
                    resource_id=str(CAMPAIGN_ID),
                    purpose=self.purpose,
                    approval_receipt_id="approval-training",
                ),
            )
        return TenantAuthorizationContext(
            principal_id=PRINCIPAL_ID,
            tenant_id=tenant_id,
            evaluated_at=datetime(2026, 8, 1, 6, tzinfo=UTC),
            memberships=(
                EffectiveMembership(
                    membership_id=UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"),
                    campaign_id=self.campaign_id,
                    roles=("label_only",),
                    grants=grants,
                ),
            ),
        )


def assignment(*, version: int = 1, status: str = "ASSIGNED") -> TrainingAssignmentProjection:
    return TrainingAssignmentProjection.model_validate(
        {
            "id": ASSIGNMENT_ID,
            "tenant_id": TENANT_ID,
            "campaign_id": CAMPAIGN_ID,
            "principal_id": PRINCIPAL_ID,
            "path_id": "research_foundations_path",
            "path_version": "1.0.0",
            "role_slug": "electoral_research",
            "status": status,
            "modules": (
                TrainingModuleProgressProjection.model_validate(
                    {
                        "id": PROGRESS_ID,
                        "module_id": "research_foundations",
                        "module_version": "1.0.0",
                        "status": "NOT_STARTED" if status == "ASSIGNED" else "IN_PROGRESS",
                        "attempt_count": 0,
                        "latest_result": None,
                        "started_at": None,
                        "completed_at": None,
                        "version": version,
                    }
                ),
            ),
            "completed_modules": 0,
            "total_modules": 1,
            "next_module_id": "research_foundations",
            "catalog_digest": CATALOG_DIGEST,
            "version": version,
            "assigned_at": datetime(2026, 8, 1, 6, tzinfo=UTC),
            "due_at": None,
            "completed_at": None,
        }
    )


class Service:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def catalog(self, locale: str):
        self.calls.append(("catalog", {"locale": locale}))
        return project_catalog(locale)  # type: ignore[arg-type]

    def list_self(self, *args: object, **kwargs: Any) -> TrainingAssignmentListEvidence:
        self.calls.append(("list_self", kwargs))
        return TrainingAssignmentListEvidence(assignments=(assignment(),), audit_event_id=AUDIT_ID)

    def create_assignment(self, *args: object, **kwargs: Any) -> TrainingAssignmentCreateEvidence:
        self.calls.append(("create_assignment", kwargs))
        return TrainingAssignmentCreateEvidence(
            assignment=assignment(), audit_event_id=AUDIT_ID, outbox_event_id=OUTBOX_ID
        )

    def get_assignment(self, *args: object, **kwargs: Any) -> TrainingAssignmentEvidence:
        self.calls.append(("get_assignment", kwargs))
        return TrainingAssignmentEvidence(assignment=assignment(), audit_event_id=AUDIT_ID)

    def start_module(self, *args: object, **kwargs: Any) -> TrainingAssignmentEvidence:
        self.calls.append(("start_module", kwargs))
        return TrainingAssignmentEvidence(
            assignment=assignment(version=2, status="IN_PROGRESS"),
            audit_event_id=AUDIT_ID,
        )

    def submit_attempt(self, *args: object, **kwargs: Any) -> TrainingAttemptEvidence:
        self.calls.append(("submit_attempt", kwargs))
        receipt = TrainingCompletionReceiptProjection(
            id=RECEIPT_ID,
            assignment_id=ASSIGNMENT_ID,
            module_progress_id=PROGRESS_ID,
            principal_id=PRINCIPAL_ID,
            module_id="research_foundations",
            module_version="1.0.0",
            result="PASS",
            completed_at=datetime(2026, 8, 1, 6, 5, tzinfo=UTC),
            catalog_digest=CATALOG_DIGEST,
            audit_event_id=AUDIT_ID,
        )
        return TrainingAttemptEvidence(
            assignment=assignment(version=3, status="IN_PROGRESS"),
            outcome=TrainingAssessmentOutcome(
                result="PASS",
                correct_count=1,
                total_questions=1,
                passing_percent=100,
                feedback=(
                    TrainingQuestionFeedback(
                        question_id="knowledge_check",
                        correct=True,
                        explanation="Reviewed explanation",
                    ),
                ),
            ),
            receipt=receipt,
            audit_event_id=AUDIT_ID,
        )

    def list_receipts(self, *args: object, **kwargs: Any) -> TrainingReceiptListEvidence:
        self.calls.append(("list_receipts", kwargs))
        return TrainingReceiptListEvidence(receipts=(), audit_event_id=AUDIT_ID)


def settings() -> Settings:
    return Settings(environment=Environment.TEST, expose_api_docs=True)


def client(directory: Directory, service: Service) -> TestClient:
    return TestClient(
        create_app(
            settings(),
            token_verifier=Verifier(),
            database=Database(),
            membership_directory=directory,
            training_service=service,  # type: ignore[arg-type]
        )
    )


def headers(*, key: str | None = None) -> dict[str, str]:
    result = {"Authorization": "Bearer valid-token", "X-Correlation-ID": "training-api"}
    if key is not None:
        result["Idempotency-Key"] = key
    return result


def root() -> str:
    return f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/training"


def test_catalog_requires_exact_grant_and_hides_answer_keys() -> None:
    service = Service()
    directory = Directory(
        action="training.catalog.read",
        purpose="Review approved training catalog",
    )
    with client(directory, service) as api:
        response = api.get(f"{root()}/catalog?locale=es", headers=headers())
    assert response.status_code == 200
    assert response.json()["modules"][0]["title"] == "Investigar antes de actuar"
    assert "correct_option_ids" not in response.text
    assert service.calls == [("catalog", {"locale": "es"})]


@pytest.mark.parametrize(
    "directory",
    [
        Directory(
            action="training.catalog.read",
            purpose="Review approved training catalog",
            include_grant=False,
        ),
        Directory(action="read", purpose="Review approved training catalog"),
        Directory(action="training.catalog.read", purpose="Different purpose"),
        Directory(
            action="training.catalog.read",
            purpose="Review approved training catalog",
            resource_type="campaign",
        ),
        Directory(
            action="training.catalog.read",
            purpose="Review approved training catalog",
            workspace_id=UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"),
        ),
    ],
)
def test_catalog_denies_mismatched_grant_before_service(directory: Directory) -> None:
    service = Service()
    with client(directory, service) as api:
        response = api.get(f"{root()}/catalog?locale=es", headers=headers())
    assert response.status_code == 403
    assert service.calls == []


def test_self_list_requires_self_grant_and_preserves_principal_scope() -> None:
    service = Service()
    directory = Directory(action="training.self.read", purpose="Review own campaign training")
    with client(directory, service) as api:
        response = api.get(f"{root()}/me", headers=headers())
    assert response.status_code == 200
    assert response.json()["assignments"][0]["principal_id"] == str(PRINCIPAL_ID)
    assert service.calls[0][0] == "list_self"
    assert service.calls[0][1]["principal_id"] == PRINCIPAL_ID


def test_assignment_creation_requires_idempotency_and_forwards_authority() -> None:
    service = Service()
    directory = Directory(
        action="training.assignment.manage",
        purpose="Assign campaign learning path",
    )
    payload = {
        "principal_id": str(PRINCIPAL_ID),
        "path_id": "research_foundations_path",
        "path_version": "1.0.0",
        "catalog_digest": CATALOG_DIGEST,
        "role_slug": "electoral_research",
    }
    with client(directory, service) as api:
        missing = api.post(f"{root()}/assignments", headers=headers(), json=payload)
        created = api.post(
            f"{root()}/assignments",
            headers=headers(key=" training-create "),
            json=payload,
        )
    assert missing.status_code == 428
    assert created.status_code == 201
    assert created.headers["etag"] == '"1"'
    assert created.json()["assignment"]["authority_effect"] == "NONE"
    operation, kwargs = service.calls[0]
    assert operation == "create_assignment"
    assert kwargs["principal_id"] == PRINCIPAL_ID
    assert kwargs["authorization_grant_id"] == GRANT_ID
    assert kwargs["approval_receipt_id"] == "approval-training"
    assert kwargs["idempotency_key"] == "training-create"


def test_self_start_attempt_and_receipts_use_distinct_exact_actions() -> None:
    service = Service()
    start_path = f"{root()}/assignments/{ASSIGNMENT_ID}/modules/research_foundations/start"
    attempt_path = f"{root()}/assignments/{ASSIGNMENT_ID}/modules/research_foundations/attempts"
    start_payload = {
        "expected_assignment_version": 1,
        "expected_progress_version": 1,
        "catalog_digest": CATALOG_DIGEST,
    }
    attempt_payload = {
        "locale": "es",
        "expected_assignment_version": 2,
        "expected_progress_version": 2,
        "catalog_digest": CATALOG_DIGEST,
        "answers": [{"question_id": "knowledge_check", "option_ids": ["correct"]}],
    }
    self_directory = Directory(
        action="training.self.complete",
        purpose="Complete assigned campaign training",
    )
    with client(self_directory, service) as api:
        started = api.post(start_path, headers=headers(key="start-key"), json=start_payload)
        attempted = api.post(attempt_path, headers=headers(key="attempt-key"), json=attempt_payload)
    assert started.status_code == 200
    assert attempted.status_code == 200
    assert attempted.json()["receipt"]["authority_effect"] == "NONE"
    assert [item[0] for item in service.calls] == ["start_module", "submit_attempt"]

    service = Service()
    receipt_directory = Directory(
        action="training.receipt.read",
        purpose="Review own campaign training",
    )
    with client(receipt_directory, service) as api:
        receipts = api.get(
            f"{root()}/me/assignments/{ASSIGNMENT_ID}/receipts",
            headers=headers(),
        )
    assert receipts.status_code == 200
    assert service.calls[0][0] == "list_receipts"


def test_openapi_declares_training_security_and_idempotency_headers() -> None:
    directory = Directory(
        action="training.catalog.read",
        purpose="Review approved training catalog",
    )
    with client(directory, Service()) as api:
        schema = api.get("/api/v1/openapi.json").json()
    catalog_operation = schema["paths"][
        "/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/training/catalog"
    ]["get"]
    create_operation = schema["paths"][
        "/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/training/assignments"
    ]["post"]
    assert catalog_operation["security"] == [{"OIDC bearer token": []}]
    assert create_operation["security"] == [{"OIDC bearer token": []}]
    assert "Idempotency-Key" in {item["name"] for item in create_operation["parameters"]}
