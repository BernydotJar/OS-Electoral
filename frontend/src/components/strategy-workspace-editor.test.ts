import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { StrategyWorkspaceEditor } from "@/components/strategy-workspace-editor";
import type { StrategyWorkspaceProjection, TeamRoleCard } from "@/lib/contracts";
import { dictionaryFor } from "@/lib/i18n";

const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";
const WORKSPACE = "33333333-3333-4333-8333-333333333333";
const ROLE = "44444444-4444-4444-8444-444444444444";
const EVIDENCE = "55555555-5555-4555-8555-555555555555";
const HYPOTHESIS_A = "66666666-6666-4666-8666-666666666661";
const HYPOTHESIS_B = "66666666-6666-4666-8666-666666666662";
const OPTION_A = "77777777-7777-4777-8777-777777777771";
const OPTION_B = "77777777-7777-4777-8777-777777777772";

const role: TeamRoleCard = {
  id: ROLE,
  title: "Dirección de campaña",
  area: "Dirección",
  purpose: "Coordinar",
  responsibilities: ["Coordinar"],
  decision_scope: ["Decidir internamente"],
  deliverables: ["Agenda"],
  collaboration_points: ["Equipo"],
  success_signals: ["Cadencia"],
  status: "FILLED",
  principal_id: "88888888-8888-4888-8888-888888888888",
  availability_status: "AVAILABLE",
  weekly_capacity_hours: 40,
  onboarding_status: "COMPLETE",
  vacancy_plan: null,
};

function workspace(overrides: Partial<StrategyWorkspaceProjection> = {}): StrategyWorkspaceProjection {
  return {
    id: WORKSPACE,
    tenant_id: TENANT,
    campaign_id: CAMPAIGN,
    campaign_version: 4,
    campaign_status: "ACTIVE",
    campaign_name: "Campaign",
    candidate_workspace_version: 9,
    team_workspace_version: 8,
    title: "Sala interna",
    evidence: [{
      id: EVIDENCE,
      classification: "VERIFIED",
      statement: "Verified internal operating capacity.",
      source_reference: "https://example.test/source",
      authority: "Official source",
      jurisdiction: "Guatemala",
      status: "ACCEPTED",
      collected_at: "2026-08-13T12:00:00Z",
    }],
    assumptions: [],
    hypotheses: [
      { id: HYPOTHESIS_A, title: "Hypothesis A", statement: "A", evidence_refs: [EVIDENCE], assumption_refs: [], invalidation_signals: ["Signal A"], status: "IN_REVIEW" },
      { id: HYPOTHESIS_B, title: "Hypothesis B", statement: "B", evidence_refs: [EVIDENCE], assumption_refs: [], invalidation_signals: ["Signal B"], status: "IN_REVIEW" },
    ],
    options: [
      { id: OPTION_A, title: "Option A", summary: "A", hypothesis_refs: [HYPOTHESIS_A], evidence_refs: [EVIDENCE], benefits: ["Benefit"], risks: ["Risk"], tradeoffs: ["Tradeoff"] },
      { id: OPTION_B, title: "Option B", summary: "B", hypothesis_refs: [HYPOTHESIS_B], evidence_refs: [EVIDENCE], benefits: ["Benefit"], risks: ["Risk"], tradeoffs: ["Tradeoff"] },
    ],
    objectives: [{ id: "99999999-9999-4999-8999-999999999999", outcome: "Review", metric: "Records", baseline: "1", target: "5", deadline: "2026-09-01", owner_role_id: ROLE, evidence_refs: [EVIDENCE] }],
    contradictions: [],
    red_team_findings: [],
    decision: null,
    status: "READY_FOR_HUMAN_DECISION",
    verified_evidence_count: 1,
    inferred_evidence_count: 0,
    unknown_evidence_count: 0,
    open_contradiction_count: 0,
    open_high_risk_count: 0,
    complete_option_count: 2,
    measurable_objective_count: 1,
    next_action: "MAKE_HUMAN_DECISION",
    human_decision_required: true,
    authority_effect: "NONE",
    external_effects: "NONE",
    limitation_codes: ["NOT_PUBLIC_POSITIONING", "NOT_A_HUMAN_APPROVAL", "NO_VOTER_PROFILING_OR_INDIVIDUAL_TARGETING", "NO_CITIZEN_CONTACT_OR_EXTERNAL_EFFECTS"],
    version: 7,
    created_at: "2026-08-13T12:00:00Z",
    updated_at: "2026-08-13T13:00:00Z",
    ...overrides,
  };
}

