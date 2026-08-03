"""Strict contracts for the governed CampaignOS Training Academy."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Locale = Literal["es", "en"]
ModuleStatus = Literal["APPROVED", "RETIRED"]
AssignmentStatus = Literal["ASSIGNED", "IN_PROGRESS", "COMPLETED"]
ModuleProgressStatus = Literal["NOT_STARTED", "IN_PROGRESS", "COMPLETED"]
AssessmentResult = Literal["PASS", "FAIL"]
_SLUG = re.compile(r"^[a-z][a-z0-9_]{2,79}$")
_VERSION = re.compile(r"^[1-9][0-9]{0,3}\.[0-9]{1,4}\.[0-9]{1,4}$")
_FORBIDDEN = ("<", ">", "javascript:", "data:", "http://", "https://", "iframe")


def safe_text(value: object, *, label: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string")
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > maximum:
        raise ValueError(f"{label} must contain 1 to {maximum} characters")
    lowered = normalized.casefold()
    if any(marker in lowered for marker in _FORBIDDEN):
        raise ValueError(f"{label} contains prohibited markup or remote content")
    if any(ord(character) < 32 for character in normalized):
        raise ValueError(f"{label} contains control characters")
    return normalized


def slug(value: object, *, label: str) -> str:
    normalized = safe_text(value, label=label, maximum=80)
    if _SLUG.fullmatch(normalized) is None:
        raise ValueError(f"{label} must be a stable lowercase identifier")
    return normalized


def version(value: object, *, label: str) -> str:
    normalized = safe_text(value, label=label, maximum=20)
    if _VERSION.fullmatch(normalized) is None:
        raise ValueError(f"{label} must be a semantic version")
    return normalized


def source_path(value: object) -> str:
    normalized = safe_text(value, label="source reference", maximum=255)
    if not normalized.startswith("docs/") or ".." in normalized or not normalized.endswith(".md"):
        raise ValueError("source references must be repository documentation paths")
    return normalized


class StrictFrozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", strict=True)


class TrainingObjective(StrictFrozen):
    id: str
    text: str

    @field_validator("id", mode="before")
    @classmethod
    def valid_id(cls, value: object) -> str:
        return slug(value, label="objective id")

    @field_validator("text", mode="before")
    @classmethod
    def valid_text(cls, value: object) -> str:
        return safe_text(value, label="objective text", maximum=500)


class TrainingLesson(StrictFrozen):
    id: str
    title: str
    body: str
    source_refs: tuple[str, ...] = Field(min_length=1, max_length=12)

    @field_validator("id", mode="before")
    @classmethod
    def valid_id(cls, value: object) -> str:
        return slug(value, label="lesson id")

    @field_validator("title", mode="before")
    @classmethod
    def valid_title(cls, value: object) -> str:
        return safe_text(value, label="lesson title", maximum=180)

    @field_validator("body", mode="before")
    @classmethod
    def valid_body(cls, value: object) -> str:
        return safe_text(value, label="lesson body", maximum=4000)

    @field_validator("source_refs", mode="before")
    @classmethod
    def valid_sources(cls, value: object) -> object:
        if not isinstance(value, (list, tuple)):
            raise TypeError("lesson source_refs must be a list")
        return tuple(source_path(item) for item in value)

    @model_validator(mode="after")
    def unique_sources(self) -> Self:
        if len(set(self.source_refs)) != len(self.source_refs):
            raise ValueError("lesson source_refs must be unique")
        return self


class TrainingOption(StrictFrozen):
    id: str
    label: str

    @field_validator("id", mode="before")
    @classmethod
    def valid_id(cls, value: object) -> str:
        return slug(value, label="option id")

    @field_validator("label", mode="before")
    @classmethod
    def valid_label(cls, value: object) -> str:
        return safe_text(value, label="option label", maximum=300)


class TrainingQuestion(StrictFrozen):
    id: str
    prompt: str
    options: tuple[TrainingOption, ...] = Field(min_length=2, max_length=6)
    correct_option_ids: tuple[str, ...] = Field(min_length=1, max_length=6)
    explanation: str

    @field_validator("id", mode="before")
    @classmethod
    def valid_id(cls, value: object) -> str:
        return slug(value, label="question id")

    @field_validator("prompt", mode="before")
    @classmethod
    def valid_prompt(cls, value: object) -> str:
        return safe_text(value, label="question prompt", maximum=600)

    @field_validator("correct_option_ids", mode="before")
    @classmethod
    def valid_correct_ids(cls, value: object) -> object:
        if not isinstance(value, (list, tuple)):
            raise TypeError("correct_option_ids must be a list")
        return tuple(slug(item, label="correct option id") for item in value)

    @field_validator("explanation", mode="before")
    @classmethod
    def valid_explanation(cls, value: object) -> str:
        return safe_text(value, label="question explanation", maximum=1000)

    @model_validator(mode="after")
    def validate_options(self) -> Self:
        option_ids = [item.id for item in self.options]
        if len(set(option_ids)) != len(option_ids):
            raise ValueError("question option ids must be unique")
        if len(set(self.correct_option_ids)) != len(self.correct_option_ids):
            raise ValueError("correct option ids must be unique")
        if not set(self.correct_option_ids) <= set(option_ids):
            raise ValueError("correct option ids must reference question options")
        return self


class TrainingLocalizedModule(StrictFrozen):
    locale: Locale
    title: str
    summary: str
    objectives: tuple[TrainingObjective, ...] = Field(min_length=1, max_length=20)
    lessons: tuple[TrainingLesson, ...] = Field(min_length=1, max_length=20)
    questions: tuple[TrainingQuestion, ...] = Field(min_length=1, max_length=20)

    @field_validator("title", mode="before")
    @classmethod
    def valid_title(cls, value: object) -> str:
        return safe_text(value, label="module title", maximum=180)

    @field_validator("summary", mode="before")
    @classmethod
    def valid_summary(cls, value: object) -> str:
        return safe_text(value, label="module summary", maximum=800)

    @model_validator(mode="after")
    def unique_structure(self) -> Self:
        groups = (self.objectives, self.lessons, self.questions)
        if any(len({item.id for item in group}) != len(group) for group in groups):
            raise ValueError("module structure ids must be unique")
        return self


class TrainingModule(StrictFrozen):
    module_id: str
    version: str
    status: ModuleStatus
    owner: str
    reviewer: str
    passing_percent: int = Field(ge=1, le=100)
    sources: tuple[str, ...] = Field(min_length=1, max_length=20)
    locales: tuple[TrainingLocalizedModule, ...] = Field(min_length=2, max_length=2)
    authority_effect: Literal["NONE"] = "NONE"
    external_effects: Literal["NONE"] = "NONE"

    @field_validator("module_id", mode="before")
    @classmethod
    def valid_module_id(cls, value: object) -> str:
        return slug(value, label="module id")

    @field_validator("version", mode="before")
    @classmethod
    def valid_version(cls, value: object) -> str:
        return version(value, label="module version")

    @field_validator("owner", "reviewer", mode="before")
    @classmethod
    def valid_governance(cls, value: object) -> str:
        return safe_text(value, label="governance label", maximum=160)

    @field_validator("sources", mode="before")
    @classmethod
    def valid_sources(cls, value: object) -> object:
        if not isinstance(value, (list, tuple)):
            raise TypeError("module sources must be a list")
        return tuple(source_path(item) for item in value)

    @model_validator(mode="after")
    def locale_parity(self) -> Self:
        localized = {item.locale: item for item in self.locales}
        if set(localized) != {"es", "en"} or len(localized) != 2:
            raise ValueError("modules require exactly one Spanish and one English locale")
        es, en = localized["es"], localized["en"]
        if [x.id for x in es.objectives] != [x.id for x in en.objectives]:
            raise ValueError("module objective structure must match across locales")
        if [x.id for x in es.lessons] != [x.id for x in en.lessons]:
            raise ValueError("module lesson structure must match across locales")
        if [x.id for x in es.questions] != [x.id for x in en.questions]:
            raise ValueError("module question structure must match across locales")
        for left, right in zip(es.questions, en.questions, strict=True):
            if [x.id for x in left.options] != [x.id for x in right.options]:
                raise ValueError("question option structure must match across locales")
            if left.correct_option_ids != right.correct_option_ids:
                raise ValueError("question answer keys must match across locales")
        lesson_sources = {
            source
            for locale in self.locales
            for lesson in locale.lessons
            for source in lesson.source_refs
        }
        if not lesson_sources <= set(self.sources):
            raise ValueError("lesson sources must be declared by the module")
        return self

    def localized(self, locale: Locale) -> TrainingLocalizedModule:
        return next(item for item in self.locales if item.locale == locale)


class TrainingPathModule(StrictFrozen):
    module_id: str
    version: str
    required: bool = True

    @field_validator("module_id", mode="before")
    @classmethod
    def valid_module_id(cls, value: object) -> str:
        return slug(value, label="path module id")

    @field_validator("version", mode="before")
    @classmethod
    def valid_version(cls, value: object) -> str:
        return version(value, label="path module version")


class TrainingLearningPath(StrictFrozen):
    path_id: str
    version: str
    role_slugs: tuple[str, ...] = Field(min_length=1, max_length=40)
    modules: tuple[TrainingPathModule, ...] = Field(min_length=1, max_length=20)
    authority_effect: Literal["NONE"] = "NONE"

    @field_validator("path_id", mode="before")
    @classmethod
    def valid_path_id(cls, value: object) -> str:
        return slug(value, label="path id")

    @field_validator("version", mode="before")
    @classmethod
    def valid_version(cls, value: object) -> str:
        return version(value, label="path version")

    @field_validator("role_slugs", mode="before")
    @classmethod
    def valid_roles(cls, value: object) -> object:
        if not isinstance(value, (list, tuple)):
            raise TypeError("role_slugs must be a list")
        return tuple(slug(item, label="role slug") for item in value)

    @model_validator(mode="after")
    def unique_references(self) -> Self:
        if len(set(self.role_slugs)) != len(self.role_slugs):
            raise ValueError("role slugs must be unique")
        refs = [(item.module_id, item.version) for item in self.modules]
        if len(set(refs)) != len(refs):
            raise ValueError("path module references must be unique")
        return self


class TrainingCatalog(StrictFrozen):
    schema_version: Literal["1.0"] = "1.0"
    modules: tuple[TrainingModule, ...] = Field(min_length=1, max_length=50)
    paths: tuple[TrainingLearningPath, ...] = Field(min_length=1, max_length=50)
    authority_effect: Literal["NONE"] = "NONE"
    external_effects: Literal["NONE"] = "NONE"

    @model_validator(mode="after")
    def valid_catalog(self) -> Self:
        module_refs = [(item.module_id, item.version) for item in self.modules]
        path_refs = [(item.path_id, item.version) for item in self.paths]
        if len(set(module_refs)) != len(module_refs):
            raise ValueError("catalog module/version pairs must be unique")
        if len(set(path_refs)) != len(path_refs):
            raise ValueError("catalog path/version pairs must be unique")
        known = set(module_refs)
        if any(
            (item.module_id, item.version) not in known
            for path in self.paths
            for item in path.modules
        ):
            raise ValueError("learning path references an unknown module version")
        return self


class TrainingAnswerSubmission(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    question_id: str
    option_ids: tuple[str, ...] = Field(min_length=1, max_length=6)

    @field_validator("question_id", mode="before")
    @classmethod
    def valid_question_id(cls, value: object) -> str:
        return slug(value, label="question id")

    @field_validator("option_ids", mode="before")
    @classmethod
    def valid_option_ids(cls, value: object) -> object:
        if not isinstance(value, (list, tuple)):
            raise TypeError("option_ids must be a list")
        return tuple(slug(item, label="option id") for item in value)

    @model_validator(mode="after")
    def unique_options(self) -> Self:
        if len(set(self.option_ids)) != len(self.option_ids):
            raise ValueError("submitted option ids must be unique")
        return self


class TrainingQuestionFeedback(StrictFrozen):
    question_id: str
    correct: bool
    explanation: str


class TrainingAssessmentOutcome(StrictFrozen):
    result: AssessmentResult
    correct_count: int = Field(ge=0)
    total_questions: int = Field(ge=1)
    passing_percent: int = Field(ge=1, le=100)
    feedback: tuple[TrainingQuestionFeedback, ...]
    authority_effect: Literal["NONE"] = "NONE"


class TrainingAssignmentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    principal_id: UUID
    path_id: str
    path_version: str
    catalog_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    role_slug: str | None = None
    due_at: datetime | None = None

    @field_validator("path_id", mode="before")
    @classmethod
    def valid_path_id(cls, value: object) -> str:
        return slug(value, label="path id")

    @field_validator("path_version", mode="before")
    @classmethod
    def valid_path_version(cls, value: object) -> str:
        return version(value, label="path version")

    @field_validator("role_slug", mode="before")
    @classmethod
    def valid_role_slug(cls, value: object) -> object:
        return None if value is None else slug(value, label="role slug")

    @field_validator("due_at")
    @classmethod
    def due_at_timezone(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.utcoffset() is None:
            raise ValueError("due_at must include a timezone")
        return value


class TrainingModuleStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_assignment_version: int = Field(ge=1)
    expected_progress_version: int = Field(ge=1)
    catalog_digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class TrainingAttemptRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    locale: Locale
    expected_assignment_version: int = Field(ge=1)
    expected_progress_version: int = Field(ge=1)
    catalog_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    answers: tuple[TrainingAnswerSubmission, ...] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def unique_questions(self) -> Self:
        ids = [item.question_id for item in self.answers]
        if len(set(ids)) != len(ids):
            raise ValueError("submitted question ids must be unique")
        return self


class TrainingModuleProgressProjection(StrictFrozen):
    id: UUID
    module_id: str
    module_version: str
    status: ModuleProgressStatus
    attempt_count: int = Field(ge=0, le=10)
    latest_result: AssessmentResult | None
    started_at: datetime | None
    completed_at: datetime | None
    version: int = Field(ge=1)


class TrainingAssignmentProjection(StrictFrozen):
    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    principal_id: UUID
    path_id: str
    path_version: str
    role_slug: str | None
    status: AssignmentStatus
    modules: tuple[TrainingModuleProgressProjection, ...]
    completed_modules: int = Field(ge=0)
    total_modules: int = Field(ge=1)
    next_module_id: str | None
    catalog_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    version: int = Field(ge=1)
    assigned_at: datetime
    due_at: datetime | None
    completed_at: datetime | None
    authority_effect: Literal["NONE"] = "NONE"
    external_effects: Literal["NONE"] = "NONE"


class TrainingCompletionReceiptProjection(StrictFrozen):
    id: UUID
    assignment_id: UUID
    module_progress_id: UUID
    principal_id: UUID
    module_id: str
    module_version: str
    result: Literal["PASS"]
    completed_at: datetime
    catalog_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    audit_event_id: UUID
    authority_effect: Literal["NONE"] = "NONE"
    external_effects: Literal["NONE"] = "NONE"


class TrainingCatalogOptionProjection(StrictFrozen):
    id: str
    label: str


class TrainingCatalogQuestionProjection(StrictFrozen):
    id: str
    prompt: str
    options: tuple[TrainingCatalogOptionProjection, ...]


class TrainingCatalogLessonProjection(StrictFrozen):
    id: str
    title: str
    body: str
    source_refs: tuple[str, ...]


class TrainingCatalogModuleProjection(StrictFrozen):
    module_id: str
    version: str
    status: ModuleStatus
    title: str
    summary: str
    objectives: tuple[TrainingObjective, ...]
    lessons: tuple[TrainingCatalogLessonProjection, ...]
    questions: tuple[TrainingCatalogQuestionProjection, ...]
    passing_percent: int
    sources: tuple[str, ...]
    authority_effect: Literal["NONE"] = "NONE"


class TrainingCatalogPathProjection(StrictFrozen):
    path_id: str
    version: str
    role_slugs: tuple[str, ...]
    modules: tuple[TrainingPathModule, ...]
    authority_effect: Literal["NONE"] = "NONE"


class TrainingCatalogProjection(StrictFrozen):
    locale: Locale
    catalog_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    modules: tuple[TrainingCatalogModuleProjection, ...]
    paths: tuple[TrainingCatalogPathProjection, ...]
    authority_effect: Literal["NONE"] = "NONE"
    external_effects: Literal["NONE"] = "NONE"


class TrainingAssignmentListEvidence(StrictFrozen):
    assignments: tuple[TrainingAssignmentProjection, ...]
    audit_event_id: UUID
    authority_effect: Literal["NONE"] = "NONE"


class TrainingAssignmentEvidence(StrictFrozen):
    assignment: TrainingAssignmentProjection
    audit_event_id: UUID


class TrainingAssignmentCreateEvidence(TrainingAssignmentEvidence):
    outbox_event_id: UUID


class TrainingAttemptEvidence(StrictFrozen):
    assignment: TrainingAssignmentProjection
    outcome: TrainingAssessmentOutcome
    receipt: TrainingCompletionReceiptProjection | None
    audit_event_id: UUID


class TrainingReceiptListEvidence(StrictFrozen):
    receipts: tuple[TrainingCompletionReceiptProjection, ...]
    audit_event_id: UUID
    authority_effect: Literal["NONE"] = "NONE"
