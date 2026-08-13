import type {
  CampaignJourney,
  CampaignJourneyPhase,
  CampaignJourneyPhaseKey,
} from "@/lib/campaign-journey";

export const CAMPAIGN_CHAPTER_DEFINITIONS = [
  { key: "foundation", anchor: "guided-intake" },
  { key: "evidence", anchor: "candidate-workspace" },
  { key: "team", anchor: "team-workspace" },
  { key: "strategy", anchor: "strategy-room" },
  { key: "operations", anchor: "war-room" },
] as const satisfies readonly Readonly<{
  key: CampaignJourneyPhaseKey;
  anchor: string;
}>[];

const CHAPTER_KEYS = new Set<string>(
  CAMPAIGN_CHAPTER_DEFINITIONS.map((chapter) => chapter.key),
);

const ANCHOR_TO_CHAPTER = new Map<string, CampaignJourneyPhaseKey>([
  ...CAMPAIGN_CHAPTER_DEFINITIONS.map(
    (chapter) => [chapter.anchor, chapter.key] as const,
  ),
  ["candidate-completion", "evidence"],
  ["candidate-edit-identity", "evidence"],
  ["candidate-edit-biography", "evidence"],
  ["candidate-edit-purpose", "evidence"],
  ["candidate-edit-values", "evidence"],
  ["candidate-edit-attributes", "evidence"],
  ["candidate-edit-contradictions", "evidence"],
  ["candidate-edit-development_goals", "evidence"],
  ["candidate-edit-reputation", "evidence"],
  ["candidate-approvals", "evidence"],
  ["team-template-preview", "team"],
  ["team-role-editor", "team"],
  ["team-operations-board", "team"],
  ["training-academy", "team"],
]);

export function parseCampaignChapterKey(
  value: string | null | undefined,
): CampaignJourneyPhaseKey | null {
  return value !== null && value !== undefined && CHAPTER_KEYS.has(value)
    ? (value as CampaignJourneyPhaseKey)
    : null;
}

export function campaignChapterAnchor(key: CampaignJourneyPhaseKey): string {
  return (
    CAMPAIGN_CHAPTER_DEFINITIONS.find((chapter) => chapter.key === key)
      ?.anchor ?? "main"
  );
}

export function campaignChapterPath(
  locale: "es" | "en" | string,
  key: CampaignJourneyPhaseKey,
): string {
  return `/${locale}/campaign/${key}`;
}

export function campaignChapterHref(
  locale: "es" | "en" | string,
  key: CampaignJourneyPhaseKey,
  anchor = campaignChapterAnchor(key),
): string {
  return `${campaignChapterPath(locale, key)}#${anchor}`;
}

export function campaignChapterKeyForAnchor(
  anchor: string,
): CampaignJourneyPhaseKey | null {
  return ANCHOR_TO_CHAPTER.get(anchor.replace(/^#/, "")) ?? null;
}

export function resolveCampaignChapter(
  journey: CampaignJourney,
  requested: CampaignJourneyPhaseKey | null,
): CampaignJourneyPhase {
  const current =
    journey.phases.find((phase) => phase.key === journey.currentPhase) ??
    journey.phases[0];
  if (!current) {
    throw new Error("Campaign journey must contain at least one phase");
  }
  if (requested === null) return current;
  const requestedPhase = journey.phases.find(
    (phase) => phase.key === requested,
  );
  if (!requestedPhase || requestedPhase.state === "LOCKED") return current;
  return requestedPhase;
}
