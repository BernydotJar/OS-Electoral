import type { CampaignExperienceMode } from "@/lib/campaign-experience";
import type { CampaignJourneyPhase } from "@/lib/campaign-journey";
import type { Dictionary } from "@/lib/i18n";

export function CampaignExperienceHero({
  dictionary,
  mode,
  campaignName,
  currentPhase,
}: Readonly<{
  dictionary: Dictionary;
  mode: CampaignExperienceMode;
  campaignName: string;
  currentPhase: CampaignJourneyPhase;
}>) {
  const firstUse = mode === "FIRST_USE";
  const complete = mode === "COMPLETE";
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
    : dictionary.journey.resumeAction;

  return (
    <section className="campaign-experience" data-mode={mode} aria-labelledby="experience-title">
      <div className="experience-atmosphere" aria-hidden="true">
        <span />
        <span />
        <span />
      </div>
      <div className="experience-copy">
        <p className="eyebrow">{eyebrow}</p>
        <h1 id="experience-title">{title}</h1>
        <p>{body}</p>
        <a href={firstUse ? "#guided-intake" : currentPhase.href}>
          <span>{action}</span>
          <span className="experience-arrow" aria-hidden="true">→</span>
        </a>
      </div>
      <div className="experience-context" aria-label={dictionary.journey.progressLabel}>
        <span>{dictionary.shell.campaign}</span>
        <strong>{campaignName}</strong>
        <small>
          {dictionary.journey.phaseLabels[currentPhase.key]} · {dictionary.journey.statusLabels[currentPhase.state]}
        </small>
      </div>
    </section>
  );
}
