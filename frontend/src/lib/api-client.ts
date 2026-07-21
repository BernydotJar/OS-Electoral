import "server-only";

import { CandidateContractValidationError } from "@/lib/candidate-contract-parser";
import type { FrontendConfig } from "@/lib/config";
import {
  parseTeamWorkspaceReadEvidence,
  TeamContractValidationError,
} from "@/lib/team-contract-parser";
import {
  ContractValidationError,
  parseCampaignPage,
  parseCandidateWorkspaceReadEvidence,
  parseGuidedIntakeReadEvidence,
  parseMe,
  parseReadinessEvidence,
  parseTenantMe,
} from "@/lib/contract-parsers";
import type {
  CampaignPage,
  CampaignReadinessEvidence,
  CandidateWorkspaceReadEvidence,
  GuidedIntakeReadEvidence,
  MeResponse,
  ProblemDetail,
  TeamWorkspaceReadEvidence,
  TenantMeResponse,
  UUID,
} from "@/lib/contracts";

export class CampaignOsApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code: string,
    readonly correlationId: string | null,
  ) {
    super(message);
  }
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function parseProblem(value: unknown): ProblemDetail | null {
  if (!isObject(value)) return null;
  if (
    typeof value.status !== "number" ||
    typeof value.code !== "string" ||
    typeof value.detail !== "string" ||
    typeof value.correlation_id !== "string"
  ) {
    return null;
  }
  return value as ProblemDetail;
}

export class CampaignOsApiClient {
  constructor(
    private readonly config: FrontendConfig,
    private readonly token: string,
  ) {
    if (config.apiBaseUrl === null) {
      throw new CampaignOsApiError(
        "CampaignOS API is not configured",
        503,
        "API_UNAVAILABLE",
        null,
      );
    }
  }

  private async get<T>(
    path: string,
    label: string,
    parse: (value: unknown) => T,
  ): Promise<T> {
    const url = new URL(path, this.config.apiBaseUrl!);
    let response: Response;
    try {
      response = await fetch(url, {
        method: "GET",
        cache: "no-store",
        headers: {
          accept: "application/json, application/problem+json",
          authorization: `Bearer ${this.token}`,
        },
        signal: AbortSignal.timeout(this.config.requestTimeoutMs),
      });
    } catch {
      throw new CampaignOsApiError(
        "CampaignOS API is unavailable",
        503,
        "API_UNAVAILABLE",
        null,
      );
    }
    const body: unknown = await response.json().catch(() => null);
    if (!response.ok) {
      const problem = parseProblem(body);
      throw new CampaignOsApiError(
        problem?.detail ?? "CampaignOS request failed",
        response.status,
        problem?.code ?? "UPSTREAM_ERROR",
        problem?.correlation_id ?? response.headers.get("x-correlation-id"),
      );
    }
    try {
      return parse(body);
    } catch (error) {
      if (
        error instanceof ContractValidationError ||
        error instanceof CandidateContractValidationError ||
        error instanceof TeamContractValidationError
      ) {
        throw new CampaignOsApiError(
          `${label} response is invalid`,
          502,
          "INVALID_UPSTREAM_RESPONSE",
          response.headers.get("x-correlation-id"),
        );
      }
      throw error;
    }
  }

  me(): Promise<MeResponse> {
    return this.get<MeResponse>("/api/v1/me", "Identity", parseMe);
  }

  tenantMe(tenantId: UUID): Promise<TenantMeResponse> {
    return this.get<TenantMeResponse>(
      `/api/v1/tenants/${tenantId}/me`,
      "Tenant identity",
      parseTenantMe,
    );
  }

  campaigns(tenantId: UUID): Promise<CampaignPage> {
    return this.get<CampaignPage>(
      `/api/v1/tenants/${tenantId}/campaigns?limit=100`,
      "Campaign list",
      (value) => parseCampaignPage(value, tenantId),
    );
  }

  readiness(
    tenantId: UUID,
    campaignId: UUID,
  ): Promise<CampaignReadinessEvidence> {
    return this.get<CampaignReadinessEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/readiness`,
      "Campaign readiness",
      parseReadinessEvidence,
    );
  }

  guidedIntake(
    tenantId: UUID,
    campaignId: UUID,
  ): Promise<GuidedIntakeReadEvidence> {
    return this.get<GuidedIntakeReadEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/guided-intake`,
      "Guided intake",
      parseGuidedIntakeReadEvidence,
    );
  }

  candidateWorkspace(
    tenantId: UUID,
    campaignId: UUID,
  ): Promise<CandidateWorkspaceReadEvidence> {
    return this.get<CandidateWorkspaceReadEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/candidate-workspace`,
      "Candidate workspace",
      parseCandidateWorkspaceReadEvidence,
    );
  }

  teamWorkspace(
    tenantId: UUID,
    campaignId: UUID,
  ): Promise<TeamWorkspaceReadEvidence> {
    return this.get<TeamWorkspaceReadEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/team-workspace`,
      "Team workspace",
      parseTeamWorkspaceReadEvidence,
    );
  }
}
