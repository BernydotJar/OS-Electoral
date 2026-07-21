import type {
  CampaignMilestone,
  CampaignOperationsBlocker,
  CampaignOperationsDecision,
  CampaignOperationsFollowUp,
  CampaignOperationsLearningNote,
  CampaignOperationsTask,
  CampaignOperationsWorkstream,
  CampaignPhase,
  CampaignRoadmapNextAction,
  CampaignRoadmapProjection,
  CampaignRoadmapReadEvidence,
  WarRoomSnapshotProjection,
  WarRoomSnapshotReadEvidence,
} from "@/lib/contracts";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const LIMITATIONS = [
  "HUMAN_DECISIONS_REQUIRED",
  "NO_AUTONOMOUS_TASK_EXECUTION",
  "NO_CITIZEN_CONTACT",
  "NO_EXTERNAL_EFFECTS",
] as const;

type JsonRecord = Record<string, unknown>;
export class OperationsContractValidationError extends Error {}

function record(value: unknown, label: string): JsonRecord {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new OperationsContractValidationError(`${label} must be an object`);
  }
  return value as JsonRecord;
}

function exactKeys(
  source: JsonRecord,
  allowed: readonly string[],
  label: string,
): void {
  if (Object.keys(source).some((key) => !allowed.includes(key))) {
    throw new OperationsContractValidationError(
      `${label} contains unexpected fields`,
    );
  }
}

function text(value: unknown, label: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new OperationsContractValidationError(
      `${label} must be a non-empty string`,
    );
  }
  return value;
}

function uuid(value: unknown, label: string): string {
  const candidate = text(value, label);
  if (!UUID_PATTERN.test(candidate)) {
    throw new OperationsContractValidationError(`${label} must be a UUID`);
  }
  return candidate;
}

function nullableUuid(value: unknown, label: string): string | null {
  return value === null ? null : uuid(value, label);
}

function integer(value: unknown, label: string, minimum = 0): number {
  if (!Number.isInteger(value) || (value as number) < minimum) {
    throw new OperationsContractValidationError(
      `${label} must be an integer >= ${minimum}`,
    );
  }
  return value as number;
}

function array(value: unknown, label: string): readonly unknown[] {
  if (!Array.isArray(value)) {
    throw new OperationsContractValidationError(`${label} must be an array`);
  }
  return value;
}

function stringArray(value: unknown, label: string): readonly string[] {
  const values = array(value, label).map((item, index) =>
    text(item, `${label}[${index}]`),
  );
  if (new Set(values).size !== values.length) {
    throw new OperationsContractValidationError(`${label} contains duplicates`);
  }
  return values;
}

function uuidArray(value: unknown, label: string): readonly string[] {
  const values = array(value, label).map((item, index) =>
    uuid(item, `${label}[${index}]`),
  );
  if (new Set(values).size !== values.length) {
    throw new OperationsContractValidationError(`${label} contains duplicates`);
  }
  return values;
}

function literal<T extends string>(
  value: unknown,
  allowed: readonly T[],
  label: string,
): T {
  const candidate = text(value, label);
  if (!allowed.includes(candidate as T)) {
    throw new OperationsContractValidationError(`${label} is not supported`);
  }
  return candidate as T;
}

function date(value: unknown, label: string): string {
  const candidate = text(value, label);
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(candidate) ||
    !Number.isFinite(Date.parse(`${candidate}T00:00:00Z`))
  ) {
    throw new OperationsContractValidationError(`${label} must be an ISO date`);
  }
  return candidate;
}

function timestamp(value: unknown, label: string): string {
  const candidate = text(value, label);
  if (
    !Number.isFinite(Date.parse(candidate)) ||
    !/(?:Z|[+-]\d{2}:\d{2})$/.test(candidate)
  ) {
    throw new OperationsContractValidationError(
      `${label} must be a timezone-aware timestamp`,
    );
  }
  return candidate;
}

function nullableModels<T>(
  value: unknown,
  label: string,
  parse: (value: unknown, label: string) => T,
): readonly T[] | null {
  if (value === null) return null;
  return array(value, label).map((item, index) =>
    parse(item, `${label}[${index}]`),
  );
}

