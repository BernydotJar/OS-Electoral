import { describe, expect, it } from "vitest";

import { deriveCampaignExperienceMode } from "@/lib/campaign-experience";
import type { CampaignJourney } from "@/lib/campaign-journey";

function journey(
  currentPhase: CampaignJourney["currentPhase"],
  completedPhaseCount: number,
): CampaignJourney {
  return {
    currentPhase,
    completedPhaseCount,
    releaseAuthority: "NONE",
    phases: [
      { key: "foundation", state: "ACTIVE", href: "#guided-intake" },
      { key: "evidence", state: "LOCKED", href: "#candidate-workspace" },
      { key: "team", state: "LOCKED", href: "#team-workspace" },
      { key: "strategy", state: "LOCKED", href: "#strategy-room" },
      { key: "operations", state: "LOCKED", href: "#war-room" },
    ],
  };
}

describe("deriveCampaignExperienceMode", () => {
  it("shows the cinematic welcome only before the guided path exists", () => {
    expect(
      deriveCampaignExperienceMode({
        guidedIntakeAvailability: "NOT_STARTED",
        journey: journey("foundation", 0),
      }),
    ).toBe("FIRST_USE");
  });

  it("switches to an operational mission after work has started", () => {
    expect(
      deriveCampaignExperienceMode({
        guidedIntakeAvailability: "AVAILABLE",
        journey: journey("foundation", 0),
      }),
    ).toBe("ACTIVE");
  });

  it("recognizes a fully completed campaign route without granting release authority", () => {
    expect(
      deriveCampaignExperienceMode({
        guidedIntakeAvailability: "AVAILABLE",
        journey: journey("operations", 5),
      }),
    ).toBe("COMPLETE");
  });
});
