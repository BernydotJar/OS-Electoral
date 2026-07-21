from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker

from campaignos.candidates import (
    CandidateSectionApprovalRequest,
    CandidateWorkspaceCreate,
    CandidateWorkspaceUpdate,
)
from campaignos.candidates.service import (
    CandidateWorkspaceApprovalConflict,
    CandidateWorkspaceIdempotencyConflict,
    CandidateWorkspaceNotFound,
    CandidateWorkspacePrerequisiteConflict,
    CandidateWorkspaceUnavailable,
    CandidateWorkspaceVersionConflict,
    SqlAlchemyCandidateWorkspaceService,
    UnavailableCandidateWorkspaceService,
)
from campaignos.data.audit import AuditScopeUnavailable
from campaignos.data.database import Database, TenantSession
from campaignos.data.models import (
    AuditEvent,
    Base,
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

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")
OTHER_CAMPAIGN_ID = UUID("44444444-4444-4444-8444-444444444444")
WORKSPACE_ID = UUID("55555555-5555-4555-8555-555555555555")
PRINCIPAL_ID = UUID("66666666-6666-4666-8666-666666666666")
GRANT_ID = UUID("77777777-7777-4777-8777-777777777777")
CREATE_PURPOSE = "Create candidate evidence workspace"
READ_PURPOSE = "Review candidate evidence workspace"
UPDATE_PURPOSE = "Maintain candidate evidence workspace"
APPROVE_PURPOSE = "Approve candidate evidence section"


@pytest.fixture
def database() -> Iterator[Database]:
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(
        bind=engine,
        class_=TenantSession,
        autoflush=False,
        expire_on_commit=False,
    )
    runtime = Database(engine=engine, _sessions=sessions)
    now = datetime(2026, 7, 21, 21, 0, tzinfo=UTC)
    with runtime.tenant_transaction(TENANT_ID) as session:
        session.add_all(
            [
                Tenant(id=TENANT_ID, slug="tenant", name="Tenant", status="ACTIVE"),
                Tenant(
                    id=OTHER_TENANT_ID,
                    slug="other-tenant",
                    name="Other Tenant",
                    status="ACTIVE",
                ),
                Principal(
                    id=PRINCIPAL_ID,
                    issuer="https://identity.example.test/",
                    subject="candidate-workspace-reviewer",
                ),
            ]
        )
        session.flush()
        session.add_all(
            [
                Campaign(
                    id=CAMPAIGN_ID,
                    tenant_id=TENANT_ID,
                    slug="campaign",
                    name="Campaign",
                    jurisdiction="Antigua Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=3,
                ),
                Campaign(
                    id=OTHER_CAMPAIGN_ID,
                    tenant_id=OTHER_TENANT_ID,
                    slug="other-campaign",
                    name="Other Campaign",
                    jurisdiction="Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=1,
                ),
            ]
        )
        session.flush()
        session.add(
            Workspace(
                id=WORKSPACE_ID,
                tenant_id=TENANT_ID,
                campaign_id=CAMPAIGN_ID,
                slug="governance",
                name="Governance",
                status="ACTIVE",
                version=1,
            )
        )
        session.add(
            GuidedIntake(
                tenant_id=TENANT_ID,
                campaign_id=CAMPAIGN_ID,
                status="READY_FOR_RESEARCH",
                office="Alcaldía Municipal",
                candidate_project="Proyecto sujeto a evidencia y revisión humana.",
                current_team=["Dirección de campaña"],
                current_assets=[],
                budget_status="DOCUMENTED",
                known_unknowns=["Requisitos de inscripción"],
                evidence_requirements=["Biografía verificable"],
                version=2,
                created_at=now,
                updated_at=now,
            )
        )
    try:
        yield runtime
    finally:
        runtime.dispose()


def _create(
    database: Database,
    *,
    tenant_id: UUID = TENANT_ID,
    campaign_id: UUID = CAMPAIGN_ID,
    key: str = "candidate-create-1",
):
    return SqlAlchemyCandidateWorkspaceService(database).create(
        tenant_id,
        campaign_id,
        request=CandidateWorkspaceCreate(display_name="Candidatura sintética"),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-candidate-create",
        authorization_purpose=CREATE_PURPOSE,
        correlation_id="candidate-create-correlation",
        idempotency_key=key,
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
            "excerpt": "Synthetic evidence for deterministic persistence verification.",
            "observed_at": "2026-07-21T21:00:00Z",
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


def test_unavailable_service_fails_closed() -> None:
    with pytest.raises(CandidateWorkspaceUnavailable):
        UnavailableCandidateWorkspaceService().create(
            TENANT_ID,
            CAMPAIGN_ID,
            request=CandidateWorkspaceCreate(display_name="Candidate"),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval",
            authorization_purpose=CREATE_PURPOSE,
            correlation_id="unavailable",
            idempotency_key="unavailable",
        )


def test_create_requires_guided_intake_ready_without_partial_evidence(database: Database) -> None:
    with database.tenant_transaction(TENANT_ID) as session:
        intake = session.scalar(select(GuidedIntake))
        assert intake is not None
        intake.status = "IN_PROGRESS"
        intake.office = None

    with pytest.raises(CandidateWorkspacePrerequisiteConflict):
        _create(database)

    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(CandidateWorkspace)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 0


def test_create_commits_workspace_audit_outbox_and_exact_replay(database: Database) -> None:
    created = _create(database)
    replay = _create(database)

    assert replay == created
    assert created.workspace.status == "SETUP_REQUIRED"
    assert created.workspace.version == 1
    assert created.workspace.public_use_status == "BLOCKED"
    assert created.workspace.external_effects == "NONE"

    with database.tenant_transaction(TENANT_ID) as session:
        row = session.get(CandidateWorkspace, created.workspace.id)
        audit = session.get(AuditEvent, created.audit_event_id)
        outbox = session.get(OutboxEvent, created.outbox_event_id)
        assert row is not None
        assert row.candidate_id == created.workspace.candidate_id
        assert audit is not None
        assert audit.event_type == "candidate_workspace.created"
        assert audit.payload["authorization_purpose"] == CREATE_PURPOSE
        assert audit.payload["external_effects"] == "NONE"
        assert outbox is not None
        assert outbox.topic == "candidate_workspace.created"
        assert outbox.payload["external_effects"] == "NONE"
        assert session.scalar(select(func.count()).select_from(CandidateWorkspace)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 1
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 1


def test_update_approval_cycle_is_version_bound_and_append_only(database: Database) -> None:
    _create(database)
    service = SqlAlchemyCandidateWorkspaceService(database)
    updated = service.update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=1,
        changes=_complete_update(),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-candidate-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="candidate-update-correlation",
        idempotency_key="candidate-update-1",
    )

    assert updated.workspace.version == 2
    assert updated.workspace.status == "AWAITING_APPROVAL"
    assert updated.workspace.approvable_sections == updated.workspace.approvals_required

    latest = updated
    for section in updated.workspace.approvals_required:
        approval = service.approve_section(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=2,
            request=CandidateSectionApprovalRequest(
                section=section,
                reason=f"Reviewed {section} evidence for internal use only.",
            ),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id=f"approval-candidate-section-{section}",
            authorization_purpose=APPROVE_PURPOSE,
            correlation_id=f"candidate-approval-{section}",
            idempotency_key=f"candidate-approval-{section}",
        )
        latest = approval

    assert latest.workspace.status == "INTERNALLY_APPROVED"
    assert latest.workspace.approvals_required == ()
    assert latest.workspace.public_use_status == "BLOCKED"

    changed = service.update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=2,
        changes=CandidateWorkspaceUpdate(display_name="Candidatura sintética actualizada"),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-candidate-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="candidate-update-correlation-2",
        idempotency_key="candidate-update-2",
    )
    assert changed.workspace.version == 3
    assert changed.workspace.status == "AWAITING_APPROVAL"
    assert changed.workspace.current_approved_sections == ()
    assert changed.workspace.approvals_required == changed.workspace.approvable_sections

    with database.tenant_transaction(TENANT_ID) as session:
        approvals = list(session.scalars(select(CandidateSectionApproval)))
        assert len(approvals) == 8
        assert {approval.approved_version for approval in approvals} == {2}
        assert session.scalar(select(func.count()).select_from(CandidateWorkspace)) == 1


def test_incomplete_section_and_stale_version_cannot_be_approved(database: Database) -> None:
    _create(database)
    service = SqlAlchemyCandidateWorkspaceService(database)

    with pytest.raises(CandidateWorkspaceApprovalConflict):
        service.approve_section(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=1,
            request=CandidateSectionApprovalRequest(
                section="identity",
                reason="Identity is not complete and must remain blocked.",
            ),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-candidate-section-identity",
            authorization_purpose=APPROVE_PURPOSE,
            correlation_id="candidate-approval-incomplete",
            idempotency_key="candidate-approval-incomplete",
        )

    service.update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=1,
        changes=CandidateWorkspaceUpdate(display_name="Updated candidate"),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-candidate-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="candidate-update",
        idempotency_key="candidate-update-stale",
    )
    with pytest.raises(CandidateWorkspaceVersionConflict):
        service.approve_section(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=1,
            request=CandidateSectionApprovalRequest(
                section="identity",
                reason="Stale version cannot approve evidence.",
            ),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-candidate-section-stale",
            authorization_purpose=APPROVE_PURPOSE,
            correlation_id="candidate-approval-stale",
            idempotency_key="candidate-approval-stale",
        )


