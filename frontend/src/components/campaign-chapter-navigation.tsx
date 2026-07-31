import type { Route } from "next";
import Link from "next/link";
import { ViewTransition } from "react";

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
        <Link
          className="chapter-command-back"
          href={`/${locale}` as Route}
          transitionTypes={["chapter-back"]}
        >
          <span aria-hidden="true">←</span>
          {dictionary.journey.backToOverview}
        </Link>

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
            <Link
              href={campaignChapterHref(locale, previous.key) as Route}
              transitionTypes={["chapter-back"]}
              aria-label={`${dictionary.journey.previousChapter}: ${dictionary.journey.phaseLabels[previous.key]}`}
            >
              <span aria-hidden="true">←</span>
              <small>{dictionary.journey.previousChapter}</small>
            </Link>
          ) : (
            <span aria-hidden="true" />
          )}
          {next ? (
            <Link
              href={campaignChapterHref(locale, next.key) as Route}
              transitionTypes={["chapter-forward"]}
              aria-label={`${dictionary.journey.nextChapter}: ${dictionary.journey.phaseLabels[next.key]}`}
            >
              <small>{dictionary.journey.nextChapter}</small>
              <span aria-hidden="true">→</span>
            </Link>
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
                  <ViewTransition
                    name="campaign-current-chapter"
                    share="chapter-indicator"
                  >
                    <div>{content}</div>
                  </ViewTransition>
                ) : navigable(phase) ? (
                  <Link
                    href={campaignChapterHref(locale, phase.key) as Route}
                    transitionTypes={[
                      index < currentIndex ? "chapter-back" : "chapter-forward",
                    ]}
                  >
                    {content}
                  </Link>
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
