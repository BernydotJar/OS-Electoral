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

import { POST } from "@/app/api/ui/operations-workspace/start/route";
import { loadLiveCampaignContext } from "@/lib/server-context";

const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";
const ROLE = "33333333-3333-4333-8333-333333333333";

function memberships(exact = true) {
  const grants = exact
    ? [
        ["create", "Create campaign operations roadmap", "campaign_roadmap"],
        ["read", "Review campaign operations roadmap", "campaign_roadmap"],
      ]
    : [["create", "Wrong purpose", "campaign_roadmap"]];
  return [{
    membership_id: "44444444-4444-4444-8444-444444444444",
    campaign_id: CAMPAIGN,
    roles: ["director_label_only"],
    grants: grants.map(([action, purpose, resource_type], index) => ({
      grant_id: `55555555-5555-4555-8555-55555555555${index}`,
      campaign_id: CAMPAIGN,
      workspace_id: null,
      action,
      resource_type,
      resource_id: CAMPAIGN,
      purpose,
      approval_receipt_id: `approval-${index}`,
    })),
  }];
}

function request() {
  const form = new FormData();
  form.set("locale", "es");
  form.set("idempotency_key", "operations-start:12345678-1234-4234-8234-123456789abc");
  form.set("title", "Roadmap operativo 2026");
  return new Request("https://campaign.example.test/api/ui/operations-workspace/start", {
    method: "POST",
    headers: { origin: "https://campaign.example.test", host: "campaign.example.test" },
    body: form,
  });
}

function context(strategyStatus = "DECIDED_INTERNAL", teamStatus = "READY_FOR_HUMAN_REVIEW", exact = true) {
  const start = vi.fn(async () => ({ roadmap: { tenant_id: TENANT, campaign_id: CAMPAIGN, version: 1 } }));
  vi.mocked(loadLiveCampaignContext).mockResolvedValue({
    tenantId: TENANT,
    campaign: { id: CAMPAIGN },
    identity: { application_memberships: memberships(exact) },
    api: {
      strategyWorkspace: vi.fn(async () => ({ workspace: { tenant_id: TENANT, campaign_id: CAMPAIGN, status: strategyStatus } })),
      teamWorkspace: vi.fn(async () => ({ workspace: { tenant_id: TENANT, campaign_id: CAMPAIGN, status: teamStatus, roles: [{ id: ROLE, status: "FILLED" }] } })),
      startCampaignRoadmap: start,
    },
  } as never);
  return start;
}

describe("POST /api/ui/operations-workspace/start", () => {
  beforeEach(() => vi.clearAllMocks());

  it("starts Operations only after Strategy decision and Team readiness", async () => {
    const start = context();
    const response = await POST(request());
    const location = new URL(response.headers.get("location")!);
    expect(location.pathname).toBe("/es/campaign/operations");
    expect(location.hash).toBe("#war-room");
    expect(location.searchParams.get("notice")).toBe("operations_started");
    expect(start).toHaveBeenCalledWith(TENANT, CAMPAIGN, expect.any(String), { title: "Roadmap operativo 2026" });
  });

  it("fails closed when Strategy is not currently decided", async () => {
    const start = context("READY_FOR_HUMAN_DECISION");
    const response = await POST(request());
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("conflict");
    expect(start).not.toHaveBeenCalled();
  });

  it("requires exact grants instead of trusting a role label", async () => {
    const start = context("DECIDED_INTERNAL", "READY_FOR_HUMAN_REVIEW", false);
    const response = await POST(request());
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe("authorization_denied");
    expect(start).not.toHaveBeenCalled();
  });
});
