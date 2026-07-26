import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

import { TeamWorkspaceEditor } from "@/components/team-workspace-editor";
import type { TeamWorkspaceTemplatePreview } from "@/lib/contracts";
import { demoTeamWorkspace } from "@/lib/demo-data";
import { dictionaryFor } from "@/lib/i18n";

const dictionary = dictionaryFor("es");
const preview: TeamWorkspaceTemplatePreview = {
  audit_event_id: demoTeamWorkspace.audit_event_id,
  workspace_id: demoTeamWorkspace.workspace.id,
  tenant_id: demoTeamWorkspace.workspace.tenant_id,
  campaign_id: demoTeamWorkspace.workspace.campaign_id,
  workspace_version: demoTeamWorkspace.workspace.version,
  organization_template: "FULL_CAMPAIGN",
  blueprint_locale: "es",
  blueprint_version: "2026-07-25.1",
  additions: [
    {
      id: "abababab-abab-4bab-8bab-abababababab",
      title: "Estrategia digital",
      area: "Digital",
      purpose: "Preparar planes digitales gobernados y medibles.",
      responsibilities: ["Mantener hipótesis", "Escalar riesgos de privacidad"],
      status: "VACANT",
      principal_id: null,
      availability_status: "UNASSESSED",
      weekly_capacity_hours: null,
      onboarding_status: "NOT_STARTED",
      vacancy_plan: "Seleccionar y aprobar humanamente el perfil.",
    },
  ],
  skipped: [
    {
      blueprint_key: "campaign_direction",
      title: "Jefatura de campaña",
      area: "Dirección de campaña",
      matched_role_id: "cdcdcdcd-cdcd-4dcd-8dcd-cdcdcdcdcdcd",
      reason: "CANONICAL_BLUEPRINT_MATCH",
    },
  ],
  preview_digest: "a".repeat(64),
  authority_effect: "NONE",
  external_effects: "NONE",
};

function render(templatePreview: TeamWorkspaceTemplatePreview | null): string {
  return renderToStaticMarkup(
    createElement(TeamWorkspaceEditor, {
      locale: "es",
      dictionary,
      demo: false,
      availability: "AVAILABLE",
      workspace: demoTeamWorkspace.workspace,
      templatePreview,
      templatePreviewUnavailable: false,
      capabilities: { canStart: true, canRead: true, canUpdate: true },
      prerequisiteReady: true,
    }),
  );
}

describe("TeamWorkspaceEditor template application", () => {
  it("renders preview selection separately from manual role creation", () => {
    const html = render(null);

    expect(html).toContain('name="team_template"');
    expect(html).toContain("Previsualizar cambios");
    expect(html).toContain("/api/ui/team-workspace/role");
    expect(html).not.toContain("/api/ui/team-workspace/template-apply");
  });

  it("renders additions, preserved roles, digest confirmation, and no authority claim", () => {
    const html = render(preview);

    expect(html).toContain("Funciones nuevas propuestas");
    expect(html).toContain("Estrategia digital");
    expect(html).toContain("Funciones existentes que se conservarán");
    expect(html).toContain("Jefatura de campaña");
    expect(html).toContain("/api/ui/team-workspace/template-apply");
    expect(html).toContain('name="preview_digest"');
    expect(html).toContain("a".repeat(64));
    expect(html).toContain("No asigna personas");
  });

  it("does not render an apply button when the authoritative preview is a no-op", () => {
    const html = render({ ...preview, additions: [] });

    expect(html).toContain(dictionary.teamWorkspace.templateNoChanges);
    expect(html).not.toContain("/api/ui/team-workspace/template-apply");
  });
});
