import type { CampaignJourney } from "@/lib/campaign-journey";
import type { Dictionary } from "@/lib/i18n";

export function CampaignLaunchRoadmap({
  dictionary,
  journey,
}: {
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

      <div className="journey-mission">
        <div>
          <span>{dictionary.journey.missionLabel}</span>
          <h3>{dictionary.journey.phaseLabels[currentPhase.key]}</h3>
          <p>{dictionary.journey.phaseDescriptions[currentPhase.key]}</p>
        </div>
        {currentPhase.state === "BLOCKED" ? (
          <span className="journey-blocked-action">
            {dictionary.journey.blockedAction}
          </span>
        ) : (
          <a href={currentPhase.href}>
            {dictionary.journey.phaseActions[currentPhase.key]}
          </a>
        )}
      </div>

      <ol className="journey-track">
        {journey.phases.map((phase, index) => (
          <li key={phase.key} data-state={phase.state}>
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
            </div>
            {phase.state === "LOCKED" || phase.state === "BLOCKED" ? (
              <span className="journey-lock" aria-hidden="true">
                ·
              </span>
            ) : (
              <a className="journey-open" href={phase.href}>
                {dictionary.journey.openPhase}
              </a>
            )}
          </li>
        ))}
      </ol>

      <p className="journey-boundary">{dictionary.journey.boundary}</p>
    </section>
  );
}
