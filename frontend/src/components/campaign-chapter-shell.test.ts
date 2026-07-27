import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
vi.mock("react", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react")>();
  return {
    ...actual,
    ViewTransition: ({ children }: { children: React.ReactNode }) => children,
  };
});

import { CampaignShell } from "@/components/shell";
import {
  demoCampaign,
  demoCandidateWorkspace,
  demoCampaignRoadmap,
  demoGuidedIntake,
  demoReadiness,
  demoStrategyWorkspace,
  demoTeamWorkspace,
  demoTenantIdentity,
  demoWarRoomSnapshot,
} from "@/lib/demo-data";
import { dictionaryFor } from "@/lib/i18n";
import type { ShellViewModel } from "@/lib/shell-view-model";

const model: ShellViewModel = {
  kind: "authorized",
  demo: true,
  identity: demoTenantIdentity,
  memberships: demoTenantIdentity.application_memberships,
  campaign: demoCampaign,
  campaigns: [demoCampaign],
  readiness: demoReadiness,
  readinessUnavailable: false,
  guidedIntake: demoGuidedIntake,
  guidedIntakeAvailability: "AVAILABLE",
  candidateWorkspace: demoCandidateWorkspace,
  candidateWorkspaceAvailability: "AVAILABLE",
  teamWorkspace: demoTeamWorkspace,
  teamWorkspaceAvailability: "AVAILABLE",
  teamTemplatePreview: null,
  teamTemplatePreviewUnavailable: false,
  campaignRoadmap: demoCampaignRoadmap,
  campaignRoadmapAvailability: "AVAILABLE",
  warRoomSnapshot: demoWarRoomSnapshot,
  warRoomSnapshotAvailability: "AVAILABLE",
  strategyWorkspace: demoStrategyWorkspace,
  strategyWorkspaceAvailability: "AVAILABLE",
};

function render(selectedChapter: "team" | null): string {
  return renderToStaticMarkup(
    createElement(CampaignShell, {
      locale: "es",
      dictionary: dictionaryFor("es"),
      model,
      selectedChapter,
    }),
  );
}

describe("CampaignShell chapter routes", () => {
  it("keeps the command overview focused on roadmap and campaign context", () => {
    const html = render(null);

    expect(html).toContain('id="campaign-journey"');
    expect(html).toContain('id="campaigns"');
    expect(html).not.toContain('id="guided-intake"');
    expect(html).not.toContain('id="candidate-workspace"');
    expect(html).not.toContain('id="team-workspace"');
    expect(html).not.toContain('id="strategy-room"');
    expect(html).not.toContain('id="war-room"');
  });

  it("renders only the selected team mission on the team chapter route", () => {
    const html = render("team");

    expect(html).toContain('data-chapter="team"');
    expect(html).toContain('id="team-workspace"');
    expect(html).toContain('class="chapter-navigation"');
    expect(html).not.toContain('id="campaign-journey"');
    expect(html).not.toContain('id="campaigns"');
    expect(html).not.toContain('id="guided-intake"');
    expect(html).not.toContain('id="candidate-workspace"');
    expect(html).not.toContain('id="strategy-room"');
    expect(html).not.toContain('id="war-room"');
  });
});
