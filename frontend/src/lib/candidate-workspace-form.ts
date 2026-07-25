import type {
  CandidateEvidence,
  CandidateEvidenceClassification,
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
