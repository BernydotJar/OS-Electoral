import type {
  TeamAccessReviewStatus,
  TeamAvailabilityStatus,
  TeamBlueprintTemplate,
  TeamOrganizationTemplate,
  TeamProgressStatus,
  TeamRoleCard,
  TeamTrainingRequirement,
  TeamWorkItem,
  TeamWorkItemCadence,
  TeamWorkItemHealth,
  TeamWorkItemPriority,
  TeamWorkItemStatus,
  TeamWorkItemType,
  TeamWorkspaceTemplateApplyInput,
  TeamWorkspaceCreateInput,
} from "@/lib/contracts";
import { validIdempotencyKey } from "@/lib/guided-intake-form";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const TEMPLATES = new Set<TeamOrganizationTemplate>([
  "LEAN_CAMPAIGN",
  "FULL_CAMPAIGN",
  "CUSTOM",
]);
const BLUEPRINT_TEMPLATES = new Set<TeamBlueprintTemplate>([
  "LEAN_CAMPAIGN",
  "FULL_CAMPAIGN",
]);
const DIGEST_PATTERN = /^[0-9a-f]{64}$/;
const WORK_ITEM_TYPES = new Set<TeamWorkItemType>([
  "TASK",
  "DELIVERABLE",
  "CHECK_IN",
  "DECISION_PREP",
]);
const WORK_ITEM_PRIORITIES = new Set<TeamWorkItemPriority>([
  "CRITICAL",
  "HIGH",
  "MEDIUM",
  "LOW",
]);
const WORK_ITEM_CADENCES = new Set<TeamWorkItemCadence>([
  "AD_HOC",
  "DAILY",
  "WEEKLY",
  "BIWEEKLY",
  "MONTHLY",
]);
const WORK_ITEM_STATUSES = new Set<TeamWorkItemStatus>([
  "PLANNED",
  "ACTIVE",
  "BLOCKED",
  "COMPLETE",
]);
const WORK_ITEM_HEALTH = new Set<TeamWorkItemHealth>([
  "NOT_REPORTED",
  "ON_TRACK",
  "AT_RISK",
  "OFF_TRACK",
]);
const TRAINING_STATUSES = new Set<TeamProgressStatus>([
  "NOT_STARTED",
  "IN_PROGRESS",
  "COMPLETE",
]);
const ACCESS_REVIEW_STATUSES = new Set<TeamAccessReviewStatus>([
  "PROPOSED",
  "REVIEWED",
  "REJECTED",
]);
const COVERAGE_AVAILABILITY = new Set<TeamAvailabilityStatus>([
  "AVAILABLE",
  "LIMITED",
]);
const READINESS_SECTIONS = new Set([
  "training_requirements",
  "access_recommendations",
] as const);
const READINESS_ACTIONS = new Set(["save", "review_empty"] as const);


export class TeamWorkspaceFormError extends Error {}

function field(form: FormData, name: string): string {
  const value = form.get(name);
  if (typeof value !== "string") {
    throw new TeamWorkspaceFormError(`${name} is required`);
  }
  return value;
}

function locale(form: FormData): "es" | "en" {
  const value = field(form, "locale");
  if (value !== "es" && value !== "en") {
    throw new TeamWorkspaceFormError("Locale is invalid");
  }
  return value;
}

