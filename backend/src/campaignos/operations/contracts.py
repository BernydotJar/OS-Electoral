"""Typed contracts and deterministic campaign operations assessment."""

from __future__ import annotations

import re
from collections import deque
from datetime import date, datetime
from typing import Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

PhaseStatus = Literal["PLANNED", "ACTIVE", "COMPLETE"]
WorkstreamStatus = Literal["PLANNED", "ACTIVE", "PAUSED", "COMPLETE"]
MilestoneStatus = Literal["PLANNED", "IN_PROGRESS", "COMPLETE"]
TaskExecutionStatus = Literal["PLANNED", "IN_PROGRESS", "COMPLETE"]
BlockerSeverity = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
BlockerStatus = Literal["OPEN", "RESOLVED"]
DecisionStatus = Literal["REQUIRED", "DECIDED", "DEFERRED"]
FollowUpStatus = Literal["OPEN", "COMPLETE"]
RoadmapStatus = Literal["SETUP_REQUIRED", "IN_PROGRESS", "READY_FOR_DAILY_OPERATION", "COMPLETE"]
RoadmapNextAction = Literal[
    "DEFINE_ROADMAP",
    "RESOLVE_BLOCKERS",
    "MAKE_HUMAN_DECISIONS",
    "START_READY_TASKS",
    "CONTINUE_ACTIVE_WORK",
    "REVIEW_COMPLETION",
]
OperationsLimitation = Literal[
    "HUMAN_DECISIONS_REQUIRED",
    "NO_AUTONOMOUS_TASK_EXECUTION",
    "NO_CITIZEN_CONTACT",
    "NO_EXTERNAL_EFFECTS",
]

LIMITATION_CODES: tuple[OperationsLimitation, ...] = (
    "HUMAN_DECISIONS_REQUIRED",
    "NO_AUTONOMOUS_TASK_EXECUTION",
    "NO_CITIZEN_CONTACT",
    "NO_EXTERNAL_EFFECTS",
)
_PERSONAL_PATH = re.compile(r"(?:/Users/[^/]+|/home/[^/]+|[A-Za-z]:\\Users\\[^\\]+)")


