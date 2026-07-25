from uuid import UUID

from campaignos.teams.blueprints import build_role_blueprints


def test_lean_blueprint_creates_five_safe_vacant_job_descriptions() -> None:
    roles = build_role_blueprints("LEAN_CAMPAIGN", "es")

    assert roles is not None and len(roles) == 5
    assert len({role.id for role in roles}) == 5
    assert {role.title for role in roles} >= {
        "Dirección de campaña",
        "Investigación y evidencia",
        "Territorio y organización",
    }
    for role in roles:
        assert isinstance(role.id, UUID)
        assert role.status == "VACANT"
        assert role.principal_id is None
        assert role.weekly_capacity_hours is None
        assert role.availability_status == "UNASSESSED"
        assert role.onboarding_status == "NOT_STARTED"
        assert role.purpose
        assert len(role.responsibilities) >= 3
        assert role.vacancy_plan


def test_lean_blueprint_preserves_the_same_five_functions_in_english() -> None:
    roles = build_role_blueprints("LEAN_CAMPAIGN", "en")

    assert roles is not None
    assert {role.title for role in roles} == {
        "Campaign Direction",
        "Research and Evidence",
        "Territory and Organization",
        "Communications and Narrative",
        "Administration, Legal, and Finance",
    }


def test_full_blueprint_matches_the_eight_operating_stations() -> None:
    roles = build_role_blueprints("FULL_CAMPAIGN", "en")

    assert roles is not None and len(roles) == 8
    assert {role.title for role in roles} == {
        "Campaign Chief",
        "Electoral Research",
        "Digital Strategy",
        "Territory and Mobilization",
        "Political Content",
        "Paid Media and Distribution",
        "Storytelling, Speech, and Media Training",
        "Tracking, Risks, and Learning",
    }


def test_custom_blueprint_does_not_impose_roles() -> None:
    assert build_role_blueprints("CUSTOM", "es") is None
