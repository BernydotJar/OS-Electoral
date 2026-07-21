import type {
  CandidateAttribute,
  CandidateCheckKey,
  CandidateClaim,
  CandidateContradiction,
  CandidateDevelopmentGoal,
  CandidateEvidence,
  CandidateEvidenceClassification,
  CandidateLimitation,
  CandidateNextAction,
  CandidateReputationRisk,
  CandidateSection,
  CandidateWorkspaceCheck,
  CandidateWorkspaceProjection,
  CandidateWorkspaceReadEvidence,
} from "@/lib/contracts";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
const SECTIONS = [
  "identity",
  "biography",
  "purpose",
  "values",
  "attributes",
  "contradictions",
  "development_goals",
  "reputation",
] as const satisfies readonly CandidateSection[];
const CHECKS = [
  ...SECTIONS,
  "approvals",
] as const satisfies readonly CandidateCheckKey[];
const LIMITATIONS = [
  "NOT_PUBLIC_POSITIONING_APPROVAL",
  "NOT_A_STRATEGY",
  "NO_VOTER_PROFILING",
  "NO_EXTERNAL_EFFECTS",
  "HUMAN_REVIEW_REQUIRED",
] as const satisfies readonly CandidateLimitation[];
const INDEPENDENT = new Set<CandidateEvidenceClassification>([
  "OFFICIAL_SOURCE",
  "CAMPAIGN_RESEARCH",
]);
const ENABLING = new Set(["ACCEPTED", "VERIFIED", "READY"]);

export class CandidateContractValidationError extends Error {}
type JsonRecord = Record<string, unknown>;

function record(value: unknown, label: string): JsonRecord {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new CandidateContractValidationError(`${label} must be an object`);
  }
  return value as JsonRecord;
}

function exactKeys(
  source: JsonRecord,
  keys: readonly string[],
  label: string,
): void {
  if (Object.keys(source).some((key) => !keys.includes(key))) {
    throw new CandidateContractValidationError(
      `${label} contains unexpected fields`,
    );
  }
}

function text(value: unknown, label: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new CandidateContractValidationError(
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
    throw new CandidateContractValidationError(`${label} must be a UUID`);
  }
  return candidate;
}

function integer(value: unknown, label: string, minimum = 0): number {
  if (!Number.isInteger(value) || (value as number) < minimum) {
    throw new CandidateContractValidationError(
      `${label} must be an integer >= ${minimum}`,
    );
  }
  return value as number;
}

function boolean(value: unknown, label: string): boolean {
  if (typeof value !== "boolean") {
    throw new CandidateContractValidationError(`${label} must be a boolean`);
  }
  return value;
}

function array(value: unknown, label: string): readonly unknown[] {
  if (!Array.isArray(value)) {
    throw new CandidateContractValidationError(`${label} must be an array`);
  }
  return value;
}

function timestamp(value: unknown, label: string): string {
  const candidate = text(value, label);
  if (
    !Number.isFinite(Date.parse(candidate)) ||
    !/(?:Z|[+-]\d{2}:\d{2})$/.test(candidate)
  ) {
    throw new CandidateContractValidationError(
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
  if (!allowed.includes(candidate as T)) {
    throw new CandidateContractValidationError(`${label} is not supported`);
  }
  return candidate as T;
}

function refs(value: unknown, label: string): readonly string[] {
  const items = array(value, label).map((item, index) =>
    uuid(item, `${label}[${index}]`),
  );
  if (new Set(items).size !== items.length) {
    throw new CandidateContractValidationError(
      `${label} contains duplicate references`,
    );
  }
  return items;
}

function parseEvidence(value: unknown, label: string): CandidateEvidence {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "classification",
      "status",
      "title",
      "source_reference",
      "source_authority",
      "jurisdiction",
      "excerpt",
      "observed_at",
    ],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    classification: literal(
      source.classification,
      [
        "OFFICIAL_SOURCE",
        "CAMPAIGN_RESEARCH",
        "PERCEPTION",
        "HYPOTHESIS",
        "UNKNOWN",
      ] as const,
      `${label}.classification`,
    ),
    status: literal(
      source.status,
      ["ACCEPTED", "VERIFIED", "READY", "REJECTED", "EXPIRED"] as const,
      `${label}.status`,
    ),
    title: text(source.title, `${label}.title`),
    source_reference: text(
      source.source_reference,
      `${label}.source_reference`,
    ),
    source_authority: nullableText(
      source.source_authority,
      `${label}.source_authority`,
    ),
    jurisdiction: nullableText(source.jurisdiction, `${label}.jurisdiction`),
    excerpt: nullableText(source.excerpt, `${label}.excerpt`),
    observed_at:
      source.observed_at === null
        ? null
        : timestamp(source.observed_at, `${label}.observed_at`),
  };
}

