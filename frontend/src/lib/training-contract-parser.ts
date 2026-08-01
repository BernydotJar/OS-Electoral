import type {
  TrainingAssessmentOutcome,
  TrainingAssignmentCreateEvidence,
  TrainingAssignmentListEvidence,
  TrainingAssignmentProjection,
  TrainingAttemptEvidence,
  TrainingCatalogLesson,
  TrainingCatalogModule,
  TrainingCatalogOption,
  TrainingCatalogPath,
  TrainingCatalogProjection,
  TrainingCatalogQuestion,
  TrainingCompletionReceiptProjection,
  TrainingModuleProgressProjection,
  TrainingObjective,
  TrainingPathModule,
  TrainingQuestionFeedback,
  TrainingReceiptListEvidence,
} from "@/lib/contracts";

const UUID =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const DIGEST = /^[0-9a-f]{64}$/;
const IDENTIFIER = /^[a-z][a-z0-9_]{2,79}$/;
const VERSION = /^[1-9][0-9]{0,3}\.[0-9]{1,4}\.[0-9]{1,4}$/;

export class TrainingContractValidationError extends Error {}

type RecordValue = Record<string, unknown>;

function record(value: unknown, label: string): RecordValue {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new TrainingContractValidationError(`${label} must be an object`);
  }
  return value as RecordValue;
}

function exact(
  value: RecordValue,
  keys: readonly string[],
  label: string,
): void {
  const actual = Object.keys(value).sort();
  const expected = [...keys].sort();
  if (
    actual.length !== expected.length ||
    actual.some((key, index) => key !== expected[index])
  ) {
    throw new TrainingContractValidationError(
      `${label} has unexpected or missing fields`,
    );
  }
}

function string(value: unknown, label: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new TrainingContractValidationError(
      `${label} must be a non-empty string`,
    );
  }
  return value;
}

function identifier(value: unknown, label: string): string {
  const result = string(value, label);
  if (!IDENTIFIER.test(result)) {
    throw new TrainingContractValidationError(`${label} is invalid`);
  }
  return result;
}

function version(value: unknown, label: string): string {
  const result = string(value, label);
  if (!VERSION.test(result)) {
    throw new TrainingContractValidationError(`${label} is invalid`);
  }
  return result;
}

function uuid(value: unknown, label: string): string {
  const result = string(value, label);
  if (!UUID.test(result)) {
    throw new TrainingContractValidationError(`${label} is not a UUID`);
  }
  return result;
}

function digest(value: unknown, label: string): string {
  const result = string(value, label);
  if (!DIGEST.test(result)) {
    throw new TrainingContractValidationError(
      `${label} is not a SHA-256 digest`,
    );
  }
  return result;
}

function integer(
  value: unknown,
  label: string,
  minimum = 0,
  maximum = Number.MAX_SAFE_INTEGER,
): number {
  if (
    !Number.isInteger(value) ||
    (value as number) < minimum ||
    (value as number) > maximum
  ) {
    throw new TrainingContractValidationError(
      `${label} must be an integer in range`,
    );
  }
  return value as number;
}

function boolean(value: unknown, label: string): boolean {
  if (typeof value !== "boolean") {
    throw new TrainingContractValidationError(`${label} must be boolean`);
  }
  return value;
}

function date(value: unknown, label: string): string {
  const result = string(value, label);
  if (Number.isNaN(Date.parse(result))) {
    throw new TrainingContractValidationError(
      `${label} must be an ISO timestamp`,
    );
  }
  return result;
}

function nullableDate(value: unknown, label: string): string | null {
  return value === null ? null : date(value, label);
}

function nullableString(value: unknown, label: string): string | null {
  return value === null ? null : string(value, label);
}

function array<T>(
  value: unknown,
  label: string,
  parse: (item: unknown, index: number) => T,
): readonly T[] {
  if (!Array.isArray(value)) {
    throw new TrainingContractValidationError(`${label} must be an array`);
  }
  return value.map(parse);
}

function none(value: unknown, label: string): "NONE" {
  if (value !== "NONE") {
    throw new TrainingContractValidationError(`${label} must be NONE`);
  }
  return "NONE";
}