function requiredText(form: FormData, name: string, maximum: number): string {
  const value = field(form, name).trim().replace(/\s+/g, " ");
  if (!value || value.length > maximum) {
    throw new TeamWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function optionalText(
  form: FormData,
  name: string,
  maximum: number,
): string | null {
  const value = field(form, name).trim().replace(/\s+/g, " ");
  if (!value) return null;
  if (value.length > maximum) {
    throw new TeamWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function optionalDate(form: FormData, name: string): string | null {
  const value = field(form, name).trim();
  if (!value) return null;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    throw new TeamWorkspaceFormError(`${name} is invalid`);
  }
  const parsed = new Date(`${value}T00:00:00Z`);
  if (
    !Number.isFinite(parsed.getTime()) ||
    parsed.toISOString().slice(0, 10) !== value
  ) {
    throw new TeamWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function enumField<T extends string>(
  form: FormData,
  name: string,
  allowed: ReadonlySet<T>,
): T {
  const value = field(form, name) as T;
  if (!allowed.has(value)) {
    throw new TeamWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function idempotencyKey(form: FormData): string {
  const value = field(form, "idempotency_key").trim();
  if (!validIdempotencyKey(value)) {
    throw new TeamWorkspaceFormError("Idempotency key is invalid");
  }
  return value;
}

function expectedVersion(form: FormData): number {
  const value = Number(field(form, "version"));
  if (!Number.isInteger(value) || value < 1) {
    throw new TeamWorkspaceFormError("Version is invalid");
  }
  return value;
}

function boundedLines(
  form: FormData,
  name: string,
  maximum: number,
): readonly string[] {
  const values = field(form, name)
    .split(/\r?\n/)
    .map((value) => value.trim().replace(/\s+/g, " "))
    .filter(Boolean);
  if (values.length < 1 || values.length > maximum) {
    throw new TeamWorkspaceFormError(`${name} is invalid`);
  }
  if (values.some((value) => value.length > 500)) {
    throw new TeamWorkspaceFormError(
      `${name} contains an entry that is too long`,
    );
  }
  if (
    new Set(values.map((value) => value.toLocaleLowerCase())).size !==
    values.length
  ) {
    throw new TeamWorkspaceFormError(`${name} contains duplicates`);
  }
  return values;
}

function optionalLines(
  form: FormData,
  name: string,
  maximum: number,
): readonly string[] {
  const raw = field(form, name).trim();
  if (!raw) return [];
  const values = raw
    .split(/\r?\n/)
    .map((value) => value.trim().replace(/\s+/g, " "))
    .filter(Boolean);
  if (values.length > maximum || values.some((value) => value.length > 500)) {
    throw new TeamWorkspaceFormError(`${name} is invalid`);
  }
  if (
    new Set(values.map((value) => value.toLocaleLowerCase())).size !==
    values.length
  ) {
    throw new TeamWorkspaceFormError(`${name} contains duplicates`);
  }
  return values;
}

export type ParsedTeamWorkspaceStartForm = Readonly<{
  locale: "es" | "en";
  idempotencyKey: string;
  create: TeamWorkspaceCreateInput;
}>;

export function parseTeamWorkspaceStartForm(
  form: FormData,
): ParsedTeamWorkspaceStartForm {
  const organizationTemplate = field(
    form,
    "organization_template",
  ) as TeamOrganizationTemplate;
  if (!TEMPLATES.has(organizationTemplate)) {
    throw new TeamWorkspaceFormError("Organization template is invalid");
  }
  const selectedLocale = locale(form);
  return {
    locale: selectedLocale,
    idempotencyKey: idempotencyKey(form),
    create: {
      organization_template: organizationTemplate,
      blueprint_locale: selectedLocale,
    },
  };
}

export type ParsedTeamRoleCoverageForm = Readonly<{
  locale: "es" | "en";
  expectedVersion: number;
  idempotencyKey: string;
  roleId: string;
  availabilityStatus: "AVAILABLE" | "LIMITED";
  weeklyCapacityHours: number;
}>;

export function parseTeamRoleCoverageForm(
  form: FormData,
): ParsedTeamRoleCoverageForm {
  const roleId = field(form, "role_id").trim();
  if (!UUID_PATTERN.test(roleId)) {
    throw new TeamWorkspaceFormError("role_id is invalid");
  }
  const weeklyCapacityHours = Number(field(form, "weekly_capacity_hours"));
  if (
    !Number.isInteger(weeklyCapacityHours) ||
    weeklyCapacityHours < 1 ||
    weeklyCapacityHours > 168
  ) {
    throw new TeamWorkspaceFormError("weekly_capacity_hours is invalid");
  }
  if (field(form, "onboarding_confirmed") !== "confirmed") {
    throw new TeamWorkspaceFormError("onboarding confirmation is required");
  }
  return {
    locale: locale(form),
    expectedVersion: expectedVersion(form),
    idempotencyKey: idempotencyKey(form),
    roleId,
    availabilityStatus: enumField(
      form,
      "availability_status",
      COVERAGE_AVAILABILITY,
    ) as "AVAILABLE" | "LIMITED",
    weeklyCapacityHours,
  };
}

export type ParsedTeamRoleForm = Readonly<{
  locale: "es" | "en";
  expectedVersion: number;
  idempotencyKey: string;
  role: TeamRoleCard;
}>;

export function parseTeamRoleForm(
  form: FormData,
  roleId: string,
): ParsedTeamRoleForm {
  if (!UUID_PATTERN.test(roleId)) {
    throw new TeamWorkspaceFormError("Role ID is invalid");
  }
  return {
    locale: locale(form),
    expectedVersion: expectedVersion(form),
    idempotencyKey: idempotencyKey(form),
    role: {
      id: roleId,
      title: requiredText(form, "title", 160),
      area: requiredText(form, "area", 160),
      purpose: requiredText(form, "purpose", 1000),
      responsibilities: boundedLines(form, "responsibilities", 20),
      decision_scope: boundedLines(form, "decision_scope", 12),
      deliverables: boundedLines(form, "deliverables", 12),
      collaboration_points: boundedLines(form, "collaboration_points", 12),
      success_signals: boundedLines(form, "success_signals", 12),
      status: "VACANT",
      principal_id: null,
      availability_status: "UNASSESSED",
      weekly_capacity_hours: null,
      onboarding_status: "NOT_STARTED",
      vacancy_plan: requiredText(form, "vacancy_plan", 1000),
    },
  };
}

export type ParsedTeamWorkItemForm = Readonly<{
  locale: "es" | "en";
  expectedVersion: number;
  idempotencyKey: string;
  workItem: TeamWorkItem;
}>;

export function parseTeamWorkItemForm(form: FormData): ParsedTeamWorkItemForm {
  const workItemId = field(form, "work_item_id").trim();
  if (!UUID_PATTERN.test(workItemId)) {
    throw new TeamWorkspaceFormError("work_item_id is invalid");
  }
  const roleId = field(form, "role_id").trim();
  if (!UUID_PATTERN.test(roleId)) {
    throw new TeamWorkspaceFormError("role_id is invalid");
  }
  return {
    locale: locale(form),
    expectedVersion: expectedVersion(form),
    idempotencyKey: idempotencyKey(form),
    workItem: {
      id: workItemId,
      name: requiredText(form, "name", 255),
      description: requiredText(form, "description", 2000),
      status: "PLANNED",
      work_type: enumField(form, "work_type", WORK_ITEM_TYPES),
      priority: enumField(form, "priority", WORK_ITEM_PRIORITIES),
      health: "NOT_REPORTED",
      target_date: optionalDate(form, "target_date"),
      next_action: requiredText(form, "next_action", 1000),
      blocker: null,
      evidence: optionalLines(form, "evidence", 12),
      cadence: enumField(form, "cadence", WORK_ITEM_CADENCES),
      check_in_note: null,
      last_check_in_at: null,
      assignments: [
        { role_id: roleId, responsibility: "ACCOUNTABLE" },
        { role_id: roleId, responsibility: "RESPONSIBLE" },
      ],
    },
  };
}

export type ParsedTeamWorkItemUpdateForm = Readonly<{
  locale: "es" | "en";
  expectedVersion: number;
  idempotencyKey: string;
  workItemId: string;
  updates: Readonly<{
    status: TeamWorkItemStatus;
    priority: TeamWorkItemPriority;
    health: TeamWorkItemHealth;
    target_date: string | null;
    next_action: string | null;
    blocker: string | null;
    cadence: TeamWorkItemCadence;
    check_in_note: string | null;
  }>;
}>;

export function parseTeamWorkItemUpdateForm(
  form: FormData,
): ParsedTeamWorkItemUpdateForm {
  const workItemId = field(form, "work_item_id").trim();
  if (!UUID_PATTERN.test(workItemId)) {
    throw new TeamWorkspaceFormError("work_item_id is invalid");
  }
  const status = enumField(form, "status", WORK_ITEM_STATUSES);
  const health = enumField(form, "health", WORK_ITEM_HEALTH);
  const nextAction = optionalText(form, "next_action", 1000);
  const blocker = optionalText(form, "blocker", 1000);
  const checkInNote = optionalText(form, "check_in_note", 2000);
  if (checkInNote === null) {
    throw new TeamWorkspaceFormError("check_in_note is required");
  }
  if (status !== "COMPLETE" && nextAction === null) {
    throw new TeamWorkspaceFormError("next_action is required");
  }
  if (status === "BLOCKED") {
    if (blocker === null || (health !== "AT_RISK" && health !== "OFF_TRACK")) {
      throw new TeamWorkspaceFormError(
        "blocked work requires a blocker and risk health",
      );
    }
  } else if (blocker !== null) {
    throw new TeamWorkspaceFormError(
      "non-blocked work cannot retain a blocker",
    );
  }
  if (
    (health === "AT_RISK" || health === "OFF_TRACK") &&
    checkInNote === null
  ) {
    throw new TeamWorkspaceFormError("at-risk work requires a check-in note");
  }
  return {
    locale: locale(form),
    expectedVersion: expectedVersion(form),
    idempotencyKey: idempotencyKey(form),
    workItemId,
    updates: {
      status,
      priority: enumField(form, "priority", WORK_ITEM_PRIORITIES),
      health,
      target_date: optionalDate(form, "target_date"),
      next_action: nextAction,
      blocker,
      cadence: enumField(form, "cadence", WORK_ITEM_CADENCES),
      check_in_note: checkInNote,
    },
  };
}

export type ParsedTeamTemplateApplyForm = Readonly<{
  locale: "es" | "en";
  expectedVersion: number;
  idempotencyKey: string;
  apply: TeamWorkspaceTemplateApplyInput;
}>;

export function parseTeamTemplateApplyForm(
  form: FormData,
): ParsedTeamTemplateApplyForm {
  const organizationTemplate = field(
    form,
    "organization_template",
  ) as TeamBlueprintTemplate;
  if (!BLUEPRINT_TEMPLATES.has(organizationTemplate)) {
    throw new TeamWorkspaceFormError("Blueprint template is invalid");
  }
  const previewDigest = field(form, "preview_digest").trim();
  if (!DIGEST_PATTERN.test(previewDigest)) {
    throw new TeamWorkspaceFormError("Preview digest is invalid");
  }
  const selectedLocale = locale(form);
  return {
    locale: selectedLocale,
    expectedVersion: expectedVersion(form),
    idempotencyKey: idempotencyKey(form),
    apply: {
      organization_template: organizationTemplate,
      blueprint_locale: selectedLocale,
      preview_digest: previewDigest,
    },
  };
}

export type TeamReadinessSection =
  | "training_requirements"
  | "access_recommendations";
export type TeamReadinessAction = "save" | "review_empty";

export type ParsedTeamReadinessForm =
  | Readonly<{
      locale: "es" | "en";
      expectedVersion: number;
      idempotencyKey: string;
      section: TeamReadinessSection;
      action: "review_empty";
    }>
  | Readonly<{
      locale: "es" | "en";
      expectedVersion: number;
      idempotencyKey: string;
      section: "training_requirements";
      action: "save";
      requirement: TeamTrainingRequirement;
    }>
  | Readonly<{
      locale: "es" | "en";
      expectedVersion: number;
      idempotencyKey: string;
      section: "access_recommendations";
      action: "save";
      recommendation: Readonly<{
        id: string;
        role_id: string;
        action: string;
        resource_type: string;
        purpose: string;
        status: TeamAccessReviewStatus;
      }>;
    }>;

function readinessSection(form: FormData): TeamReadinessSection {
  const value = field(form, "section") as TeamReadinessSection;
  if (!READINESS_SECTIONS.has(value)) {
    throw new TeamWorkspaceFormError("Readiness section is invalid");
  }
  return value;
}

function readinessAction(form: FormData): TeamReadinessAction {
  const value = field(form, "readiness_action") as TeamReadinessAction;
  if (!READINESS_ACTIONS.has(value)) {
    throw new TeamWorkspaceFormError("Readiness action is invalid");
  }
  return value;
}

function recordId(form: FormData, generatedId: string): string {
  const raw = field(form, "record_id").trim();
  const value = raw || generatedId;
  if (!UUID_PATTERN.test(value)) {
    throw new TeamWorkspaceFormError("record_id is invalid");
  }
  return value;
}

function roleId(form: FormData): string {
  const value = field(form, "role_id").trim();
  if (!UUID_PATTERN.test(value)) {
    throw new TeamWorkspaceFormError("role_id is invalid");
  }
  return value;
}

export function parseTeamReadinessForm(
  form: FormData,
  generatedId: string,
): ParsedTeamReadinessForm {
  if (!UUID_PATTERN.test(generatedId)) {
    throw new TeamWorkspaceFormError("Generated record ID is invalid");
  }
  const selectedLocale = locale(form);
  const version = expectedVersion(form);
  const key = idempotencyKey(form);
  const section = readinessSection(form);
  const action = readinessAction(form);
  if (action === "review_empty") {
    return {
      locale: selectedLocale,
      expectedVersion: version,
      idempotencyKey: key,
      section,
      action,
    };
  }
  const id = recordId(form, generatedId);
  const selectedRoleId = roleId(form);
  if (section === "training_requirements") {
    return {
      locale: selectedLocale,
      expectedVersion: version,
      idempotencyKey: key,
      section,
      action,
      requirement: {
        id,
        role_id: selectedRoleId,
        title: requiredText(form, "title", 255),
        description: requiredText(form, "description", 2000),
        status: enumField(form, "status", TRAINING_STATUSES),
      },
    };
  }
  return {
    locale: selectedLocale,
    expectedVersion: version,
    idempotencyKey: key,
    section,
    action,
    recommendation: {
      id,
      role_id: selectedRoleId,
      action: requiredText(form, "access_action", 100),
      resource_type: requiredText(form, "resource_type", 100),
      purpose: requiredText(form, "purpose", 500),
      status: enumField(form, "status", ACCESS_REVIEW_STATUSES),
    },
  };
}
