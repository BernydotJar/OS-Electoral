import { afterEach, describe, expect, it, vi } from "vitest";

import { GET } from "@/app/api/v1/ready/route";

const liveEnvironment = {
  CAMPAIGNOS_FRONTEND_ENVIRONMENT: "development",
  CAMPAIGNOS_FRONTEND_MODE: "live",
  CAMPAIGNOS_API_BASE_URL: "http://127.0.0.1:61234",
  CAMPAIGNOS_API_TIMEOUT_MS: "1000",
} as const;

function stubLiveEnvironment(): void {
  for (const [key, value] of Object.entries(liveEnvironment)) {
    vi.stubEnv(key, value);
  }
}

afterEach(() => {
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

describe("frontend readiness proxy", () => {
  it("proxies the backend readiness response without exposing its URL", async () => {
    stubLiveEnvironment();
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: "ready" }), {
        status: 200,
        headers: { "content-type": "application/json" },
      }),
    );
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET();

    expect(response.status).toBe(200);
    expect(await response.json()).toEqual({ status: "ready" });
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(String(url)).toBe("http://127.0.0.1:61234/api/v1/ready");
    expect(init).toMatchObject({ cache: "no-store" });
  });

  it("returns a sanitized unavailable response when the backend cannot be reached", async () => {
    stubLiveEnvironment();
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("connection refused")));

    const response = await GET();

    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({
      status: "unavailable",
      code: "API_UNAVAILABLE",
    });
  });

  it("fails closed when the frontend runtime configuration is invalid", async () => {
    vi.stubEnv("CAMPAIGNOS_FRONTEND_ENVIRONMENT", "development");
    vi.stubEnv("CAMPAIGNOS_FRONTEND_MODE", "live");
    vi.stubEnv("CAMPAIGNOS_API_BASE_URL", "");
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const response = await GET();

    expect(response.status).toBe(503);
    expect(await response.json()).toEqual({
      status: "unavailable",
      code: "FRONTEND_CONFIGURATION_INVALID",
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });
});
