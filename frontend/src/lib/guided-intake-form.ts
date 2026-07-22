import type {
  GuidedIntakeBudgetStatus,
  GuidedIntakeUpdateInput,
} from "@/lib/contracts";

const IDEMPOTENCY_PATTERN = /^[A-Za-z0-9._:-]{8,128}$/;
const BUDGET_STATUSES = new Set<GuidedIntakeBudgetStatus>([
  "NOT_ASSESSED",
  "NO_DOCUMENT",
  "ROUGH_RANGE",
  "DOCUMENTED",
]);

export class GuidedIntakeFormError extends Error {}

function field(form: FormData, name: string): string {
  const value = form.get(name);
  if (typeof value !== "string") {
    throw new GuidedIntakeFormError(`${name} is required`);
  }
  return value;
}

function optionalText(value: string, maximum: number): string | null {
  const normalized = value.trim().replace(/\s+/g, " ");
  if (!normalized) return null;
  if (normalized.length > maximum) {
    throw new GuidedIntakeFormError("Text field exceeds the allowed size");
  }
  return normalized;
}

function lineItems(value: string): readonly string[] {
  const items = value
    .split(/\r?\n/)
    .map((item) => item.trim().replace(/\s+/g, " "))
    .filter(Boolean);
  if (items.length > 30 || items.some((item) => item.length > 255)) {
    throw new GuidedIntakeFormError("List field exceeds the allowed size");
  }
  const folded = items.map((item) => item.toLocaleLowerCase("es"));
  if (new Set(folded).size !== folded.length) {
    throw new GuidedIntakeFormError("List field contains duplicates");
  }
  return items;
}

export type ParsedGuidedIntakeForm = Readonly<{
  locale: "es" | "en";
  expectedVersion: number;
  idempotencyKey: string;
  update: GuidedIntakeUpdateInput;
}>;

export function parseGuidedIntakeForm(
  form: FormData,
): ParsedGuidedIntakeForm {
  const localeValue = field(form, "locale");
  if (localeValue !== "es" && localeValue !== "en") {
    throw new GuidedIntakeFormError("Locale is invalid");
  }
  const expectedVersion = Number(field(form, "version"));
  if (!Number.isInteger(expectedVersion) || expectedVersion < 1) {
    throw new GuidedIntakeFormError("Version is invalid");
  }
  const idempotencyKey = field(form, "idempotency_key").trim();
  if (!IDEMPOTENCY_PATTERN.test(idempotencyKey)) {
    throw new GuidedIntakeFormError("Idempotency key is invalid");
  }
  const budgetStatus = field(form, "budget_status") as GuidedIntakeBudgetStatus;
  if (!BUDGET_STATUSES.has(budgetStatus)) {
    throw new GuidedIntakeFormError("Budget status is invalid");
  }
  return {
    locale: localeValue,
    expectedVersion,
    idempotencyKey,
    update: {
      office: optionalText(field(form, "office"), 255),
      candidate_project: optionalText(field(form, "candidate_project"), 2000),
      current_team: lineItems(field(form, "current_team")),
      current_assets: lineItems(field(form, "current_assets")),
      budget_status: budgetStatus,
      known_unknowns: lineItems(field(form, "known_unknowns")),
      evidence_requirements: lineItems(
        field(form, "evidence_requirements"),
      ),
    },
  };
}

export function validIdempotencyKey(value: unknown): value is string {
  return typeof value === "string" && IDEMPOTENCY_PATTERN.test(value);
}
