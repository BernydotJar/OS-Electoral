import type { Route } from "next";
import Link from "next/link";

import { campaignChapterHref } from "@/lib/campaign-chapters";
import type { CampaignJourney } from "@/lib/campaign-journey";
import type { Dictionary, Locale } from "@/lib/i18n";

export function CampaignLaunchRoadmap({
  locale,
  dictionary,
  journey,
}: {
  locale: Locale;
  dictionary: Dictionary;
  journey: CampaignJourney;
}) {
  const currentPhase =
    journey.phases.find((phase) => phase.key === journey.currentPhase) ??
    journey.phases[0];
  if (!currentPhase) return null;

  const currentIndex = journey.phases.findIndex(
    (phase) => phase.key === currentPhase.key,
  );

  return (
    <section
      id="campaign-journey"
      className="campaign-journey"
      aria-labelledby="campaign-journey-title"
    >
      <div className="journey-heading">
        <div>
          <p className="eyebrow">{dictionary.journey.eyebrow}</p>
          <h2 id="campaign-journey-title">{dictionary.journey.title}</h2>
          <p>{dictionary.journey.body}</p>
        </div>
        <div
          className="journey-stage"
          role="group"
          aria-label={dictionary.journey.progressLabel}
        >
          <span>{dictionary.journey.stageLabel}</span>
          <strong>
            {currentIndex + 1}/{journey.phases.length}
          </strong>
          <small>
            {journey.completedPhaseCount} {dictionary.journey.completedLabel}
          </small>
        </div>
      </div>

      <article className="journey-chapter" data-state={currentPhase.state}>
        <div>
          <span className="journey-chapter-kicker">
            {dictionary.journey.chapterLabel}{" "}
            {String(currentIndex + 1).padStart(2, "0")}
          </span>
          <span>{dictionary.journey.missionLabel}</span>
          <h3>{dictionary.journey.phaseLabels[currentPhase.key]}</h3>
          <p>{dictionary.journey.phaseDescriptions[currentPhase.key]}</p>
          <small>{dictionary.journey.phaseOutcomes[currentPhase.key]}</small>
        </div>
        {currentPhase.state === "BLOCKED" ? (
          <div className="journey-blocked-action" role="status">
            <strong>{dictionary.journey.blockedTitle}</strong>
            <span>{dictionary.journey.blockedBody}</span>
          </div>
        ) : (
          <Link
            href={campaignChapterHref(locale, currentPhase.key) as Route}
            transitionTypes={["chapter-forward"]}
          >
            {dictionary.journey.phaseActions[currentPhase.key]}
          </Link>
        )}
      </article>

      <ol className="journey-horizon">
        {journey.phases.map((phase, index) => {
          const current = phase.key === currentPhase.key;
          return (
            <li
              key={phase.key}
              data-state={phase.state}
              data-current={current}
              aria-current={current ? "step" : undefined}
            >
              <span className="journey-index" aria-hidden="true">
                {String(index + 1).padStart(2, "0")}
              </span>
              <div>
                <span className="journey-status">
                  {dictionary.journey.statusLabels[phase.state]}
                </span>
                <h3>{dictionary.journey.phaseLabels[phase.key]}</h3>
                <p>{dictionary.journey.phaseDescriptions[phase.key]}</p>
                <small>{dictionary.journey.phaseOutcomes[phase.key]}</small>
                {phase.state === "BLOCKED" ? (
                  <span className="journey-blocked-explanation">
                    <strong>{dictionary.journey.blockedTitle}</strong>
                    {dictionary.journey.blockedBody}
                  </span>
                ) : null}
              </div>
              {phase.state === "LOCKED" || phase.state === "BLOCKED" ? (
                <span className="journey-lock" aria-hidden="true">
                  ·
                </span>
              ) : (
                <Link
                  className="journey-open"
                  href={campaignChapterHref(locale, phase.key) as Route}
                  transitionTypes={["chapter-forward"]}
                >
                  {dictionary.journey.openPhase}
                </Link>
              )}
            </li>
          );
        })}
      </ol>

      <p className="journey-boundary">{dictionary.journey.boundary}</p>
    </section>
  );
}