function enumValue<T extends string>(
  value: unknown,
  allowed: readonly T[],
  label: string,
): T {
  if (typeof value !== "string" || !allowed.includes(value as T)) {
    throw new TrainingContractValidationError(
      `${label} has an unsupported value`,
    );
  }
  return value as T;
}

function objective(value: unknown, index: number): TrainingObjective {
  const source = record(value, `objective ${index}`);
  exact(source, ["id", "text"], `objective ${index}`);
  return {
    id: identifier(source.id, "objective id"),
    text: string(source.text, "objective text"),
  };
}

function option(value: unknown, index: number): TrainingCatalogOption {
  const source = record(value, `option ${index}`);
  exact(source, ["id", "label"], `option ${index}`);
  return {
    id: identifier(source.id, "option id"),
    label: string(source.label, "option label"),
  };
}

function question(value: unknown, index: number): TrainingCatalogQuestion {
  const source = record(value, `question ${index}`);
  exact(source, ["id", "prompt", "options"], `question ${index}`);
  const options = array(source.options, "question options", option);
  if (options.length < 2 || options.length > 6) {
    throw new TrainingContractValidationError(
      "question options are out of bounds",
    );
  }
  return {
    id: identifier(source.id, "question id"),
    prompt: string(source.prompt, "question prompt"),
    options,
  };
}

function lesson(value: unknown, index: number): TrainingCatalogLesson {
  const source = record(value, `lesson ${index}`);
  exact(source, ["id", "title", "body", "source_refs"], `lesson ${index}`);
  return {
    id: identifier(source.id, "lesson id"),
    title: string(source.title, "lesson title"),
    body: string(source.body, "lesson body"),
    source_refs: array(source.source_refs, "lesson sources", (item) =>
      string(item, "source path"),
    ),
  };
}

function module(value: unknown, index: number): TrainingCatalogModule {
  const source = record(value, `module ${index}`);
  exact(
    source,
    [
      "module_id",
      "version",
      "status",
      "title",
      "summary",
      "objectives",
      "lessons",
      "questions",
      "passing_percent",
      "sources",
      "authority_effect",
    ],
    `module ${index}`,
  );
  const result: TrainingCatalogModule = {
    module_id: identifier(source.module_id, "module id"),
    version: version(source.version, "module version"),
    status: enumValue(source.status, ["APPROVED", "RETIRED"], "module status"),
    title: string(source.title, "module title"),
    summary: string(source.summary, "module summary"),
    objectives: array(source.objectives, "module objectives", objective),
    lessons: array(source.lessons, "module lessons", lesson),
    questions: array(source.questions, "module questions", question),
    passing_percent: integer(source.passing_percent, "passing percent", 1, 100),
    sources: array(source.sources, "module sources", (item) =>
      string(item, "source path"),
    ),
    authority_effect: none(source.authority_effect, "module authority effect"),
  };
  if (
    result.objectives.length === 0 ||
    result.lessons.length === 0 ||
    result.questions.length === 0
  ) {
    throw new TrainingContractValidationError(
      "approved module must contain learning content",
    );
  }
  return result;
}

function pathModule(value: unknown, index: number): TrainingPathModule {
  const source = record(value, `path module ${index}`);
  exact(source, ["module_id", "version", "required"], `path module ${index}`);
  return {
    module_id: identifier(source.module_id, "path module id"),
    version: version(source.version, "path module version"),
    required: boolean(source.required, "path module required"),
  };
}

function path(value: unknown, index: number): TrainingCatalogPath {
  const source = record(value, `path ${index}`);
  exact(
    source,
    ["path_id", "version", "role_slugs", "modules", "authority_effect"],
    `path ${index}`,
  );
  return {
    path_id: identifier(source.path_id, "path id"),
    version: version(source.version, "path version"),
    role_slugs: array(source.role_slugs, "path role slugs", (item) =>
      identifier(item, "role slug"),
    ),
    modules: array(source.modules, "path modules", pathModule),
    authority_effect: none(source.authority_effect, "path authority effect"),
  };
}

