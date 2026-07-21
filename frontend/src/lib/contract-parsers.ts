import type {
  CampaignPage,
  CampaignProjection,
  CampaignReadinessCheck,
  CampaignReadinessEvidence,
  CampaignReadinessProjection,
  EffectiveMembership,
  EffectivePermissionGrant,
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