def test_replay_is_bound_to_exact_authority_and_approval_intent(database: Database) -> None:
    created = _create(database, key="candidate-authority-key")
    service = SqlAlchemyCandidateWorkspaceService(database)

    with pytest.raises(CandidateWorkspaceIdempotencyConflict):
        service.create(
            TENANT_ID,
            CAMPAIGN_ID,
            request=CandidateWorkspaceCreate(display_name="Candidatura sintética"),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=uuid4(),
            approval_receipt_id="approval-candidate-create",
            authorization_purpose=CREATE_PURPOSE,
            correlation_id="candidate-authority-drift",
            idempotency_key="candidate-authority-key",
        )

    updated = service.update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=created.workspace.version,
        changes=_complete_update(),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-candidate-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="candidate-update-for-replay",
        idempotency_key="candidate-update-for-replay",
    )
    request = CandidateSectionApprovalRequest(
        section="identity",
        reason="Identity evidence reviewed for internal use only.",
    )
    first = service.approve_section(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=updated.workspace.version,
        request=request,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-candidate-identity",
        authorization_purpose=APPROVE_PURPOSE,
        correlation_id="candidate-approve-replay",
        idempotency_key="candidate-approve-replay",
    )
    replay = service.approve_section(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=updated.workspace.version,
        request=request,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-candidate-identity",
        authorization_purpose=APPROVE_PURPOSE,
        correlation_id="candidate-approve-replay",
        idempotency_key="candidate-approve-replay",
    )
    assert replay == first

    with pytest.raises(CandidateWorkspaceIdempotencyConflict):
        service.approve_section(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=updated.workspace.version,
            request=CandidateSectionApprovalRequest(
                section="identity",
                reason="A changed reason cannot reuse the approval key.",
            ),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-candidate-identity",
            authorization_purpose=APPROVE_PURPOSE,
            correlation_id="candidate-approve-replay-drift",
            idempotency_key="candidate-approve-replay",
        )


