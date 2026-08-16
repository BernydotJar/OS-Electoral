import type {
  CampaignMilestone,
  CampaignOperationsBlocker,
  CampaignOperationsDecision,
  CampaignOperationsFollowUp,
  CampaignOperationsLearningNote,
  CampaignOperationsTask,
  CampaignOperationsWorkstream,
  CampaignPhase,
  CampaignRoadmapCreateInput,
  WarRoomSnapshotCreateInput,
} from "@/lib/contracts";
import { validIdempotencyKey } from "@/lib/guided-intake-form";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export type OperationsSection =
  | "phases"
  | "workstreams"
  | "milestones"
  | "tasks"
  | "blockers"
  | "decisions"
  | "follow_up_items"
  | "learning_notes";

const SECTIONS = new Set<OperationsSection>([
  "phases",
  "workstreams",
  "milestones",
  "tasks",
  "blockers",
  "decisions",
  "follow_up_items",
  "learning_notes",
]);
const PHASE_STATUSES = new Set<CampaignPhase["status"]>([
  "PLANNED",
  "ACTIVE",
  "COMPLETE",
]);
const WORKSTREAM_STATUSES = new Set<CampaignOperationsWorkstream["status"]>([
  "PLANNED",
  "ACTIVE",
  "PAUSED",
  "COMPLETE",
]);
const MILESTONE_STATUSES = new Set<CampaignMilestone["status"]>([
  "PLANNED",
  "IN_PROGRESS",
  "COMPLETE",
]);
const TASK_STATUSES = new Set<CampaignOperationsTask["execution_status"]>([
  "PLANNED",
  "IN_PROGRESS",
  "COMPLETE",
]);
const BLOCKER_SEVERITIES = new Set<CampaignOperationsBlocker["severity"]>([
  "CRITICAL",
  "HIGH",
  "MEDIUM",
  "LOW",
]);
const BLOCKER_STATUSES = new Set<CampaignOperationsBlocker["status"]>([
  "OPEN",
  "RESOLVED",
]);
const DECISION_STATUSES = new Set<CampaignOperationsDecision["status"]>([
  "REQUIRED",
  "DECIDED",
  "DEFERRED",
]);
const FOLLOW_UP_STATUSES = new Set<CampaignOperationsFollowUp["status"]>([
  "OPEN",
  "COMPLETE",
]);

export class OperationsWorkspaceFormError extends Error {}

function field(form: FormData, name: string): string {
  const value = form.get(name);
  if (typeof value !== "string") {
    throw new OperationsWorkspaceFormError(`${name} is required`);
  }
  return value;
}

function locale(form: FormData): "es" | "en" {
  const value = field(form, "locale");
  if (value !== "es" && value !== "en") {
    throw new OperationsWorkspaceFormError("Locale is invalid");
  }
  return value;
}

