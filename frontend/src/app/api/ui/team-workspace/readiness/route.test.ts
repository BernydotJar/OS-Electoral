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

import { POST } from "@/app/api/ui/team-workspace/readiness/route";
import { loadLiveCampaignContext } from "@/lib/server-context";
import type { TeamWorkspaceProjection } from "@/lib/contracts";

const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";
const ROLE = "33333333-3333-4333-8333-333333333333";
const WORKSPACE = "44444444-4444-4444-8444-444444444444";

function workspace(
  overrides: Partial<TeamWorkspaceProjection> = {},
): TeamWorkspaceProjection {
  return {
    id: WORKSPACE,
    tenant_id: TENANT,
    campaign_id: CAMPAIGN,
    campaign_version: 1,
    campaign_status: "ACTIVE",
    campaign_name: "Campaña",
    organization_template: "LEAN_CAMPAIGN",
    roles: [
      {
        id: ROLE,
        title: "Dirección",
        area: "Dirección",
        purpose: "Coordinar",
        responsibilities: ["Coordinar"],
        decision_scope: ["Preparar"],
        deliverables: ["Agenda"],
        collaboration_points: ["Equipo"],
        success_signals: ["Visibilidad"],
        status: "VACANT",
        principal_id: null,
        availability_status: "UNASSESSED",
        weekly_capacity_hours: null,
        onboarding_status: "NOT_STARTED",
        vacancy_plan: "Cubrir con decisión humana.",
      },
    ],
    work_items: [],
    training_requirements: null,
    access_recommendations: null,
    status: "STRUCTURE_IN_PROGRESS",
    checks: [],
    completed_checks: 5,
    total_checks: 8,
    filled_role_count: 0,
    vacant_role_count: 1,
    total_weekly_capacity_hours: 0,
    total_work_item_count: 0,
    planned_work_item_count: 0,
    active_work_item_count: 0,
    blocked_work_item_count: 0,
    completed_work_item_count: 0,
    attention_work_item_count: 0,
    next_action: "ASSIGN_ACCOUNTABILITY",
    authority_effect: "NONE",
    external_effects: "NONE",
    limitation_codes: [
      "ROLE_LABELS_ARE_NOT_PERMISSIONS",
      "ACCESS_RECOMMENDATIONS_REQUIRE_HUMAN_AUTHORIZATION",
      "NO_VOTER_PROFILING",
      "NO_EXTERNAL_EFFECTS",
    ],
    version: 3,
    created_at: "2026-08-12T00:00:00Z",
    updated_at: "2026-08-12T00:00:00Z",
    ...overrides,
  };
}

function membership(update = true) {
  return [
    {
      membership_id: "55555555-5555-4555-8555-555555555555",
      campaign_id: CAMPAIGN,
      roles: ["operator_label_only"],
      grants: [
        {
          grant_id: "66666666-6666-4666-8666-666666666666",
          campaign_id: CAMPAIGN,
          workspace_id: null,
          action: "read",
          resource_type: "team_workspace",
          resource_id: CAMPAIGN,
          purpose: "Review campaign team workspace",
          approval_receipt_id: "approval-read",
        },
        ...(update
          ? [
              {
                grant_id: "77777777-7777-4777-8777-777777777777",
                campaign_id: CAMPAIGN,
                workspace_id: null,
                action: "update",
                resource_type: "team_workspace",
                resource_id: CAMPAIGN,
                purpose: "Maintain campaign team workspace",
                approval_receipt_id: "approval-update",
              },
            ]
          : []),
      ],
    },
  ];
}

