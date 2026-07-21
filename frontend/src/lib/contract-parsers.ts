import type {
  CampaignPage,
  CampaignProjection,
  CampaignReadinessCheck,
  CampaignReadinessEvidence,
  CampaignReadinessProjection,
  EffectiveMembership,
  EffectivePermissionGrant,
  GuidedIntakeCheck,
  GuidedIntakeCheckKey,
  GuidedIntakeLimitation,
  GuidedIntakeNextAction,
  GuidedIntakeProjection,
  GuidedIntakeReadEvidence,
  GuidedIntakeResearchAction,
  MeResponse,
  TenantMeResponse,
} from "@/lib/contracts";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export class ContractValidationError extends Error {}

type JsonRecord = Record<string, unknown>;

function record(value: unknown, label: string): JsonRecord {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new ContractValidationError(`${label} must be an object`);
  }
  return value as JsonRecord;
}

function exactKeys(value: JsonRecord, allowed: readonly string[], label: string): void {
  const extras = Object.keys(value).filter((key) => !allowed.includes(key));
  if (extras.length > 0) {
    throw new ContractValidationError(`${label} contains unexpected fields`);
  }
}

function string(value: unknown, label: string): string {
  if (typeof value !== "string" || value.length === 0) {
    throw new ContractValidationError(`${label} must be a non-empty string`);
  }
  return value;
}

function nullableString(value: unknown, label: string): string | null {
  if (value === null) return null;
  return string(value, label);
}

function uuid(value: unknown, label: string): string {
  const candidate = string(value, label);
  if (!UUID_PATTERN.test(candidate)) {
    throw new ContractValidationError(`${label} must be a UUID`);
  }
  return candidate;
}

function integer(value: unknown, label: string, minimum = 0): number {
  if (!Number.isInteger(value) || (value as number) < minimum) {
    throw new ContractValidationError(`${label} must be an integer >= ${minimum}`);
  }
  return value as number;
}

function boolean(value: unknown, label: string): boolean {
  if (typeof value !== "boolean") {
    throw new ContractValidationError(`${label} must be a boolean`);
  }
  return value;
}

function array(value: unknown, label: string): readonly unknown[] {
  if (!Array.isArray(value)) throw new ContractValidationError(`${label} must be an array`);
  return value;
}

function nullableStringArray(value: unknown, label: string): readonly string[] | null {
  if (value === null) return null;
  return array(value, label).map((item, index) => string(item, `${label}[${index}]`));
}

function isoTimestamp(value: unknown, label: string): string {
  const candidate = string(value, label);
  const timestamp = Date.parse(candidate);
  if (!Number.isFinite(timestamp) || !/(?:Z|[+-]\d{2}:\d{2})$/.test(candidate)) {
    throw new ContractValidationError(`${label} must be a timezone-aware timestamp`);
  }
  return candidate;
}

function literal<T extends string>(value: unknown, allowed: readonly T[], label: string): T {
  const candidate = string(value, label);
  if (!allowed.includes(candidate as T)) {
    throw new ContractValidationError(`${label} is not supported`);
  }
  return candidate as T;
}

function parseGrant(value: unknown, label: string): EffectivePermissionGrant {
  const source = record(value, label);
  exactKeys(
    source,
    [
      "grant_id",
      "campaign_id",
      "workspace_id",
      "action",
      "resource_type",
      "resource_id",
      "purpose",
      "approval_receipt_id",
    ],
    label,
  );
  const campaignId = source.campaign_id === null ? null : uuid(source.campaign_id, `${label}.campaign_id`);
  const workspaceId =
    source.workspace_id === null ? null : uuid(source.workspace_id, `${label}.workspace_id`);
  if (workspaceId !== null && campaignId === null) {
    throw new ContractValidationError(`${label} workspace scope requires campaign scope`);
  }
  return {
    grant_id: uuid(source.grant_id, `${label}.grant_id`),
    campaign_id: campaignId,
    workspace_id: workspaceId,
    action: string(source.action, `${label}.action`),
    resource_type: string(source.resource_type, `${label}.resource_type`),
    resource_id: string(source.resource_id, `${label}.resource_id`),
    purpose: string(source.purpose, `${label}.purpose`),
    approval_receipt_id: string(source.approval_receipt_id, `${label}.approval_receipt_id`),
  };
}

