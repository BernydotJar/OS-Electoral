import { describe, expect, it } from "vitest";

import { deriveCampaignJourney } from "@/lib/campaign-journey";

describe("deriveCampaignJourney", () => {
  it("blocks the foundation when guided intake access is unavailable", () => {
    const journey = deriveCampaignJourney({
      readinessStatus: "READY_FOR_GUIDED_INTAKE",
      intakeStatus: null,
      candidateStatus: null,
      teamStatus: null,
      strategyStatus: null,
      operationsStatus: null,
      availablePhases: {
        foundation: false,
        evidence: false,
        team: false,
        strategy: false,
        operations: false,
      },
    });

    expect(journey.currentPhase).toBe("foundation");
    expect(journey.phases.map((phase) => phase.state)).toEqual([
      "BLOCKED",
      "LOCKED",
      "LOCKED",
      "LOCKED",
      "LOCKED",
    ]);
  });

  it("keeps campaign foundation active until guided intake is research-ready", () => {
    const journey = deriveCampaignJourney({
      readinessStatus: "READY_FOR_GUIDED_INTAKE",
      intakeStatus: "IN_PROGRESS",
      candidateStatus: null,
      teamStatus: null,
      strategyStatus: null,
      operationsStatus: null,
    });

    expect(journey.currentPhase).toBe("foundation");
    expect(journey.completedPhaseCount).toBe(0);
    expect(journey.phases.map((phase) => phase.state)).toEqual([
      "ACTIVE",
      "LOCKED",
      "LOCKED",
      "LOCKED",
      "LOCKED",
    ]);
  });

  it("opens evidence as the next phase when intake is ready", () => {
    const journey = deriveCampaignJourney({
      readinessStatus: "READY_FOR_GUIDED_INTAKE",
      intakeStatus: "READY_FOR_RESEARCH",
      candidateStatus: null,
      teamStatus: null,
      strategyStatus: null,
      operationsStatus: null,
    });

    expect(journey.currentPhase).toBe("evidence");
    expect(journey.completedPhaseCount).toBe(1);
    expect(journey.phases.map((phase) => phase.state)).toEqual([
      "COMPLETE",
      "AVAILABLE",
      "LOCKED",
      "LOCKED",
      "LOCKED",
    ]);
  });

  it("advances through candidate, team, strategy, and daily operations without claiming production readiness", () => {
    const journey = deriveCampaignJourney({
      readinessStatus: "READY_FOR_GUIDED_INTAKE",
      intakeStatus: "READY_FOR_RESEARCH",
      candidateStatus: "INTERNALLY_APPROVED",
      teamStatus: "READY_FOR_HUMAN_REVIEW",
      strategyStatus: "DECIDED_INTERNAL",
      operationsStatus: "READY_FOR_DAILY_OPERATION",
    });

    expect(journey.currentPhase).toBe("operations");
    expect(journey.completedPhaseCount).toBe(4);
    expect(journey.phases.map((phase) => phase.state)).toEqual([
      "COMPLETE",
      "COMPLETE",
      "COMPLETE",
      "COMPLETE",
      "ACTIVE",
    ]);
    expect(journey.releaseAuthority).toBe("NONE");
  });


  it("marks the next phase blocked when its module is unavailable", () => {
    const journey = deriveCampaignJourney({
      readinessStatus: "READY_FOR_GUIDED_INTAKE",
      intakeStatus: "READY_FOR_RESEARCH",
      candidateStatus: null,
      teamStatus: null,
      strategyStatus: null,
      operationsStatus: null,
      availablePhases: {
        foundation: true,
        evidence: false,
        team: false,
        strategy: false,
        operations: false,
      },
    });

    expect(journey.currentPhase).toBe("evidence");
    expect(journey.phases.map((phase) => phase.state)).toEqual([
      "COMPLETE",
      "BLOCKED",
      "LOCKED",
      "LOCKED",
      "LOCKED",
    ]);
  });

  it("does not skip an incomplete earlier gate even when a later module has data", () => {
    const journey = deriveCampaignJourney({
      readinessStatus: "READY_FOR_GUIDED_INTAKE",
      intakeStatus: "IN_PROGRESS",
      candidateStatus: "UNDER_REVIEW",
      teamStatus: "STRUCTURE_IN_PROGRESS",
      strategyStatus: null,
      operationsStatus: null,
    });

    expect(journey.currentPhase).toBe("foundation");
    expect(journey.phases[1]?.state).toBe("LOCKED");
    expect(journey.phases[2]?.state).toBe("LOCKED");
  });
});