export function parseTrainingCatalogProjection(
  value: unknown,
): TrainingCatalogProjection {
  const source = record(value, "training catalog");
  exact(
    source,
    [
      "locale",
      "catalog_digest",
      "modules",
      "paths",
      "authority_effect",
      "external_effects",
    ],
    "training catalog",
  );
  const modules = array(source.modules, "catalog modules", module);
  const paths = array(source.paths, "catalog paths", path);
  const known = new Set(
    modules.map((item) => `${item.module_id}@${item.version}`),
  );
  if (
    paths.some((item) =>
      item.modules.some(
        (entry) => !known.has(`${entry.module_id}@${entry.version}`),
      ),
    )
  ) {
    throw new TrainingContractValidationError(
      "training path references an unknown module",
    );
  }
  return {
    locale: enumValue(source.locale, ["es", "en"], "training locale"),
    catalog_digest: digest(source.catalog_digest, "catalog digest"),
    modules,
    paths,
    authority_effect: none(source.authority_effect, "catalog authority effect"),
    external_effects: none(source.external_effects, "catalog external effects"),
  };
}

function progress(
  value: unknown,
  index: number,
): TrainingModuleProgressProjection {
  const source = record(value, `training progress ${index}`);
  exact(
    source,
    [
      "id",
      "module_id",
      "module_version",
      "status",
      "attempt_count",
      "latest_result",
      "started_at",
      "completed_at",
      "version",
    ],
    `training progress ${index}`,
  );
  const latestResult: "PASS" | "FAIL" | null =
    source.latest_result === null
      ? null
      : enumValue(
          source.latest_result,
          ["PASS", "FAIL"] as const,
          "latest training result",
        );
  return {
    id: uuid(source.id, "training progress id"),
    module_id: identifier(source.module_id, "training module id"),
    module_version: version(source.module_version, "training module version"),
    status: enumValue(
      source.status,
      ["NOT_STARTED", "IN_PROGRESS", "COMPLETED"],
      "training progress status",
    ),
    attempt_count: integer(
      source.attempt_count,
      "training attempt count",
      0,
      10,
    ),
    latest_result: latestResult,
    started_at: nullableDate(source.started_at, "training started at"),
    completed_at: nullableDate(source.completed_at, "training completed at"),
    version: integer(source.version, "training progress version", 1),
  };
}

function assignment(value: unknown): TrainingAssignmentProjection {
  const source = record(value, "training assignment");
  exact(
    source,
    [
      "id",
      "tenant_id",
      "campaign_id",
      "principal_id",
      "path_id",
      "path_version",
      "role_slug",
      "status",
      "modules",
      "completed_modules",
      "total_modules",
      "next_module_id",
      "catalog_digest",
      "version",
      "assigned_at",
      "due_at",
      "completed_at",
      "authority_effect",
      "external_effects",
    ],
    "training assignment",
  );
  const modules = array(
    source.modules,
    "training assignment modules",
    progress,
  );
  const total = integer(source.total_modules, "training total modules", 1, 20);
  const completed = integer(
    source.completed_modules,
    "training completed modules",
    0,
    total,
  );
  if (
    modules.length !== total ||
    modules.filter((item) => item.status === "COMPLETED").length !== completed
  ) {
    throw new TrainingContractValidationError(
      "training assignment progress totals are inconsistent",
    );
  }
  const nextModule = nullableString(
    source.next_module_id,
    "next training module",
  );
  if (
    nextModule !== null &&
    !modules.some(
      (item) => item.module_id === nextModule && item.status !== "COMPLETED",
    )
  ) {
    throw new TrainingContractValidationError(
      "next training module is inconsistent",
    );
  }
  return {
    id: uuid(source.id, "training assignment id"),
    tenant_id: uuid(source.tenant_id, "training tenant id"),
    campaign_id: uuid(source.campaign_id, "training campaign id"),
    principal_id: uuid(source.principal_id, "training principal id"),
    path_id: identifier(source.path_id, "training path id"),
    path_version: version(source.path_version, "training path version"),
    role_slug:
      source.role_slug === null
        ? null
        : identifier(source.role_slug, "training role slug"),
    status: enumValue(
      source.status,
      ["ASSIGNED", "IN_PROGRESS", "COMPLETED"],
      "training assignment status",
    ),
    modules,
    completed_modules: completed,
    total_modules: total,
    next_module_id: nextModule,
    catalog_digest: digest(source.catalog_digest, "training catalog digest"),
    version: integer(source.version, "training assignment version", 1),
    assigned_at: date(source.assigned_at, "training assigned at"),
    due_at: nullableDate(source.due_at, "training due at"),
    completed_at: nullableDate(source.completed_at, "training completed at"),
    authority_effect: none(
      source.authority_effect,
      "training assignment authority effect",
    ),
    external_effects: none(
      source.external_effects,
      "training assignment external effects",
    ),
  };
}

