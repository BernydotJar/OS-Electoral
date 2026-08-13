import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { TeamReadinessCompletion } from "@/components/team-readiness-completion";
import type { TeamWorkspaceProjection } from "@/lib/contracts";
import { dictionaryFor } from "@/lib/i18n";

const dictionary = dictionaryFor("es");
const workspace: TeamWorkspaceProjection = {
  id: "11111111-1111-4111-8111-111111111111",
  tenant_id: "22222222-2222-4222-8222-222222222222",
  campaign_id: "33333333-3333-4333-8333-333333333333",
  campaign_version: 1,
  campaign_status: "ACTIVE",
  campaign_name: "Campaña",
  organization_template: "LEAN_CAMPAIGN",
  roles: [
    {
      id: "44444444-4444-4444-8444-444444444444",
      title: "Dirección",
      area: "Dirección",
      purpose: "Coordinar",
      responsibilities: ["Coordinar"],
      decision_scope: ["Preparar decisiones"],
      deliverables: ["Agenda"],
      collaboration_points: ["Equipo"],
      success_signals: ["Decisiones visibles"],
      status: "VACANT",
      principal_id: null,
      availability_status: "UNASSESSED",
      weekly_capacity_hours: null,
      onboarding_status: "NOT_STARTED",
      vacancy_plan: "Cubrir con aprobación humana.",
    },
  ],
  work_items: [],
  training_requirements: null,
  access_recommendations: null,
  status: "STRUCTURE_IN_PROGRESS",
  checks: [],
  completed_checks: 5,
  total_checks: 8,
  filled_role_count: 0,
  vacant_role_count: 1,
  total_weekly_capacity_hours: 0,
  total_work_item_count: 0,
  planned_work_item_count: 0,
  active_work_item_count: 0,
  blocked_work_item_count: 0,
  completed_work_item_count: 0,
  attention_work_item_count: 0,
  next_action: "ASSIGN_ACCOUNTABILITY",
  authority_effect: "NONE",
  external_effects: "NONE",
  limitation_codes: [
    "ROLE_LABELS_ARE_NOT_PERMISSIONS",
    "ACCESS_RECOMMENDATIONS_REQUIRE_HUMAN_AUTHORIZATION",
    "NO_VOTER_PROFILING",
    "NO_EXTERNAL_EFFECTS",
  ],
  version: 3,
  created_at: "2026-08-12T00:00:00Z",
  updated_at: "2026-08-12T00:00:00Z",
};

const writable = { canStart: true, canRead: true, canUpdate: true };

describe("TeamReadinessCompletion", () => {
  it("renders explicit reviewed-empty controls and bounded record editors", () => {
    const html = renderToStaticMarkup(
      createElement(TeamReadinessCompletion, {
        locale: "es",
        dictionary,
        demo: false,
        workspace,
        capabilities: writable,
      }),
    );
    expect(html).toContain("Cerrar preparación del equipo");
    expect(html).toContain("Registrar revisión sin requisitos de formación");
    expect(html).toContain("Registrar revisión sin recomendaciones de acceso");
    expect(html).toContain('/api/ui/team-workspace/readiness');
    expect(html).toContain('name="section" value="training_requirements"');
    expect(html).toContain('name="section" value="access_recommendations"');
    expect(html).toContain("no asignan personas ni conceden permisos");
  });

  it("renders no mutation surface in read-only review mode", () => {
    const html = renderToStaticMarkup(
      createElement(TeamReadinessCompletion, {
        locale: "es",
        dictionary,
        demo: true,
        workspace,
        capabilities: writable,
      }),
    );
    expect(html).toBe("");
    expect(html.toLowerCase()).not.toContain("demo");
  });

  it("requires exact update authority before rendering forms", () => {
    const html = renderToStaticMarkup(
      createElement(TeamReadinessCompletion, {
        locale: "es",
        dictionary,
        demo: false,
        workspace,
        capabilities: { ...writable, canUpdate: false },
      }),
    );
    expect(html).toBe("");
  });
});
