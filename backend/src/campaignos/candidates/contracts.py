"""Typed evidence contracts and deterministic assessment for candidate workspaces."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

EvidenceClassification = Literal[
    "OFFICIAL_SOURCE",
    "CAMPAIGN_RESEARCH",
    "PERCEPTION",
    "HYPOTHESIS",
    "UNKNOWN",
]
EvidenceStatus = Literal["ACCEPTED", "VERIFIED", "READY", "REJECTED", "EXPIRED"]
ClaimStatus = Literal[
    "UNKNOWN",
    "SELF_REPORTED",
    "UNDER_REVIEW",
    "EVIDENCE_PARTIAL",
    "VERIFIED",
    "REJECTED",
    "CONTRADICTED",
]
CandidateWorkspaceStatus = Literal[
    "SETUP_REQUIRED",
    "UNDER_REVIEW",
    "AWAITING_APPROVAL",
    "INTERNALLY_APPROVED",
]
CandidateSection = Literal[
    "identity",
    "biography",
    "purpose",
    "values",
    "attributes",
    "contradictions",
    "development_goals",
    "reputation",
]
CandidateCheckKey = Literal[
    "identity",
    "biography",
    "purpose",
    "values",
    "attributes",
    "contradictions",
    "development_goals",
    "reputation",
    "approvals",
]
CandidateNextAction = Literal[
    "DEFINE_IDENTITY",
    "DOCUMENT_BIOGRAPHY",
    "DEFINE_PURPOSE",
    "VERIFY_VALUES",
    "VERIFY_ATTRIBUTES",
    "REVIEW_CONTRADICTIONS",
    "DEFINE_DEVELOPMENT_GOALS",
    "REVIEW_REPUTATION_RISKS",
    "OBTAIN_SECTION_APPROVALS",
    "CONTINUE_HUMAN_GOVERNANCE",
]
CandidateLimitation = Literal[
    "NOT_PUBLIC_POSITIONING_APPROVAL",
    "NOT_A_STRATEGY",
    "NO_VOTER_PROFILING",
    "NO_EXTERNAL_EFFECTS",
    "HUMAN_REVIEW_REQUIRED",
]

SECTION_ORDER: tuple[CandidateSection, ...] = (
    "identity",
    "biography",
    "purpose",
    "values",
    "attributes",
    "contradictions",
    "development_goals",
    "reputation",
)
CHECK_ORDER: tuple[CandidateCheckKey, ...] = (*SECTION_ORDER, "approvals")
LIMITATION_CODES: tuple[CandidateLimitation, ...] = (
    "NOT_PUBLIC_POSITIONING_APPROVAL",
    "NOT_A_STRATEGY",
    "NO_VOTER_PROFILING",
    "NO_EXTERNAL_EFFECTS",
    "HUMAN_REVIEW_REQUIRED",
)
INDEPENDENT_EVIDENCE = {"OFFICIAL_SOURCE", "CAMPAIGN_RESEARCH"}
ENABLING_EVIDENCE = {"ACCEPTED", "VERIFIED", "READY"}
_PERSONAL_PATH = re.compile(r"(?:/Users/[^/]+|/home/[^/]+|[A-Za-z]:\\Users\\[^\\]+)")


class CandidateWorkspaceContractError(ValueError):
    """Candidate evidence is structurally valid but violates a domain invariant."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CandidateWorkspaceContractError(message)


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


def _normalize_model_list(
    value: object,
    *,
    label: str,
    maximum: int,
) -> object:
    if value is None:
        return None
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be an array or null")
    if len(value) > maximum:
        raise ValueError(f"{label} must contain at most {maximum} items")
    return value


def _unique_refs(value: tuple[UUID, ...], *, label: str) -> tuple[UUID, ...]:
    if len(value) != len(set(value)):
        raise ValueError(f"{label} contains duplicate evidence references")
    return value


class CandidateEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    classification: EvidenceClassification
    status: EvidenceStatus
    title: str = Field(min_length=1, max_length=255)
    source_reference: str = Field(min_length=1, max_length=2048)
    source_authority: str | None = Field(default=None, max_length=255)
    jurisdiction: str | None = Field(default=None, max_length=255)
    excerpt: str | None = Field(default=None, max_length=2000)
    observed_at: datetime | None = None

    @field_validator("title", "source_reference", mode="before")
    @classmethod
    def normalize_required_text(cls, value: object, info: object) -> str:
        field_name = str(getattr(info, "field_name", "text"))
        maximum = 2048 if field_name == "source_reference" else 255
        return _normalize_text(value, label=field_name, maximum=maximum)

    @field_validator("source_authority", "jurisdiction", mode="before")
    @classmethod
    def normalize_optional_short_text(cls, value: object, info: object) -> str | None:
        return _normalize_optional_text(
            value,
            label=str(getattr(info, "field_name", "text")),
            maximum=255,
        )

    @field_validator("excerpt", mode="before")
    @classmethod
    def normalize_excerpt(cls, value: object) -> str | None:
        return _normalize_optional_text(value, label="excerpt", maximum=2000)

    @model_validator(mode="after")
    def validate_timestamp(self) -> Self:
        if self.observed_at is not None and self.observed_at.utcoffset() is None:
            raise ValueError("evidence observed_at must include a timezone")
        return self