class CampaignRoadmapContractError(ValueError):
    """A structurally valid operations document violates a graph invariant."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise CampaignRoadmapContractError(message)


def _normalize_text(value: object, *, label: str, maximum: int) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{label} must be text")
    normalized = " ".join(value.split())
    if not normalized:
        raise ValueError(f"{label} must not be blank")
    if len(normalized) > maximum:
        raise ValueError(f"{label} must not exceed {maximum} characters")
    if _PERSONAL_PATH.search(normalized) or "../" in normalized or "..\\" in normalized:
        raise ValueError(f"{label} must not contain a personal or traversing path")
    return normalized


def _normalize_text_list(
    value: object,
    *,
    label: str,
    maximum_items: int,
    allow_empty: bool = True,
) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} must be an array")
    if not allow_empty and not value:
        raise ValueError(f"{label} must contain at least one item")
    if len(value) > maximum_items:
        raise ValueError(f"{label} must contain at most {maximum_items} items")
    normalized = tuple(
        _normalize_text(item, label=f"{label}[{index}]", maximum=1000)
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


class CampaignPhase(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    name: str = Field(min_length=1, max_length=255)
    sequence: int = Field(ge=1, le=1000)
    start_date: date
    end_date: date
    status: PhaseStatus

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> str:
        return _normalize_text(value, label="phase name", maximum=255)

    @model_validator(mode="after")
    def validate_window(self) -> Self:
        if self.end_date < self.start_date:
            raise ValueError("phase end date must not precede start date")
        return self


class CampaignWorkstream(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    name: str = Field(min_length=1, max_length=255)
    purpose: str = Field(min_length=1, max_length=2000)
    accountable_role_id: UUID
    status: WorkstreamStatus

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> str:
        return _normalize_text(value, label="workstream name", maximum=255)

    @field_validator("purpose", mode="before")
    @classmethod
    def normalize_purpose(cls, value: object) -> str:
        return _normalize_text(value, label="workstream purpose", maximum=2000)


class CampaignMilestone(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    phase_id: UUID
    name: str = Field(min_length=1, max_length=255)
    completion_criteria: str = Field(min_length=1, max_length=2000)
    owner_role_id: UUID
    due_date: date
    status: MilestoneStatus

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value: object) -> str:
        return _normalize_text(value, label="milestone name", maximum=255)

    @field_validator("completion_criteria", mode="before")
    @classmethod
    def normalize_criteria(cls, value: object) -> str:
        return _normalize_text(value, label="milestone completion criteria", maximum=2000)


class CampaignTask(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    phase_id: UUID
    workstream_id: UUID
    milestone_id: UUID | None
    title: str = Field(min_length=1, max_length=500)
    owner_role_id: UUID
    execution_status: TaskExecutionStatus
    dependency_ids: tuple[UUID, ...] = Field(max_length=100)
    due_date: date
    evidence_refs: tuple[UUID, ...] = Field(max_length=100)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> str:
        return _normalize_text(value, label="task title", maximum=500)

    @field_validator("dependency_ids", "evidence_refs", mode="after")
    @classmethod
    def unique_refs(cls, value: tuple[UUID, ...], info: object) -> tuple[UUID, ...]:
        if len(set(value)) != len(value):
            raise ValueError(f"{getattr(info, 'field_name', 'references')} contains duplicates")
        return value


class CampaignBlocker(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    task_id: UUID | None
    severity: BlockerSeverity
    status: BlockerStatus
    owner_role_id: UUID
    description: str = Field(min_length=1, max_length=2000)
    resolution_condition: str = Field(min_length=1, max_length=2000)

    @field_validator("description", "resolution_condition", mode="before")
    @classmethod
    def normalize_text(cls, value: object, info: object) -> str:
        return _normalize_text(
            value,
            label=str(getattr(info, "field_name", "blocker")),
            maximum=2000,
        )


class CampaignDecision(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    title: str = Field(min_length=1, max_length=500)
    human_role_id: UUID
    options: tuple[str, ...] = Field(min_length=2, max_length=10)
    due_date: date
    status: DecisionStatus
    decision: str | None = Field(default=None, max_length=1000)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> str:
        return _normalize_text(value, label="decision title", maximum=500)

    @field_validator("options", mode="before")
    @classmethod
    def normalize_options(cls, value: object) -> tuple[str, ...]:
        return _normalize_text_list(
            value,
            label="decision options",
            maximum_items=10,
            allow_empty=False,
        )

    @field_validator("decision", mode="before")
    @classmethod
    def normalize_decision(cls, value: object) -> str | None:
        if value is None:
            return None
        return _normalize_text(value, label="selected decision", maximum=1000)


class CampaignFollowUpItem(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    title: str = Field(min_length=1, max_length=500)
    owner_role_id: UUID
    due_date: date
    status: FollowUpStatus

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> str:
        return _normalize_text(value, label="follow-up title", maximum=500)


class CampaignLearningNote(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    title: str = Field(min_length=1, max_length=500)
    note: str = Field(min_length=1, max_length=4000)
    evidence_refs: tuple[UUID, ...] = Field(max_length=100)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> str:
        return _normalize_text(value, label="learning title", maximum=500)

    @field_validator("note", mode="before")
    @classmethod
    def normalize_note(cls, value: object) -> str:
        return _normalize_text(value, label="learning note", maximum=4000)

    @field_validator("evidence_refs", mode="after")
    @classmethod
    def unique_refs(cls, value: tuple[UUID, ...]) -> tuple[UUID, ...]:
        if len(set(value)) != len(value):
            raise ValueError("learning evidence references contain duplicates")
        return value


class CampaignRoadmapCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=255)

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> str:
        return _normalize_text(value, label="roadmap title", maximum=255)


class CampaignRoadmapUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=255)
    phases: tuple[CampaignPhase, ...] | None = None
    workstreams: tuple[CampaignWorkstream, ...] | None = None
    milestones: tuple[CampaignMilestone, ...] | None = None
    tasks: tuple[CampaignTask, ...] | None = None
    blockers: tuple[CampaignBlocker, ...] | None = None
    decisions: tuple[CampaignDecision, ...] | None = None
    follow_up_items: tuple[CampaignFollowUpItem, ...] | None = None
    learning_notes: tuple[CampaignLearningNote, ...] | None = None

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> str | None:
        if value is None:
            return None
        return _normalize_text(value, label="roadmap title", maximum=255)

    @field_validator(
        "phases",
        "workstreams",
        "milestones",
        "tasks",
        "blockers",
        "decisions",
        "follow_up_items",
        "learning_notes",
        mode="before",
    )
    @classmethod
    def bound_records(cls, value: object, info: object) -> object:
        return _bound_models(
            value,
            label=str(getattr(info, "field_name", "records")),
            maximum=500,
        )

    @model_validator(mode="after")
    def validate_patch(self) -> Self:
        if not self.model_fields_set:
            raise ValueError("campaign roadmap update requires at least one field")
        if "title" in self.model_fields_set and self.title is None:
            raise ValueError("title cannot be null")
        return self


class WarRoomSnapshotCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshot_date: date
    priorities: tuple[str, ...] = Field(min_length=1, max_length=10)
    follow_up_notes: tuple[str, ...] = Field(max_length=20)

    @field_validator("priorities", mode="before")
    @classmethod
    def normalize_priorities(cls, value: object) -> tuple[str, ...]:
        return _normalize_text_list(
            value,
            label="war room priorities",
            maximum_items=10,
            allow_empty=False,
        )

    @field_validator("follow_up_notes", mode="before")
    @classmethod
    def normalize_follow_up(cls, value: object) -> tuple[str, ...]:
        return _normalize_text_list(
            value,
            label="war room follow-up notes",
            maximum_items=20,
        )


class CampaignRoadmapAssessmentInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    campaign_version: int = Field(ge=1)
    campaign_status: Literal["DRAFT", "ACTIVE"]
    campaign_name: str = Field(min_length=1, max_length=255)
    title: str = Field(default="Campaign roadmap", min_length=1, max_length=255)
    team_role_ids: tuple[UUID, ...] = Field(max_length=200)
    phases: tuple[CampaignPhase, ...] | None = Field(default=None, max_length=100)
    workstreams: tuple[CampaignWorkstream, ...] | None = Field(default=None, max_length=100)
    milestones: tuple[CampaignMilestone, ...] | None = Field(default=None, max_length=300)
    tasks: tuple[CampaignTask, ...] | None = Field(default=None, max_length=500)
    blockers: tuple[CampaignBlocker, ...] | None = Field(default=None, max_length=500)
    decisions: tuple[CampaignDecision, ...] | None = Field(default=None, max_length=300)
    follow_up_items: tuple[CampaignFollowUpItem, ...] | None = Field(default=None, max_length=300)
    learning_notes: tuple[CampaignLearningNote, ...] | None = Field(default=None, max_length=300)
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime

    @field_validator("title", mode="before")
    @classmethod
    def normalize_title(cls, value: object) -> str:
        return _normalize_text(value, label="roadmap title", maximum=255)

    @model_validator(mode="after")
    def validate_timestamps(self) -> Self:
        if self.created_at.utcoffset() is None or self.updated_at.utcoffset() is None:
            raise ValueError("roadmap timestamps must include timezone")
        return self


class CampaignRoadmapProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    campaign_version: int
    campaign_status: Literal["DRAFT", "ACTIVE"]
    campaign_name: str
    title: str
    phases: tuple[CampaignPhase, ...] | None
    workstreams: tuple[CampaignWorkstream, ...] | None
    milestones: tuple[CampaignMilestone, ...] | None
    tasks: tuple[CampaignTask, ...] | None
    blockers: tuple[CampaignBlocker, ...] | None
    decisions: tuple[CampaignDecision, ...] | None
    follow_up_items: tuple[CampaignFollowUpItem, ...] | None
    learning_notes: tuple[CampaignLearningNote, ...] | None
    status: RoadmapStatus
    execution_order: tuple[UUID, ...]
    ready_task_ids: tuple[UUID, ...]
    blocked_task_ids: tuple[UUID, ...]
    critical_path_task_ids: tuple[UUID, ...]
    open_blocker_count: int = Field(ge=0)
    required_decision_count: int = Field(ge=0)
    next_action: RoadmapNextAction
    authority_effect: Literal["NONE"] = "NONE"
    external_effects: Literal["NONE"] = "NONE"
    limitation_codes: tuple[OperationsLimitation, ...]
    version: int = Field(ge=1)
    created_at: datetime
    updated_at: datetime


class WarRoomSnapshotProjection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    id: UUID
    tenant_id: UUID
    campaign_id: UUID
    roadmap_id: UUID
    roadmap_version: int = Field(ge=1)
    snapshot_date: date
    priorities: tuple[str, ...]
    ready_task_ids: tuple[UUID, ...]
    blocked_task_ids: tuple[UUID, ...]
    required_decision_ids: tuple[UUID, ...]
    follow_up_notes: tuple[str, ...]
    learning_note_ids: tuple[UUID, ...]
    authority_effect: Literal["NONE"] = "NONE"
    external_effects: Literal["NONE"] = "NONE"
    created_at: datetime


def _validate_unique_ids(value: CampaignRoadmapAssessmentInput) -> None:
    seen: set[UUID] = {value.id}
    for collection in (
        value.phases,
        value.workstreams,
        value.milestones,
        value.tasks,
        value.blockers,
        value.decisions,
        value.follow_up_items,
        value.learning_notes,
    ):
        for item in collection or ():
            _require(item.id not in seen, f"duplicate or colliding roadmap record ID: {item.id}")
            seen.add(item.id)


def _topological_order(tasks: tuple[CampaignTask, ...]) -> tuple[UUID, ...]:
    by_id = {task.id: task for task in tasks}
    index = {task.id: position for position, task in enumerate(tasks)}
    indegree = {task.id: 0 for task in tasks}
    dependents: dict[UUID, list[UUID]] = {task.id: [] for task in tasks}
    for task in tasks:
        for dependency_id in task.dependency_ids:
            _require(dependency_id != task.id, f"task self-dependency: {task.id}")
            _require(dependency_id in by_id, f"unknown task dependency: {dependency_id}")
            indegree[task.id] += 1
            dependents[dependency_id].append(task.id)
    ready = deque(
        sorted(
            (task_id for task_id, degree in indegree.items() if degree == 0),
            key=lambda task_id: index[task_id],
        )
    )
    order: list[UUID] = []
    while ready:
        task_id = ready.popleft()
        order.append(task_id)
        for dependent_id in sorted(
            dependents[task_id], key=lambda candidate_id: index[candidate_id]
        ):
            indegree[dependent_id] -= 1
            if indegree[dependent_id] == 0:
                ready.append(dependent_id)
    _require(len(order) == len(tasks), "task dependency graph contains a cycle")
    return tuple(order)


def _critical_path(
    tasks: tuple[CampaignTask, ...],
    execution_order: tuple[UUID, ...],
) -> tuple[UUID, ...]:
    by_id = {task.id: task for task in tasks}
    incomplete = {task.id for task in tasks if task.execution_status != "COMPLETE"}
    if not incomplete:
        return ()
    best: dict[UUID, tuple[UUID, ...]] = {}
    for task_id in execution_order:
        if task_id not in incomplete:
            continue
        predecessors = [
            best[dependency_id]
            for dependency_id in by_id[task_id].dependency_ids
            if dependency_id in best
        ]
        prefix = max(predecessors, key=lambda path: (len(path), tuple(map(str, path))), default=())
        best[task_id] = (*prefix, task_id)
    return max(best.values(), key=lambda path: (len(path), tuple(map(str, path))))


def assess_campaign_roadmap(value: CampaignRoadmapAssessmentInput) -> CampaignRoadmapProjection:
    """Validate the roadmap graph and derive operational views without execution."""
    _validate_unique_ids(value)
    team_roles = set(value.team_role_ids)
    _require(len(team_roles) == len(value.team_role_ids), "duplicate team role IDs")
    phases = value.phases or ()
    workstreams = value.workstreams or ()
    milestones = value.milestones or ()
    tasks = value.tasks or ()
    blockers = value.blockers or ()
    decisions = value.decisions or ()
    follow_up = value.follow_up_items or ()

    phase_ids = {item.id for item in phases}
    workstream_ids = {item.id for item in workstreams}
    milestone_ids = {item.id for item in milestones}
    task_ids = {item.id for item in tasks}
    _require(len({item.sequence for item in phases}) == len(phases), "duplicate phase sequence")

    for workstream in workstreams:
        _require(
            workstream.accountable_role_id in team_roles,
            f"unknown team role: {workstream.accountable_role_id}",
        )
    for milestone in milestones:
        _require(milestone.phase_id in phase_ids, f"unknown phase: {milestone.phase_id}")
        _require(
            milestone.owner_role_id in team_roles, f"unknown team role: {milestone.owner_role_id}"
        )
    for task in tasks:
        _require(task.phase_id in phase_ids, f"unknown phase: {task.phase_id}")
        _require(task.workstream_id in workstream_ids, f"unknown workstream: {task.workstream_id}")
        _require(
            task.milestone_id is None or task.milestone_id in milestone_ids,
            f"unknown milestone: {task.milestone_id}",
        )
        _require(task.owner_role_id in team_roles, f"unknown team role: {task.owner_role_id}")
    for blocker in blockers:
        _require(
            blocker.task_id is None or blocker.task_id in task_ids,
            f"unknown task: {blocker.task_id}",
        )
        _require(blocker.owner_role_id in team_roles, f"unknown team role: {blocker.owner_role_id}")
    for decision in decisions:
        _require(
            decision.human_role_id in team_roles, f"unknown team role: {decision.human_role_id}"
        )
        if decision.status == "DECIDED":
            _require(decision.decision is not None, "decided item requires a selected option")
            _require(decision.decision in decision.options, "selected option is not available")
        else:
            _require(decision.decision is None, "undecided item cannot contain a selected option")
    for item in follow_up:
        _require(item.owner_role_id in team_roles, f"unknown team role: {item.owner_role_id}")

    execution_order = _topological_order(tasks)
    tasks_by_id = {task.id: task for task in tasks}
    open_blockers = tuple(blocker for blocker in blockers if blocker.status == "OPEN")
    blocked_task_ids = tuple(
        task_id
        for task_id in execution_order
        if any(blocker.task_id == task_id for blocker in open_blockers)
    )
    blocked_set = set(blocked_task_ids)
    ready_task_ids = tuple(
        task_id
        for task_id in execution_order
        if tasks_by_id[task_id].execution_status == "PLANNED"
        and task_id not in blocked_set
        and all(
            tasks_by_id[dependency_id].execution_status == "COMPLETE"
            for dependency_id in tasks_by_id[task_id].dependency_ids
        )
    )
    critical_path = _critical_path(tasks, execution_order)
    required_decisions = tuple(item for item in decisions if item.status == "REQUIRED")

    if not tasks:
        status: RoadmapStatus = "SETUP_REQUIRED"
    elif all(task.execution_status == "COMPLETE" for task in tasks):
        status = "COMPLETE"
    elif ready_task_ids or any(task.execution_status == "IN_PROGRESS" for task in tasks):
        status = "READY_FOR_DAILY_OPERATION"
    else:
        status = "IN_PROGRESS"

    if open_blockers:
        next_action: RoadmapNextAction = "RESOLVE_BLOCKERS"
    elif required_decisions:
        next_action = "MAKE_HUMAN_DECISIONS"
    elif ready_task_ids:
        next_action = "START_READY_TASKS"
    elif any(task.execution_status == "IN_PROGRESS" for task in tasks):
        next_action = "CONTINUE_ACTIVE_WORK"
    elif tasks and all(task.execution_status == "COMPLETE" for task in tasks):
        next_action = "REVIEW_COMPLETION"
    else:
        next_action = "DEFINE_ROADMAP"

    return CampaignRoadmapProjection(
        id=value.id,
        tenant_id=value.tenant_id,
        campaign_id=value.campaign_id,
        campaign_version=value.campaign_version,
        campaign_status=value.campaign_status,
        campaign_name=value.campaign_name,
        title=value.title,
        phases=value.phases,
        workstreams=value.workstreams,
        milestones=value.milestones,
        tasks=value.tasks,
        blockers=value.blockers,
        decisions=value.decisions,
        follow_up_items=value.follow_up_items,
        learning_notes=value.learning_notes,
        status=status,
        execution_order=execution_order,
        ready_task_ids=ready_task_ids,
        blocked_task_ids=blocked_task_ids,
        critical_path_task_ids=critical_path,
        open_blocker_count=len(open_blockers),
        required_decision_count=len(required_decisions),
        next_action=next_action,
        limitation_codes=LIMITATION_CODES,
        version=value.version,
        created_at=value.created_at,
        updated_at=value.updated_at,
    )


def build_war_room_snapshot(
    roadmap: CampaignRoadmapProjection,
    *,
    request: WarRoomSnapshotCreate,
    snapshot_id: UUID,
    created_at: datetime,
) -> WarRoomSnapshotProjection:
    """Create an immutable operational snapshot from an exact roadmap version."""
    if created_at.utcoffset() is None:
        raise ValueError("war room snapshot created_at must include timezone")
    return WarRoomSnapshotProjection(
        id=snapshot_id,
        tenant_id=roadmap.tenant_id,
        campaign_id=roadmap.campaign_id,
        roadmap_id=roadmap.id,
        roadmap_version=roadmap.version,
        snapshot_date=request.snapshot_date,
        priorities=request.priorities,
        ready_task_ids=roadmap.ready_task_ids,
        blocked_task_ids=roadmap.blocked_task_ids,
        required_decision_ids=tuple(
            item.id for item in roadmap.decisions or () if item.status == "REQUIRED"
        ),
        follow_up_notes=request.follow_up_notes,
        learning_note_ids=tuple(item.id for item in roadmap.learning_notes or ()),
        created_at=created_at,
    )


class CampaignRoadmapCreateEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    roadmap: CampaignRoadmapProjection
    audit_event_id: UUID
    outbox_event_id: UUID


class CampaignRoadmapReadEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    roadmap: CampaignRoadmapProjection
    audit_event_id: UUID


class CampaignRoadmapUpdateEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    roadmap: CampaignRoadmapProjection
    audit_event_id: UUID
    outbox_event_id: UUID


class WarRoomSnapshotEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    snapshot: WarRoomSnapshotProjection
    audit_event_id: UUID
    outbox_event_id: UUID


class WarRoomSnapshotReadEvidence(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")

    snapshot: WarRoomSnapshotProjection
    audit_event_id: UUID
