import "server-only";

import {
  CandidateContractValidationError,
  parseCandidateWorkspaceCreateEvidence,
  parseCandidateWorkspaceUpdateEvidence,
} from "@/lib/candidate-contract-parser";
import {
  OperationsContractValidationError,
  parseCampaignRoadmapReadEvidence,
  parseWarRoomSnapshotReadEvidence,
} from "@/lib/operations-contract-parser";
import {
  StrategyContractValidationError,
  parseStrategyWorkspaceReadEvidence,
} from "@/lib/strategy-contract-parser";
import type { FrontendConfig } from "@/lib/config";
import {
  parseTeamWorkspaceCreateEvidence,
  parseTeamWorkspaceReadEvidence,
  parseTeamWorkspaceTemplateApplyEvidence,
  parseTeamWorkspaceTemplatePreview,
  parseTeamWorkspaceUpdateEvidence,
  TeamContractValidationError,
} from "@/lib/team-contract-parser";
import {
  ContractValidationError,
  parseCampaignCreateEvidence,
  parseCampaignPage,
  parseCandidateWorkspaceReadEvidence,
  parseGuidedIntakeReadEvidence,
  parseGuidedIntakeStartEvidence,
  parseGuidedIntakeUpdateEvidence,
  parseMe,
  parseReadinessEvidence,
  parseTenantMe,
} from "@/lib/contract-parsers";
import type {
  CampaignCreateEvidence,
  CampaignCreateInput,
  CampaignPage,
  CampaignReadinessEvidence,
  CampaignRoadmapReadEvidence,
  CandidateWorkspaceCreateEvidence,
  CandidateWorkspaceCreateInput,
  CandidateWorkspaceReadEvidence,
  CandidateWorkspaceUpdateEvidence,
  CandidateWorkspaceUpdateInput,
  GuidedIntakeReadEvidence,
  GuidedIntakeStartEvidence,
  GuidedIntakeUpdateEvidence,
  GuidedIntakeUpdateInput,
  MeResponse,
  ProblemDetail,
  StrategyWorkspaceReadEvidence,
  TeamWorkspaceCreateEvidence,
  TeamWorkspaceCreateInput,
  TeamWorkspaceReadEvidence,
  TeamWorkspaceTemplateApplyEvidence,
  TeamWorkspaceTemplateApplyInput,
  TeamWorkspaceTemplatePreview,
  TeamWorkspaceTemplatePreviewInput,
  TeamWorkspaceUpdateEvidence,
  TeamWorkspaceUpdateInput,
  WarRoomSnapshotReadEvidence,
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

  private async request<T>(
    path: string,
    label: string,
    parse: (value: unknown) => T,
    init: Readonly<{
      method?: "GET" | "POST" | "PATCH";
      body?: unknown;
      headers?: Readonly<Record<string, string>>;
    }> = {},
  ): Promise<T> {
    const url = new URL(path, this.config.apiBaseUrl!);
    const method = init.method ?? "GET";
    const headers: Record<string, string> = {
      accept: "application/json, application/problem+json",
      authorization: `Bearer ${this.token}`,
      ...init.headers,
    };
    if (init.body !== undefined) headers["content-type"] = "application/json";
    let response: Response;
    try {
      response = await fetch(url, {
        method,
        cache: "no-store",
        headers,
        body: init.body === undefined ? undefined : JSON.stringify(init.body),
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
        error instanceof TeamContractValidationError ||
        error instanceof OperationsContractValidationError ||
        error instanceof StrategyContractValidationError
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

  private get<T>(
    path: string,
    label: string,
    parse: (value: unknown) => T,
  ): Promise<T> {
    return this.request(path, label, parse);
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

  createCampaign(
    tenantId: UUID,
    idempotencyKey: string,
    create: CampaignCreateInput,
  ): Promise<CampaignCreateEvidence> {
    return this.request<CampaignCreateEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns`,
      "Campaign create",
      (value) => parseCampaignCreateEvidence(value, tenantId),
      {
        method: "POST",
        body: create,
        headers: { "idempotency-key": idempotencyKey },
      },
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

  startGuidedIntake(
    tenantId: UUID,
    campaignId: UUID,
    idempotencyKey: string,
  ): Promise<GuidedIntakeStartEvidence> {
    return this.request<GuidedIntakeStartEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/guided-intake`,
      "Guided intake start",
      parseGuidedIntakeStartEvidence,
      { method: "POST", headers: { "idempotency-key": idempotencyKey } },
    );
  }

  updateGuidedIntake(
    tenantId: UUID,
    campaignId: UUID,
    expectedVersion: number,
    idempotencyKey: string,
    update: GuidedIntakeUpdateInput,
  ): Promise<GuidedIntakeUpdateEvidence> {
    return this.request<GuidedIntakeUpdateEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/guided-intake`,
      "Guided intake update",
      parseGuidedIntakeUpdateEvidence,
      {
        method: "PATCH",
        body: update,
        headers: {
          "idempotency-key": idempotencyKey,
          "if-match": `"${expectedVersion}"`,
        },
      },
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

  startCandidateWorkspace(
    tenantId: UUID,
    campaignId: UUID,
    idempotencyKey: string,
    create: CandidateWorkspaceCreateInput,
  ): Promise<CandidateWorkspaceCreateEvidence> {
    return this.request<CandidateWorkspaceCreateEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/candidate-workspace`,
      "Candidate workspace create",
      parseCandidateWorkspaceCreateEvidence,
      {
        method: "POST",
        body: create,
        headers: { "idempotency-key": idempotencyKey },
      },
    );
  }

  updateCandidateWorkspace(
    tenantId: UUID,
    campaignId: UUID,
    expectedVersion: number,
    idempotencyKey: string,
    update: CandidateWorkspaceUpdateInput,
  ): Promise<CandidateWorkspaceUpdateEvidence> {
    return this.request<CandidateWorkspaceUpdateEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/candidate-workspace`,
      "Candidate workspace update",
      parseCandidateWorkspaceUpdateEvidence,
      {
        method: "PATCH",
        body: update,
        headers: {
          "idempotency-key": idempotencyKey,
          "if-match": `"${expectedVersion}"`,
        },
      },
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

  startTeamWorkspace(
    tenantId: UUID,
    campaignId: UUID,
    idempotencyKey: string,
    create: TeamWorkspaceCreateInput,
  ): Promise<TeamWorkspaceCreateEvidence> {
    return this.request<TeamWorkspaceCreateEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/team-workspace`,
      "Team workspace create",
      parseTeamWorkspaceCreateEvidence,
      {
        method: "POST",
        body: create,
        headers: { "idempotency-key": idempotencyKey },
      },
    );
  }

  updateTeamWorkspace(
    tenantId: UUID,
    campaignId: UUID,
    expectedVersion: number,
    idempotencyKey: string,
    update: TeamWorkspaceUpdateInput,
  ): Promise<TeamWorkspaceUpdateEvidence> {
    return this.request<TeamWorkspaceUpdateEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/team-workspace`,
      "Team workspace update",
      parseTeamWorkspaceUpdateEvidence,
      {
        method: "PATCH",
        body: update,
        headers: {
          "idempotency-key": idempotencyKey,
          "if-match": `"${expectedVersion}"`,
        },
      },
    );
  }

  previewTeamWorkspaceTemplate(
    tenantId: UUID,
    campaignId: UUID,
    expectedVersion: number,
    preview: TeamWorkspaceTemplatePreviewInput,
  ): Promise<TeamWorkspaceTemplatePreview> {
    return this.request<TeamWorkspaceTemplatePreview>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/team-workspace/template-preview`,
      "Team workspace template preview",
      parseTeamWorkspaceTemplatePreview,
      {
        method: "POST",
        body: preview,
        headers: { "if-match": `"${expectedVersion}"` },
      },
    );
  }

  applyTeamWorkspaceTemplate(
    tenantId: UUID,
    campaignId: UUID,
    expectedVersion: number,
    idempotencyKey: string,
    apply: TeamWorkspaceTemplateApplyInput,
  ): Promise<TeamWorkspaceTemplateApplyEvidence> {
    return this.request<TeamWorkspaceTemplateApplyEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/team-workspace/template-apply`,
      "Team workspace template apply",
      parseTeamWorkspaceTemplateApplyEvidence,
      {
        method: "POST",
        body: apply,
        headers: {
          "idempotency-key": idempotencyKey,
          "if-match": `"${expectedVersion}"`,
        },
      },
    );
  }

  campaignRoadmap(
    tenantId: UUID,
    campaignId: UUID,
  ): Promise<CampaignRoadmapReadEvidence> {
    return this.get<CampaignRoadmapReadEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/operations/roadmap`,
      "Campaign roadmap",
      parseCampaignRoadmapReadEvidence,
    );
  }

  latestWarRoomSnapshot(
    tenantId: UUID,
    campaignId: UUID,
  ): Promise<WarRoomSnapshotReadEvidence> {
    return this.get<WarRoomSnapshotReadEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/operations/roadmap/war-room-snapshots/latest`,
      "Daily War Room snapshot",
      parseWarRoomSnapshotReadEvidence,
    );
  }

  strategyWorkspace(
    tenantId: UUID,
    campaignId: UUID,
  ): Promise<StrategyWorkspaceReadEvidence> {
    return this.get<StrategyWorkspaceReadEvidence>(
      `/api/v1/tenants/${tenantId}/campaigns/${campaignId}/strategy-workspace`,
      "Strategy workspace",
      parseStrategyWorkspaceReadEvidence,
    );
  }
}
