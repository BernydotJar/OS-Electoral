"""Evidence-first campaign strategy and human decision contracts."""

from __future__ import annotations

from datetime import date, datetime
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

StrategyEvidenceClassification = Literal["VERIFIED", "INFERRED", "UNKNOWN"]
StrategyEvidenceStatus = Literal["ACCEPTED", "NEEDS_REVIEW", "REJECTED"]
StrategyAssumptionStatus = Literal["ACTIVE", "INVALIDATED"]
StrategyHypothesisStatus = Literal["DRAFT", "IN_REVIEW", "REJECTED"]
StrategyContradictionStatus = Literal["OPEN", "RESOLVED"]
StrategyFindingSeverity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
StrategyFindingStatus = Literal["OPEN", "RESOLVED"]
StrategyWorkspaceStatus = Literal[
    "EVIDENCE_REQUIRED",
    "CONTRADICTIONS_OPEN",
    "RED_TEAM_BLOCKED",
    "OPTIONS_INCOMPLETE",
    "OBJECTIVES_INCOMPLETE",
    "READY_FOR_HUMAN_DECISION",
    "DECIDED_INTERNAL",
]
StrategyNextAction = Literal[
    "ADD_VERIFIED_EVIDENCE",
    "RESOLVE_CONTRADICTIONS",
    "ADDRESS_RED_TEAM_FINDINGS",
    "COMPLETE_COMPARABLE_OPTIONS",
    "DEFINE_MEASURABLE_OBJECTIVES",
    "MAKE_HUMAN_DECISION",
    "REVALIDATE_DECISION",
]
StrategyLimitation = Literal[
    "NOT_PUBLIC_POSITIONING",
    "NOT_A_HUMAN_APPROVAL",
    "NO_VOTER_PROFILING_OR_INDIVIDUAL_TARGETING",
    "NO_CITIZEN_CONTACT_OR_EXTERNAL_EFFECTS",
]

LIMITATION_CODES: tuple[StrategyLimitation, ...] = (
    "NOT_PUBLIC_POSITIONING",
    "NOT_A_HUMAN_APPROVAL",
    "NO_VOTER_PROFILING_OR_INDIVIDUAL_TARGETING",
    "NO_CITIZEN_CONTACT_OR_EXTERNAL_EFFECTS",
)

PROHIBITED_FIELD_FRAGMENTS = (
    "voter",
    "persuad",
    "psychographic",
    "political_preference",
    "individual_target",
    "contact_list",
    "microtarget",
)

ShortText = Annotated[str, Field(min_length=1, max_length=180)]
LongText = Annotated[str, Field(min_length=1, max_length=2000)]
ReferenceText = Annotated[str, Field(min_length=1, max_length=500)]
TextList = Annotated[tuple[ShortText, ...], Field(max_length=40)]
UuidList = Annotated[tuple[UUID, ...], Field(max_length=80)]


class StrategyContractError(ValueError):
    """Raised when strategy evidence contradicts deterministic governance rules."""


def _normalized_text(value: str) -> str:
    return " ".join(value.split())


def _normalize_text_list(value: object) -> object:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        raise ValueError("expected an array of strings")
    normalized = tuple(_normalized_text(str(item)) for item in value)  # type: ignore[arg-type]
    if any(not item for item in normalized):
        raise ValueError("array values must be non-empty")
    if len(set(normalized)) != len(normalized):
        raise ValueError("array values must be unique")
    return normalized


def _normalize_uuid_list(value: object) -> object:
    if value is None:
        return ()
    if isinstance(value, (str, bytes, bytearray)):
        raise ValueError("expected an array of UUIDs")
    parsed = tuple(UUID(str(item)) for item in value)  # type: ignore[arg-type]
    if len(set(parsed)) != len(parsed):
        raise ValueError("UUID references must be unique")
    return parsed


def _require(condition: bool, detail: str) -> None:
    if not condition:
        raise StrategyContractError(detail)


def _refs_exist(refs: tuple[UUID, ...], known: set[UUID], label: str) -> None:
    for ref in refs:
        _require(ref in known, f"unknown {label} reference {ref}")