function parseMembership(value: unknown, label: string): EffectiveMembership {
  const source = record(value, label);
  exactKeys(source, ["membership_id", "campaign_id", "roles", "grants"], label);
  const campaignId = source.campaign_id === null ? null : uuid(source.campaign_id, `${label}.campaign_id`);
  const grants = array(source.grants, `${label}.grants`).map((grant, index) =>
    parseGrant(grant, `${label}.grants[${index}]`),
  );
  if (campaignId !== null && grants.some((grant) => grant.campaign_id !== campaignId)) {
    throw new ContractValidationError(`${label} contains a cross-campaign grant`);
  }
  return {
    membership_id: uuid(source.membership_id, `${label}.membership_id`),
    campaign_id: campaignId,
    roles: array(source.roles, `${label}.roles`).map((role, index) =>
      string(role, `${label}.roles[${index}]`),
    ),
    grants,
  };
}

export function parseMe(value: unknown): MeResponse {
  const source = record(value, "identity");
  exactKeys(
    source,
    [
      "principal_id",
      "subject",
      "issuer",
      "display_name",
      "email",
      "authenticated_at",
      "application_memberships",
      "authorization_status",
    ],
    "identity",
  );
  const memberships = array(source.application_memberships, "identity.application_memberships");
  if (memberships.length !== 0) {
    throw new ContractValidationError("identity-only response must not contain memberships");
  }
  return {
    principal_id: string(source.principal_id, "identity.principal_id"),
    subject: string(source.subject, "identity.subject"),
    issuer: string(source.issuer, "identity.issuer"),
    display_name: nullableString(source.display_name, "identity.display_name"),
    email: nullableString(source.email, "identity.email"),
    authenticated_at: isoTimestamp(source.authenticated_at, "identity.authenticated_at"),
    application_memberships: memberships as readonly Record<string, string>[],
    authorization_status: literal(
      source.authorization_status,
      ["NOT_LOADED"] as const,
      "identity.authorization_status",
    ),
  };
}

export function parseTenantMe(value: unknown): TenantMeResponse {
  const source = record(value, "tenant identity");
  exactKeys(
    source,
    [
      "principal_id",
      "tenant_id",
      "subject",
      "issuer",
      "display_name",
      "email",
      "authenticated_at",
      "evaluated_at",
      "application_memberships",
      "authorization_status",
    ],
    "tenant identity",
  );
  const memberships = array(
    source.application_memberships,
    "tenant identity.application_memberships",
  ).map((membership, index) =>
    parseMembership(membership, `tenant identity.application_memberships[${index}]`),
  );
  if (memberships.length === 0) {
    throw new ContractValidationError("tenant identity requires an active membership");
  }
  return {
    principal_id: uuid(source.principal_id, "tenant identity.principal_id"),
    tenant_id: uuid(source.tenant_id, "tenant identity.tenant_id"),
    subject: string(source.subject, "tenant identity.subject"),
    issuer: string(source.issuer, "tenant identity.issuer"),
    display_name: nullableString(source.display_name, "tenant identity.display_name"),
    email: nullableString(source.email, "tenant identity.email"),
    authenticated_at: isoTimestamp(source.authenticated_at, "tenant identity.authenticated_at"),
    evaluated_at: isoTimestamp(source.evaluated_at, "tenant identity.evaluated_at"),
    application_memberships: memberships,
    authorization_status: literal(
      source.authorization_status,
      ["LOADED"] as const,
      "tenant identity.authorization_status",
    ),
  };
}

function parseCampaign(value: unknown, label: string): CampaignProjection {
  const source = record(value, label);
  exactKeys(
    source,
    ["id", "tenant_id", "slug", "name", "jurisdiction", "stage", "status", "version"],
    label,
  );
  return {
    id: uuid(source.id, `${label}.id`),
    tenant_id: uuid(source.tenant_id, `${label}.tenant_id`),
    slug: string(source.slug, `${label}.slug`),
    name: string(source.name, `${label}.name`),
    jurisdiction: string(source.jurisdiction, `${label}.jurisdiction`),
    stage: string(source.stage, `${label}.stage`),
    status: literal(source.status, ["DRAFT", "ACTIVE"] as const, `${label}.status`),
    version: integer(source.version, `${label}.version`, 1),
  };
}

