import type {
  StrategyAssumptionRecord,
  StrategyContradictionRecord,
  StrategyDecisionInput,
  StrategyEvidenceClassification,
  StrategyEvidenceRecord,
  StrategyHypothesisRecord,
  StrategyObjectiveRecord,
  StrategyOptionRecord,
  StrategyRedTeamFindingRecord,
  StrategyWorkspaceCreateInput,
} from "@/lib/contracts";
import { validIdempotencyKey } from "@/lib/guided-intake-form";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export type StrategySection =
  | "evidence"
  | "assumptions"
  | "hypotheses"
  | "options"
  | "objectives"
  | "contradictions"
  | "red_team_findings";

const SECTIONS = new Set<StrategySection>([
  "evidence",
  "assumptions",
  "hypotheses",
  "options",
  "objectives",
  "contradictions",
  "red_team_findings",
]);
const CLASSIFICATIONS = new Set<StrategyEvidenceClassification>([
  "VERIFIED",
  "INFERRED",
  "UNKNOWN",
]);
const ASSUMPTION_STATUSES = new Set<StrategyAssumptionRecord["status"]>([
  "ACTIVE",
  "INVALIDATED",
]);
const HYPOTHESIS_STATUSES = new Set<StrategyHypothesisRecord["status"]>([
  "DRAFT",
  "IN_REVIEW",
  "REJECTED",
]);
const CONTRADICTION_STATUSES = new Set<StrategyContradictionRecord["status"]>([
  "OPEN",
  "RESOLVED",
]);
const FINDING_SEVERITIES = new Set<StrategyRedTeamFindingRecord["severity"]>([
  "CRITICAL",
  "HIGH",
  "MEDIUM",
  "LOW",
]);
const FINDING_STATUSES = new Set<StrategyRedTeamFindingRecord["status"]>([
  "OPEN",
  "RESOLVED",
]);

export class StrategyWorkspaceFormError extends Error {}

function field(form: FormData, name: string): string {
  const value = form.get(name);
  if (typeof value !== "string") {
    throw new StrategyWorkspaceFormError(`${name} is required`);
  }
  return value;
}

function locale(form: FormData): "es" | "en" {
  const value = field(form, "locale");
  if (value !== "es" && value !== "en") {
    throw new StrategyWorkspaceFormError("Locale is invalid");
  }
  return value;
}

function idempotencyKey(form: FormData): string {
  const value = field(form, "idempotency_key").trim();
  if (!validIdempotencyKey(value)) {
    throw new StrategyWorkspaceFormError("Idempotency key is invalid");
  }
  return value;
}

function expectedVersion(form: FormData): number {
  const value = Number(field(form, "version"));
  if (!Number.isInteger(value) || value < 1) {
    throw new StrategyWorkspaceFormError("Version is invalid");
  }
  return value;
}