function normalized(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function requiredText(form: FormData, name: string, maximum: number): string {
  const value = normalized(field(form, name));
  if (!value || value.length > maximum) {
    throw new OperationsWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function optionalText(form: FormData, name: string, maximum: number): string | null {
  const value = normalized(field(form, name));
  if (!value) return null;
  if (value.length > maximum) {
    throw new OperationsWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function idempotencyKey(form: FormData): string {
  const value = field(form, "idempotency_key").trim();
  if (!validIdempotencyKey(value)) {
    throw new OperationsWorkspaceFormError("Idempotency key is invalid");
  }
  return value;
}

function expectedVersion(form: FormData): number {
  const value = Number(field(form, "version"));
  if (!Number.isInteger(value) || value < 1) {
    throw new OperationsWorkspaceFormError("Version is invalid");
  }
  return value;
}

function requiredUuid(form: FormData, name: string): string {
  const value = field(form, name).trim();
  if (!UUID_PATTERN.test(value)) {
    throw new OperationsWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function optionalUuid(form: FormData, name: string): string | null {
  const value = field(form, name).trim();
  if (!value) return null;
  if (!UUID_PATTERN.test(value)) {
    throw new OperationsWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function recordId(form: FormData): string | null {
  const value = field(form, "record_id").trim();
  if (!value) return null;
  if (!UUID_PATTERN.test(value)) {
    throw new OperationsWorkspaceFormError("record_id is invalid");
  }
  return value;
}

function integerField(form: FormData, name: string, minimum: number, maximum: number): number {
  const value = Number(field(form, name));
  if (!Number.isInteger(value) || value < minimum || value > maximum) {
    throw new OperationsWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function enumField<T extends string>(
  form: FormData,
  name: string,
  values: ReadonlySet<T>,
): T {
  const value = field(form, name) as T;
  if (!values.has(value)) {
    throw new OperationsWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function isoDate(form: FormData, name: string): string {
  const value = field(form, name).trim();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    throw new OperationsWorkspaceFormError(`${name} is invalid`);
  }
  const parsed = new Date(`${value}T00:00:00.000Z`);
  if (!Number.isFinite(parsed.valueOf()) || parsed.toISOString().slice(0, 10) !== value) {
    throw new OperationsWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function refs(form: FormData, name: string, maximum: number): readonly string[] {
  const values = form.getAll(name).map((value) => {
    if (typeof value !== "string" || !UUID_PATTERN.test(value)) {
      throw new OperationsWorkspaceFormError(`${name} contains an invalid reference`);
    }
    return value;
  });
  if (values.length > maximum || new Set(values).size !== values.length) {
    throw new OperationsWorkspaceFormError(`${name} is invalid`);
  }
  return values;
}

function lines(
  form: FormData,
  name: string,
  maximumItems: number,
  maximumLength: number,
  minimumItems = 0,
): readonly string[] {
  const values = field(form, name)
    .split(/\r?\n/)
    .map(normalized)
    .filter(Boolean);
  if (
    values.length < minimumItems ||
    values.length > maximumItems ||
    values.some((value) => value.length > maximumLength) ||
    new Set(values).size !== values.length
  ) {
    throw new OperationsWorkspaceFormError(`${name} is invalid`);
  }
  return values;
}

export type ParsedOperationsStartForm = Readonly<{
  locale: "es" | "en";
  idempotencyKey: string;
  create: CampaignRoadmapCreateInput;
}>;

export function parseOperationsStartForm(form: FormData): ParsedOperationsStartForm {
  return {
    locale: locale(form),
    idempotencyKey: idempotencyKey(form),
    create: { title: requiredText(form, "title", 255) },
  };
}

type RecordMutation<T> = Readonly<{
  recordId: string | null;
  record: Omit<T, "id">;
}>;

export type OperationsSectionMutation =
  | (Readonly<{ kind: "phase"; section: "phases" }> & RecordMutation<CampaignPhase>)
  | (Readonly<{ kind: "workstream"; section: "workstreams" }> &
      RecordMutation<CampaignOperationsWorkstream>)
  | (Readonly<{ kind: "milestone"; section: "milestones" }> &
      RecordMutation<CampaignMilestone>)
  | (Readonly<{ kind: "task"; section: "tasks" }> &
      RecordMutation<CampaignOperationsTask>)
  | (Readonly<{ kind: "blocker"; section: "blockers" }> &
      RecordMutation<CampaignOperationsBlocker>)
  | (Readonly<{ kind: "decision"; section: "decisions" }> &
      RecordMutation<CampaignOperationsDecision>)
  | (Readonly<{ kind: "follow_up"; section: "follow_up_items" }> &
      RecordMutation<CampaignOperationsFollowUp>)
  | (Readonly<{ kind: "learning"; section: "learning_notes" }> &
      RecordMutation<CampaignOperationsLearningNote>);

export type ParsedOperationsSectionForm = Readonly<{
  locale: "es" | "en";
  expectedVersion: number;
  idempotencyKey: string;
  mutation: OperationsSectionMutation;
}>;

export function parseOperationsSectionForm(form: FormData): ParsedOperationsSectionForm {
  const section = field(form, "section") as OperationsSection;
  if (!SECTIONS.has(section)) {
    throw new OperationsWorkspaceFormError("Operations section is invalid");
  }
  const base = {
    locale: locale(form),
    expectedVersion: expectedVersion(form),
    idempotencyKey: idempotencyKey(form),
  };
  const currentId = recordId(form);

  if (section === "phases") {
    const startDate = isoDate(form, "start_date");
    const endDate = isoDate(form, "end_date");
    if (endDate < startDate) {
      throw new OperationsWorkspaceFormError("phase date window is invalid");
    }
    return {
      ...base,
      mutation: {
        kind: "phase",
        section,
        recordId: currentId,
        record: {
          name: requiredText(form, "name", 255),
          sequence: integerField(form, "sequence", 1, 1000),
          start_date: startDate,
          end_date: endDate,
          status: enumField(form, "status", PHASE_STATUSES),
        },
      },
    };
  }

  if (section === "workstreams") {
    return {
      ...base,
      mutation: {
        kind: "workstream",
        section,
        recordId: currentId,
        record: {
          name: requiredText(form, "name", 255),
          purpose: requiredText(form, "purpose", 2000),
          accountable_role_id: requiredUuid(form, "accountable_role_id"),
          status: enumField(form, "status", WORKSTREAM_STATUSES),
        },
      },
    };
  }

  if (section === "milestones") {
    return {
      ...base,
      mutation: {
        kind: "milestone",
        section,
        recordId: currentId,
        record: {
          phase_id: requiredUuid(form, "phase_id"),
          name: requiredText(form, "name", 255),
          completion_criteria: requiredText(form, "completion_criteria", 2000),
          owner_role_id: requiredUuid(form, "owner_role_id"),
          due_date: isoDate(form, "due_date"),
          status: enumField(form, "status", MILESTONE_STATUSES),
        },
      },
    };
  }

  if (section === "tasks") {
    return {
      ...base,
      mutation: {
        kind: "task",
        section,
        recordId: currentId,
        record: {
          phase_id: requiredUuid(form, "phase_id"),
          workstream_id: requiredUuid(form, "workstream_id"),
          milestone_id: optionalUuid(form, "milestone_id"),
          title: requiredText(form, "title", 500),
          owner_role_id: requiredUuid(form, "owner_role_id"),
          execution_status: enumField(form, "execution_status", TASK_STATUSES),
          dependency_ids: refs(form, "dependency_ids", 100),
          due_date: isoDate(form, "due_date"),
          evidence_refs: refs(form, "evidence_refs", 100),
        },
      },
    };
  }

  if (section === "blockers") {
    return {
      ...base,
      mutation: {
        kind: "blocker",
        section,
        recordId: currentId,
        record: {
          task_id: optionalUuid(form, "task_id"),
          severity: enumField(form, "severity", BLOCKER_SEVERITIES),
          status: enumField(form, "status", BLOCKER_STATUSES),
          owner_role_id: requiredUuid(form, "owner_role_id"),
          description: requiredText(form, "description", 2000),
          resolution_condition: requiredText(form, "resolution_condition", 2000),
        },
      },
    };
  }

  if (section === "decisions") {
    const options = lines(form, "options", 10, 1000, 2);
    const status = enumField(form, "status", DECISION_STATUSES);
    const decision = optionalText(form, "decision", 1000);
    if (status === "DECIDED") {
      if (decision === null || !options.includes(decision)) {
        throw new OperationsWorkspaceFormError("decided item requires a listed option");
      }
    } else if (decision !== null) {
      throw new OperationsWorkspaceFormError("undecided item cannot select an option");
    }
    return {
      ...base,
      mutation: {
        kind: "decision",
        section,
        recordId: currentId,
        record: {
          title: requiredText(form, "title", 500),
          human_role_id: requiredUuid(form, "human_role_id"),
          options,
          due_date: isoDate(form, "due_date"),
          status,
          decision,
        },
      },
    };
  }

  if (section === "follow_up_items") {
    return {
      ...base,
      mutation: {
        kind: "follow_up",
        section,
        recordId: currentId,
        record: {
          title: requiredText(form, "title", 500),
          owner_role_id: requiredUuid(form, "owner_role_id"),
          due_date: isoDate(form, "due_date"),
          status: enumField(form, "status", FOLLOW_UP_STATUSES),
        },
      },
    };
  }

  return {
    ...base,
    mutation: {
      kind: "learning",
      section: "learning_notes",
      recordId: currentId,
      record: {
        title: requiredText(form, "title", 500),
        note: requiredText(form, "note", 4000),
        evidence_refs: refs(form, "evidence_refs", 100),
      },
    },
  };
}

export type ParsedWarRoomSnapshotForm = Readonly<{
  locale: "es" | "en";
  expectedVersion: number;
  idempotencyKey: string;
  create: WarRoomSnapshotCreateInput;
}>;

export function parseWarRoomSnapshotForm(form: FormData): ParsedWarRoomSnapshotForm {
  return {
    locale: locale(form),
    expectedVersion: expectedVersion(form),
    idempotencyKey: idempotencyKey(form),
    create: {
      snapshot_date: isoDate(form, "snapshot_date"),
      priorities: lines(form, "priorities", 10, 1000, 1),
      follow_up_notes: lines(form, "follow_up_notes", 20, 1000),
    },
  };
}
