import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { CandidateWorkspaceCompletion } from "@/components/candidate-workspace-completion";
import type { CandidateWorkspaceProjection } from "@/lib/contracts";
import { dictionaryFor } from "@/lib/i18n";

const dictionary = dictionaryFor("es");
const workspace: CandidateWorkspaceProjection = {
  id: "11111111-1111-4111-8111-111111111111",
  tenant_id: "22222222-2222-4222-8222-222222222222",
  campaign_id: "33333333-3333-4333-8333-333333333333",
  campaign_version: 1,
  campaign_status: "ACTIVE",
  campaign_name: "Campaña local",
  jurisdiction: "Municipio",
  candidate_id: "44444444-4444-4444-8444-444444444444",
  display_name: "Candidatura",
  status: "SETUP_REQUIRED",
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
  checks: [
    { key: "identity", complete: false, reason_code: "IDENTITY_NOT_VERIFIED" },
    { key: "biography", complete: false, reason_code: "BIOGRAPHY_NOT_VERIFIED" },
    { key: "purpose", complete: false, reason_code: "PURPOSE_NOT_VERIFIED" },
    { key: "values", complete: false, reason_code: "VALUES_NOT_VERIFIED" },
    { key: "attributes", complete: false, reason_code: "ATTRIBUTES_NOT_VERIFIED" },
    { key: "contradictions", complete: false, reason_code: "CONTRADICTIONS_UNRESOLVED" },
    { key: "development_goals", complete: false, reason_code: "DEVELOPMENT_GOALS_MISSING" },
    { key: "reputation", complete: false, reason_code: "REPUTATION_RISKS_UNRESOLVED" },
    { key: "approvals", complete: false, reason_code: "CURRENT_SECTION_APPROVALS_REQUIRED" },
  ],
  completed_checks: 0,
  total_checks: 9,
  approvable_sections: ["identity"],
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
  version: 3,
  created_at: "2026-08-12T00:00:00Z",
  updated_at: "2026-08-12T00:00:00Z",
};

const capabilities = {
  canStart: true,
  canRead: true,
  canUpdate: true,
  canApprove: true,
} as const;

describe("CandidateWorkspaceCompletion", () => {
  it("provides an actionable editor for every candidate gate", () => {
    const html = renderToStaticMarkup(
      createElement(CandidateWorkspaceCompletion, {
        locale: "es",
        dictionary,
        demo: false,
        workspace,
        capabilities,
      }),
    );
    for (const id of [
      "identity",
      "biography",
      "purpose",
      "values",
      "attributes",
      "contradictions",
      "development_goals",
      "reputation",
    ]) {
      expect(html).toContain(`id="candidate-edit-${id}"`);
    }
    expect(html).toContain('id="candidate-approvals"');
    expect(html).toContain('action="/api/ui/candidate-workspace/section"');
    expect(html).toContain('action="/api/ui/candidate-workspace/approval"');
    expect(html).toContain("Las aprobaciones de la versión anterior");
  });

  it("renders no mutation forms in read-only review", () => {
    const html = renderToStaticMarkup(
      createElement(CandidateWorkspaceCompletion, {
        locale: "es",
        dictionary,
        demo: true,
        workspace,
        capabilities,
      }),
    );
    expect(html).not.toContain('/api/ui/candidate-workspace/section');
    expect(html).not.toContain('/api/ui/candidate-workspace/approval');
    expect(html.toLocaleLowerCase()).not.toContain("demo");
    expect(html).toContain("no tiene autoridad de edición");
  });

  it("withholds approval forms without the exact approval grant", () => {
    const html = renderToStaticMarkup(
      createElement(CandidateWorkspaceCompletion, {
        locale: "es",
        dictionary,
        demo: false,
        workspace,
        capabilities: { ...capabilities, canApprove: false },
      }),
    );
    expect(html).toContain('/api/ui/candidate-workspace/section');
    expect(html).not.toContain('/api/ui/candidate-workspace/approval');
    expect(html).toContain("permiso exacto");
  });
});
