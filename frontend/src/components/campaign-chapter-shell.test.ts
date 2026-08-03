import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: vi.fn() }),
}));
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

function render(
  selectedChapter: "foundation" | "evidence" | "team" | null,
  notice: "authorization_denied" | null = null,
): string {
  return renderToStaticMarkup(
    createElement(CampaignShell, {
      locale: "es",
      dictionary: dictionaryFor("es"),
      model,
      selectedChapter,
      notice,
    }),
  );
}

describe("CampaignShell chapter routes", () => {
  it("keeps the command overview focused on roadmap and campaign context", () => {
    const html = render(null);

    expect(html).toContain('class="topbar topbar-overview"');
    expect(html).toContain('class="context-strip"');
    expect(html).toContain('class="campaign-command-overview"');
    expect(html).toContain('id="campaign-journey"');
    expect(html).not.toContain('class="campaign-experience"');
    expect(html).toContain('id="campaigns"');
    expect(html).toContain('id="candidate-summary"');
    expect(html).toContain("Resumen de candidatura");
    expect(html).toContain("Qué hacer ahora");
    expect(html).not.toContain('id="readiness"');
    expect(html).not.toContain('id="guided-intake"');
    expect(html).not.toContain('id="candidate-workspace"');
    expect(html).not.toContain('id="team-workspace"');
    expect(html).not.toContain('id="strategy-room"');
    expect(html).not.toContain('id="war-room"');
  });

  it("lets an authorized empty tenant create its first draft", () => {
    const emptyModel: ShellViewModel = {
      kind: "empty",
      demo: false,
      identity: demoTenantIdentity,
    };
    const html = renderToStaticMarkup(
      createElement(CampaignShell, {
        locale: "es",
        dictionary: dictionaryFor("es"),
        model: emptyModel,
      }),
    );

    expect(html).toContain('class="empty-campaign-page"');
    expect(html).toContain("Nueva candidatura");
    expect(html).toContain('action="/api/ui/campaign-context/create"');
  });

  it("renders only the selected team mission on the team chapter route", () => {
    const html = render("team");

    expect(html).toContain('data-chapter="team"');
    expect(html).toContain('id="team-workspace"');
    expect(html).toContain('class="chapter-command-bar"');
    expect(html).toContain('class="chapter-orientation"');
    expect(html).toContain("Capítulo actual 3/5");
    expect(html).toContain("Organizar el equipo");
    expect(html).toContain('class="topbar topbar-compact"');
    expect(html).toContain('class="topbar-context"');
    expect(html).toContain('class="session-context-menu"');
    expect(html).toContain(">Equipo</p>");
    expect(html).not.toContain('class="context-strip"');
    expect(html).not.toContain(dictionaryFor("es").shell.title);
    expect(html).not.toContain('class="campaign-experience"');
    expect(html).not.toContain("MISIÓN ACTIVA");
    expect(html).not.toContain('id="campaign-journey"');
    expect(html).not.toContain('id="campaigns"');
    expect(html).not.toContain('id="guided-intake"');
    expect(html).not.toContain('id="candidate-workspace"');
    expect(html).not.toContain('id="strategy-room"');
    expect(html).not.toContain('id="war-room"');
  });

  it("keeps the candidate profile visible without a three-tab selector", () => {
    const html = render("evidence");

    expect(html).toContain('data-chapter="evidence"');
    expect(html).toContain('class="chapter-orientation"');
    expect(html).toContain("Capítulo actual 2/5");
    expect(html).toContain("Conocer la candidatura y el territorio");
    expect(html).toContain(
      'class="candidate-workspace-deck candidate-workspace-single"',
    );
    expect(html).toContain("Perfil y riesgos");
    expect(html).toContain(
      "Revisa lo confirmado, las contradicciones, el desarrollo pendiente y los riesgos de la candidatura.",
    );
    expect(html).toContain('class="candidate-evidence-disclosure"');
    expect(html).not.toContain("Resumen de candidatura");
    expect(html).not.toContain("Qué hacer ahora");
    expect(html).not.toContain('role="tablist"');
  });

  it("keeps authorization feedback compact and dismissible", () => {
    const html = render("team", "authorization_denied");

    expect(html).toContain('data-notice="authorization_denied"');
    expect(html).toContain("Esta acción necesita un permiso adicional");
    expect(html).toContain("Cerrar aviso");
    expect(html).toContain("/es/campaign/team#team-workspace");
    expect(html).toContain('id="team-workspace"');
  });

  it("treats completed guided intake as a revisable one-time setup", () => {
    const html = render("foundation");

    expect(html).toContain('id="readiness"');
    expect(html).toContain("BASE OPERATIVA");
    expect(html).toContain("Preparación operativa");
    expect(html).toContain("Espacios de trabajo activos");
    expect(html).toContain('id="guided-intake"');
    expect(html).toContain('data-complete="true"');
    expect(html).toContain("Ver la configuración registrada");
    expect(html).toContain('class="guided-intake-review"');
    expect(html).not.toContain('class="campaign-experience"');
  });
});
