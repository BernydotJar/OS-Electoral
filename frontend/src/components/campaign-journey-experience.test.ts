import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { CampaignLaunchRoadmap } from "@/components/campaign-launch-roadmap";
import type {
  CampaignJourney,
  CampaignJourneyPhase,
} from "@/lib/campaign-journey";
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

function renderRoadmap(value: CampaignJourney = journey): string {
  return renderToStaticMarkup(
    createElement(CampaignLaunchRoadmap, {
      locale: "es",
      dictionary,
      journey: value,
    }),
  );
}

describe("CampaignLaunchRoadmap", () => {
  it("renders one restrained command overview without the former mission hero", () => {
    const html = renderRoadmap();

    expect(html).toContain('class="campaign-command-overview"');
    expect(html).toContain('class="command-priority"');
    expect(html).toContain(dictionary.journey.title);
    expect(html).toContain(dictionary.journey.commandPriorityLabel);
    expect(html).toContain("Conocer la candidatura y el territorio");
    expect(html).toContain('aria-current="step"');
    expect(html).not.toContain('class="campaign-experience"');
    expect(html).not.toContain("MISIÓN ACTIVA");
  });

  it("keeps the full path available through an accessible disclosure", () => {
    const html = renderRoadmap();

    expect(html).toContain('class="command-path-disclosure"');
    expect(html).toContain(dictionary.journey.explorePathLabel);
    expect(html.match(/class="command-path-index"/g)).toHaveLength(5);
    expect(html).toContain('href="/es/campaign/evidence#candidate-workspace"');
  });

  it("explains blocked stages without presenting a broken workspace action", () => {
    const html = renderRoadmap();

    expect(html).toContain(dictionary.journey.blockedTitle);
    expect(html).toContain(dictionary.journey.blockedBody);
    expect(html).not.toContain('href="/es/campaign/operations#war-room"');
  });
});
