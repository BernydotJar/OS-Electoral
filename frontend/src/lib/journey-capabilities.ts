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
