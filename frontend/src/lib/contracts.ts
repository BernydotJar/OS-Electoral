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

export type GuidedIntakeBudgetStatus =
  | "NOT_ASSESSED"
  | "NO_DOCUMENT"
  | "ROUGH_RANGE"
  | "DOCUMENTED";

export type GuidedIntakeStatus =
  | "BLOCKED_BY_CAMPAIGN_SETUP"
  | "IN_PROGRESS"
  | "READY_FOR_RESEARCH";

export type GuidedIntakeCheckKey =
  | "campaign_operational_setup"
  | "office"
  | "candidate_project"
  | "current_team"
  | "current_assets"
  | "budget_status"
  | "known_unknowns"
  | "evidence_requirements";

export type GuidedIntakeNextAction =
  | "COMPLETE_CAMPAIGN_SETUP"
  | "DEFINE_TARGET_OFFICE"
  | "DESCRIBE_CANDIDATE_PROJECT"
  | "ASSESS_CURRENT_TEAM"
  | "ASSESS_CURRENT_ASSETS"
  | "ASSESS_BUDGET_EVIDENCE"
  | "RECORD_KNOWN_UNKNOWNS"
  | "DEFINE_EVIDENCE_REQUIREMENTS"
  | "BEGIN_RESEARCH";

export type GuidedIntakeResearchAction =
  | "VERIFY_OFFICE_AND_JURISDICTION_EVIDENCE"
  | "VALIDATE_CANDIDATE_PROJECT_EVIDENCE"
  | "ASSESS_TEAM_CAPACITY_GAPS"
  | "INVENTORY_ASSET_PROVENANCE"
  | "DOCUMENT_BUDGET_ASSUMPTIONS"
  | "RESEARCH_KNOWN_UNKNOWNS"
  | "COLLECT_REQUIRED_EVIDENCE";

export type GuidedIntakeLimitation =
  | "NOT_A_STRATEGY"
  | "NOT_A_HUMAN_APPROVAL"
  | "NO_CITIZEN_CONTACT_OR_PROFILING"
  | "NO_EXTERNAL_EFFECTS";

export type GuidedIntakeCheck = Readonly<{
  key: GuidedIntakeCheckKey;
  complete: boolean;
  reason_code: string;
}>;

export type GuidedIntakeProjection = Readonly<{
  id: UUID;
  tenant_id: UUID;
  campaign_id: UUID;
  campaign_version: number;
  campaign_status: "DRAFT" | "ACTIVE";
  campaign_name: string;
  jurisdiction: string;
  stage: string;
  active_workspace_count: number;
  readiness_scope: "GUIDED_INTAKE_ONLY";
  status: GuidedIntakeStatus;
  ready_for_research: boolean;
  office: string | null;
  candidate_project: string | null;
  current_team: readonly string[] | null;
  current_assets: readonly string[] | null;
  budget_status: GuidedIntakeBudgetStatus;
  known_unknowns: readonly string[] | null;
  evidence_requirements: readonly string[] | null;
  completed_checks: number;
  total_checks: number;
  next_action: GuidedIntakeNextAction;
  checks: readonly GuidedIntakeCheck[];
  research_first_actions: readonly GuidedIntakeResearchAction[];
  limitation_codes: readonly GuidedIntakeLimitation[];
  version: number;
  created_at: string;
  updated_at: string;
}>;

export type GuidedIntakeReadEvidence = Readonly<{
  intake: GuidedIntakeProjection;
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
