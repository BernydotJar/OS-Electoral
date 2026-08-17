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

import { POST } from "@/app/api/ui/operations-workspace/section/route";
import { loadLiveCampaignContext } from "@/lib/server-context";

const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";
const ROLE = "33333333-3333-4333-8333-333333333333";
const PHASE = "44444444-4444-4444-8444-444444444444";
const WORKSTREAM = "55555555-5555-4555-8555-555555555555";
const TASK = "66666666-6666-4666-8666-666666666666";
const EVIDENCE = "77777777-7777-4777-8777-777777777777";
const DECISION = "88888888-8888-4888-8888-888888888888";

function memberships(exact = true) {
  const grants = exact
    ? [
        ["read", "Review campaign operations roadmap"],
        ["update", "Maintain campaign operations roadmap"],
      ]
    : [["update", "Wrong purpose"]];
  return [{
    membership_id: "99999999-9999-4999-8999-999999999999",
    campaign_id: CAMPAIGN,
    roles: ["director_label_only"],
    grants: grants.map(([action, purpose], index) => ({
      grant_id: `aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaa${index}`,
      campaign_id: CAMPAIGN,
      workspace_id: null,
      action,
      resource_type: "campaign_roadmap",
      resource_id: CAMPAIGN,
      purpose,
      approval_receipt_id: `approval-${index}`,
    })),
  }];
}

function roadmap(version = 7) {
  return {
    id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
    tenant_id: TENANT,
    campaign_id: CAMPAIGN,
    version,
    phases: [{ id: PHASE, name: "Foundation" }],
    workstreams: [{ id: WORKSTREAM, name: "Evidence" }],
    milestones: [],
    tasks: [{ id: TASK, title: "Existing task" }],
    blockers: [],
    decisions: [{
      id: DECISION,
      title: "Choose scope",
      human_role_id: ROLE,
      options: ["Option A", "Option B"],
      due_date: "2026-08-18",
      status: "REQUIRED",
      decision: null,
    }],
    follow_up_items: [],
    learning_notes: [],
  };
}

function context(options: {
  exact?: boolean;
  version?: number;
  strategyStatus?: string;
} = {}) {
  const update = vi.fn(async (_tenant, _campaign, expectedVersion) => ({
    roadmap: { tenant_id: TENANT, campaign_id: CAMPAIGN, version: expectedVersion + 1 },
  }));
  vi.mocked(loadLiveCampaignContext).mockResolvedValue({
    tenantId: TENANT,
    campaign: { id: CAMPAIGN },
    identity: { application_memberships: memberships(options.exact ?? true) },
    api: {
      campaignRoadmap: vi.fn(async () => ({ roadmap: roadmap(options.version ?? 7) })),
      teamWorkspace: vi.fn(async () => ({ workspace: {
        tenant_id: TENANT,
        campaign_id: CAMPAIGN,
        status: "READY_FOR_HUMAN_REVIEW",
        roles: [{ id: ROLE, status: "FILLED" }],
      } })),
      strategyWorkspace: vi.fn(async () => ({ workspace: {
        tenant_id: TENANT,
        campaign_id: CAMPAIGN,
        status: options.strategyStatus ?? "DECIDED_INTERNAL",
        evidence: [{ id: EVIDENCE }],
      } })),
      candidateWorkspace: vi.fn(async () => ({ workspace: {
        tenant_id: TENANT,
        campaign_id: CAMPAIGN,
        evidence: [],
      } })),
      updateCampaignRoadmap: update,
    },
  } as never);
  return update;
}

function baseForm(section: string, recordId = "") {
  const form = new FormData();
  form.set("locale", "es");
  form.set("version", "7");
  form.set("idempotency_key", `operations-${section}:12345678-1234-4234-8234-123456789abc`);
  form.set("section", section);
  form.set("record_id", recordId);
  return form;
}

