import { describe, expect, it } from "vitest";

import type { CandidateWorkspaceProjection } from "@/lib/contracts";
import { deriveCandidateActionInsights } from "@/lib/candidate-action-insights";

const base: CandidateWorkspaceProjection = {
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
  approvals_required: ["identity", "biography"],
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

describe("deriveCandidateActionInsights", () => {
  it("turns evidence gaps and pending approvals into bounded actions", () => {
    const insights = deriveCandidateActionInsights(base);

    expect(insights.map((item) => item.code)).toEqual([
      "NEXT_ACTION",
      "EVIDENCE_GAP",
      "APPROVALS_PENDING",
    ]);
    expect(insights.every((item) => item.externalEffects === "NONE")).toBe(true);
  });

  it("surfaces open contradictions, development work, and critical risk decisions", () => {
    const insights = deriveCandidateActionInsights({
      ...base,
      evidence: [
        {
          id: "55555555-5555-4555-8555-555555555555",
          classification: "OFFICIAL_SOURCE",
          status: "VERIFIED",
          title: "Registro oficial",
          source_reference: "https://example.test/source",
          source_authority: "Autoridad",
          jurisdiction: "Municipio",
          excerpt: "Referencia verificable",
          observed_at: "2026-07-28T00:00:00Z",
        },
      ],
      contradictions: [
        {
          id: "66666666-6666-4666-8666-666666666666",
          subject_ref: "77777777-7777-4777-8777-777777777777",
          description: "Declaraciones incompatibles",
          status: "OPEN",
          evidence_refs: [],
        },
      ],
      development_goals: [
        {
          id: "88888888-8888-4888-8888-888888888888",
          area: "Preparación",
          objective: "Completar entrenamiento",
          status: "IN_PROGRESS",
          evidence_refs: [],
        },
      ],
      reputation_risks: [
        {
          id: "99999999-9999-4999-8999-999999999999",
          title: "Riesgo abierto",
          description: "Requiere decisión humana",
          severity: "HIGH",
          status: "OPEN",
          decision_required: true,
          evidence_refs: [],
        },
      ],
      open_critical_high_risks: 1,
      approvals_required: [],
    });

    expect(insights.map((item) => item.code)).toEqual([
      "NEXT_ACTION",
      "CONTRADICTIONS_OPEN",
      "RISK_DECISION_REQUIRED",
      "DEVELOPMENT_ACTIVE",
    ]);
  });
});
