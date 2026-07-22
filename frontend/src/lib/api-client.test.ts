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

import { demoGuidedIntake } from "@/lib/demo-data";

describe("CampaignOsApiClient guided intake mutations", () => {
  it("sends exact start headers and validates the committed evidence", async () => {
    const fetchMock = vi.fn(async (_input: URL | RequestInfo, init?: RequestInit) => {
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
    });
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
    const fetchMock = vi.fn(async (_input: URL | RequestInfo, init?: RequestInit) => {
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
    });
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