function taskRequest(dependency = TASK, evidence = EVIDENCE) {
  const form = baseForm("tasks");
  form.set("phase_id", PHASE);
  form.set("workstream_id", WORKSTREAM);
  form.set("milestone_id", "");
  form.set("title", "Verify launch checklist");
  form.set("owner_role_id", ROLE);
  form.set("execution_status", "PLANNED");
  form.set("due_date", "2026-08-20");
  form.append("dependency_ids", dependency);
  form.append("evidence_refs", evidence);
  return request(form);
}

function decisionRequest(options: string, selected: string) {
  const form = baseForm("decisions", DECISION);
  form.set("title", "Choose scope");
  form.set("human_role_id", ROLE);
  form.set("options", options);
  form.set("due_date", "2026-08-18");
  form.set("status", "DECIDED");
  form.set("decision", selected);
  return request(form);
}

function request(form: FormData) {
  return new Request("https://campaign.example.test/api/ui/operations-workspace/section", {
    method: "POST",
    headers: { origin: "https://campaign.example.test", host: "campaign.example.test" },
    body: form,
  });
}

function notice(response: Response) {
  return new URL(response.headers.get("location")!).searchParams.get("notice");
}

describe("POST /api/ui/operations-workspace/section", () => {
  beforeEach(() => vi.clearAllMocks());

  it("persists a bounded task update using only current roadmap, Team, and evidence references", async () => {
    const update = context();
    const response = await POST(taskRequest());
    expect(notice(response)).toBe("operations_section_saved");
    expect(update).toHaveBeenCalledWith(
      TENANT,
      CAMPAIGN,
      7,
      expect.any(String),
      { tasks: [
        expect.objectContaining({ id: TASK, title: "Existing task" }),
        expect.objectContaining({
          title: "Verify launch checklist",
          owner_role_id: ROLE,
          phase_id: PHASE,
          workstream_id: WORKSTREAM,
          dependency_ids: [TASK],
          evidence_refs: [EVIDENCE],
          execution_status: "PLANNED",
        }),
      ] },
    );
  });

  it("fails closed for stale versions, undecided Strategy, and non-exact grants", async () => {
    let update = context({ version: 8 });
    expect(notice(await POST(taskRequest()))).toBe("conflict");
    expect(update).not.toHaveBeenCalled();

    update = context({ strategyStatus: "READY_FOR_HUMAN_DECISION" });
    expect(notice(await POST(taskRequest()))).toBe("conflict");
    expect(update).not.toHaveBeenCalled();

    update = context({ exact: false });
    expect(notice(await POST(taskRequest()))).toBe("authorization_denied");
    expect(update).not.toHaveBeenCalled();
  });

  it("rejects unknown dependency and evidence references before mutation", async () => {
    const unknown = "cccccccc-cccc-4ccc-8ccc-cccccccccccc";
    let update = context();
    expect(notice(await POST(taskRequest(unknown, EVIDENCE)))).toBe("conflict");
    expect(update).not.toHaveBeenCalled();

    update = context();
    expect(notice(await POST(taskRequest(TASK, unknown)))).toBe("conflict");
    expect(update).not.toHaveBeenCalled();
  });

  it("allows a human decision only from options already persisted on the current roadmap", async () => {
    const update = context();
    expect(notice(await POST(decisionRequest("Option A\nOption B", "Option B")))).toBe("operations_section_saved");
    expect(update).toHaveBeenCalledWith(
      TENANT,
      CAMPAIGN,
      7,
      expect.any(String),
      { decisions: [expect.objectContaining({
        id: DECISION,
        options: ["Option A", "Option B"],
        status: "DECIDED",
        decision: "Option B",
      })] },
    );
  });

  it("rejects changing the alternatives and deciding in the same request", async () => {
    const update = context();
    expect(notice(await POST(decisionRequest("Option A\nOption C", "Option C")))).toBe("conflict");
    expect(update).not.toHaveBeenCalled();
  });
});