function parsePhase(value: unknown, label: string): CampaignPhase {
  const source = record(value, label);
  exactKeys(
    source,
    ["id", "name", "sequence", "start_date", "end_date", "status"],
    label,
  );
  const startDate = date(source.start_date, `${label}.start_date`);
  const endDate = date(source.end_date, `${label}.end_date`);
  if (endDate < startDate) {
    throw new OperationsContractValidationError(
      `${label} end date precedes start date`,
    );
  }
  return {
    id: uuid(source.id, `${label}.id`),
    name: text(source.name, `${label}.name`),
    sequence: integer(source.sequence, `${label}.sequence`, 1),
    start_date: startDate,
    end_date: endDate,
    status: literal(
      source.status,
      ["PLANNED", "ACTIVE", "COMPLETE"] as const,
      `${label}.status`,
    ),
  };
}

function parseWorkstream(
  value: unknown,
  label: string,
): CampaignOperationsWorkstream {
  const source = record(value, label);
  exactKeys(
    source,
    ["id", "name", "purpose", "accountable_role_id", "status"],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    name: text(source.name, `${label}.name`),
    purpose: text(source.purpose, `${label}.purpose`),
    accountable_role_id: uuid(
      source.accountable_role_id,
      `${label}.accountable_role_id`,
    ),
    status: literal(
      source.status,
      ["PLANNED", "ACTIVE", "PAUSED", "COMPLETE"] as const,
      `${label}.status`,
    ),
  };
}

function parseMilestone(value: unknown, label: string): CampaignMilestone {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "phase_id",
      "name",
      "completion_criteria",
      "owner_role_id",
      "due_date",
      "status",
    ],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    phase_id: uuid(source.phase_id, `${label}.phase_id`),
    name: text(source.name, `${label}.name`),
    completion_criteria: text(
      source.completion_criteria,
      `${label}.completion_criteria`,
    ),
    owner_role_id: uuid(source.owner_role_id, `${label}.owner_role_id`),
    due_date: date(source.due_date, `${label}.due_date`),
    status: literal(
      source.status,
      ["PLANNED", "IN_PROGRESS", "COMPLETE"] as const,
      `${label}.status`,
    ),
  };
}

function parseTask(value: unknown, label: string): CampaignOperationsTask {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "phase_id",
      "workstream_id",
      "milestone_id",
      "title",
      "owner_role_id",
      "execution_status",
      "dependency_ids",
      "due_date",
      "evidence_refs",
    ],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    phase_id: uuid(source.phase_id, `${label}.phase_id`),
    workstream_id: uuid(source.workstream_id, `${label}.workstream_id`),
    milestone_id: nullableUuid(source.milestone_id, `${label}.milestone_id`),
    title: text(source.title, `${label}.title`),
    owner_role_id: uuid(source.owner_role_id, `${label}.owner_role_id`),
    execution_status: literal(
      source.execution_status,
      ["PLANNED", "IN_PROGRESS", "COMPLETE"] as const,
      `${label}.execution_status`,
    ),
    dependency_ids: uuidArray(source.dependency_ids, `${label}.dependency_ids`),
    due_date: date(source.due_date, `${label}.due_date`),
    evidence_refs: uuidArray(source.evidence_refs, `${label}.evidence_refs`),
  };
}

function parseBlocker(
  value: unknown,
  label: string,
): CampaignOperationsBlocker {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "task_id",
      "severity",
      "status",
      "owner_role_id",
      "description",
      "resolution_condition",
    ],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    task_id: nullableUuid(source.task_id, `${label}.task_id`),
    severity: literal(
      source.severity,
      ["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const,
      `${label}.severity`,
    ),
    status: literal(
      source.status,
      ["OPEN", "RESOLVED"] as const,
      `${label}.status`,
    ),
    owner_role_id: uuid(source.owner_role_id, `${label}.owner_role_id`),
    description: text(source.description, `${label}.description`),
    resolution_condition: text(
      source.resolution_condition,
      `${label}.resolution_condition`,
    ),
  };
}

