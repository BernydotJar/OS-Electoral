import type {
  TeamAccessRecommendation,
  TeamCheckKey,
  TeamLimitation,
  TeamNextAction,
  TeamRaciAssignment,
  TeamRoleCard,
  TeamTrainingRequirement,
  TeamWorkItem,
  TeamWorkspaceCheck,
  TeamWorkspaceProjection,
  TeamWorkspaceReadEvidence,
} from "@/lib/contracts";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const CHECKS = [
  "organization_template",
  "role_cards",
  "accountability",
  "availability",
  "vacancies",
  "onboarding",
  "training",
  "access_review",
] as const satisfies readonly TeamCheckKey[];
const LIMITATIONS = [
  "ROLE_LABELS_ARE_NOT_PERMISSIONS",
  "ACCESS_RECOMMENDATIONS_REQUIRE_HUMAN_AUTHORIZATION",
  "NO_VOTER_PROFILING",
  "NO_EXTERNAL_EFFECTS",
] as const satisfies readonly TeamLimitation[];

export class TeamContractValidationError extends Error {}
type JsonRecord = Record<string, unknown>;

function record(value: unknown, label: string): JsonRecord {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TeamContractValidationError(`${label} must be an object`);
  }
  return value as JsonRecord;
}

function exactKeys(
  source: JsonRecord,
  keys: readonly string[],
  label: string,
): void {
  if (Object.keys(source).some((key) => !keys.includes(key))) {
    throw new TeamContractValidationError(
      `${label} contains unexpected fields`,
    );
  }
}

function text(value: unknown, label: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new TeamContractValidationError(
      `${label} must be a non-empty string`,
    );
  }
  return value;
}

function uuid(value: unknown, label: string): string {
  const candidate = text(value, label);
  if (!UUID_PATTERN.test(candidate))
    throw new TeamContractValidationError(`${label} must be a UUID`);
  return candidate;
}

function nullableUuid(value: unknown, label: string): string | null {
  return value === null ? null : uuid(value, label);
}

function integer(value: unknown, label: string, minimum = 0): number {
  if (!Number.isInteger(value) || (value as number) < minimum) {
    throw new TeamContractValidationError(
      `${label} must be an integer >= ${minimum}`,
    );
  }
  return value as number;
}

function boolean(value: unknown, label: string): boolean {
  if (typeof value !== "boolean")
    throw new TeamContractValidationError(`${label} must be a boolean`);
  return value;
}

function array(value: unknown, label: string): readonly unknown[] {
  if (!Array.isArray(value))
    throw new TeamContractValidationError(`${label} must be an array`);
  return value;
}

function timestamp(value: unknown, label: string): string {
  const candidate = text(value, label);
  if (
    !Number.isFinite(Date.parse(candidate)) ||
    !/(?:Z|[+-]\d{2}:\d{2})$/.test(candidate)
  ) {
    throw new TeamContractValidationError(
      `${label} must be a timezone-aware timestamp`,
    );
  }
  return candidate;
}