export function parseTrainingAssignmentListEvidence(
  value: unknown,
  tenantId?: string,
  campaignId?: string,
  principalId?: string,
): TrainingAssignmentListEvidence {
  const source = record(value, "training assignment list evidence");
  exact(
    source,
    ["assignments", "audit_event_id", "authority_effect"],
    "training assignment list evidence",
  );
  const assignments = array(
    source.assignments,
    "training assignments",
    (item) => assignment(item),
  );
  if (
    assignments.some(
      (item) =>
        (tenantId !== undefined && item.tenant_id !== tenantId) ||
        (campaignId !== undefined && item.campaign_id !== campaignId) ||
        (principalId !== undefined && item.principal_id !== principalId),
    )
  ) {
    throw new TrainingContractValidationError(
      "training assignments escaped the requested scope",
    );
  }
  return {
    assignments,
    audit_event_id: uuid(source.audit_event_id, "training assignment audit id"),
    authority_effect: none(
      source.authority_effect,
      "training assignment list authority effect",
    ),
  };
}

export function parseTrainingAssignmentCreateEvidence(
  value: unknown,
  tenantId?: string,
  campaignId?: string,
  principalId?: string,
): TrainingAssignmentCreateEvidence {
  const source = record(value, "training assignment create evidence");
  exact(
    source,
    ["assignment", "audit_event_id", "outbox_event_id"],
    "training assignment create evidence",
  );
  const parsed = assignment(source.assignment);
  if (
    (tenantId !== undefined && parsed.tenant_id !== tenantId) ||
    (campaignId !== undefined && parsed.campaign_id !== campaignId) ||
    (principalId !== undefined && parsed.principal_id !== principalId)
  ) {
    throw new TrainingContractValidationError(
      "created training assignment escaped scope",
    );
  }
  return {
    assignment: parsed,
    audit_event_id: uuid(source.audit_event_id, "training assignment audit id"),
    outbox_event_id: uuid(
      source.outbox_event_id,
      "training assignment outbox id",
    ),
  };
}

function feedback(value: unknown, index: number): TrainingQuestionFeedback {
  const source = record(value, `training feedback ${index}`);
  exact(
    source,
    ["question_id", "correct", "explanation"],
    `training feedback ${index}`,
  );
  return {
    question_id: identifier(source.question_id, "feedback question id"),
    correct: boolean(source.correct, "feedback correct"),
    explanation: string(source.explanation, "feedback explanation"),
  };
}

function outcome(value: unknown): TrainingAssessmentOutcome {
  const source = record(value, "training assessment outcome");
  exact(
    source,
    [
      "result",
      "correct_count",
      "total_questions",
      "passing_percent",
      "feedback",
      "authority_effect",
    ],
    "training assessment outcome",
  );
  const total = integer(
    source.total_questions,
    "training question total",
    1,
    20,
  );
  const correct = integer(
    source.correct_count,
    "training correct count",
    0,
    total,
  );
  const parsedFeedback = array(source.feedback, "training feedback", feedback);
  if (parsedFeedback.length !== total) {
    throw new TrainingContractValidationError(
      "training feedback count is inconsistent",
    );
  }
  return {
    result: enumValue(
      source.result,
      ["PASS", "FAIL"],
      "training assessment result",
    ),
    correct_count: correct,
    total_questions: total,
    passing_percent: integer(
      source.passing_percent,
      "training passing percent",
      1,
      100,
    ),
    feedback: parsedFeedback,
    authority_effect: none(
      source.authority_effect,
      "training assessment authority effect",
    ),
  };
}

