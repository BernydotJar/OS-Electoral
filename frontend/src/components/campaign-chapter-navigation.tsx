
import { campaignChapterHref } from "@/lib/campaign-chapters";
import type {
  CampaignJourney,
  CampaignJourneyPhase,
} from "@/lib/campaign-journey";
import type { Dictionary, Locale } from "@/lib/i18n";

function navigable(phase: CampaignJourneyPhase): boolean {
  return phase.state !== "LOCKED";
}

export function CampaignChapterNavigation({
  locale,
  dictionary,
  journey,
  selected,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  journey: CampaignJourney;
  selected: CampaignJourneyPhase;
}>) {
  const currentIndex = journey.phases.findIndex(
    (phase) => phase.key === selected.key,
  );
  const previous = journey.phases
    .slice(0, currentIndex)
    .reverse()
    .find(navigable);
  const next = journey.phases.slice(currentIndex + 1).find(navigable);

  return (
    <nav
      className="chapter-command-bar"
      aria-label={dictionary.journey.chapterNavigationLabel}
    >
      <div className="chapter-command-primary">
        <a
          className="chapter-command-back"
          href={`/${locale}`}
        >
          <span aria-hidden="true">←</span>
          {dictionary.journey.backToOverview}
        </a>

        <div className="chapter-command-current">
          <span>
            {dictionary.journey.currentChapter} {currentIndex + 1}/
            {journey.phases.length}
          </span>
          <strong>{dictionary.journey.phaseLabels[selected.key]}</strong>
          <small>{dictionary.journey.statusLabels[selected.state]}</small>
        </div>

        <div className="chapter-command-actions">
          {previous ? (
            <a
              href={campaignChapterHref(locale, previous.key)}
                  aria-label={`${dictionary.journey.previousChapter}: ${dictionary.journey.phaseLabels[previous.key]}`}
            >
              <span aria-hidden="true">←</span>
              <small>{dictionary.journey.previousChapter}</small>
            </a>
          ) : (
            <span aria-hidden="true" />
          )}
          {next ? (
            <a
              href={campaignChapterHref(locale, next.key)}
              aria-label={`${dictionary.journey.nextChapter}: ${dictionary.journey.phaseLabels[next.key]}`}
            >
              <small>{dictionary.journey.nextChapter}</small>
              <span aria-hidden="true">→</span>
            </a>
          ) : null}
        </div>
      </div>

      <details className="chapter-command-map">
        <summary>
          <span>{dictionary.journey.chapterMapLabel}</span>
          <small>{dictionary.journey.chapterMapBody}</small>
        </summary>
        <ol className="chapter-command-track">
          {journey.phases.map((phase, index) => {
            const current = phase.key === selected.key;
            const content = (
              <>
                <span aria-hidden="true">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <strong>{dictionary.journey.phaseLabels[phase.key]}</strong>
                <small>{dictionary.journey.statusLabels[phase.state]}</small>
              </>
            );
            return (
              <li
                key={phase.key}
                data-state={phase.state}
                data-current={current}
                aria-current={current ? "step" : undefined}
              >
                {current ? (
                  <div>{content}</div>
                ) : navigable(phase) ? (
                  <a
                    href={campaignChapterHref(locale, phase.key)}
                  >
                    {content}
                  </a>
                ) : (
                  <div aria-disabled="true">{content}</div>
                )}
              </li>
            );
          })}
        </ol>
      </details>
    </nav>
  );
}
