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
      className="chapter-navigation"
      aria-label={dictionary.journey.chapterNavigationLabel}
    >
      <div className="chapter-navigation-heading">
        <Link
          href={`/${locale}` as Route}
          transitionTypes={["chapter-back"]}
        >
          <span aria-hidden="true">←</span>
          {dictionary.journey.backToOverview}
        </Link>
        <p>
          {dictionary.journey.currentChapter}{" "}
          <strong>{String(currentIndex + 1).padStart(2, "0")}</strong>
          <span aria-hidden="true"> / </span>
          {journey.phases.length}
        </p>
      </div>

      <ol className="chapter-navigation-track">
        {journey.phases.map((phase, index) => {
          const current = phase.key === selected.key;
          const content = (
            <>
              <span aria-hidden="true">{String(index + 1).padStart(2, "0")}</span>
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
                <ViewTransition name="campaign-current-chapter" share="chapter-indicator">
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

      <div className="chapter-navigation-actions">
        {previous ? (
          <Link
            href={campaignChapterHref(locale, previous.key) as Route}
            transitionTypes={["chapter-back"]}
          >
            <span>{dictionary.journey.previousChapter}</span>
            <strong>{dictionary.journey.phaseLabels[previous.key]}</strong>
          </Link>
        ) : (
          <span />
        )}
        {next ? (
          <Link
            href={campaignChapterHref(locale, next.key) as Route}
            transitionTypes={["chapter-forward"]}
          >
            <span>{dictionary.journey.nextChapter}</span>
            <strong>{dictionary.journey.phaseLabels[next.key]}</strong>
          </Link>
        ) : null}
      </div>
    </nav>
  );
}
