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

export type CandidateEvidenceClassification =
  | "OFFICIAL_SOURCE"
  | "CAMPAIGN_RESEARCH"
  | "PERCEPTION"
  | "HYPOTHESIS"
  | "UNKNOWN";

export type CandidateEvidenceStatus = "ACCEPTED" | "VERIFIED" | "READY" | "REJECTED" | "EXPIRED";
export type CandidateClaimStatus =
  | "UNKNOWN"
  | "SELF_REPORTED"
  | "UNDER_REVIEW"
  | "EVIDENCE_PARTIAL"
  | "VERIFIED"
  | "REJECTED"
  | "CONTRADICTED";
export type CandidateSection =
  | "identity"
  | "biography"
  | "purpose"
  | "values"
  | "attributes"
  | "contradictions"
  | "development_goals"
  | "reputation";
export type CandidateCheckKey = CandidateSection | "approvals";
export type CandidateWorkspaceStatus =
  | "SETUP_REQUIRED"
  | "UNDER_REVIEW"
  | "AWAITING_APPROVAL"
  | "INTERNALLY_APPROVED";
export type CandidateNextAction =
  | "DEFINE_IDENTITY"
  | "DOCUMENT_BIOGRAPHY"
  | "DEFINE_PURPOSE"
  | "VERIFY_VALUES"
  | "VERIFY_ATTRIBUTES"
  | "REVIEW_CONTRADICTIONS"
  | "DEFINE_DEVELOPMENT_GOALS"
  | "REVIEW_REPUTATION_RISKS"
  | "OBTAIN_SECTION_APPROVALS"
  | "CONTINUE_HUMAN_GOVERNANCE";
export type CandidateLimitation =
  | "NOT_PUBLIC_POSITIONING_APPROVAL"
  | "NOT_A_STRATEGY"
  | "NO_VOTER_PROFILING"
  | "NO_EXTERNAL_EFFECTS"
  | "HUMAN_REVIEW_REQUIRED";

export type CandidateEvidence = Readonly<{
  id: UUID;
  classification: CandidateEvidenceClassification;
  status: CandidateEvidenceStatus;
  title: string;
  source_reference: string;
  source_authority: string | null;
  jurisdiction: string | null;
  excerpt: string | null;
  observed_at: string | null;
}>;

export type CandidateClaim = Readonly<{
  id: UUID;
  label: string;
  claim: string;
  status: CandidateClaimStatus;
  classification: CandidateEvidenceClassification;
  evidence_refs: readonly UUID[];
}>;

export type CandidateAttribute = Readonly<{
  id: UUID;
  name: string;
  claim: string;
  status: CandidateClaimStatus;
  candidate_self_assessment: "YES" | "NO" | "UNKNOWN";
  team_assessment: "YES" | "PARTIAL" | "NO" | "UNKNOWN";
  citizen_evidence: "SUPPORTED" | "PARTIAL" | "UNRESOLVED" | "CONTRADICTED";
  evidence_refs: readonly UUID[];
  perception_refs: readonly UUID[];
  contradiction_refs: readonly UUID[];
  risk: string;
}>;

export type CandidateContradiction = Readonly<{
  id: UUID;
  subject_ref: UUID;
  description: string;
  status: "OPEN" | "UNDER_REVIEW" | "RESOLVED";
  evidence_refs: readonly UUID[];
}>;

export type CandidateDevelopmentGoal = Readonly<{
  id: UUID;
  area: string;
  objective: string;
  status: "OPEN" | "IN_PROGRESS" | "COMPLETE";
  evidence_refs: readonly UUID[];
}>;

export type CandidateReputationRisk = Readonly<{
  id: UUID;
  title: string;
  description: string;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  status: "OPEN" | "MITIGATING" | "RESOLVED" | "CLOSED";
  decision_required: boolean;
  evidence_refs: readonly UUID[];
}>;

export type CandidateWorkspaceCheck = Readonly<{
  key: CandidateCheckKey;
  complete: boolean;
  reason_code: string;
}>;

export type CandidateWorkspaceProjection = Readonly<{
  id: UUID;
  tenant_id: UUID;
  campaign_id: UUID;
  campaign_version: number;
  campaign_status: "DRAFT" | "ACTIVE";
  campaign_name: string;
  jurisdiction: string;
  candidate_id: UUID;
  display_name: string;
  status: CandidateWorkspaceStatus;
  public_use_status: "BLOCKED";
  external_effects: "NONE";
  evidence: readonly CandidateEvidence[];
  identity: CandidateClaim | null;
  biography: CandidateClaim | null;
  purpose: CandidateClaim | null;
  values: readonly CandidateClaim[] | null;
  attributes: readonly CandidateAttribute[] | null;
  contradictions: readonly CandidateContradiction[] | null;
  development_goals: readonly CandidateDevelopmentGoal[] | null;
  reputation_risks: readonly CandidateReputationRisk[] | null;
  checks: readonly CandidateWorkspaceCheck[];
  completed_checks: number;
  total_checks: number;
  approvable_sections: readonly CandidateSection[];
  current_approved_sections: readonly CandidateSection[];
  approvals_required: readonly CandidateSection[];
  open_critical_high_risks: number;
  next_action: CandidateNextAction;
  limitation_codes: readonly CandidateLimitation[];
  version: number;
  created_at: string;
  updated_at: string;
}>;

export type CandidateWorkspaceReadEvidence = Readonly<{
  workspace: CandidateWorkspaceProjection;
  audit_event_id: UUID;
}>;
