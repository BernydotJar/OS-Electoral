import type { CSSProperties } from "react";

import { campaignChapterHref } from "@/lib/campaign-chapters";

import type { CampaignExperienceMode } from "@/lib/campaign-experience";
import type {
  CampaignJourney,
  CampaignJourneyPhase,
} from "@/lib/campaign-journey";
import type { Dictionary } from "@/lib/i18n";

export function CampaignExperienceHero({
  locale,
  dictionary,
  mode,
  campaignName,
  currentPhase,
  journey,
}: Readonly<{
  locale: "es" | "en";
  dictionary: Dictionary;
  mode: CampaignExperienceMode;
  campaignName: string;
  currentPhase: CampaignJourneyPhase;
  journey: CampaignJourney;
}>) {
  const firstUse = mode === "FIRST_USE";
  const complete = mode === "COMPLETE";
  const layout = firstUse ? "opening" : complete ? "command" : "mission";
  const title = firstUse
    ? dictionary.journey.firstUseTitle
    : complete
      ? dictionary.journey.completeTitle
      : dictionary.journey.phaseLabels[currentPhase.key];
  const body = firstUse
    ? dictionary.journey.firstUseBody
    : complete
      ? dictionary.journey.completeBody
      : dictionary.journey.activeBody;
  const eyebrow = firstUse
    ? dictionary.journey.firstUseEyebrow
    : complete
      ? dictionary.journey.completeEyebrow
      : dictionary.journey.activeEyebrow;
  const action = firstUse
    ? dictionary.journey.firstUseAction
    : complete
      ? dictionary.journey.commandCenterAction
      : dictionary.journey.resumeAction;
  const actionHref = campaignChapterHref(
    locale,
    firstUse ? "foundation" : complete ? "operations" : currentPhase.key,
  );
  const progress =
    journey.phases.length === 0
      ? 0
      : (journey.completedPhaseCount / journey.phases.length) * 100;
  const currentChapter = Math.max(
    1,
    journey.phases.findIndex((phase) => phase.key === currentPhase.key) + 1,
  );

  return (
    <section
      className="campaign-experience"
      data-mode={mode}
      data-layout={layout}
      aria-labelledby="experience-title"
      data-chapter={currentPhase.key}
    >
      <div className="experience-atmosphere" aria-hidden="true">
        <span className="experience-orbit experience-orbit-one" />
        <span className="experience-orbit experience-orbit-two" />
        <span className="experience-beacon" />
        <span className="experience-grid" />
        <span className="experience-horizon-light" />
        <span className="experience-aurora" />
        <span className="experience-signal" />
        <span className="experience-sweep" />
      </div>

      {!firstUse ? (
        <span className="experience-chapter-mark" aria-hidden="true">
          {String(currentChapter).padStart(2, "0")}
        </span>
      ) : null}

      <div className="experience-copy">
        <p className="eyebrow">{eyebrow}</p>
        <h1 id="experience-title">{title}</h1>
        {firstUse ? (
          <p>{body}</p>
        ) : (
          <details className="experience-hint">
            <summary>{dictionary.journey.contextHintLabel}</summary>
            <p>{body}</p>
          </details>
        )}
        <a href={actionHref}>
          <span>{action}</span>
          <span className="experience-arrow" aria-hidden="true">
            →
          </span>
        </a>
        <ol
          className="experience-mission-pulse"
          aria-label={dictionary.journey.missionPulseLabel}
        >
          {Object.entries(dictionary.journey.missionPulseStages).map(
            ([stage, label], index) => (
              <li
                key={stage}
                data-stage={stage}
                style={{ "--pulse-index": index } as CSSProperties}
              >
                <i aria-hidden="true" />
                <span>{label}</span>
              </li>
            ),
          )}
        </ol>
      </div>

      {firstUse ? (
        <div className="experience-storyboard" aria-hidden="true">
          {journey.phases.map((phase, index) => (
            <span
              key={phase.key}
              data-scene={phase.key}
              style={{ "--scene-index": index } as CSSProperties}
            >
              <i />
              {dictionary.journey.sceneLabels[phase.key]}
            </span>
          ))}
        </div>
      ) : null}

      <div
        className="experience-context"
        aria-label={dictionary.journey.progressLabel}
      >
        <span>
          {complete
            ? dictionary.journey.commandCenterLabel
            : dictionary.shell.campaign}
        </span>
        <strong>{campaignName}</strong>
        <small>
          {dictionary.journey.phaseLabels[currentPhase.key]} ·{" "}
          {dictionary.journey.statusLabels[currentPhase.state]}
        </small>
        <div
          className="experience-progress"
          role="progressbar"
          aria-label={dictionary.journey.progressLabel}
          aria-valuemin={0}
          aria-valuemax={journey.phases.length}
          aria-valuenow={journey.completedPhaseCount}
        >
          <span
            style={{ "--journey-progress": `${progress}%` } as CSSProperties}
          />
        </div>
      </div>
    </section>
  );
}
