import type { CampaignJourney } from "@/lib/campaign-journey";
import type { GuidedIntakeAvailability } from "@/lib/shell-view-model";

export type CampaignExperienceMode = "FIRST_USE" | "ACTIVE" | "COMPLETE";

export function deriveCampaignExperienceMode({
  guidedIntakeAvailability,
  journey,
}: Readonly<{
  guidedIntakeAvailability: GuidedIntakeAvailability;
  journey: CampaignJourney;
}>): CampaignExperienceMode {
  if (
    guidedIntakeAvailability === "NOT_STARTED" &&
    journey.currentPhase === "foundation" &&
    journey.completedPhaseCount === 0
  ) {
    return "FIRST_USE";
  }
  if (journey.completedPhaseCount === journey.phases.length) return "COMPLETE";
  return "ACTIVE";
}
