export type UUID = string;

export type EffectivePermissionGrant = Readonly<{
  grant_id: UUID;
  campaign_id: UUID | null;
  workspace_id: UUID | null;
  action: string;
  resource_type: string;
  resource_id: string;
  purpose: string;
  approval_receipt_id: string;
}>;

export type EffectiveMembership = Readonly<{
  membership_id: UUID;
  campaign_id: UUID | null;
  roles: readonly string[];
  grants: readonly EffectivePermissionGrant[];
}>;

export type MeResponse = Readonly<{
  principal_id: string;
  subject: string;
  issuer: string;
  display_name: string | null;
  email: string | null;
  authenticated_at: string;
  application_memberships: readonly Record<string, string>[];
  authorization_status: "NOT_LOADED";
}>;

export type TenantMeResponse = Readonly<{
  principal_id: UUID;
  tenant_id: UUID;
  subject: string;
  issuer: string;
  display_name: string | null;
  email: string | null;
  authenticated_at: string;
  evaluated_at: string;
  application_memberships: readonly EffectiveMembership[];
  authorization_status: "LOADED";
}>;

export type CampaignProjection = Readonly<{
  id: UUID;
  tenant_id: UUID;
  slug: string;
  name: string;
  jurisdiction: string;
  stage: string;
  status: "DRAFT" | "ACTIVE";
  version: number;
}>;

export type CampaignPage = Readonly<{
  items: readonly CampaignProjection[];
  next_cursor: UUID | null;
}>;

export type CampaignReadinessCheck = Readonly<{
  key: "campaign_name" | "jurisdiction" | "campaign_stage" | "active_workspace";
  complete: boolean;
  reason_code: string;
}>;

export type CampaignReadinessProjection = Readonly<{
  tenant_id: UUID;
  campaign_id: UUID;
  campaign_version: number;
  campaign_status: "DRAFT" | "ACTIVE";
  readiness_scope: "OPERATIONAL_SETUP_ONLY";
  status:
    | "NEEDS_CAMPAIGN_METADATA"
    | "NEEDS_CAMPAIGN_WORKSPACE"
    | "READY_FOR_GUIDED_INTAKE";
  ready_for_guided_intake: boolean;
  completed_checks: number;
  total_checks: number;
  active_workspace_count: number;
  next_action:
    | "COMPLETE_CAMPAIGN_METADATA"
    | "CREATE_CAMPAIGN_WORKSPACE"
    | "BEGIN_GUIDED_INTAKE";
  checks: readonly CampaignReadinessCheck[];
  limitation_codes: readonly [
    "NOT_A_HUMAN_APPROVAL",
    "NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT",
  ];
}>;

export type CampaignReadinessEvidence = Readonly<{
  readiness: CampaignReadinessProjection;
  audit_event_id: UUID;
}>;

export type ProblemDetail = Readonly<{
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
  code: string;
  correlation_id: string;
}>;
