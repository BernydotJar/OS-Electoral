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

import { POST } from "@/app/api/ui/strategy-workspace/decision/route";
import { loadLiveCampaignContext } from "@/lib/server-context";

const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";
const ROLE = "33333333-3333-4333-8333-333333333333";
const OPTION = "44444444-4444-4444-8444-444444444444";

function memberships(approve = true) {
  return [{
    membership_id: "55555555-5555-4555-8555-555555555555",
    campaign_id: CAMPAIGN,
    roles: ["director_label_only"],
    grants: [
      {
        grant_id: "66666666-6666-4666-8666-666666666661",
        campaign_id: CAMPAIGN,
        workspace_id: null,
        action: "read",
        resource_type: "strategy_workspace",
        resource_id: CAMPAIGN,
        purpose: "Review campaign strategy workspace",
        approval_receipt_id: "approval-read",
      },
      ...(approve ? [{
        grant_id: "66666666-6666-4666-8666-666666666662",
        campaign_id: CAMPAIGN,
        workspace_id: null,
        action: "approve",
        resource_type: "strategy_workspace",
        resource_id: CAMPAIGN,
        purpose: "Approve internal campaign strategy option",
        approval_receipt_id: "approval-decide",
      }] : []),
    ],
  }];
}

function workspace(overrides: Record<string, unknown> = {}) {
  return {
    version: 8,
    status: "READY_FOR_HUMAN_DECISION",
    human_decision_required: true,
    decision: null,
    options: [{ id: OPTION, title: "Option A" }],
    ...overrides,
  };
}

function team() {
  return {
    status: "READY_FOR_HUMAN_REVIEW",
    roles: [{ id: ROLE, title: "Dirección", area: "Dirección" }],
  };
}

function request(overrides: Record<string, string> = {}) {
  const form = new FormData();
  form.set("locale", "es");
  form.set("version", overrides.version ?? "8");
  form.set("idempotency_key", "strategy-decision:12345678-1234-4234-8234-123456789abc");
  form.set("selected_option_id", overrides.selected_option_id ?? OPTION);
  form.set("human_role_id", overrides.human_role_id ?? ROLE);
  form.set("reason", "La persona autorizada comparó evidencia, riesgos y tradeoffs.");
  return new Request("https://campaign.example.test/api/ui/strategy-workspace/decision", {
    method: "POST",
    headers: { origin: "https://campaign.example.test", host: "campaign.example.test" },
    body: form,
  });
}

function context(current = workspace(), approve = true) {
  const decide = vi.fn(async () => ({}));
  vi.mocked(loadLiveCampaignContext).mockResolvedValue({
    tenantId: TENANT,
    campaign: { id: CAMPAIGN },
    identity: { application_memberships: memberships(approve) },
    api: {
      strategyWorkspace: vi.fn(async () => ({ workspace: current })),
      teamWorkspace: vi.fn(async () => ({ workspace: team() })),
      decideStrategyWorkspace: decide,
    },
  } as never);
  return decide;
}

describe("POST /api/ui/strategy-workspace/decision", () => {
  beforeEach(() => vi.clearAllMocks());

  it("records a human decision against the current version without inventing an option", async () => {
    const decide = context();
    const response = await POST(request());
    const location = new URL(response.headers.get("location")!);
    expect(location.pathname).toBe("/es/campaign/strategy");
    expect(location.hash).toBe("#strategy-room");
    expect(location.searchParams.get("notice")).toBe("strategy_decided");
    expect(decide).toHaveBeenCalledWith(
      TENANT,
      CAMPAIGN,
      8,
      expect.any(String),
      {
        selected_option_id: OPTION,
        human_role_id: ROLE,
        reason: "La persona autorizada comparó evidencia, riesgos y tradeoffs.",
      },
    );
  });

  it("rejects premature and stale decisions", async () => {
    let decide = context(workspace({ status: "OPTIONS_INCOMPLETE", human_decision_required: false }));
    let response = await POST(request());
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("conflict");
    expect(decide).not.toHaveBeenCalled();

    decide = context(workspace({ version: 9 }));
    response = await POST(request());
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("conflict");
    expect(decide).not.toHaveBeenCalled();
  });

  it("rejects unknown option and Team role references", async () => {
    let decide = context();
    let response = await POST(request({ selected_option_id: "77777777-7777-4777-8777-777777777777" }));
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("conflict");
    expect(decide).not.toHaveBeenCalled();

    decide = context();
    response = await POST(request({ human_role_id: "88888888-8888-4888-8888-888888888888" }));
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("conflict");
    expect(decide).not.toHaveBeenCalled();
  });

  it("requires the exact approve grant rather than a role label", async () => {
    const decide = context(workspace(), false);
    const response = await POST(request());
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("authorization_denied");
    expect(decide).not.toHaveBeenCalled();
  });
});
