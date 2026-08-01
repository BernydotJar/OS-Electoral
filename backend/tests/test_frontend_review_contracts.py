from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
REVIEW_SCRIPTS = (
    ROOT / "scripts/frontend/review_dynamic_shell.py",
    ROOT / "scripts/frontend/review_functional_onboarding.py",
)
RETIRED_CANDIDATE_TAB_SELECTORS = (
    'get_by_role("tab", name="Qué hacer ahora")',
    'get_by_role("tab", name="Perfil y riesgos")',
    'get_by_role("tab", name="Fuentes y evidencia")',
    'get_by_role("tab", name="What to do now")',
    'get_by_role("tab", name="Profile and risks")',
    'get_by_role("tab", name="Sources and evidence")',
)


@pytest.mark.parametrize("script", REVIEW_SCRIPTS, ids=lambda path: path.name)
def test_candidate_review_scripts_use_the_single_profile_contract(script: Path) -> None:
    source = script.read_text(encoding="utf-8")

    assert ".candidate-evidence-disclosure" in source
    for selector in RETIRED_CANDIDATE_TAB_SELECTORS:
        assert selector not in source
