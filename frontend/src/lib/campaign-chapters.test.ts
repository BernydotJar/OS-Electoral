import { describe, expect, it } from "vitest";

import {
  campaignChapterHref,
  campaignChapterKeyForAnchor,
  parseCampaignChapterKey,
  resolveCampaignChapter,
} from "@/lib/campaign-chapters";
import type { CampaignJourney } from "@/lib/campaign-journey";

const journey: CampaignJourney = {
  currentPhase: "evidence",
  completedPhaseCount: 1,
  releaseAuthority: "NONE",
  phases: [
    { key: "foundation", state: "COMPLETE", href: "#guided-intake" },
    { key: "evidence", state: "ACTIVE", href: "#candidate-workspace" },
    { key: "team", state: "AVAILABLE", href: "#team-workspace" },
    { key: "strategy", state: "LOCKED", href: "#strategy-room" },
    { key: "operations", state: "BLOCKED", href: "#war-room" },
  ],
};

describe("campaign chapter routing", () => {
  it("builds stable localized chapter URLs with canonical anchors", () => {
    expect(campaignChapterHref("es", "team")).toBe(
      "/es/campaign/team#team-workspace",
    );
    expect(campaignChapterHref("en", "evidence")).toBe(
      "/en/campaign/evidence#candidate-workspace",
    );
  });

  it("maps existing workspace anchors to their chapter", () => {
    expect(campaignChapterKeyForAnchor("guided-intake")).toBe("foundation");
    expect(campaignChapterKeyForAnchor("team-template-preview")).toBe("team");
    expect(campaignChapterKeyForAnchor("campaigns")).toBeNull();
  });

  it("parses only canonical chapter keys", () => {
    expect(parseCampaignChapterKey("operations")).toBe("operations");
    expect(parseCampaignChapterKey("../../operations")).toBeNull();
    expect(parseCampaignChapterKey("unknown")).toBeNull();
  });

  it("allows revisiting visible chapters but fails closed for locked routes", () => {
    expect(resolveCampaignChapter(journey, "foundation").key).toBe("foundation");
    expect(resolveCampaignChapter(journey, "team").key).toBe("team");
    expect(resolveCampaignChapter(journey, "operations").key).toBe("operations");
    expect(resolveCampaignChapter(journey, "strategy").key).toBe("evidence");
  });
});
