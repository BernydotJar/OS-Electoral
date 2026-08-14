import type { EffectiveMembership } from "@/lib/contracts";

type ExactGrant = Readonly<{
  action: string;
  resourceType: string;
  resourceId: string;
  purpose: string;
  campaignId: string | null;
  workspaceId: string | null;
}>;

export function hasExactGrant(
  memberships: readonly EffectiveMembership[],
  expected: ExactGrant,
): boolean {
  return memberships.some((membership) =>
    membership.grants.some(
      (grant) =>
        grant.action === expected.action &&
        grant.resource_type === expected.resourceType &&
        grant.resource_id === expected.resourceId &&
        grant.purpose === expected.purpose &&
        grant.campaign_id === expected.campaignId &&
        grant.workspace_id === expected.workspaceId,
    ),
  );
}

export type GuidedIntakeCapabilities = Readonly<{
  canStart: boolean;
  canRead: boolean;
  canUpdate: boolean;
}>;

export function deriveGuidedIntakeCapabilities(
  memberships: readonly EffectiveMembership[],
  campaignId: string,
): GuidedIntakeCapabilities {
  const exact = (action: string, purpose: string) =>
    hasExactGrant(memberships, {
      action,
      resourceType: "guided_intake",
      resourceId: campaignId,
      purpose,
      campaignId,
      workspaceId: null,
    });
  return {
    canStart: exact("create", "Begin guided campaign intake"),
    canRead: exact("read", "Review guided campaign intake"),
    canUpdate: exact("update", "Maintain guided campaign intake"),
  };
}

export type CandidateWorkspaceCapabilities = Readonly<{
  canStart: boolean;
  canRead: boolean;
  canUpdate: boolean;
  canApprove: boolean;
}>;

export function deriveCandidateWorkspaceCapabilities(
  memberships: readonly EffectiveMembership[],
  campaignId: string,
): CandidateWorkspaceCapabilities {
  const exact = (action: string, purpose: string) =>
    hasExactGrant(memberships, {
      action,
      resourceType: "candidate_workspace",
      resourceId: campaignId,
      purpose,
      campaignId,
      workspaceId: null,
    });
  return {
    canStart: exact("create", "Create candidate evidence workspace"),
    canRead: exact("read", "Review candidate evidence workspace"),
    canUpdate: exact("update", "Maintain candidate evidence workspace"),
    canApprove: exact("approve", "Approve candidate evidence section"),
  };
}

export type TeamWorkspaceCapabilities = Readonly<{
  canStart: boolean;
  canRead: boolean;
  canUpdate: boolean;
}>;

export function deriveTeamWorkspaceCapabilities(
  memberships: readonly EffectiveMembership[],
  campaignId: string,
): TeamWorkspaceCapabilities {
  const exact = (action: string, purpose: string) =>
    hasExactGrant(memberships, {
      action,
      resourceType: "team_workspace",
      resourceId: campaignId,
      purpose,
      campaignId,
      workspaceId: null,
    });
  return {
    canStart: exact("create", "Create campaign team workspace"),
    canRead: exact("read", "Review campaign team workspace"),
    canUpdate: exact("update", "Maintain campaign team workspace"),
  };
}

export type StrategyWorkspaceCapabilities = Readonly<{
  canStart: boolean;
  canRead: boolean;
  canUpdate: boolean;
  canApprove: boolean;
}>;

export function deriveStrategyWorkspaceCapabilities(
  memberships: readonly EffectiveMembership[],
  campaignId: string,
): StrategyWorkspaceCapabilities {
  const exact = (action: string, purpose: string) =>
    hasExactGrant(memberships, {
      action,
      resourceType: "strategy_workspace",
      resourceId: campaignId,
      purpose,
      campaignId,
      workspaceId: null,
    });
  return {
    canStart: exact("create", "Create campaign strategy workspace"),
    canRead: exact("read", "Review campaign strategy workspace"),
    canUpdate: exact("update", "Maintain campaign strategy workspace"),
    canApprove: exact("approve", "Approve internal campaign strategy option"),
  };
}

export type CampaignContextCapabilities = Readonly<{
  canCreateCampaign: boolean;
}>;

export function deriveCampaignContextCapabilities(
  memberships: readonly EffectiveMembership[],
  tenantId: string,
): CampaignContextCapabilities {
  return {
    canCreateCampaign: memberships.some((membership) =>
      membership.grants.some(
        (grant) =>
          grant.action === "create" &&
          grant.resource_type === "campaign_collection" &&
          grant.resource_id === tenantId &&
          grant.campaign_id === null &&
          grant.workspace_id === null &&
          grant.purpose === "Create tenant campaign",
      ),
    ),
  };
}

export type TrainingCapabilities = Readonly<{
  canReadCatalog: boolean;
  canReadSelf: boolean;
  canCompleteSelf: boolean;
  canManageAssignments: boolean;
  canReadReceipts: boolean;
}>;

export function deriveTrainingCapabilities(
  memberships: readonly EffectiveMembership[],
  campaignId: string,
): TrainingCapabilities {
  const exact = (action: string, purpose: string) =>
    hasExactGrant(memberships, {
      action,
      resourceType: "training_academy",
      resourceId: campaignId,
      purpose,
      campaignId,
      workspaceId: null,
    });
  return {
    canReadCatalog: exact(
      "training.catalog.read",
      "Review approved training catalog",
    ),
    canReadSelf: exact("training.self.read", "Review own campaign training"),
    canCompleteSelf: exact(
      "training.self.complete",
      "Complete assigned campaign training",
    ),
    canManageAssignments: exact(
      "training.assignment.manage",
      "Assign campaign learning path",
    ),
    canReadReceipts: exact(
      "training.receipt.read",
      "Review own campaign training",
    ),
  };
}