function parseClaim(value: unknown, label: string): CandidateClaim {
  const source = record(value, label);
  exactKeys(
    source,
    ["id", "label", "claim", "status", "classification", "evidence_refs"],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    label: text(source.label, `${label}.label`),
    claim: text(source.claim, `${label}.claim`),
    status: literal(
      source.status,
      [
        "UNKNOWN",
        "SELF_REPORTED",
        "UNDER_REVIEW",
        "EVIDENCE_PARTIAL",
        "VERIFIED",
        "REJECTED",
        "CONTRADICTED",
      ] as const,
      `${label}.status`,
    ),
    classification: literal(
      source.classification,
      [
        "OFFICIAL_SOURCE",
        "CAMPAIGN_RESEARCH",
        "PERCEPTION",
        "HYPOTHESIS",
        "UNKNOWN",
      ] as const,
      `${label}.classification`,
    ),
    evidence_refs: refs(source.evidence_refs, `${label}.evidence_refs`),
  };
}

function parseAttribute(value: unknown, label: string): CandidateAttribute {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "name",
      "claim",
      "status",
      "candidate_self_assessment",
      "team_assessment",
      "citizen_evidence",
      "evidence_refs",
      "perception_refs",
      "contradiction_refs",
      "risk",
    ],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    name: text(source.name, `${label}.name`),
    claim: text(source.claim, `${label}.claim`),
    status: literal(
      source.status,
      [
        "UNKNOWN",
        "SELF_REPORTED",
        "UNDER_REVIEW",
        "EVIDENCE_PARTIAL",
        "VERIFIED",
        "REJECTED",
        "CONTRADICTED",
      ] as const,
      `${label}.status`,
    ),
    candidate_self_assessment: literal(
      source.candidate_self_assessment,
      ["YES", "NO", "UNKNOWN"] as const,
      `${label}.candidate_self_assessment`,
    ),
    team_assessment: literal(
      source.team_assessment,
      ["YES", "PARTIAL", "NO", "UNKNOWN"] as const,
      `${label}.team_assessment`,
    ),
    citizen_evidence: literal(
      source.citizen_evidence,
      ["SUPPORTED", "PARTIAL", "UNRESOLVED", "CONTRADICTED"] as const,
      `${label}.citizen_evidence`,
    ),
    evidence_refs: refs(source.evidence_refs, `${label}.evidence_refs`),
    perception_refs: refs(source.perception_refs, `${label}.perception_refs`),
    contradiction_refs: refs(
      source.contradiction_refs,
      `${label}.contradiction_refs`,
    ),
    risk: text(source.risk, `${label}.risk`),
  };
}

function parseContradiction(
  value: unknown,
  label: string,
): CandidateContradiction {
  const source = record(value, label);
  exactKeys(
    source,
    ["id", "subject_ref", "description", "status", "evidence_refs"],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    subject_ref: uuid(source.subject_ref, `${label}.subject_ref`),
    description: text(source.description, `${label}.description`),
    status: literal(
      source.status,
      ["OPEN", "UNDER_REVIEW", "RESOLVED"] as const,
      `${label}.status`,
    ),
    evidence_refs: refs(source.evidence_refs, `${label}.evidence_refs`),
  };
}

