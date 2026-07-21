import type {
  StrategyAssumptionRecord,
  StrategyContradictionRecord,
  StrategyDecisionRecord,
  StrategyEvidenceRecord,
  StrategyHypothesisRecord,
  StrategyNextAction,
  StrategyObjectiveRecord,
  StrategyOptionRecord,
  StrategyRedTeamFindingRecord,
  StrategyWorkspaceProjection,
  StrategyWorkspaceReadEvidence,
} from "@/lib/contracts";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const LIMITATIONS = [
  "NOT_PUBLIC_POSITIONING",
  "NOT_A_HUMAN_APPROVAL",
  "NO_VOTER_PROFILING_OR_INDIVIDUAL_TARGETING",
  "NO_CITIZEN_CONTACT_OR_EXTERNAL_EFFECTS",
] as const;

type JsonRecord = Record<string, unknown>;

export class StrategyContractValidationError extends Error {}

function record(value: unknown, label: string): JsonRecord {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new StrategyContractValidationError(`${label} must be an object`);
  }
  return value as JsonRecord;
}

function exactKeys(
  source: JsonRecord,
  allowed: readonly string[],
  label: string,
): void {
  const extras = Object.keys(source).filter((key) => !allowed.includes(key));
  if (extras.length > 0) {
    throw new StrategyContractValidationError(
      `${label} contains unexpected fields`,
    );
  }
}

function text(value: unknown, label: string): string {
  if (typeof value !== "string" || value.trim().length === 0) {
    throw new StrategyContractValidationError(
      `${label} must be a non-empty string`,
    );
  }
  return value;
}

function nullableText(value: unknown, label: string): string | null {
  return value === null ? null : text(value, label);
}

function uuid(value: unknown, label: string): string {
  const candidate = text(value, label);
  if (!UUID_PATTERN.test(candidate)) {
    throw new StrategyContractValidationError(`${label} must be a UUID`);
  }
  return candidate;
}

function integer(value: unknown, label: string, minimum = 0): number {
  if (!Number.isInteger(value) || (value as number) < minimum) {
    throw new StrategyContractValidationError(
      `${label} must be an integer >= ${minimum}`,
    );
  }
  return value as number;
}

function boolean(value: unknown, label: string): boolean {
  if (typeof value !== "boolean") {
    throw new StrategyContractValidationError(`${label} must be a boolean`);
  }
  return value;
}

function array(value: unknown, label: string): readonly unknown[] {
  if (!Array.isArray(value)) {
    throw new StrategyContractValidationError(`${label} must be an array`);
  }
  return value;
}

function stringArray(value: unknown, label: string): readonly string[] {
  const values = array(value, label).map((item, index) =>
    text(item, `${label}[${index}]`),
  );
  if (new Set(values).size !== values.length) {
    throw new StrategyContractValidationError(`${label} contains duplicates`);
  }
  return values;
}

function uuidArray(value: unknown, label: string): readonly string[] {
  const values = array(value, label).map((item, index) =>
    uuid(item, `${label}[${index}]`),
  );
  if (new Set(values).size !== values.length) {
    throw new StrategyContractValidationError(`${label} contains duplicates`);
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
    throw new StrategyContractValidationError(`${label} is not supported`);
  }
  return candidate as T;
}

function timestamp(value: unknown, label: string): string {
  const candidate = text(value, label);
  if (
    !Number.isFinite(Date.parse(candidate)) ||
    !/(?:Z|[+-]\d{2}:\d{2})$/.test(candidate)
  ) {
    throw new StrategyContractValidationError(
      `${label} must be a timezone-aware timestamp`,
    );
  }
  return candidate;
}

