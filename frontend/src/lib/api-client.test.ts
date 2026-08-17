import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

import { CampaignOsApiClient } from "@/lib/api-client";
import type { FrontendConfig } from "@/lib/config";

const config: FrontendConfig = {
  environment: "test",
  mode: "live",
  apiBaseUrl: new URL("https://api.example.test/"),
  requestTimeoutMs: 1000,
  developmentAccessToken: null,
  developmentTenantId: null,
};
const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";

afterEach(() => vi.restoreAllMocks());

function corruptResponse(): Response {
  return new Response(JSON.stringify({ unexpected: true }), {
    status: 200,
    headers: {
      "content-type": "application/json",
      "x-correlation-id": "corr-1",
    },
  });
}

describe("CampaignOsApiClient contract failures", () => {
  it.each([
    [
      "candidate",
      (client: CampaignOsApiClient) =>
        client.candidateWorkspace(TENANT, CAMPAIGN),
    ],
    [
      "team",
      (client: CampaignOsApiClient) => client.teamWorkspace(TENANT, CAMPAIGN),
    ],
    [
      "strategy",
      (client: CampaignOsApiClient) =>
        client.strategyWorkspace(TENANT, CAMPAIGN),
    ],
    [
      "roadmap",
      (client: CampaignOsApiClient) => client.campaignRoadmap(TENANT, CAMPAIGN),
    ],
    [
      "War Room snapshot",
      (client: CampaignOsApiClient) =>
        client.latestWarRoomSnapshot(TENANT, CAMPAIGN),
    ],
  ])(
    "maps invalid %s responses to one fail-closed upstream error",
    async (_label, request) => {
      vi.stubGlobal(
        "fetch",
        vi.fn(async () => corruptResponse()),
      );
      const client = new CampaignOsApiClient(config, "synthetic-token");

      await expect(request(client)).rejects.toMatchObject({
        status: 502,
        code: "INVALID_UPSTREAM_RESPONSE",
        correlationId: "corr-1",
      });
    },
  );
});

import {
  demoCandidateWorkspace,
  demoCampaignRoadmap,
  demoGuidedIntake,
  demoStrategyWorkspace,
  demoTeamWorkspace,
  demoWarRoomSnapshot,
} from "@/lib/demo-data";

