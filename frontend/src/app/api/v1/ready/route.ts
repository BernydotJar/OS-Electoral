import {
  FrontendConfigurationError,
  resolveFrontendConfig,
} from "@/lib/config";

const RESPONSE_HEADERS = {
  "cache-control": "no-store",
  "content-type": "application/json; charset=utf-8",
  "x-content-type-options": "nosniff",
} as const;

function unavailable(code: string): Response {
  return Response.json(
    { status: "unavailable", code },
    { status: 503, headers: RESPONSE_HEADERS },
  );
}

export async function GET(): Promise<Response> {
  let config;
  try {
    config = resolveFrontendConfig(process.env);
  } catch (error) {
    if (error instanceof FrontendConfigurationError) {
      return unavailable("FRONTEND_CONFIGURATION_INVALID");
    }
    throw error;
  }

  if (config.apiBaseUrl === null) return unavailable("API_NOT_CONFIGURED");

  let upstream: Response;
  try {
    upstream = await fetch(new URL("/api/v1/ready", config.apiBaseUrl), {
      cache: "no-store",
      headers: { accept: "application/json" },
      signal: AbortSignal.timeout(config.requestTimeoutMs),
    });
  } catch {
    return unavailable("API_UNAVAILABLE");
  }

  const body: unknown = await upstream.json().catch(() => null);
  if (typeof body !== "object" || body === null || Array.isArray(body)) {
    return unavailable("INVALID_UPSTREAM_RESPONSE");
  }

  return Response.json(body, {
    status: upstream.status,
    headers: RESPONSE_HEADERS,
  });
}
