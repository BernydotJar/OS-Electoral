from __future__ import annotations

from copy import deepcopy
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from campaignos.teams.contracts import (
    TeamWorkspaceAssessmentInput,
    TeamWorkspaceContractError,
    TeamWorkspaceCreate,
    TeamWorkspaceUpdate,
    assess_team_workspace,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
WORKSPACE_ID = UUID("33333333-3333-4333-8333-333333333333")
PRINCIPAL_ID = UUID("44444444-4444-4444-8444-444444444444")
NOW = datetime(2026, 7, 21, 23, tzinfo=UTC)


def _payload() -> dict[str, object]:
    director_id = UUID("50000000-0000-4000-8000-000000000001")
    research_id = UUID("50000000-0000-4000-8000-000000000002")
    vacancy_id = UUID("50000000-0000-4000-8000-000000000003")
    work_item_id = UUID("60000000-0000-4000-8000-000000000001")
    return {
        "id": WORKSPACE_ID,
        "tenant_id": TENANT_ID,
        "campaign_id": CAMPAIGN_ID,
        "campaign_version": 4,
        "campaign_status": "ACTIVE",
        "campaign_name": "Campaña sintética Antigua",
        "organization_template": "LEAN_CAMPAIGN",
        "roles": [
            {
                "id": director_id,
                "title": "Dirección de campaña",
                "area": "Dirección",
                "purpose": "Coordinar decisiones y accountability de la campaña.",
                "responsibilities": ["Coordinar prioridades", "Escalar decisiones humanas"],
                "status": "FILLED",
                "principal_id": PRINCIPAL_ID,
                "availability_status": "AVAILABLE",
                "weekly_capacity_hours": 40,
                "onboarding_status": "COMPLETE",
                "vacancy_plan": None,
            },
            {
                "id": research_id,
                "title": "Investigación",
                "area": "Evidencia",
                "purpose": "Mantener evidencia verificable y contradicciones visibles.",
                "responsibilities": ["Validar fuentes", "Registrar gaps"],
                "status": "FILLED",
                "principal_id": uuid4(),
                "availability_status": "LIMITED",
                "weekly_capacity_hours": 20,
                "onboarding_status": "COMPLETE",
                "vacancy_plan": None,
            },
            {
                "id": vacancy_id,
                "title": "Coordinación territorial",
                "area": "Organización",
                "purpose": "Diseñar coordinación territorial agregada y lawful.",
                "responsibilities": ["Definir estructura territorial"],
                "status": "VACANT",
                "principal_id": None,
                "availability_status": "UNASSESSED",
                "weekly_capacity_hours": None,
                "onboarding_status": "NOT_STARTED",
                "vacancy_plan": "Reclutar y revisar humanamente antes de conceder acceso.",
            },
        ],
        "work_items": [
            {
                "id": work_item_id,
                "name": "Preparar diagnóstico inicial",
                "description": "Organizar evidencia y decisiones requeridas.",
                "status": "ACTIVE",
                "assignments": [
                    {"role_id": director_id, "responsibility": "ACCOUNTABLE"},
                    {"role_id": research_id, "responsibility": "RESPONSIBLE"},
                    {"role_id": vacancy_id, "responsibility": "INFORMED"},
                ],
            }
        ],
        "training_requirements": [
            {
                "id": UUID("70000000-0000-4000-8000-000000000001"),
                "role_id": research_id,
                "title": "Evidence and provenance",
                "description": "Apply evidence classifications and citation boundaries.",
                "status": "COMPLETE",
            }
        ],
        "access_recommendations": [
            {
                "id": UUID("80000000-0000-4000-8000-000000000001"),
                "role_id": research_id,
                "campaign_id": CAMPAIGN_ID,
                "workspace_id": None,
                "action": "read",
                "resource_type": "candidate_workspace",
                "resource_id": str(CAMPAIGN_ID),
                "purpose": "Review candidate evidence workspace",
                "status": "REVIEWED",
                "authority_effect": "NONE",
            }
        ],
        "version": 1,
        "created_at": NOW,
        "updated_at": NOW,
    }


def test_create_and_update_normalize_bounded_team_fields() -> None:
    create = TeamWorkspaceCreate(organization_template="LEAN_CAMPAIGN")
    assert create.organization_template == "LEAN_CAMPAIGN"

    update = TeamWorkspaceUpdate.model_validate(
        {
            "roles": [],
            "training_requirements": [],
            "access_recommendations": [],
        }
    )
    assert update.roles == ()
    assert update.model_fields_set == {
        "roles",
        "training_requirements",
        "access_recommendations",
    }

    with pytest.raises(ValidationError, match="at least one field"):
        TeamWorkspaceUpdate.model_validate({})
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        TeamWorkspaceUpdate.model_validate({"role_grants": ["admin"]})


def test_complete_team_projection_exposes_gaps_without_creating_authority() -> None:
    projection = assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(_payload()))

    assert projection.status == "READY_FOR_HUMAN_REVIEW"
    assert projection.completed_checks == projection.total_checks == 8
    assert projection.vacant_role_count == 1
    assert projection.total_weekly_capacity_hours == 60
    assert projection.next_action == "CONTINUE_HUMAN_GOVERNANCE"
    assert projection.authority_effect == "NONE"
    assert projection.external_effects == "NONE"
    assert projection.limitation_codes == (
        "ROLE_LABELS_ARE_NOT_PERMISSIONS",
        "ACCESS_RECOMMENDATIONS_REQUIRE_HUMAN_AUTHORIZATION",
        "NO_VOTER_PROFILING",
        "NO_EXTERNAL_EFFECTS",
    )


