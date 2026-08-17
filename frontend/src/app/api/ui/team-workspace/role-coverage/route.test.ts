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

import { POST } from "@/app/api/ui/team-workspace/role-coverage/route";
import { loadLiveCampaignContext } from "@/lib/server-context";

const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";
const PRINCIPAL = "33333333-3333-4333-8333-333333333333";
const FOREIGN_PRINCIPAL = "44444444-4444-4444-8444-444444444444";
const ROLE = "55555555-5555-4555-8555-555555555555";

function membership(exact = true) {
  const grants = exact
    ? [
        ["read", "Review campaign team workspace"],
        ["update", "Maintain campaign team workspace"],
      ]
    : [["update", "Wrong purpose"]];
  return [{
    membership_id: "66666666-6666-4666-8666-666666666666",
    campaign_id: CAMPAIGN,
    roles: ["operator_label_only"],
    grants: grants.map(([action, purpose], index) => ({
      grant_id: `77777777-7777-4777-8777-77777777777${index}`,
      campaign_id: CAMPAIGN,
      workspace_id: null,
      action,
      resource_type: "team_workspace",
      resource_id: CAMPAIGN,
      purpose,
      approval_receipt_id: `approval-${index}`,
    })),
  }];
}

function vacantRole() {
  return {
    id: ROLE,
    title: "Dirección de campaña",
    area: "Dirección",
    purpose: "Coordinar trabajo interno.",
    responsibilities: ["Coordinar"],
    decision_scope: ["Preparar decisiones"],
    deliverables: ["Agenda"],
    collaboration_points: ["Equipo"],
    success_signals: ["Cadencia"],
    status: "VACANT",
    principal_id: null,
    availability_status: "UNASSESSED",
    weekly_capacity_hours: null,
    onboarding_status: "NOT_STARTED",
    vacancy_plan: "Cubrir mediante decisión humana.",
  };
}

function context(options: {
  exact?: boolean;
  currentVersion?: number;
  roleStatus?: "VACANT" | "FILLED";
  savedPrincipal?: string;
} = {}) {
  const role = vacantRole();
  if (options.roleStatus === "FILLED") {
    Object.assign(role, {
      status: "FILLED",
      principal_id: FOREIGN_PRINCIPAL,
      availability_status: "AVAILABLE",
      weekly_capacity_hours: 20,
      onboarding_status: "COMPLETE",
      vacancy_plan: null,
    });
  }
  const update = vi.fn(async (_tenant, _campaign, expectedVersion, _key, changes) => ({
    workspace: {
      tenant_id: TENANT,
      campaign_id: CAMPAIGN,
      version: expectedVersion + 1,
      roles: changes.roles.map((item: Record<string, unknown>) =>
        item.id === ROLE && options.savedPrincipal
          ? { ...item, principal_id: options.savedPrincipal }
          : item,
      ),
    },
  }));
  vi.mocked(loadLiveCampaignContext).mockResolvedValue({
    tenantId: TENANT,
    campaign: { id: CAMPAIGN },
    identity: {
      principal_id: PRINCIPAL,
      application_memberships: membership(options.exact ?? true),
    },
    api: {
      teamWorkspace: vi.fn(async () => ({ workspace: {
        tenant_id: TENANT,
        campaign_id: CAMPAIGN,
        version: options.currentVersion ?? 6,
        roles: [role],
      } })),
      updateTeamWorkspace: update,
    },
  } as never);
  return update;
}

function request() {
  const form = new FormData();
  form.set("locale", "es");
  form.set("version", "6");
  form.set("idempotency_key", "team-role-coverage:12345678-1234-4234-8234-123456789abc");
  form.set("role_id", ROLE);
  form.set("availability_status", "AVAILABLE");
  form.set("weekly_capacity_hours", "40");
  form.set("onboarding_confirmed", "confirmed");
  form.set("principal_id", FOREIGN_PRINCIPAL);
  return new Request("https://campaign.example.test/api/ui/team-workspace/role-coverage", {
    method: "POST",
    headers: { origin: "https://campaign.example.test", host: "campaign.example.test" },
    body: form,
  });
}

function notice(response: Response) {
  return new URL(response.headers.get("location")!).searchParams.get("notice");
}

describe("POST /api/ui/team-workspace/role-coverage", () => {
  beforeEach(() => vi.clearAllMocks());

  it("binds only the authenticated principal to a current vacant role", async () => {
    const update = context();
    const response = await POST(request());
    expect(notice(response)).toBe("team_role_covered");
    expect(update).toHaveBeenCalledWith(
      TENANT,
      CAMPAIGN,
      6,
      expect.any(String),
      { roles: [expect.objectContaining({
        id: ROLE,
        status: "FILLED",
        principal_id: PRINCIPAL,
        availability_status: "AVAILABLE",
        weekly_capacity_hours: 40,
        onboarding_status: "COMPLETE",
        vacancy_plan: null,
      })] },
    );
  });

  it("fails closed for stale versions, already-filled roles, and non-exact grants", async () => {
    let update = context({ currentVersion: 7 });
    expect(notice(await POST(request()))).toBe("conflict");
    expect(update).not.toHaveBeenCalled();

    update = context({ roleStatus: "FILLED" });
    expect(notice(await POST(request()))).toBe("conflict");
    expect(update).not.toHaveBeenCalled();

    update = context({ exact: false });
    expect(notice(await POST(request()))).toBe("authorization_denied");
    expect(update).not.toHaveBeenCalled();
  });

  it("rejects upstream evidence that binds a different principal", async () => {
    const update = context({ savedPrincipal: FOREIGN_PRINCIPAL });
    expect(notice(await POST(request()))).toBe("dependency_failure");
    expect(update).toHaveBeenCalledTimes(1);
  });
});
