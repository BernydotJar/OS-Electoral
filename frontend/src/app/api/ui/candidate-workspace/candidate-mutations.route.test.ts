import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
vi.mock("@/lib/server-context", () => {
  class UiContextError extends Error {
    constructor(readonly notice: string) {
      super(notice);
    }
  }
  return {
    UiContextError,
    requireSameOrigin: vi.fn(),
    loadLiveCampaignContext: vi.fn(),
    noticeForError: vi.fn((error: unknown) =>
      error instanceof UiContextError ? error.notice : "request_failed",
    ),
  };
});

import { POST as approve } from "@/app/api/ui/candidate-workspace/approval/route";
import { POST as updateSection } from "@/app/api/ui/candidate-workspace/section/route";
import type { CandidateWorkspaceProjection } from "@/lib/contracts";
import { loadLiveCampaignContext } from "@/lib/server-context";

const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";
const EVIDENCE = "33333333-3333-4333-8333-333333333333";

const workspace: CandidateWorkspaceProjection = {
  id: "44444444-4444-4444-8444-444444444444",
  tenant_id: TENANT,
  campaign_id: CAMPAIGN,
  campaign_version: 1,
  campaign_status: "ACTIVE",
  campaign_name: "Campaña local",
  jurisdiction: "Municipio",
  candidate_id: "55555555-5555-4555-8555-555555555555",
  display_name: "Candidatura",
  status: "UNDER_REVIEW",
  public_use_status: "BLOCKED",
  external_effects: "NONE",
  evidence: [
    {
      id: EVIDENCE,
      classification: "OFFICIAL_SOURCE",
      status: "ACCEPTED",
      title: "Documento oficial",
      source_reference: "https://example.test/source",
      source_authority: "Autoridad",
      jurisdiction: "Municipio",
      excerpt: "Confirma identidad",
      observed_at: "2026-08-12T00:00:00Z",
    },
  ],
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

function grant(action: string, purpose: string) {
  return {
    grant_id: crypto.randomUUID(),
    campaign_id: CAMPAIGN,
    workspace_id: null,
    action,
    resource_type: "candidate_workspace",
    resource_id: CAMPAIGN,
    purpose,
    approval_receipt_id: "approval",
  };
}

function context(
  api: Record<string, unknown>,
  grants = [
    grant("read", "Review candidate evidence workspace"),
    grant("update", "Maintain candidate evidence workspace"),
    grant("approve", "Approve candidate evidence section"),
  ],
) {
  return {
    tenantId: TENANT,
    campaign: {
      id: CAMPAIGN,
      tenant_id: TENANT,
      slug: "local",
      name: "Campaña local",
      jurisdiction: "Municipio",
      stage: "PRECAMPAIGN",
      status: "ACTIVE",
      version: 1,
    },
    campaigns: [],
    api,
    identity: {
      application_memberships: [
        {
          membership_id: "66666666-6666-4666-8666-666666666666",
          campaign_id: CAMPAIGN,
          roles: [],
          grants,
        },
      ],
    },
  } as never;
}

function sectionRequest(version = "3"): Request {
  const form = new FormData();
  form.set("locale", "es");
  form.set("version", version);
  form.set("idempotency_key", "candidate-identity:77777777-7777-4777-8777-777777777777");
  form.set("section", "identity");
  form.set("section_action", "save");
  form.set("record_id", "");
  form.set("label", "Identidad");
  form.set("claim", "Identidad confirmada por documento oficial");
  form.set("status", "VERIFIED");
  form.set("classification", "OFFICIAL_SOURCE");
  form.append("evidence_refs", EVIDENCE);
  return new Request("https://campaign.example.test/api/ui/candidate-workspace/section", {
    method: "POST",
    body: form,
  });
}

function approvalRequest(section = "identity"): Request {
  const form = new FormData();
  form.set("locale", "es");
  form.set("version", "3");
  form.set("idempotency_key", "candidate-approval:88888888-8888-4888-8888-888888888888");
  form.set("section", section);
  form.set("reason", "Evidencia revisada por la persona responsable.");
  return new Request("https://campaign.example.test/api/ui/candidate-workspace/approval", {
    method: "POST",
    body: form,
  });
}

describe("candidate workspace mutation routes", () => {
  beforeEach(() => vi.clearAllMocks());

  it("updates one candidate section while leaving unrelated sections out of the patch", async () => {
    const candidateWorkspace = vi.fn(async () => ({ workspace, audit_event_id: crypto.randomUUID() }));
    const updateCandidateWorkspace = vi.fn(async () => ({}));
    vi.mocked(loadLiveCampaignContext).mockResolvedValue(
      context({ candidateWorkspace, updateCandidateWorkspace }),
    );

    const response = await updateSection(sectionRequest());
    const destination = new URL(response.headers.get("location")!);

    expect(response.status).toBe(303);
    expect(destination.pathname).toBe("/es/campaign/evidence");
    expect(destination.hash).toBe("#candidate-edit-identity");
    expect(destination.searchParams.get("notice")).toBe("candidate_section_saved");
    expect(updateCandidateWorkspace).toHaveBeenCalledTimes(1);
    const patch = (updateCandidateWorkspace.mock.calls[0] as unknown[])[4];
    expect(patch).toEqual({
      identity: {
        id: expect.any(String),
        label: "Identidad",
        claim: "Identidad confirmada por documento oficial",
        status: "VERIFIED",
        classification: "OFFICIAL_SOURCE",
        evidence_refs: [EVIDENCE],
      },
    });
  });

  it("fails closed on a stale candidate version", async () => {
    const candidateWorkspace = vi.fn(async () => ({ workspace, audit_event_id: crypto.randomUUID() }));
    const updateCandidateWorkspace = vi.fn();
    vi.mocked(loadLiveCampaignContext).mockResolvedValue(
      context({ candidateWorkspace, updateCandidateWorkspace }),
    );

    const response = await updateSection(sectionRequest("2"));
    const destination = new URL(response.headers.get("location")!);
    expect(destination.searchParams.get("notice")).toBe("conflict");
    expect(updateCandidateWorkspace).not.toHaveBeenCalled();
  });

  it("denies section mutation without the exact update grant", async () => {
    const candidateWorkspace = vi.fn();
    const updateCandidateWorkspace = vi.fn();
    vi.mocked(loadLiveCampaignContext).mockResolvedValue(
      context(
        { candidateWorkspace, updateCandidateWorkspace },
        [grant("read", "Review candidate evidence workspace")],
      ),
    );

    const response = await updateSection(sectionRequest());
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe(
      "authorization_denied",
    );
    expect(candidateWorkspace).not.toHaveBeenCalled();
  });

  it("records only an approval that is required for the current version", async () => {
    const candidateWorkspace = vi.fn(async () => ({ workspace, audit_event_id: crypto.randomUUID() }));
    const approveCandidateWorkspaceSection = vi.fn(async () => ({}));
    vi.mocked(loadLiveCampaignContext).mockResolvedValue(
      context({ candidateWorkspace, approveCandidateWorkspaceSection }),
    );

    const response = await approve(approvalRequest());
    const destination = new URL(response.headers.get("location")!);
    expect(destination.pathname).toBe("/es/campaign/evidence");
    expect(destination.hash).toBe("#candidate-approvals");
    expect(destination.searchParams.get("notice")).toBe("candidate_section_approved");
    expect(approveCandidateWorkspaceSection).toHaveBeenCalledWith(
      TENANT,
      CAMPAIGN,
      3,
      expect.stringMatching(/^candidate-approval:/),
      "identity",
      "Evidencia revisada por la persona responsable.",
    );
  });

  it("denies approval without the exact approval grant", async () => {
    const candidateWorkspace = vi.fn();
    const approveCandidateWorkspaceSection = vi.fn();
    vi.mocked(loadLiveCampaignContext).mockResolvedValue(
      context(
        { candidateWorkspace, approveCandidateWorkspaceSection },
        [grant("read", "Review candidate evidence workspace")],
      ),
    );
    const response = await approve(approvalRequest());
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe(
      "authorization_denied",
    );
    expect(candidateWorkspace).not.toHaveBeenCalled();
  });

  it("rejects an approval for a section that is not currently required", async () => {
    const candidateWorkspace = vi.fn(async () => ({ workspace, audit_event_id: crypto.randomUUID() }));
    const approveCandidateWorkspaceSection = vi.fn();
    vi.mocked(loadLiveCampaignContext).mockResolvedValue(
      context({ candidateWorkspace, approveCandidateWorkspaceSection }),
    );
    const response = await approve(approvalRequest("purpose"));
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe(
      "conflict",
    );
    expect(approveCandidateWorkspaceSection).not.toHaveBeenCalled();
  });
});