def test_approval_audit_failure_rolls_back_receipt_outbox_and_replay(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    created = _create(database)
    service = SqlAlchemyCandidateWorkspaceService(database)
    updated = service.update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=created.workspace.version,
        changes=_complete_update(),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-candidate-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="candidate-update-before-audit-failure",
        idempotency_key="candidate-update-before-audit-failure",
    )
    before_counts: tuple[int, int, int]
    with database.tenant_transaction(TENANT_ID) as session:
        before_counts = (
            int(session.scalar(select(func.count()).select_from(AuditEvent)) or 0),
            int(session.scalar(select(func.count()).select_from(OutboxEvent)) or 0),
            int(session.scalar(select(func.count()).select_from(IdempotencyRecord)) or 0),
        )

    def fail_audit(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AuditScopeUnavailable("synthetic approval audit failure")

    monkeypatch.setattr("campaignos.candidates.service.append_audit_event", fail_audit)
    with pytest.raises(CandidateWorkspaceUnavailable):
        service.approve_section(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=updated.workspace.version,
            request=CandidateSectionApprovalRequest(
                section="identity",
                reason="This receipt must roll back with audit failure.",
            ),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-candidate-identity",
            authorization_purpose=APPROVE_PURPOSE,
            correlation_id="candidate-approval-audit-failure",
            idempotency_key="candidate-approval-audit-failure",
        )

    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(CandidateSectionApproval)) == 0
        assert (
            int(session.scalar(select(func.count()).select_from(AuditEvent)) or 0),
            int(session.scalar(select(func.count()).select_from(OutboxEvent)) or 0),
            int(session.scalar(select(func.count()).select_from(IdempotencyRecord)) or 0),
        ) == before_counts


def test_read_is_audited_and_cross_tenant_scope_does_not_leak(database: Database) -> None:
    created = _create(database)
    service = SqlAlchemyCandidateWorkspaceService(database)
    read = service.get(
        TENANT_ID,
        CAMPAIGN_ID,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-candidate-read",
        authorization_purpose=READ_PURPOSE,
        correlation_id="candidate-read-correlation",
    )
    assert read.workspace.id == created.workspace.id

    with pytest.raises(CandidateWorkspaceNotFound):
        service.get(
            TENANT_ID,
            OTHER_CAMPAIGN_ID,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-candidate-read",
            authorization_purpose=READ_PURPOSE,
            correlation_id="candidate-cross-tenant",
        )

    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 2
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 1


def test_audit_failure_rolls_back_candidate_creation(
    database: Database,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_audit(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise AuditScopeUnavailable("synthetic candidate audit failure")

    monkeypatch.setattr("campaignos.candidates.service.append_audit_event", fail_audit)
    with pytest.raises(CandidateWorkspaceUnavailable):
        _create(database)

    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(CandidateWorkspace)) == 0
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 0
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 0