function isoDate(value: unknown, label: string): string {
  const candidate = text(value, label);
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(candidate) ||
    !Number.isFinite(Date.parse(`${candidate}T00:00:00Z`))
  ) {
    throw new StrategyContractValidationError(`${label} must be an ISO date`);
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

function parseEvidence(value: unknown, label: string): StrategyEvidenceRecord {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "classification",
      "statement",
      "source_reference",
      "authority",
      "jurisdiction",
      "status",
      "collected_at",
    ],
    label,
  );
  const classification = literal(
    source.classification,
    ["VERIFIED", "INFERRED", "UNKNOWN"] as const,
    `${label}.classification`,
  );
  const status = literal(
    source.status,
    ["ACCEPTED", "NEEDS_REVIEW", "REJECTED"] as const,
    `${label}.status`,
  );
  const sourceReference = nullableText(
    source.source_reference,
    `${label}.source_reference`,
  );
  const authority = nullableText(source.authority, `${label}.authority`);
  const jurisdiction = nullableText(
    source.jurisdiction,
    `${label}.jurisdiction`,
  );
  if (
    classification === "VERIFIED" &&
    (status !== "ACCEPTED" ||
      sourceReference === null ||
      authority === null ||
      jurisdiction === null)
  ) {
    throw new StrategyContractValidationError(
      `${label} verified evidence lacks accepted provenance`,
    );
  }
  if (
    classification === "UNKNOWN" &&
    (status !== "NEEDS_REVIEW" ||
      sourceReference !== null ||
      authority !== null ||
      jurisdiction !== null)
  ) {
    throw new StrategyContractValidationError(
      `${label} unknown evidence cannot claim provenance`,
    );
  }
  if (
    classification === "INFERRED" &&
    (status === "REJECTED" || sourceReference === null)
  ) {
    throw new StrategyContractValidationError(
      `${label} inferred evidence lacks valid provenance`,
    );
  }
  return {
    id: uuid(source.id, `${label}.id`),
    classification,
    statement: text(source.statement, `${label}.statement`),
    source_reference: sourceReference,
    authority,
    jurisdiction,
    status,
    collected_at: timestamp(source.collected_at, `${label}.collected_at`),
  };
}

function parseAssumption(
  value: unknown,
  label: string,
): StrategyAssumptionRecord {
  const source = record(value, label);
  exactKeys(
    source,
    ["id", "statement", "evidence_refs", "invalidation_signals", "status"],
    label,
  );
  const signals = stringArray(
    source.invalidation_signals,
    `${label}.invalidation_signals`,
  );
  if (signals.length === 0) {
    throw new StrategyContractValidationError(
      `${label} requires invalidation signals`,
    );
  }
  return {
    id: uuid(source.id, `${label}.id`),
    statement: text(source.statement, `${label}.statement`),
    evidence_refs: uuidArray(source.evidence_refs, `${label}.evidence_refs`),
    invalidation_signals: signals,
    status: literal(
      source.status,
      ["ACTIVE", "INVALIDATED"] as const,
      `${label}.status`,
    ),
  };
}

function parseHypothesis(
  value: unknown,
  label: string,
): StrategyHypothesisRecord {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "title",
      "statement",
      "evidence_refs",
      "assumption_refs",
      "invalidation_signals",
      "status",
    ],
    label,
  );
  const evidenceRefs = uuidArray(
    source.evidence_refs,
    `${label}.evidence_refs`,
  );
  const signals = stringArray(
    source.invalidation_signals,
    `${label}.invalidation_signals`,
  );
  if (evidenceRefs.length === 0 || signals.length === 0) {
    throw new StrategyContractValidationError(
      `${label} requires evidence and invalidation signals`,
    );
  }
  return {
    id: uuid(source.id, `${label}.id`),
    title: text(source.title, `${label}.title`),
    statement: text(source.statement, `${label}.statement`),
    evidence_refs: evidenceRefs,
    assumption_refs: uuidArray(
      source.assumption_refs,
      `${label}.assumption_refs`,
    ),
    invalidation_signals: signals,
    status: literal(
      source.status,
      ["DRAFT", "IN_REVIEW", "REJECTED"] as const,
      `${label}.status`,
    ),
  };
}

function parseOption(value: unknown, label: string): StrategyOptionRecord {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "title",
      "summary",
      "hypothesis_refs",
      "evidence_refs",
      "benefits",
      "risks",
      "tradeoffs",
    ],
    label,
  );
  const hypothesisRefs = uuidArray(
    source.hypothesis_refs,
    `${label}.hypothesis_refs`,
  );
  const evidenceRefs = uuidArray(
    source.evidence_refs,
    `${label}.evidence_refs`,
  );
  const benefits = stringArray(source.benefits, `${label}.benefits`);
  const risks = stringArray(source.risks, `${label}.risks`);
  const tradeoffs = stringArray(source.tradeoffs, `${label}.tradeoffs`);
  if (
    hypothesisRefs.length === 0 ||
    evidenceRefs.length === 0 ||
    benefits.length === 0 ||
    risks.length === 0 ||
    tradeoffs.length === 0
  ) {
    throw new StrategyContractValidationError(
      `${label} is not a complete comparable option`,
    );
  }
  return {
    id: uuid(source.id, `${label}.id`),
    title: text(source.title, `${label}.title`),
    summary: text(source.summary, `${label}.summary`),
    hypothesis_refs: hypothesisRefs,
    evidence_refs: evidenceRefs,
    benefits,
    risks,
    tradeoffs,
  };
}

