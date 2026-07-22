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

it("allows a complete server-only development context only in development live mode", () => {
  const config = resolveFrontendConfig({
    CAMPAIGNOS_FRONTEND_ENVIRONMENT: "development",
    CAMPAIGNOS_FRONTEND_MODE: "live",
    CAMPAIGNOS_API_BASE_URL: "http://127.0.0.1:8000",
    CAMPAIGNOS_FRONTEND_DEVELOPMENT_TOKEN: "campaignos-local-development-token",
    CAMPAIGNOS_FRONTEND_DEVELOPMENT_TENANT_ID:
      "11111111-1111-4111-8111-111111111111",
  });

  expect(config.developmentAccessToken).toBe(
    "campaignos-local-development-token",
  );
  expect(config.developmentTenantId).toBe(
    "11111111-1111-4111-8111-111111111111",
  );
});

it("rejects incomplete, shared, demo, or weak development contexts", () => {
  const base = {
    CAMPAIGNOS_FRONTEND_MODE: "live",
    CAMPAIGNOS_API_BASE_URL: "http://127.0.0.1:8000",
  };
  expect(() =>
    resolveFrontendConfig({
      ...base,
      CAMPAIGNOS_FRONTEND_ENVIRONMENT: "development",
      CAMPAIGNOS_FRONTEND_DEVELOPMENT_TOKEN:
        "campaignos-local-development-token",
    }),
  ).toThrow("configured together");
  expect(() =>
    resolveFrontendConfig({
      ...base,
      CAMPAIGNOS_FRONTEND_ENVIRONMENT: "development",
      CAMPAIGNOS_FRONTEND_DEVELOPMENT_TOKEN: "too-short",
      CAMPAIGNOS_FRONTEND_DEVELOPMENT_TENANT_ID:
        "11111111-1111-4111-8111-111111111111",
    }),
  ).toThrow("at least 24 characters");
  expect(() =>
    resolveFrontendConfig({
      CAMPAIGNOS_FRONTEND_ENVIRONMENT: "shared",
      CAMPAIGNOS_FRONTEND_MODE: "live",
      CAMPAIGNOS_API_BASE_URL: "https://api.example.test",
      CAMPAIGNOS_FRONTEND_DEVELOPMENT_TOKEN:
        "campaignos-local-development-token",
      CAMPAIGNOS_FRONTEND_DEVELOPMENT_TENANT_ID:
        "11111111-1111-4111-8111-111111111111",
    }),
  ).toThrow("development environment");
  expect(() =>
    resolveFrontendConfig({
      CAMPAIGNOS_FRONTEND_ENVIRONMENT: "test",
      CAMPAIGNOS_FRONTEND_MODE: "demo_read_only",
      CAMPAIGNOS_FRONTEND_DEVELOPMENT_TOKEN:
        "campaignos-local-development-token",
      CAMPAIGNOS_FRONTEND_DEVELOPMENT_TENANT_ID:
        "11111111-1111-4111-8111-111111111111",
    }),
  ).toThrow("live mode");
});
