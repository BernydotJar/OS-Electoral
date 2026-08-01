import type {
  TrainingAnswerSubmissionInput,
  TrainingAssignmentCreateInput,
  TrainingAttemptInput,
  TrainingLocale,
  TrainingModuleStartInput,
  UUID,
} from "@/lib/contracts";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const DIGEST_PATTERN = /^[0-9a-f]{64}$/;
const IDENTIFIER_PATTERN = /^[a-z][a-z0-9_]{2,79}$/;
const VERSION_PATTERN = /^[1-9][0-9]{0,3}\.[0-9]{1,4}\.[0-9]{1,4}$/;

export class TrainingFormError extends Error {}

function single(formData: FormData, key: string): string {
  const values = formData.getAll(key);
  if (values.length !== 1 || typeof values[0] !== "string") {
    throw new TrainingFormError(`${key} must appear exactly once`);
  }
  const value = values[0].trim();
  if (!value) throw new TrainingFormError(`${key} must not be empty`);
  return value;
}

function optional(formData: FormData, key: string): string | null {
  const values = formData.getAll(key);
  if (
    values.length > 1 ||
    (values.length === 1 && typeof values[0] !== "string")
  ) {
    throw new TrainingFormError(`${key} must appear at most once`);
  }
  if (values.length === 0) return null;
  const value = (values[0] as string).trim();
  return value || null;
}

function locale(formData: FormData): TrainingLocale {
  const value = single(formData, "locale");
  if (value !== "es" && value !== "en") {
    throw new TrainingFormError("locale must be es or en");
  }
  return value;
}

function identifier(formData: FormData, key: string): string {
  const value = single(formData, key);
  if (!IDENTIFIER_PATTERN.test(value)) {
    throw new TrainingFormError(`${key} is invalid`);
  }
  return value;
}

function version(formData: FormData, key: string): string {
  const value = single(formData, key);
  if (!VERSION_PATTERN.test(value)) {
    throw new TrainingFormError(`${key} is invalid`);
  }
  return value;
}

function uuid(formData: FormData, key: string): UUID {
  const value = single(formData, key);
  if (!UUID_PATTERN.test(value)) {
    throw new TrainingFormError(`${key} is not a UUID`);
  }
  return value;
}

function digest(formData: FormData): string {
  const value = single(formData, "catalog_digest");
  if (!DIGEST_PATTERN.test(value)) {
    throw new TrainingFormError("catalog_digest is invalid");
  }
  return value;
}

function positiveInteger(formData: FormData, key: string): number {
  const value = single(formData, key);
  if (!/^[1-9][0-9]*$/.test(value)) {
    throw new TrainingFormError(`${key} must be a positive integer`);
  }
  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed)) {
    throw new TrainingFormError(`${key} is out of range`);
  }
  return parsed;
}

function exactKeys(formData: FormData, allowed: ReadonlySet<string>): void {
  for (const key of formData.keys()) {
    if (!allowed.has(key)) {
      throw new TrainingFormError(`unexpected training field ${key}`);
    }
  }
}

export function parseTrainingAssignForm(formData: FormData): Readonly<{
  locale: TrainingLocale;
  input: TrainingAssignmentCreateInput;
}> {
  exactKeys(
    formData,
    new Set([
      "locale",
      "path_id",
      "path_version",
      "catalog_digest",
      "role_slug",
    ]),
  );
  const role = optional(formData, "role_slug");
  if (role !== null && !IDENTIFIER_PATTERN.test(role)) {
    throw new TrainingFormError("role_slug is invalid");
  }
  return {
    locale: locale(formData),
    input: {
      principal_id: "00000000-0000-4000-8000-000000000000",
      path_id: identifier(formData, "path_id"),
      path_version: version(formData, "path_version"),
      catalog_digest: digest(formData),
      role_slug: role,
    },
  };
}

export function parseTrainingStartForm(formData: FormData): Readonly<{
  locale: TrainingLocale;
  assignmentId: UUID;
  moduleId: string;
  input: TrainingModuleStartInput;
}> {
  exactKeys(
    formData,
    new Set([
      "locale",
      "assignment_id",
      "module_id",
      "expected_assignment_version",
      "expected_progress_version",
      "catalog_digest",
    ]),
  );
  return {
    locale: locale(formData),
    assignmentId: uuid(formData, "assignment_id"),
    moduleId: identifier(formData, "module_id"),
    input: {
      expected_assignment_version: positiveInteger(
        formData,
        "expected_assignment_version",
      ),
      expected_progress_version: positiveInteger(
        formData,
        "expected_progress_version",
      ),
      catalog_digest: digest(formData),
    },
  };
}

export function parseTrainingAttemptForm(formData: FormData): Readonly<{
  locale: TrainingLocale;
  assignmentId: UUID;
  moduleId: string;
  input: TrainingAttemptInput;
}> {
  const baseKeys = new Set([
    "locale",
    "assignment_id",
    "module_id",
    "expected_assignment_version",
    "expected_progress_version",
    "catalog_digest",
  ]);
  const answerKeys = [...formData.keys()].filter((key) =>
    key.startsWith("answer:"),
  );
  exactKeys(formData, new Set([...baseKeys, ...answerKeys]));
  if (answerKeys.length === 0 || answerKeys.length > 20) {
    throw new TrainingFormError("assessment answers are out of bounds");
  }
  const uniqueQuestions = new Set<string>();
  const answers: TrainingAnswerSubmissionInput[] = [];
  for (const key of answerKeys) {
    const questionId = key.slice("answer:".length);
    if (
      !IDENTIFIER_PATTERN.test(questionId) ||
      uniqueQuestions.has(questionId)
    ) {
      throw new TrainingFormError(
        "assessment question id is invalid or repeated",
      );
    }
    uniqueQuestions.add(questionId);
    const values = formData
      .getAll(key)
      .map((value) => (typeof value === "string" ? value.trim() : ""));
    if (
      values.length === 0 ||
      values.length > 6 ||
      values.some((value) => !IDENTIFIER_PATTERN.test(value)) ||
      new Set(values).size !== values.length
    ) {
      throw new TrainingFormError("assessment option ids are invalid");
    }
    answers.push({ question_id: questionId, option_ids: values });
  }
  return {
    locale: locale(formData),
    assignmentId: uuid(formData, "assignment_id"),
    moduleId: identifier(formData, "module_id"),
    input: {
      locale: locale(formData),
      expected_assignment_version: positiveInteger(
        formData,
        "expected_assignment_version",
      ),
      expected_progress_version: positiveInteger(
        formData,
        "expected_progress_version",
      ),
      catalog_digest: digest(formData),
      answers,
    },
  };
}
