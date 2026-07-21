import { describe, expect, it } from "vitest";

import { parseCandidateWorkspaceReadEvidence } from "@/lib/contract-parsers";

const TENANT_ID = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN_ID = "22222222-2222-4222-8222-222222222222";
const WORKSPACE_ID = "33333333-3333-4333-8333-333333333333";
const CANDIDATE_ID = "44444444-4444-4444-8444-444444444444";

function candidateEvidence() {
  const evidenceIds = [
    "50000000-0000-4000-8000-000000000001",
    "50000000-0000-4000-8000-000000000002",
    "50000000-0000-4000-8000-000000000003",
    "50000000-0000-4000-8000-000000000004",
    "50000000-0000-4000-8000-000000000005",
    "50000000-0000-4000-8000-000000000006",
  ];
  const sections = [
    "identity",
    "biography",
    "purpose",
    "values",
    "attributes",
    "contradictions",
    "development_goals",
    "reputation",
  ];
  const evidence = evidenceIds.map((id, index) => ({
    id,
    classification: "CAMPAIGN_RESEARCH",
    status: "ACCEPTED",
    title: `Synthetic evidence ${index + 1}`,
    source_reference: `synthetic://candidate/${id}`,
    source_authority: "Synthetic campaign research fixture",
    jurisdiction: "Antigua Guatemala",
    excerpt: "Synthetic evidence for deterministic frontend verification.",
    observed_at: "2026-07-21T22:00:00Z",
  }));
  const claim = (id: string, label: string, evidenceId: string) => ({
    id,
    label,
    claim: `Verified synthetic ${label.toLowerCase()} claim.`,
    status: "VERIFIED",
    classification: "CAMPAIGN_RESEARCH",
    evidence_refs: [evidenceId],
  });
  return {
    audit_event_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    workspace: {
      id: WORKSPACE_ID,
      tenant_id: TENANT_ID,
      campaign_id: CAMPAIGN_ID,
      campaign_version: 3,
      campaign_status: "ACTIVE",
      campaign_name: "Campaña sintética Antigua",
      jurisdiction: "Antigua Guatemala",
      candidate_id: CANDIDATE_ID,
      display_name: "Candidatura sintética",
      status: "INTERNALLY_APPROVED",
      public_use_status: "BLOCKED",
      external_effects: "NONE",
      evidence,
      identity: claim(
        "60000000-0000-4000-8000-000000000001",
        "Identity",
        evidenceIds[0]!,
      ) as ReturnType<typeof claim> | null,
      biography: claim(
        "60000000-0000-4000-8000-000000000002",
        "Biography",
        evidenceIds[1]!,
      ),
      purpose: claim(
        "60000000-0000-4000-8000-000000000003",
        "Purpose",
        evidenceIds[2]!,
      ),
      values: [
        claim(
          "60000000-0000-4000-8000-000000000004",
          "Public service",
          evidenceIds[3]!,
        ),
      ],
      attributes: [
        {
          id: "70000000-0000-4000-8000-000000000001",
          name: "Capacity to form teams",
          claim: "The candidate has demonstrated team-building capacity.",
          status: "VERIFIED",
          candidate_self_assessment: "YES",
          team_assessment: "PARTIAL",
          citizen_evidence: "UNRESOLVED",
          evidence_refs: [evidenceIds[4]],
          perception_refs: [] as string[],
          contradiction_refs: [] as string[],
          risk: "Evidence is sufficient only for internal assessment.",
        },
      ],
      contradictions: [] as Array<{
        id: string;
        subject_ref: string;
        description: string;
        status: string;
        evidence_refs: string[];
      }>,
      development_goals: [
        {
          id: "80000000-0000-4000-8000-000000000001",
          area: "Evidence discipline",
          objective: "Document every material claim before human review.",
          status: "OPEN",
          evidence_refs: [evidenceIds[5]],
        },
      ],
      reputation_risks: [],
      checks: [
        { key: "identity", complete: true, reason_code: "IDENTITY_VERIFIED" },
        { key: "biography", complete: true, reason_code: "BIOGRAPHY_VERIFIED" },
        { key: "purpose", complete: true, reason_code: "PURPOSE_VERIFIED" },
        { key: "values", complete: true, reason_code: "VALUES_VERIFIED" },
        {
          key: "attributes",
          complete: true,
          reason_code: "ATTRIBUTES_VERIFIED",
        },
        {
          key: "contradictions",
          complete: true,
          reason_code: "CONTRADICTIONS_REVIEWED",
        },
        {
          key: "development_goals",
          complete: true,
          reason_code: "DEVELOPMENT_GOALS_DEFINED",
        },
        {
          key: "reputation",
          complete: true,
          reason_code: "REPUTATION_RISKS_REVIEWED",
        },
        {
          key: "approvals",
          complete: true,
          reason_code: "CURRENT_SECTION_APPROVALS_COMPLETE",
        },
      ],
      completed_checks: 9,
      total_checks: 9,
      approvable_sections: [...sections],
      current_approved_sections: [...sections],
      approvals_required: [],
      open_critical_high_risks: 0,
      next_action: "CONTINUE_HUMAN_GOVERNANCE",
      limitation_codes: [
        "NOT_PUBLIC_POSITIONING_APPROVAL",
        "NOT_A_STRATEGY",
        "NO_VOTER_PROFILING",
        "NO_EXTERNAL_EFFECTS",
        "HUMAN_REVIEW_REQUIRED",
      ],
      version: 2,
      created_at: "2026-07-21T21:00:00Z",
      updated_at: "2026-07-21T22:00:00Z",
    },
  };
}

