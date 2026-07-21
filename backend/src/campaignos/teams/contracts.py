"""Typed contracts and deterministic assessment for campaign team workspaces."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

OrganizationTemplate = Literal["LEAN_CAMPAIGN", "FULL_CAMPAIGN", "CUSTOM"]
RoleStatus = Literal["FILLED", "VACANT"]
AvailabilityStatus = Literal["UNASSESSED", "AVAILABLE", "LIMITED", "UNAVAILABLE"]
ProgressStatus = Literal["NOT_STARTED", "IN_PROGRESS", "COMPLETE"]
WorkItemStatus = Literal["PLANNED", "ACTIVE", "BLOCKED", "COMPLETE"]
RaciResponsibility = Literal["RESPONSIBLE", "ACCOUNTABLE", "CONSULTED", "INFORMED"]
AccessReviewStatus = Literal["PROPOSED", "REVIEWED", "REJECTED"]
TeamWorkspaceStatus = Literal["SETUP_REQUIRED", "STRUCTURE_IN_PROGRESS", "READY_FOR_HUMAN_REVIEW"]
TeamCheckKey = Literal[
    "organization_template",
    "role_cards",
    "accountability",
    "availability",
    "vacancies",
    "onboarding",
    "training",
    "access_review",
]
TeamNextAction = Literal[
    "SELECT_ORGANIZATION_TEMPLATE",
    "DEFINE_ROLE_CARDS",
    "ASSIGN_ACCOUNTABILITY",
    "ASSESS_AVAILABILITY",
    "PLAN_VACANCIES",
    "COMPLETE_ONBOARDING",
    "COMPLETE_TRAINING",
    "REVIEW_ACCESS_RECOMMENDATIONS",
    "CONTINUE_HUMAN_GOVERNANCE",
]
TeamLimitation = Literal[
    "ROLE_LABELS_ARE_NOT_PERMISSIONS",
    "ACCESS_RECOMMENDATIONS_REQUIRE_HUMAN_AUTHORIZATION",
    "NO_VOTER_PROFILING",
    "NO_EXTERNAL_EFFECTS",
]

CHECK_ORDER: tuple[TeamCheckKey, ...] = (
    "organization_template",
    "role_cards",
    "accountability",
    "availability",
    "vacancies",
    "onboarding",
    "training",
    "access_review",
)
LIMITATION_CODES: tuple[TeamLimitation, ...] = (
    "ROLE_LABELS_ARE_NOT_PERMISSIONS",
    "ACCESS_RECOMMENDATIONS_REQUIRE_HUMAN_AUTHORIZATION",
    "NO_VOTER_PROFILING",
    "NO_EXTERNAL_EFFECTS",
)
_PERSONAL_PATH = re.compile(r"(?:/Users/[^/]+|/home/[^/]+|[A-Za-z]:\\Users\\[^\\]+)")


class TeamWorkspaceContractError(ValueError):
    """A structurally valid team document violates an organizational invariant."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise TeamWorkspaceContractError(message)