function receipt(
  value: unknown,
  index = 0,
): TrainingCompletionReceiptProjection {
  const source = record(value, `training receipt ${index}`);
  exact(
    source,
    [
      "id",
      "assignment_id",
      "module_progress_id",
      "principal_id",
      "module_id",
      "module_version",
      "result",
      "completed_at",
      "catalog_digest",
      "audit_event_id",
      "authority_effect",
      "external_effects",
    ],
    `training receipt ${index}`,
  );
  if (source.result !== "PASS") {
    throw new TrainingContractValidationError(
      "training receipt must represent a passing completion",
    );
  }
  return {
    id: uuid(source.id, "training receipt id"),
    assignment_id: uuid(source.assignment_id, "training receipt assignment id"),
    module_progress_id: uuid(
      source.module_progress_id,
      "training receipt progress id",
    ),
    principal_id: uuid(source.principal_id, "training receipt principal id"),
    module_id: identifier(source.module_id, "training receipt module id"),
    module_version: version(
      source.module_version,
      "training receipt module version",
    ),
    result: "PASS",
    completed_at: date(source.completed_at, "training receipt completed at"),
    catalog_digest: digest(source.catalog_digest, "training receipt digest"),
    audit_event_id: uuid(source.audit_event_id, "training receipt audit id"),
    authority_effect: none(
      source.authority_effect,
      "training receipt authority effect",
    ),
    external_effects: none(
      source.external_effects,
      "training receipt external effects",
    ),
  };
}

export function parseTrainingAttemptEvidence(
  value: unknown,
  tenantId?: string,
  campaignId?: string,
  principalId?: string,
): TrainingAttemptEvidence {
  const source = record(value, "training attempt evidence");
  exact(
    source,
    ["assignment", "outcome", "receipt", "audit_event_id"],
    "training attempt evidence",
  );
  const parsedAssignment = assignment(source.assignment);
  const parsedReceipt =
    source.receipt === null ? null : receipt(source.receipt);
  if (
    (tenantId !== undefined && parsedAssignment.tenant_id !== tenantId) ||
    (campaignId !== undefined && parsedAssignment.campaign_id !== campaignId) ||
    (principalId !== undefined &&
      parsedAssignment.principal_id !== principalId) ||
    (parsedReceipt !== null &&
      parsedReceipt.principal_id !== parsedAssignment.principal_id)
  ) {
    throw new TrainingContractValidationError("training attempt escaped scope");
  }
  return {
    assignment: parsedAssignment,
    outcome: outcome(source.outcome),
    receipt: parsedReceipt,
    audit_event_id: uuid(source.audit_event_id, "training attempt audit id"),
  };
}

export function parseTrainingReceiptListEvidence(
  value: unknown,
  principalId?: string,
): TrainingReceiptListEvidence {
  const source = record(value, "training receipt list evidence");
  exact(
    source,
    ["receipts", "audit_event_id", "authority_effect"],
    "training receipt list evidence",
  );
  const receipts = array(source.receipts, "training receipts", receipt);
  if (
    principalId !== undefined &&
    receipts.some((item) => item.principal_id !== principalId)
  ) {
    throw new TrainingContractValidationError(
      "training receipt escaped principal scope",
    );
  }
  return {
    receipts,
    audit_event_id: uuid(
      source.audit_event_id,
      "training receipt list audit id",
    ),
    authority_effect: none(
      source.authority_effect,
      "training receipt list authority effect",
    ),
  };
}

export function parseTrainingAssignmentEvidence(
  value: unknown,
  tenantId?: string,
  campaignId?: string,
  principalId?: string,
): Readonly<{
  assignment: TrainingAssignmentProjection;
  audit_event_id: string;
}> {
  const source = record(value, "training assignment evidence");
  exact(
    source,
    ["assignment", "audit_event_id"],
    "training assignment evidence",
  );
  const parsed = assignment(source.assignment);
  if (
    (tenantId !== undefined && parsed.tenant_id !== tenantId) ||
    (campaignId !== undefined && parsed.campaign_id !== campaignId) ||
    (principalId !== undefined && parsed.principal_id !== principalId)
  ) {
    throw new TrainingContractValidationError(
      "training assignment escaped scope",
    );
  }
  return {
    assignment: parsed,
    audit_event_id: uuid(source.audit_event_id, "training assignment audit id"),
  };
}
