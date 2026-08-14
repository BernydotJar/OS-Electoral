import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
vi.mock("@/lib/server-context", () => {
  class UiContextError extends Error {
    constructor(readonly notice: string) { super(notice); }
  }
  return {
    UiContextError,
    requireSameOrigin: vi.fn(),
    loadLiveCampaignContext: vi.fn(),
    noticeForError: vi.fn((error: unknown) => error instanceof UiContextError ? error.notice : "request_failed"),
  };
});

import { POST } from "@/app/api/ui/strategy-workspace/section/route";
import { loadLiveCampaignContext } from "@/lib/server-context";

const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";
const ROLE = "33333333-3333-4333-8333-333333333333";
const EVIDENCE = "44444444-4444-4444-8444-444444444444";
const HYPOTHESIS = "55555555-5555-4555-8555-555555555555";
const OPTION = "66666666-6666-4666-8666-666666666666";

function memberships(update = true) {
  return [{
    membership_id: "77777777-7777-4777-8777-777777777777",
    campaign_id: CAMPAIGN,
    roles: ["strategy_label_only"],
    grants: [
      {
        grant_id: "88888888-8888-4888-8888-888888888881",
        campaign_id: CAMPAIGN,
        workspace_id: null,
        action: "read",
        resource_type: "strategy_workspace",
        resource_id: CAMPAIGN,
        purpose: "Review campaign strategy workspace",
        approval_receipt_id: "approval-read",
      },
      ...(update ? [{
        grant_id: "88888888-8888-4888-8888-888888888882",
        campaign_id: CAMPAIGN,
        workspace_id: null,
        action: "update",
        resource_type: "strategy_workspace",
        resource_id: CAMPAIGN,
        purpose: "Maintain campaign strategy workspace",
        approval_receipt_id: "approval-update",
      }] : []),
    ],
  }];
}

function workspace(overrides: Record<string, unknown> = {}) {
  return {
    id: "99999999-9999-4999-8999-999999999999",
    tenant_id: TENANT,
    campaign_id: CAMPAIGN,
    version: 3,
    evidence: [{
      id: EVIDENCE,
      classification: "VERIFIED",
      statement: "Verified internal operating evidence.",
      source_reference: "https://example.test/source",
      authority: "Official source",
      jurisdiction: "Guatemala",
      status: "ACCEPTED",
      collected_at: "2026-08-12T12:00:00.000Z",
    }],
    assumptions: [],
    hypotheses: [{
      id: HYPOTHESIS,
      title: "Operating hypothesis",
      statement: "Evidence can support the internal operating decision.",
      evidence_refs: [EVIDENCE],
      assumption_refs: [],
      invalidation_signals: ["Observed capacity fails"],
      status: "IN_REVIEW",
    }],
    options: [{
      id: OPTION,
      title: "Option A",
      summary: "Sequence verified internal work.",
      hypothesis_refs: [HYPOTHESIS],
      evidence_refs: [EVIDENCE],
      benefits: ["Traceable"],
      risks: ["Review time"],
      tradeoffs: ["Slower sequencing"],
    }],
    objectives: [],
    contradictions: null,
    red_team_findings: null,
    ...overrides,
  };
}

function team() {
  return {
    id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    tenant_id: TENANT,
    campaign_id: CAMPAIGN,
    status: "READY_FOR_HUMAN_REVIEW",
    roles: [{ id: ROLE, title: "Dirección", area: "Dirección" }],
  };
}

function base(section: string, action = "save") {
  const form = new FormData();
  form.set("locale", "es");
  form.set("version", "3");
  form.set("idempotency_key", "strategy-section:12345678-1234-4234-8234-123456789abc");
  form.set("section", section);
  form.set("strategy_action", action);
  form.set("record_id", "");
  return form;
}

function request(form: FormData) {
  return new Request("https://campaign.example.test/api/ui/strategy-workspace/section", {
    method: "POST",
    headers: { origin: "https://campaign.example.test", host: "campaign.example.test" },
    body: form,
  });
}

function context(current = workspace(), allowUpdate = true) {
  const update = vi.fn(async () => ({}));
  vi.mocked(loadLiveCampaignContext).mockResolvedValue({
    tenantId: TENANT,
    campaign: { id: CAMPAIGN },
    identity: { application_memberships: memberships(allowUpdate) },
    api: {
      strategyWorkspace: vi.fn(async () => ({ workspace: current })),
      teamWorkspace: vi.fn(async () => ({ workspace: team() })),
      updateStrategyWorkspace: update,
    },
  } as never);
  return update;
}

describe("POST /api/ui/strategy-workspace/section", () => {
  beforeEach(() => vi.clearAllMocks());

  it("persists explicit reviewed-empty contradiction assessment", async () => {
    const update = context();
    const form = base("contradictions", "review_empty");
    const response = await POST(request(form));
    const location = new URL(response.headers.get("location")!);
    expect(location.pathname).toBe("/es/campaign/strategy");
    expect(location.hash).toBe("#strategy-room");
    expect(location.searchParams.get("notice")).toBe("strategy_section_saved");
    expect(update).toHaveBeenCalledWith(TENANT, CAMPAIGN, 3, expect.any(String), { contradictions: [] });
  });

  it("refuses reviewed-empty when it would erase an existing record", async () => {
    const update = context(workspace({ contradictions: [{
      id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      left_ref: EVIDENCE,
      right_ref: HYPOTHESIS,
      description: "Conflict",
      evidence_refs: [EVIDENCE],
      status: "OPEN",
      resolution: null,
    }] }));
    const response = await POST(request(base("contradictions", "review_empty")));
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("conflict");
    expect(update).not.toHaveBeenCalled();
  });

  it("rejects stale versions and unknown references", async () => {
    const stale = context(workspace({ version: 4 }));
    const staleForm = base("red_team_findings", "review_empty");
    let response = await POST(request(staleForm));
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("conflict");
    expect(stale).not.toHaveBeenCalled();

    const update = context();
    const option = base("options");
    option.set("title", "Option B");
    option.set("summary", "Second internal option.");
    option.append("hypothesis_refs", "cccccccc-cccc-4ccc-8ccc-cccccccccccc");
    option.append("evidence_refs", EVIDENCE);
    option.set("benefits", "Comparable");
    option.set("risks", "Review load");
    option.set("tradeoffs", "Time");
    response = await POST(request(option));
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("conflict");
    expect(update).not.toHaveBeenCalled();
  });

  it("requires objectives to reference an existing Team role", async () => {
    const update = context();
    const form = base("objectives");
    form.set("outcome", "Complete review");
    form.set("metric", "Reviewed records");
    form.set("baseline", "1");
    form.set("target", "5");
    form.set("deadline", "2026-09-01");
    form.set("owner_role_id", "dddddddd-dddd-4ddd-8ddd-dddddddddddd");
    form.append("evidence_refs", EVIDENCE);
    const response = await POST(request(form));
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("conflict");
    expect(update).not.toHaveBeenCalled();
  });

  it("requires the exact update grant rather than a role label", async () => {
    const update = context(workspace(), false);
    const response = await POST(request(base("contradictions", "review_empty")));
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("authorization_denied");
    expect(update).not.toHaveBeenCalled();
  });
});
