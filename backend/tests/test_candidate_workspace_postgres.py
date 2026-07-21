from __future__ import annotations

import os
import re
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

from campaignos.candidates import (
    CandidateSectionApprovalRequest,
    CandidateWorkspaceCreate,
    CandidateWorkspaceUpdate,
)
from campaignos.candidates.service import (
    CandidateWorkspaceConflict,
    CandidateWorkspaceCreateEvidence,
    CandidateWorkspaceVersionConflict,
    SqlAlchemyCandidateWorkspaceService,
)
from campaignos.data import Database
from campaignos.data.models import (
    AuditEvent,
    Campaign,
    CandidateSectionApproval,
    CandidateWorkspace,
    GuidedIntake,
    IdempotencyRecord,
    OutboxEvent,
    Principal,
    Tenant,
    Workspace,
)

CREATE_PURPOSE = "Create candidate evidence workspace"
UPDATE_PURPOSE = "Maintain candidate evidence workspace"
APPROVE_PURPOSE = "Approve candidate evidence section"


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


def _ready_intake(tenant_id: UUID, campaign_id: UUID) -> GuidedIntake:
    return GuidedIntake(
        tenant_id=tenant_id,
        campaign_id=campaign_id,
        status="READY_FOR_RESEARCH",
        office="Alcaldía Municipal",
        candidate_project="Proyecto sujeto a evidencia y revisión humana.",
        current_team=["Dirección de campaña"],
        current_assets=[],
        budget_status="DOCUMENTED",
        known_unknowns=["Requisitos de inscripción"],
        evidence_requirements=["Biografía verificable"],
        version=2,
    )


def _complete_update() -> CandidateWorkspaceUpdate:
    evidence_ids = [uuid4() for _ in range(6)]

    def evidence(evidence_id: UUID, title: str) -> dict[str, object]:
        return {
            "id": evidence_id,
            "classification": "CAMPAIGN_RESEARCH",
            "status": "ACCEPTED",
            "title": title,
            "source_reference": f"synthetic://candidate/{evidence_id}",
            "source_authority": "Synthetic campaign research fixture",
            "jurisdiction": "Antigua Guatemala",
            "observed_at": "2026-07-21T22:00:00Z",
        }

    def claim(label: str, evidence_id: UUID) -> dict[str, object]:
        return {
            "id": uuid4(),
            "label": label,
            "claim": f"Verified synthetic {label.lower()} claim.",
            "status": "VERIFIED",
            "classification": "CAMPAIGN_RESEARCH",
            "evidence_refs": [evidence_id],
        }

    return CandidateWorkspaceUpdate.model_validate(
        {
            "evidence": [
                evidence(evidence_id, title)
                for evidence_id, title in zip(
                    evidence_ids,
                    ("Identity", "Biography", "Purpose", "Value", "Attribute", "Goal"),
                    strict=True,
                )
            ],
            "identity": claim("Identity", evidence_ids[0]),
            "biography": claim("Biography", evidence_ids[1]),
            "purpose": claim("Purpose", evidence_ids[2]),
            "values": [claim("Public service", evidence_ids[3])],
            "attributes": [
                {
                    "id": uuid4(),
                    "name": "Capacity to form teams",
                    "claim": "The candidate has demonstrated team-building capacity.",
                    "status": "VERIFIED",
                    "candidate_self_assessment": "YES",
                    "team_assessment": "PARTIAL",
                    "citizen_evidence": "UNRESOLVED",
                    "evidence_refs": [evidence_ids[4]],
                    "perception_refs": [],
                    "contradiction_refs": [],
                    "risk": "Evidence is sufficient only for internal assessment.",
                }
            ],
            "contradictions": [],
            "development_goals": [
                {
                    "id": uuid4(),
                    "area": "Evidence discipline",
                    "objective": "Document every material claim before human review.",
                    "status": "OPEN",
                    "evidence_refs": [evidence_ids[5]],
                }
            ],
            "reputation_risks": [],
        }
    )


