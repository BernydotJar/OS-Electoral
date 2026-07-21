import { afterEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

import { CampaignOsApiClient } from "@/lib/api-client";
import type { FrontendConfig } from "@/lib/config";

const config: FrontendConfig = {
  environment: "test",
  mode: "live",
  apiBaseUrl: new URL("https://api.example.test/"),
  requestTimeoutMs: 1000,
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