class StrategyBaseModel(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    @field_validator("*", mode="before")
    @classmethod
    def reject_prohibited_field_values(cls, value: object) -> object:
        return value


class StrategyEvidence(StrategyBaseModel):
    id: UUID
    classification: StrategyEvidenceClassification
    statement: LongText
    source_reference: ReferenceText | None = None
    authority: ShortText | None = None
    jurisdiction: ShortText | None = None
    status: StrategyEvidenceStatus
    collected_at: datetime

    @field_validator("statement", "source_reference", "authority", "jurisdiction", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            return _normalized_text(value)
        return value

    @model_validator(mode="after")
    def validate_provenance(self) -> Self:
        if self.classification == "VERIFIED":
            _require(self.status == "ACCEPTED", "verified evidence must be accepted")
            _require(self.source_reference is not None, "verified evidence requires a source")
            _require(self.authority is not None, "verified evidence requires authority")
            _require(self.jurisdiction is not None, "verified evidence requires jurisdiction")
        elif self.classification == "UNKNOWN":
            _require(self.status == "NEEDS_REVIEW", "unknown evidence must need review")
            _require(self.source_reference is None, "unknown evidence cannot claim a source")
            _require(self.authority is None, "unknown evidence cannot claim authority")
            _require(self.jurisdiction is None, "unknown evidence cannot claim jurisdiction")
        else:
            _require(self.status != "REJECTED", "inferred evidence cannot be rejected")
            _require(self.source_reference is not None, "inferred evidence requires provenance")
        return self


class StrategyAssumption(StrategyBaseModel):
    id: UUID
    statement: LongText
    evidence_refs: UuidList = ()
    invalidation_signals: TextList
    status: StrategyAssumptionStatus = "ACTIVE"

    _normalize_statement = field_validator("statement", mode="before")(_normalized_text)
    _normalize_evidence = field_validator("evidence_refs", mode="before")(_normalize_uuid_list)
    _normalize_signals = field_validator("invalidation_signals", mode="before")(
        _normalize_text_list
    )


class StrategyHypothesis(StrategyBaseModel):
    id: UUID
    title: ShortText
    statement: LongText
    evidence_refs: UuidList
    assumption_refs: UuidList = ()
    invalidation_signals: TextList
    status: StrategyHypothesisStatus = "DRAFT"

    @field_validator("title", "statement", mode="before")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return _normalized_text(value)

    _normalize_evidence = field_validator("evidence_refs", mode="before")(_normalize_uuid_list)
    _normalize_assumptions = field_validator("assumption_refs", mode="before")(_normalize_uuid_list)
    _normalize_signals = field_validator("invalidation_signals", mode="before")(
        _normalize_text_list
    )


class StrategyOption(StrategyBaseModel):
    id: UUID
    title: ShortText
    summary: LongText
    hypothesis_refs: UuidList
    evidence_refs: UuidList
    benefits: TextList
    risks: TextList
    tradeoffs: TextList

    @field_validator("title", "summary", mode="before")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return _normalized_text(value)

    _normalize_hypotheses = field_validator("hypothesis_refs", mode="before")(_normalize_uuid_list)
    _normalize_evidence = field_validator("evidence_refs", mode="before")(_normalize_uuid_list)
    _normalize_benefits = field_validator("benefits", mode="before")(_normalize_text_list)
    _normalize_risks = field_validator("risks", mode="before")(_normalize_text_list)
    _normalize_tradeoffs = field_validator("tradeoffs", mode="before")(_normalize_text_list)


class StrategyObjective(StrategyBaseModel):
    id: UUID
    outcome: LongText
    metric: ShortText
    baseline: ShortText
    target: ShortText
    deadline: date
    owner_role_id: UUID
    evidence_refs: UuidList

    @field_validator("outcome", "metric", "baseline", "target", mode="before")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return _normalized_text(value)

    _normalize_evidence = field_validator("evidence_refs", mode="before")(_normalize_uuid_list)


class StrategyContradiction(StrategyBaseModel):
    id: UUID
    left_ref: UUID
    right_ref: UUID
    description: LongText
    evidence_refs: UuidList
    status: StrategyContradictionStatus
    resolution: LongText | None = None

    @field_validator("description", "resolution", mode="before")
    @classmethod
    def normalize_text(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            return _normalized_text(value)
        return value

    _normalize_evidence = field_validator("evidence_refs", mode="before")(_normalize_uuid_list)

    @model_validator(mode="after")
    def validate_resolution(self) -> Self:
        _require(self.left_ref != self.right_ref, "contradiction sides must differ")
        if self.status == "OPEN":
            _require(self.resolution is None, "open contradiction cannot have resolution")
        else:
            _require(self.resolution is not None, "resolved contradiction requires resolution")
        return self


class StrategyRedTeamFinding(StrategyBaseModel):
    id: UUID
    severity: StrategyFindingSeverity
    description: LongText
    option_refs: UuidList
    mitigation: LongText
    status: StrategyFindingStatus

    @field_validator("description", "mitigation", mode="before")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return _normalized_text(value)

    _normalize_options = field_validator("option_refs", mode="before")(_normalize_uuid_list)


class StrategyDecision(StrategyBaseModel):
    id: UUID
    workspace_version: int = Field(ge=1)
    selected_option_id: UUID
    reason: LongText
    human_role_id: UUID
    approval_receipt_id: ShortText
    decided_at: datetime

    @field_validator("reason", "approval_receipt_id", mode="before")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return _normalized_text(value)


class StrategyWorkspaceCreate(StrategyBaseModel):
    title: ShortText = "Campaign Strategy and Decision Room"

    _normalize_title = field_validator("title", mode="before")(_normalized_text)


class StrategyWorkspaceUpdate(StrategyBaseModel):
    title: ShortText | None = None
    evidence: tuple[StrategyEvidence, ...] | None = Field(default=None, max_length=100)
    assumptions: tuple[StrategyAssumption, ...] | None = Field(default=None, max_length=60)
    hypotheses: tuple[StrategyHypothesis, ...] | None = Field(default=None, max_length=60)
    options: tuple[StrategyOption, ...] | None = Field(default=None, max_length=20)
    objectives: tuple[StrategyObjective, ...] | None = Field(default=None, max_length=40)
    contradictions: tuple[StrategyContradiction, ...] | None = Field(default=None, max_length=60)
    red_team_findings: tuple[StrategyRedTeamFinding, ...] | None = Field(
        default=None, max_length=60
    )

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            return _normalized_text(value)
        return value

    @model_validator(mode="after")
    def require_change(self) -> Self:
        _require(bool(self.model_fields_set), "strategy update must include a change")
        return self


class StrategyDecisionRequest(StrategyBaseModel):
    selected_option_id: UUID
    reason: LongText
    human_role_id: UUID

    _normalize_reason = field_validator("reason", mode="before")(_normalized_text)


class StrategyWorkspaceAssessmentInput(StrategyBaseModel):
    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    campaign_version: int = Field(ge=1)
    campaign_status: Literal["DRAFT", "ACTIVE"]
    campaign_name: ShortText
    candidate_workspace_version: int = Field(ge=1)
    team_workspace_version: int = Field(ge=1)
    known_role_ids: tuple[UUID, ...] = Field(max_length=100)
    title: ShortText
    evidence: tuple[StrategyEvidence, ...] | None = None
    assumptions: tuple[StrategyAssumption, ...] | None = None
    hypotheses: tuple[StrategyHypothesis, ...] | None = None
    options: tuple[StrategyOption, ...] | None = None
    objectives: tuple[StrategyObjective, ...] | None = None
    contradictions: tuple[StrategyContradiction, ...] | None = None
    red_team_findings: tuple[StrategyRedTeamFinding, ...] | None = None
    decision: StrategyDecision | None = None
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime

    @field_validator("campaign_name", "title", mode="before")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        return _normalized_text(value)

    _normalize_roles = field_validator("known_role_ids", mode="before")(_normalize_uuid_list)


class StrategyWorkspaceProjection(StrategyBaseModel):
    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    campaign_version: int
    campaign_status: Literal["DRAFT", "ACTIVE"]
    campaign_name: str
    candidate_workspace_version: int
    team_workspace_version: int
    title: str
    evidence: tuple[StrategyEvidence, ...] | None
    assumptions: tuple[StrategyAssumption, ...] | None
    hypotheses: tuple[StrategyHypothesis, ...] | None
    options: tuple[StrategyOption, ...] | None
    objectives: tuple[StrategyObjective, ...] | None
    contradictions: tuple[StrategyContradiction, ...] | None
    red_team_findings: tuple[StrategyRedTeamFinding, ...] | None
    decision: StrategyDecision | None
    status: StrategyWorkspaceStatus
    verified_evidence_count: int
    inferred_evidence_count: int
    unknown_evidence_count: int
    open_contradiction_count: int
    open_high_risk_count: int
    complete_option_count: int
    measurable_objective_count: int
    next_action: StrategyNextAction
    human_decision_required: bool
    authority_effect: Literal["NONE"] = "NONE"
    external_effects: Literal["NONE"] = "NONE"
    limitation_codes: tuple[StrategyLimitation, ...] = LIMITATION_CODES
    version: int
    created_at: datetime
    updated_at: datetime


class StrategyWorkspaceCreateEvidence(StrategyBaseModel):
    workspace: StrategyWorkspaceProjection
    audit_event_id: UUID
    outbox_event_id: UUID


class StrategyWorkspaceReadEvidence(StrategyBaseModel):
    workspace: StrategyWorkspaceProjection
    audit_event_id: UUID


class StrategyWorkspaceUpdateEvidence(StrategyBaseModel):
    workspace: StrategyWorkspaceProjection
    audit_event_id: UUID
    outbox_event_id: UUID


class StrategyDecisionEvidence(StrategyBaseModel):
    workspace: StrategyWorkspaceProjection
    decision: StrategyDecision
    audit_event_id: UUID
    outbox_event_id: UUID


def assess_strategy_workspace(
    value: StrategyWorkspaceAssessmentInput,
) -> StrategyWorkspaceProjection:
    """Validate evidence relationships and derive decision readiness without authority."""

    evidence = value.evidence or ()
    assumptions = value.assumptions or ()
    hypotheses = value.hypotheses or ()
    options = value.options or ()
    objectives = value.objectives or ()
    contradictions = value.contradictions or ()
    findings = value.red_team_findings or ()

    all_records = (
        list(evidence)
        + list(assumptions)
        + list(hypotheses)
        + list(options)
        + list(objectives)
        + list(contradictions)
        + list(findings)
    )
    ids = [value.id, *(item.id for item in all_records)]
    _require(len(ids) == len(set(ids)), "strategy records must use unique IDs")

    evidence_by_id = {item.id: item for item in evidence}
    assumption_ids = {item.id for item in assumptions}
    hypothesis_ids = {item.id for item in hypotheses}
    option_ids = {item.id for item in options}
    objective_ids = {item.id for item in objectives}
    referenceable_ids = (
        set(evidence_by_id) | assumption_ids | hypothesis_ids | option_ids | objective_ids
    )
    role_ids = set(value.known_role_ids)

    for assumption in assumptions:
        _refs_exist(assumption.evidence_refs, set(evidence_by_id), "evidence")
        _require(bool(assumption.invalidation_signals), "assumption requires invalidation signals")
        _require(
            all(evidence_by_id[ref].status != "REJECTED" for ref in assumption.evidence_refs),
            "assumption cannot use rejected evidence",
        )

    for hypothesis in hypotheses:
        _require(bool(hypothesis.evidence_refs), "hypothesis requires evidence")
        _require(bool(hypothesis.invalidation_signals), "hypothesis requires invalidation signals")
        _refs_exist(hypothesis.evidence_refs, set(evidence_by_id), "evidence")
        _refs_exist(hypothesis.assumption_refs, assumption_ids, "assumption")
        _require(
            all(evidence_by_id[ref].status != "REJECTED" for ref in hypothesis.evidence_refs),
            "hypothesis cannot use rejected evidence",
        )
        if hypothesis.status == "IN_REVIEW":
            _require(
                any(
                    evidence_by_id[ref].classification == "VERIFIED"
                    and evidence_by_id[ref].status == "ACCEPTED"
                    for ref in hypothesis.evidence_refs
                ),
                "hypothesis in review requires accepted verified evidence",
            )

    for option in options:
        _require(bool(option.hypothesis_refs), "strategy option requires hypotheses")
        _require(bool(option.evidence_refs), "strategy option requires evidence")
        _require(bool(option.benefits), "strategy option requires benefits")
        _require(bool(option.risks), "strategy option requires risks")
        _require(bool(option.tradeoffs), "strategy option requires tradeoffs")
        _refs_exist(option.hypothesis_refs, hypothesis_ids, "hypothesis")
        _refs_exist(option.evidence_refs, set(evidence_by_id), "evidence")
        _require(
            all(evidence_by_id[ref].status != "REJECTED" for ref in option.evidence_refs),
            "strategy option cannot use rejected evidence",
        )

    for objective in objectives:
        _require(objective.owner_role_id in role_ids, "objective owner must be a known team role")
        _require(bool(objective.evidence_refs), "objective requires evidence")
        _refs_exist(objective.evidence_refs, set(evidence_by_id), "evidence")

    for contradiction in contradictions:
        _require(
            contradiction.left_ref in referenceable_ids,
            f"unknown contradiction reference {contradiction.left_ref}",
        )
        _require(
            contradiction.right_ref in referenceable_ids,
            f"unknown contradiction reference {contradiction.right_ref}",
        )
        _refs_exist(contradiction.evidence_refs, set(evidence_by_id), "evidence")

    for finding in findings:
        _require(bool(finding.option_refs), "red-team finding requires affected options")
        _refs_exist(finding.option_refs, option_ids, "strategy option")

    verified_count = sum(
        item.classification == "VERIFIED" and item.status == "ACCEPTED" for item in evidence
    )
    inferred_count = sum(item.classification == "INFERRED" for item in evidence)
    unknown_count = sum(item.classification == "UNKNOWN" for item in evidence)
    open_contradictions = sum(item.status == "OPEN" for item in contradictions)
    open_high = sum(
        item.status == "OPEN" and item.severity in {"CRITICAL", "HIGH"} for item in findings
    )
    complete_options = sum(
        bool(item.hypothesis_refs)
        and bool(item.evidence_refs)
        and bool(item.benefits)
        and bool(item.risks)
        and bool(item.tradeoffs)
        for item in options
    )
    measurable_objectives = sum(
        bool(item.metric) and bool(item.baseline) and bool(item.target) for item in objectives
    )

    decision_ready = (
        verified_count > 0
        and unknown_count == 0
        and open_contradictions == 0
        and open_high == 0
        and complete_options >= 2
        and measurable_objectives > 0
    )

    if value.decision is not None:
        _require(decision_ready, "strategy decision requires current decision readiness")
        _require(
            value.decision.workspace_version == value.version,
            "strategy decision must bind the current workspace version",
        )
        _require(
            value.decision.selected_option_id in option_ids,
            "strategy decision selected option is unknown",
        )
        _require(
            value.decision.human_role_id in role_ids,
            "strategy decision role must be a known team role",
        )
        status: StrategyWorkspaceStatus = "DECIDED_INTERNAL"
        next_action: StrategyNextAction = "REVALIDATE_DECISION"
    elif verified_count == 0 or unknown_count > 0:
        status = "EVIDENCE_REQUIRED"
        next_action = "ADD_VERIFIED_EVIDENCE"
    elif open_contradictions > 0:
        status = "CONTRADICTIONS_OPEN"
        next_action = "RESOLVE_CONTRADICTIONS"
    elif open_high > 0:
        status = "RED_TEAM_BLOCKED"
        next_action = "ADDRESS_RED_TEAM_FINDINGS"
    elif complete_options < 2:
        status = "OPTIONS_INCOMPLETE"
        next_action = "COMPLETE_COMPARABLE_OPTIONS"
    elif measurable_objectives == 0:
        status = "OBJECTIVES_INCOMPLETE"
        next_action = "DEFINE_MEASURABLE_OBJECTIVES"
    else:
        status = "READY_FOR_HUMAN_DECISION"
        next_action = "MAKE_HUMAN_DECISION"

    return StrategyWorkspaceProjection(
        id=value.id,
        tenant_id=value.tenant_id,
        campaign_id=value.campaign_id,
        campaign_version=value.campaign_version,
        campaign_status=value.campaign_status,
        campaign_name=value.campaign_name,
        candidate_workspace_version=value.candidate_workspace_version,
        team_workspace_version=value.team_workspace_version,
        title=value.title,
        evidence=value.evidence,
        assumptions=value.assumptions,
        hypotheses=value.hypotheses,
        options=value.options,
        objectives=value.objectives,
        contradictions=value.contradictions,
        red_team_findings=value.red_team_findings,
        decision=value.decision,
        status=status,
        verified_evidence_count=verified_count,
        inferred_evidence_count=inferred_count,
        unknown_evidence_count=unknown_count,
        open_contradiction_count=open_contradictions,
        open_high_risk_count=open_high,
        complete_option_count=complete_options,
        measurable_objective_count=measurable_objectives,
        next_action=next_action,
        human_decision_required=value.decision is None,
        version=value.version,
        created_at=value.created_at,
        updated_at=value.updated_at,
    )
