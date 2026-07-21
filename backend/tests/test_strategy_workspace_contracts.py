from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from campaignos.strategy import (
    LIMITATION_CODES,
    StrategyAssumption,
    StrategyContradiction,
    StrategyDecision,
    StrategyEvidence,
    StrategyHypothesis,
    StrategyObjective,
    StrategyOption,
    StrategyRedTeamFinding,
    StrategyWorkspaceAssessmentInput,
    StrategyWorkspaceUpdate,
    assess_strategy_workspace,
)

WORKSPACE_ID = UUID("11111111-1111-4111-8111-111111111111")
TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")
ROLE_ID = UUID("44444444-4444-4444-8444-444444444444")
EVIDENCE_ID = UUID("55555555-5555-4555-8555-555555555555")
INFERRED_ID = UUID("66666666-6666-4666-8666-666666666666")
UNKNOWN_ID = UUID("77777777-7777-4777-8777-777777777777")
ASSUMPTION_ID = UUID("88888888-8888-4888-8888-888888888888")
HYPOTHESIS_A = UUID("99999999-9999-4999-8999-999999999991")
HYPOTHESIS_B = UUID("99999999-9999-4999-8999-999999999992")
OPTION_A = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa1")
OPTION_B = UUID("aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa2")
OBJECTIVE_ID = UUID("bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb")
CONTRADICTION_ID = UUID("cccccccc-cccc-4ccc-8ccc-cccccccccccc")
FINDING_ID = UUID("dddddddd-dddd-4ddd-8ddd-dddddddddddd")
DECISION_ID = UUID("eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee")
NOW = datetime(2026, 7, 21, 12, tzinfo=UTC)


def verified() -> StrategyEvidence:
    return StrategyEvidence(
        id=EVIDENCE_ID,
        classification="VERIFIED",
        statement="  Public record confirms the campaign context. ",
        source_reference="https://example.test/public-record",
        authority="Public authority",
        jurisdiction="Guatemala",
        status="ACCEPTED",
        collected_at=NOW,
    )


def inferred() -> StrategyEvidence:
    return StrategyEvidence(
        id=INFERRED_ID,
        classification="INFERRED",
        statement="The evidence may indicate an organizational constraint.",
        source_reference="internal-research:constraint-1",
        authority="Campaign research",
        jurisdiction="Campaign scope",
        status="NEEDS_REVIEW",
        collected_at=NOW,
    )


def unknown() -> StrategyEvidence:
    return StrategyEvidence(
        id=UNKNOWN_ID,
        classification="UNKNOWN",
        statement="Budget feasibility remains unknown.",
        source_reference=None,
        authority=None,
        jurisdiction=None,
        status="NEEDS_REVIEW",
        collected_at=NOW,
    )


def assumption() -> StrategyAssumption:
    return StrategyAssumption(
        id=ASSUMPTION_ID,
        statement="The team can maintain the proposed operating cadence.",
        evidence_refs=[EVIDENCE_ID],
        invalidation_signals=["Capacity falls below the documented minimum"],
        status="ACTIVE",
    )


def hypothesis(identifier: UUID, title: str) -> StrategyHypothesis:
    return StrategyHypothesis(
        id=identifier,
        title=title,
        statement=f"{title} remains viable while evidence and assumptions hold.",
        evidence_refs=[EVIDENCE_ID],
        assumption_refs=[ASSUMPTION_ID],
        invalidation_signals=[f"Verified evidence contradicts {title}"],
        status="IN_REVIEW",
    )


def option(identifier: UUID, hypothesis_id: UUID, title: str) -> StrategyOption:
    return StrategyOption(
        id=identifier,
        title=title,
        summary=f"Internal option {title} for human comparison.",
        hypothesis_refs=[hypothesis_id],
        evidence_refs=[EVIDENCE_ID],
        benefits=["Preserves evidence traceability"],
        risks=["Depends on current organizational capacity"],
        tradeoffs=["Requires additional human review time"],
    )


def objective(owner_role_id: UUID = ROLE_ID) -> StrategyObjective:
    return StrategyObjective(
        id=OBJECTIVE_ID,
        outcome="Complete the verified internal evidence review.",
        metric="Accepted evidence records",
        baseline="1 accepted record",
        target="10 accepted records",
        deadline=date(2026, 8, 15),
        owner_role_id=owner_role_id,
        evidence_refs=[EVIDENCE_ID],
    )


