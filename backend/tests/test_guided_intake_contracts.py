from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from pydantic import ValidationError

from campaignos.onboarding import (
    GuidedIntakeAssessmentInput,
    GuidedIntakeUpdate,
    assess_guided_intake,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
INTAKE_ID = UUID("33333333-3333-4333-8333-333333333333")
NOW = datetime(2026, 7, 21, 12, tzinfo=UTC)


def assessment(**overrides: object) -> GuidedIntakeAssessmentInput:
    values: dict[str, object] = {
        "id": INTAKE_ID,
        "tenant_id": TENANT_ID,
        "campaign_id": CAMPAIGN_ID,
        "campaign_version": 2,
        "campaign_status": "ACTIVE",
        "campaign_name": "Antigua 2028",
        "jurisdiction": "Antigua Guatemala",
        "stage": "PRECAMPAIGN",
        "active_workspace_count": 1,
        "office": None,
        "candidate_project": None,
        "current_team": None,
        "current_assets": None,
        "budget_status": "NOT_ASSESSED",
        "known_unknowns": None,
        "evidence_requirements": None,
        "version": 1,
        "created_at": NOW,
        "updated_at": NOW,
    }
    values.update(overrides)
    return GuidedIntakeAssessmentInput.model_validate(values)


def test_update_normalizes_bounded_fields_and_preserves_assessed_empty_lists() -> None:
    update = GuidedIntakeUpdate(
        office="  Alcaldía   Municipal  ",
        candidate_project="  Proyecto   ciudadano con evidencia pendiente.  ",
        current_team=["  Directora de campaña  ", "Analista"],
        current_assets=[],
        budget_status="ROUGH_RANGE",
        known_unknowns=["  Requisitos de inscripción  ", "Disponibilidad del equipo"],
        evidence_requirements=["  Documento de identidad  ", "Hoja de vida verificable"],
    )

    assert update.model_dump() == {
        "office": "Alcaldía Municipal",
        "candidate_project": "Proyecto ciudadano con evidencia pendiente.",
        "current_team": ("Directora de campaña", "Analista"),
        "current_assets": (),
        "budget_status": "ROUGH_RANGE",
        "known_unknowns": ("Requisitos de inscripción", "Disponibilidad del equipo"),
        "evidence_requirements": ("Documento de identidad", "Hoja de vida verificable"),
    }
    assert update.model_fields_set == {
        "office",
        "candidate_project",
        "current_team",
        "current_assets",
        "budget_status",
        "known_unknowns",
        "evidence_requirements",
    }


def test_update_rejects_empty_patch_blank_items_duplicates_and_null_budget() -> None:
    with pytest.raises(ValidationError, match="at least one field"):
        GuidedIntakeUpdate()
    with pytest.raises(ValidationError):
        GuidedIntakeUpdate(office="   ")
    with pytest.raises(ValidationError, match="duplicate"):
        GuidedIntakeUpdate(current_team=["Analista", " analista "])
    with pytest.raises(ValidationError, match="budget_status cannot be null"):
        GuidedIntakeUpdate(budget_status=None)
    with pytest.raises(ValidationError):
        GuidedIntakeUpdate(known_unknowns=["x" * 256])


def test_assessment_is_blocked_when_campaign_setup_drifted() -> None:
    projection = assess_guided_intake(assessment(active_workspace_count=0))

    assert projection.status == "BLOCKED_BY_CAMPAIGN_SETUP"
    assert projection.ready_for_research is False
    assert projection.next_action == "COMPLETE_CAMPAIGN_SETUP"
    assert projection.completed_checks == 0
    assert [check.key for check in projection.checks] == [
        "campaign_operational_setup",
        "office",
        "candidate_project",
        "current_team",
        "current_assets",
        "budget_status",
        "known_unknowns",
        "evidence_requirements",
    ]
    assert projection.research_first_actions == ()


def test_assessment_selects_first_missing_intake_section_canonically() -> None:
    projection = assess_guided_intake(
        assessment(
            office="Alcaldía Municipal",
            candidate_project=None,
            current_team=(),
            current_assets=(),
            budget_status="NO_DOCUMENT",
            known_unknowns=("Requisitos legales",),
            evidence_requirements=("Identidad verificable",),
        )
    )

    assert projection.status == "IN_PROGRESS"
    assert projection.completed_checks == 7
    assert projection.total_checks == 8
    assert projection.next_action == "DESCRIBE_CANDIDATE_PROJECT"
    assert projection.research_first_actions == ()


def test_complete_intake_becomes_ready_for_research_with_mandatory_limits() -> None:
    projection = assess_guided_intake(
        assessment(
            office="Alcaldía Municipal",
            candidate_project="Proyecto ciudadano sujeto a evidencia y revisión humana.",
            current_team=("Directora",),
            current_assets=(),
            budget_status="DOCUMENTED",
            known_unknowns=("Requisitos de inscripción",),
            evidence_requirements=("Identidad", "Biografía verificable"),
        )
    )

    assert projection.status == "READY_FOR_RESEARCH"
    assert projection.ready_for_research is True
    assert projection.completed_checks == projection.total_checks == 8
    assert projection.next_action == "BEGIN_RESEARCH"
    assert projection.research_first_actions == (
        "VERIFY_OFFICE_AND_JURISDICTION_EVIDENCE",
        "VALIDATE_CANDIDATE_PROJECT_EVIDENCE",
        "ASSESS_TEAM_CAPACITY_GAPS",
        "INVENTORY_ASSET_PROVENANCE",
        "DOCUMENT_BUDGET_ASSUMPTIONS",
        "RESEARCH_KNOWN_UNKNOWNS",
        "COLLECT_REQUIRED_EVIDENCE",
    )
    assert projection.limitation_codes == (
        "NOT_A_STRATEGY",
        "NOT_A_HUMAN_APPROVAL",
        "NO_CITIZEN_CONTACT_OR_PROFILING",
        "NO_EXTERNAL_EFFECTS",
    )