def _normalize_text(value: object, *, label: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{label} must not be blank")
    if len(normalized) > maximum:
        raise ValueError(f"{label} must not exceed {maximum} characters")
    if _PERSONAL_PATH.search(normalized):
        raise ValueError(f"{label} must not contain a personal filesystem path")
    if "../" in normalized or "..\\" in normalized:
        raise ValueError(f"{label} must not contain path traversal")
    return normalized


def _normalize_optional_text(value: object, *, label: str, maximum: int) -> str | None:
    if value is None:
        return None
    return _normalize_text(value, label=label, maximum=maximum)


def _normalize_text_list(value: object, *, label: str, maximum: int) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be an array")
    if not value:
        raise ValueError(f"{label} must contain at least one item")
    if len(value) > maximum:
        raise ValueError(f"{label} must contain at most {maximum} items")
    normalized = tuple(
        _normalize_text(item, label=f"{label}[{index}]", maximum=500)
        for index, item in enumerate(value)
    )
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{label} contains duplicate items")
    return normalized


def _bound_models(value: object, *, label: str, maximum: int) -> object:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be an array or null")
    if len(value) > maximum:
        raise ValueError(f"{label} must contain at most {maximum} items")
    return value


class TeamRoleCard(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    title: str = Field(min_length=1, max_length=160)
    area: str = Field(min_length=1, max_length=160)
    purpose: str = Field(min_length=1, max_length=1000)
    responsibilities: tuple[str, ...] = Field(min_length=1, max_length=20)
    status: RoleStatus
    principal_id: UUID | None
    availability_status: AvailabilityStatus
    weekly_capacity_hours: int | None = Field(default=None, ge=0, le=168)
    onboarding_status: ProgressStatus
    vacancy_plan: str | None = Field(default=None, max_length=1000)

    @field_validator("title", "area", mode="before")
    @classmethod
    def normalize_short_text(cls, value: object, info: object) -> str:
        return _normalize_text(
            value,
            label=str(getattr(info, "field_name", "role")),
            maximum=160,
        )

    @field_validator("purpose", mode="before")
    @classmethod
    def normalize_purpose(cls, value: object) -> str:
        return _normalize_text(value, label="role purpose", maximum=1000)

    @field_validator("responsibilities", mode="before")
    @classmethod
    def normalize_responsibilities(cls, value: object) -> tuple[str, ...]:
        return _normalize_text_list(value, label="role responsibilities", maximum=20)

    @field_validator("vacancy_plan", mode="before")
    @classmethod
    def normalize_vacancy_plan(cls, value: object) -> str | None:
        return _normalize_optional_text(value, label="vacancy plan", maximum=1000)


class RaciAssignment(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    role_id: UUID
    responsibility: RaciResponsibility


class TeamWorkItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    name: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=2000)
    status: WorkItemStatus
    assignments: tuple[RaciAssignment, ...] = Field(min_length=1, max_length=50)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> str:
        return _normalize_text(value, label="work item name", maximum=255)

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: object) -> str:
        return _normalize_text(value, label="work item description", maximum=2000)


class TeamTrainingRequirement(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    role_id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=2000)
    status: ProgressStatus

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> str:
        return _normalize_text(value, label="training title", maximum=255)

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: object) -> str:
        return _normalize_text(value, label="training description", maximum=2000)


