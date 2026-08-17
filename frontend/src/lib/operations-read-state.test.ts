import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

import { CampaignOsApiError } from "@/lib/api-client";
import { campaignRoadmapReadFallback } from "@/lib/operations-read-state";

function apiError(status: number, code: string): CampaignOsApiError {
  return new CampaignOsApiError("operations read failed", status, code, null);
}

describe("campaignRoadmapReadFallback", () => {
  it("treats an absent roadmap and incomplete Operations prerequisites as not started", () => {
    expect(campaignRoadmapReadFallback(apiError(404, "NOT_FOUND"))).toBe(
      "NOT_STARTED",
    );
    expect(
      campaignRoadmapReadFallback(apiError(409, "CAMPAIGN_NOT_READY")),
    ).toBe("NOT_STARTED");
  });

  it("preserves dependency outages and fails closed for unrelated conflicts", () => {
    expect(
      campaignRoadmapReadFallback(apiError(503, "DEPENDENCY_UNAVAILABLE")),
    ).toBe("DEPENDENCY_UNAVAILABLE");
    expect(campaignRoadmapReadFallback(apiError(409, "ROADMAP_CONFLICT"))).toBe(
      null,
    );
    expect(
      campaignRoadmapReadFallback(apiError(409, "IDEMPOTENCY_CONFLICT")),
    ).toBe(null);
  });
});