function parseDecision(
  value: unknown,
  label: string,
): CampaignOperationsDecision {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "title",
      "human_role_id",
      "options",
      "due_date",
      "status",
      "decision",
    ],
    label,
  );
  const status = literal(
    source.status,
    ["REQUIRED", "DECIDED", "DEFERRED"] as const,
    `${label}.status`,
  );
  const options = stringArray(source.options, `${label}.options`);
  if (options.length < 2) {
    throw new OperationsContractValidationError(
      `${label} requires at least two options`,
    );
  }
  const selected =
    source.decision === null
      ? null
      : text(source.decision, `${label}.decision`);
  if (
    status === "DECIDED" &&
    (selected === null || !options.includes(selected))
  ) {
    throw new OperationsContractValidationError(
      `${label} decided item requires an available option`,
    );
  }
  if (status !== "DECIDED" && selected !== null) {
    throw new OperationsContractValidationError(
      `${label} undecided item cannot select an option`,
    );
  }
  return {
    id: uuid(source.id, `${label}.id`),
    title: text(source.title, `${label}.title`),
    human_role_id: uuid(source.human_role_id, `${label}.human_role_id`),
    options,
    due_date: date(source.due_date, `${label}.due_date`),
    status,
    decision: selected,
  };
}

function parseFollowUp(
  value: unknown,
  label: string,
): CampaignOperationsFollowUp {
  const source = record(value, label);
  exactKeys(
    source,
    ["id", "title", "owner_role_id", "due_date", "status"],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    title: text(source.title, `${label}.title`),
    owner_role_id: uuid(source.owner_role_id, `${label}.owner_role_id`),
    due_date: date(source.due_date, `${label}.due_date`),
    status: literal(
      source.status,
      ["OPEN", "COMPLETE"] as const,
      `${label}.status`,
    ),
  };
}

function parseLearning(
  value: unknown,
  label: string,
): CampaignOperationsLearningNote {
  const source = record(value, label);
  exactKeys(source, ["id", "title", "note", "evidence_refs"], label);
  return {
    id: uuid(source.id, `${label}.id`),
    title: text(source.title, `${label}.title`),
    note: text(source.note, `${label}.note`),
    evidence_refs: uuidArray(source.evidence_refs, `${label}.evidence_refs`),
  };
}

function topologicalOrder(
  tasks: readonly CampaignOperationsTask[],
): readonly string[] {
  const byId = new Map(tasks.map((task) => [task.id, task]));
  const index = new Map(tasks.map((task, position) => [task.id, position]));
  const indegree = new Map(tasks.map((task) => [task.id, 0]));
  const dependents = new Map(tasks.map((task) => [task.id, [] as string[]]));
  for (const task of tasks) {
    for (const dependencyId of task.dependency_ids) {
      if (dependencyId === task.id) {
        throw new OperationsContractValidationError(
          `task self-dependency ${task.id}`,
        );
      }
      if (!byId.has(dependencyId)) {
        throw new OperationsContractValidationError(
          `unknown task dependency ${dependencyId}`,
        );
      }
      indegree.set(task.id, (indegree.get(task.id) ?? 0) + 1);
      dependents.get(dependencyId)!.push(task.id);
    }
  }
  const ready = [...indegree.entries()]
    .filter(([, degree]) => degree === 0)
    .map(([id]) => id)
    .sort((a, b) => index.get(a)! - index.get(b)!);
  const order: string[] = [];
  while (ready.length > 0) {
    const taskId = ready.shift()!;
    order.push(taskId);
    for (const dependentId of dependents
      .get(taskId)!
      .sort((a, b) => index.get(a)! - index.get(b)!)) {
      const degree = (indegree.get(dependentId) ?? 0) - 1;
      indegree.set(dependentId, degree);
      if (degree === 0) ready.push(dependentId);
    }
  }
  if (order.length !== tasks.length) {
    throw new OperationsContractValidationError(
      "task dependency graph contains a cycle",
    );
  }
  return order;
}

