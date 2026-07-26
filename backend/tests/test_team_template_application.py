from datetime import UTC, datetime
from uuid import UUID

from campaignos.teams.blueprints import canonical_blueprint_key
from campaignos.teams.contracts import (
    TeamWorkspaceAssessmentInput,
    TeamWorkspaceTemplatePreviewRequest,
    assess_team_workspace,
)
from campaignos.teams.template_application import build_team_template_preview

WORKSPACE_ID = UUID("11111111-1111-4111-8111-111111111111")
TENANT_ID = UUID("22222222-2222-4222-8222-222222222222")
CAMPAIGN_ID = UUID("33333333-3333-4333-8333-333333333333")


def workspace(*, version: int = 3):
    return assess_team_workspace(
        TeamWorkspaceAssessmentInput(
            id=WORKSPACE_ID,
            tenant_id=TENANT_ID,
            campaign_id=CAMPAIGN_ID,
            campaign_version=4,
            campaign_status="ACTIVE",
            campaign_name="Campaign",
            organization_template="LEAN_CAMPAIGN",
            roles=[
                {
                    "id": UUID("44444444-4444-4444-8444-444444444441"),
                    "title": "Dirección de campaña",
                    "area": "Dirección de campaña",
                    "purpose": "Coordinar decisiones humanas.",
                    "responsibilities": ["Coordinar prioridades"],
                    "status": "FILLED",
                    "principal_id": UUID("55555555-5555-4555-8555-555555555555"),
                    "availability_status": "AVAILABLE",
                    "weekly_capacity_hours": 40,
                    "onboarding_status": "COMPLETE",
                    "vacancy_plan": None,
                },
                {
                    "id": UUID("44444444-4444-4444-8444-444444444442"),
                    "title": "Investigación y evidencia",
                    "area": "Investigación electoral",
                    "purpose": "Mantener evidencia verificable.",
                    "responsibilities": ["Verificar fuentes"],
                    "status": "VACANT",
                    "principal_id": None,
                    "availability_status": "UNASSESSED",
                    "weekly_capacity_hours": None,
                    "onboarding_status": "NOT_STARTED",
                    "vacancy_plan": "Cubrir mediante selección humana.",
                },
                {
                    "id": UUID("44444444-4444-4444-8444-444444444443"),
                    "title": "Territorio y organización",
                    "area": "Territorio",
                    "purpose": "Coordinar territorio.",
                    "responsibilities": ["Coordinar cobertura"],
                    "status": "VACANT",
                    "principal_id": None,
                    "availability_status": "UNASSESSED",
                    "weekly_capacity_hours": None,
                    "onboarding_status": "NOT_STARTED",
                    "vacancy_plan": "Cubrir mediante selección humana.",
                },
            ],
            work_items=None,
            training_requirements=None,
            access_recommendations=None,
            version=version,
            created_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
            updated_at=datetime(2026, 7, 21, 12, tzinfo=UTC),
        )
    )


def test_preview_recognizes_spanish_roles_when_full_template_is_english() -> None:
    preview = build_team_template_preview(
        workspace(),
        TeamWorkspaceTemplatePreviewRequest(
            organization_template="FULL_CAMPAIGN", blueprint_locale="en"
        ),
    )

    assert preview.added_role_count == 5
    assert preview.skipped_role_count == 3
    assert {item.blueprint_key for item in preview.skipped} == {
        "campaign_direction",
        "research_evidence",
        "territory_organization",
    }
    assert {role.title for role in preview.additions} == {
        "Digital Strategy",
        "Political Content",
        "Paid Media and Distribution",
        "Storytelling, Speech, and Media Training",
        "Tracking, Risks, and Learning",
    }
    assert all(role.principal_id is None for role in preview.additions)
    assert preview.authority_effect == preview.external_effects == "NONE"


def test_preview_is_deterministic_and_version_bound() -> None:
    request = TeamWorkspaceTemplatePreviewRequest(
        organization_template="FULL_CAMPAIGN", blueprint_locale="en"
    )
    first = build_team_template_preview(workspace(), request)
    replay = build_team_template_preview(workspace(), request)
    changed = build_team_template_preview(workspace(version=4), request)

    assert replay == first
    assert replay.preview_digest == first.preview_digest
    assert [role.id for role in replay.additions] == [role.id for role in first.additions]
    assert changed.preview_digest != first.preview_digest
    assert [role.id for role in changed.additions] != [role.id for role in first.additions]


def test_canonical_identity_is_bilingual() -> None:
    assert (
        canonical_blueprint_key("Campaign Direction", "Campaign leadership") == "campaign_direction"
    )
    assert (
        canonical_blueprint_key("Dirección de campaña", "Dirección de campaña")
        == "campaign_direction"
    )
    assert canonical_blueprint_key("Custom role", "Custom") is None