def assessment(**changes: object) -> StrategyWorkspaceAssessmentInput:
    values: dict[str, object] = {
        "id": WORKSPACE_ID,
        "tenant_id": TENANT_ID,
        "campaign_id": CAMPAIGN_ID,
        "campaign_version": 4,
        "campaign_status": "ACTIVE",
        "campaign_name": "Synthetic campaign",
        "candidate_workspace_version": 2,
        "team_workspace_version": 3,
        "known_role_ids": [ROLE_ID],
        "title": "Campaign Strategy and Decision Room",
        "evidence": [verified(), inferred()],
        "assumptions": [assumption()],
        "hypotheses": [
            hypothesis(HYPOTHESIS_A, "Evidence consolidation"),
            hypothesis(HYPOTHESIS_B, "Capacity-first sequencing"),
        ],
        "options": [
            option(OPTION_A, HYPOTHESIS_A, "Option A"),
            option(OPTION_B, HYPOTHESIS_B, "Option B"),
        ],
        "objectives": [objective()],
        "contradictions": [],
        "red_team_findings": [],
        "decision": None,
        "version": 2,
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(changes)
    return StrategyWorkspaceAssessmentInput.model_validate(values)


def test_evidence_classifications_preserve_provenance_and_normalize_text() -> None:
    item = verified()
    assert item.statement == "Public record confirms the campaign context."
    assert inferred().classification == "INFERRED"
    assert unknown().classification == "UNKNOWN"

    with pytest.raises(ValidationError, match="verified evidence requires a source"):
        StrategyEvidence.model_validate({**item.model_dump(), "source_reference": None})
    with pytest.raises(ValidationError, match="unknown evidence cannot claim a source"):
        StrategyEvidence.model_validate(
            {**unknown().model_dump(), "source_reference": "https://unsupported.test"}
        )


def test_contracts_reject_prohibited_profiling_fields_and_noop_updates() -> None:
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        StrategyWorkspaceUpdate.model_validate({"voter_persuadability_score": 92})
    with pytest.raises(ValidationError, match="strategy update must include a change"):
        StrategyWorkspaceUpdate()


def test_ready_workspace_requires_verified_evidence_options_and_objectives() -> None:
    projection = assess_strategy_workspace(assessment())
    assert projection.status == "READY_FOR_HUMAN_DECISION"
    assert projection.next_action == "MAKE_HUMAN_DECISION"
    assert projection.verified_evidence_count == 1
    assert projection.inferred_evidence_count == 1
    assert projection.unknown_evidence_count == 0
    assert projection.complete_option_count == 2
    assert projection.measurable_objective_count == 1
    assert projection.human_decision_required is True
    assert projection.authority_effect == "NONE"
    assert projection.external_effects == "NONE"
    assert projection.limitation_codes == LIMITATION_CODES


def test_unknown_evidence_blocks_decision_readiness() -> None:
    projection = assess_strategy_workspace(assessment(evidence=[verified(), inferred(), unknown()]))
    assert projection.status == "EVIDENCE_REQUIRED"
    assert projection.next_action == "ADD_VERIFIED_EVIDENCE"
    assert projection.unknown_evidence_count == 1


def test_hypotheses_and_options_require_known_non_rejected_evidence() -> None:
    bad_hypothesis = hypothesis(HYPOTHESIS_A, "Unsupported")
    bad_hypothesis = bad_hypothesis.model_copy(
        update={"evidence_refs": (UUID("ffffffff-ffff-4fff-8fff-ffffffffffff"),)}
    )
    with pytest.raises(ValueError, match="unknown evidence reference"):
        assess_strategy_workspace(assessment(hypotheses=[bad_hypothesis]))

    rejected = verified().model_copy(update={"status": "REJECTED", "classification": "INFERRED"})
    bad_option = option(OPTION_A, HYPOTHESIS_A, "Rejected evidence option")
    with pytest.raises(ValueError, match="cannot use rejected evidence"):
        assess_strategy_workspace(
            assessment(
                evidence=[rejected],
                assumptions=[],
                hypotheses=[
                    hypothesis(HYPOTHESIS_A, "Evidence consolidation").model_copy(
                        update={"status": "DRAFT", "assumption_refs": ()}
                    )
                ],
                options=[bad_option],
                objectives=[],
            )
        )


def test_objective_owner_must_be_a_known_team_role() -> None:
    with pytest.raises(ValueError, match="objective owner must be a known team role"):
        assess_strategy_workspace(
            assessment(objectives=[objective(UUID("ffffffff-ffff-4fff-8fff-ffffffffffff"))])
        )


def test_open_contradiction_blocks_and_resolution_is_explicit() -> None:
    open_item = StrategyContradiction(
        id=CONTRADICTION_ID,
        left_ref=EVIDENCE_ID,
        right_ref=HYPOTHESIS_A,
        description="Public evidence and the hypothesis require reconciliation.",
        evidence_refs=[EVIDENCE_ID],
        status="OPEN",
        resolution=None,
    )
    projection = assess_strategy_workspace(assessment(contradictions=[open_item]))
    assert projection.status == "CONTRADICTIONS_OPEN"
    assert projection.next_action == "RESOLVE_CONTRADICTIONS"

    resolved = open_item.model_copy(
        update={"status": "RESOLVED", "resolution": "The hypothesis was narrowed."}
    )
    assert assess_strategy_workspace(assessment(contradictions=[resolved])).status == (
        "READY_FOR_HUMAN_DECISION"
    )


def test_open_high_red_team_finding_blocks_human_decision() -> None:
    finding = StrategyRedTeamFinding(
        id=FINDING_ID,
        severity="HIGH",
        description="The option relies on an unstable capacity assumption.",
        option_refs=[OPTION_A],
        mitigation="Validate capacity and revise the option before decision.",
        status="OPEN",
    )
    projection = assess_strategy_workspace(assessment(red_team_findings=[finding]))
    assert projection.status == "RED_TEAM_BLOCKED"
    assert projection.next_action == "ADDRESS_RED_TEAM_FINDINGS"
    assert projection.open_high_risk_count == 1


def test_options_and_objectives_have_distinct_incomplete_states() -> None:
    without_options = assess_strategy_workspace(assessment(options=[]))
    assert without_options.status == "OPTIONS_INCOMPLETE"
    assert without_options.next_action == "COMPLETE_COMPARABLE_OPTIONS"

    without_objectives = assess_strategy_workspace(assessment(objectives=[]))
    assert without_objectives.status == "OBJECTIVES_INCOMPLETE"
    assert without_objectives.next_action == "DEFINE_MEASURABLE_OBJECTIVES"


def test_decision_is_exact_version_option_role_and_receipt_bound() -> None:
    decision = StrategyDecision(
        id=DECISION_ID,
        workspace_version=2,
        selected_option_id=OPTION_A,
        reason="Option A is selected for internal execution planning after human review.",
        human_role_id=ROLE_ID,
        approval_receipt_id="approval-strategy-v2-option-a",
        decided_at=NOW,
    )
    projection = assess_strategy_workspace(assessment(decision=decision))
    assert projection.status == "DECIDED_INTERNAL"
    assert projection.next_action == "REVALIDATE_DECISION"
    assert projection.human_decision_required is False

    with pytest.raises(ValueError, match="current workspace version"):
        assess_strategy_workspace(
            assessment(decision=decision.model_copy(update={"workspace_version": 1}))
        )
    with pytest.raises(ValueError, match="selected option is unknown"):
        assess_strategy_workspace(
            assessment(
                decision=decision.model_copy(
                    update={"selected_option_id": UUID("ffffffff-ffff-4fff-8fff-ffffffffffff")}
                )
            )
        )


def test_duplicate_ids_and_unknown_contradiction_refs_fail_closed() -> None:
    duplicate = hypothesis(EVIDENCE_ID, "Colliding record")
    with pytest.raises(ValueError, match="unique IDs"):
        assess_strategy_workspace(assessment(hypotheses=[duplicate]))

    contradiction = StrategyContradiction(
        id=CONTRADICTION_ID,
        left_ref=UUID("ffffffff-ffff-4fff-8fff-ffffffffffff"),
        right_ref=HYPOTHESIS_A,
        description="Unknown reference must fail.",
        evidence_refs=[EVIDENCE_ID],
        status="OPEN",
    )
    with pytest.raises(ValueError, match="unknown contradiction reference"):
        assess_strategy_workspace(assessment(contradictions=[contradiction]))