function normalized(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function requiredText(form: FormData, name: string, maximum: number): string {
  const value = normalized(field(form, name));
  if (!value || value.length > maximum) {
    throw new StrategyWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function optionalText(form: FormData, name: string, maximum: number): string | null {
  const value = normalized(field(form, name));
  if (!value) return null;
  if (value.length > maximum) {
    throw new StrategyWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function requiredUuid(form: FormData, name: string): string {
  const value = field(form, name).trim();
  if (!UUID_PATTERN.test(value)) {
    throw new StrategyWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function recordId(form: FormData): string | null {
  const value = field(form, "record_id").trim();
  if (!value) return null;
  if (!UUID_PATTERN.test(value)) {
    throw new StrategyWorkspaceFormError("record_id is invalid");
  }
  return value;
}

function refs(
  form: FormData,
  name: string,
  maximum: number,
  required: boolean,
): readonly string[] {
  const values = form.getAll(name).map((value) => {
    if (typeof value !== "string" || !UUID_PATTERN.test(value)) {
      throw new StrategyWorkspaceFormError(`${name} contains an invalid reference`);
    }
    return value;
  });
  if (
    values.length > maximum ||
    (required && values.length === 0) ||
    new Set(values).size !== values.length
  ) {
    throw new StrategyWorkspaceFormError(`${name} is invalid`);
  }
  return values;
}

function lines(
  form: FormData,
  name: string,
  maximumItems: number,
  required: boolean,
): readonly string[] {
  const values = field(form, name)
    .split(/\r?\n/)
    .map(normalized)
    .filter(Boolean);
  if (
    values.length > maximumItems ||
    (required && values.length === 0) ||
    values.some((value) => value.length > 180) ||
    new Set(values).size !== values.length
  ) {
    throw new StrategyWorkspaceFormError(`${name} is invalid`);
  }
  return values;
}

function enumField<T extends string>(
  form: FormData,
  name: string,
  values: ReadonlySet<T>,
): T {
  const value = field(form, name) as T;
  if (!values.has(value)) {
    throw new StrategyWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function isoDate(form: FormData, name: string): string {
  const value = field(form, name).trim();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    throw new StrategyWorkspaceFormError(`${name} is invalid`);
  }
  const parsed = new Date(`${value}T00:00:00.000Z`);
  if (!Number.isFinite(parsed.valueOf())) {
    throw new StrategyWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function collectedAt(form: FormData): string {
  return `${isoDate(form, "collected_at")}T12:00:00.000Z`;
}

export type ParsedStrategyWorkspaceStartForm = Readonly<{
  locale: "es" | "en";
  idempotencyKey: string;
  create: StrategyWorkspaceCreateInput;
}>;

export function parseStrategyWorkspaceStartForm(
  form: FormData,
): ParsedStrategyWorkspaceStartForm {
  return {
    locale: locale(form),
    idempotencyKey: idempotencyKey(form),
    create: { title: requiredText(form, "title", 180) },
  };
}

type RecordMutation<T> = Readonly<{
  recordId: string | null;
  record: Omit<T, "id">;
}>;

export type StrategySectionMutation =
  | (Readonly<{ kind: "evidence"; section: "evidence" }> &
      RecordMutation<StrategyEvidenceRecord>)
  | (Readonly<{ kind: "assumption"; section: "assumptions" }> &
      RecordMutation<StrategyAssumptionRecord>)
  | (Readonly<{ kind: "hypothesis"; section: "hypotheses" }> &
      RecordMutation<StrategyHypothesisRecord>)
  | (Readonly<{ kind: "option"; section: "options" }> &
      RecordMutation<StrategyOptionRecord>)
  | (Readonly<{ kind: "objective"; section: "objectives" }> &
      RecordMutation<StrategyObjectiveRecord>)
  | (Readonly<{ kind: "contradiction"; section: "contradictions" }> &
      RecordMutation<StrategyContradictionRecord>)
  | (Readonly<{ kind: "finding"; section: "red_team_findings" }> &
      RecordMutation<StrategyRedTeamFindingRecord>)
  | Readonly<{
      kind: "review_empty";
      section: "contradictions" | "red_team_findings";
      recordId: null;
    }>;

export type ParsedStrategySectionForm = Readonly<{
  locale: "es" | "en";
  expectedVersion: number;
  idempotencyKey: string;
  mutation: StrategySectionMutation;
}>;

export function parseStrategySectionForm(form: FormData): ParsedStrategySectionForm {
  const section = field(form, "section") as StrategySection;
  if (!SECTIONS.has(section)) {
    throw new StrategyWorkspaceFormError("Strategy section is invalid");
  }
  const mutationAction = field(form, "strategy_action");
  const base = {
    locale: locale(form),
    expectedVersion: expectedVersion(form),
    idempotencyKey: idempotencyKey(form),
  };
  if (mutationAction === "review_empty") {
    if (section !== "contradictions" && section !== "red_team_findings") {
      throw new StrategyWorkspaceFormError("Reviewed-empty state is not allowed for this section");
    }
    return {
      ...base,
      mutation: { kind: "review_empty", section, recordId: null },
    };
  }
  if (mutationAction !== "save") {
    throw new StrategyWorkspaceFormError("Strategy action is invalid");
  }
  const currentId = recordId(form);

  if (section === "evidence") {
    const classification = enumField(form, "classification", CLASSIFICATIONS);
    const sourceReference = optionalText(form, "source_reference", 500);
    const authority = optionalText(form, "authority", 180);
    const jurisdiction = optionalText(form, "jurisdiction", 180);
    if (
      classification === "VERIFIED" &&
      (sourceReference === null || authority === null || jurisdiction === null)
    ) {
      throw new StrategyWorkspaceFormError("Verified evidence requires source, authority and jurisdiction");
    }
    if (classification === "INFERRED" && sourceReference === null) {
      throw new StrategyWorkspaceFormError("Inferred evidence requires a source reference");
    }
    return {
      ...base,
      mutation: {
        kind: "evidence",
        section,
        recordId: currentId,
        record: {
          classification,
          statement: requiredText(form, "statement", 2000),
          source_reference: classification === "UNKNOWN" ? null : sourceReference,
          authority: classification === "UNKNOWN" ? null : authority,
          jurisdiction: classification === "UNKNOWN" ? null : jurisdiction,
          status: classification === "VERIFIED" ? "ACCEPTED" : "NEEDS_REVIEW",
          collected_at: collectedAt(form),
        },
      },
    };
  }

  if (section === "assumptions") {
    return {
      ...base,
      mutation: {
        kind: "assumption",
        section,
        recordId: currentId,
        record: {
          statement: requiredText(form, "statement", 2000),
          evidence_refs: refs(form, "evidence_refs", 80, false),
          invalidation_signals: lines(form, "invalidation_signals", 40, true),
          status: enumField(form, "status", ASSUMPTION_STATUSES),
        },
      },
    };
  }

  if (section === "hypotheses") {
    return {
      ...base,
      mutation: {
        kind: "hypothesis",
        section,
        recordId: currentId,
        record: {
          title: requiredText(form, "title", 180),
          statement: requiredText(form, "statement", 2000),
          evidence_refs: refs(form, "evidence_refs", 80, true),
          assumption_refs: refs(form, "assumption_refs", 80, false),
          invalidation_signals: lines(form, "invalidation_signals", 40, true),
          status: enumField(form, "status", HYPOTHESIS_STATUSES),
        },
      },
    };
  }

  if (section === "options") {
    return {
      ...base,
      mutation: {
        kind: "option",
        section,
        recordId: currentId,
        record: {
          title: requiredText(form, "title", 180),
          summary: requiredText(form, "summary", 2000),
          hypothesis_refs: refs(form, "hypothesis_refs", 80, true),
          evidence_refs: refs(form, "evidence_refs", 80, true),
          benefits: lines(form, "benefits", 40, true),
          risks: lines(form, "risks", 40, true),
          tradeoffs: lines(form, "tradeoffs", 40, true),
        },
      },
    };
  }

  if (section === "objectives") {
    return {
      ...base,
      mutation: {
        kind: "objective",
        section,
        recordId: currentId,
        record: {
          outcome: requiredText(form, "outcome", 2000),
          metric: requiredText(form, "metric", 180),
          baseline: requiredText(form, "baseline", 180),
          target: requiredText(form, "target", 180),
          deadline: isoDate(form, "deadline"),
          owner_role_id: requiredUuid(form, "owner_role_id"),
          evidence_refs: refs(form, "evidence_refs", 80, true),
        },
      },
    };
  }

  if (section === "contradictions") {
    const status = enumField(form, "status", CONTRADICTION_STATUSES);
    const resolution = optionalText(form, "resolution", 2000);
    if ((status === "RESOLVED") !== (resolution !== null)) {
      throw new StrategyWorkspaceFormError("Contradiction resolution is inconsistent");
    }
    return {
      ...base,
      mutation: {
        kind: "contradiction",
        section,
        recordId: currentId,
        record: {
          left_ref: requiredUuid(form, "left_ref"),
          right_ref: requiredUuid(form, "right_ref"),
          description: requiredText(form, "description", 2000),
          evidence_refs: refs(form, "evidence_refs", 80, false),
          status,
          resolution,
        },
      },
    };
  }

  const status = enumField(form, "status", FINDING_STATUSES);
  return {
    ...base,
    mutation: {
      kind: "finding",
      section: "red_team_findings",
      recordId: currentId,
      record: {
        severity: enumField(form, "severity", FINDING_SEVERITIES),
        description: requiredText(form, "description", 2000),
        option_refs: refs(form, "option_refs", 80, true),
        mitigation: requiredText(form, "mitigation", 2000),
        status,
      },
    },
  };
}

export type ParsedStrategyDecisionForm = Readonly<{
  locale: "es" | "en";
  expectedVersion: number;
  idempotencyKey: string;
  decision: StrategyDecisionInput;
}>;

export function parseStrategyDecisionForm(form: FormData): ParsedStrategyDecisionForm {
  return {
    locale: locale(form),
    expectedVersion: expectedVersion(form),
    idempotencyKey: idempotencyKey(form),
    decision: {
      selected_option_id: requiredUuid(form, "selected_option_id"),
      human_role_id: requiredUuid(form, "human_role_id"),
      reason: requiredText(form, "reason", 2000),
    },
  };
}