def _drop_role(admin_engine: object, role_name: str) -> None:
    with admin_engine.begin() as connection:  # type: ignore[union-attr]
        exists = bool(
            connection.scalar(
                text("SELECT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = :name)"),
                {"name": role_name},
            )
        )
        if exists:
            connection.execute(text(f'DROP OWNED BY "{role_name}"'))
            connection.execute(text(f'DROP ROLE "{role_name}"'))


@pytest.mark.postgres
def test_postgresql_candidate_workspace_concurrency_rls_and_approvals(
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
    role_name = "campaignos_candidate_workspace_test"
    role_password = f"test-{uuid4().hex}"
    _drop_role(admin_engine, role_name)
    with admin_engine.begin() as connection:
        connection.execute(
            text(
                f"CREATE ROLE \"{role_name}\" LOGIN PASSWORD '{role_password}' "
                "NOSUPERUSER NOBYPASSRLS"
            )
        )
        role = connection.execute(
            text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = :role_name"),
            {"role_name": role_name},
        ).one()
        assert role == (False, False)
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
        pool_size=8,
        max_overflow=0,
    )
    tenant_id = uuid4()
    other_tenant_id = uuid4()
    principal_id = uuid4()
    campaign_a = uuid4()
    campaign_b = uuid4()
    other_campaign = uuid4()
    grant_id = uuid4()
    try:
        with database.tenant_transaction(tenant_id) as session:
            session.add_all(
                [
                    Tenant(id=tenant_id, slug=f"tenant-{tenant_id}", name="Candidate Tenant"),
                    Principal(
                        id=principal_id,
                        issuer="https://identity.example.test/",
                        subject=f"candidate-{principal_id}",
                    ),
                ]
            )
            session.flush()
            for campaign_id, slug in ((campaign_a, "candidate-a"), (campaign_b, "candidate-b")):
                session.add(
                    Campaign(
                        id=campaign_id,
                        tenant_id=tenant_id,
                        slug=slug,
                        name=f"Campaign {slug}",
                        jurisdiction="Antigua Guatemala",
                        stage="PRECAMPAIGN",
                        status="ACTIVE",
                        version=3,
                    )
                )
                session.flush()
                session.add_all(
                    [
                        Workspace(
                            tenant_id=tenant_id,
                            campaign_id=campaign_id,
                            slug="governance",
                            name="Governance",
                            status="ACTIVE",
                            version=1,
                        ),
                        _ready_intake(tenant_id, campaign_id),
                    ]
                )
        with database.tenant_transaction(other_tenant_id) as session:
            session.add(
                Tenant(
                    id=other_tenant_id,
                    slug=f"tenant-{other_tenant_id}",
                    name="Foreign Candidate Tenant",
                )
            )
            session.flush()
            session.add(
                Campaign(
                    id=other_campaign,
                    tenant_id=other_tenant_id,
                    slug="foreign-candidate",
                    name="Foreign Candidate",
                    jurisdiction="Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=1,
                )
            )
            session.flush()
            session.add_all(
                [
                    Workspace(
                        tenant_id=other_tenant_id,
                        campaign_id=other_campaign,
                        slug="governance",
                        name="Governance",
                        status="ACTIVE",
                        version=1,
                    ),
                    _ready_intake(other_tenant_id, other_campaign),
                ]
            )

        service = SqlAlchemyCandidateWorkspaceService(database)

        def create(campaign_id: UUID, key: str) -> CandidateWorkspaceCreateEvidence:
            return service.create(
                tenant_id,
                campaign_id,
                request=CandidateWorkspaceCreate(display_name="Candidatura sintética"),
                principal_id=principal_id,
                authorization_grant_id=grant_id,
                approval_receipt_id="approval-candidate-postgres",
                authorization_purpose=CREATE_PURPOSE,
                correlation_id=f"candidate-{key}",
                idempotency_key=key,
            )

        same_key_barrier = Barrier(2)

        def create_same_key(index: int) -> CandidateWorkspaceCreateEvidence:
            same_key_barrier.wait()
            return create(campaign_a, "candidate-same-key")

        with ThreadPoolExecutor(max_workers=2) as executor:
            same_key = list(executor.map(create_same_key, (1, 2)))
        assert same_key[0] == same_key[1]
        candidate_a_id = same_key[0].workspace.id

        distinct_barrier = Barrier(2)

        def create_distinct(index: int) -> str:
            distinct_barrier.wait()
            try:
                create(campaign_b, f"candidate-distinct-{index}")
            except CandidateWorkspaceConflict:
                return "CONFLICT"
            return "CREATED"

        with ThreadPoolExecutor(max_workers=2) as executor:
            distinct = sorted(executor.map(create_distinct, (1, 2)))
        assert distinct == ["CONFLICT", "CREATED"]

        complete = service.update(
            tenant_id,
            campaign_a,
            expected_version=1,
            changes=_complete_update(),
            principal_id=principal_id,
            authorization_grant_id=grant_id,
            approval_receipt_id="approval-candidate-update",
            authorization_purpose=UPDATE_PURPOSE,
            correlation_id="candidate-complete",
            idempotency_key="candidate-complete",
        )
        assert complete.workspace.status == "AWAITING_APPROVAL"
        approved = service.approve_section(
            tenant_id,
            campaign_a,
            expected_version=2,
            request=CandidateSectionApprovalRequest(
                section="identity",
                reason="Identity evidence reviewed for internal use only.",
            ),
            principal_id=principal_id,
            authorization_grant_id=grant_id,
            approval_receipt_id="approval-candidate-identity",
            authorization_purpose=APPROVE_PURPOSE,
            correlation_id="candidate-approve-identity",
            idempotency_key="candidate-approve-identity",
        )
        assert approved.workspace.public_use_status == "BLOCKED"
        assert approved.approval.approved_version == 2

        update_barrier = Barrier(2)

        def update_distinct(index: int) -> str:
            update_barrier.wait()
            try:
                service.update(
                    tenant_id,
                    campaign_a,
                    expected_version=2,
                    changes=CandidateWorkspaceUpdate(display_name=f"Candidate {index}"),
                    principal_id=principal_id,
                    authorization_grant_id=grant_id,
                    approval_receipt_id="approval-candidate-update",
                    authorization_purpose=UPDATE_PURPOSE,
                    correlation_id=f"candidate-update-{index}",
                    idempotency_key=f"candidate-update-{index}",
                )
            except CandidateWorkspaceVersionConflict:
                return "VERSION_CONFLICT"
            return "UPDATED"

        with ThreadPoolExecutor(max_workers=2) as executor:
            updates = sorted(executor.map(update_distinct, (1, 2)))
        assert updates == ["UPDATED", "VERSION_CONFLICT"]

        other = service.create(
            other_tenant_id,
            other_campaign,
            request=CandidateWorkspaceCreate(display_name="Foreign candidate"),
            principal_id=principal_id,
            authorization_grant_id=grant_id,
            approval_receipt_id="approval-candidate-postgres",
            authorization_purpose=CREATE_PURPOSE,
            correlation_id="candidate-other-tenant",
            idempotency_key="candidate-other-tenant",
        )
        with database.tenant_transaction(tenant_id) as session:
            visible = set(session.scalars(select(CandidateWorkspace.id)))
            assert candidate_a_id in visible
            assert other.workspace.id not in visible
            assert session.get(CandidateWorkspace, other.workspace.id) is None
        with database.tenant_transaction(other_tenant_id) as session:
            assert set(session.scalars(select(CandidateWorkspace.id))) == {other.workspace.id}

        with pytest.raises(DBAPIError):
            with database.tenant_transaction(tenant_id) as session:
                session.add(
                    CandidateWorkspace(
                        tenant_id=other_tenant_id,
                        campaign_id=other_campaign,
                        candidate_id=uuid4(),
                        display_name="Forbidden cross-tenant candidate",
                        evidence=[],
                        version=1,
                    )
                )

        with database.tenant_transaction(tenant_id) as session:
            assert session.scalar(select(func.count()).select_from(CandidateWorkspace)) == 2
            assert session.scalar(select(func.count()).select_from(CandidateSectionApproval)) == 1
            assert session.scalar(select(func.count()).select_from(AuditEvent)) == 5
            assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 5
            assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 5
    finally:
        database.dispose()
        _drop_role(admin_engine, role_name)
        admin_engine.dispose()