class TeamAccessRecommendation(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    role_id: UUID
    campaign_id: UUID
    workspace_id: UUID | None
    action: str = Field(min_length=1, max_length=100)
    resource_type: str = Field(min_length=1, max_length=100)
    resource_id: str = Field(min_length=1, max_length=255)
    purpose: str = Field(min_length=1, max_length=500)
    status: AccessReviewStatus
    authority_effect: Literal["NONE"] = "NONE"

    @field_validator("action", "resource_type", mode="before")
    @classmethod
    def normalize_identifier(cls, value: object, info: object) -> str:
        return _normalize_text(
            value,
            label=str(getattr(info, "field_name", "access")),
            maximum=100,
        )

    @field_validator("resource_id", mode="before")
    @classmethod
    def normalize_resource_id(cls, value: object) -> str:
        return _normalize_text(value, label="resource_id", maximum=255)

    @field_validator("purpose", mode="before")
    @classmethod
    def normalize_purpose(cls, value: object) -> str:
        return _normalize_text(value, label="access purpose", maximum=500)


class TeamWorkspaceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_template: OrganizationTemplate


class TeamWorkspaceUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    organization_template: OrganizationTemplate | None = None
    roles: tuple[TeamRoleCard, ...] | None = None
    work_items: tuple[TeamWorkItem, ...] | None = None
    training_requirements: tuple[TeamTrainingRequirement, ...] | None = None
    access_recommendations: tuple[TeamAccessRecommendation, ...] | None = None

    @field_validator("roles", mode="before")
    @classmethod
    def bound_roles(cls, value: object) -> object:
        return _bound_models(value, label="roles", maximum=100)

    @field_validator("work_items", mode="before")
    @classmethod
    def bound_work_items(cls, value: object) -> object:
        return _bound_models(value, label="work_items", maximum=200)

    @field_validator("training_requirements", "access_recommendations", mode="before")
    @classmethod
    def bound_supporting_records(cls, value: object, info: object) -> object:
        return _bound_models(
            value,
            label=str(getattr(info, "field_name", "records")),
            maximum=200,
        )

    @model_validator(mode="after")
    def validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("team workspace update requires at least one field")
        if "organization_template" in self.model_fields_set and self.organization_template is None:
            raise ValueError("organization_template cannot be null")
        return self


class TeamWorkspaceAssessmentInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    campaign_version: int = Field(ge=1)
    campaign_status: Literal["DRAFT", "ACTIVE"]
    campaign_name: str = Field(min_length=1, max_length=255)
    organization_template: OrganizationTemplate
    roles: tuple[TeamRoleCard, ...] | None = Field(default=None, max_length=100)
    work_items: tuple[TeamWorkItem, ...] | None = Field(default=None, max_length=200)
    training_requirements: tuple[TeamTrainingRequirement, ...] | None = Field(
        default=None, max_length=200
    )
    access_recommendations: tuple[TeamAccessRecommendation, ...] | None = Field(
        default=None, max_length=200
    )
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_timestamps(self) -> Self:
        if self.created_at.utcoffset() is None or self.updated_at.utcoffset() is None:
            raise ValueError("team workspace timestamps must include a timezone")
        return self


class TeamWorkspaceCheck(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: TeamCheckKey
    complete: bool
    reason_code: str = Field(min_length=1, max_length=100)


class TeamWorkspaceProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    campaign_version: int = Field(ge=1)
    campaign_status: Literal["DRAFT", "ACTIVE"]
    campaign_name: str
    organization_template: OrganizationTemplate
    roles: tuple[TeamRoleCard, ...] | None
    work_items: tuple[TeamWorkItem, ...] | None
    training_requirements: tuple[TeamTrainingRequirement, ...] | None
    access_recommendations: tuple[TeamAccessRecommendation, ...] | None
    status: TeamWorkspaceStatus
    checks: tuple[TeamWorkspaceCheck, ...]
    completed_checks: int = Field(ge=0)
    total_checks: int = Field(ge=1)
    filled_role_count: int = Field(ge=0)
    vacant_role_count: int = Field(ge=0)
    total_weekly_capacity_hours: int = Field(ge=0)
    next_action: TeamNextAction
    authority_effect: Literal["NONE"] = "NONE"
    external_effects: Literal["NONE"] = "NONE"
    limitation_codes: tuple[TeamLimitation, ...]
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime


class TeamWorkspaceCreateEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace: TeamWorkspaceProjection
    audit_event_id: UUID
    outbox_event_id: UUID


class TeamWorkspaceReadEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace: TeamWorkspaceProjection
    audit_event_id: UUID


class TeamWorkspaceUpdateEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace: TeamWorkspaceProjection
    audit_event_id: UUID
    outbox_event_id: UUID


def _register_ids(value: TeamWorkspaceAssessmentInput) -> set[UUID]:
    ids: set[UUID] = {value.id}
    record_ids: list[UUID] = []
    for collection in (
        value.roles,
        value.work_items,
        value.training_requirements,
        value.access_recommendations,
    ):
        if collection is not None:
            record_ids.extend(item.id for item in collection)
    for record_id in record_ids:
        _require(record_id not in ids, f"duplicate or colliding team record ID: {record_id}")
        ids.add(record_id)
    return ids


def assess_team_workspace(value: TeamWorkspaceAssessmentInput) -> TeamWorkspaceProjection:
    """Derive organizational readiness without creating application authority."""
    _register_ids(value)
    roles_by_id = {role.id: role for role in value.roles or ()}
    _require(len(roles_by_id) == len(value.roles or ()), "duplicate role IDs")

    for role in value.roles or ():
        if role.status == "FILLED":
            _require(role.principal_id is not None, f"filled role requires a principal: {role.id}")
            _require(
                role.vacancy_plan is None, f"filled role cannot have a vacancy plan: {role.id}"
            )
        else:
            _require(role.principal_id is None, f"vacant role cannot have a principal: {role.id}")
            _require(
                role.weekly_capacity_hours is None, f"vacant role cannot have capacity: {role.id}"
            )
            _require(
                role.availability_status == "UNASSESSED",
                f"vacant role availability must be unassessed: {role.id}",
            )
            _require(role.vacancy_plan is not None, f"vacant role requires a plan: {role.id}")

    for work_item in value.work_items or ():
        seen_assignments: set[tuple[UUID, RaciResponsibility]] = set()
        accountable = 0
        responsible = 0
        for assignment in work_item.assignments:
            _require(
                assignment.role_id in roles_by_id,
                f"unknown role reference {assignment.role_id} from work item {work_item.id}",
            )
            assigned_role = roles_by_id[assignment.role_id]
            if work_item.status in {"ACTIVE", "BLOCKED"} and assignment.responsibility in {
                "ACCOUNTABLE",
                "RESPONSIBLE",
            }:
                _require(
                    assigned_role.status == "FILLED",
                    f"active accountability requires a filled role: {assignment.role_id}",
                )
            key = (assignment.role_id, assignment.responsibility)
            _require(
                key not in seen_assignments,
                f"duplicate RACI assignment in work item {work_item.id}",
            )
            seen_assignments.add(key)
            accountable += assignment.responsibility == "ACCOUNTABLE"
            responsible += assignment.responsibility == "RESPONSIBLE"
        _require(
            accountable == 1, f"work item requires exactly one accountable role: {work_item.id}"
        )
        _require(
            responsible >= 1, f"work item requires at least one responsible role: {work_item.id}"
        )

    for requirement in value.training_requirements or ():
        _require(
            requirement.role_id in roles_by_id,
            f"unknown role reference {requirement.role_id} from training {requirement.id}",
        )
    for recommendation in value.access_recommendations or ():
        _require(
            recommendation.role_id in roles_by_id,
            (
                f"unknown role reference {recommendation.role_id} "
                f"from access recommendation {recommendation.id}"
            ),
        )
        _require(
            recommendation.campaign_id == value.campaign_id,
            f"cross-campaign access recommendation: {recommendation.id}",
        )
        if recommendation.workspace_id is None:
            _require(
                recommendation.resource_id == str(value.campaign_id),
                f"campaign-scoped resource ID must match campaign: {recommendation.id}",
            )
        else:
            _require(
                recommendation.resource_id == str(recommendation.workspace_id),
                f"workspace-scoped resource ID must match workspace: {recommendation.id}",
            )

    roles_defined = bool(value.roles)
    accountability_complete = bool(value.work_items)
    availability_complete = value.roles is not None and all(
        role.status == "VACANT"
        or (
            role.availability_status in {"AVAILABLE", "LIMITED"}
            and role.weekly_capacity_hours is not None
            and role.weekly_capacity_hours > 0
        )
        for role in value.roles
    )
    vacancies_complete = value.roles is not None
    onboarding_complete = value.roles is not None and all(
        role.status == "VACANT" or role.onboarding_status == "COMPLETE" for role in value.roles
    )
    training_complete = value.training_requirements is not None and all(
        requirement.status == "COMPLETE" for requirement in value.training_requirements
    )
    access_complete = value.access_recommendations is not None and all(
        recommendation.status in {"REVIEWED", "REJECTED"}
        for recommendation in value.access_recommendations
    )

    checks = (
        TeamWorkspaceCheck(
            key="organization_template",
            complete=True,
            reason_code="ORGANIZATION_TEMPLATE_SELECTED",
        ),
        TeamWorkspaceCheck(
            key="role_cards",
            complete=roles_defined,
            reason_code="ROLE_CARDS_DEFINED" if roles_defined else "ROLE_CARDS_MISSING",
        ),
        TeamWorkspaceCheck(
            key="accountability",
            complete=accountability_complete,
            reason_code=(
                "RACI_ACCOUNTABILITY_DEFINED"
                if accountability_complete
                else "RACI_ACCOUNTABILITY_MISSING"
            ),
        ),
        TeamWorkspaceCheck(
            key="availability",
            complete=availability_complete,
            reason_code=(
                "AVAILABILITY_ASSESSED" if availability_complete else "AVAILABILITY_GAPS_REMAIN"
            ),
        ),
        TeamWorkspaceCheck(
            key="vacancies",
            complete=vacancies_complete,
            reason_code="VACANCIES_IDENTIFIED" if vacancies_complete else "VACANCIES_NOT_ASSESSED",
        ),
        TeamWorkspaceCheck(
            key="onboarding",
            complete=onboarding_complete,
            reason_code=(
                "FILLED_ROLES_ONBOARDED" if onboarding_complete else "ONBOARDING_INCOMPLETE"
            ),
        ),
        TeamWorkspaceCheck(
            key="training",
            complete=training_complete,
            reason_code="TRAINING_COMPLETE" if training_complete else "TRAINING_INCOMPLETE",
        ),
        TeamWorkspaceCheck(
            key="access_review",
            complete=access_complete,
            reason_code=(
                "ACCESS_RECOMMENDATIONS_REVIEWED"
                if access_complete
                else "ACCESS_RECOMMENDATIONS_PENDING"
            ),
        ),
    )
    completed_checks = sum(check.complete for check in checks)
    if not roles_defined:
        status: TeamWorkspaceStatus = "SETUP_REQUIRED"
    elif completed_checks != len(checks):
        status = "STRUCTURE_IN_PROGRESS"
    else:
        status = "READY_FOR_HUMAN_REVIEW"

    if not roles_defined:
        next_action: TeamNextAction = "DEFINE_ROLE_CARDS"
    elif not accountability_complete:
        next_action = "ASSIGN_ACCOUNTABILITY"
    elif not availability_complete:
        next_action = "ASSESS_AVAILABILITY"
    elif not vacancies_complete:
        next_action = "PLAN_VACANCIES"
    elif not onboarding_complete:
        next_action = "COMPLETE_ONBOARDING"
    elif not training_complete:
        next_action = "COMPLETE_TRAINING"
    elif not access_complete:
        next_action = "REVIEW_ACCESS_RECOMMENDATIONS"
    else:
        next_action = "CONTINUE_HUMAN_GOVERNANCE"

    filled_roles = tuple(role for role in value.roles or () if role.status == "FILLED")
    vacant_roles = tuple(role for role in value.roles or () if role.status == "VACANT")
    total_capacity = sum(role.weekly_capacity_hours or 0 for role in filled_roles)

    return TeamWorkspaceProjection(
        id=value.id,
        tenant_id=value.tenant_id,
        campaign_id=value.campaign_id,
        campaign_version=value.campaign_version,
        campaign_status=value.campaign_status,
        campaign_name=value.campaign_name,
        organization_template=value.organization_template,
        roles=value.roles,
        work_items=value.work_items,
        training_requirements=value.training_requirements,
        access_recommendations=value.access_recommendations,
        status=status,
        checks=checks,
        completed_checks=completed_checks,
        total_checks=len(checks),
        filled_role_count=len(filled_roles),
        vacant_role_count=len(vacant_roles),
        total_weekly_capacity_hours=total_capacity,
        next_action=next_action,
        limitation_codes=LIMITATION_CODES,
        version=value.version,
        created_at=value.created_at,
        updated_at=value.updated_at,
    )