function criticalPath(
  tasks: readonly CampaignOperationsTask[],
  order: readonly string[],
): readonly string[] {
  const byId = new Map(tasks.map((task) => [task.id, task]));
  const incomplete = new Set(
    tasks
      .filter((task) => task.execution_status !== "COMPLETE")
      .map((task) => task.id),
  );
  const best = new Map<string, readonly string[]>();
  for (const taskId of order) {
    if (!incomplete.has(taskId)) continue;
    const task = byId.get(taskId)!;
    const predecessors = task.dependency_ids
      .map((dependency) => best.get(dependency))
      .filter((path): path is readonly string[] => path !== undefined);
    const prefix =
      [...predecessors].sort(
        (a, b) => b.length - a.length || b.join().localeCompare(a.join()),
      )[0] ?? [];
    best.set(taskId, [...prefix, taskId]);
  }
  return (
    [...best.values()].sort(
      (a, b) => b.length - a.length || b.join().localeCompare(a.join()),
    )[0] ?? []
  );
}

function sameArray(
  actual: readonly string[],
  expected: readonly string[],
): boolean {
  return (
    actual.length === expected.length &&
    actual.every((item, index) => item === expected[index])
  );
}

function parseRoadmap(value: unknown): CampaignRoadmapProjection {
  const source = record(value, "campaign roadmap");
  exactKeys(
    source,
    [
      "id",
      "tenant_id",
      "campaign_id",
      "campaign_version",
      "campaign_status",
      "campaign_name",
      "title",
      "phases",
      "workstreams",
      "milestones",
      "tasks",
      "blockers",
      "decisions",
      "follow_up_items",
      "learning_notes",
      "status",
      "execution_order",
      "ready_task_ids",
      "blocked_task_ids",
      "critical_path_task_ids",
      "open_blocker_count",
      "required_decision_count",
      "next_action",
      "authority_effect",
      "external_effects",
      "limitation_codes",
      "version",
      "created_at",
      "updated_at",
    ],
    "campaign roadmap",
  );
  const roadmapId = uuid(source.id, "campaign roadmap.id");
  const phases = nullableModels(
    source.phases,
    "campaign roadmap.phases",
    parsePhase,
  );
  const workstreams = nullableModels(
    source.workstreams,
    "campaign roadmap.workstreams",
    parseWorkstream,
  );
  const milestones = nullableModels(
    source.milestones,
    "campaign roadmap.milestones",
    parseMilestone,
  );
  const tasks = nullableModels(
    source.tasks,
    "campaign roadmap.tasks",
    parseTask,
  );
  const blockers = nullableModels(
    source.blockers,
    "campaign roadmap.blockers",
    parseBlocker,
  );
  const decisions = nullableModels(
    source.decisions,
    "campaign roadmap.decisions",
    parseDecision,
  );
  const followUps = nullableModels(
    source.follow_up_items,
    "campaign roadmap.follow_up_items",
    parseFollowUp,
  );
  const learning = nullableModels(
    source.learning_notes,
    "campaign roadmap.learning_notes",
    parseLearning,
  );

  const ids = [
    roadmapId,
    ...(phases ?? []).map((item) => item.id),
    ...(workstreams ?? []).map((item) => item.id),
    ...(milestones ?? []).map((item) => item.id),
    ...(tasks ?? []).map((item) => item.id),
    ...(blockers ?? []).map((item) => item.id),
    ...(decisions ?? []).map((item) => item.id),
    ...(followUps ?? []).map((item) => item.id),
    ...(learning ?? []).map((item) => item.id),
  ];
  if (new Set(ids).size !== ids.length) {
    throw new OperationsContractValidationError(
      "roadmap contains duplicate or colliding IDs",
    );
  }
  const phaseIds = new Set((phases ?? []).map((item) => item.id));
  const workstreamIds = new Set((workstreams ?? []).map((item) => item.id));
  const milestoneIds = new Set((milestones ?? []).map((item) => item.id));
  const taskIds = new Set((tasks ?? []).map((item) => item.id));
  if (
    new Set((phases ?? []).map((item) => item.sequence)).size !==
    (phases ?? []).length
  ) {
    throw new OperationsContractValidationError("duplicate phase sequence");
  }
  for (const milestone of milestones ?? []) {
    if (!phaseIds.has(milestone.phase_id))
      throw new OperationsContractValidationError(
        `unknown phase ${milestone.phase_id}`,
      );
  }
  for (const task of tasks ?? []) {
    if (!phaseIds.has(task.phase_id))
      throw new OperationsContractValidationError(
        `unknown phase ${task.phase_id}`,
      );
    if (!workstreamIds.has(task.workstream_id))
      throw new OperationsContractValidationError(
        `unknown workstream ${task.workstream_id}`,
      );
    if (task.milestone_id !== null && !milestoneIds.has(task.milestone_id)) {
      throw new OperationsContractValidationError(
        `unknown milestone ${task.milestone_id}`,
      );
    }
  }
  for (const blocker of blockers ?? []) {
    if (blocker.task_id !== null && !taskIds.has(blocker.task_id)) {
      throw new OperationsContractValidationError(
        `unknown blocker task ${blocker.task_id}`,
      );
    }
  }
  const taskList = tasks ?? [];
  const order = topologicalOrder(taskList);
  const tasksById = new Map(taskList.map((task) => [task.id, task]));
  for (const task of taskList) {
    if (
      task.execution_status === "COMPLETE" &&
      task.dependency_ids.some(
        (dependency) =>
          tasksById.get(dependency)?.execution_status !== "COMPLETE",
      )
    ) {
      throw new OperationsContractValidationError(
        `complete task requires complete dependencies ${task.id}`,
      );
    }
  }
  const openBlockers = (blockers ?? []).filter(
    (blocker) => blocker.status === "OPEN",
  );
  const blocked = order.filter((taskId) =>
    openBlockers.some((blocker) => blocker.task_id === taskId),
  );
  const blockedSet = new Set(blocked);
  const ready = order.filter((taskId) => {
    const task = tasksById.get(taskId)!;
    return (
      task.execution_status === "PLANNED" &&
      !blockedSet.has(taskId) &&
      task.dependency_ids.every(
        (dependency) =>
          tasksById.get(dependency)?.execution_status === "COMPLETE",
      )
    );
  });
  const path = criticalPath(taskList, order);
  const requiredDecisions = (decisions ?? []).filter(
    (item) => item.status === "REQUIRED",
  );
  const expectedStatus =
    taskList.length === 0
      ? "SETUP_REQUIRED"
      : taskList.every((task) => task.execution_status === "COMPLETE")
        ? "COMPLETE"
        : ready.length > 0 ||
            taskList.some((task) => task.execution_status === "IN_PROGRESS")
          ? "READY_FOR_DAILY_OPERATION"
          : "IN_PROGRESS";
  const expectedNext: CampaignRoadmapNextAction =
    openBlockers.length > 0
      ? "RESOLVE_BLOCKERS"
      : requiredDecisions.length > 0
        ? "MAKE_HUMAN_DECISIONS"
        : ready.length > 0
          ? "START_READY_TASKS"
          : taskList.some((task) => task.execution_status === "IN_PROGRESS")
            ? "CONTINUE_ACTIVE_WORK"
            : taskList.length > 0 &&
                taskList.every((task) => task.execution_status === "COMPLETE")
              ? "REVIEW_COMPLETION"
              : "DEFINE_ROADMAP";
  const actualOrder = uuidArray(
    source.execution_order,
    "campaign roadmap.execution_order",
  );
  const actualReady = uuidArray(
    source.ready_task_ids,
    "campaign roadmap.ready_task_ids",
  );
  const actualBlocked = uuidArray(
    source.blocked_task_ids,
    "campaign roadmap.blocked_task_ids",
  );
  const actualPath = uuidArray(
    source.critical_path_task_ids,
    "campaign roadmap.critical_path_task_ids",
  );
  if (!sameArray(actualOrder, order))
    throw new OperationsContractValidationError(
      "execution order is inconsistent",
    );
  if (!sameArray(actualReady, ready))
    throw new OperationsContractValidationError("ready tasks are inconsistent");
  if (!sameArray(actualBlocked, blocked))
    throw new OperationsContractValidationError(
      "blocked tasks are inconsistent",
    );
  if (!sameArray(actualPath, path))
    throw new OperationsContractValidationError(
      "critical path is inconsistent",
    );
  if (
    source.open_blocker_count !== openBlockers.length ||
    source.required_decision_count !== requiredDecisions.length
  ) {
    throw new OperationsContractValidationError(
      "roadmap summary counts are inconsistent",
    );
  }
  const status = literal(
    source.status,
    [
      "SETUP_REQUIRED",
      "IN_PROGRESS",
      "READY_FOR_DAILY_OPERATION",
      "COMPLETE",
    ] as const,
    "campaign roadmap.status",
  );
  if (status !== expectedStatus)
    throw new OperationsContractValidationError(
      "roadmap status is inconsistent",
    );
  const nextAction = literal(
    source.next_action,
    [
      "DEFINE_ROADMAP",
      "RESOLVE_BLOCKERS",
      "MAKE_HUMAN_DECISIONS",
      "START_READY_TASKS",
      "CONTINUE_ACTIVE_WORK",
      "REVIEW_COMPLETION",
    ] as const,
    "campaign roadmap.next_action",
  );
  if (nextAction !== expectedNext)
    throw new OperationsContractValidationError(
      "roadmap next action is inconsistent",
    );
  const limitations = stringArray(
    source.limitation_codes,
    "campaign roadmap.limitation_codes",
  );
  if (!sameArray(limitations, LIMITATIONS)) {
    throw new OperationsContractValidationError(
      "roadmap mandatory limitations are missing",
    );
  }
  return {
    id: roadmapId,
    tenant_id: uuid(source.tenant_id, "campaign roadmap.tenant_id"),
    campaign_id: uuid(source.campaign_id, "campaign roadmap.campaign_id"),
    campaign_version: integer(
      source.campaign_version,
      "campaign roadmap.campaign_version",
      1,
    ),
    campaign_status: literal(
      source.campaign_status,
      ["DRAFT", "ACTIVE"] as const,
      "campaign roadmap.campaign_status",
    ),
    campaign_name: text(source.campaign_name, "campaign roadmap.campaign_name"),
    title: text(source.title, "campaign roadmap.title"),
    phases,
    workstreams,
    milestones,
    tasks,
    blockers,
    decisions,
    follow_up_items: followUps,
    learning_notes: learning,
    status,
    execution_order: actualOrder,
    ready_task_ids: actualReady,
    blocked_task_ids: actualBlocked,
    critical_path_task_ids: actualPath,
    open_blocker_count: integer(
      source.open_blocker_count,
      "campaign roadmap.open_blocker_count",
    ),
    required_decision_count: integer(
      source.required_decision_count,
      "campaign roadmap.required_decision_count",
    ),
    next_action: nextAction,
    authority_effect: literal(
      source.authority_effect,
      ["NONE"] as const,
      "campaign roadmap.authority_effect",
    ),
    external_effects: literal(
      source.external_effects,
      ["NONE"] as const,
      "campaign roadmap.external_effects",
    ),
    limitation_codes:
      limitations as CampaignRoadmapProjection["limitation_codes"],
    version: integer(source.version, "campaign roadmap.version", 1),
    created_at: timestamp(source.created_at, "campaign roadmap.created_at"),
    updated_at: timestamp(source.updated_at, "campaign roadmap.updated_at"),
  };
}

