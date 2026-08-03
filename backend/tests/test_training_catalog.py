from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError

from campaignos.data.audit import canonical_hash
from campaignos.training.catalog import (
    CATALOG,
    CATALOG_DIGEST,
    grade_attempt,
    module_by_ref,
    project_catalog,
)
from campaignos.training.contracts import (
    TrainingAnswerSubmission,
    TrainingCatalog,
    TrainingLocalizedModule,
)


def correct_answers(module_id: str) -> tuple[TrainingAnswerSubmission, ...]:
    module = module_by_ref(module_id, "1.0.0")
    return tuple(
        TrainingAnswerSubmission(
            question_id=question.id,
            option_ids=question.correct_option_ids,
        )
        for question in module.localized("es").questions
    )


def test_catalog_is_bilingual_bounded_and_deterministic() -> None:
    assert len(CATALOG.modules) == 6
    assert len(CATALOG.paths) == 6
    assert CATALOG_DIGEST == canonical_hash(CATALOG.model_dump(mode="python"))
    assert CATALOG.authority_effect == "NONE"
    assert CATALOG.external_effects == "NONE"
    assert all(
        {localized.locale for localized in module.locales} == {"es", "en"}
        for module in CATALOG.modules
    )
    assert all(len(module.localized("es").lessons) <= 20 for module in CATALOG.modules)
    assert all(len(module.localized("es").questions) <= 20 for module in CATALOG.modules)


def test_catalog_projection_hides_answer_keys_and_preserves_locale() -> None:
    spanish = project_catalog("es")
    english = project_catalog("en")
    assert spanish.catalog_digest == english.catalog_digest == CATALOG_DIGEST
    assert spanish.modules[0].title == "Investigar antes de actuar"
    assert english.modules[0].title == "Research before action"
    assert "correct_option_ids" not in str(spanish.model_dump(mode="python"))
    assert spanish.authority_effect == spanish.external_effects == "NONE"


def test_catalog_rejects_html_remote_content_and_unknown_fields() -> None:
    localized = CATALOG.modules[0].localized("es").model_dump(mode="python")
    localized["summary"] = "<script>alert(1)</script>"
    with pytest.raises(ValidationError, match="prohibited markup"):
        TrainingLocalizedModule.model_validate(localized)

    localized = CATALOG.modules[0].localized("es").model_dump(mode="python")
    localized["lessons"][0]["body"] = "See https://tracking.example.test"
    with pytest.raises(ValidationError, match="remote content"):
        TrainingLocalizedModule.model_validate(localized)

    localized = CATALOG.modules[0].localized("es").model_dump(mode="python")
    localized["ranking"] = 99
    with pytest.raises(ValidationError, match="Extra inputs"):
        TrainingLocalizedModule.model_validate(localized)


def test_catalog_rejects_locale_structure_and_answer_key_drift() -> None:
    payload = CATALOG.model_dump(mode="python")
    payload["modules"][0]["locales"][1]["questions"][0]["id"] = "different_question"
    with pytest.raises(ValidationError, match="question structure"):
        TrainingCatalog.model_validate(payload)

    payload = deepcopy(CATALOG.model_dump(mode="python"))
    payload["modules"][0]["locales"][1]["questions"][0]["correct_option_ids"] = ["incorrect"]
    with pytest.raises(ValidationError, match="answer keys"):
        TrainingCatalog.model_validate(payload)


def test_deterministic_grading_requires_exact_question_and_option_sets() -> None:
    module = module_by_ref("research_foundations", "1.0.0")
    passed = grade_attempt(module, locale="es", answers=correct_answers(module.module_id))
    assert passed.result == "PASS"
    assert passed.correct_count == passed.total_questions == 1
    assert passed.authority_effect == "NONE"

    answers = list(correct_answers(module.module_id))
    answers[0] = answers[0].model_copy(update={"option_ids": ("incorrect",)})
    failed = grade_attempt(module, locale="es", answers=tuple(answers))
    assert failed.result == "FAIL"
    assert failed.correct_count == 0

    with pytest.raises(ValueError, match="every catalog question"):
        grade_attempt(module, locale="es", answers=())
    bad = list(correct_answers(module.module_id))
    bad[0] = bad[0].model_copy(update={"option_ids": ("unknown_option",)})
    with pytest.raises(ValueError, match="unknown option"):
        grade_attempt(module, locale="es", answers=tuple(bad))