function parseObjective(
  value: unknown,
  label: string,
): StrategyObjectiveRecord {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "outcome",
      "metric",
      "baseline",
      "target",
      "deadline",
      "owner_role_id",
      "evidence_refs",
    ],
    label,
  );
  const evidenceRefs = uuidArray(
    source.evidence_refs,
    `${label}.evidence_refs`,
  );
  if (evidenceRefs.length === 0) {
    throw new StrategyContractValidationError(`${label} requires evidence`);
  }
  return {
    id: uuid(source.id, `${label}.id`),
    outcome: text(source.outcome, `${label}.outcome`),
    metric: text(source.metric, `${label}.metric`),
    baseline: text(source.baseline, `${label}.baseline`),
    target: text(source.target, `${label}.target`),
    deadline: isoDate(source.deadline, `${label}.deadline`),
    owner_role_id: uuid(source.owner_role_id, `${label}.owner_role_id`),
    evidence_refs: evidenceRefs,
  };
}

function parseContradiction(
  value: unknown,
  label: string,
): StrategyContradictionRecord {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "left_ref",
      "right_ref",
      "description",
      "evidence_refs",
      "status",
      "resolution",
    ],
    label,
  );
  const left = uuid(source.left_ref, `${label}.left_ref`);
  const right = uuid(source.right_ref, `${label}.right_ref`);
  const status = literal(
    source.status,
    ["OPEN", "RESOLVED"] as const,
    `${label}.status`,
  );
  const resolution = nullableText(source.resolution, `${label}.resolution`);
  if (left === right)
    throw new StrategyContractValidationError(`${label} sides must differ`);
  if (
    (status === "OPEN" && resolution !== null) ||
    (status === "RESOLVED" && resolution === null)
  ) {
    throw new StrategyContractValidationError(
      `${label} resolution status is inconsistent`,
    );
  }
  return {
    id: uuid(source.id, `${label}.id`),
    left_ref: left,
    right_ref: right,
    description: text(source.description, `${label}.description`),
    evidence_refs: uuidArray(source.evidence_refs, `${label}.evidence_refs`),
    status,
    resolution,
  };
}

function parseFinding(
  value: unknown,
  label: string,
): StrategyRedTeamFindingRecord {
  const source = record(value, label);
  exactKeys(
    source,
    ["id", "severity", "description", "option_refs", "mitigation", "status"],
    label,
  );
  const optionRefs = uuidArray(source.option_refs, `${label}.option_refs`);
  if (optionRefs.length === 0) {
    throw new StrategyContractValidationError(
      `${label} requires affected options`,
    );
  }
  return {
    id: uuid(source.id, `${label}.id`),
    severity: literal(
      source.severity,
      ["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const,
      `${label}.severity`,
    ),
    description: text(source.description, `${label}.description`),
    option_refs: optionRefs,
    mitigation: text(source.mitigation, `${label}.mitigation`),
    status: literal(
      source.status,
      ["OPEN", "RESOLVED"] as const,
      `${label}.status`,
    ),
  };
}

function parseDecision(value: unknown, label: string): StrategyDecisionRecord {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "workspace_version",
      "selected_option_id",
      "reason",
      "human_role_id",
      "approval_receipt_id",
      "decided_at",
    ],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    workspace_version: integer(
      source.workspace_version,
      `${label}.workspace_version`,
      1,
    ),
    selected_option_id: uuid(
      source.selected_option_id,
      `${label}.selected_option_id`,
    ),
    reason: text(source.reason, `${label}.reason`),
    human_role_id: uuid(source.human_role_id, `${label}.human_role_id`),
    approval_receipt_id: text(
      source.approval_receipt_id,
      `${label}.approval_receipt_id`,
    ),
    decided_at: timestamp(source.decided_at, `${label}.decided_at`),
  };
}

