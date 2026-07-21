import { describe, expect, it } from "vitest";

import type { StrategyWorkspaceReadEvidence } from "@/lib/contracts";
import {
  StrategyContractValidationError,
  parseStrategyWorkspaceReadEvidence,
} from "@/lib/strategy-contract-parser";

const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";
const WORKSPACE = "33333333-3333-4333-8333-333333333333";
const ROLE = "44444444-4444-4444-8444-444444444444";
const EVIDENCE = "55555555-5555-4555-8555-555555555555";
const ASSUMPTION = "66666666-6666-4666-8666-666666666666";
const HYPOTHESIS_A = "77777777-7777-4777-8777-777777777771";
const HYPOTHESIS_B = "77777777-7777-4777-8777-777777777772";
const OPTION_A = "88888888-8888-4888-8888-888888888881";
const OPTION_B = "88888888-8888-4888-8888-888888888882";
const OBJECTIVE = "99999999-9999-4999-8999-999999999999";

type DeepMutable<T> = {
  -readonly [Key in keyof T]: T[Key] extends readonly (infer Item)[]
    ? DeepMutable<Item>[]
    : T[Key] extends object
      ? DeepMutable<T[Key]>
      : T[Key];
};

function evidence() {
  return {
    audit_event_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    workspace: {
      id: WORKSPACE,
      tenant_id: TENANT,
      campaign_id: CAMPAIGN,
      campaign_version: 5,
      campaign_status: "ACTIVE",
      campaign_name: "Synthetic campaign",
      candidate_workspace_version: 2,
      team_workspace_version: 3,
      title: "Campaign Strategy and Decision Room",
      evidence: [
        {
          id: EVIDENCE,
          classification: "VERIFIED",
          statement: "Public record confirms campaign context.",
          source_reference: "https://example.test/public-record",
          authority: "Public authority",
          jurisdiction: "Guatemala",
          status: "ACCEPTED",
          collected_at: "2026-07-21T12:00:00Z",
        },
      ],
      assumptions: [
        {
          id: ASSUMPTION,
          statement: "The team can maintain the operating cadence.",
          evidence_refs: [EVIDENCE],
          invalidation_signals: ["Capacity falls below threshold"],
          status: "ACTIVE",
        },
      ],
      hypotheses: [
        {
          id: HYPOTHESIS_A,
          title: "Evidence consolidation",
          statement: "Evidence consolidation improves internal decisions.",
          evidence_refs: [EVIDENCE],
          assumption_refs: [ASSUMPTION],
          invalidation_signals: ["Decision quality does not improve"],
          status: "IN_REVIEW",
        },
        {
          id: HYPOTHESIS_B,
          title: "Capacity sequencing",
          statement: "Capacity sequencing reduces blockers.",
          evidence_refs: [EVIDENCE],
          assumption_refs: [ASSUMPTION],
          invalidation_signals: ["Blockers increase"],
          status: "IN_REVIEW",
        },
      ],
      options: [
        {
          id: OPTION_A,
          title: "Option A",
          summary: "Consolidate evidence first.",
          hypothesis_refs: [HYPOTHESIS_A],
          evidence_refs: [EVIDENCE],
          benefits: ["Preserves provenance"],
          risks: ["Requires review time"],
          tradeoffs: ["Delays downstream planning"],
        },
        {
          id: OPTION_B,
          title: "Option B",
          summary: "Sequence internal work by capacity.",
          hypothesis_refs: [HYPOTHESIS_B],
          evidence_refs: [EVIDENCE],
          benefits: ["Surfaces constraints"],
          risks: ["May defer evidence"],
          tradeoffs: ["Prioritizes capacity"],
        },
      ],
      objectives: [
        {
          id: OBJECTIVE,
          outcome: "Complete evidence review.",
          metric: "Accepted evidence records",
          baseline: "1",
          target: "10",
          deadline: "2026-08-15",
          owner_role_id: ROLE,
          evidence_refs: [EVIDENCE],
        },
      ],
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
      limitation_codes: [
        "NOT_PUBLIC_POSITIONING",
        "NOT_A_HUMAN_APPROVAL",
        "NO_VOTER_PROFILING_OR_INDIVIDUAL_TARGETING",
        "NO_CITIZEN_CONTACT_OR_EXTERNAL_EFFECTS",
      ],
      version: 2,
      created_at: "2026-07-21T12:00:00Z",
      updated_at: "2026-07-21T12:10:00Z",
    },
  };
}

describe("strategy contract parser", () => {
  it("accepts an exact evidence-first workspace ready for human decision", () => {
    const parsed = parseStrategyWorkspaceReadEvidence(evidence());
    expect(parsed.workspace.status).toBe("READY_FOR_HUMAN_DECISION");
    expect(parsed.workspace.complete_option_count).toBe(2);
    expect(parsed.workspace.authority_effect).toBe("NONE");
  });

  it("rejects false provenance and summary count drift", () => {
    const falseProvenance = structuredClone(evidence());
    falseProvenance.workspace.evidence[0]!.classification = "UNKNOWN";
    expect(() => parseStrategyWorkspaceReadEvidence(falseProvenance)).toThrow(
      StrategyContractValidationError,
    );

    const countDrift = structuredClone(evidence());
    countDrift.workspace.verified_evidence_count = 2;
    expect(() => parseStrategyWorkspaceReadEvidence(countDrift)).toThrow(
      "counts are inconsistent",
    );
  });

  it("rejects unknown option references and status drift", () => {
    const unknownReference = structuredClone(evidence());
    unknownReference.workspace.options[0]!.hypothesis_refs = [
      "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
    ];
    expect(() => parseStrategyWorkspaceReadEvidence(unknownReference)).toThrow(
      "unknown hypothesis reference",
    );

    const statusDrift = structuredClone(evidence());
    statusDrift.workspace.status = "DECIDED_INTERNAL";
    statusDrift.workspace.human_decision_required = false;
    expect(() => parseStrategyWorkspaceReadEvidence(statusDrift)).toThrow(
      "status is inconsistent",
    );
  });

  it("rejects a stale or unknown human decision", () => {
    const stale = structuredClone(
      evidence(),
    ) as DeepMutable<StrategyWorkspaceReadEvidence>;
    stale.workspace.decision = {
      id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
      workspace_version: 1,
      selected_option_id: OPTION_A,
      reason: "Human decision.",
      human_role_id: ROLE,
      approval_receipt_id: "approval-strategy-v1",
      decided_at: "2026-07-21T12:15:00Z",
    };
    stale.workspace.status = "DECIDED_INTERNAL";
    stale.workspace.next_action = "REVALIDATE_DECISION";
    stale.workspace.human_decision_required = false;
    expect(() => parseStrategyWorkspaceReadEvidence(stale)).toThrow(
      "current workspace version",
    );
  });

  it("rejects prohibited profiling fields even when hidden beside valid data", () => {
    const corrupted = structuredClone(evidence()) as Record<string, unknown>;
    const workspace = corrupted.workspace as Record<string, unknown>;
    workspace.voter_persuadability_score = 91;
    expect(() => parseStrategyWorkspaceReadEvidence(corrupted)).toThrow(
      "unexpected fields",
    );
  });
});
