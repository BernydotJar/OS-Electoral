export type FrontendEnvironment = "development" | "test" | "shared" | "production";
export type FrontendMode = "live" | "demo_read_only";

export type FrontendConfig = Readonly<{
  environment: FrontendEnvironment;
  mode: FrontendMode;
  apiBaseUrl: URL | null;
  requestTimeoutMs: number;
}>;

export class FrontendConfigurationError extends Error {}

function readEnvironment(value: string | undefined, nodeEnv: string | undefined): FrontendEnvironment {
  const resolved = value?.trim() || (nodeEnv === "production" ? "shared" : "development");
  if (!["development", "test", "shared", "production"].includes(resolved)) {
    throw new FrontendConfigurationError("Unsupported CampaignOS frontend environment");
  }
  return resolved as FrontendEnvironment;
}

function readMode(value: string | undefined): FrontendMode {
  const resolved = value?.trim() || "live";
  if (resolved !== "live" && resolved !== "demo_read_only") {
    throw new FrontendConfigurationError("Unsupported CampaignOS frontend mode");
  }
  return resolved;
}

function readTimeout(value: string | undefined): number {
  const resolved = value ? Number(value) : 5000;
  if (!Number.isInteger(resolved) || resolved < 250 || resolved > 30000) {
    throw new FrontendConfigurationError("Frontend request timeout must be between 250 and 30000 ms");
  }
  return resolved;
}

function readApiBaseUrl(value: string | undefined, environment: FrontendEnvironment): URL | null {
  if (!value?.trim()) return null;
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new FrontendConfigurationError("CAMPAIGNOS_API_BASE_URL must be an absolute URL");
  }
  if (url.protocol !== "https:" && url.protocol !== "http:") {
    throw new FrontendConfigurationError("CampaignOS API URL must use HTTP or HTTPS");
  }
  const localHost = ["127.0.0.1", "localhost"].includes(url.hostname);
  if (["shared", "production"].includes(environment) && (url.protocol !== "https:" || localHost)) {
    throw new FrontendConfigurationError("Shared frontend environments require a non-local HTTPS API");
  }
  return url;
}

export function resolveFrontendConfig(
  env: Readonly<Record<string, string | undefined>>,
): FrontendConfig {
  const environment = readEnvironment(env.CAMPAIGNOS_FRONTEND_ENVIRONMENT, env.NODE_ENV);
  const mode = readMode(env.CAMPAIGNOS_FRONTEND_MODE);
  const apiBaseUrl = readApiBaseUrl(env.CAMPAIGNOS_API_BASE_URL, environment);
  if (mode === "demo_read_only" && environment !== "development" && environment !== "test") {
    throw new FrontendConfigurationError("Synthetic demo mode is forbidden outside development and test");
  }
  if (mode === "live" && apiBaseUrl === null) {
    throw new FrontendConfigurationError("Live frontend mode requires CAMPAIGNOS_API_BASE_URL");
  }
  return {
    environment,
    mode,
    apiBaseUrl,
    requestTimeoutMs: readTimeout(env.CAMPAIGNOS_API_TIMEOUT_MS),
  };
}