function literal<T extends string>(
  value: unknown,
  allowed: readonly T[],
  label: string,
): T {
  const candidate = text(value, label);
  if (!allowed.includes(candidate as T))
    throw new TeamContractValidationError(`${label} is not supported`);
  return candidate as T;
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

function parseRole(value: unknown, label: string): TeamRoleCard {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "title",
      "area",
      "purpose",
      "responsibilities",
      "status",
      "principal_id",
      "availability_status",
      "weekly_capacity_hours",
      "onboarding_status",
      "vacancy_plan",
    ],
    label,
  );
  const role: TeamRoleCard = {
    id: uuid(source.id, `${label}.id`),
    title: text(source.title, `${label}.title`),
    area: text(source.area, `${label}.area`),
    purpose: text(source.purpose, `${label}.purpose`),
    responsibilities: array(
      source.responsibilities,
      `${label}.responsibilities`,
    ).map((item, index) => text(item, `${label}.responsibilities[${index}]`)),
    status: literal(
      source.status,
      ["FILLED", "VACANT"] as const,
      `${label}.status`,
    ),
    principal_id: nullableUuid(source.principal_id, `${label}.principal_id`),
    availability_status: literal(
      source.availability_status,
      ["UNASSESSED", "AVAILABLE", "LIMITED", "UNAVAILABLE"] as const,
      `${label}.availability_status`,
    ),
    weekly_capacity_hours:
      source.weekly_capacity_hours === null
        ? null
        : integer(
            source.weekly_capacity_hours,
            `${label}.weekly_capacity_hours`,
          ),
    onboarding_status: literal(
      source.onboarding_status,
      ["NOT_STARTED", "IN_PROGRESS", "COMPLETE"] as const,
      `${label}.onboarding_status`,
    ),
    vacancy_plan:
      source.vacancy_plan === null
        ? null
        : text(source.vacancy_plan, `${label}.vacancy_plan`),
  };
  if (role.status === "FILLED") {
    if (role.principal_id === null) {
      throw new TeamContractValidationError(
        `${label} filled role requires a principal`,
      );
    }
    if (role.vacancy_plan !== null) {
      throw new TeamContractValidationError(
        `${label} filled role cannot retain a vacancy plan`,
      );
    }
  } else {
    if (role.principal_id !== null) {
      throw new TeamContractValidationError(
        `${label} vacant role cannot have a principal`,
      );
    }
    if (role.weekly_capacity_hours !== null) {
      throw new TeamContractValidationError(
        `${label} vacant role cannot have capacity`,
      );
    }
    if (role.availability_status !== "UNASSESSED") {
      throw new TeamContractValidationError(
        `${label} vacant role availability must be unassessed`,
      );
    }
    if (role.vacancy_plan === null) {
      throw new TeamContractValidationError(
        `${label} vacant role requires a vacancy plan`,
      );
    }
  }
  return role;
}

function parseAssignment(value: unknown, label: string): TeamRaciAssignment {
  const source = record(value, label);
  exactKeys(source, ["role_id", "responsibility"], label);
  return {
    role_id: uuid(source.role_id, `${label}.role_id`),
    responsibility: literal(
      source.responsibility,
      ["RESPONSIBLE", "ACCOUNTABLE", "CONSULTED", "INFORMED"] as const,
      `${label}.responsibility`,
    ),
  };
}

function parseWorkItem(value: unknown, label: string): TeamWorkItem {
  const source = record(value, label);
  exactKeys(
    source,
    ["id", "name", "description", "status", "assignments"],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    name: text(source.name, `${label}.name`),
    description: text(source.description, `${label}.description`),
    status: literal(
      source.status,
      ["PLANNED", "ACTIVE", "BLOCKED", "COMPLETE"] as const,
      `${label}.status`,
    ),
    assignments: array(source.assignments, `${label}.assignments`).map(
      (item, index) => parseAssignment(item, `${label}.assignments[${index}]`),
    ),
  };
}

function parseTraining(value: unknown, label: string): TeamTrainingRequirement {
  const source = record(value, label);
  exactKeys(source, ["id", "role_id", "title", "description", "status"], label);
  return {
    id: uuid(source.id, `${label}.id`),
    role_id: uuid(source.role_id, `${label}.role_id`),
    title: text(source.title, `${label}.title`),
    description: text(source.description, `${label}.description`),
    status: literal(
      source.status,
      ["NOT_STARTED", "IN_PROGRESS", "COMPLETE"] as const,
      `${label}.status`,
    ),
  };
}

