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
  "NOT_ASSESSED" | "NO_DOCUMENT" | "ROUGH_RANGE" | "DOCUMENTED";

export type GuidedIntakeStatus =
  "BLOCKED_BY_CAMPAIGN_SETUP" | "IN_PROGRESS" | "READY_FOR_RESEARCH";

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

export type GuidedIntakeStartEvidence = Readonly<{
  intake: GuidedIntakeProjection;
  audit_event_id: UUID;
  outbox_event_id: UUID | null;
  created: boolean;
}>;

export type GuidedIntakeUpdateInput = Readonly<{
  office?: string | null;
  candidate_project?: string | null;
  current_team?: readonly string[] | null;
  current_assets?: readonly string[] | null;
  budget_status?: GuidedIntakeBudgetStatus;
  known_unknowns?: readonly string[] | null;
  evidence_requirements?: readonly string[] | null;
}>;

export type GuidedIntakeUpdateEvidence = Readonly<{
  intake: GuidedIntakeProjection;
  audit_event_id: UUID;
  outbox_event_id: UUID;
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

export type CandidateEvidenceStatus =
  "ACCEPTED" | "VERIFIED" | "READY" | "REJECTED" | "EXPIRED";
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

export type TeamOrganizationTemplate =
  "LEAN_CAMPAIGN" | "FULL_CAMPAIGN" | "CUSTOM";
export type TeamRoleStatus = "FILLED" | "VACANT";
export type TeamAvailabilityStatus =
  "UNASSESSED" | "AVAILABLE" | "LIMITED" | "UNAVAILABLE";
export type TeamProgressStatus = "NOT_STARTED" | "IN_PROGRESS" | "COMPLETE";
export type TeamWorkItemStatus = "PLANNED" | "ACTIVE" | "BLOCKED" | "COMPLETE";
export type TeamRaciResponsibility =
  "RESPONSIBLE" | "ACCOUNTABLE" | "CONSULTED" | "INFORMED";
export type TeamAccessReviewStatus = "PROPOSED" | "REVIEWED" | "REJECTED";
export type TeamWorkspaceStatus =
  "SETUP_REQUIRED" | "STRUCTURE_IN_PROGRESS" | "READY_FOR_HUMAN_REVIEW";
export type TeamCheckKey =
  | "organization_template"
  | "role_cards"
  | "accountability"
  | "availability"
  | "vacancies"
  | "onboarding"
  | "training"
  | "access_review";
export type TeamNextAction =
  | "SELECT_ORGANIZATION_TEMPLATE"
  | "DEFINE_ROLE_CARDS"
  | "ASSIGN_ACCOUNTABILITY"
  | "ASSESS_AVAILABILITY"
  | "PLAN_VACANCIES"
  | "COMPLETE_ONBOARDING"
  | "COMPLETE_TRAINING"
  | "REVIEW_ACCESS_RECOMMENDATIONS"
  | "CONTINUE_HUMAN_GOVERNANCE";
export type TeamLimitation =
  | "ROLE_LABELS_ARE_NOT_PERMISSIONS"
  | "ACCESS_RECOMMENDATIONS_REQUIRE_HUMAN_AUTHORIZATION"
  | "NO_VOTER_PROFILING"
  | "NO_EXTERNAL_EFFECTS";

export type TeamRoleCard = Readonly<{
  id: UUID;
  title: string;
  area: string;
  purpose: string;
  responsibilities: readonly string[];
  status: TeamRoleStatus;
  principal_id: UUID | null;
  availability_status: TeamAvailabilityStatus;
  weekly_capacity_hours: number | null;
  onboarding_status: TeamProgressStatus;
  vacancy_plan: string | null;
}>;

export type TeamRaciAssignment = Readonly<{
  role_id: UUID;
  responsibility: TeamRaciResponsibility;
}>;

export type TeamWorkItem = Readonly<{
  id: UUID;
  name: string;
  description: string;
  status: TeamWorkItemStatus;
  assignments: readonly TeamRaciAssignment[];
}>;

export type TeamTrainingRequirement = Readonly<{
  id: UUID;
  role_id: UUID;
  title: string;
  description: string;
  status: TeamProgressStatus;
}>;

export type TeamAccessRecommendation = Readonly<{
  id: UUID;
  role_id: UUID;
  campaign_id: UUID;
  workspace_id: UUID | null;
  action: string;
  resource_type: string;
  resource_id: string;
  purpose: string;
  status: TeamAccessReviewStatus;
  authority_effect: "NONE";
}>;

export type TeamWorkspaceCheck = Readonly<{
  key: TeamCheckKey;
  complete: boolean;
  reason_code: string;
}>;

export type TeamWorkspaceProjection = Readonly<{
  id: UUID;
  tenant_id: UUID;
  campaign_id: UUID;
  campaign_version: number;
  campaign_status: "DRAFT" | "ACTIVE";
  campaign_name: string;
  organization_template: TeamOrganizationTemplate;
  roles: readonly TeamRoleCard[] | null;
  work_items: readonly TeamWorkItem[] | null;
  training_requirements: readonly TeamTrainingRequirement[] | null;
  access_recommendations: readonly TeamAccessRecommendation[] | null;
  status: TeamWorkspaceStatus;
  checks: readonly TeamWorkspaceCheck[];
  completed_checks: number;
  total_checks: number;
  filled_role_count: number;
  vacant_role_count: number;
  total_weekly_capacity_hours: number;
  next_action: TeamNextAction;
  authority_effect: "NONE";
  external_effects: "NONE";
  limitation_codes: readonly TeamLimitation[];
  version: number;
  created_at: string;
  updated_at: string;
}>;

export type TeamWorkspaceReadEvidence = Readonly<{
  workspace: TeamWorkspaceProjection;
  audit_event_id: UUID;
}>;

export type CampaignPhaseStatus = "PLANNED" | "ACTIVE" | "COMPLETE";
export type CampaignWorkstreamStatus =
  "PLANNED" | "ACTIVE" | "PAUSED" | "COMPLETE";
export type CampaignMilestoneStatus = "PLANNED" | "IN_PROGRESS" | "COMPLETE";
export type CampaignTaskExecutionStatus =
  "PLANNED" | "IN_PROGRESS" | "COMPLETE";
export type CampaignBlockerSeverity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
export type CampaignBlockerStatus = "OPEN" | "RESOLVED";
export type CampaignDecisionStatus = "REQUIRED" | "DECIDED" | "DEFERRED";
export type CampaignFollowUpStatus = "OPEN" | "COMPLETE";
export type CampaignRoadmapStatus =
  "SETUP_REQUIRED" | "IN_PROGRESS" | "READY_FOR_DAILY_OPERATION" | "COMPLETE";
export type CampaignRoadmapNextAction =
  | "DEFINE_ROADMAP"
  | "RESOLVE_BLOCKERS"
  | "MAKE_HUMAN_DECISIONS"
  | "START_READY_TASKS"
  | "CONTINUE_ACTIVE_WORK"
  | "REVIEW_COMPLETION";
export type CampaignOperationsLimitation =
  | "HUMAN_DECISIONS_REQUIRED"
  | "NO_AUTONOMOUS_TASK_EXECUTION"
  | "NO_CITIZEN_CONTACT"
  | "NO_EXTERNAL_EFFECTS";

export type CampaignPhase = Readonly<{
  id: UUID;
  name: string;
  sequence: number;
  start_date: string;
  end_date: string;
  status: CampaignPhaseStatus;
}>;

export type CampaignOperationsWorkstream = Readonly<{
  id: UUID;
  name: string;
  purpose: string;
  accountable_role_id: UUID;
  status: CampaignWorkstreamStatus;
}>;

export type CampaignMilestone = Readonly<{
  id: UUID;
  phase_id: UUID;
  name: string;
  completion_criteria: string;
  owner_role_id: UUID;
  due_date: string;
  status: CampaignMilestoneStatus;
}>;

export type CampaignOperationsTask = Readonly<{
  id: UUID;
  phase_id: UUID;
  workstream_id: UUID;
  milestone_id: UUID | null;
  title: string;
  owner_role_id: UUID;
  execution_status: CampaignTaskExecutionStatus;
  dependency_ids: readonly UUID[];
  due_date: string;
  evidence_refs: readonly UUID[];
}>;

export type CampaignOperationsBlocker = Readonly<{
  id: UUID;
  task_id: UUID | null;
  severity: CampaignBlockerSeverity;
  status: CampaignBlockerStatus;
  owner_role_id: UUID;
  description: string;
  resolution_condition: string;
}>;

export type CampaignOperationsDecision = Readonly<{
  id: UUID;
  title: string;
  human_role_id: UUID;
  options: readonly string[];
  due_date: string;
  status: CampaignDecisionStatus;
  decision: string | null;
}>;

export type CampaignOperationsFollowUp = Readonly<{
  id: UUID;
  title: string;
  owner_role_id: UUID;
  due_date: string;
  status: CampaignFollowUpStatus;
}>;

export type CampaignOperationsLearningNote = Readonly<{
  id: UUID;
  title: string;
  note: string;
  evidence_refs: readonly UUID[];
}>;

export type CampaignRoadmapProjection = Readonly<{
  id: UUID;
  tenant_id: UUID;
  campaign_id: UUID;
  campaign_version: number;
  campaign_status: "DRAFT" | "ACTIVE";
  campaign_name: string;
  title: string;
  phases: readonly CampaignPhase[] | null;
  workstreams: readonly CampaignOperationsWorkstream[] | null;
  milestones: readonly CampaignMilestone[] | null;
  tasks: readonly CampaignOperationsTask[] | null;
  blockers: readonly CampaignOperationsBlocker[] | null;
  decisions: readonly CampaignOperationsDecision[] | null;
  follow_up_items: readonly CampaignOperationsFollowUp[] | null;
  learning_notes: readonly CampaignOperationsLearningNote[] | null;
  status: CampaignRoadmapStatus;
  execution_order: readonly UUID[];
  ready_task_ids: readonly UUID[];
  blocked_task_ids: readonly UUID[];
  critical_path_task_ids: readonly UUID[];
  open_blocker_count: number;
  required_decision_count: number;
  next_action: CampaignRoadmapNextAction;
  authority_effect: "NONE";
  external_effects: "NONE";
  limitation_codes: readonly CampaignOperationsLimitation[];
  version: number;
  created_at: string;
  updated_at: string;
}>;

export type CampaignRoadmapReadEvidence = Readonly<{
  roadmap: CampaignRoadmapProjection;
  audit_event_id: UUID;
}>;

export type WarRoomSnapshotProjection = Readonly<{
  id: UUID;
  tenant_id: UUID;
  campaign_id: UUID;
  roadmap_id: UUID;
  roadmap_version: number;
  snapshot_date: string;
  priorities: readonly string[];
  ready_task_ids: readonly UUID[];
  blocked_task_ids: readonly UUID[];
  required_decision_ids: readonly UUID[];
  follow_up_notes: readonly string[];
  learning_note_ids: readonly UUID[];
  authority_effect: "NONE";
  external_effects: "NONE";
  created_at: string;
}>;

export type WarRoomSnapshotReadEvidence = Readonly<{
  snapshot: WarRoomSnapshotProjection;
  audit_event_id: UUID;
}>;

export type StrategyEvidenceClassification =
  "VERIFIED" | "INFERRED" | "UNKNOWN";
export type StrategyEvidenceStatus = "ACCEPTED" | "NEEDS_REVIEW" | "REJECTED";
export type StrategyWorkspaceStatus =
  | "EVIDENCE_REQUIRED"
  | "CONTRADICTIONS_OPEN"
  | "RED_TEAM_BLOCKED"
  | "OPTIONS_INCOMPLETE"
  | "OBJECTIVES_INCOMPLETE"
  | "READY_FOR_HUMAN_DECISION"
  | "DECIDED_INTERNAL";
export type StrategyNextAction =
  | "ADD_VERIFIED_EVIDENCE"
  | "RESOLVE_CONTRADICTIONS"
  | "ADDRESS_RED_TEAM_FINDINGS"
  | "COMPLETE_COMPARABLE_OPTIONS"
  | "DEFINE_MEASURABLE_OBJECTIVES"
  | "MAKE_HUMAN_DECISION"
  | "REVALIDATE_DECISION";
export type StrategyLimitation =
  | "NOT_PUBLIC_POSITIONING"
  | "NOT_A_HUMAN_APPROVAL"
  | "NO_VOTER_PROFILING_OR_INDIVIDUAL_TARGETING"
  | "NO_CITIZEN_CONTACT_OR_EXTERNAL_EFFECTS";

export type StrategyEvidenceRecord = Readonly<{
  id: UUID;
  classification: StrategyEvidenceClassification;
  statement: string;
  source_reference: string | null;
  authority: string | null;
  jurisdiction: string | null;
  status: StrategyEvidenceStatus;
  collected_at: string;
}>;

export type StrategyAssumptionRecord = Readonly<{
  id: UUID;
  statement: string;
  evidence_refs: readonly UUID[];
  invalidation_signals: readonly string[];
  status: "ACTIVE" | "INVALIDATED";
}>;

export type StrategyHypothesisRecord = Readonly<{
  id: UUID;
  title: string;
  statement: string;
  evidence_refs: readonly UUID[];
  assumption_refs: readonly UUID[];
  invalidation_signals: readonly string[];
  status: "DRAFT" | "IN_REVIEW" | "REJECTED";
}>;

export type StrategyOptionRecord = Readonly<{
  id: UUID;
  title: string;
  summary: string;
  hypothesis_refs: readonly UUID[];
  evidence_refs: readonly UUID[];
  benefits: readonly string[];
  risks: readonly string[];
  tradeoffs: readonly string[];
}>;

export type StrategyObjectiveRecord = Readonly<{
  id: UUID;
  outcome: string;
  metric: string;
  baseline: string;
  target: string;
  deadline: string;
  owner_role_id: UUID;
  evidence_refs: readonly UUID[];
}>;

export type StrategyContradictionRecord = Readonly<{
  id: UUID;
  left_ref: UUID;
  right_ref: UUID;
  description: string;
  evidence_refs: readonly UUID[];
  status: "OPEN" | "RESOLVED";
  resolution: string | null;
}>;

export type StrategyRedTeamFindingRecord = Readonly<{
  id: UUID;
  severity: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  description: string;
  option_refs: readonly UUID[];
  mitigation: string;
  status: "OPEN" | "RESOLVED";
}>;

export type StrategyDecisionRecord = Readonly<{
  id: UUID;
  workspace_version: number;
  selected_option_id: UUID;
  reason: string;
  human_role_id: UUID;
  approval_receipt_id: string;
  decided_at: string;
}>;

export type StrategyWorkspaceProjection = Readonly<{
  id: UUID;
  tenant_id: UUID;
  campaign_id: UUID;
  campaign_version: number;
  campaign_status: "DRAFT" | "ACTIVE";
  campaign_name: string;
  candidate_workspace_version: number;
  team_workspace_version: number;
  title: string;
  evidence: readonly StrategyEvidenceRecord[] | null;
  assumptions: readonly StrategyAssumptionRecord[] | null;
  hypotheses: readonly StrategyHypothesisRecord[] | null;
  options: readonly StrategyOptionRecord[] | null;
  objectives: readonly StrategyObjectiveRecord[] | null;
  contradictions: readonly StrategyContradictionRecord[] | null;
  red_team_findings: readonly StrategyRedTeamFindingRecord[] | null;
  decision: StrategyDecisionRecord | null;
  status: StrategyWorkspaceStatus;
  verified_evidence_count: number;
  inferred_evidence_count: number;
  unknown_evidence_count: number;
  open_contradiction_count: number;
  open_high_risk_count: number;
  complete_option_count: number;
  measurable_objective_count: number;
  next_action: StrategyNextAction;
  human_decision_required: boolean;
  authority_effect: "NONE";
  external_effects: "NONE";
  limitation_codes: readonly StrategyLimitation[];
  version: number;
  created_at: string;
  updated_at: string;
}>;

export type StrategyWorkspaceReadEvidence = Readonly<{
  workspace: StrategyWorkspaceProjection;
  audit_event_id: UUID;
}>;