function parseGoal(value: unknown, label: string): CandidateDevelopmentGoal {
  const source = record(value, label);
  exactKeys(
    source,
    ["id", "area", "objective", "status", "evidence_refs"],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    area: text(source.area, `${label}.area`),
    objective: text(source.objective, `${label}.objective`),
    status: literal(
      source.status,
      ["OPEN", "IN_PROGRESS", "COMPLETE"] as const,
      `${label}.status`,
    ),
    evidence_refs: refs(source.evidence_refs, `${label}.evidence_refs`),
  };
}

function parseRisk(value: unknown, label: string): CandidateReputationRisk {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "id",
      "title",
      "description",
      "severity",
      "status",
      "decision_required",
      "evidence_refs",
    ],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    title: text(source.title, `${label}.title`),
    description: text(source.description, `${label}.description`),
    severity: literal(
      source.severity,
      ["CRITICAL", "HIGH", "MEDIUM", "LOW"] as const,
      `${label}.severity`,
    ),
    status: literal(
      source.status,
      ["OPEN", "MITIGATING", "RESOLVED", "CLOSED"] as const,
      `${label}.status`,
    ),
    decision_required: boolean(
      source.decision_required,
      `${label}.decision_required`,
    ),
    evidence_refs: refs(source.evidence_refs, `${label}.evidence_refs`),
  };
}

function nullableItems<T>(
  value: unknown,
  label: string,
  parser: (item: unknown, itemLabel: string) => T,
): readonly T[] | null {
  if (value === null) return null;
  return array(value, label).map((item, index) =>
    parser(item, `${label}[${index}]`),
  );
}

function parseCheck(value: unknown, label: string): CandidateWorkspaceCheck {
  const source = record(value, label);
  exactKeys(source, ["key", "complete", "reason_code"], label);
  return {
    key: literal(source.key, CHECKS, `${label}.key`),
    complete: boolean(source.complete, `${label}.complete`),
    reason_code: text(source.reason_code, `${label}.reason_code`),
  };
}

function sections(value: unknown, label: string): readonly CandidateSection[] {
  const result = array(value, label).map((item, index) =>
    literal(item, SECTIONS, `${label}[${index}]`),
  );
  if (new Set(result).size !== result.length) {
    throw new CandidateContractValidationError(
      `${label} contains duplicate sections`,
    );
  }
  const canonical = SECTIONS.filter((section) => result.includes(section));
  if (canonical.some((section, index) => section !== result[index])) {
    throw new CandidateContractValidationError(`${label} is not canonical`);
  }
  return result;
}