function parseAccess(value: unknown, label: string): TeamAccessRecommendation {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "role_id",
      "campaign_id",
      "workspace_id",
      "action",
      "resource_type",
      "resource_id",
      "purpose",
      "status",
      "authority_effect",
    ],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    role_id: uuid(source.role_id, `${label}.role_id`),
    campaign_id: uuid(source.campaign_id, `${label}.campaign_id`),
    workspace_id: nullableUuid(source.workspace_id, `${label}.workspace_id`),
    action: text(source.action, `${label}.action`),
    resource_type: text(source.resource_type, `${label}.resource_type`),
    resource_id: text(source.resource_id, `${label}.resource_id`),
    purpose: text(source.purpose, `${label}.purpose`),
    status: literal(
      source.status,
      ["PROPOSED", "REVIEWED", "REJECTED"] as const,
      `${label}.status`,
    ),
    authority_effect: literal(
      source.authority_effect,
      ["NONE"] as const,
      `${label}.authority_effect`,
    ),
  };
}

function parseCheck(value: unknown, label: string): TeamWorkspaceCheck {
  const source = record(value, label);
  exactKeys(source, ["key", "complete", "reason_code"], label);
  return {
    key: literal(source.key, CHECKS, `${label}.key`),
    complete: boolean(source.complete, `${label}.complete`),
    reason_code: text(source.reason_code, `${label}.reason_code`),
  };
}

