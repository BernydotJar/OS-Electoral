import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { CampaignExperienceHero } from "@/components/campaign-experience-hero";
import { CampaignLaunchRoadmap } from "@/components/campaign-launch-roadmap";
import type { CampaignJourney, CampaignJourneyPhase } from "@/lib/campaign-journey";
import { dictionaryFor } from "@/lib/i18n";

const dictionary = dictionaryFor("es");

const phases: CampaignJourneyPhase[] = [
  { key: "foundation", state: "COMPLETE", href: "#guided-intake" },
  { key: "evidence", state: "ACTIVE", href: "#candidate-workspace" },
  { key: "team", state: "AVAILABLE", href: "#team-workspace" },
  { key: "strategy", state: "LOCKED", href: "#strategy-room" },
  { key: "operations", state: "BLOCKED", href: "#war-room" },
];

const journey: CampaignJourney = {
  currentPhase: "evidence",
  completedPhaseCount: 1,
  releaseAuthority: "NONE",
  phases,
};

function hero(mode: "FIRST_USE" | "ACTIVE" | "COMPLETE") {
  return renderToStaticMarkup(
    createElement(CampaignExperienceHero, {
      dictionary,
      mode,
      campaignName: "Campaña Horizonte",
      currentPhase: phases[1]!,
      journey,
    }),
  );
}

describe("CampaignExperienceHero", () => {
  it("renders a five-act owned cinematic story for first use", () => {
    const html = hero("FIRST_USE");

    expect(html).toContain('data-layout="opening"');
    expect(html).toContain('class="experience-storyboard"');
    expect(html.match(/data-scene=/g)).toHaveLength(5);
    expect(html).toContain("Territorio");
    expect(html).toContain("Evidencia");
    expect(html).toContain("Equipo");
    expect(html).toContain("Estrategia");
    expect(html).toContain("Operación");
    expect(html).not.toContain("<video");
    expect(html).not.toContain("sceneai.art");
  });

  it("renders a compact active mission with real progress", () => {
    const html = hero("ACTIVE");

    expect(html).toContain('data-layout="mission"');
    expect(html).toContain('aria-valuenow="1"');
    expect(html).toContain('aria-valuemax="5"');
    expect(html).toContain("Conocer la candidatura y el territorio");
    expect(html).toContain('class="experience-hint"');
    expect(html).toContain("Por qué importa");
    expect(html).toContain('class="experience-chapter-mark"');
    expect(html).toContain('class="experience-horizon-light"');
    expect(html).not.toContain("Tu campaña empieza aquí");
  });

  it("renders a command-center completion state instead of onboarding", () => {
    const html = hero("COMPLETE");

    expect(html).toContain('data-layout="command"');
    expect(html).toContain(dictionary.journey.commandCenterLabel);
    expect(html).toContain(dictionary.journey.completeTitle);
    expect(html).not.toContain(dictionary.journey.firstUseAction);
  });
});

describe("CampaignLaunchRoadmap", () => {
  it("renders one dominant chapter with accessible current-step semantics", () => {
    const html = renderToStaticMarkup(
      createElement(CampaignLaunchRoadmap, { dictionary, journey }),
    );

    expect(html).toContain('class="journey-chapter"');
    expect(html).toContain('aria-current="step"');
    expect(html).toContain('data-current="true"');
    expect(html).toContain('class="journey-horizon"');
  });

  it("explains blocked chapters in text without presenting a broken link", () => {
    const html = renderToStaticMarkup(
      createElement(CampaignLaunchRoadmap, { dictionary, journey }),
    );

    expect(html).toContain(dictionary.journey.blockedTitle);
    expect(html).toContain(dictionary.journey.blockedBody);
    expect(html).not.toMatch(/href="#war-room"/);
  });
});