export function parseCampaignPage(
  value: unknown,
  expectedTenantId?: string,
): CampaignPage {
  const source = record(value, "campaign page");
  exactKeys(source, ["items", "next_cursor"], "campaign page");
  const items = array(source.items, "campaign page.items").map((item, index) =>
    parseCampaign(item, `campaign page.items[${index}]`),
  );
  if (expectedTenantId !== undefined) {
    const tenantId = uuid(expectedTenantId, "campaign page expected tenant");
    if (items.some((item) => item.tenant_id !== tenantId)) {
      throw new ContractValidationError("campaign page contains a cross-tenant campaign");
    }
  }
  return {
    items,
    next_cursor:
      source.next_cursor === null ? null : uuid(source.next_cursor, "campaign page.next_cursor"),
  };
}

function parseReadinessCheck(value: unknown, label: string): CampaignReadinessCheck {
  const source = record(value, label);
  exactKeys(source, ["key", "complete", "reason_code"], label);
  return {
    key: literal(
      source.key,
      ["campaign_name", "jurisdiction", "campaign_stage", "active_workspace"] as const,
      `${label}.key`,
    ),
    complete: boolean(source.complete, `${label}.complete`),
    reason_code: string(source.reason_code, `${label}.reason_code`),
  };
}

function parseReadinessProjection(value: unknown): CampaignReadinessProjection {
  const source = record(value, "readiness");
  exactKeys(
    source,
    [
      "tenant_id",
      "campaign_id",
      "campaign_version",
      "campaign_status",
      "readiness_scope",
      "status",
      "ready_for_guided_intake",
      "completed_checks",
      "total_checks",
      "active_workspace_count",
      "next_action",
      "checks",
      "limitation_codes",
    ],
    "readiness",
  );
  const checks = array(source.checks, "readiness.checks").map((check, index) =>
    parseReadinessCheck(check, `readiness.checks[${index}]`),
  );
  const expectedKeys = [
    "campaign_name",
    "jurisdiction",
    "campaign_stage",
    "active_workspace",
  ] as const;
  if (checks.length !== expectedKeys.length || checks.some((check, index) => check.key !== expectedKeys[index])) {
    throw new ContractValidationError("readiness checks are not canonical");
  }
  const completedChecks = integer(source.completed_checks, "readiness.completed_checks");
  const totalChecks = integer(source.total_checks, "readiness.total_checks", 1);
  if (totalChecks !== checks.length || completedChecks !== checks.filter((check) => check.complete).length) {
    throw new ContractValidationError("readiness summary does not match checks");
  }
  const limitations = array(source.limitation_codes, "readiness.limitation_codes").map(
    (limitation, index) => string(limitation, `readiness.limitation_codes[${index}]`),
  );
  if (
    limitations.length !== 2 ||
    limitations[0] !== "NOT_A_HUMAN_APPROVAL" ||
    limitations[1] !== "NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT"
  ) {
    throw new ContractValidationError("readiness mandatory limitations are missing");
  }
  const ready = boolean(source.ready_for_guided_intake, "readiness.ready_for_guided_intake");
  const status = literal(
    source.status,
    ["NEEDS_CAMPAIGN_METADATA", "NEEDS_CAMPAIGN_WORKSPACE", "READY_FOR_GUIDED_INTAKE"] as const,
    "readiness.status",
  );
  if (ready !== (status === "READY_FOR_GUIDED_INTAKE")) {
    throw new ContractValidationError("readiness status and boolean disagree");
  }
  return {
    tenant_id: uuid(source.tenant_id, "readiness.tenant_id"),
    campaign_id: uuid(source.campaign_id, "readiness.campaign_id"),
    campaign_version: integer(source.campaign_version, "readiness.campaign_version", 1),
    campaign_status: literal(
      source.campaign_status,
      ["DRAFT", "ACTIVE"] as const,
      "readiness.campaign_status",
    ),
    readiness_scope: literal(
      source.readiness_scope,
      ["OPERATIONAL_SETUP_ONLY"] as const,
      "readiness.readiness_scope",
    ),
    status,
    ready_for_guided_intake: ready,
    completed_checks: completedChecks,
    total_checks: totalChecks,
    active_workspace_count: integer(
      source.active_workspace_count,
      "readiness.active_workspace_count",
    ),
    next_action: literal(
      source.next_action,
      ["COMPLETE_CAMPAIGN_METADATA", "CREATE_CAMPAIGN_WORKSPACE", "BEGIN_GUIDED_INTAKE"] as const,
      "readiness.next_action",
    ),
    checks,
    limitation_codes: [
      "NOT_A_HUMAN_APPROVAL",
      "NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT",
    ],
  };
}

