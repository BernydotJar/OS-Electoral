import { describe, expect, it } from "vitest";

import { FrontendConfigurationError, resolveFrontendConfig } from "@/lib/config";

describe("resolveFrontendConfig", () => {
  it("allows synthetic demo only in test or development", () => {
    expect(
      resolveFrontendConfig({
        CAMPAIGNOS_FRONTEND_ENVIRONMENT: "test",
        CAMPAIGNOS_FRONTEND_MODE: "demo_read_only",
      }).mode,
    ).toBe("demo_read_only");
    expect(() =>
      resolveFrontendConfig({
        CAMPAIGNOS_FRONTEND_ENVIRONMENT: "shared",
        CAMPAIGNOS_FRONTEND_MODE: "demo_read_only",
      }),
    ).toThrow(FrontendConfigurationError);
  });

  it("requires an API URL in live mode", () => {
    expect(() =>
      resolveFrontendConfig({
        CAMPAIGNOS_FRONTEND_ENVIRONMENT: "development",
        CAMPAIGNOS_FRONTEND_MODE: "live",
      }),
    ).toThrow("requires CAMPAIGNOS_API_BASE_URL");
  });

  it("requires non-local HTTPS in shared environments", () => {
    expect(() =>
      resolveFrontendConfig({
        CAMPAIGNOS_FRONTEND_ENVIRONMENT: "shared",
        CAMPAIGNOS_FRONTEND_MODE: "live",
        CAMPAIGNOS_API_BASE_URL: "http://127.0.0.1:8000",
      }),
    ).toThrow("non-local HTTPS");
    expect(
      resolveFrontendConfig({
        CAMPAIGNOS_FRONTEND_ENVIRONMENT: "shared",
        CAMPAIGNOS_FRONTEND_MODE: "live",
        CAMPAIGNOS_API_BASE_URL: "https://api.example.test",
      }).apiBaseUrl?.protocol,
    ).toBe("https:");
  });
});
