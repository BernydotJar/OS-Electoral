import type {
  CampaignReadinessProjection,
  CampaignRoadmapStatus,
  CandidateWorkspaceStatus,
  GuidedIntakeStatus,
  StrategyWorkspaceStatus,
  TeamWorkspaceStatus,
} from "@/lib/contracts";

export type CampaignJourneyPhaseKey =
  | "foundation"
  | "evidence"
  | "team"
  | "strategy"
  | "operations";

export type CampaignJourneyPhaseState =
  | "COMPLETE"
  | "ACTIVE"
  | "AVAILABLE"
  | "BLOCKED"
  | "LOCKED";

export type CampaignJourneyPhase = Readonly<{
  key: CampaignJourneyPhaseKey;
  state: CampaignJourneyPhaseState;
  href: string;
}>;

export type CampaignJourney = Readonly<{
  phases: readonly CampaignJourneyPhase[];
  currentPhase: CampaignJourneyPhaseKey;
  completedPhaseCount: number;
  releaseAuthority: "NONE";
}>;

export type CampaignJourneyInput = Readonly<{
  readinessStatus: CampaignReadinessProjection["status"] | null;
  intakeStatus: GuidedIntakeStatus | null;
  candidateStatus: CandidateWorkspaceStatus | null;
  teamStatus: TeamWorkspaceStatus | null;
  strategyStatus: StrategyWorkspaceStatus | null;
  operationsStatus: CampaignRoadmapStatus | null;
  availablePhases?: Readonly<{
    foundation: boolean;
    evidence: boolean;
    team: boolean;
    strategy: boolean;
    operations: boolean;
  }>;
}>;

const phaseDefinitions = [
  { key: "foundation", href: "#guided-intake" },
  { key: "evidence", href: "#candidate-workspace" },
  { key: "team", href: "#team-workspace" },
  { key: "strategy", href: "#strategy-room" },
  { key: "operations", href: "#war-room" },
] as const satisfies readonly Readonly<{
  key: CampaignJourneyPhaseKey;
  href: string;
}>[];

export function deriveCampaignJourney(
  input: CampaignJourneyInput,
): CampaignJourney {
  const complete = [
    input.intakeStatus === "READY_FOR_RESEARCH",
    input.candidateStatus === "INTERNALLY_APPROVED",
    input.teamStatus === "READY_FOR_HUMAN_REVIEW",
    input.strategyStatus === "DECIDED_INTERNAL",
    input.operationsStatus === "COMPLETE",
  ];
  const started = [
    input.readinessStatus !== null || input.intakeStatus !== null,
    input.candidateStatus !== null,
    input.teamStatus !== null,
    input.strategyStatus !== null,
    input.operationsStatus !== null,
  ];
  const availability = [
    input.availablePhases?.foundation ?? true,
    input.availablePhases?.evidence ?? true,
    input.availablePhases?.team ?? true,
    input.availablePhases?.strategy ?? true,
    input.availablePhases?.operations ?? true,
  ];

  let gateOpen = true;
  const phases = phaseDefinitions.map((phase, index): CampaignJourneyPhase => {
    if (!gateOpen) return { ...phase, state: "LOCKED" };
    if (complete[index]) return { ...phase, state: "COMPLETE" };

    gateOpen = false;
    if (!availability[index]) return { ...phase, state: "BLOCKED" };
    return { ...phase, state: started[index] ? "ACTIVE" : "AVAILABLE" };
  });
  const current = phases.find(
    (phase) =>
      phase.state === "ACTIVE" ||
      phase.state === "AVAILABLE" ||
      phase.state === "BLOCKED",
  );

  return {
    phases,
    currentPhase: current?.key ?? "operations",
    completedPhaseCount: phases.filter((phase) => phase.state === "COMPLETE")
      .length,
    releaseAuthority: "NONE",
  };
}
