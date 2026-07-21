from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from campaignos.candidates.contracts import (
    CandidateSectionApprovalRequest,
    CandidateWorkspaceAssessmentInput,
    CandidateWorkspaceContractError,
    CandidateWorkspaceCreate,
    CandidateWorkspaceUpdate,
    assess_candidate_workspace,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
WORKSPACE_ID = UUID("33333333-3333-4333-8333-333333333333")
CANDIDATE_ID = UUID("44444444-4444-4444-8444-444444444444")
PRINCIPAL_ID = UUID("55555555-5555-4555-8555-555555555555")
NOW = datetime(2026, 7, 21, 20, 30, tzinfo=UTC)


def _evidence(evidence_id: UUID, title: str) -> dict[str, object]:
    return {
        "id": evidence_id,
        "classification": "CAMPAIGN_RESEARCH",
        "status": "ACCEPTED",
        "title": title,
        "source_reference": f"synthetic://candidate/{evidence_id}",
        "source_authority": "Synthetic campaign research fixture",
        "jurisdiction": "Antigua Guatemala",
        "excerpt": "Synthetic evidence used only for deterministic contract verification.",
        "observed_at": NOW,
    }


def _claim(claim_id: UUID, label: str, evidence_id: UUID) -> dict[str, object]:
    return {
        "id": claim_id,
        "label": label,
        "claim": f"Verified synthetic {label.lower()} claim.",
        "status": "VERIFIED",
        "classification": "CAMPAIGN_RESEARCH",
        "evidence_refs": [evidence_id],
    }


def _assessment_payload() -> dict[str, object]:
    evidence_ids = [uuid4() for _ in range(6)]
    identity_id, biography_id, purpose_id, value_id, attribute_id, goal_id = [
        uuid4() for _ in range(6)
    ]
    approvals = [
        {
            "id": uuid4(),
            "section": section,
            "approved_version": 1,
            "principal_id": PRINCIPAL_ID,
            "authorization_grant_id": uuid4(),
            "approval_receipt_id": f"candidate-approval-{section}",
            "reason": f"Reviewed {section} evidence for internal use only.",
            "approved_at": NOW,
        }
        for section in (
            "identity",
            "biography",
            "purpose",
            "values",
            "attributes",
            "contradictions",
            "development_goals",
            "reputation",
        )
    ]
    return {
        "id": WORKSPACE_ID,
        "tenant_id": TENANT_ID,
        "campaign_id": CAMPAIGN_ID,
        "campaign_version": 3,
        "campaign_status": "DRAFT",
        "campaign_name": "Campaña sintética Antigua",
        "jurisdiction": "Antigua Guatemala",
        "candidate_id": CANDIDATE_ID,
        "display_name": "Candidatura sintética",
        "evidence": [
            _evidence(evidence_id, title)
            for evidence_id, title in zip(
                evidence_ids,
                ("Identity", "Biography", "Purpose", "Value", "Attribute", "Goal"),
                strict=True,
            )
        ],
        "identity": _claim(identity_id, "Identity", evidence_ids[0]),
        "biography": _claim(biography_id, "Biography", evidence_ids[1]),
        "purpose": _claim(purpose_id, "Purpose", evidence_ids[2]),
        "values": [_claim(value_id, "Public service", evidence_ids[3])],
        "attributes": [
            {
                "id": attribute_id,
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
                "id": goal_id,
                "area": "Evidence discipline",
                "objective": "Document every material public claim before human review.",
                "status": "OPEN",
                "evidence_refs": [evidence_ids[5]],
            }
        ],
        "reputation_risks": [],
        "approvals": approvals,
        "version": 1,
        "created_at": NOW,
        "updated_at": NOW,
    }


def test_create_and_update_normalize_bounded_candidate_fields() -> None:
    create = CandidateWorkspaceCreate(display_name="  Candidatura   Sintética ")
    assert create.display_name == "Candidatura Sintética"

    update = CandidateWorkspaceUpdate.model_validate(
        {
            "display_name": "  Nuevo   nombre  ",
            "values": [],
            "contradictions": [],
            "reputation_risks": [],
        }
    )
    assert update.display_name == "Nuevo nombre"
    assert update.values == ()
    assert update.model_fields_set == {
        "display_name",
        "values",
        "contradictions",
        "reputation_risks",
    }

    with pytest.raises(ValidationError, match="at least one field"):
        CandidateWorkspaceUpdate.model_validate({})
    with pytest.raises(ValidationError, match="must not be blank"):
        CandidateWorkspaceCreate(display_name="   ")


def test_complete_evidence_and_current_section_approvals_are_internal_only() -> None:
    projection = assess_candidate_workspace(
        CandidateWorkspaceAssessmentInput.model_validate(_assessment_payload())
    )

    assert projection.status == "INTERNALLY_APPROVED"
    assert projection.completed_checks == projection.total_checks == 9
    assert projection.approvals_required == ()
    assert projection.current_approved_sections == (
        "identity",
        "biography",
        "purpose",
        "values",
        "attributes",
        "contradictions",
        "development_goals",
        "reputation",
    )
    assert projection.public_use_status == "BLOCKED"
    assert projection.external_effects == "NONE"
    assert projection.limitation_codes == (
        "NOT_PUBLIC_POSITIONING_APPROVAL",
        "NOT_A_STRATEGY",
        "NO_VOTER_PROFILING",
        "NO_EXTERNAL_EFFECTS",
        "HUMAN_REVIEW_REQUIRED",
    )


def test_verified_claim_requires_same_workspace_independent_evidence() -> None:
    payload = _assessment_payload()
    payload["identity"]["evidence_refs"] = [uuid4()]  # type: ignore[index]
    with pytest.raises(CandidateWorkspaceContractError, match="unknown evidence reference"):
        assess_candidate_workspace(CandidateWorkspaceAssessmentInput.model_validate(payload))

    payload = _assessment_payload()
    evidence_id = payload["identity"]["evidence_refs"][0]  # type: ignore[index]
    for evidence in payload["evidence"]:  # type: ignore[union-attr]
        if evidence["id"] == evidence_id:
            evidence["classification"] = "PERCEPTION"
    with pytest.raises(CandidateWorkspaceContractError, match="independent evidence"):
        assess_candidate_workspace(CandidateWorkspaceAssessmentInput.model_validate(payload))


def test_self_assessment_alone_cannot_verify_an_attribute() -> None:
    payload = _assessment_payload()
    payload["attributes"][0]["evidence_refs"] = []  # type: ignore[index]
    with pytest.raises(CandidateWorkspaceContractError, match="self-assessment alone"):
        assess_candidate_workspace(CandidateWorkspaceAssessmentInput.model_validate(payload))


def test_attribute_perception_and_contradiction_references_are_semantically_typed() -> None:
    payload = _assessment_payload()
    perception_id = uuid4()
    payload["evidence"].append(  # type: ignore[union-attr]
        {
            **_evidence(perception_id, "Perception"),
            "classification": "CAMPAIGN_RESEARCH",
        }
    )
    payload["attributes"][0]["perception_refs"] = [perception_id]  # type: ignore[index]
    with pytest.raises(CandidateWorkspaceContractError, match="PERCEPTION records"):
        assess_candidate_workspace(CandidateWorkspaceAssessmentInput.model_validate(payload))

    payload = _assessment_payload()
    payload["attributes"][0]["contradiction_refs"] = [uuid4()]  # type: ignore[index]
    with pytest.raises(CandidateWorkspaceContractError, match="unknown contradiction reference"):
        assess_candidate_workspace(CandidateWorkspaceAssessmentInput.model_validate(payload))

    payload = _assessment_payload()
    attribute_id = payload["attributes"][0]["id"]  # type: ignore[index]
    evidence_id = payload["evidence"][0]["id"]  # type: ignore[index]
    contradiction_id = uuid4()
    payload["contradictions"] = [
        {
            "id": contradiction_id,
            "subject_ref": attribute_id,
            "description": "Synthetic contradiction reviewed and resolved.",
            "status": "RESOLVED",
            "evidence_refs": [evidence_id],
        }
    ]
    payload["attributes"][0]["contradiction_refs"] = [contradiction_id]  # type: ignore[index]
    projection = assess_candidate_workspace(
        CandidateWorkspaceAssessmentInput.model_validate(payload)
    )
    assert projection.attributes is not None
    assert projection.attributes[0].contradiction_refs == (contradiction_id,)

    payload = _assessment_payload()
    attribute_id = payload["attributes"][0]["id"]  # type: ignore[index]
    other_claim_id = payload["identity"]["id"]  # type: ignore[index]
    evidence_id = payload["evidence"][0]["id"]  # type: ignore[index]
    contradiction_id = uuid4()
    payload["contradictions"] = [
        {
            "id": contradiction_id,
            "subject_ref": other_claim_id,
            "description": "Synthetic contradiction about a different subject.",
            "status": "RESOLVED",
            "evidence_refs": [evidence_id],
        }
    ]
    payload["attributes"][0]["contradiction_refs"] = [contradiction_id]  # type: ignore[index]
    with pytest.raises(CandidateWorkspaceContractError, match="targets another subject"):
        assess_candidate_workspace(CandidateWorkspaceAssessmentInput.model_validate(payload))


def test_duplicate_ids_and_prohibited_profiling_fields_are_rejected() -> None:
    payload = _assessment_payload()
    payload["identity"]["id"] = payload["evidence"][0]["id"]  # type: ignore[index]
    with pytest.raises(CandidateWorkspaceContractError, match="duplicate or colliding"):
        assess_candidate_workspace(CandidateWorkspaceAssessmentInput.model_validate(payload))

    invalid_attribute = deepcopy(payload["attributes"][0])  # type: ignore[index]
    invalid_attribute["persuadability_score"] = 0.9
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CandidateWorkspaceUpdate.model_validate({"attributes": [invalid_attribute]})


def test_stale_approvals_do_not_survive_a_workspace_version_change() -> None:
    payload = _assessment_payload()
    payload["version"] = 2
    projection = assess_candidate_workspace(
        CandidateWorkspaceAssessmentInput.model_validate(payload)
    )

    assert projection.status == "AWAITING_APPROVAL"
    assert projection.current_approved_sections == ()
    assert projection.approvals_required == (
        "identity",
        "biography",
        "purpose",
        "values",
        "attributes",
        "contradictions",
        "development_goals",
        "reputation",
    )
    assert projection.next_action == "OBTAIN_SECTION_APPROVALS"


def test_open_high_reputation_risk_blocks_approval_readiness() -> None:
    payload = _assessment_payload()
    payload["reputation_risks"] = [
        {
            "id": uuid4(),
            "title": "Unresolved material contradiction",
            "description": "A high-severity contradiction remains unresolved.",
            "severity": "HIGH",
            "status": "OPEN",
            "decision_required": True,
            "evidence_refs": [payload["evidence"][0]["id"]],  # type: ignore[index]
        }
    ]
    projection = assess_candidate_workspace(
        CandidateWorkspaceAssessmentInput.model_validate(payload)
    )

    assert projection.status == "UNDER_REVIEW"
    assert projection.next_action == "REVIEW_REPUTATION_RISKS"
    assert "reputation" not in projection.approvable_sections
    assert projection.open_critical_high_risks == 1


def test_section_approval_request_is_explicit_and_bounded() -> None:
    request = CandidateSectionApprovalRequest.model_validate(
        {
            "section": "biography",
            "reason": "  Evidence   reviewed for internal candidate assessment.  ",
        }
    )
    assert request.reason == "Evidence reviewed for internal candidate assessment."

    with pytest.raises(ValidationError, match="must not be blank"):
        CandidateSectionApprovalRequest.model_validate({"section": "identity", "reason": "   "})
