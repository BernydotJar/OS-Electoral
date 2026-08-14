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

import { POST } from "@/app/api/ui/strategy-workspace/start/route";
import { loadLiveCampaignContext } from "@/lib/server-context";

const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";

function memberships(exact = true) {
  const grants = exact ? [
    ["create", "Create campaign strategy workspace"],
    ["read", "Review campaign strategy workspace"],
  ] : [["create", "Wrong purpose"]];
  return [{
    membership_id: "33333333-3333-4333-8333-333333333333",
    campaign_id: CAMPAIGN,
    roles: ["strategy_director_label_only"],
    grants: grants.map(([action, purpose], index) => ({
      grant_id: `44444444-4444-4444-8444-44444444444${index}`,
      campaign_id: CAMPAIGN,
      workspace_id: null,
      action,
      resource_type: "strategy_workspace",
      resource_id: CAMPAIGN,
      purpose,
      approval_receipt_id: `approval-${index}`,
    })),
  }];
}

function request() {
  const form = new FormData();
  form.set("locale", "es");
  form.set("idempotency_key", "strategy-start:12345678-1234-4234-8234-123456789abc");
  form.set("title", "Sala de estrategia interna");
  return new Request("https://campaign.example.test/api/ui/strategy-workspace/start", {
    method: "POST",
    headers: { origin: "https://campaign.example.test", host: "campaign.example.test" },
    body: form,
  });
}

function context(candidateStatus = "INTERNALLY_APPROVED", teamStatus = "READY_FOR_HUMAN_REVIEW", exact = true) {
  const start = vi.fn(async () => ({}));
  vi.mocked(loadLiveCampaignContext).mockResolvedValue({
    tenantId: TENANT,
    campaign: { id: CAMPAIGN },
    identity: { application_memberships: memberships(exact) },
    api: {
      candidateWorkspace: vi.fn(async () => ({ workspace: { status: candidateStatus } })),
      teamWorkspace: vi.fn(async () => ({ workspace: { status: teamStatus } })),
      startStrategyWorkspace: start,
    },
  } as never);
  return start;
}

describe("POST /api/ui/strategy-workspace/start", () => {
  beforeEach(() => vi.clearAllMocks());

  it("starts only after Candidate and Team prerequisites", async () => {
    const start = context();
    const response = await POST(request());
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("strategy_started");
    expect(start).toHaveBeenCalledWith(
      TENANT,
      CAMPAIGN,
      expect.any(String),
      { title: "Sala de estrategia interna" },
    );
  });

  it("fails closed when a prerequisite is not ready", async () => {
    const start = context("IN_REVIEW");
    const response = await POST(request());
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("conflict");
    expect(start).not.toHaveBeenCalled();
  });

  it("does not trust role labels without the exact grants", async () => {
    const start = context("INTERNALLY_APPROVED", "READY_FOR_HUMAN_REVIEW", false);
    const response = await POST(request());
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("authorization_denied");
    expect(start).not.toHaveBeenCalled();
  });
});
