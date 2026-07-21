"""Typed contracts and deterministic assessment for guided campaign intake."""

from __future__ import annotations

from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

BudgetStatus = Literal["NOT_ASSESSED", "NO_DOCUMENT", "ROUGH_RANGE", "DOCUMENTED"]
GuidedIntakeStatus = Literal[
    "BLOCKED_BY_CAMPAIGN_SETUP",
    "IN_PROGRESS",
    "READY_FOR_RESEARCH",
]
GuidedIntakeCheckKey = Literal[
    "campaign_operational_setup",
    "office",
    "candidate_project",
    "current_team",
    "current_assets",
    "budget_status",
    "known_unknowns",
    "evidence_requirements",
]
GuidedIntakeNextAction = Literal[
    "COMPLETE_CAMPAIGN_SETUP",
    "DEFINE_TARGET_OFFICE",
    "DESCRIBE_CANDIDATE_PROJECT",
    "ASSESS_CURRENT_TEAM",
    "ASSESS_CURRENT_ASSETS",
    "ASSESS_BUDGET_EVIDENCE",
    "RECORD_KNOWN_UNKNOWNS",
    "DEFINE_EVIDENCE_REQUIREMENTS",
    "BEGIN_RESEARCH",
]
ResearchFirstAction = Literal[
    "VERIFY_OFFICE_AND_JURISDICTION_EVIDENCE",
    "VALIDATE_CANDIDATE_PROJECT_EVIDENCE",
    "ASSESS_TEAM_CAPACITY_GAPS",
    "INVENTORY_ASSET_PROVENANCE",
    "DOCUMENT_BUDGET_ASSUMPTIONS",
    "RESEARCH_KNOWN_UNKNOWNS",
    "COLLECT_REQUIRED_EVIDENCE",
]
IntakeLimitation = Literal[
    "NOT_A_STRATEGY",
    "NOT_A_HUMAN_APPROVAL",
    "NO_CITIZEN_CONTACT_OR_PROFILING",
    "NO_EXTERNAL_EFFECTS",
]

CHECK_ORDER: tuple[GuidedIntakeCheckKey, ...] = (
    "campaign_operational_setup",
    "office",
    "candidate_project",
    "current_team",
    "current_assets",
    "budget_status",
    "known_unknowns",
    "evidence_requirements",
)
RESEARCH_FIRST_ACTIONS: tuple[ResearchFirstAction, ...] = (
    "VERIFY_OFFICE_AND_JURISDICTION_EVIDENCE",
    "VALIDATE_CANDIDATE_PROJECT_EVIDENCE",
    "ASSESS_TEAM_CAPACITY_GAPS",
    "INVENTORY_ASSET_PROVENANCE",
    "DOCUMENT_BUDGET_ASSUMPTIONS",
    "RESEARCH_KNOWN_UNKNOWNS",
    "COLLECT_REQUIRED_EVIDENCE",
)
LIMITATION_CODES: tuple[IntakeLimitation, ...] = (
    "NOT_A_STRATEGY",
    "NOT_A_HUMAN_APPROVAL",
    "NO_CITIZEN_CONTACT_OR_PROFILING",
    "NO_EXTERNAL_EFFECTS",
)