def test_each_work_item_requires_one_accountable_and_one_responsible_role() -> None:
    missing_accountable = _payload()
    missing_accountable["work_items"][0]["assignments"] = [  # type: ignore[index]
        missing_accountable["work_items"][0]["assignments"][1]  # type: ignore[index]
    ]
    with pytest.raises(TeamWorkspaceContractError, match="exactly one accountable"):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(missing_accountable))

    multiple_accountable = _payload()
    role_id = multiple_accountable["roles"][1]["id"]  # type: ignore[index]
    multiple_accountable["work_items"][0]["assignments"].append(  # type: ignore[index]
        {"role_id": role_id, "responsibility": "ACCOUNTABLE"}
    )
    with pytest.raises(TeamWorkspaceContractError, match="exactly one accountable"):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(multiple_accountable))

    missing_responsible = _payload()
    missing_responsible["work_items"][0]["assignments"] = [  # type: ignore[index]
        missing_responsible["work_items"][0]["assignments"][0]  # type: ignore[index]
    ]
    with pytest.raises(TeamWorkspaceContractError, match="at least one responsible"):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(missing_responsible))


def test_active_accountable_and_responsible_assignments_require_filled_roles() -> None:
    accountable_vacancy = _payload()
    vacancy_id = accountable_vacancy["roles"][2]["id"]  # type: ignore[index]
    accountable_vacancy["work_items"][0]["assignments"][0]["role_id"] = vacancy_id  # type: ignore[index]
    with pytest.raises(
        TeamWorkspaceContractError, match="active accountability requires a filled role"
    ):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(accountable_vacancy))

    responsible_vacancy = _payload()
    vacancy_id = responsible_vacancy["roles"][2]["id"]  # type: ignore[index]
    responsible_vacancy["work_items"][0]["assignments"][1]["role_id"] = vacancy_id  # type: ignore[index]
    with pytest.raises(
        TeamWorkspaceContractError, match="active accountability requires a filled role"
    ):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(responsible_vacancy))


def test_raci_and_requirement_references_must_resolve_inside_workspace() -> None:
    payload = _payload()
    payload["work_items"][0]["assignments"][0]["role_id"] = uuid4()  # type: ignore[index]
    with pytest.raises(TeamWorkspaceContractError, match="unknown role reference"):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(payload))

    payload = _payload()
    payload["training_requirements"][0]["role_id"] = uuid4()  # type: ignore[index]
    with pytest.raises(TeamWorkspaceContractError, match="unknown role reference"):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(payload))


