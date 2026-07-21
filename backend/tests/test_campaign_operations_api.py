from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

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
from campaignos.operations import (
    CampaignRoadmapAssessmentInput,
    CampaignRoadmapCreateEvidence,
    CampaignRoadmapReadEvidence,
    CampaignRoadmapUpdateEvidence,
    WarRoomSnapshotEvidence,
    assess_campaign_roadmap,
    build_war_room_snapshot,
)
from campaignos.operations.service import (
    CampaignRoadmapConflict,
    CampaignRoadmapEvidenceConflict,
    CampaignRoadmapIdempotencyConflict,
    CampaignRoadmapNotFound,
    CampaignRoadmapPrerequisiteConflict,
    CampaignRoadmapUnavailable,
    CampaignRoadmapVersionConflict,
    WarRoomSnapshotConflict,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
FOREIGN_CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")
PRINCIPAL_ID = UUID("44444444-4444-4444-8444-444444444444")
MEMBERSHIP_ID = UUID("55555555-5555-4555-8555-555555555555")
GRANT_ID = UUID("66666666-6666-4666-8666-666666666666")
ROADMAP_ID = UUID("77777777-7777-4777-8777-777777777777")
AUDIT_ID = UUID("88888888-8888-4888-8888-888888888888")
OUTBOX_ID = UUID("99999999-9999-4999-8999-999999999999")
CREATE_PURPOSE = "Create campaign operations roadmap"
READ_PURPOSE = "Review campaign operations roadmap"
UPDATE_PURPOSE = "Maintain campaign operations roadmap"
SNAPSHOT_PURPOSE = "Create daily campaign war room snapshot"


class Verifier:
    def verify(self, token: str) -> AuthenticatedPrincipal:
        assert token == "valid-token"  # noqa: S105 - fixture.
        return AuthenticatedPrincipal(
            subject="operations-user",
            issuer="https://identity.example.test/",
            audience="campaignos-test",
            authenticated_at=datetime(2026, 7, 21, 23, 55, tzinfo=UTC),
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
        resource_type: str = "campaign_roadmap",
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
                    approval_receipt_id="approval-operations",
                ),
            )
        return TenantAuthorizationContext(
            principal_id=PRINCIPAL_ID,
            tenant_id=tenant_id,
            evaluated_at=datetime(2026, 7, 21, 23, 55, tzinfo=UTC),
            memberships=(
                EffectiveMembership(
                    membership_id=MEMBERSHIP_ID,
                    campaign_id=self.campaign_id,
                    roles=("campaign_director_label_only",),
                    grants=grants,
                ),
            ),
        )


def roadmap(*, version: int = 1, campaign_id: UUID = CAMPAIGN_ID):
    return assess_campaign_roadmap(
        CampaignRoadmapAssessmentInput(
            id=ROADMAP_ID,
            tenant_id=TENANT_ID,
            campaign_id=campaign_id,
            campaign_version=5,
            campaign_status="ACTIVE",
            campaign_name="Campaign",
            title="Campaign roadmap",
            team_role_ids=(GRANT_ID,),
            phases=None,
            workstreams=None,
            milestones=None,
            tasks=None,
            blockers=None,
            decisions=None,
            follow_up_items=None,
            learning_notes=None,
            version=version,
            created_at=datetime(2026, 7, 21, 23, 55, tzinfo=UTC),
            updated_at=datetime(2026, 7, 21, 23, 55, tzinfo=UTC),
        )
    )