describe("candidate workspace parser", () => {
  it("accepts canonical internal evidence while public use remains blocked", () => {
    const parsed = parseCandidateWorkspaceReadEvidence(candidateEvidence());
    expect(parsed.workspace.status).toBe("INTERNALLY_APPROVED");
    expect(parsed.workspace.current_approved_sections).toHaveLength(8);
    expect(parsed.workspace.public_use_status).toBe("BLOCKED");
    expect(parsed.workspace.external_effects).toBe("NONE");
  });

  it("rejects unknown evidence and self-assessment-only verification", () => {
    const unknown = structuredClone(candidateEvidence());
    unknown.workspace.identity!.evidence_refs = [
      "99999999-9999-4999-8999-999999999999",
    ];
    expect(() => parseCandidateWorkspaceReadEvidence(unknown)).toThrow(
      "unknown evidence reference",
    );

    const selfOnly = structuredClone(candidateEvidence());
    selfOnly.workspace.attributes[0]!.evidence_refs = [];
    expect(() => parseCandidateWorkspaceReadEvidence(selfOnly)).toThrow(
      "self-assessment alone",
    );
  });

  it("types perception and contradiction references semantically", () => {
    const wrongPerception = structuredClone(candidateEvidence());
    wrongPerception.workspace.attributes[0]!.perception_refs = [
      wrongPerception.workspace.evidence[0]!.id,
    ];
    expect(() => parseCandidateWorkspaceReadEvidence(wrongPerception)).toThrow(
      "perception records",
    );

    const unknownContradiction = structuredClone(candidateEvidence());
    unknownContradiction.workspace.attributes[0]!.contradiction_refs = [
      "99999999-9999-4999-8999-999999999999",
    ];
    expect(() =>
      parseCandidateWorkspaceReadEvidence(unknownContradiction),
    ).toThrow("unknown contradiction reference");

    const wrongSubject = structuredClone(candidateEvidence());
    const contradictionId = "90000000-0000-4000-8000-000000000001";
    wrongSubject.workspace.contradictions = [
      {
        id: contradictionId,
        subject_ref: wrongSubject.workspace.identity!.id,
        description: "Synthetic contradiction about another subject.",
        status: "RESOLVED",
        evidence_refs: [wrongSubject.workspace.evidence[0]!.id],
      },
    ];
    wrongSubject.workspace.attributes[0]!.contradiction_refs = [
      contradictionId,
    ];
    expect(() => parseCandidateWorkspaceReadEvidence(wrongSubject)).toThrow(
      "targets another subject",
    );
  });

  it("rejects approval, status, and next-action summaries that contradict sections", () => {
    const missingApproval = structuredClone(candidateEvidence());
    missingApproval.workspace.current_approved_sections.pop();
    expect(() => parseCandidateWorkspaceReadEvidence(missingApproval)).toThrow(
      "approval summary is inconsistent",
    );

    const wrongStatus = structuredClone(candidateEvidence());
    wrongStatus.workspace.status = "AWAITING_APPROVAL";
    expect(() => parseCandidateWorkspaceReadEvidence(wrongStatus)).toThrow(
      "status is inconsistent",
    );

    const wrongAction = structuredClone(candidateEvidence());
    wrongAction.workspace.next_action = "VERIFY_ATTRIBUTES";
    expect(() => parseCandidateWorkspaceReadEvidence(wrongAction)).toThrow(
      "next action is inconsistent",
    );
  });

  it("rejects check, risk, and mandatory-boundary contradictions", () => {
    const missingIdentity = structuredClone(candidateEvidence());
    missingIdentity.workspace.identity = null;
    missingIdentity.workspace.approvable_sections.shift();
    missingIdentity.workspace.current_approved_sections.shift();
    missingIdentity.workspace.status = "SETUP_REQUIRED";
    missingIdentity.workspace.next_action = "DEFINE_IDENTITY";
    missingIdentity.workspace.checks[8]!.complete = false;
    missingIdentity.workspace.checks[8]!.reason_code =
      "CURRENT_SECTION_APPROVALS_REQUIRED";
    missingIdentity.workspace.completed_checks = 7;
    expect(() => parseCandidateWorkspaceReadEvidence(missingIdentity)).toThrow(
      "checks contradict source fields",
    );

    const wrongRiskCount = structuredClone(candidateEvidence());
    wrongRiskCount.workspace.open_critical_high_risks = 1;
    expect(() => parseCandidateWorkspaceReadEvidence(wrongRiskCount)).toThrow(
      "risk summary is inconsistent",
    );

    const publicDrift = structuredClone(candidateEvidence());
    publicDrift.workspace.public_use_status = "APPROVED";
    expect(() => parseCandidateWorkspaceReadEvidence(publicDrift)).toThrow();

    const missingLimit = structuredClone(candidateEvidence());
    missingLimit.workspace.limitation_codes.pop();
    expect(() => parseCandidateWorkspaceReadEvidence(missingLimit)).toThrow(
      "mandatory limitations are missing",
    );
  });
});