def test_filled_and_vacant_role_invariants_are_mutually_exclusive() -> None:
    filled_without_principal = _payload()
    filled_without_principal["roles"][0]["principal_id"] = None  # type: ignore[index]
    with pytest.raises(TeamWorkspaceContractError, match="filled role requires a principal"):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(filled_without_principal))

    vacant_with_principal = _payload()
    vacant_with_principal["roles"][2]["principal_id"] = uuid4()  # type: ignore[index]
    with pytest.raises(TeamWorkspaceContractError, match="vacant role cannot have a principal"):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(vacant_with_principal))

    vacant_without_plan = _payload()
    vacant_without_plan["roles"][2]["vacancy_plan"] = None  # type: ignore[index]
    with pytest.raises(TeamWorkspaceContractError, match="vacant role requires a plan"):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(vacant_without_plan))


def test_access_recommendations_are_exact_but_never_authoritative() -> None:
    payload = _payload()
    payload["access_recommendations"][0]["campaign_id"] = uuid4()  # type: ignore[index]
    with pytest.raises(TeamWorkspaceContractError, match="cross-campaign access recommendation"):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(payload))

    invalid = deepcopy(_payload()["access_recommendations"][0])  # type: ignore[index]
    invalid["authority_effect"] = "GRANT"
    with pytest.raises(ValidationError, match="Input should be 'NONE'"):
        TeamWorkspaceUpdate.model_validate({"access_recommendations": [invalid]})


def test_access_recommendation_resource_scope_is_canonical() -> None:
    campaign_scope = _payload()
    campaign_scope["access_recommendations"][0]["resource_id"] = str(uuid4())  # type: ignore[index]
    with pytest.raises(TeamWorkspaceContractError, match="campaign-scoped resource ID"):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(campaign_scope))

    workspace_scope = _payload()
    workspace_id = uuid4()
    workspace_scope["access_recommendations"][0]["workspace_id"] = workspace_id  # type: ignore[index]
    workspace_scope["access_recommendations"][0]["resource_id"] = str(uuid4())  # type: ignore[index]
    with pytest.raises(TeamWorkspaceContractError, match="workspace-scoped resource ID"):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(workspace_scope))


def test_duplicate_record_ids_and_duplicate_raci_assignments_are_rejected() -> None:
    payload = _payload()
    payload["work_items"][0]["id"] = payload["roles"][0]["id"]  # type: ignore[index]
    with pytest.raises(TeamWorkspaceContractError, match="duplicate or colliding"):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(payload))

    payload = _payload()
    payload["work_items"][0]["assignments"].append(  # type: ignore[index]
        deepcopy(payload["work_items"][0]["assignments"][0])  # type: ignore[index]
    )
    with pytest.raises(TeamWorkspaceContractError, match="duplicate RACI assignment"):
        assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(payload))


def test_incomplete_onboarding_training_or_access_review_drives_next_action() -> None:
    onboarding = _payload()
    onboarding["roles"][0]["onboarding_status"] = "IN_PROGRESS"  # type: ignore[index]
    projection = assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(onboarding))
    assert projection.status == "STRUCTURE_IN_PROGRESS"
    assert projection.next_action == "COMPLETE_ONBOARDING"

    training = _payload()
    training["training_requirements"][0]["status"] = "IN_PROGRESS"  # type: ignore[index]
    projection = assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(training))
    assert projection.next_action == "COMPLETE_TRAINING"

    access = _payload()
    access["access_recommendations"][0]["status"] = "PROPOSED"  # type: ignore[index]
    projection = assess_team_workspace(TeamWorkspaceAssessmentInput.model_validate(access))
    assert projection.next_action == "REVIEW_ACCESS_RECOMMENDATIONS"
