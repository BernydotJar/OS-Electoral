import { campaignChapterHref } from "@/lib/campaign-chapters";
import type { EffectiveMembership } from "@/lib/contracts";
import type { Dictionary } from "@/lib/i18n";

export type NavigationKey = keyof Dictionary["nav"];
export type NavigationItem = Readonly<{
  key: NavigationKey;
  href: string;
  enabled: boolean;
  reason: "BASE" | "EXACT_GRANT" | "FUTURE_CAPABILITY";
}>;

function hasGrant(
  memberships: readonly EffectiveMembership[],
  predicate: (grant: EffectiveMembership["grants"][number]) => boolean,
): boolean {
  return memberships.some((membership) => membership.grants.some(predicate));
}

export function deriveNavigation(
  locale: string,
  memberships: readonly EffectiveMembership[],
  currentCampaignId?: string,
): readonly NavigationItem[] {
  const base = `/${locale}`;
  return [
    {
      key: "intake",
      href: campaignChapterHref(locale, "foundation"),
      enabled: hasGrant(
        memberships,
        (grant) =>
          currentCampaignId !== undefined &&
          grant.action === "read" &&
          grant.resource_type === "guided_intake" &&
          grant.resource_id === currentCampaignId &&
          grant.campaign_id === currentCampaignId &&
          grant.workspace_id === null &&
          grant.purpose === "Review guided campaign intake",
      ),
      reason: "EXACT_GRANT",
    },
    { key: "overview", href: `${base}#main`, enabled: true, reason: "BASE" },
    {
      key: "campaigns",
      href: `${base}#campaigns`,
      enabled: true,
      reason: "BASE",
    },
    {
      key: "readiness",
      href: `${base}#readiness`,
      enabled: hasGrant(
        memberships,
        (grant) => grant.resource_type === "campaign_readiness",
      ),
      reason: "EXACT_GRANT",
    },
    {
      key: "candidate",
      href: campaignChapterHref(locale, "evidence"),
      enabled: hasGrant(
        memberships,
        (grant) =>
          currentCampaignId !== undefined &&
          grant.action === "read" &&
          grant.resource_type === "candidate_workspace" &&
          grant.resource_id === currentCampaignId &&
          grant.campaign_id === currentCampaignId &&
          grant.workspace_id === null &&
          grant.purpose === "Review candidate evidence workspace",
      ),
      reason: "EXACT_GRANT",
    },
    {
      key: "team",
      href: campaignChapterHref(locale, "team"),
      enabled: hasGrant(
        memberships,
        (grant) =>
          currentCampaignId !== undefined &&
          grant.action === "read" &&
          grant.resource_type === "team_workspace" &&
          grant.resource_id === currentCampaignId &&
          grant.campaign_id === currentCampaignId &&
          grant.workspace_id === null &&
          grant.purpose === "Review campaign team workspace",
      ),
      reason: "EXACT_GRANT",
    },
    {
      key: "strategy",
      href: campaignChapterHref(locale, "strategy"),
      enabled: hasGrant(
        memberships,
        (grant) =>
          currentCampaignId !== undefined &&
          grant.action === "read" &&
          grant.resource_type === "strategy_workspace" &&
          grant.resource_id === currentCampaignId &&
          grant.campaign_id === currentCampaignId &&
          grant.workspace_id === null &&
          grant.purpose === "Review campaign strategy workspace",
      ),
      reason: "EXACT_GRANT",
    },
    {
      key: "warRoom",
      href: campaignChapterHref(locale, "operations"),
      enabled: hasGrant(
        memberships,
        (grant) =>
          currentCampaignId !== undefined &&
          grant.action === "read" &&
          grant.resource_type === "campaign_roadmap" &&
          grant.resource_id === currentCampaignId &&
          grant.campaign_id === currentCampaignId &&
          grant.workspace_id === null &&
          grant.purpose === "Review campaign operations roadmap",
      ),
      reason: "EXACT_GRANT",
    },
    {
      key: "evidence",
      href: `${base}#evidence`,
      enabled: false,
      reason: "FUTURE_CAPABILITY",
    },
  ];
}