const fullCaps = { canStart: true, canRead: true, canUpdate: true, canApprove: true };

describe("StrategyWorkspaceEditor", () => {
  it("shows the start control only when prerequisites and exact capabilities allow it", () => {
    const html = renderToStaticMarkup(createElement(StrategyWorkspaceEditor, { locale: "es", dictionary: dictionaryFor("es"), demo: false, availability: "NOT_STARTED", workspace: null, capabilities: fullCaps, prerequisiteReady: true, teamRoles: [role] }));
    expect(html).toContain('action="/api/ui/strategy-workspace/start"');

    const locked = renderToStaticMarkup(createElement(StrategyWorkspaceEditor, { locale: "es", dictionary: dictionaryFor("es"), demo: false, availability: "NOT_STARTED", workspace: null, capabilities: fullCaps, prerequisiteReady: false, teamRoles: [role] }));
    expect(locked).not.toContain("<form");
  });

  it("exposes authoring with bounded references and no free-form UUID fields", () => {
    const html = renderToStaticMarkup(createElement(StrategyWorkspaceEditor, { locale: "es", dictionary: dictionaryFor("es"), demo: false, availability: "AVAILABLE", workspace: workspace(), capabilities: fullCaps, prerequisiteReady: true, teamRoles: [role] }));
    expect(html).toContain('id="strategy-authoring"');
    expect(html).toContain('name="evidence_refs"');
    expect(html).toContain('type="checkbox"');
    expect(html).toContain('<select name="owner_role_id"');
    expect(html).not.toContain('<input name="owner_role_id"');
    expect(html).not.toContain('<input name="selected_option_id"');
    expect(html).toContain('<option value="" disabled="" selected="">Selecciona una opción</option>');
    expect(html).toContain('<option value="" disabled="" selected="">Selecciona una función</option>');
  });

  it("shows the human decision form only for backend-derived readiness and exact approval authority", () => {
    const ready = renderToStaticMarkup(createElement(StrategyWorkspaceEditor, { locale: "es", dictionary: dictionaryFor("es"), demo: false, availability: "AVAILABLE", workspace: workspace(), capabilities: fullCaps, prerequisiteReady: true, teamRoles: [role] }));
    expect(ready).toContain('action="/api/ui/strategy-workspace/decision"');

    const incomplete = renderToStaticMarkup(createElement(StrategyWorkspaceEditor, { locale: "es", dictionary: dictionaryFor("es"), demo: false, availability: "AVAILABLE", workspace: workspace({ status: "OPTIONS_INCOMPLETE", next_action: "COMPLETE_COMPARABLE_OPTIONS", human_decision_required: false }), capabilities: fullCaps, prerequisiteReady: true, teamRoles: [role] }));
    expect(incomplete).not.toContain('action="/api/ui/strategy-workspace/decision"');

    const noApproval = renderToStaticMarkup(createElement(StrategyWorkspaceEditor, { locale: "es", dictionary: dictionaryFor("es"), demo: false, availability: "AVAILABLE", workspace: workspace(), capabilities: { ...fullCaps, canApprove: false }, prerequisiteReady: true, teamRoles: [role] }));
    expect(noApproval).not.toContain('action="/api/ui/strategy-workspace/decision"');
  });

  it("renders no mutation controls in read-only review mode", () => {
    const html = renderToStaticMarkup(createElement(StrategyWorkspaceEditor, { locale: "es", dictionary: dictionaryFor("es"), demo: true, availability: "AVAILABLE", workspace: workspace(), capabilities: fullCaps, prerequisiteReady: true, teamRoles: [role] }));
    expect(html).toBe("");
  });
});