function assertRefs(
  refs: readonly string[],
  known: Set<string>,
  label: string,
): void {
  for (const ref of refs) {
    if (!known.has(ref)) {
      throw new StrategyContractValidationError(
        `unknown ${label} reference ${ref}`,
      );
    }
  }
}

function parseWorkspace(value: unknown): StrategyWorkspaceProjection {
  const source = record(value, "strategy workspace");
  exactKeys(
    source,
    [
      "id",
      "tenant_id",
      "campaign_id",
      "campaign_version",
      "campaign_status",
      "campaign_name",
      "candidate_workspace_version",
      "team_workspace_version",
      "title",
      "evidence",
      "assumptions",
      "hypotheses",
      "options",
      "objectives",
      "contradictions",
      "red_team_findings",
      "decision",
      "status",
      "verified_evidence_count",
      "inferred_evidence_count",
      "unknown_evidence_count",
      "open_contradiction_count",
      "open_high_risk_count",
      "complete_option_count",
      "measurable_objective_count",
      "next_action",
      "human_decision_required",
      "authority_effect",
      "external_effects",
      "limitation_codes",
      "version",
      "created_at",
      "updated_at",
    ],
    "strategy workspace",
  );
  const evidence = nullableModels(
    source.evidence,
    "strategy workspace.evidence",
    parseEvidence,
  );
  const assumptions = nullableModels(
    source.assumptions,
    "strategy workspace.assumptions",
    parseAssumption,
  );
  const hypotheses = nullableModels(
    source.hypotheses,
    "strategy workspace.hypotheses",
    parseHypothesis,
  );
  const options = nullableModels(
    source.options,
    "strategy workspace.options",
    parseOption,
  );
  const objectives = nullableModels(
    source.objectives,
    "strategy workspace.objectives",
    parseObjective,
  );
  const contradictions = nullableModels(
    source.contradictions,
    "strategy workspace.contradictions",
    parseContradiction,
  );
  const findings = nullableModels(
    source.red_team_findings,
    "strategy workspace.red_team_findings",
    parseFinding,
  );
  const decision =
    source.decision === null
      ? null
      : parseDecision(source.decision, "strategy workspace.decision");

  const workspaceId = uuid(source.id, "strategy workspace.id");
  const allIds = [
    workspaceId,
    ...(evidence ?? []).map((item) => item.id),
    ...(assumptions ?? []).map((item) => item.id),
    ...(hypotheses ?? []).map((item) => item.id),
    ...(options ?? []).map((item) => item.id),
    ...(objectives ?? []).map((item) => item.id),
    ...(contradictions ?? []).map((item) => item.id),
    ...(findings ?? []).map((item) => item.id),
    ...(decision ? [decision.id] : []),
  ];
  if (new Set(allIds).size !== allIds.length) {
    throw new StrategyContractValidationError(
      "strategy records must use unique IDs",
    );
  }

  const evidenceById = new Map((evidence ?? []).map((item) => [item.id, item]));
  const evidenceIds = new Set(evidenceById.keys());
  const assumptionIds = new Set((assumptions ?? []).map((item) => item.id));
  const hypothesisIds = new Set((hypotheses ?? []).map((item) => item.id));
  const optionIds = new Set((options ?? []).map((item) => item.id));
  const objectiveIds = new Set((objectives ?? []).map((item) => item.id));
  const referenceable = new Set([
    ...evidenceIds,
    ...assumptionIds,
    ...hypothesisIds,
    ...optionIds,
    ...objectiveIds,
  ]);

  for (const assumption of assumptions ?? []) {
    assertRefs(assumption.evidence_refs, evidenceIds, "evidence");
    if (
      assumption.evidence_refs.some(
        (ref) => evidenceById.get(ref)?.status === "REJECTED",
      )
    ) {
      throw new StrategyContractValidationError(
        "assumption cannot use rejected evidence",
      );
    }
  }
  for (const hypothesis of hypotheses ?? []) {
    assertRefs(hypothesis.evidence_refs, evidenceIds, "evidence");
    assertRefs(hypothesis.assumption_refs, assumptionIds, "assumption");
    if (
      hypothesis.evidence_refs.some(
        (ref) => evidenceById.get(ref)?.status === "REJECTED",
      )
    ) {
      throw new StrategyContractValidationError(
        "hypothesis cannot use rejected evidence",
      );
    }
    if (
      hypothesis.status === "IN_REVIEW" &&
      !hypothesis.evidence_refs.some(
        (ref) =>
          evidenceById.get(ref)?.classification === "VERIFIED" &&
          evidenceById.get(ref)?.status === "ACCEPTED",
      )
    ) {
      throw new StrategyContractValidationError(
        "hypothesis in review requires verified evidence",
      );
    }
  }
  for (const option of options ?? []) {
    assertRefs(option.hypothesis_refs, hypothesisIds, "hypothesis");
    assertRefs(option.evidence_refs, evidenceIds, "evidence");
    if (
      option.evidence_refs.some(
        (ref) => evidenceById.get(ref)?.status === "REJECTED",
      )
    ) {
      throw new StrategyContractValidationError(
        "strategy option cannot use rejected evidence",
      );
    }
  }
  for (const objective of objectives ?? [])
    assertRefs(objective.evidence_refs, evidenceIds, "evidence");
  for (const contradiction of contradictions ?? []) {
    if (
      !referenceable.has(contradiction.left_ref) ||
      !referenceable.has(contradiction.right_ref)
    ) {
      throw new StrategyContractValidationError(
        "unknown contradiction reference",
      );
    }
    assertRefs(contradiction.evidence_refs, evidenceIds, "evidence");
  }
  for (const finding of findings ?? [])
    assertRefs(finding.option_refs, optionIds, "strategy option");

  const version = integer(source.version, "strategy workspace.version", 1);
  if (decision !== null) {
    if (decision.workspace_version !== version) {
      throw new StrategyContractValidationError(
        "strategy decision must bind the current workspace version",
      );
    }
    if (!optionIds.has(decision.selected_option_id)) {
      throw new StrategyContractValidationError(
        "strategy decision selected option is unknown",
      );
    }
  }

  const verifiedCount = (evidence ?? []).filter(
    (item) => item.classification === "VERIFIED" && item.status === "ACCEPTED",
  ).length;
  const inferredCount = (evidence ?? []).filter(
    (item) => item.classification === "INFERRED",
  ).length;
  const unknownCount = (evidence ?? []).filter(
    (item) => item.classification === "UNKNOWN",
  ).length;
  const openContradictions = (contradictions ?? []).filter(
    (item) => item.status === "OPEN",
  ).length;
  const openHigh = (findings ?? []).filter(
    (item) =>
      item.status === "OPEN" &&
      (item.severity === "CRITICAL" || item.severity === "HIGH"),
  ).length;
  const completeOptions = (options ?? []).length;
  const measurableObjectives = (objectives ?? []).length;

  if (
    source.verified_evidence_count !== verifiedCount ||
    source.inferred_evidence_count !== inferredCount ||
    source.unknown_evidence_count !== unknownCount ||
    source.open_contradiction_count !== openContradictions ||
    source.open_high_risk_count !== openHigh ||
    source.complete_option_count !== completeOptions ||
    source.measurable_objective_count !== measurableObjectives
  ) {
    throw new StrategyContractValidationError(
      "strategy workspace counts are inconsistent",
    );
  }

  let expectedStatus: StrategyWorkspaceProjection["status"];
  let expectedNext: StrategyNextAction;
  if (decision !== null) {
    expectedStatus = "DECIDED_INTERNAL";
    expectedNext = "REVALIDATE_DECISION";
  } else if (verifiedCount === 0 || unknownCount > 0) {
    expectedStatus = "EVIDENCE_REQUIRED";
    expectedNext = "ADD_VERIFIED_EVIDENCE";
  } else if (openContradictions > 0) {
    expectedStatus = "CONTRADICTIONS_OPEN";
    expectedNext = "RESOLVE_CONTRADICTIONS";
  } else if (openHigh > 0) {
    expectedStatus = "RED_TEAM_BLOCKED";
    expectedNext = "ADDRESS_RED_TEAM_FINDINGS";
  } else if (completeOptions < 2) {
    expectedStatus = "OPTIONS_INCOMPLETE";
    expectedNext = "COMPLETE_COMPARABLE_OPTIONS";
  } else if (measurableObjectives === 0) {
    expectedStatus = "OBJECTIVES_INCOMPLETE";
    expectedNext = "DEFINE_MEASURABLE_OBJECTIVES";
  } else {
    expectedStatus = "READY_FOR_HUMAN_DECISION";
    expectedNext = "MAKE_HUMAN_DECISION";
  }
  const status = literal(
    source.status,
    [
      "EVIDENCE_REQUIRED",
      "CONTRADICTIONS_OPEN",
      "RED_TEAM_BLOCKED",
      "OPTIONS_INCOMPLETE",
      "OBJECTIVES_INCOMPLETE",
      "READY_FOR_HUMAN_DECISION",
      "DECIDED_INTERNAL",
    ] as const,
    "strategy workspace.status",
  );
  const nextAction = literal(
    source.next_action,
    [
      "ADD_VERIFIED_EVIDENCE",
      "RESOLVE_CONTRADICTIONS",
      "ADDRESS_RED_TEAM_FINDINGS",
      "COMPLETE_COMPARABLE_OPTIONS",
      "DEFINE_MEASURABLE_OBJECTIVES",
      "MAKE_HUMAN_DECISION",
      "REVALIDATE_DECISION",
    ] as const,
    "strategy workspace.next_action",
  );
  const humanDecisionRequired = boolean(
    source.human_decision_required,
    "strategy workspace.human_decision_required",
  );
  if (
    status !== expectedStatus ||
    nextAction !== expectedNext ||
    humanDecisionRequired !== (decision === null)
  ) {
    throw new StrategyContractValidationError(
      "strategy workspace status is inconsistent",
    );
  }
  const limitations = stringArray(
    source.limitation_codes,
    "strategy workspace.limitation_codes",
  );
  if (
    limitations.length !== LIMITATIONS.length ||
    !limitations.every((item, index) => item === LIMITATIONS[index])
  ) {
    throw new StrategyContractValidationError(
      "strategy mandatory limitations are missing",
    );
  }

  return {
    id: workspaceId,
    tenant_id: uuid(source.tenant_id, "strategy workspace.tenant_id"),
    campaign_id: uuid(source.campaign_id, "strategy workspace.campaign_id"),
    campaign_version: integer(
      source.campaign_version,
      "strategy workspace.campaign_version",
      1,
    ),
    campaign_status: literal(
      source.campaign_status,
      ["DRAFT", "ACTIVE"] as const,
      "strategy workspace.campaign_status",
    ),
    campaign_name: text(
      source.campaign_name,
      "strategy workspace.campaign_name",
    ),
    candidate_workspace_version: integer(
      source.candidate_workspace_version,
      "strategy workspace.candidate_workspace_version",
      1,
    ),
    team_workspace_version: integer(
      source.team_workspace_version,
      "strategy workspace.team_workspace_version",
      1,
    ),
    title: text(source.title, "strategy workspace.title"),
    evidence,
    assumptions,
    hypotheses,
    options,
    objectives,
    contradictions,
    red_team_findings: findings,
    decision,
    status,
    verified_evidence_count: verifiedCount,
    inferred_evidence_count: inferredCount,
    unknown_evidence_count: unknownCount,
    open_contradiction_count: openContradictions,
    open_high_risk_count: openHigh,
    complete_option_count: completeOptions,
    measurable_objective_count: measurableObjectives,
    next_action: nextAction,
    human_decision_required: humanDecisionRequired,
    authority_effect: literal(
      source.authority_effect,
      ["NONE"] as const,
      "strategy workspace.authority_effect",
    ),
    external_effects: literal(
      source.external_effects,
      ["NONE"] as const,
      "strategy workspace.external_effects",
    ),
    limitation_codes:
      limitations as StrategyWorkspaceProjection["limitation_codes"],
    version,
    created_at: timestamp(source.created_at, "strategy workspace.created_at"),
    updated_at: timestamp(source.updated_at, "strategy workspace.updated_at"),
  };
}

export function parseStrategyWorkspaceReadEvidence(
  value: unknown,
): StrategyWorkspaceReadEvidence {
  const source = record(value, "strategy workspace evidence");
  exactKeys(
    source,
    ["workspace", "audit_event_id"],
    "strategy workspace evidence",
  );
  return {
    workspace: parseWorkspace(source.workspace),
    audit_event_id: uuid(
      source.audit_event_id,
      "strategy workspace evidence.audit_event_id",
    ),
  };
}