function request(
  section: "training_requirements" | "access_recommendations",
  action: "save" | "review_empty" = "review_empty",
  overrides: Record<string, string> = {},
) {
  const form = new FormData();
  form.set("locale", "es");
  form.set("version", overrides.version ?? "3");
  form.set("idempotency_key", "team-readiness:12345678-1234-4234-8234-123456789abc");
  form.set("section", section);
  form.set("readiness_action", action);
  form.set("record_id", overrides.record_id ?? "");
  if (action === "save") {
    form.set("role_id", overrides.role_id ?? ROLE);
    form.set("status", overrides.status ?? (section === "training_requirements" ? "COMPLETE" : "REVIEWED"));
    if (section === "training_requirements") {
      form.set("title", overrides.title ?? "Orientación interna");
      form.set("description", overrides.description ?? "Completar orientación documentada.");
    } else {
      form.set("access_action", overrides.access_action ?? "read");
      form.set("resource_type", overrides.resource_type ?? "candidate_workspace");
      form.set("purpose", overrides.purpose ?? "Review candidate evidence workspace");
    }
  }
  return new Request("https://campaign.example.test/api/ui/team-workspace/readiness", {
    method: "POST",
    headers: {
      origin: "https://campaign.example.test",
      host: "campaign.example.test",
    },
    body: form,
  });
}

function context(current: TeamWorkspaceProjection, update = true) {
  const updateTeamWorkspace = vi.fn(async () => ({}));
  vi.mocked(loadLiveCampaignContext).mockResolvedValue({
    tenantId: TENANT,
    campaign: { id: CAMPAIGN },
    identity: { application_memberships: membership(update) },
    api: {
      teamWorkspace: vi.fn(async () => ({ workspace: current, audit_event_id: ROLE })),
      updateTeamWorkspace,
    },
  } as never);
  return updateTeamWorkspace;
}

describe("POST /api/ui/team-workspace/readiness", () => {
  beforeEach(() => vi.clearAllMocks());

  it("persists an explicit reviewed-empty training collection", async () => {
    const update = context(workspace());
    const response = await POST(request("training_requirements"));
    const destination = new URL(response.headers.get("location")!);
    expect(destination.pathname).toBe("/es/campaign/team");
    expect(destination.searchParams.get("notice")).toBe("team_readiness_saved");
    expect(destination.hash).toBe("#team-readiness-completion");
    expect(update).toHaveBeenCalledWith(
      TENANT,
      CAMPAIGN,
      3,
      expect.any(String),
      { training_requirements: [] },
    );
  });

  it("upserts a campaign-scoped reviewed access recommendation with no authority effect", async () => {
    const update = context(workspace());
    await POST(request("access_recommendations", "save"));
    expect(update).toHaveBeenCalledWith(
      TENANT,
      CAMPAIGN,
      3,
      expect.any(String),
      {
        access_recommendations: [
          expect.objectContaining({
            role_id: ROLE,
            campaign_id: CAMPAIGN,
            workspace_id: null,
            resource_id: CAMPAIGN,
            action: "read",
            resource_type: "candidate_workspace",
            status: "REVIEWED",
            authority_effect: "NONE",
          }),
        ],
      },
    );
  });

  it("fails closed rather than erasing a non-empty collection", async () => {
    const current = workspace({
      training_requirements: [
        {
          id: "88888888-8888-4888-8888-888888888888",
          role_id: ROLE,
          title: "Orientación",
          description: "Completar orientación.",
          status: "COMPLETE",
        },
      ],
    });
    const update = context(current);
    const response = await POST(request("training_requirements"));
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe(
      "conflict",
    );
    expect(update).not.toHaveBeenCalled();
  });

  it("rejects stale versions and unknown role references", async () => {
    const update = context(workspace({ version: 4 }));
    let response = await POST(request("training_requirements", "save"));
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe(
      "conflict",
    );
    expect(update).not.toHaveBeenCalled();

    const update2 = context(workspace());
    response = await POST(
      request("training_requirements", "save", {
        role_id: "99999999-9999-4999-8999-999999999999",
      }),
    );
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe(
      "conflict",
    );
    expect(update2).not.toHaveBeenCalled();
  });

  it("requires the exact Team update grant", async () => {
    const update = context(workspace(), false);
    const response = await POST(request("training_requirements"));
    expect(new URL(response.headers.get("location")!).searchParams.get("notice")).toBe(
      "authorization_denied",
    );
    expect(update).not.toHaveBeenCalled();
  });
});
