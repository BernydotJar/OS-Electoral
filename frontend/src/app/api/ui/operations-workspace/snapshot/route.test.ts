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
    noticeForError: vi.fn((error: unknown) =>
      error instanceof UiContextError ? error.notice : "request_failed"),
  };
});

import { POST } from "@/app/api/ui/operations-workspace/snapshot/route";
import { loadLiveCampaignContext } from "@/lib/server-context";

const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";
const ROADMAP = "33333333-3333-4333-8333-333333333333";

function memberships(mode: "exact" | "missing-read" | "wrong" = "exact") {
  const grants = mode === "exact"
    ? [
        ["read", "campaign_roadmap", "Review campaign operations roadmap"],
        ["create", "war_room_snapshot", "Create daily campaign war room snapshot"],
        ["read", "war_room_snapshot", "Review daily campaign war room snapshot"],
      ]
    : mode === "missing-read"
      ? [
          ["read", "campaign_roadmap", "Review campaign operations roadmap"],
          ["create", "war_room_snapshot", "Create daily campaign war room snapshot"],
        ]
      : [["create", "war_room_snapshot", "Wrong purpose"]];
  return [{
    membership_id: "44444444-4444-4444-8444-444444444444",
    campaign_id: CAMPAIGN,
    roles: ["director_label_only"],
    grants: grants.map(([action, resource_type, purpose], index) => ({
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

function context(options: {
  mode?: "exact" | "missing-read" | "wrong";
  roadmapVersion?: number;
  strategyStatus?: string;
  createdRoadmapId?: string;
} = {}) {
  const create = vi.fn(async (_tenant, _campaign, expectedVersion) => ({
    snapshot: {
      id: "66666666-6666-4666-8666-666666666666",
      tenant_id: TENANT,
      campaign_id: CAMPAIGN,
      roadmap_id: options.createdRoadmapId ?? ROADMAP,
      roadmap_version: expectedVersion,
    },
  }));
  vi.mocked(loadLiveCampaignContext).mockResolvedValue({
    tenantId: TENANT,
    campaign: { id: CAMPAIGN },
    identity: { application_memberships: memberships(options.mode ?? "exact") },
    api: {
      campaignRoadmap: vi.fn(async () => ({ roadmap: {
        id: ROADMAP,
        tenant_id: TENANT,
        campaign_id: CAMPAIGN,
        version: options.roadmapVersion ?? 7,
      } })),
      strategyWorkspace: vi.fn(async () => ({ workspace: {
        tenant_id: TENANT,
        campaign_id: CAMPAIGN,
        status: options.strategyStatus ?? "DECIDED_INTERNAL",
      } })),
      createWarRoomSnapshot: create,
    },
  } as never);
  return create;
}

function request() {
  const form = new FormData();
  form.set("locale", "es");
  form.set("version", "7");
  form.set("idempotency_key", "war-room-snapshot:12345678-1234-4234-8234-123456789abc");
  form.set("snapshot_date", "2026-08-16");
  form.set("priorities", "Resolver blocker de evidencia\nConfirmar decisión humana");
  form.set("follow_up_notes", "Revisar evidencia al cierre del día");
  return new Request("https://campaign.example.test/api/ui/operations-workspace/snapshot", {
    method: "POST",
    headers: { origin: "https://campaign.example.test", host: "campaign.example.test" },
    body: form,
  });
}

function notice(response: Response) {
  return new URL(response.headers.get("location")!).searchParams.get("notice");
}

describe("POST /api/ui/operations-workspace/snapshot", () => {
  beforeEach(() => vi.clearAllMocks());

  it("creates an immutable snapshot from the exact current roadmap version", async () => {
    const create = context();
    const response = await POST(request());
    const location = new URL(response.headers.get("location")!);
    expect(location.pathname).toBe("/es/campaign/operations");
    expect(location.hash).toBe("#war-room");
    expect(notice(response)).toBe("war_room_snapshot_created");
    expect(create).toHaveBeenCalledWith(
      TENANT,
      CAMPAIGN,
      7,
      expect.any(String),
      {
        snapshot_date: "2026-08-16",
        priorities: ["Resolver blocker de evidencia", "Confirmar decisión humana"],
        follow_up_notes: ["Revisar evidencia al cierre del día"],
      },
    );
  });

  it("fails closed for stale roadmap versions and a Strategy that is no longer decided", async () => {
    let create = context({ roadmapVersion: 8 });
    expect(notice(await POST(request()))).toBe("conflict");
    expect(create).not.toHaveBeenCalled();

    create = context({ strategyStatus: "READY_FOR_HUMAN_DECISION" });
    expect(notice(await POST(request()))).toBe("conflict");
    expect(create).not.toHaveBeenCalled();
  });

  it("requires exact roadmap-read, snapshot-create, and snapshot-read authority", async () => {
    let create = context({ mode: "missing-read" });
    expect(notice(await POST(request()))).toBe("authorization_denied");
    expect(create).not.toHaveBeenCalled();

    create = context({ mode: "wrong" });
    expect(notice(await POST(request()))).toBe("authorization_denied");
    expect(create).not.toHaveBeenCalled();
  });

  it("rejects upstream snapshot evidence that does not bind to the current roadmap", async () => {
    const create = context({ createdRoadmapId: "77777777-7777-4777-8777-777777777777" });
    expect(notice(await POST(request()))).toBe("dependency_failure");
    expect(create).toHaveBeenCalledTimes(1);
  });
});
