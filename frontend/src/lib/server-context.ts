import "server-only";

import { cookies } from "next/headers";

import { CampaignOsApiClient, CampaignOsApiError } from "@/lib/api-client";
import {
  FrontendConfigurationError,
  resolveFrontendConfig,
} from "@/lib/config";
import type {
  CampaignProjection,
  TenantMeResponse,
} from "@/lib/contracts";
import type { UiNotice } from "@/lib/ui-notices";

const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export class UiContextError extends Error {
  constructor(readonly notice: UiNotice) {
    super(notice);
  }
}

export type LiveTenantContext = Readonly<{
  api: CampaignOsApiClient;
  tenantId: string;
  identity: TenantMeResponse;
  campaigns: readonly CampaignProjection[];
}>;

export type LiveCampaignContext = LiveTenantContext &
  Readonly<{ campaign: CampaignProjection }>;

export function requireSameOrigin(request: Request): void {
  const origin = request.headers.get("origin");
  const host = request.headers.get("host");
  if (origin === null || host === null || host.includes(",")) {
    throw new UiContextError("authorization_denied");
  }
  try {
    const source = new URL(origin);
    const requestUrl = new URL(request.url);
    const forwardedProtocol = request.headers
      .get("x-forwarded-proto")
      ?.split(",", 1)[0]
      ?.trim();
    const protocol = forwardedProtocol || requestUrl.protocol.replace(":", "");
    if (source.protocol !== `${protocol}:` || source.host !== host) {
      throw new UiContextError("authorization_denied");
    }
  } catch (error) {
    if (error instanceof UiContextError) throw error;
    throw new UiContextError("authorization_denied");
  }
}

export function validLocale(value: unknown): value is "es" | "en" {
  return value === "es" || value === "en";
}

export async function loadLiveTenantContext(): Promise<LiveTenantContext> {
  let config;
  try {
    config = resolveFrontendConfig(process.env);
  } catch (error) {
    if (error instanceof FrontendConfigurationError) {
      throw new UiContextError("dependency_failure");
    }
    throw error;
  }
  if (config.mode !== "live") throw new UiContextError("authorization_denied");
  const cookieStore = await cookies();
  const token =
    cookieStore.get("campaignos_access_token")?.value ??
    config.developmentAccessToken;
  const tenantId =
    cookieStore.get("campaignos_tenant_id")?.value ??
    config.developmentTenantId;
  if (!token) throw new UiContextError("unauthenticated");
  if (!tenantId || !UUID_PATTERN.test(tenantId)) {
    throw new UiContextError("authorization_denied");
  }
  const api = new CampaignOsApiClient(config, token);
  const [identity, page] = await Promise.all([
    api.tenantMe(tenantId),
    api.campaigns(tenantId),
  ]);
  if (identity.tenant_id !== tenantId) {
    throw new UiContextError("dependency_failure");
  }
  return { api, tenantId, identity, campaigns: page.items };
}

export async function loadLiveCampaignContext(): Promise<LiveCampaignContext> {
  const context = await loadLiveTenantContext();
  const cookieStore = await cookies();
  const requested = cookieStore.get("campaignos_campaign_id")?.value;
  const campaign =
    (requested && UUID_PATTERN.test(requested)
      ? context.campaigns.find((item) => item.id === requested)
      : undefined) ?? context.campaigns[0];
  if (!campaign || campaign.tenant_id !== context.tenantId) {
    throw new UiContextError("not_found");
  }
  return { ...context, campaign };
}

export function noticeForError(error: unknown): UiNotice {
  if (error instanceof UiContextError) return error.notice;
  if (error instanceof CampaignOsApiError) {
    if (error.status === 401) return "unauthenticated";
    if (error.status === 403) return "authorization_denied";
    if (error.status === 404) return "not_found";
    if (error.status === 409 || error.status === 412) return "conflict";
    if (error.status === 400 || error.status === 422) return "validation_error";
    if (error.status === 429) return "dependency_failure";
    if (error.status >= 500) return "dependency_failure";
  }
  return "request_failed";
}