describe("CampaignOsApiClient campaign mutations", () => {
  it("creates one draft through the tenant collection with idempotency", async () => {
    const create = {
      slug: "nueva-candidatura-a1b2c3d4",
      name: "Nueva candidatura",
      jurisdiction: "Antigua Guatemala",
      stage: "PREPARATION",
    };
    const fetchMock = vi.fn(
      async (input: URL | RequestInfo, init?: RequestInit) => {
        expect(String(input)).toBe(
          `https://api.example.test/api/v1/tenants/${TENANT}/campaigns`,
        );
        expect(init?.method).toBe("POST");
        const headers = new Headers(init?.headers);
        expect(headers.get("authorization")).toBe("Bearer synthetic-token");
        expect(headers.get("idempotency-key")).toBe("campaign-create-1");
        expect(headers.get("content-type")).toBe("application/json");
        expect(JSON.parse(String(init?.body))).toEqual(create);
        return new Response(
          JSON.stringify({
            campaign: {
              id: CAMPAIGN,
              tenant_id: TENANT,
              ...create,
              status: "DRAFT",
              version: 1,
            },
            audit_event_id: "66666666-6666-4666-8666-666666666666",
            outbox_event_id: "77777777-7777-4777-8777-777777777777",
          }),
          { status: 201, headers: { "content-type": "application/json" } },
        );
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new CampaignOsApiClient(config, "synthetic-token");

    const result = await client.createCampaign(
      TENANT,
      "campaign-create-1",
      create,
    );

    expect(result.campaign.status).toBe("DRAFT");
    expect(result.campaign.version).toBe(1);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});

describe("CampaignOsApiClient guided intake mutations", () => {
  it("sends exact start headers and validates the committed evidence", async () => {
    const fetchMock = vi.fn(
      async (_input: URL | RequestInfo, init?: RequestInit) => {
        expect(init?.method).toBe("POST");
        expect(new Headers(init?.headers).get("authorization")).toBe(
          "Bearer synthetic-token",
        );
        expect(new Headers(init?.headers).get("idempotency-key")).toBe(
          "start-key-1",
        );
        expect(init?.body).toBeUndefined();
        return new Response(
          JSON.stringify({
            ...demoGuidedIntake,
            outbox_event_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
            created: true,
          }),
          { status: 201, headers: { "content-type": "application/json" } },
        );
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new CampaignOsApiClient(config, "synthetic-token");

    const result = await client.startGuidedIntake(
      TENANT,
      CAMPAIGN,
      "start-key-1",
    );

    expect(result.created).toBe(true);
    expect(result.intake.campaign_id).toBe(CAMPAIGN);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("sends versioned update headers and a bounded JSON patch", async () => {
    const update = {
      office: "Alcaldía Municipal",
      budget_status: "ROUGH_RANGE" as const,
      known_unknowns: ["Calendario de inscripción"],
    };
    const fetchMock = vi.fn(
      async (_input: URL | RequestInfo, init?: RequestInit) => {
        expect(init?.method).toBe("PATCH");
        const headers = new Headers(init?.headers);
        expect(headers.get("idempotency-key")).toBe("update-key-1");
        expect(headers.get("if-match")).toBe('"2"');
        expect(headers.get("content-type")).toBe("application/json");
        expect(JSON.parse(String(init?.body))).toEqual(update);
        return new Response(
          JSON.stringify({
            ...demoGuidedIntake,
            intake: { ...demoGuidedIntake.intake, version: 3 },
            outbox_event_id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        );
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new CampaignOsApiClient(config, "synthetic-token");

    const result = await client.updateGuidedIntake(
      TENANT,
      CAMPAIGN,
      2,
      "update-key-1",
      update,
    );

    expect(result.intake.version).toBe(3);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});

describe("CampaignOsApiClient candidate workspace mutations", () => {
  it("creates the candidate workspace with an exact idempotency header", async () => {
    const fetchMock = vi.fn(
      async (_input: URL | RequestInfo, init?: RequestInit) => {
        expect(init?.method).toBe("POST");
        const headers = new Headers(init?.headers);
        expect(headers.get("idempotency-key")).toBe("candidate-start-1");
        expect(JSON.parse(String(init?.body))).toEqual({
          display_name: "Ana Pérez",
        });
        return new Response(
          JSON.stringify({
            ...demoCandidateWorkspace,
            outbox_event_id: "abababab-abab-4bab-8bab-abababababab",
          }),
          { status: 201, headers: { "content-type": "application/json" } },
        );
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new CampaignOsApiClient(config, "synthetic-token");

    const result = await client.startCandidateWorkspace(
      TENANT,
      CAMPAIGN,
      "candidate-start-1",
      { display_name: "Ana Pérez" },
    );

    expect(result.workspace.campaign_id).toBe(CAMPAIGN);
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("updates candidate evidence with optimistic concurrency", async () => {
    const evidence = {
      id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
      classification: "OFFICIAL_SOURCE" as const,
      status: "ACCEPTED" as const,
      title: "Convocatoria",
      source_reference: "https://example.test/convocatoria",
      source_authority: "Tribunal Electoral",
      jurisdiction: "Municipio de ejemplo",
      excerpt: null,
      observed_at: null,
    };
    const fetchMock = vi.fn(
      async (_input: URL | RequestInfo, init?: RequestInit) => {
        expect(init?.method).toBe("PATCH");
        const headers = new Headers(init?.headers);
        expect(headers.get("idempotency-key")).toBe("candidate-update-1");
        expect(headers.get("if-match")).toBe('"1"');
        expect(JSON.parse(String(init?.body))).toEqual({
          evidence: [evidence],
        });
        return new Response(
          JSON.stringify({
            ...demoCandidateWorkspace,
            workspace: {
              ...demoCandidateWorkspace.workspace,
              evidence: [evidence],
              version: 2,
            },
            outbox_event_id: "cdcdcdcd-cdcd-4dcd-8dcd-cdcdcdcdcdcd",
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        );
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new CampaignOsApiClient(config, "synthetic-token");

    const result = await client.updateCandidateWorkspace(
      TENANT,
      CAMPAIGN,
      1,
      "candidate-update-1",
      { evidence: [evidence] },
    );

    expect(result.workspace.version).toBe(2);
    expect(result.workspace.evidence).toEqual([evidence]);
  });
});

describe("CampaignOsApiClient team workspace mutations", () => {
  it("creates the team workspace with an exact idempotency header", async () => {
    const fetchMock = vi.fn(
      async (_input: URL | RequestInfo, init?: RequestInit) => {
        expect(init?.method).toBe("POST");
        const headers = new Headers(init?.headers);
        expect(headers.get("idempotency-key")).toBe("team-start-1");
        expect(JSON.parse(String(init?.body))).toEqual({
          organization_template: "LEAN_CAMPAIGN",
          blueprint_locale: "es",
        });
        return new Response(
          JSON.stringify({
            ...demoTeamWorkspace,
            outbox_event_id: "edededed-eded-4ded-8ded-edededededed",
          }),
          { status: 201, headers: { "content-type": "application/json" } },
        );
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new CampaignOsApiClient(config, "synthetic-token");

    const result = await client.startTeamWorkspace(
      TENANT,
      CAMPAIGN,
      "team-start-1",
      { organization_template: "LEAN_CAMPAIGN", blueprint_locale: "es" },
    );

    expect(result.workspace.organization_template).toBe("LEAN_CAMPAIGN");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("appends role cards with optimistic concurrency", async () => {
    const role = {
      id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
      title: "Coordinación territorial",
      area: "Territorio",
      purpose: "Organizar cobertura territorial verificable.",
      responsibilities: ["Diseñar coordinaciones", "Escalar bloqueos"],
      decision_scope: ["Prepare decisions", "Elevate approval needs"],
      deliverables: ["Plan", "Register", "Checklist"],
      collaboration_points: ["Research", "Legal"],
      success_signals: ["Owned", "Traceable", "Human-gated"],
      status: "VACANT" as const,
      principal_id: null,
      availability_status: "UNASSESSED" as const,
      weekly_capacity_hours: null,
      onboarding_status: "NOT_STARTED" as const,
      vacancy_plan: "Definir perfil y aprobar asignación humana.",
    };
    const fetchMock = vi.fn(
      async (_input: URL | RequestInfo, init?: RequestInit) => {
        expect(init?.method).toBe("PATCH");
        const headers = new Headers(init?.headers);
        expect(headers.get("idempotency-key")).toBe("team-role-1");
        expect(headers.get("if-match")).toBe('"1"');
        expect(JSON.parse(String(init?.body))).toEqual({ roles: [role] });
        return new Response(
          JSON.stringify({
            ...demoTeamWorkspace,
            workspace: {
              ...demoTeamWorkspace.workspace,
              roles: [role],
              vacant_role_count: 1,
              completed_checks: 5,
              status: "STRUCTURE_IN_PROGRESS",
              next_action: "ASSIGN_ACCOUNTABILITY",
              checks: demoTeamWorkspace.workspace.checks.map((check) => {
                if (check.key === "role_cards") {
                  return {
                    ...check,
                    complete: true,
                    reason_code: "ROLE_CARDS_DEFINED",
                  };
                }
                if (check.key === "availability") {
                  return {
                    ...check,
                    complete: true,
                    reason_code: "AVAILABILITY_ASSESSED",
                  };
                }
                if (check.key === "vacancies") {
                  return {
                    ...check,
                    complete: true,
                    reason_code: "VACANCIES_IDENTIFIED",
                  };
                }
                if (check.key === "onboarding") {
                  return {
                    ...check,
                    complete: true,
                    reason_code: "FILLED_ROLES_ONBOARDED",
                  };
                }
                return check;
              }),
              version: 2,
            },
            outbox_event_id: "fdfdfdfd-fdfd-4dfd-8dfd-fdfdfdfdfdfd",
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        );
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new CampaignOsApiClient(config, "synthetic-token");

    const result = await client.updateTeamWorkspace(
      TENANT,
      CAMPAIGN,
      1,
      "team-role-1",
      { roles: [role] },
    );

    expect(result.workspace.version).toBe(2);
    expect(result.workspace.roles).toEqual([role]);
  });
  it("previews append-only template changes with optimistic concurrency", async () => {
    const addition = {
      id: "abababab-abab-4bab-8bab-abababababab",
      title: "Digital Strategy",
      area: "Digital",
      purpose: "Prepare governed digital plans.",
      responsibilities: ["Maintain measurable hypotheses"],
      decision_scope: ["Prepare decisions", "Elevate approval needs"],
      deliverables: ["Plan", "Register", "Checklist"],
      collaboration_points: ["Research", "Legal"],
      success_signals: ["Owned", "Traceable", "Human-gated"],
      status: "VACANT" as const,
      principal_id: null,
      availability_status: "UNASSESSED" as const,
      weekly_capacity_hours: null,
      onboarding_status: "NOT_STARTED" as const,
      vacancy_plan: "Require human selection and approval.",
    };
    const fetchMock = vi.fn(
      async (_input: URL | RequestInfo, init?: RequestInit) => {
        expect(init?.method).toBe("POST");
        const headers = new Headers(init?.headers);
        expect(headers.get("if-match")).toBe('"5"');
        expect(headers.get("idempotency-key")).toBeNull();
        expect(JSON.parse(String(init?.body))).toEqual({
          organization_template: "FULL_CAMPAIGN",
          blueprint_locale: "en",
        });
        return new Response(
          JSON.stringify({
            audit_event_id: demoTeamWorkspace.audit_event_id,
            workspace_id: demoTeamWorkspace.workspace.id,
            tenant_id: TENANT,
            campaign_id: CAMPAIGN,
            workspace_version: 5,
            organization_template: "FULL_CAMPAIGN",
            blueprint_locale: "en",
            blueprint_version: "2026-07-27.1",
            additions: [addition],
            skipped: [],
            preview_digest: "a".repeat(64),
            authority_effect: "NONE",
            external_effects: "NONE",
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        );
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new CampaignOsApiClient(config, "synthetic-token");

    const result = await client.previewTeamWorkspaceTemplate(
      TENANT,
      CAMPAIGN,
      5,
      { organization_template: "FULL_CAMPAIGN", blueprint_locale: "en" },
    );

    expect(result.additions).toEqual([addition]);
    expect(result.authority_effect).toBe("NONE");
  });

  it("applies only the confirmed template preview with exact headers", async () => {
    const digest = "b".repeat(64);
    const fetchMock = vi.fn(
      async (_input: URL | RequestInfo, init?: RequestInit) => {
        expect(init?.method).toBe("POST");
        const headers = new Headers(init?.headers);
        expect(headers.get("if-match")).toBe('"5"');
        expect(headers.get("idempotency-key")).toBe("team-template-1");
        expect(JSON.parse(String(init?.body))).toEqual({
          organization_template: "FULL_CAMPAIGN",
          blueprint_locale: "es",
          preview_digest: digest,
        });
        return new Response(
          JSON.stringify({
            workspace: { ...demoTeamWorkspace.workspace, version: 6 },
            audit_event_id: demoTeamWorkspace.audit_event_id,
            outbox_event_id: "cdcdcdcd-cdcd-4dcd-8dcd-cdcdcdcdcdcd",
            preview_digest: digest,
            added_role_count: 5,
            skipped_role_count: 3,
          }),
          { status: 200, headers: { "content-type": "application/json" } },
        );
      },
    );
    vi.stubGlobal("fetch", fetchMock);
    const client = new CampaignOsApiClient(config, "synthetic-token");

    const result = await client.applyTeamWorkspaceTemplate(
      TENANT,
      CAMPAIGN,
      5,
      "team-template-1",
      {
        organization_template: "FULL_CAMPAIGN",
        blueprint_locale: "es",
        preview_digest: digest,
      },
    );

    expect(result.workspace.version).toBe(6);
    expect(result.added_role_count).toBe(5);
    expect(result.skipped_role_count).toBe(3);
  });
});


describe("CampaignOsApiClient strategy workspace mutations", () => {
  it("creates and updates Strategy with exact idempotency and optimistic concurrency", async () => {
    const fetchMock = vi.fn(async (input: URL | RequestInfo, init?: RequestInit) => {
      const headers = new Headers(init?.headers);
      const url = String(input);
      if (init?.method === "POST") {
        expect(url).toBe(`https://api.example.test/api/v1/tenants/${TENANT}/campaigns/${CAMPAIGN}/strategy-workspace`);
        expect(headers.get("idempotency-key")).toBe("strategy-start-1");
        expect(JSON.parse(String(init?.body))).toEqual({ title: "Internal strategy room" });
      } else {
        expect(init?.method).toBe("PATCH");
        expect(headers.get("idempotency-key")).toBe("strategy-update-1");
        expect(headers.get("if-match")).toBe('"2"');
        expect(JSON.parse(String(init?.body))).toEqual({ contradictions: [] });
      }
      return new Response(JSON.stringify({
        workspace: demoStrategyWorkspace.workspace,
        audit_event_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        outbox_event_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      }), { status: init?.method === "POST" ? 201 : 200, headers: { "content-type": "application/json" } });
    });
    vi.stubGlobal("fetch", fetchMock);
    const client = new CampaignOsApiClient(config, "synthetic-token");

    await client.startStrategyWorkspace(TENANT, CAMPAIGN, "strategy-start-1", { title: "Internal strategy room" });
    await client.updateStrategyWorkspace(TENANT, CAMPAIGN, 2, "strategy-update-1", { contradictions: [] });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("records a version-bound internal human decision without changing the requested workspace version", async () => {
    const selectedOptionId = demoStrategyWorkspace.workspace.options?.[0]?.id;
    const ownerRoleId = demoStrategyWorkspace.workspace.objectives?.[0]?.owner_role_id;
    if (!selectedOptionId || !ownerRoleId) throw new Error("strategy fixture incomplete");
    const decision = {
      id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
      workspace_version: 2,
      selected_option_id: selectedOptionId,
      reason: "Human compared the existing options.",
      human_role_id: ownerRoleId,
      approval_receipt_id: "approval-strategy-v2",
      decided_at: "2026-08-13T12:00:00Z",
    };
    const decidedWorkspace = {
      ...demoStrategyWorkspace.workspace,
      decision,
      status: "DECIDED_INTERNAL" as const,
      next_action: "REVALIDATE_DECISION" as const,
      human_decision_required: false,
    };
    const fetchMock = vi.fn(async (input: URL | RequestInfo, init?: RequestInit) => {
      expect(String(input)).toBe(`https://api.example.test/api/v1/tenants/${TENANT}/campaigns/${CAMPAIGN}/strategy-workspace/decision`);
      expect(init?.method).toBe("POST");
      const headers = new Headers(init?.headers);
      expect(headers.get("idempotency-key")).toBe("strategy-decision-1");
      expect(headers.get("if-match")).toBe('"2"');
      return new Response(JSON.stringify({
        workspace: decidedWorkspace,
        decision,
        audit_event_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
        outbox_event_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      }), { status: 200, headers: { "content-type": "application/json" } });
    });
    vi.stubGlobal("fetch", fetchMock);
    const client = new CampaignOsApiClient(config, "synthetic-token");

    const result = await client.decideStrategyWorkspace(TENANT, CAMPAIGN, 2, "strategy-decision-1", {
      selected_option_id: selectedOptionId,
      human_role_id: ownerRoleId,
      reason: decision.reason,
    });
    expect(result.workspace.version).toBe(2);
    expect(result.workspace.status).toBe("DECIDED_INTERNAL");
  });
});


describe("CampaignOsApiClient Operations mutations", () => {
  it("creates and updates the roadmap with idempotency and optimistic concurrency", async () => {
    const fetchMock = vi.fn(async (input: URL | RequestInfo, init?: RequestInit) => {
      expect(String(input)).toBe(
        `https://api.example.test/api/v1/tenants/${TENANT}/campaigns/${CAMPAIGN}/operations/roadmap`,
      );
      const headers = new Headers(init?.headers);
      if (init?.method === "POST") {
        expect(headers.get("idempotency-key")).toBe("operations-start-1");
        expect(JSON.parse(String(init?.body))).toEqual({ title: "Campaign execution roadmap" });
      } else {
        expect(init?.method).toBe("PATCH");
        expect(headers.get("idempotency-key")).toBe("operations-update-1");
        expect(headers.get("if-match")).toBe('"2"');
        expect(JSON.parse(String(init?.body))).toEqual({ blockers: [] });
      }
      return new Response(
        JSON.stringify({
          roadmap: demoCampaignRoadmap.roadmap,
          audit_event_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
          outbox_event_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        }),
        { status: init?.method === "POST" ? 201 : 200, headers: { "content-type": "application/json" } },
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    const client = new CampaignOsApiClient(config, "synthetic-token");

    await client.startCampaignRoadmap(TENANT, CAMPAIGN, "operations-start-1", {
      title: "Campaign execution roadmap",
    });
    await client.updateCampaignRoadmap(TENANT, CAMPAIGN, 2, "operations-update-1", {
      blockers: [],
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("creates a version-bound daily War Room snapshot without execution authority", async () => {
    const create = {
      snapshot_date: "2026-08-16",
      priorities: ["Resolve current blockers"],
      follow_up_notes: ["Director review at 17:00"],
    };
    const fetchMock = vi.fn(async (input: URL | RequestInfo, init?: RequestInit) => {
      expect(String(input)).toBe(
        `https://api.example.test/api/v1/tenants/${TENANT}/campaigns/${CAMPAIGN}/operations/roadmap/war-room-snapshots`,
      );
      expect(init?.method).toBe("POST");
      const headers = new Headers(init?.headers);
      expect(headers.get("idempotency-key")).toBe("war-room-1");
      expect(headers.get("if-match")).toBe('"2"');
      expect(JSON.parse(String(init?.body))).toEqual(create);
      return new Response(
        JSON.stringify({
          snapshot: demoWarRoomSnapshot.snapshot,
          audit_event_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
          outbox_event_id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        }),
        { status: 201, headers: { "content-type": "application/json" } },
      );
    });
    vi.stubGlobal("fetch", fetchMock);
    const client = new CampaignOsApiClient(config, "synthetic-token");

    const result = await client.createWarRoomSnapshot(
      TENANT,
      CAMPAIGN,
      2,
      "war-room-1",
      create,
    );
    expect(result.snapshot.authority_effect).toBe("NONE");
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