class CandidateClaim(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    label: str = Field(min_length=1, max_length=120)
    claim: str = Field(min_length=1, max_length=2000)
    status: ClaimStatus
    classification: EvidenceClassification
    evidence_refs: tuple[UUID, ...] = Field(max_length=20)

    @field_validator("label", mode="before")
    @classmethod
    def normalize_label(cls, value: object) -> str:
        return _normalize_text(value, label="claim label", maximum=120)

    @field_validator("claim", mode="before")
    @classmethod
    def normalize_claim(cls, value: object) -> str:
        return _normalize_text(value, label="claim", maximum=2000)

    @field_validator("evidence_refs")
    @classmethod
    def validate_refs(cls, value: tuple[UUID, ...]) -> tuple[UUID, ...]:
        return _unique_refs(value, label="claim")


class CandidateAttribute(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    name: str = Field(min_length=1, max_length=160)
    claim: str = Field(min_length=1, max_length=2000)
    status: ClaimStatus
    candidate_self_assessment: Literal["YES", "NO", "UNKNOWN"]
    team_assessment: Literal["YES", "PARTIAL", "NO", "UNKNOWN"]
    citizen_evidence: Literal["SUPPORTED", "PARTIAL", "UNRESOLVED", "CONTRADICTED"]
    evidence_refs: tuple[UUID, ...] = Field(max_length=20)
    perception_refs: tuple[UUID, ...] = Field(max_length=20)
    contradiction_refs: tuple[UUID, ...] = Field(max_length=20)
    risk: str = Field(min_length=1, max_length=1000)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> str:
        return _normalize_text(value, label="attribute name", maximum=160)

    @field_validator("claim", mode="before")
    @classmethod
    def normalize_attribute_claim(cls, value: object) -> str:
        return _normalize_text(value, label="attribute claim", maximum=2000)

    @field_validator("risk", mode="before")
    @classmethod
    def normalize_risk(cls, value: object) -> str:
        return _normalize_text(value, label="attribute risk", maximum=1000)

    @field_validator("evidence_refs", "perception_refs", "contradiction_refs")
    @classmethod
    def validate_refs(cls, value: tuple[UUID, ...], info: object) -> tuple[UUID, ...]:
        return _unique_refs(value, label=str(getattr(info, "field_name", "attribute")))


class CandidateContradiction(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    subject_ref: UUID
    description: str = Field(min_length=1, max_length=2000)
    status: Literal["OPEN", "UNDER_REVIEW", "RESOLVED"]
    evidence_refs: tuple[UUID, ...] = Field(max_length=20)

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: object) -> str:
        return _normalize_text(value, label="contradiction description", maximum=2000)

    @field_validator("evidence_refs")
    @classmethod
    def validate_refs(cls, value: tuple[UUID, ...]) -> tuple[UUID, ...]:
        return _unique_refs(value, label="contradiction")


class CandidateDevelopmentGoal(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    area: str = Field(min_length=1, max_length=160)
    objective: str = Field(min_length=1, max_length=2000)
    status: Literal["OPEN", "IN_PROGRESS", "COMPLETE"]
    evidence_refs: tuple[UUID, ...] = Field(max_length=20)

    @field_validator("area", mode="before")
    @classmethod
    def normalize_area(cls, value: object) -> str:
        return _normalize_text(value, label="development area", maximum=160)

    @field_validator("objective", mode="before")
    @classmethod
    def normalize_objective(cls, value: object) -> str:
        return _normalize_text(value, label="development objective", maximum=2000)

    @field_validator("evidence_refs")
    @classmethod
    def validate_refs(cls, value: tuple[UUID, ...]) -> tuple[UUID, ...]:
        return _unique_refs(value, label="development goal")


class CandidateReputationRisk(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1, max_length=2000)
    severity: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    status: Literal["OPEN", "MITIGATING", "RESOLVED", "CLOSED"]
    decision_required: bool
    evidence_refs: tuple[UUID, ...] = Field(max_length=20)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> str:
        return _normalize_text(value, label="reputation risk title", maximum=255)

    @field_validator("description", mode="before")
    @classmethod
    def normalize_description(cls, value: object) -> str:
        return _normalize_text(value, label="reputation risk description", maximum=2000)

    @field_validator("evidence_refs")
    @classmethod
    def validate_refs(cls, value: tuple[UUID, ...]) -> tuple[UUID, ...]:
        return _unique_refs(value, label="reputation risk")


class CandidateSectionApproval(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    section: CandidateSection
    approved_version: int = Field(ge=1)
    principal_id: UUID
    authorization_grant_id: UUID
    approval_receipt_id: str = Field(min_length=1, max_length=255)
    reason: str = Field(min_length=1, max_length=1000)
    approved_at: datetime

    @field_validator("approval_receipt_id", mode="before")
    @classmethod
    def normalize_receipt(cls, value: object) -> str:
        return _normalize_text(value, label="approval receipt", maximum=255)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: object) -> str:
        return _normalize_text(value, label="approval reason", maximum=1000)

    @model_validator(mode="after")
    def validate_timestamp(self) -> Self:
        if self.approved_at.utcoffset() is None:
            raise ValueError("approval timestamp must include a timezone")
        return self


class CandidateWorkspaceCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    display_name: str = Field(min_length=1, max_length=255)

    @field_validator("display_name", mode="before")
    @classmethod
    def normalize_display_name(cls, value: object) -> str:
        return _normalize_text(value, label="display_name", maximum=255)


class CandidateWorkspaceUpdate(BaseModel):
    """Bounded partial replacement of candidate evidence sections."""

    model_config = ConfigDict(extra="forbid")

    display_name: str | None = Field(default=None, max_length=255)
    evidence: tuple[CandidateEvidence, ...] | None = None
    identity: CandidateClaim | None = None
    biography: CandidateClaim | None = None
    purpose: CandidateClaim | None = None
    values: tuple[CandidateClaim, ...] | None = None
    attributes: tuple[CandidateAttribute, ...] | None = None
    contradictions: tuple[CandidateContradiction, ...] | None = None
    development_goals: tuple[CandidateDevelopmentGoal, ...] | None = None
    reputation_risks: tuple[CandidateReputationRisk, ...] | None = None

    @field_validator("display_name", mode="before")
    @classmethod
    def normalize_display_name(cls, value: object) -> str | None:
        return _normalize_optional_text(value, label="display_name", maximum=255)

    @field_validator("evidence", mode="before")
    @classmethod
    def bound_evidence(cls, value: object) -> object:
        return _normalize_model_list(value, label="evidence", maximum=100)

    @field_validator("values", "attributes", mode="before")
    @classmethod
    def bound_primary_records(cls, value: object, info: object) -> object:
        return _normalize_model_list(
            value,
            label=str(getattr(info, "field_name", "records")),
            maximum=30,
        )

    @field_validator(
        "contradictions",
        "development_goals",
        "reputation_risks",
        mode="before",
    )
    @classmethod
    def bound_review_records(cls, value: object, info: object) -> object:
        return _normalize_model_list(
            value,
            label=str(getattr(info, "field_name", "records")),
            maximum=50,
        )

    @model_validator(mode="after")
    def validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("candidate workspace update requires at least one field")
        if "display_name" in self.model_fields_set and self.display_name is None:
            raise ValueError("display_name cannot be null")
        if "evidence" in self.model_fields_set and self.evidence is None:
            raise ValueError("evidence cannot be null")
        return self


class CandidateSectionApprovalRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    section: CandidateSection
    reason: str = Field(min_length=1, max_length=1000)

    @field_validator("reason", mode="before")
    @classmethod
    def normalize_reason(cls, value: object) -> str:
        return _normalize_text(value, label="approval reason", maximum=1000)


class CandidateWorkspaceAssessmentInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    campaign_version: int = Field(ge=1)
    campaign_status: Literal["DRAFT", "ACTIVE"]
    campaign_name: str = Field(min_length=1, max_length=255)
    jurisdiction: str = Field(min_length=1, max_length=255)
    candidate_id: UUID
    display_name: str = Field(min_length=1, max_length=255)
    evidence: tuple[CandidateEvidence, ...] = Field(max_length=100)
    identity: CandidateClaim | None
    biography: CandidateClaim | None
    purpose: CandidateClaim | None
    values: tuple[CandidateClaim, ...] | None = Field(default=None, max_length=30)
    attributes: tuple[CandidateAttribute, ...] | None = Field(default=None, max_length=30)
    contradictions: tuple[CandidateContradiction, ...] | None = Field(default=None, max_length=50)
    development_goals: tuple[CandidateDevelopmentGoal, ...] | None = Field(
        default=None, max_length=50
    )
    reputation_risks: tuple[CandidateReputationRisk, ...] | None = Field(
        default=None, max_length=50
    )
    approvals: tuple[CandidateSectionApproval, ...] = Field(max_length=200)
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime

    @model_validator(mode="after")
    def validate_timestamps(self) -> Self:
        if self.created_at.utcoffset() is None or self.updated_at.utcoffset() is None:
            raise ValueError("candidate workspace timestamps must include a timezone")
        return self


class CandidateWorkspaceCheck(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    key: CandidateCheckKey
    complete: bool
    reason_code: str = Field(min_length=1, max_length=100)


class CandidateWorkspaceProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    campaign_version: int = Field(ge=1)
    campaign_status: Literal["DRAFT", "ACTIVE"]
    campaign_name: str
    jurisdiction: str
    candidate_id: UUID
    display_name: str
    status: CandidateWorkspaceStatus
    public_use_status: Literal["BLOCKED"] = "BLOCKED"
    external_effects: Literal["NONE"] = "NONE"
    evidence: tuple[CandidateEvidence, ...]
    identity: CandidateClaim | None
    biography: CandidateClaim | None
    purpose: CandidateClaim | None
    values: tuple[CandidateClaim, ...] | None
    attributes: tuple[CandidateAttribute, ...] | None
    contradictions: tuple[CandidateContradiction, ...] | None
    development_goals: tuple[CandidateDevelopmentGoal, ...] | None
    reputation_risks: tuple[CandidateReputationRisk, ...] | None
    checks: tuple[CandidateWorkspaceCheck, ...]
    completed_checks: int = Field(ge=0)
    total_checks: int = Field(ge=1)
    approvable_sections: tuple[CandidateSection, ...]
    current_approved_sections: tuple[CandidateSection, ...]
    approvals_required: tuple[CandidateSection, ...]
    open_critical_high_risks: int = Field(ge=0)
    next_action: CandidateNextAction
    limitation_codes: tuple[CandidateLimitation, ...]
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime


class CandidateWorkspaceCreateEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace: CandidateWorkspaceProjection
    audit_event_id: UUID
    outbox_event_id: UUID


class CandidateWorkspaceReadEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace: CandidateWorkspaceProjection
    audit_event_id: UUID


class CandidateWorkspaceUpdateEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace: CandidateWorkspaceProjection
    audit_event_id: UUID
    outbox_event_id: UUID


class CandidateWorkspaceApprovalEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    workspace: CandidateWorkspaceProjection
    approval: CandidateSectionApproval
    audit_event_id: UUID
    outbox_event_id: UUID


def _evidence_index(value: CandidateWorkspaceAssessmentInput) -> dict[UUID, CandidateEvidence]:
    index: dict[UUID, CandidateEvidence] = {}
    for evidence in value.evidence:
        _require(
            evidence.id not in index,
            f"duplicate or colliding candidate record ID: {evidence.id}",
        )
        index[evidence.id] = evidence
    return index


def _resolved_evidence(
    refs: tuple[UUID, ...],
    evidence: dict[UUID, CandidateEvidence],
    *,
    label: str,
) -> tuple[CandidateEvidence, ...]:
    resolved: list[CandidateEvidence] = []
    for ref in refs:
        _require(ref in evidence, f"unknown evidence reference {ref} from {label}")
        resolved.append(evidence[ref])
    return tuple(resolved)


def _validate_claim(
    claim: CandidateClaim,
    evidence: dict[UUID, CandidateEvidence],
    *,
    label: str,
) -> None:
    resolved = _resolved_evidence(claim.evidence_refs, evidence, label=label)
    if claim.status == "VERIFIED":
        _require(bool(resolved), f"verified {label} requires evidence")
        _require(
            all(item.status in ENABLING_EVIDENCE for item in resolved),
            f"verified {label} has non-enabling evidence",
        )
        _require(
            claim.classification in INDEPENDENT_EVIDENCE
            and any(item.classification in INDEPENDENT_EVIDENCE for item in resolved),
            f"verified {label} requires independent evidence",
        )


def _validate_attribute(
    attribute: CandidateAttribute,
    evidence: dict[UUID, CandidateEvidence],
    contradictions: dict[UUID, CandidateContradiction],
) -> None:
    resolved = _resolved_evidence(
        attribute.evidence_refs,
        evidence,
        label=f"attribute {attribute.id}",
    )
    perception = _resolved_evidence(
        attribute.perception_refs,
        evidence,
        label=f"attribute perception {attribute.id}",
    )
    _require(
        all(item.classification == "PERCEPTION" for item in perception),
        f"attribute perception references must use PERCEPTION records: {attribute.id}",
    )
    for contradiction_ref in attribute.contradiction_refs:
        _require(
            contradiction_ref in contradictions,
            f"unknown contradiction reference {contradiction_ref} from attribute {attribute.id}",
        )
        _require(
            contradictions[contradiction_ref].subject_ref == attribute.id,
            f"attribute contradiction reference targets another subject: {contradiction_ref}",
        )
    if attribute.status == "VERIFIED":
        _require(
            any(
                item.status in ENABLING_EVIDENCE and item.classification in INDEPENDENT_EVIDENCE
                for item in resolved
            ),
            f"self-assessment alone cannot verify attribute: {attribute.id}",
        )
    if attribute.citizen_evidence != "UNRESOLVED":
        _require(
            bool(perception),
            f"candidate public evidence must use PERCEPTION records: {attribute.id}",
        )


def _register_ids(value: CandidateWorkspaceAssessmentInput) -> set[UUID]:
    ids: set[UUID] = {value.id, value.candidate_id}
    record_ids: list[UUID] = [evidence.id for evidence in value.evidence]
    for optional in (value.identity, value.biography, value.purpose):
        if optional is not None:
            record_ids.append(optional.id)
    for collection in (
        value.values,
        value.attributes,
        value.contradictions,
        value.development_goals,
        value.reputation_risks,
    ):
        if collection is not None:
            record_ids.extend(record.id for record in collection)
    record_ids.extend(approval.id for approval in value.approvals)
    for record_id in record_ids:
        _require(record_id not in ids, f"duplicate or colliding candidate record ID: {record_id}")
        ids.add(record_id)
    return ids


def _current_approval_sections(
    value: CandidateWorkspaceAssessmentInput,
    approvable: tuple[CandidateSection, ...],
) -> tuple[CandidateSection, ...]:
    seen_version_sections: set[tuple[int, CandidateSection]] = set()
    current: set[CandidateSection] = set()
    approvable_set = set(approvable)
    for approval in value.approvals:
        key = (approval.approved_version, approval.section)
        _require(key not in seen_version_sections, "duplicate candidate section approval")
        seen_version_sections.add(key)
        _require(
            approval.approved_version <= value.version,
            "candidate section approval cannot target a future version",
        )
        if approval.approved_version == value.version and approval.section in approvable_set:
            current.add(approval.section)
    return tuple(section for section in SECTION_ORDER if section in current)


def assess_candidate_workspace(
    value: CandidateWorkspaceAssessmentInput,
) -> CandidateWorkspaceProjection:
    """Derive internal readiness while keeping public use and external effects blocked."""
    evidence = _evidence_index(value)
    all_ids = _register_ids(value)
    contradiction_index = {
        contradiction.id: contradiction for contradiction in value.contradictions or ()
    }

    for label, claim in (
        ("identity", value.identity),
        ("biography", value.biography),
        ("purpose", value.purpose),
    ):
        if claim is not None:
            _validate_claim(claim, evidence, label=label)
    for claim in value.values or ():
        _validate_claim(claim, evidence, label=f"value {claim.id}")
    for attribute in value.attributes or ():
        _validate_attribute(attribute, evidence, contradiction_index)
    for contradiction in value.contradictions or ():
        _require(
            contradiction.subject_ref in all_ids,
            f"unknown contradiction subject: {contradiction.subject_ref}",
        )
        _resolved_evidence(
            contradiction.evidence_refs,
            evidence,
            label=f"contradiction {contradiction.id}",
        )
    for goal in value.development_goals or ():
        _resolved_evidence(goal.evidence_refs, evidence, label=f"development goal {goal.id}")
    for risk in value.reputation_risks or ():
        _resolved_evidence(risk.evidence_refs, evidence, label=f"reputation risk {risk.id}")

    identity_complete = value.identity is not None and value.identity.status == "VERIFIED"
    biography_complete = value.biography is not None and value.biography.status == "VERIFIED"
    purpose_complete = value.purpose is not None and value.purpose.status == "VERIFIED"
    values_complete = bool(value.values) and all(
        item.status == "VERIFIED" for item in value.values or ()
    )
    attributes_complete = bool(value.attributes) and all(
        item.status == "VERIFIED" for item in value.attributes or ()
    )
    contradictions_complete = value.contradictions is not None and all(
        item.status == "RESOLVED" for item in value.contradictions
    )
    development_goals_complete = bool(value.development_goals)
    open_critical_high = sum(
        1
        for risk in value.reputation_risks or ()
        if risk.severity in {"CRITICAL", "HIGH"} and risk.status not in {"RESOLVED", "CLOSED"}
    )
    reputation_complete = value.reputation_risks is not None and open_critical_high == 0

    section_states: dict[CandidateSection, tuple[bool, str]] = {
        "identity": (
            identity_complete,
            "IDENTITY_VERIFIED" if identity_complete else "IDENTITY_NOT_VERIFIED",
        ),
        "biography": (
            biography_complete,
            "BIOGRAPHY_VERIFIED" if biography_complete else "BIOGRAPHY_NOT_VERIFIED",
        ),
        "purpose": (
            purpose_complete,
            "PURPOSE_VERIFIED" if purpose_complete else "PURPOSE_NOT_VERIFIED",
        ),
        "values": (
            values_complete,
            "VALUES_VERIFIED" if values_complete else "VALUES_NOT_VERIFIED",
        ),
        "attributes": (
            attributes_complete,
            "ATTRIBUTES_VERIFIED" if attributes_complete else "ATTRIBUTES_NOT_VERIFIED",
        ),
        "contradictions": (
            contradictions_complete,
            "CONTRADICTIONS_REVIEWED" if contradictions_complete else "CONTRADICTIONS_UNRESOLVED",
        ),
        "development_goals": (
            development_goals_complete,
            "DEVELOPMENT_GOALS_DEFINED"
            if development_goals_complete
            else "DEVELOPMENT_GOALS_MISSING",
        ),
        "reputation": (
            reputation_complete,
            "REPUTATION_RISKS_REVIEWED" if reputation_complete else "REPUTATION_RISKS_UNRESOLVED",
        ),
    }
    approvable = tuple(section for section in SECTION_ORDER if section_states[section][0])
    current_approved = _current_approval_sections(value, approvable)
    approvals_required = tuple(section for section in approvable if section not in current_approved)
    all_evidence_complete = len(approvable) == len(SECTION_ORDER)
    approvals_complete = all_evidence_complete and not approvals_required

    checks = tuple(
        CandidateWorkspaceCheck(
            key=section,
            complete=section_states[section][0],
            reason_code=section_states[section][1],
        )
        for section in SECTION_ORDER
    ) + (
        CandidateWorkspaceCheck(
            key="approvals",
            complete=approvals_complete,
            reason_code=(
                "CURRENT_SECTION_APPROVALS_COMPLETE"
                if approvals_complete
                else "CURRENT_SECTION_APPROVALS_REQUIRED"
            ),
        ),
    )

    if value.identity is None or value.biography is None or value.purpose is None:
        status: CandidateWorkspaceStatus = "SETUP_REQUIRED"
    elif not all_evidence_complete:
        status = "UNDER_REVIEW"
    elif not approvals_complete:
        status = "AWAITING_APPROVAL"
    else:
        status = "INTERNALLY_APPROVED"

    next_action_by_section: dict[CandidateSection, CandidateNextAction] = {
        "identity": "DEFINE_IDENTITY",
        "biography": "DOCUMENT_BIOGRAPHY",
        "purpose": "DEFINE_PURPOSE",
        "values": "VERIFY_VALUES",
        "attributes": "VERIFY_ATTRIBUTES",
        "contradictions": "REVIEW_CONTRADICTIONS",
        "development_goals": "DEFINE_DEVELOPMENT_GOALS",
        "reputation": "REVIEW_REPUTATION_RISKS",
    }
    first_incomplete = next(
        (section for section in SECTION_ORDER if not section_states[section][0]),
        None,
    )
    if first_incomplete is not None:
        next_action = next_action_by_section[first_incomplete]
    elif approvals_required:
        next_action = "OBTAIN_SECTION_APPROVALS"
    else:
        next_action = "CONTINUE_HUMAN_GOVERNANCE"

    return CandidateWorkspaceProjection(
        id=value.id,
        tenant_id=value.tenant_id,
        campaign_id=value.campaign_id,
        campaign_version=value.campaign_version,
        campaign_status=value.campaign_status,
        campaign_name=value.campaign_name,
        jurisdiction=value.jurisdiction,
        candidate_id=value.candidate_id,
        display_name=value.display_name,
        status=status,
        evidence=value.evidence,
        identity=value.identity,
        biography=value.biography,
        purpose=value.purpose,
        values=value.values,
        attributes=value.attributes,
        contradictions=value.contradictions,
        development_goals=value.development_goals,
        reputation_risks=value.reputation_risks,
        checks=checks,
        completed_checks=sum(check.complete for check in checks),
        total_checks=len(checks),
        approvable_sections=approvable,
        current_approved_sections=current_approved,
        approvals_required=approvals_required,
        open_critical_high_risks=open_critical_high,
        next_action=next_action,
        limitation_codes=LIMITATION_CODES,
        version=value.version,
        created_at=value.created_at,
        updated_at=value.updated_at,
    )
