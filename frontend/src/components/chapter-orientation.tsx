import type {
  CampaignJourney,
  CampaignJourneyPhase,
} from "@/lib/campaign-journey";
import type { Dictionary } from "@/lib/i18n";

export function ChapterOrientation({
  dictionary,
  journey,
  selected,
}: Readonly<{
  dictionary: Dictionary;
  journey: CampaignJourney;
  selected: CampaignJourneyPhase;
}>) {
  const currentIndex = journey.phases.findIndex(
    (phase) => phase.key === selected.key,
  );
  return (
    <section
      className="chapter-orientation"
      data-state={selected.state}
      aria-labelledby="chapter-orientation-title"
    >
      <div className="chapter-orientation-heading">
        <span className="chapter-orientation-index">
          {dictionary.journey.currentChapter} {currentIndex + 1}/
          {journey.phases.length}
        </span>
        <span className="chapter-orientation-status">
          {dictionary.journey.statusLabels[selected.state]}
        </span>
      </div>
      <div className="chapter-orientation-copy">
        <div>
          <p className="eyebrow">{dictionary.journey.contextHintLabel}</p>
          <h2 id="chapter-orientation-title">
            {dictionary.journey.phaseLabels[selected.key]}
          </h2>
          <p>{dictionary.journey.phaseOutcomes[selected.key]}</p>
        </div>
        <div className="chapter-orientation-next">
          <span>{dictionary.journey.missionLabel}</span>
          <strong>{dictionary.journey.phaseActions[selected.key]}</strong>
        </div>
      </div>
    </section>
  );
}