function parseProjection(value: unknown): CandidateWorkspaceProjection {
  const source = record(value, "candidate workspace");
  exactKeys(
    source,
    [
      "id",
      "tenant_id",
      "campaign_id",
      "campaign_version",
      "campaign_status",
      "campaign_name",
      "jurisdiction",
      "candidate_id",
      "display_name",
      "status",
      "public_use_status",
      "external_effects",
      "evidence",
      "identity",
      "biography",
      "purpose",
      "values",
      "attributes",
      "contradictions",
      "development_goals",
      "reputation_risks",
      "checks",
      "completed_checks",
      "total_checks",
      "approvable_sections",
      "current_approved_sections",
      "approvals_required",
      "open_critical_high_risks",
      "next_action",
      "limitation_codes",
      "version",
      "created_at",
      "updated_at",
    ],
    "candidate workspace",
  );

  const workspaceId = uuid(source.id, "candidate workspace.id");
  const candidateId = uuid(
    source.candidate_id,
    "candidate workspace.candidate_id",
  );
  const evidence = array(source.evidence, "candidate workspace.evidence").map(
    (item, index) =>
      parseEvidence(item, `candidate workspace.evidence[${index}]`),
  );
  const evidenceById = new Map(evidence.map((item) => [item.id, item]));
  if (evidenceById.size !== evidence.length) {
    throw new CandidateContractValidationError(
      "candidate workspace contains duplicate evidence IDs",
    );
  }
  const identity =
    source.identity === null
      ? null
      : parseClaim(source.identity, "candidate workspace.identity");
  const biography =
    source.biography === null
      ? null
      : parseClaim(source.biography, "candidate workspace.biography");
  const purpose =
    source.purpose === null
      ? null
      : parseClaim(source.purpose, "candidate workspace.purpose");
  const values = nullableItems(
    source.values,
    "candidate workspace.values",
    parseClaim,
  );
  const attributes = nullableItems(
    source.attributes,
    "candidate workspace.attributes",
    parseAttribute,
  );
  const contradictions = nullableItems(
    source.contradictions,
    "candidate workspace.contradictions",
    parseContradiction,
  );
  const developmentGoals = nullableItems(
    source.development_goals,
    "candidate workspace.development_goals",
    parseGoal,
  );
  const reputationRisks = nullableItems(
    source.reputation_risks,
    "candidate workspace.reputation_risks",
    parseRisk,
  );

  const recordIds = [
    workspaceId,
    candidateId,
    ...evidence.map((item) => item.id),
    ...[identity, biography, purpose]
      .filter((item): item is CandidateClaim => item !== null)
      .map((item) => item.id),
    ...(values ?? []).map((item) => item.id),
    ...(attributes ?? []).map((item) => item.id),
    ...(contradictions ?? []).map((item) => item.id),
    ...(developmentGoals ?? []).map((item) => item.id),
    ...(reputationRisks ?? []).map((item) => item.id),
  ];
  if (new Set(recordIds).size !== recordIds.length) {
    throw new CandidateContractValidationError(
      "candidate workspace contains duplicate or colliding record IDs",
    );
  }
  const knownIds = new Set(recordIds);
  const contradictionById = new Map(
    (contradictions ?? []).map((item) => [item.id, item]),
  );
  const resolve = (
    evidenceRefs: readonly string[],
    label: string,
  ): readonly CandidateEvidence[] =>
    evidenceRefs.map((ref) => {
      const item = evidenceById.get(ref);
      if (!item)
        throw new CandidateContractValidationError(
          `unknown evidence reference ${ref} from ${label}`,
        );
      return item;
    });
  const validateClaim = (claim: CandidateClaim | null, label: string): void => {
    if (claim === null) return;
    const resolved = resolve(claim.evidence_refs, label);
    if (
      claim.status === "VERIFIED" &&
      (resolved.length === 0 ||
        !INDEPENDENT.has(claim.classification) ||
        !resolved.some(
          (item) =>
            INDEPENDENT.has(item.classification) && ENABLING.has(item.status),
        ))
    ) {
      throw new CandidateContractValidationError(
        `verified ${label} requires independent evidence`,
      );
    }
  };
  validateClaim(identity, "identity");
  validateClaim(biography, "biography");
  validateClaim(purpose, "purpose");
  (values ?? []).forEach((item) => validateClaim(item, `value ${item.id}`));
  (attributes ?? []).forEach((item) => {
    const resolved = resolve(item.evidence_refs, `attribute ${item.id}`);
    const perception = resolve(
      item.perception_refs,
      `attribute perception ${item.id}`,
    );
    if (perception.some((entry) => entry.classification !== "PERCEPTION")) {
      throw new CandidateContractValidationError(
        `attribute perception references must use perception records ${item.id}`,
      );
    }
    item.contradiction_refs.forEach((ref) => {
      const contradiction = contradictionById.get(ref);
      if (!contradiction) {
        throw new CandidateContractValidationError(
          `unknown contradiction reference ${ref} from attribute ${item.id}`,
        );
      }
      if (contradiction.subject_ref !== item.id) {
        throw new CandidateContractValidationError(
          `attribute contradiction reference targets another subject ${ref}`,
        );
      }
    });
    if (
      item.status === "VERIFIED" &&
      !resolved.some(
        (entry) =>
          INDEPENDENT.has(entry.classification) && ENABLING.has(entry.status),
      )
    ) {
      throw new CandidateContractValidationError(
        `self-assessment alone cannot verify attribute ${item.id}`,
      );
    }
    if (item.citizen_evidence !== "UNRESOLVED" && perception.length === 0) {
      throw new CandidateContractValidationError(
        `candidate public evidence must use perception records ${item.id}`,
      );
    }
  });
  (contradictions ?? []).forEach((item) => {
    if (!knownIds.has(item.subject_ref)) {
      throw new CandidateContractValidationError(
        `unknown contradiction subject ${item.subject_ref}`,
      );
    }
    resolve(item.evidence_refs, `contradiction ${item.id}`);
  });
  (developmentGoals ?? []).forEach((item) =>
    resolve(item.evidence_refs, `development goal ${item.id}`),
  );
  (reputationRisks ?? []).forEach((item) =>
    resolve(item.evidence_refs, `reputation risk ${item.id}`),
  );

  const state: Readonly<Record<CandidateSection, readonly [boolean, string]>> =
    {
      identity: [
        identity?.status === "VERIFIED",
        identity?.status === "VERIFIED"
          ? "IDENTITY_VERIFIED"
          : "IDENTITY_NOT_VERIFIED",
      ],
      biography: [
        biography?.status === "VERIFIED",
        biography?.status === "VERIFIED"
          ? "BIOGRAPHY_VERIFIED"
          : "BIOGRAPHY_NOT_VERIFIED",
      ],
      purpose: [
        purpose?.status === "VERIFIED",
        purpose?.status === "VERIFIED"
          ? "PURPOSE_VERIFIED"
          : "PURPOSE_NOT_VERIFIED",
      ],
      values: [
        values !== null &&
          values.length > 0 &&
          values.every((item) => item.status === "VERIFIED"),
        values !== null &&
        values.length > 0 &&
        values.every((item) => item.status === "VERIFIED")
          ? "VALUES_VERIFIED"
          : "VALUES_NOT_VERIFIED",
      ],
      attributes: [
        attributes !== null &&
          attributes.length > 0 &&
          attributes.every((item) => item.status === "VERIFIED"),
        attributes !== null &&
        attributes.length > 0 &&
        attributes.every((item) => item.status === "VERIFIED")
          ? "ATTRIBUTES_VERIFIED"
          : "ATTRIBUTES_NOT_VERIFIED",
      ],
      contradictions: [
        contradictions !== null &&
          contradictions.every((item) => item.status === "RESOLVED"),
        contradictions !== null &&
        contradictions.every((item) => item.status === "RESOLVED")
          ? "CONTRADICTIONS_REVIEWED"
          : "CONTRADICTIONS_UNRESOLVED",
      ],
      development_goals: [
        developmentGoals !== null && developmentGoals.length > 0,
        developmentGoals !== null && developmentGoals.length > 0
          ? "DEVELOPMENT_GOALS_DEFINED"
          : "DEVELOPMENT_GOALS_MISSING",
      ],
      reputation: [
        reputationRisks !== null &&
          (reputationRisks ?? []).every(
            (item) =>
              !(item.severity === "CRITICAL" || item.severity === "HIGH") ||
              item.status === "RESOLVED" ||
              item.status === "CLOSED",
          ),
        reputationRisks !== null &&
        (reputationRisks ?? []).every(
          (item) =>
            !(item.severity === "CRITICAL" || item.severity === "HIGH") ||
            item.status === "RESOLVED" ||
            item.status === "CLOSED",
        )
          ? "REPUTATION_RISKS_REVIEWED"
          : "REPUTATION_RISKS_UNRESOLVED",
      ],
    };
  const openCriticalHigh = (reputationRisks ?? []).filter(
    (item) =>
      (item.severity === "CRITICAL" || item.severity === "HIGH") &&
      item.status !== "RESOLVED" &&
      item.status !== "CLOSED",
  ).length;
  if (
    integer(
      source.open_critical_high_risks,
      "candidate workspace.open_critical_high_risks",
    ) !== openCriticalHigh
  ) {
    throw new CandidateContractValidationError(
      "candidate workspace risk summary is inconsistent",
    );
  }

  const expectedApprovable = SECTIONS.filter((section) => state[section][0]);
  const approvable = sections(
    source.approvable_sections,
    "candidate workspace.approvable_sections",
  );
  const approved = sections(
    source.current_approved_sections,
    "candidate workspace.current_approved_sections",
  );
  const required = sections(
    source.approvals_required,
    "candidate workspace.approvals_required",
  );
  if (
    approvable.length !== expectedApprovable.length ||
    approvable.some((item, index) => item !== expectedApprovable[index]) ||
    approved.some(
      (item) => !approvable.includes(item) || required.includes(item),
    ) ||
    required.some((item) => !approvable.includes(item)) ||
    approvable.some(
      (item) => !approved.includes(item) && !required.includes(item),
    )
  ) {
    throw new CandidateContractValidationError(
      "candidate workspace approval summary is inconsistent",
    );
  }
  const allEvidenceComplete = expectedApprovable.length === SECTIONS.length;
  const approvalsComplete = allEvidenceComplete && required.length === 0;

  const parsedChecks = array(source.checks, "candidate workspace.checks").map(
    (item, index) => parseCheck(item, `candidate workspace.checks[${index}]`),
  );
  if (
    parsedChecks.length !== CHECKS.length ||
    parsedChecks.some((item, index) => item.key !== CHECKS[index])
  ) {
    throw new CandidateContractValidationError(
      "candidate workspace checks are not canonical",
    );
  }
  if (
    parsedChecks.some((check) => {
      if (check.key === "approvals") {
        return (
          check.complete !== approvalsComplete ||
          check.reason_code !==
            (approvalsComplete
              ? "CURRENT_SECTION_APPROVALS_COMPLETE"
              : "CURRENT_SECTION_APPROVALS_REQUIRED")
        );
      }
      const expected = state[check.key];
      return (
        check.complete !== expected[0] || check.reason_code !== expected[1]
      );
    })
  ) {
    throw new CandidateContractValidationError(
      "candidate workspace checks contradict source fields",
    );
  }
  const completed = integer(
    source.completed_checks,
    "candidate workspace.completed_checks",
  );
  const total = integer(
    source.total_checks,
    "candidate workspace.total_checks",
    1,
  );
  if (
    total !== parsedChecks.length ||
    completed !== parsedChecks.filter((item) => item.complete).length
  ) {
    throw new CandidateContractValidationError(
      "candidate workspace summary does not match checks",
    );
  }

  const expectedStatus: CandidateWorkspaceProjection["status"] =
    identity === null || biography === null || purpose === null
      ? "SETUP_REQUIRED"
      : !allEvidenceComplete
        ? "UNDER_REVIEW"
        : !approvalsComplete
          ? "AWAITING_APPROVAL"
          : "INTERNALLY_APPROVED";
  const status = literal(
    source.status,
    [
      "SETUP_REQUIRED",
      "UNDER_REVIEW",
      "AWAITING_APPROVAL",
      "INTERNALLY_APPROVED",
    ] as const,
    "candidate workspace.status",
  );
  if (status !== expectedStatus) {
    throw new CandidateContractValidationError(
      "candidate workspace status is inconsistent",
    );
  }
  const nextBySection: Readonly<Record<CandidateSection, CandidateNextAction>> =
    {
      identity: "DEFINE_IDENTITY",
      biography: "DOCUMENT_BIOGRAPHY",
      purpose: "DEFINE_PURPOSE",
      values: "VERIFY_VALUES",
      attributes: "VERIFY_ATTRIBUTES",
      contradictions: "REVIEW_CONTRADICTIONS",
      development_goals: "DEFINE_DEVELOPMENT_GOALS",
      reputation: "REVIEW_REPUTATION_RISKS",
    };
  const incomplete = SECTIONS.find((section) => !state[section][0]);
  const expectedAction = incomplete
    ? nextBySection[incomplete]
    : required.length > 0
      ? "OBTAIN_SECTION_APPROVALS"
      : "CONTINUE_HUMAN_GOVERNANCE";
  const nextAction = literal(
    source.next_action,
    [
      "DEFINE_IDENTITY",
      "DOCUMENT_BIOGRAPHY",
      "DEFINE_PURPOSE",
      "VERIFY_VALUES",
      "VERIFY_ATTRIBUTES",
      "REVIEW_CONTRADICTIONS",
      "DEFINE_DEVELOPMENT_GOALS",
      "REVIEW_REPUTATION_RISKS",
      "OBTAIN_SECTION_APPROVALS",
      "CONTINUE_HUMAN_GOVERNANCE",
    ] as const,
    "candidate workspace.next_action",
  );
  if (nextAction !== expectedAction) {
    throw new CandidateContractValidationError(
      "candidate workspace next action is inconsistent",
    );
  }
  const limitations = array(
    source.limitation_codes,
    "candidate workspace.limitation_codes",
  ).map((item, index) =>
    literal(
      item,
      LIMITATIONS,
      `candidate workspace.limitation_codes[${index}]`,
    ),
  );
  if (
    limitations.length !== LIMITATIONS.length ||
    limitations.some((item, index) => item !== LIMITATIONS[index])
  ) {
    throw new CandidateContractValidationError(
      "candidate workspace mandatory limitations are missing",
    );
  }

  return {
    id: workspaceId,
    tenant_id: uuid(source.tenant_id, "candidate workspace.tenant_id"),
    campaign_id: uuid(source.campaign_id, "candidate workspace.campaign_id"),
    campaign_version: integer(
      source.campaign_version,
      "candidate workspace.campaign_version",
      1,
    ),
    campaign_status: literal(
      source.campaign_status,
      ["DRAFT", "ACTIVE"] as const,
      "candidate workspace.campaign_status",
    ),
    campaign_name: text(
      source.campaign_name,
      "candidate workspace.campaign_name",
    ),
    jurisdiction: text(source.jurisdiction, "candidate workspace.jurisdiction"),
    candidate_id: candidateId,
    display_name: text(source.display_name, "candidate workspace.display_name"),
    status,
    public_use_status: literal(
      source.public_use_status,
      ["BLOCKED"] as const,
      "candidate workspace.public_use_status",
    ),
    external_effects: literal(
      source.external_effects,
      ["NONE"] as const,
      "candidate workspace.external_effects",
    ),
    evidence,
    identity,
    biography,
    purpose,
    values,
    attributes,
    contradictions,
    development_goals: developmentGoals,
    reputation_risks: reputationRisks,
    checks: parsedChecks,
    completed_checks: completed,
    total_checks: total,
    approvable_sections: approvable,
    current_approved_sections: approved,
    approvals_required: required,
    open_critical_high_risks: openCriticalHigh,
    next_action: nextAction,
    limitation_codes: limitations,
    version: integer(source.version, "candidate workspace.version", 1),
    created_at: timestamp(source.created_at, "candidate workspace.created_at"),
    updated_at: timestamp(source.updated_at, "candidate workspace.updated_at"),
  };
}

export function parseCandidateWorkspaceReadEvidence(
  value: unknown,
): CandidateWorkspaceReadEvidence {
  const source = record(value, "candidate workspace evidence");
  exactKeys(
    source,
    ["workspace", "audit_event_id"],
    "candidate workspace evidence",
  );
  return {
    workspace: parseProjection(source.workspace),
    audit_event_id: uuid(
      source.audit_event_id,
      "candidate workspace evidence.audit_event_id",
    ),
  };
}