export function parseReadinessEvidence(value: unknown): CampaignReadinessEvidence {
  const source = record(value, "readiness evidence");
  exactKeys(source, ["readiness", "audit_event_id"], "readiness evidence");
  return {
    readiness: parseReadinessProjection(source.readiness),
    audit_event_id: uuid(source.audit_event_id, "readiness evidence.audit_event_id"),
  };
}

const GUIDED_INTAKE_CHECK_ORDER = [
  "campaign_operational_setup",
  "office",
  "candidate_project",
  "current_team",
  "current_assets",
  "budget_status",
  "known_unknowns",
  "evidence_requirements",
] as const satisfies readonly GuidedIntakeCheckKey[];

const GUIDED_INTAKE_NEXT_ACTIONS = [
  "COMPLETE_CAMPAIGN_SETUP",
  "DEFINE_TARGET_OFFICE",
  "DESCRIBE_CANDIDATE_PROJECT",
  "ASSESS_CURRENT_TEAM",
  "ASSESS_CURRENT_ASSETS",
  "ASSESS_BUDGET_EVIDENCE",
  "RECORD_KNOWN_UNKNOWNS",
  "DEFINE_EVIDENCE_REQUIREMENTS",
  "BEGIN_RESEARCH",
] as const satisfies readonly GuidedIntakeNextAction[];

const GUIDED_INTAKE_RESEARCH_ACTIONS = [
  "VERIFY_OFFICE_AND_JURISDICTION_EVIDENCE",
  "VALIDATE_CANDIDATE_PROJECT_EVIDENCE",
  "ASSESS_TEAM_CAPACITY_GAPS",
  "INVENTORY_ASSET_PROVENANCE",
  "DOCUMENT_BUDGET_ASSUMPTIONS",
  "RESEARCH_KNOWN_UNKNOWNS",
  "COLLECT_REQUIRED_EVIDENCE",
] as const satisfies readonly GuidedIntakeResearchAction[];

const GUIDED_INTAKE_LIMITATIONS = [
  "NOT_A_STRATEGY",
  "NOT_A_HUMAN_APPROVAL",
  "NO_CITIZEN_CONTACT_OR_PROFILING",
  "NO_EXTERNAL_EFFECTS",
] as const satisfies readonly GuidedIntakeLimitation[];

const GUIDED_INTAKE_NEXT_ACTION_BY_CHECK: Readonly<
  Record<GuidedIntakeCheckKey, GuidedIntakeNextAction>
> = {
  campaign_operational_setup: "COMPLETE_CAMPAIGN_SETUP",
  office: "DEFINE_TARGET_OFFICE",
  candidate_project: "DESCRIBE_CANDIDATE_PROJECT",
  current_team: "ASSESS_CURRENT_TEAM",
  current_assets: "ASSESS_CURRENT_ASSETS",
  budget_status: "ASSESS_BUDGET_EVIDENCE",
  known_unknowns: "RECORD_KNOWN_UNKNOWNS",
  evidence_requirements: "DEFINE_EVIDENCE_REQUIREMENTS",
};

function parseGuidedIntakeCheck(value: unknown, label: string): GuidedIntakeCheck {
  const source = record(value, label);
  exactKeys(source, ["key", "complete", "reason_code"], label);
  return {
    key: literal(source.key, GUIDED_INTAKE_CHECK_ORDER, `${label}.key`),
    complete: boolean(source.complete, `${label}.complete`),
    reason_code: string(source.reason_code, `${label}.reason_code`),
  };
}