def _normalize_text(value: object, *, label: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{label} must not be blank")
    if len(normalized) > maximum:
        raise ValueError(f"{label} must not exceed {maximum} characters")
    return normalized


def _normalize_optional_text(value: object, *, label: str, maximum: int) -> str | None:
    if value is None:
        return None
    return _normalize_text(value, label=label, maximum=maximum)


def _normalize_items(value: object, *, label: str) -> tuple[str, ...] | None:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be an array or null")
    if len(value) > 30:
        raise ValueError(f"{label} must contain at most 30 items")
    normalized = tuple(_normalize_text(item, label=f"{label} item", maximum=255) for item in value)
    folded = [item.casefold() for item in normalized]
    if len(folded) != len(set(folded)):
        raise ValueError(f"{label} contains a duplicate item")
    return normalized


class GuidedIntakeUpdate(BaseModel):
    """Bounded partial update; null clears an assessed field except budget status."""

    model_config = ConfigDict(extra="forbid")

    office: str | None = Field(default=None, max_length=255)
    candidate_project: str | None = Field(default=None, max_length=2000)
    current_team: tuple[str, ...] | None = None
    current_assets: tuple[str, ...] | None = None
    budget_status: BudgetStatus | None = None
    known_unknowns: tuple[str, ...] | None = None
    evidence_requirements: tuple[str, ...] | None = None

    @field_validator("office", mode="before")
    @classmethod
    def normalize_office(cls, value: object) -> str | None:
        return _normalize_optional_text(value, label="office", maximum=255)

    @field_validator("candidate_project", mode="before")
    @classmethod
    def normalize_candidate_project(cls, value: object) -> str | None:
        return _normalize_optional_text(value, label="candidate_project", maximum=2000)

    @field_validator(
        "current_team",
        "current_assets",
        "known_unknowns",
        "evidence_requirements",
        mode="before",
    )
    @classmethod
    def normalize_items(cls, value: object, info: object) -> tuple[str, ...] | None:
        field_name = getattr(info, "field_name", "items")
        return _normalize_items(value, label=str(field_name))

    @model_validator(mode="after")
    def validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("guided intake update requires at least one field")
        if "budget_status" in self.model_fields_set and self.budget_status is None:
            raise ValueError("budget_status cannot be null")
        return self


class GuidedIntakeAssessmentInput(BaseModel):
    """Server-owned campaign context plus one persisted intake row."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    campaign_version: int = Field(ge=1)
    campaign_status: Literal["DRAFT", "ACTIVE"]
    campaign_name: str = Field(min_length=1, max_length=255)
    jurisdiction: str = Field(min_length=1, max_length=255)
    stage: str = Field(min_length=1, max_length=80)
    active_workspace_count: int = Field(ge=0)
    office: str | None = Field(default=None, max_length=255)
    candidate_project: str | None = Field(default=None, max_length=2000)
    current_team: tuple[str, ...] | None = None
    current_assets: tuple[str, ...] | None = None
    budget_status: BudgetStatus
    known_unknowns: tuple[str, ...] | None = None
    evidence_requirements: tuple[str, ...] | None = None
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_timestamps(self) -> Self:
        if self.created_at.utcoffset() is None or self.updated_at.utcoffset() is None:
            raise ValueError("guided intake timestamps must include a timezone")
        return self


class GuidedIntakeCheck(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: GuidedIntakeCheckKey
    complete: bool
    reason_code: str = Field(min_length=1, max_length=100)


class GuidedIntakeProjection(BaseModel):
    """Exact read projection with deterministic progress and authority limits."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    campaign_version: int = Field(ge=1)
    campaign_status: Literal["DRAFT", "ACTIVE"]
    campaign_name: str
    jurisdiction: str
    stage: str
    active_workspace_count: int = Field(ge=0)
    readiness_scope: Literal["GUIDED_INTAKE_ONLY"] = "GUIDED_INTAKE_ONLY"
    status: GuidedIntakeStatus
    ready_for_research: bool
    office: str | None
    candidate_project: str | None
    current_team: tuple[str, ...] | None
    current_assets: tuple[str, ...] | None
    budget_status: BudgetStatus
    known_unknowns: tuple[str, ...] | None
    evidence_requirements: tuple[str, ...] | None
    completed_checks: int = Field(ge=0)
    total_checks: int = Field(ge=1)
    next_action: GuidedIntakeNextAction
    checks: tuple[GuidedIntakeCheck, ...]
    research_first_actions: tuple[ResearchFirstAction, ...]
    limitation_codes: tuple[IntakeLimitation, ...]
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime


class GuidedIntakeStartEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    intake: GuidedIntakeProjection
    audit_event_id: UUID
    outbox_event_id: UUID | None
    created: bool


class GuidedIntakeReadEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    intake: GuidedIntakeProjection
    audit_event_id: UUID


class GuidedIntakeUpdateEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    intake: GuidedIntakeProjection
    audit_event_id: UUID
    outbox_event_id: UUID


def assess_guided_intake(value: GuidedIntakeAssessmentInput) -> GuidedIntakeProjection:
    """Derive canonical progress without strategy, approval or external effects."""
    campaign_setup = bool(
        value.campaign_name.strip()
        and value.jurisdiction.strip()
        and value.stage.strip()
        and value.active_workspace_count > 0
    )
    completeness: dict[GuidedIntakeCheckKey, tuple[bool, str]] = {
        "campaign_operational_setup": (
            campaign_setup,
            "CAMPAIGN_OPERATIONAL_SETUP_COMPLETE"
            if campaign_setup
            else "CAMPAIGN_OPERATIONAL_SETUP_INCOMPLETE",
        ),
        "office": (
            value.office is not None,
            "TARGET_OFFICE_DEFINED" if value.office is not None else "TARGET_OFFICE_MISSING",
        ),
        "candidate_project": (
            value.candidate_project is not None,
            "CANDIDATE_PROJECT_DESCRIBED"
            if value.candidate_project is not None
            else "CANDIDATE_PROJECT_MISSING",
        ),
        "current_team": (
            value.current_team is not None,
            "CURRENT_TEAM_ASSESSED"
            if value.current_team is not None
            else "CURRENT_TEAM_NOT_ASSESSED",
        ),
        "current_assets": (
            value.current_assets is not None,
            "CURRENT_ASSETS_ASSESSED"
            if value.current_assets is not None
            else "CURRENT_ASSETS_NOT_ASSESSED",
        ),
        "budget_status": (
            value.budget_status != "NOT_ASSESSED",
            "BUDGET_EVIDENCE_ASSESSED"
            if value.budget_status != "NOT_ASSESSED"
            else "BUDGET_EVIDENCE_NOT_ASSESSED",
        ),
        "known_unknowns": (
            bool(value.known_unknowns),
            "KNOWN_UNKNOWNS_RECORDED" if value.known_unknowns else "KNOWN_UNKNOWNS_MISSING",
        ),
        "evidence_requirements": (
            bool(value.evidence_requirements),
            "EVIDENCE_REQUIREMENTS_DEFINED"
            if value.evidence_requirements
            else "EVIDENCE_REQUIREMENTS_MISSING",
        ),
    }
    checks = tuple(
        GuidedIntakeCheck(
            key=key,
            complete=completeness[key][0],
            reason_code=completeness[key][1],
        )
        for key in CHECK_ORDER
    )
    completed = sum(check.complete for check in checks)
    ready = completed == len(checks)
    if not campaign_setup:
        status: GuidedIntakeStatus = "BLOCKED_BY_CAMPAIGN_SETUP"
        next_action: GuidedIntakeNextAction = "COMPLETE_CAMPAIGN_SETUP"
    elif ready:
        status = "READY_FOR_RESEARCH"
        next_action = "BEGIN_RESEARCH"
    else:
        status = "IN_PROGRESS"
        next_action_by_key: dict[GuidedIntakeCheckKey, GuidedIntakeNextAction] = {
            "campaign_operational_setup": "COMPLETE_CAMPAIGN_SETUP",
            "office": "DEFINE_TARGET_OFFICE",
            "candidate_project": "DESCRIBE_CANDIDATE_PROJECT",
            "current_team": "ASSESS_CURRENT_TEAM",
            "current_assets": "ASSESS_CURRENT_ASSETS",
            "budget_status": "ASSESS_BUDGET_EVIDENCE",
            "known_unknowns": "RECORD_KNOWN_UNKNOWNS",
            "evidence_requirements": "DEFINE_EVIDENCE_REQUIREMENTS",
        }
        next_action = next(next_action_by_key[check.key] for check in checks if not check.complete)

    return GuidedIntakeProjection(
        id=value.id,
        tenant_id=value.tenant_id,
        campaign_id=value.campaign_id,
        campaign_version=value.campaign_version,
        campaign_status=value.campaign_status,
        campaign_name=value.campaign_name,
        jurisdiction=value.jurisdiction,
        stage=value.stage,
        active_workspace_count=value.active_workspace_count,
        status=status,
        ready_for_research=ready,
        office=value.office,
        candidate_project=value.candidate_project,
        current_team=value.current_team,
        current_assets=value.current_assets,
        budget_status=value.budget_status,
        known_unknowns=value.known_unknowns,
        evidence_requirements=value.evidence_requirements,
        completed_checks=completed,
        total_checks=len(checks),
        next_action=next_action,
        checks=checks,
        research_first_actions=RESEARCH_FIRST_ACTIONS if ready else (),
        limitation_codes=LIMITATION_CODES,
        version=value.version,
        created_at=value.created_at,
        updated_at=value.updated_at,
    )
