from __future__ import annotations

from uuid import UUID

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from campaignos.data.database import Database, TenantSession
from campaignos.data.models import (
    AuditEvent,
    Base,
    Campaign,
    IdempotencyRecord,
    OutboxEvent,
    Principal,
    Tenant,
    Workspace,
)
from campaignos.workspaces import (
    SqlAlchemyWorkspaceWriter,
    WorkspaceCreate,
    WorkspaceIdempotencyConflict,
    WorkspaceMutationNotFound,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")
PRINCIPAL_ID = UUID("44444444-4444-4444-8444-444444444444")
GRANT_ID = UUID("55555555-5555-4555-8555-555555555555")


@pytest.fixture
def database() -> Database:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(
        bind=engine,
        class_=TenantSession,
        autoflush=False,
        expire_on_commit=False,
    )
    database = Database(engine=engine, _sessions=sessions)
    with database.tenant_transaction(TENANT_ID) as session:
        session.add_all(
            [
                Tenant(id=TENANT_ID, slug="tenant", name="Tenant", status="ACTIVE"),
                Principal(
                    id=PRINCIPAL_ID,
                    issuer="https://identity.example.test/",
                    subject="workspace-writer",
                ),
                Campaign(
                    id=CAMPAIGN_ID,
                    tenant_id=TENANT_ID,
                    slug="campaign",
                    name="Campaign",
                    jurisdiction="Antigua Guatemala",
                    stage="PRECAMPAIGN",
                    status="DRAFT",
                    version=1,
                ),
            ]
        )
    with database.tenant_transaction(OTHER_TENANT_ID) as session:
        session.add(Tenant(id=OTHER_TENANT_ID, slug="other", name="Other", status="ACTIVE"))
    try:
        yield database
    finally:
        database.dispose()


def _create(
    database: Database,
    *,
    key: str = "workspace-create-1",
    name: str = "War Room",
):
    return SqlAlchemyWorkspaceWriter(database).create(
        TENANT_ID,
        CAMPAIGN_ID,
        request=WorkspaceCreate(slug="war-room", name=name),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-workspace-1",
        correlation_id="workspace-correlation-1",
        idempotency_key=key,
    )


def test_create_commits_workspace_audit_outbox_and_idempotency(database: Database) -> None:
    evidence = _create(database)

    assert evidence.workspace.status == "ACTIVE"
    assert evidence.workspace.version == 1
    with database.tenant_transaction(TENANT_ID) as session:
        workspace = session.get(Workspace, evidence.workspace.id)
        audit = session.get(AuditEvent, evidence.audit_event_id)
        outbox = session.get(OutboxEvent, evidence.outbox_event_id)
        assert workspace is not None
        assert workspace.campaign_id == CAMPAIGN_ID
        assert audit is not None
        assert audit.event_type == "workspace.created"
        assert audit.workspace_id == workspace.id
        assert audit.payload["authorization_grant_id"] == str(GRANT_ID)
        assert outbox is not None
        assert outbox.topic == "workspace.created"
        assert outbox.payload["workspace_id"] == str(workspace.id)
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1


def test_same_key_and_request_replays_without_duplicates(database: Database) -> None:
    first = _create(database)
    replay = _create(database)

    assert replay == first
    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(Workspace)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1


def test_reused_key_with_different_request_fails_closed(database: Database) -> None:
    first = _create(database)

    with pytest.raises(WorkspaceIdempotencyConflict):
        _create(database, name="Different")

    with database.tenant_transaction(TENANT_ID) as session:
        workspace = session.get(Workspace, first.workspace.id)
        assert workspace is not None and workspace.name == "War Room"
        assert session.scalar(select(func.count()).select_from(Workspace)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1


def test_missing_or_cross_tenant_campaign_rolls_back_without_evidence(database: Database) -> None:
    writer = SqlAlchemyWorkspaceWriter(database)
    with pytest.raises(WorkspaceMutationNotFound):
        writer.create(
            OTHER_TENANT_ID,
            CAMPAIGN_ID,
            request=WorkspaceCreate(slug="foreign", name="Foreign"),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-workspace-1",
            correlation_id="workspace-correlation-2",
            idempotency_key="workspace-foreign-1",
        )

    with database.tenant_transaction(OTHER_TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(Workspace)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
