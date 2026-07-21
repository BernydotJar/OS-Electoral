from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from threading import Barrier
from uuid import UUID

import pytest

from campaignos.strategy import (
    InMemoryStrategyWorkspaceService,
    StrategyAssumption,
    StrategyDecisionRequest,
    StrategyEvidence,
    StrategyHypothesis,
    StrategyObjective,
    StrategyOption,
    StrategyPrerequisites,
    StrategyWorkspaceCreate,
    StrategyWorkspaceEvidenceConflict,
    StrategyWorkspaceIdempotencyConflict,
    StrategyWorkspaceNotFound,
    StrategyWorkspaceUnavailable,
    StrategyWorkspaceUpdate,
    StrategyWorkspaceVersionConflict,
    UnavailableStrategyWorkspaceService,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
OTHER_TENANT_ID = UUID("12121212-1212-4212-8212-121212121212")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
PRINCIPAL_ID = UUID("33333333-3333-4333-8333-333333333333")
OTHER_PRINCIPAL_ID = UUID("34343434-3434-4434-8434-343434343434")
GRANT_ID = UUID("44444444-4444-4444-8444-444444444444")
ROLE_ID = UUID("55555555-5555-4555-8555-555555555555")
EVIDENCE_ID = UUID("66666666-6666-4666-8666-666666666666")
ASSUMPTION_ID = UUID("77777777-7777-4777-8777-777777777777")
HYPOTHESIS_A = UUID("88888888-8888-4888-8888-888888888881")
HYPOTHESIS_B = UUID("88888888-8888-4888-8888-888888888882")
OPTION_A = UUID("99999999-9999-4999-8999-999999999991")
OPTION_B = UUID("99999999-9999-4999-8999-999999999992")
OBJECTIVE_ID = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa")
NOW = datetime(2026, 7, 21, 12, tzinfo=UTC)
CREATE_PURPOSE = "Create campaign strategy workspace"
READ_PURPOSE = "Review campaign strategy workspace"
UPDATE_PURPOSE = "Maintain campaign strategy workspace"
DECIDE_PURPOSE = "Approve internal campaign strategy option"


def service() -> InMemoryStrategyWorkspaceService:
    return InMemoryStrategyWorkspaceService(
        {
            (TENANT_ID, CAMPAIGN_ID): StrategyPrerequisites(
                campaign_version=5,
                campaign_status="ACTIVE",
                campaign_name="Synthetic campaign",
                candidate_workspace_version=2,
                team_workspace_version=3,
                known_role_ids=(ROLE_ID,),
            )
        }
    )


def create(
    boundary: InMemoryStrategyWorkspaceService,
    *,
    key: str = "strategy-create",
    principal_id: UUID = PRINCIPAL_ID,
    purpose: str = CREATE_PURPOSE,
):
    return boundary.create(
        TENANT_ID,
        CAMPAIGN_ID,
        request=StrategyWorkspaceCreate(title="Evidence-first strategy room"),
        principal_id=principal_id,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-strategy-create",
        authorization_purpose=purpose,
        correlation_id="strategy-create-correlation",
        idempotency_key=key,
    )


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
        invalidation_signals=("Available capacity falls below the documented threshold",),
    )
    hypothesis_a = StrategyHypothesis(
        id=HYPOTHESIS_A,
        title="Evidence consolidation",
        statement="Consolidating accepted evidence improves internal decision quality.",
        evidence_refs=(EVIDENCE_ID,),
        assumption_refs=(ASSUMPTION_ID,),
        invalidation_signals=("Decision quality does not improve after evidence review",),
        status="IN_REVIEW",
    )
    hypothesis_b = StrategyHypothesis(
        id=HYPOTHESIS_B,
        title="Capacity-first sequencing",
        statement="Sequencing work by available capacity reduces internal blockers.",
        evidence_refs=(EVIDENCE_ID,),
        assumption_refs=(ASSUMPTION_ID,),
        invalidation_signals=("Capacity-first sequencing increases unresolved blockers",),
        status="IN_REVIEW",
    )
    return StrategyWorkspaceUpdate(
        evidence=(evidence,),
        assumptions=(assumption,),
        hypotheses=(hypothesis_a, hypothesis_b),
        options=(
            StrategyOption(
                id=OPTION_A,
                title="Option A",
                summary="Consolidate evidence before expanding internal planning.",
                hypothesis_refs=(HYPOTHESIS_A,),
                evidence_refs=(EVIDENCE_ID,),
                benefits=("Preserves provenance",),
                risks=("Requires additional review time",),
                tradeoffs=("Delays downstream planning",),
            ),
            StrategyOption(
                id=OPTION_B,
                title="Option B",
                summary="Sequence internal planning by verified team capacity.",
                hypothesis_refs=(HYPOTHESIS_B,),
                evidence_refs=(EVIDENCE_ID,),
                benefits=("Surfaces capacity constraints",),
                risks=("May defer evidence collection",),
                tradeoffs=("Prioritizes capacity over speed",),
            ),
        ),
        objectives=(
            StrategyObjective(
                id=OBJECTIVE_ID,
                outcome="Complete the accepted internal evidence review.",
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


def update_ready(
    boundary: InMemoryStrategyWorkspaceService,
    *,
    key: str = "strategy-update",
    expected_version: int = 1,
):
    return boundary.update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=expected_version,
        changes=ready_update(),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-strategy-update",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="strategy-update-correlation",
        idempotency_key=key,
    )


def decide(
    boundary: InMemoryStrategyWorkspaceService,
    *,
    key: str = "strategy-decide",
    expected_version: int = 2,
):
    return boundary.decide(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=expected_version,
        request=StrategyDecisionRequest(
            selected_option_id=OPTION_A,
            reason="The authorized human selected Option A after evidence and risk review.",
            human_role_id=ROLE_ID,
        ),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-strategy-v2-option-a",
        authorization_purpose=DECIDE_PURPOSE,
        correlation_id="strategy-decision-correlation",
        idempotency_key=key,
    )


def read(boundary: InMemoryStrategyWorkspaceService):
    return boundary.get(
        TENANT_ID,
        CAMPAIGN_ID,
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-strategy-read",
        authorization_purpose=READ_PURPOSE,
        correlation_id="strategy-read-correlation",
    )


def test_create_is_atomic_audited_and_replays_exact_evidence() -> None:
    boundary = service()
    first = create(boundary)
    replay = create(boundary)

    assert first == replay
    assert first.workspace.status == "EVIDENCE_REQUIRED"
    assert first.workspace.version == 1
    assert first.workspace.authority_effect == "NONE"
    assert first.workspace.external_effects == "NONE"
    assert len(boundary.audits) == 1
    assert len(boundary.outbox) == 1
    assert boundary.outbox[0].payload["external_effects"] == "NONE"


def test_same_key_changed_request_authority_or_purpose_conflicts() -> None:
    boundary = service()
    create(boundary)

    with pytest.raises(StrategyWorkspaceIdempotencyConflict):
        create(boundary, principal_id=OTHER_PRINCIPAL_ID)
    with pytest.raises(StrategyWorkspaceIdempotencyConflict):
        create(boundary, purpose="Different purpose")


def test_concurrent_same_key_creation_returns_one_exact_result() -> None:
    boundary = service()
    barrier = Barrier(2)

    def invoke(_: int):
        barrier.wait()
        return create(boundary)

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(invoke, (1, 2)))

    assert results[0] == results[1]
    assert len(boundary.audits) == 1
    assert len(boundary.outbox) == 1


def test_update_derives_human_decision_readiness_and_enforces_version() -> None:
    boundary = service()
    create(boundary)
    updated = update_ready(boundary)

    assert updated.workspace.version == 2
    assert updated.workspace.status == "READY_FOR_HUMAN_DECISION"
    assert updated.workspace.next_action == "MAKE_HUMAN_DECISION"
    assert updated.workspace.complete_option_count == 2
    assert updated.workspace.measurable_objective_count == 1

    with pytest.raises(StrategyWorkspaceVersionConflict):
        boundary.update(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=1,
            changes=StrategyWorkspaceUpdate(title="Stale update"),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-stale",
            authorization_purpose=UPDATE_PURPOSE,
            correlation_id="stale",
            idempotency_key="stale-update",
        )


def test_human_decision_is_version_option_role_and_receipt_bound() -> None:
    boundary = service()
    create(boundary)
    update_ready(boundary)
    first = decide(boundary)
    replay = decide(boundary)

    assert first == replay
    assert first.workspace.status == "DECIDED_INTERNAL"
    assert first.workspace.human_decision_required is False
    assert first.decision.workspace_version == 2
    assert first.decision.selected_option_id == OPTION_A
    assert first.decision.human_role_id == ROLE_ID
    assert first.decision.approval_receipt_id == "approval-strategy-v2-option-a"
    assert len(boundary.decisions) == 1
    assert boundary.audits[-1].payload["authority_effect"] == "INTERNAL_DECISION_ONLY"
    assert boundary.outbox[-1].payload["external_effects"] == "NONE"


def test_update_after_decision_invalidates_current_decision_but_preserves_history() -> None:
    boundary = service()
    create(boundary)
    update_ready(boundary)
    decided = decide(boundary)

    changed = boundary.update(
        TENANT_ID,
        CAMPAIGN_ID,
        expected_version=2,
        changes=StrategyWorkspaceUpdate(title="Revalidated Strategy Room"),
        principal_id=PRINCIPAL_ID,
        authorization_grant_id=GRANT_ID,
        approval_receipt_id="approval-strategy-revalidate",
        authorization_purpose=UPDATE_PURPOSE,
        correlation_id="strategy-revalidate",
        idempotency_key="strategy-revalidate",
    )

    assert decided.workspace.decision is not None
    assert changed.workspace.version == 3
    assert changed.workspace.decision is None
    assert changed.workspace.status == "READY_FOR_HUMAN_DECISION"
    assert changed.workspace.human_decision_required is True
    assert len(boundary.decisions) == 1
    assert boundary.audits[-1].payload["decision_invalidated"] is True


def test_invalid_evidence_rolls_back_state_audit_outbox_and_replay() -> None:
    boundary = service()
    created = create(boundary)
    audit_count = len(boundary.audits)
    outbox_count = len(boundary.outbox)

    invalid = ready_update().model_dump(mode="json", exclude_unset=True)
    invalid["objectives"][0]["owner_role_id"] = str(UUID("ffffffff-ffff-4fff-8fff-ffffffffffff"))
    with pytest.raises(StrategyWorkspaceEvidenceConflict):
        boundary.update(
            TENANT_ID,
            CAMPAIGN_ID,
            expected_version=1,
            changes=StrategyWorkspaceUpdate.model_validate(invalid),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-invalid",
            authorization_purpose=UPDATE_PURPOSE,
            correlation_id="invalid",
            idempotency_key="invalid-update",
        )

    assert len(boundary.audits) == audit_count
    assert len(boundary.outbox) == outbox_count
    current = read(boundary)
    assert current.workspace.id == created.workspace.id
    assert current.workspace.version == 1
    assert current.workspace.status == "EVIDENCE_REQUIRED"


def test_cross_tenant_scope_is_not_inferred_from_campaign_id() -> None:
    boundary = service()
    create(boundary)

    with pytest.raises(StrategyWorkspaceNotFound):
        boundary.get(
            OTHER_TENANT_ID,
            CAMPAIGN_ID,
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-other-tenant",
            authorization_purpose=READ_PURPOSE,
            correlation_id="other-tenant",
        )


def test_unavailable_adapter_fails_closed() -> None:
    boundary = UnavailableStrategyWorkspaceService()
    with pytest.raises(StrategyWorkspaceUnavailable):
        boundary.create(
            TENANT_ID,
            CAMPAIGN_ID,
            request=StrategyWorkspaceCreate(),
            principal_id=PRINCIPAL_ID,
            authorization_grant_id=GRANT_ID,
            approval_receipt_id="approval-unavailable",
            authorization_purpose=CREATE_PURPOSE,
            correlation_id="unavailable",
            idempotency_key="unavailable",
        )
