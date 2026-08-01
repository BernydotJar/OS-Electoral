import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { ChapterOrientation } from "@/components/chapter-orientation";
import type {
  CampaignJourney,
  CampaignJourneyPhase,
  CampaignJourneyPhaseKey,
} from "@/lib/campaign-journey";
import { dictionaryFor } from "@/lib/i18n";

const dictionary = dictionaryFor("es");
const keys: readonly CampaignJourneyPhaseKey[] = [
  "foundation",
  "evidence",
  "team",
  "strategy",
  "operations",
];
const phases: readonly CampaignJourneyPhase[] = keys.map((key, index) => ({
  key,
  state: index === 1 ? "ACTIVE" : "AVAILABLE",
  href: `#${key}`,
}));
const journey: CampaignJourney = {
  phases,
  currentPhase: "evidence",
  completedPhaseCount: 0,
  releaseAuthority: "NONE",
};

describe("ChapterOrientation", () => {
  it.each(keys.map((key, index) => [key, index] as const))(
    "explains position and next work for %s",
    (key, index) => {
      const selected = phases[index]!;
      const html = renderToStaticMarkup(
        createElement(ChapterOrientation, {
          dictionary,
          journey,
          selected,
        }),
      );

      expect(html).toContain('class="chapter-orientation"');
      expect(html).toContain(`Capítulo actual ${index + 1}/5`);
      expect(html).toContain(dictionary.journey.phaseLabels[key]);
      expect(html).toContain(dictionary.journey.phaseOutcomes[key]);
      expect(html).toContain(dictionary.journey.phaseActions[key]);
    },
  );
});
