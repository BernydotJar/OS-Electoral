from __future__ import annotations

from collections.abc import Iterator
from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from campaignos.data import Base, Database
from campaignos.data.models import (
    AuditEvent,
    Campaign,
    CandidateWorkspace,
    IdempotencyRecord,
    OutboxEvent,
    Principal,
    StrategyDecisionReceipt,
    StrategyWorkspace,
    TeamWorkspace,
    Tenant,
)
from campaignos.strategy import (
    SqlAlchemyStrategyWorkspaceService,
    StrategyAssumption,
    StrategyDecisionEvidence,
    StrategyDecisionRequest,
    StrategyEvidence,
    StrategyHypothesis,
    StrategyObjective,
    StrategyOption,
    StrategyWorkspaceCreate,
    StrategyWorkspaceCreateEvidence,
    StrategyWorkspaceUpdate,
    StrategyWorkspaceUpdateEvidence,
)
from campaignos.strategy.service import (
    StrategyWorkspaceConflict,
    StrategyWorkspaceEvidenceConflict,
    StrategyWorkspaceIdempotencyConflict,
    StrategyWorkspaceNotFound,
    StrategyWorkspacePrerequisiteConflict,
    StrategyWorkspaceVersionConflict,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("12121212-1212-4212-8212-121212121212")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
OTHER_CAMPAIGN_ID = UUID("23232323-2323-4232-8232-232323232323")
PRINCIPAL_ID = UUID("33333333-3333-4333-8333-333333333333")
ROLE_ID = UUID("44444444-4444-4444-8444-444444444444")
GRANT_ID = UUID("55555555-5555-4555-8555-555555555555")
EVIDENCE_ID = UUID("66666666-6666-4666-8666-666666666666")
ASSUMPTION_ID = UUID("77777777-7777-4777-8777-777777777777")
HYPOTHESIS_A = UUID("88888888-8888-4888-8888-888888888881")
HYPOTHESIS_B = UUID("88888888-8888-4888-8888-888888888882")
OPTION_A = UUID("99999999-9999-4999-8999-999999999991")
OPTION_B = UUID("99999999-9999-4999-8999-999999999992")
OBJECTIVE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
NOW = datetime(2026, 7, 21, 23, tzinfo=UTC)
CREATE_PURPOSE = "Create campaign strategy workspace"
READ_PURPOSE = "Review campaign strategy workspace"
UPDATE_PURPOSE = "Maintain campaign strategy workspace"
DECIDE_PURPOSE = "Approve internal campaign strategy option"


@pytest.fixture
def database() -> Iterator[Database]:
    runtime = Database.from_url("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(runtime.engine)
    with runtime.tenant_transaction(TENANT_ID) as session:
        session.add_all(
            [
                Tenant(id=TENANT_ID, slug="strategy", name="Strategy"),
                Tenant(id=OTHER_TENANT_ID, slug="other", name="Other"),
                Principal(
                    id=PRINCIPAL_ID,
                    issuer="https://identity.example.test/",
                    subject="strategy-operator",
                ),
            ]
        )
        session.flush()
        session.add_all(
            [
                Campaign(
                    id=CAMPAIGN_ID,
                    tenant_id=TENANT_ID,
                    slug="strategy-campaign",
                    name="Strategy Campaign",
                    jurisdiction="Antigua Guatemala",
                    stage="PRECAMPAIGN",
                    status="ACTIVE",
                    version=5,
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
        session.add_all(
            [
                CandidateWorkspace(
                    tenant_id=TENANT_ID,
                    campaign_id=CAMPAIGN_ID,
                    candidate_id=uuid4(),
                    display_name="Synthetic candidate",
                    evidence=[],
                    version=2,
                    created_at=NOW,
                    updated_at=NOW,
                ),
                TeamWorkspace(
                    tenant_id=TENANT_ID,
                    campaign_id=CAMPAIGN_ID,
                    organization_template="LEAN_CAMPAIGN",
                    roles=[
                        {
                            "id": str(ROLE_ID),
                            "title": "Campaign direction",
                            "area": "Direction",
                            "purpose": "Own accountable human decisions.",
                            "responsibilities": ["Decide"],
                            "status": "FILLED",
                            "principal_id": str(PRINCIPAL_ID),
                            "availability_status": "AVAILABLE",
                            "weekly_capacity_hours": 40,
                            "onboarding_status": "COMPLETE",
                            "vacancy_plan": None,
                        }
                    ],
                    work_items=[],
                    training_requirements=[],
                    access_recommendations=[],
                    version=3,
                    created_at=NOW,
                    updated_at=NOW,
                ),
            ]
        )
    try:
        yield runtime
    finally:
        runtime.dispose()


def ready_update() -> StrategyWorkspaceUpdate:
    evidence = StrategyEvidence(
        id=EVIDENCE_ID,
        classification="VERIFIED",
        statement="A public record establishes the current campaign context.",
        source_reference="https://example.test/public-record",
        authority="Public authority",
        jurisdiction="Guatemala",
        status="ACCEPTED",
        collected_at=NOW,
    )
    assumption = StrategyAssumption(
        id=ASSUMPTION_ID,
        statement="The team can maintain the documented operating cadence.",
        evidence_refs=(EVIDENCE_ID,),
        invalidation_signals=("Capacity falls below the documented threshold",),
    )
    return StrategyWorkspaceUpdate(
        evidence=(evidence,),
        assumptions=(assumption,),
        hypotheses=(
            StrategyHypothesis(
                id=HYPOTHESIS_A,
                title="Evidence consolidation",
                statement="Evidence consolidation improves internal decision quality.",
                evidence_refs=(EVIDENCE_ID,),
                assumption_refs=(ASSUMPTION_ID,),
                invalidation_signals=("Decision quality does not improve",),
                status="IN_REVIEW",
            ),
            StrategyHypothesis(
                id=HYPOTHESIS_B,
                title="Capacity sequencing",
                statement="Capacity sequencing reduces internal blockers.",
                evidence_refs=(EVIDENCE_ID,),
                assumption_refs=(ASSUMPTION_ID,),
                invalidation_signals=("Unresolved blockers increase",),
                status="IN_REVIEW",
            ),
        ),
        options=(
            StrategyOption(
                id=OPTION_A,
                title="Option A",
                summary="Consolidate evidence before downstream planning.",
                hypothesis_refs=(HYPOTHESIS_A,),
                evidence_refs=(EVIDENCE_ID,),
                benefits=("Preserves provenance",),
                risks=("Requires review time",),
                tradeoffs=("Delays downstream planning",),
            ),
            StrategyOption(
                id=OPTION_B,
                title="Option B",
                summary="Sequence planning by verified capacity.",
                hypothesis_refs=(HYPOTHESIS_B,),
                evidence_refs=(EVIDENCE_ID,),
                benefits=("Surfaces constraints",),
                risks=("May defer evidence",),
                tradeoffs=("Prioritizes capacity",),
            ),
        ),
        objectives=(
            StrategyObjective(
                id=OBJECTIVE_ID,
                outcome="Complete accepted internal evidence review.",
                metric="Accepted evidence records",
                baseline="1 accepted record",
                target="10 accepted records",
                deadline=date(2026, 8, 15),
                owner_role_id=ROLE_ID,
                evidence_refs=(EVIDENCE_ID,),
            ),
        ),
        contradictions=(),
        red_team_findings=(),
    )


def create_workspace(
    service: SqlAlchemyStrategyWorkspaceService,
    *,
    key: str = "strategy-create",
    title: str = "Evidence-first strategy room",
) -> StrategyWorkspaceCreateEvidence:
    return service.create(
        TENANT_ID,
        CAMPAIGN_ID,
        request=StrategyWorkspaceCreate(title=title),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-strategy-create",
        authorization_purpose=CREATE_PURPOSE,
        correlation_id=key,
        idempotency_key=key,
    )


def update_workspace(
    service: SqlAlchemyStrategyWorkspaceService,
    *,
    version: int,
    key: str,
    changes: StrategyWorkspaceUpdate,
) -> StrategyWorkspaceUpdateEvidence:
    return service.update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=version,
        changes=changes,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-strategy-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id=key,
        idempotency_key=key,
    )


def decide_workspace(
    service: SqlAlchemyStrategyWorkspaceService,
    *,
    version: int,
    key: str,
    option_id: UUID = OPTION_A,
) -> StrategyDecisionEvidence:
    return service.decide(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=version,
        request=StrategyDecisionRequest(
            selected_option_id=option_id,
            reason="Authorized human decision after evidence and red-team review.",
            human_role_id=ROLE_ID,
        ),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-strategy-decision",
        authorization_purpose=DECIDE_PURPOSE,
        correlation_id=key,
        idempotency_key=key,
    )


def test_sql_strategy_lifecycle_replay_and_decision_invalidation(
    database: Database,
) -> None:
    service = SqlAlchemyStrategyWorkspaceService(database)
    created = create_workspace(service)
    assert create_workspace(service) == created
    assert created.workspace.status == "EVIDENCE_REQUIRED"
    assert created.workspace.candidate_workspace_version == 2
    assert created.workspace.team_workspace_version == 3

    read = service.get(
        TENANT_ID,
        CAMPAIGN_ID,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-strategy-read",
        authorization_purpose=READ_PURPOSE,
        correlation_id="strategy-read",
    )
    assert read.workspace.id == created.workspace.id

    updated = update_workspace(
        service,
        version=1,
        key="strategy-ready",
        changes=ready_update(),
    )
    replay = update_workspace(
        service,
        version=1,
        key="strategy-ready",
        changes=ready_update(),
    )
    assert replay == updated
    assert updated.workspace.status == "READY_FOR_HUMAN_DECISION"
    assert updated.workspace.version == 2

    decision = decide_workspace(service, version=2, key="strategy-decision")
    assert decide_workspace(service, version=2, key="strategy-decision") == decision
    assert decision.workspace.status == "DECIDED_INTERNAL"
    assert decision.decision.workspace_version == 2
    assert decision.workspace.authority_effect == "NONE"
    assert decision.workspace.external_effects == "NONE"

    decided_read = service.get(
        TENANT_ID,
        CAMPAIGN_ID,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-strategy-read-decided",
        authorization_purpose=READ_PURPOSE,
        correlation_id="strategy-read-decided",
    )
    assert decided_read.workspace.status == "DECIDED_INTERNAL"

    invalidated = update_workspace(
        service,
        version=2,
        key="strategy-invalidate",
        changes=StrategyWorkspaceUpdate(title="Revalidated strategy room"),
    )
    assert invalidated.workspace.version == 3
    assert invalidated.workspace.status == "READY_FOR_HUMAN_DECISION"
    assert invalidated.workspace.decision is None

    with database.tenant_transaction(TENANT_ID) as session:
        assert session.scalar(select(func.count()).select_from(StrategyWorkspace)) == 1
        assert session.scalar(select(func.count()).select_from(StrategyDecisionReceipt)) == 1
        assert session.scalar(select(func.count()).select_from(AuditEvent)) == 6
        assert session.scalar(select(func.count()).select_from(OutboxEvent)) == 4
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 4
        payloads = tuple(session.scalars(select(OutboxEvent.payload)))
        assert all(payload["external_effects"] == "NONE" for payload in payloads)


def test_sql_strategy_conflicts_are_deterministic(database: Database) -> None:
    service = SqlAlchemyStrategyWorkspaceService(database)
    create_workspace(service)

    with pytest.raises(StrategyWorkspaceIdempotencyConflict):
        create_workspace(service, title="Different strategy title")
    with pytest.raises(StrategyWorkspaceConflict):
        create_workspace(service, key="different-create-key")
    with pytest.raises(StrategyWorkspaceVersionConflict):
        update_workspace(
            service,
            version=9,
            key="stale-update",
            changes=StrategyWorkspaceUpdate(title="Stale title"),
        )
    with pytest.raises(StrategyWorkspaceNotFound):
        service.get(
            OTHER_TENANT_ID,
            CAMPAIGN_ID,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-other-read",
            authorization_purpose=READ_PURPOSE,
            correlation_id="other-read",
        )
    with pytest.raises(StrategyWorkspacePrerequisiteConflict):
        service.create(
            OTHER_TENANT_ID,
            OTHER_CAMPAIGN_ID,
            request=StrategyWorkspaceCreate(title="Missing prerequisites"),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-other-create",
            authorization_purpose=CREATE_PURPOSE,
            correlation_id="other-create",
            idempotency_key="other-create",
        )


def test_sql_strategy_invalid_decision_and_update_roll_back(database: Database) -> None:
    service = SqlAlchemyStrategyWorkspaceService(database)
    create_workspace(service)
    update_workspace(
        service,
        version=1,
        key="strategy-ready",
        changes=ready_update(),
    )

    with pytest.raises(StrategyWorkspaceEvidenceConflict):
        decide_workspace(service, version=2, key="unknown-option", option_id=uuid4())
    decision = decide_workspace(service, version=2, key="valid-decision")
    with pytest.raises(StrategyWorkspaceConflict):
        decide_workspace(service, version=2, key="second-decision", option_id=OPTION_B)

    invalid_update = ready_update()
    objectives = invalid_update.objectives
    assert objectives is not None
    bad_objective = objectives[0].model_copy(update={"owner_role_id": uuid4()})
    with pytest.raises(StrategyWorkspaceEvidenceConflict):
        update_workspace(
            service,
            version=2,
            key="invalid-owner",
            changes=StrategyWorkspaceUpdate(objectives=(bad_objective,)),
        )

    with database.tenant_transaction(TENANT_ID) as session:
        row = session.scalar(select(StrategyWorkspace))
        assert row is not None and row.version == 2
        assert session.scalar(select(func.count()).select_from(StrategyDecisionReceipt)) == 1
        assert session.scalar(select(func.count()).select_from(IdempotencyRecord)) == 3
        assert decision.decision.selected_option_id == OPTION_A
