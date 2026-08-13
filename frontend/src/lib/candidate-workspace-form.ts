import type {
  CandidateAttribute,
  CandidateClaim,
  CandidateClaimStatus,
  CandidateContradiction,
  CandidateDevelopmentGoal,
  CandidateEvidence,
  CandidateEvidenceClassification,
  CandidateReputationRisk,
  CandidateSection,
  CandidateWorkspaceCreateInput,
} from "@/lib/contracts";
import { validIdempotencyKey } from "@/lib/guided-intake-form";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const CLASSIFICATIONS = new Set<CandidateEvidenceClassification>([
  "OFFICIAL_SOURCE",
  "CAMPAIGN_RESEARCH",
  "PERCEPTION",
  "HYPOTHESIS",
  "UNKNOWN",
]);

export class CandidateWorkspaceFormError extends Error {}

function field(form: FormData, name: string): string {
  const value = form.get(name);
  if (typeof value !== "string") {
    throw new CandidateWorkspaceFormError(`${name} is required`);
  }
  return value;
}

function locale(form: FormData): "es" | "en" {
  const value = field(form, "locale");
  if (value !== "es" && value !== "en") {
    throw new CandidateWorkspaceFormError("Locale is invalid");
  }
  return value;
}

function requiredText(form: FormData, name: string, maximum: number): string {
  const value = field(form, name).trim().replace(/\s+/g, " ");
  if (!value || value.length > maximum) {
    throw new CandidateWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function optionalText(form: FormData, name: string, maximum: number): string | null {
  const value = field(form, name).trim().replace(/\s+/g, " ");
  if (!value) return null;
  if (value.length > maximum) {
    throw new CandidateWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function idempotencyKey(form: FormData): string {
  const value = field(form, "idempotency_key").trim();
  if (!validIdempotencyKey(value)) {
    throw new CandidateWorkspaceFormError("Idempotency key is invalid");
  }
  return value;
}

function expectedVersion(form: FormData): number {
  const value = Number(field(form, "version"));
  if (!Number.isInteger(value) || value < 1) {
    throw new CandidateWorkspaceFormError("Version is invalid");
  }
  return value;
}

function sourceReference(form: FormData): string {
  const value = requiredText(form, "source_reference", 2048);
  let source: URL;
  try {
    source = new URL(value);
  } catch {
    throw new CandidateWorkspaceFormError("Source reference must be a URL");
  }
  if (source.protocol !== "https:") {
    throw new CandidateWorkspaceFormError("Source reference must use HTTPS");
  }
  return source.toString();
}

function observedAt(form: FormData): string | null {
  const value = field(form, "observed_at").trim();
  if (!value) return null;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    throw new CandidateWorkspaceFormError("Observed date is invalid");
  }
  const parsed = new Date(`${value}T00:00:00.000Z`);
  if (!Number.isFinite(parsed.valueOf())) {
    throw new CandidateWorkspaceFormError("Observed date is invalid");
  }
  return parsed.toISOString();
}

export type ParsedCandidateWorkspaceStartForm = Readonly<{
  locale: "es" | "en";
  idempotencyKey: string;
  create: CandidateWorkspaceCreateInput;
}>;

export function parseCandidateWorkspaceStartForm(
  form: FormData,
): ParsedCandidateWorkspaceStartForm {
  return {
    locale: locale(form),
    idempotencyKey: idempotencyKey(form),
    create: { display_name: requiredText(form, "display_name", 255) },
  };
}

export type ParsedCandidateEvidenceForm = Readonly<{
  locale: "es" | "en";
  expectedVersion: number;
  idempotencyKey: string;
  evidence: CandidateEvidence;
}>;

export function parseCandidateEvidenceForm(
  form: FormData,
  evidenceId: string,
): ParsedCandidateEvidenceForm {
  if (!UUID_PATTERN.test(evidenceId)) {
    throw new CandidateWorkspaceFormError("Evidence ID is invalid");
  }
  const classification = field(
    form,
    "classification",
  ) as CandidateEvidenceClassification;
  if (!CLASSIFICATIONS.has(classification)) {
    throw new CandidateWorkspaceFormError("Evidence classification is invalid");
  }
  return {
    locale: locale(form),
    expectedVersion: expectedVersion(form),
    idempotencyKey: idempotencyKey(form),
    evidence: {
      id: evidenceId,
      classification,
      status: "ACCEPTED",
      title: requiredText(form, "title", 255),
      source_reference: sourceReference(form),
      source_authority: optionalText(form, "source_authority", 255),
      jurisdiction: optionalText(form, "jurisdiction", 255),
      excerpt: optionalText(form, "excerpt", 2000),
      observed_at: observedAt(form),
    },
  };
}

const CLAIM_STATUSES = new Set<CandidateClaimStatus>([
  "UNKNOWN",
  "SELF_REPORTED",
  "UNDER_REVIEW",
  "EVIDENCE_PARTIAL",
  "VERIFIED",
  "REJECTED",
  "CONTRADICTED",
]);
const CANDIDATE_SECTIONS = new Set<CandidateSection>([
  "identity",
  "biography",
  "purpose",
  "values",
  "attributes",
  "contradictions",
  "development_goals",
  "reputation",
]);
const SELF_ASSESSMENTS = new Set<CandidateAttribute["candidate_self_assessment"]>([
  "YES",
  "NO",
  "UNKNOWN",
]);
const TEAM_ASSESSMENTS = new Set<CandidateAttribute["team_assessment"]>([
  "YES",
  "PARTIAL",
  "NO",
  "UNKNOWN",
]);
const CITIZEN_EVIDENCE = new Set<CandidateAttribute["citizen_evidence"]>([
  "SUPPORTED",
  "PARTIAL",
  "UNRESOLVED",
  "CONTRADICTED",
]);
const CONTRADICTION_STATUSES = new Set<CandidateContradiction["status"]>([
  "OPEN",
  "UNDER_REVIEW",
  "RESOLVED",
]);
const DEVELOPMENT_STATUSES = new Set<CandidateDevelopmentGoal["status"]>([
  "OPEN",
  "IN_PROGRESS",
  "COMPLETE",
]);
const RISK_SEVERITIES = new Set<CandidateReputationRisk["severity"]>([
  "CRITICAL",
  "HIGH",
  "MEDIUM",
  "LOW",
]);
const RISK_STATUSES = new Set<CandidateReputationRisk["status"]>([
  "OPEN",
  "MITIGATING",
  "RESOLVED",
  "CLOSED",
]);

function enumField<T extends string>(
  form: FormData,
  name: string,
  allowed: ReadonlySet<T>,
): T {
  const value = field(form, name) as T;
  if (!allowed.has(value)) {
    throw new CandidateWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function recordId(form: FormData): string | null {
  const value = field(form, "record_id").trim();
  if (!value) return null;
  if (!UUID_PATTERN.test(value)) {
    throw new CandidateWorkspaceFormError("record_id is invalid");
  }
  return value;
}

function requiredUuid(form: FormData, name: string): string {
  const value = field(form, name).trim();
  if (!UUID_PATTERN.test(value)) {
    throw new CandidateWorkspaceFormError(`${name} is invalid`);
  }
  return value;
}

function refs(form: FormData, name: string): readonly string[] {
  const values = form.getAll(name).map((value) => {
    if (typeof value !== "string" || !UUID_PATTERN.test(value)) {
      throw new CandidateWorkspaceFormError(`${name} contains an invalid reference`);
    }
    return value;
  });
  if (values.length > 20 || new Set(values).size !== values.length) {
    throw new CandidateWorkspaceFormError(`${name} is invalid`);
  }
  return values;
}

function checked(form: FormData, name: string): boolean {
  const value = form.get(name);
  if (value === null) return false;
  if (value !== "true") {
    throw new CandidateWorkspaceFormError(`${name} is invalid`);
  }
  return true;
}

export type CandidateSectionMutation =
  | Readonly<{
      kind: "claim";
      section: "identity" | "biography" | "purpose" | "values";
      recordId: string | null;
      record: Omit<CandidateClaim, "id">;
    }>
  | Readonly<{
      kind: "attribute";
      section: "attributes";
      recordId: string | null;
      record: Omit<CandidateAttribute, "id">;
    }>
  | Readonly<{
      kind: "contradiction";
      section: "contradictions";
      recordId: string | null;
      record: Omit<CandidateContradiction, "id">;
    }>
  | Readonly<{
      kind: "development_goal";
      section: "development_goals";
      recordId: string | null;
      record: Omit<CandidateDevelopmentGoal, "id">;
    }>
  | Readonly<{
      kind: "reputation_risk";
      section: "reputation";
      recordId: string | null;
      record: Omit<CandidateReputationRisk, "id">;
    }>
  | Readonly<{
      kind: "review_empty";
      section: "contradictions" | "reputation";
      recordId: null;
    }>;

export type ParsedCandidateSectionForm = Readonly<{
  locale: "es" | "en";
  expectedVersion: number;
  idempotencyKey: string;
  mutation: CandidateSectionMutation;
}>;

export function parseCandidateSectionForm(
  form: FormData,
): ParsedCandidateSectionForm {
  const selectedSection = enumField(form, "section", CANDIDATE_SECTIONS);
  const action = field(form, "section_action");
  const common = {
    locale: locale(form),
    expectedVersion: expectedVersion(form),
    idempotencyKey: idempotencyKey(form),
  } as const;
  if (action === "review_empty") {
    if (selectedSection !== "contradictions" && selectedSection !== "reputation") {
      throw new CandidateWorkspaceFormError("review_empty is invalid for this section");
    }
    return {
      ...common,
      mutation: { kind: "review_empty", section: selectedSection, recordId: null },
    };
  }
  if (action !== "save") {
    throw new CandidateWorkspaceFormError("section_action is invalid");
  }

  const existingId = recordId(form);
  if (
    selectedSection === "identity" ||
    selectedSection === "biography" ||
    selectedSection === "purpose" ||
    selectedSection === "values"
  ) {
    const classification = enumField(form, "classification", CLASSIFICATIONS);
    const status = enumField(form, "status", CLAIM_STATUSES);
    return {
      ...common,
      mutation: {
        kind: "claim",
        section: selectedSection,
        recordId: existingId,
        record: {
          label: requiredText(form, "label", 120),
          claim: requiredText(form, "claim", 2000),
          status,
          classification,
          evidence_refs: refs(form, "evidence_refs"),
        },
      },
    };
  }
  if (selectedSection === "attributes") {
    return {
      ...common,
      mutation: {
        kind: "attribute",
        section: selectedSection,
        recordId: existingId,
        record: {
          name: requiredText(form, "name", 160),
          claim: requiredText(form, "claim", 2000),
          status: enumField(form, "status", CLAIM_STATUSES),
          candidate_self_assessment: enumField(
            form,
            "candidate_self_assessment",
            SELF_ASSESSMENTS,
          ),
          team_assessment: enumField(form, "team_assessment", TEAM_ASSESSMENTS),
          citizen_evidence: enumField(form, "citizen_evidence", CITIZEN_EVIDENCE),
          evidence_refs: refs(form, "evidence_refs"),
          perception_refs: refs(form, "perception_refs"),
          contradiction_refs: refs(form, "contradiction_refs"),
          risk: requiredText(form, "risk", 1000),
        },
      },
    };
  }
  if (selectedSection === "contradictions") {
    return {
      ...common,
      mutation: {
        kind: "contradiction",
        section: selectedSection,
        recordId: existingId,
        record: {
          subject_ref: requiredUuid(form, "subject_ref"),
          description: requiredText(form, "description", 2000),
          status: enumField(form, "status", CONTRADICTION_STATUSES),
          evidence_refs: refs(form, "evidence_refs"),
        },
      },
    };
  }
  if (selectedSection === "development_goals") {
    return {
      ...common,
      mutation: {
        kind: "development_goal",
        section: selectedSection,
        recordId: existingId,
        record: {
          area: requiredText(form, "area", 160),
          objective: requiredText(form, "objective", 2000),
          status: enumField(form, "status", DEVELOPMENT_STATUSES),
          evidence_refs: refs(form, "evidence_refs"),
        },
      },
    };
  }
  return {
    ...common,
    mutation: {
      kind: "reputation_risk",
      section: "reputation",
      recordId: existingId,
      record: {
        title: requiredText(form, "title", 255),
        description: requiredText(form, "description", 2000),
        severity: enumField(form, "severity", RISK_SEVERITIES),
        status: enumField(form, "status", RISK_STATUSES),
        decision_required: checked(form, "decision_required"),
        evidence_refs: refs(form, "evidence_refs"),
      },
    },
  };
}

export type ParsedCandidateApprovalForm = Readonly<{
  locale: "es" | "en";
  expectedVersion: number;
  idempotencyKey: string;
  section: CandidateSection;
  reason: string;
}>;

export function parseCandidateApprovalForm(
  form: FormData,
): ParsedCandidateApprovalForm {
  return {
    locale: locale(form),
    expectedVersion: expectedVersion(form),
    idempotencyKey: idempotencyKey(form),
    section: enumField(form, "section", CANDIDATE_SECTIONS),
    reason: requiredText(form, "reason", 1000),
  };
}