function parseProjection(value: unknown): TeamWorkspaceProjection {
  const source = record(value, "team workspace");
  exactKeys(
    source,
    [
      "id",
      "tenant_id",
      "campaign_id",
      "campaign_version",
      "campaign_status",
      "campaign_name",
      "organization_template",
      "roles",
      "work_items",
      "training_requirements",
      "access_recommendations",
      "status",
      "checks",
      "completed_checks",
      "total_checks",
      "filled_role_count",
      "vacant_role_count",
      "total_weekly_capacity_hours",
      "next_action",
      "authority_effect",
      "external_effects",
      "limitation_codes",
      "version",
      "created_at",
      "updated_at",
    ],
    "team workspace",
  );
  const workspaceId = uuid(source.id, "team workspace.id");
  const campaignId = uuid(source.campaign_id, "team workspace.campaign_id");
  const roles = nullableModels(source.roles, "team workspace.roles", parseRole);
  const workItems = nullableModels(
    source.work_items,
    "team workspace.work_items",
    parseWorkItem,
  );
  const training = nullableModels(
    source.training_requirements,
    "team workspace.training",
    parseTraining,
  );
  const access = nullableModels(
    source.access_recommendations,
    "team workspace.access",
    parseAccess,
  );
  const ids = [
    workspaceId,
    ...(roles ?? []).map((item) => item.id),
    ...(workItems ?? []).map((item) => item.id),
    ...(training ?? []).map((item) => item.id),
    ...(access ?? []).map((item) => item.id),
  ];
  if (new Set(ids).size !== ids.length) {
    throw new TeamContractValidationError(
      "team workspace contains duplicate record IDs",
    );
  }
  const rolesById = new Map((roles ?? []).map((role) => [role.id, role]));
  for (const item of workItems ?? []) {
    const keys = item.assignments.map(
      (assignment) => `${assignment.role_id}:${assignment.responsibility}`,
    );
    if (new Set(keys).size !== keys.length) {
      throw new TeamContractValidationError(
        `duplicate RACI assignment ${item.id}`,
      );
    }
    if (
      item.assignments.some((assignment) => !rolesById.has(assignment.role_id))
    ) {
      throw new TeamContractValidationError(
        `unknown role reference in RACI item ${item.id}`,
      );
    }
    if (
      item.status === "ACTIVE" &&
      item.assignments.some(
        (assignment) =>
          (assignment.responsibility === "ACCOUNTABLE" ||
            assignment.responsibility === "RESPONSIBLE") &&
          rolesById.get(assignment.role_id)?.status !== "FILLED",
      )
    ) {
      throw new TeamContractValidationError(
        `active accountability requires a filled role ${item.id}`,
      );
    }
    if (
      item.assignments.filter(
        (assignment) => assignment.responsibility === "ACCOUNTABLE",
      ).length !== 1
    ) {
      throw new TeamContractValidationError(
        `work item requires exactly one accountable role ${item.id}`,
      );
    }
    if (
      !item.assignments.some(
        (assignment) => assignment.responsibility === "RESPONSIBLE",
      )
    ) {
      throw new TeamContractValidationError(
        `work item requires a responsible role ${item.id}`,
      );
    }
  }
  if ((training ?? []).some((item) => !rolesById.has(item.role_id))) {
    throw new TeamContractValidationError(
      "training references an unknown role",
    );
  }
  if ((access ?? []).some((item) => !rolesById.has(item.role_id))) {
    throw new TeamContractValidationError(
      "access recommendation references an unknown role",
    );
  }
  if ((access ?? []).some((item) => item.campaign_id !== campaignId)) {
    throw new TeamContractValidationError(
      "cross-campaign access recommendation is invalid",
    );
  }
  for (const recommendation of access ?? []) {
    if (
      recommendation.workspace_id === null &&
      recommendation.resource_id !== campaignId
    ) {
      throw new TeamContractValidationError(
        `campaign-scoped resource ID must match campaign ${recommendation.id}`,
      );
    }
    if (
      recommendation.workspace_id !== null &&
      recommendation.resource_id !== recommendation.workspace_id
    ) {
      throw new TeamContractValidationError(
        `workspace-scoped resource ID must match workspace ${recommendation.id}`,
      );
    }
  }

  const rolesDefined = roles !== null && roles.length > 0;
  const accountabilityComplete = workItems !== null && workItems.length > 0;
  const availabilityComplete =
    roles !== null &&
    roles.every(
      (role) =>
        role.status === "VACANT" ||
        ((role.availability_status === "AVAILABLE" ||
          role.availability_status === "LIMITED") &&
          role.weekly_capacity_hours !== null &&
          role.weekly_capacity_hours > 0),
    );
  const vacanciesComplete = roles !== null;
  const onboardingComplete =
    roles !== null &&
    roles.every(
      (role) =>
        role.status === "VACANT" || role.onboarding_status === "COMPLETE",
    );
  const trainingComplete =
    training !== null && training.every((item) => item.status === "COMPLETE");
  const accessComplete =
    access !== null &&
    access.every(
      (item) => item.status === "REVIEWED" || item.status === "REJECTED",
    );
  const completeByKey: Readonly<Record<TeamCheckKey, boolean>> = {
    organization_template: true,
    role_cards: rolesDefined,
    accountability: accountabilityComplete,
    availability: availabilityComplete,
    vacancies: vacanciesComplete,
    onboarding: onboardingComplete,
    training: trainingComplete,
    access_review: accessComplete,
  };
  const checks = array(source.checks, "team workspace.checks").map(
    (item, index) => parseCheck(item, `team workspace.checks[${index}]`),
  );
  if (
    checks.length !== CHECKS.length ||
    checks.some(
      (check, index) =>
        check.key !== CHECKS[index] ||
        check.complete !== completeByKey[check.key],
    )
  ) {
    throw new TeamContractValidationError(
      "team workspace checks are not canonical",
    );
  }
  const completedChecks = integer(
    source.completed_checks,
    "team workspace.completed_checks",
  );
  const totalChecks = integer(
    source.total_checks,
    "team workspace.total_checks",
    1,
  );
  if (
    totalChecks !== checks.length ||
    completedChecks !== checks.filter((check) => check.complete).length
  ) {
    throw new TeamContractValidationError(
      "team workspace summary does not match checks",
    );
  }
  const expectedStatus = !rolesDefined
    ? "SETUP_REQUIRED"
    : completedChecks === totalChecks
      ? "READY_FOR_HUMAN_REVIEW"
      : "STRUCTURE_IN_PROGRESS";
  const expectedNextAction: TeamNextAction = !rolesDefined
    ? "DEFINE_ROLE_CARDS"
    : !accountabilityComplete
      ? "ASSIGN_ACCOUNTABILITY"
      : !availabilityComplete
        ? "ASSESS_AVAILABILITY"
        : !vacanciesComplete
          ? "PLAN_VACANCIES"
          : !onboardingComplete
            ? "COMPLETE_ONBOARDING"
            : !trainingComplete
              ? "COMPLETE_TRAINING"
              : !accessComplete
                ? "REVIEW_ACCESS_RECOMMENDATIONS"
                : "CONTINUE_HUMAN_GOVERNANCE";
  const filled = (roles ?? []).filter((role) => role.status === "FILLED");
  const vacant = (roles ?? []).filter((role) => role.status === "VACANT");
  const capacity = filled.reduce(
    (sum, role) => sum + (role.weekly_capacity_hours ?? 0),
    0,
  );
  if (
    source.filled_role_count !== filled.length ||
    source.vacant_role_count !== vacant.length ||
    source.total_weekly_capacity_hours !== capacity
  ) {
    throw new TeamContractValidationError(
      "team workspace capacity summary is inconsistent",
    );
  }
  const limitations = array(
    source.limitation_codes,
    "team workspace.limitation_codes",
  ).map((item, index) =>
    literal(item, LIMITATIONS, `team workspace.limitation_codes[${index}]`),
  );
  if (
    limitations.length !== LIMITATIONS.length ||
    limitations.some((item, i) => item !== LIMITATIONS[i])
  ) {
    throw new TeamContractValidationError(
      "team workspace mandatory limitations are missing",
    );
  }
  return {
    id: workspaceId,
    tenant_id: uuid(source.tenant_id, "team workspace.tenant_id"),
    campaign_id: campaignId,
    campaign_version: integer(
      source.campaign_version,
      "team workspace.campaign_version",
      1,
    ),
    campaign_status: literal(
      source.campaign_status,
      ["DRAFT", "ACTIVE"] as const,
      "team workspace.campaign_status",
    ),
    campaign_name: text(source.campaign_name, "team workspace.campaign_name"),
    organization_template: literal(
      source.organization_template,
      ["LEAN_CAMPAIGN", "FULL_CAMPAIGN", "CUSTOM"] as const,
      "team workspace.organization_template",
    ),
    roles,
    work_items: workItems,
    training_requirements: training,
    access_recommendations: access,
    status: (() => {
      const status = literal(
        source.status,
        [
          "SETUP_REQUIRED",
          "STRUCTURE_IN_PROGRESS",
          "READY_FOR_HUMAN_REVIEW",
        ] as const,
        "team workspace.status",
      );
      if (status !== expectedStatus) {
        throw new TeamContractValidationError(
          "team workspace status is inconsistent",
        );
      }
      return status;
    })(),
    checks,
    completed_checks: completedChecks,
    total_checks: totalChecks,
    filled_role_count: integer(
      source.filled_role_count,
      "team workspace.filled_role_count",
    ),
    vacant_role_count: integer(
      source.vacant_role_count,
      "team workspace.vacant_role_count",
    ),
    total_weekly_capacity_hours: integer(
      source.total_weekly_capacity_hours,
      "team workspace.capacity",
    ),
    next_action: literal(
      source.next_action,
      [expectedNextAction] as const,
      "team workspace.next_action",
    ),
    authority_effect: literal(
      source.authority_effect,
      ["NONE"] as const,
      "team workspace.authority_effect",
    ),
    external_effects: literal(
      source.external_effects,
      ["NONE"] as const,
      "team workspace.external_effects",
    ),
    limitation_codes: limitations,
    version: integer(source.version, "team workspace.version", 1),
    created_at: timestamp(source.created_at, "team workspace.created_at"),
    updated_at: timestamp(source.updated_at, "team workspace.updated_at"),
  };
}

export function parseTeamWorkspaceReadEvidence(
  value: unknown,
): TeamWorkspaceReadEvidence {
  const source = record(value, "team workspace evidence");
  exactKeys(source, ["workspace", "audit_event_id"], "team workspace evidence");
  return {
    workspace: parseProjection(source.workspace),
    audit_event_id: uuid(
      source.audit_event_id,
      "team workspace evidence.audit_event_id",
    ),
  };
}