function parseSnapshot(value: unknown): WarRoomSnapshotProjection {
  const source = record(value, "war room snapshot");
  exactKeys(
    source,
    [
      "id",
      "tenant_id",
      "campaign_id",
      "roadmap_id",
      "roadmap_version",
      "snapshot_date",
      "priorities",
      "ready_task_ids",
      "blocked_task_ids",
      "required_decision_ids",
      "follow_up_notes",
      "learning_note_ids",
      "authority_effect",
      "external_effects",
      "created_at",
    ],
    "war room snapshot",
  );
  return {
    id: uuid(source.id, "war room snapshot.id"),
    tenant_id: uuid(source.tenant_id, "war room snapshot.tenant_id"),
    campaign_id: uuid(source.campaign_id, "war room snapshot.campaign_id"),
    roadmap_id: uuid(source.roadmap_id, "war room snapshot.roadmap_id"),
    roadmap_version: integer(
      source.roadmap_version,
      "war room snapshot.roadmap_version",
      1,
    ),
    snapshot_date: date(
      source.snapshot_date,
      "war room snapshot.snapshot_date",
    ),
    priorities: stringArray(source.priorities, "war room snapshot.priorities"),
    ready_task_ids: uuidArray(
      source.ready_task_ids,
      "war room snapshot.ready_task_ids",
    ),
    blocked_task_ids: uuidArray(
      source.blocked_task_ids,
      "war room snapshot.blocked_task_ids",
    ),
    required_decision_ids: uuidArray(
      source.required_decision_ids,
      "war room snapshot.required_decision_ids",
    ),
    follow_up_notes: stringArray(
      source.follow_up_notes,
      "war room snapshot.follow_up_notes",
    ),
    learning_note_ids: uuidArray(
      source.learning_note_ids,
      "war room snapshot.learning_note_ids",
    ),
    authority_effect: literal(
      source.authority_effect,
      ["NONE"] as const,
      "war room snapshot.authority_effect",
    ),
    external_effects: literal(
      source.external_effects,
      ["NONE"] as const,
      "war room snapshot.external_effects",
    ),
    created_at: timestamp(source.created_at, "war room snapshot.created_at"),
  };
}