function parseGuidedIntakeProjection(value: unknown): GuidedIntakeProjection {
  const source = record(value, "guided intake");
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
      "stage",
      "active_workspace_count",
      "readiness_scope",
      "status",
      "ready_for_research",
      "office",
      "candidate_project",
      "current_team",
      "current_assets",
      "budget_status",
      "known_unknowns",
      "evidence_requirements",
      "completed_checks",
      "total_checks",
      "next_action",
      "checks",
      "research_first_actions",
      "limitation_codes",
      "version",
      "created_at",
      "updated_at",
    ],
    "guided intake",
  );

  const campaignName = string(source.campaign_name, "guided intake.campaign_name");
  const jurisdiction = string(source.jurisdiction, "guided intake.jurisdiction");
  const stage = string(source.stage, "guided intake.stage");
  const activeWorkspaceCount = integer(
    source.active_workspace_count,
    "guided intake.active_workspace_count",
  );
  const office = nullableString(source.office, "guided intake.office");
  const candidateProject = nullableString(
    source.candidate_project,
    "guided intake.candidate_project",
  );
  const currentTeam = nullableStringArray(source.current_team, "guided intake.current_team");
  const currentAssets = nullableStringArray(source.current_assets, "guided intake.current_assets");
  const budgetStatus = literal(
    source.budget_status,
    ["NOT_ASSESSED", "NO_DOCUMENT", "ROUGH_RANGE", "DOCUMENTED"] as const,
    "guided intake.budget_status",
  );
  const knownUnknowns = nullableStringArray(
    source.known_unknowns,
    "guided intake.known_unknowns",
  );
  const evidenceRequirements = nullableStringArray(
    source.evidence_requirements,
    "guided intake.evidence_requirements",
  );

  const checks = array(source.checks, "guided intake.checks").map((check, index) =>
    parseGuidedIntakeCheck(check, `guided intake.checks[${index}]`),
  );
  if (
    checks.length !== GUIDED_INTAKE_CHECK_ORDER.length ||
    checks.some((check, index) => check.key !== GUIDED_INTAKE_CHECK_ORDER[index])
  ) {
    throw new ContractValidationError("guided intake checks are not canonical");
  }

  const campaignOperationalSetupComplete =
    campaignName.trim().length > 0 &&
    jurisdiction.trim().length > 0 &&
    stage.trim().length > 0 &&
    activeWorkspaceCount > 0;
  const expectedChecks: Readonly<Record<GuidedIntakeCheckKey, readonly [boolean, string]>> = {
    campaign_operational_setup: [
      campaignOperationalSetupComplete,
      campaignOperationalSetupComplete
        ? "CAMPAIGN_OPERATIONAL_SETUP_COMPLETE"
        : "CAMPAIGN_OPERATIONAL_SETUP_INCOMPLETE",
    ],
    office: [office !== null, office !== null ? "TARGET_OFFICE_DEFINED" : "TARGET_OFFICE_MISSING"],
    candidate_project: [
      candidateProject !== null,
      candidateProject !== null ? "CANDIDATE_PROJECT_DESCRIBED" : "CANDIDATE_PROJECT_MISSING",
    ],
    current_team: [
      currentTeam !== null,
      currentTeam !== null ? "CURRENT_TEAM_ASSESSED" : "CURRENT_TEAM_NOT_ASSESSED",
    ],
    current_assets: [
      currentAssets !== null,
      currentAssets !== null ? "CURRENT_ASSETS_ASSESSED" : "CURRENT_ASSETS_NOT_ASSESSED",
    ],
    budget_status: [
      budgetStatus !== "NOT_ASSESSED",
      budgetStatus !== "NOT_ASSESSED"
        ? "BUDGET_EVIDENCE_ASSESSED"
        : "BUDGET_EVIDENCE_NOT_ASSESSED",
    ],
    known_unknowns: [
      knownUnknowns !== null && knownUnknowns.length > 0,
      knownUnknowns !== null && knownUnknowns.length > 0
        ? "KNOWN_UNKNOWNS_RECORDED"
        : "KNOWN_UNKNOWNS_MISSING",
    ],
    evidence_requirements: [
      evidenceRequirements !== null && evidenceRequirements.length > 0,
      evidenceRequirements !== null && evidenceRequirements.length > 0
        ? "EVIDENCE_REQUIREMENTS_DEFINED"
        : "EVIDENCE_REQUIREMENTS_MISSING",
    ],
  };
  if (
    checks.some((check) => {
      const [complete, reasonCode] = expectedChecks[check.key];
      return check.complete !== complete || check.reason_code !== reasonCode;
    })
  ) {
    throw new ContractValidationError("guided intake checks contradict source fields");
  }

  const completedChecks = integer(source.completed_checks, "guided intake.completed_checks");
  const totalChecks = integer(source.total_checks, "guided intake.total_checks", 1);
  if (
    totalChecks !== checks.length ||
    completedChecks !== checks.filter((check) => check.complete).length
  ) {
    throw new ContractValidationError("guided intake summary does not match checks");
  }

  const ready = boolean(source.ready_for_research, "guided intake.ready_for_research");
  const status = literal(
    source.status,
    ["BLOCKED_BY_CAMPAIGN_SETUP", "IN_PROGRESS", "READY_FOR_RESEARCH"] as const,
    "guided intake.status",
  );
  if (ready !== (status === "READY_FOR_RESEARCH")) {
    throw new ContractValidationError("guided intake status and boolean disagree");
  }
  const campaignSetupComplete = checks[0]?.complete === true;
  if (
    (campaignSetupComplete && status === "BLOCKED_BY_CAMPAIGN_SETUP") ||
    (!campaignSetupComplete && status !== "BLOCKED_BY_CAMPAIGN_SETUP") ||
    (ready && completedChecks !== totalChecks) ||
    (!ready && completedChecks === totalChecks)
  ) {
    throw new ContractValidationError("guided intake status is inconsistent with checks");
  }

  const nextAction = literal(
    source.next_action,
    GUIDED_INTAKE_NEXT_ACTIONS,
    "guided intake.next_action",
  );
  const firstIncomplete = checks.find((check) => !check.complete);
  const expectedNextAction = ready
    ? "BEGIN_RESEARCH"
    : firstIncomplete
      ? GUIDED_INTAKE_NEXT_ACTION_BY_CHECK[firstIncomplete.key]
      : null;
  if (expectedNextAction === null || nextAction !== expectedNextAction) {
    throw new ContractValidationError("guided intake next action is inconsistent");
  }

  const researchActions = array(
    source.research_first_actions,
    "guided intake.research_first_actions",
  ).map((action, index) =>
    literal(
      action,
      GUIDED_INTAKE_RESEARCH_ACTIONS,
      `guided intake.research_first_actions[${index}]`,
    ),
  );
  if (!ready && researchActions.length > 0) {
    throw new ContractValidationError("guided intake research actions require ready intake");
  }
  if (
    ready &&
    (researchActions.length !== GUIDED_INTAKE_RESEARCH_ACTIONS.length ||
      researchActions.some((action, index) => action !== GUIDED_INTAKE_RESEARCH_ACTIONS[index]))
  ) {
    throw new ContractValidationError("guided intake research actions are not canonical");
  }

  const limitations = array(source.limitation_codes, "guided intake.limitation_codes").map(
    (limitation, index) =>
      literal(
        limitation,
        GUIDED_INTAKE_LIMITATIONS,
        `guided intake.limitation_codes[${index}]`,
      ),
  );
  if (
    limitations.length !== GUIDED_INTAKE_LIMITATIONS.length ||
    limitations.some((limitation, index) => limitation !== GUIDED_INTAKE_LIMITATIONS[index])
  ) {
    throw new ContractValidationError("guided intake mandatory limitations are missing");
  }

  return {
    id: uuid(source.id, "guided intake.id"),
    tenant_id: uuid(source.tenant_id, "guided intake.tenant_id"),
    campaign_id: uuid(source.campaign_id, "guided intake.campaign_id"),
    campaign_version: integer(source.campaign_version, "guided intake.campaign_version", 1),
    campaign_status: literal(
      source.campaign_status,
      ["DRAFT", "ACTIVE"] as const,
      "guided intake.campaign_status",
    ),
    campaign_name: campaignName,
    jurisdiction,
    stage,
    active_workspace_count: activeWorkspaceCount,
    readiness_scope: literal(
      source.readiness_scope,
      ["GUIDED_INTAKE_ONLY"] as const,
      "guided intake.readiness_scope",
    ),
    status,
    ready_for_research: ready,
    office,
    candidate_project: candidateProject,
    current_team: currentTeam,
    current_assets: currentAssets,
    budget_status: budgetStatus,
    known_unknowns: knownUnknowns,
    evidence_requirements: evidenceRequirements,
    completed_checks: completedChecks,
    total_checks: totalChecks,
    next_action: nextAction,
    checks,
    research_first_actions: researchActions,
    limitation_codes: limitations,
    version: integer(source.version, "guided intake.version", 1),
    created_at: isoTimestamp(source.created_at, "guided intake.created_at"),
    updated_at: isoTimestamp(source.updated_at, "guided intake.updated_at"),
  };
}

export function parseGuidedIntakeReadEvidence(value: unknown): GuidedIntakeReadEvidence {
  const source = record(value, "guided intake evidence");
  exactKeys(source, ["intake", "audit_event_id"], "guided intake evidence");
  return {
    intake: parseGuidedIntakeProjection(source.intake),
    audit_event_id: uuid(source.audit_event_id, "guided intake evidence.audit_event_id"),
  };
}

export { parseCandidateWorkspaceReadEvidence } from "@/lib/candidate-contract-parser";
