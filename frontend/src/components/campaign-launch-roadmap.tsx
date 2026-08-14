
import { campaignChapterHref } from "@/lib/campaign-chapters";
import type {
  CampaignJourney,
  CampaignJourneyPhase,
} from "@/lib/campaign-journey";
import type { Dictionary, Locale } from "@/lib/i18n";

function navigable(phase: CampaignJourneyPhase): boolean {
  return phase.state !== "LOCKED" && phase.state !== "BLOCKED";
}

export function CampaignLaunchRoadmap({
  locale,
  dictionary,
  journey,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  journey: CampaignJourney;
}>) {
  const currentPhase =
    journey.phases.find((phase) => phase.key === journey.currentPhase) ??
    journey.phases[0];
  if (!currentPhase) return null;

  const currentIndex = journey.phases.findIndex(
    (phase) => phase.key === currentPhase.key,
  );
  const progress =
    journey.phases.length === 0
      ? 0
      : Math.round((journey.completedPhaseCount / journey.phases.length) * 100);

  return (
    <section
      id="campaign-journey"
      className="campaign-command-overview"
      aria-labelledby="campaign-journey-title"
    >
      <header className="command-overview-heading">
        <div>
          <p className="eyebrow">{dictionary.journey.eyebrow}</p>
          <h1 id="campaign-journey-title">{dictionary.journey.title}</h1>
          <p>{dictionary.journey.body}</p>
        </div>
        <div
          className="command-overview-progress"
          aria-label={dictionary.journey.progressLabel}
        >
          <span>{dictionary.journey.stageLabel}</span>
          <strong>
            {currentIndex + 1}
            <small>/{journey.phases.length}</small>
          </strong>
          <progress
            aria-label={dictionary.journey.progressLabel}
            max={journey.phases.length}
            value={journey.completedPhaseCount}
          >
            {progress}%
          </progress>
          <small>
            {journey.completedPhaseCount} {dictionary.journey.completedLabel}
          </small>
        </div>
      </header>

      <div className="command-overview-focus">
        <article className="command-priority" data-state={currentPhase.state}>
          <div className="command-priority-index" aria-hidden="true">
            {String(currentIndex + 1).padStart(2, "0")}
          </div>
          <div className="command-priority-copy">
            <span>{dictionary.journey.commandPriorityLabel}</span>
            <h2>{dictionary.journey.phaseLabels[currentPhase.key]}</h2>
            <p>{dictionary.journey.phaseDescriptions[currentPhase.key]}</p>
            <dl>
              <div>
                <dt>{dictionary.journey.statusLabel}</dt>
                <dd>{dictionary.journey.statusLabels[currentPhase.state]}</dd>
              </div>
              <div>
                <dt>{dictionary.journey.outcomeLabel}</dt>
                <dd>{dictionary.journey.phaseOutcomes[currentPhase.key]}</dd>
              </div>
            </dl>
          </div>
          {navigable(currentPhase) ? (
            <a
              href={campaignChapterHref(locale, currentPhase.key)}
            >
              <span>{dictionary.journey.phaseActions[currentPhase.key]}</span>
              <span aria-hidden="true">→</span>
            </a>
          ) : (
            <div className="command-priority-blocked" role="status">
              <strong>{dictionary.journey.blockedTitle}</strong>
              <span>{dictionary.journey.blockedBody}</span>
            </div>
          )}
        </article>

        <nav
          className="command-stage-navigation"
          aria-label={dictionary.journey.stageNavigationLabel}
        >
          <ol>
            {journey.phases.map((phase, index) => {
              const current = phase.key === currentPhase.key;
              const content = (
                <>
                  <span>{String(index + 1).padStart(2, "0")}</span>
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
                  {navigable(phase) ? (
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
        </nav>
      </div>

      <details className="command-path-disclosure">
        <summary>
          <span>{dictionary.journey.explorePathLabel}</span>
          <small>{dictionary.journey.explorePathBody}</small>
        </summary>
        <ol className="command-path-grid">
          {journey.phases.map((phase, index) => (
            <li
              key={phase.key}
              data-state={phase.state}
              data-current={phase.key === currentPhase.key}
            >
              <div>
                <span className="command-path-index" aria-hidden="true">
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span className="command-path-status">
                  {dictionary.journey.statusLabels[phase.state]}
                </span>
              </div>
              <h3>{dictionary.journey.phaseLabels[phase.key]}</h3>
              <p>{dictionary.journey.phaseDescriptions[phase.key]}</p>
              <small>{dictionary.journey.phaseOutcomes[phase.key]}</small>
              {navigable(phase) ? (
                <a
                  href={campaignChapterHref(locale, phase.key)}
                >
                  {dictionary.journey.openPhase}
                </a>
              ) : phase.state === "BLOCKED" ? (
                <span className="command-path-locked">
                  <strong>{dictionary.journey.blockedTitle}</strong>
                  <span>{dictionary.journey.blockedBody}</span>
                </span>
              ) : (
                <span className="command-path-locked">
                  {dictionary.journey.statusLabels[phase.state]}
                </span>
              )}
            </li>
          ))}
        </ol>
      </details>

      <p className="journey-boundary">{dictionary.journey.boundary}</p>
    </section>
  );
}