class Service:
    def __init__(
        self, *, failure: Exception | None = None, campaign_id: UUID = CAMPAIGN_ID
    ) -> None:
        self.failure = failure
        self.campaign_id = campaign_id
        self.calls: list[tuple[str, tuple[object, ...], dict[str, Any]]] = []

    def _raise(self) -> None:
        if self.failure is not None:
            raise self.failure

    def create_roadmap(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> CampaignRoadmapCreateEvidence:
        self.calls.append(("create", (tenant_id, campaign_id), kwargs))
        self._raise()
        return CampaignRoadmapCreateEvidence(
            roadmap=roadmap(campaign_id=self.campaign_id),
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )

    def get_roadmap(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> CampaignRoadmapReadEvidence:
        self.calls.append(("get", (tenant_id, campaign_id), kwargs))
        self._raise()
        return CampaignRoadmapReadEvidence(
            roadmap=roadmap(campaign_id=self.campaign_id), audit_event_id=AUDIT_ID
        )

    def update_roadmap(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> CampaignRoadmapUpdateEvidence:
        self.calls.append(("update", (tenant_id, campaign_id), kwargs))
        self._raise()
        return CampaignRoadmapUpdateEvidence(
            roadmap=roadmap(
                version=int(kwargs["expected_version"]) + 1, campaign_id=self.campaign_id
            ),
            audit_event_id=AUDIT_ID,
            outbox_event_id=OUTBOX_ID,
        )

    def create_snapshot(
        self, tenant_id: UUID, campaign_id: UUID, **kwargs: Any
    ) -> WarRoomSnapshotEvidence:
        self.calls.append(("snapshot", (tenant_id, campaign_id), kwargs))
        self._raise()
        snapshot = build_war_room_snapshot(
            roadmap(campaign_id=self.campaign_id),
            request=kwargs["request"],
            snapshot_id=uuid4(),
            created_at=datetime(2026, 7, 21, 23, 55, tzinfo=UTC),
        )
        return WarRoomSnapshotEvidence(
            snapshot=snapshot, audit_event_id=AUDIT_ID, outbox_event_id=OUTBOX_ID
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
            campaign_operations_service=service,
        )
    )


def headers(*, key: str | None = None, version: str | None = None) -> dict[str, str]:
    result = {"Authorization": "Bearer valid-token", "X-Correlation-ID": "operations-api"}
    if key is not None:
        result["Idempotency-Key"] = key
    if version is not None:
        result["If-Match"] = version
    return result


def roadmap_path() -> str:
    return f"/api/v1/tenants/{TENANT_ID}/campaigns/{CAMPAIGN_ID}/operations/roadmap"


def snapshot_path() -> str:
    return f"{roadmap_path()}/war-room-snapshots"


def test_create_forwards_exact_authority_and_returns_headers() -> None:
    service = Service()
    with client(Directory(), service) as api:
        response = api.post(
            roadmap_path(),
            headers=headers(key=" roadmap-create "),
            json={"title": "Campaign roadmap"},
        )
    assert response.status_code == 201
    assert response.headers["etag"] == '"1"'
    assert response.json()["roadmap"]["external_effects"] == "NONE"
    assert service.calls[0][2]["idempotency_key"] == "roadmap-create"
    assert service.calls[0][2]["authorization_purpose"] == CREATE_PURPOSE


@pytest.mark.parametrize(
    "directory",
    [
        Directory(include_grant=False),
        Directory(action="read"),
        Directory(purpose="wrong"),
        Directory(resource_type="team_workspace"),
        Directory(resource_id=str(FOREIGN_CAMPAIGN_ID)),
        Directory(campaign_id=FOREIGN_CAMPAIGN_ID),
        Directory(workspace_id=uuid4()),
    ],
)
def test_create_denies_mismatch_before_adapter(directory: Directory) -> None:
    service = Service()
    with client(directory, service) as api:
        response = api.post(
            roadmap_path(), headers=headers(key="denied"), json={"title": "Roadmap"}
        )
    assert response.status_code == 403
    assert service.calls == []


def test_read_update_and_snapshot_use_separate_exact_purposes() -> None:
    read_service = Service()
    with client(Directory(action="read", purpose=READ_PURPOSE), read_service) as api:
        response = api.get(roadmap_path(), headers=headers())
    assert response.status_code == 200
    assert read_service.calls[0][2]["authorization_purpose"] == READ_PURPOSE

    update_service = Service()
    with client(Directory(action="update", purpose=UPDATE_PURPOSE), update_service) as api:
        response = api.patch(
            roadmap_path(), headers=headers(key="update", version='"1"'), json={"tasks": []}
        )
    assert response.status_code == 200
    assert update_service.calls[0][2]["authorization_purpose"] == UPDATE_PURPOSE

    snapshot_service = Service()
    with client(
        Directory(action="create", purpose=SNAPSHOT_PURPOSE, resource_type="war_room_snapshot"),
        snapshot_service,
    ) as api:
        response = api.post(
            snapshot_path(),
            headers=headers(key="snapshot", version='"1"'),
            json={
                "snapshot_date": "2026-07-22",
                "priorities": ["Review evidence"],
                "follow_up_notes": [],
            },
        )
    assert response.status_code == 201
    assert response.json()["snapshot"]["roadmap_version"] == 1
    assert snapshot_service.calls[0][2]["authorization_purpose"] == SNAPSHOT_PURPOSE


def test_write_preconditions_are_required() -> None:
    service = Service()
    with client(Directory(), service) as api:
        assert (
            api.post(roadmap_path(), headers=headers(), json={"title": "Roadmap"}).status_code
            == 428
        )
    with client(Directory(action="update", purpose=UPDATE_PURPOSE), service) as api:
        assert (
            api.patch(roadmap_path(), headers=headers(key="k"), json={"tasks": []}).status_code
            == 428
        )
    with client(
        Directory(action="create", purpose=SNAPSHOT_PURPOSE, resource_type="war_room_snapshot"),
        service,
    ) as api:
        assert (
            api.post(
                snapshot_path(),
                headers=headers(key="k"),
                json={
                    "snapshot_date": "2026-07-22",
                    "priorities": ["Review"],
                    "follow_up_notes": [],
                },
            ).status_code
            == 428
        )


@pytest.mark.parametrize(
    ("failure", "method", "status_code", "code"),
    [
        (CampaignRoadmapIdempotencyConflict("private"), "POST", 409, "IDEMPOTENCY_CONFLICT"),
        (CampaignRoadmapPrerequisiteConflict("private"), "POST", 409, "CAMPAIGN_NOT_READY"),
        (CampaignRoadmapConflict("private"), "POST", 409, "ROADMAP_CONFLICT"),
        (CampaignRoadmapEvidenceConflict("private"), "PATCH", 409, "ROADMAP_CONFLICT"),
        (CampaignRoadmapVersionConflict("private"), "PATCH", 412, "VERSION_CONFLICT"),
        (CampaignRoadmapNotFound("private"), "POST", 404, "RESOURCE_NOT_FOUND"),
        (CampaignRoadmapUnavailable("private"), "POST", 503, "AUTHORIZATION_UNAVAILABLE"),
        (WarRoomSnapshotConflict("private"), "SNAPSHOT", 409, "WAR_ROOM_SNAPSHOT_CONFLICT"),
    ],
)
def test_failures_are_sanitized(
    failure: Exception, method: str, status_code: int, code: str
) -> None:
    service = Service(failure=failure)
    if method == "PATCH":
        directory = Directory(action="update", purpose=UPDATE_PURPOSE)
        path = roadmap_path()
        kwargs = {"headers": headers(key="k", version='"1"'), "json": {"tasks": []}}
        verb = "patch"
    elif method == "SNAPSHOT":
        directory = Directory(
            action="create", purpose=SNAPSHOT_PURPOSE, resource_type="war_room_snapshot"
        )
        path = snapshot_path()
        kwargs = {
            "headers": headers(key="k", version='"1"'),
            "json": {
                "snapshot_date": "2026-07-22",
                "priorities": ["Review"],
                "follow_up_notes": [],
            },
        }
        verb = "post"
    else:
        directory = Directory()
        path = roadmap_path()
        kwargs = {"headers": headers(key="k"), "json": {"title": "Roadmap"}}
        verb = "post"
    with client(directory, service) as api:
        response = getattr(api, verb)(path, **kwargs)
    assert response.status_code == status_code
    assert response.json()["code"] == code
    assert "private" not in response.text


def test_adapter_scope_drift_fails_closed() -> None:
    service = Service(campaign_id=FOREIGN_CAMPAIGN_ID)
    with client(Directory(), service) as api:
        response = api.post(roadmap_path(), headers=headers(key="drift"), json={"title": "Roadmap"})
    assert response.status_code == 503


def test_openapi_declares_bearer_idempotency_and_version_preconditions() -> None:
    with client(Directory(), Service()) as api:
        schema = api.get("/api/v1/openapi.json").json()
    roadmap_route = schema["paths"][
        "/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap"
    ]
    snapshot_route = schema["paths"][
        "/api/v1/tenants/{tenant_id}/campaigns/{campaign_id}/operations/roadmap/war-room-snapshots"
    ]
    for method in ("post", "get", "patch"):
        assert roadmap_route[method]["security"] == [{"OIDC bearer token": []}]
    assert {"Idempotency-Key", "If-Match"} <= {
        item["name"] for item in roadmap_route["patch"]["parameters"]
    }
    assert {"Idempotency-Key", "If-Match"} <= {
        item["name"] for item in snapshot_route["post"]["parameters"]
    }
