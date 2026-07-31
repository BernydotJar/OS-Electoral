import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { CandidateActionBrief } from "@/components/candidate-action-brief";
import { CandidateWorkspaceDeck } from "@/components/candidate-workspace-deck";
import { TeamOperationsDeck } from "@/components/team-operations-deck";
import type { CandidateWorkspaceProjection } from "@/lib/contracts";
import { dictionaryFor } from "@/lib/i18n";

const dictionary = dictionaryFor("es");
const candidate: CandidateWorkspaceProjection = {
  id: "11111111-1111-4111-8111-111111111111",
  tenant_id: "22222222-2222-4222-8222-222222222222",
  campaign_id: "33333333-3333-4333-8333-333333333333",
  campaign_version: 1,
  campaign_status: "ACTIVE",
  campaign_name: "Campaña local",
  jurisdiction: "Municipio",
  candidate_id: "44444444-4444-4444-8444-444444444444",
  display_name: "Candidatura",
  status: "UNDER_REVIEW",
  public_use_status: "BLOCKED",
  external_effects: "NONE",
  evidence: [],
  identity: null,
  biography: null,
  purpose: null,
  values: null,
  attributes: null,
  contradictions: null,
  development_goals: null,
  reputation_risks: null,
  checks: [],
  completed_checks: 0,
  total_checks: 9,
  approvable_sections: [],
  current_approved_sections: [],
  approvals_required: ["identity"],
  open_critical_high_risks: 0,
  next_action: "DEFINE_IDENTITY",
  limitation_codes: [
    "NOT_PUBLIC_POSITIONING_APPROVAL",
    "NOT_A_STRATEGY",
    "NO_VOTER_PROFILING",
    "NO_EXTERNAL_EFFECTS",
    "HUMAN_REVIEW_REQUIRED",
  ],
  version: 1,
  created_at: "2026-07-28T00:00:00Z",
  updated_at: "2026-07-28T00:00:00Z",
};

describe("organic workspace decks", () => {
  it("starts the candidate workspace on actions and keeps profile and evidence in separate panels", () => {
    const html = renderToStaticMarkup(
      createElement(CandidateWorkspaceDeck, {
        dictionary,
        actions: createElement("div", null, "Acciones"),
        profile: createElement("div", null, "Perfil"),
        evidence: createElement("div", null, "Evidencia"),
      }),
    );

    expect(html).toContain('role="tablist"');
    expect(html).toContain('aria-selected="true"');
    expect(html).toContain('id="candidate-actions-panel"');
    expect(html).toContain('id="candidate-profile-panel"');
    expect(html).toContain('id="candidate-evidence-panel"');
    expect(html.match(/hidden=""/g)?.length).toBe(2);
  });

  it("renders one visible team operation panel while retaining an inert alternate panel", () => {
    const html = renderToStaticMarkup(
      createElement(TeamOperationsDeck, {
        dictionary,
        hasWorkItems: true,
        creator: createElement("div", null, "Crear seguimiento"),
        board: createElement("div", null, "Tablero operativo"),
      }),
    );

    expect(html).toContain('role="tablist"');
    expect(html).toContain("Tablero operativo");
    expect(html).toContain("Crear seguimiento");
    expect(html).toContain("Vista de mando");
    expect(html).toContain('aria-selected="true"');
    expect(html).toContain('data-active="true"');
    expect(html).toContain('data-active="false"');
    expect(html).toContain('aria-hidden="true"');
    expect(html).toContain('inert=""');
    expect(html).not.toContain('hidden=""');
  });

  it("renders candidate actions with grounded counts and no public-use claim", () => {
    const html = renderToStaticMarkup(
      createElement(CandidateActionBrief, {
        dictionary,
        workspace: candidate,
      }),
    );

    expect(html).toContain("Qué debemos resolver ahora");
    expect(html).toContain("Definir y verificar identidad");
    expect(html).toContain("Falta evidencia verificable");
    expect(html).toContain("Preparación interna activa");
    expect(html).not.toContain("publicar ahora");
  });
});