export function parseCampaignRoadmapReadEvidence(
  value: unknown,
): CampaignRoadmapReadEvidence {
  const source = record(value, "campaign roadmap evidence");
  exactKeys(source, ["roadmap", "audit_event_id"], "campaign roadmap evidence");
  return {
    roadmap: parseRoadmap(source.roadmap),
    audit_event_id: uuid(
      source.audit_event_id,
      "campaign roadmap evidence.audit_event_id",
    ),
  };
}

export function parseWarRoomSnapshotReadEvidence(
  value: unknown,
): WarRoomSnapshotReadEvidence {
  const source = record(value, "war room snapshot evidence");
  exactKeys(
    source,
    ["snapshot", "audit_event_id"],
    "war room snapshot evidence",
  );
  return {
    snapshot: parseSnapshot(source.snapshot),
    audit_event_id: uuid(
      source.audit_event_id,
      "war room snapshot evidence.audit_event_id",
    ),
  };
}

export function reconcileWarRoomSnapshot(
  roadmap: CampaignRoadmapProjection,
  snapshot: WarRoomSnapshotProjection,
): WarRoomSnapshotProjection {
  if (
    snapshot.tenant_id !== roadmap.tenant_id ||
    snapshot.campaign_id !== roadmap.campaign_id ||
    snapshot.roadmap_id !== roadmap.id
  ) {
    throw new OperationsContractValidationError(
      "war room snapshot scope mismatch",
    );
  }
  if (snapshot.roadmap_version !== roadmap.version) {
    throw new OperationsContractValidationError(
      "war room snapshot roadmap version is stale",
    );
  }
  if (!sameArray(snapshot.ready_task_ids, roadmap.ready_task_ids)) {
    throw new OperationsContractValidationError(
      "war room ready tasks contradict roadmap",
    );
  }
  if (!sameArray(snapshot.blocked_task_ids, roadmap.blocked_task_ids)) {
    throw new OperationsContractValidationError(
      "war room blocked tasks contradict roadmap",
    );
  }
  const required = (roadmap.decisions ?? [])
    .filter((item) => item.status === "REQUIRED")
    .map((item) => item.id);
  if (!sameArray(snapshot.required_decision_ids, required)) {
    throw new OperationsContractValidationError(
      "war room decisions contradict roadmap",
    );
  }
  const learning = (roadmap.learning_notes ?? []).map((item) => item.id);
  if (!sameArray(snapshot.learning_note_ids, learning)) {
    throw new OperationsContractValidationError(
      "war room learning notes contradict roadmap",
    );
  }
  return snapshot;
}
