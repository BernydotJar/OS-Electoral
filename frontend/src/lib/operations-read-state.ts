import { CampaignOsApiError } from "@/lib/api-client";

export type CampaignRoadmapReadFallback =
  | "NOT_STARTED"
  | "DEPENDENCY_UNAVAILABLE";

export function campaignRoadmapReadFallback(
  error: CampaignOsApiError,
): CampaignRoadmapReadFallback | null {
  if (error.status === 404) return "NOT_STARTED";
  if (error.status === 409 && error.code === "CAMPAIGN_NOT_READY") {
    return "NOT_STARTED";
  }
  if (error.status === 503) return "DEPENDENCY_UNAVAILABLE";
  return null;
}
