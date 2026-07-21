import "server-only";

import { cookies } from "next/headers";

import { CampaignOsApiClient, CampaignOsApiError } from "@/lib/api-client";
import { FrontendConfigurationError, resolveFrontendConfig } from "@/lib/config";
import type {
  CampaignProjection,
  CampaignReadinessEvidence,
  CandidateWorkspaceReadEvidence,
  EffectiveMembership,
  GuidedIntakeReadEvidence,
  TenantMeResponse,
} from "@/lib/contracts";
import {
  demoCampaign,
  demoCandidateWorkspace,
  demoGuidedIntake,
  demoReadiness,
  demoTenantIdentity,
} from "@/lib/demo-data";

const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;

export type GuidedIntakeAvailability =
  | "AVAILABLE"
  | "NOT_STARTED"
  | "NOT_AUTHORIZED"
  | "DEPENDENCY_UNAVAILABLE";

export type CandidateWorkspaceAvailability =
  | "AVAILABLE"
  | "NOT_STARTED"
  | "NOT_AUTHORIZED"
  | "DEPENDENCY_UNAVAILABLE";

export type ShellViewModel =
  | Readonly<{ kind: "unauthenticated" }>
  | Readonly<{ kind: "tenant_context_required"; displayName: string }>
  | Readonly<{ kind: "empty"; identity: TenantMeResponse; demo: boolean }>
  | Readonly<{
      kind: "authorized";
      demo: boolean;
      identity: TenantMeResponse;
      memberships: readonly EffectiveMembership[];
      campaign: CampaignProjection;
      campaigns: readonly CampaignProjection[];
      readiness: CampaignReadinessEvidence | null;
      readinessUnavailable: boolean;
      guidedIntake: GuidedIntakeReadEvidence | null;
      guidedIntakeAvailability: GuidedIntakeAvailability;
      candidateWorkspace: CandidateWorkspaceReadEvidence | null;
      candidateWorkspaceAvailability: CandidateWorkspaceAvailability;
    }>
  | Readonly<{
      kind: "unavailable";
      code: string;
      correlationId: string | null;
      configuration: boolean;
    }>;

function validUuid(value: string | undefined): value is string {
  return Boolean(value && UUID_PATTERN.test(value));
}

export async function loadShellViewModel(): Promise<ShellViewModel> {
  let config;
  try {
    config = resolveFrontendConfig(process.env);
  } catch (error) {
    if (error instanceof FrontendConfigurationError) {
      return {
        kind: "unavailable",
        code: "FRONTEND_CONFIGURATION",
        correlationId: null,
        configuration: true,
      };
    }
    throw error;
  }

  if (config.mode === "demo_read_only") {
    return {
      kind: "authorized",
      demo: true,
      identity: demoTenantIdentity,
      memberships: demoTenantIdentity.application_memberships,
      campaign: demoCampaign,
      campaigns: [demoCampaign],
      readiness: demoReadiness,
      readinessUnavailable: false,
      guidedIntake: demoGuidedIntake,
      guidedIntakeAvailability: "AVAILABLE",
      candidateWorkspace: demoCandidateWorkspace,
      candidateWorkspaceAvailability: "AVAILABLE",
    };
  }

  const cookieStore = await cookies();
  const token = cookieStore.get("campaignos_access_token")?.value;
  if (!token) return { kind: "unauthenticated" };

  const api = new CampaignOsApiClient(config, token);
  try {
    const identity = await api.me();
    const tenantId = cookieStore.get("campaignos_tenant_id")?.value;
    if (!validUuid(tenantId)) {
      return {
        kind: "tenant_context_required",
        displayName: identity.display_name ?? identity.subject,
      };
    }
    const [tenantIdentity, page] = await Promise.all([
      api.tenantMe(tenantId),
      api.campaigns(tenantId),
    ]);
    if (tenantIdentity.tenant_id !== tenantId) {
      return {
        kind: "unavailable",
        code: "TENANT_SCOPE_MISMATCH",
        correlationId: null,
        configuration: false,
      };
    }
    if (page.items.length === 0) {
      return { kind: "empty", identity: tenantIdentity, demo: false };
    }

    const requestedCampaign = cookieStore.get("campaignos_campaign_id")?.value;
    const campaign =
      (validUuid(requestedCampaign)
        ? page.items.find((candidate) => candidate.id === requestedCampaign)
        : undefined) ?? page.items[0];
    if (!campaign || campaign.tenant_id !== tenantId) {
      return {
        kind: "unavailable",
        code: "CAMPAIGN_SCOPE_MISMATCH",
        correlationId: null,
        configuration: false,
      };
    }

    const hasReadinessGrant = tenantIdentity.application_memberships.some((membership) =>
      membership.grants.some(
        (grant) =>
          grant.action === "read" &&
          grant.resource_type === "campaign_readiness" &&
          grant.resource_id === campaign.id &&
          grant.campaign_id === campaign.id &&
          grant.workspace_id === null &&
          grant.purpose === "Assess assigned campaign readiness",
      ),
    );
    let readiness: CampaignReadinessEvidence | null = null;
    let readinessUnavailable = false;
    if (hasReadinessGrant) {
      try {
        readiness = await api.readiness(tenantId, campaign.id);
        if (
          readiness.readiness.tenant_id !== tenantId ||
          readiness.readiness.campaign_id !== campaign.id
        ) {
          return {
            kind: "unavailable",
            code: "READINESS_SCOPE_MISMATCH",
            correlationId: null,
            configuration: false,
          };
        }
      } catch (error) {
        if (error instanceof CampaignOsApiError && error.status === 503) {
          readinessUnavailable = true;
        } else {
          throw error;
        }
      }
    }
    const hasGuidedIntakeGrant = tenantIdentity.application_memberships.some((membership) =>
      membership.grants.some(
        (grant) =>
          grant.action === "read" &&
          grant.resource_type === "guided_intake" &&
          grant.resource_id === campaign.id &&
          grant.campaign_id === campaign.id &&
          grant.workspace_id === null &&
          grant.purpose === "Review guided campaign intake",
      ),
    );
    let guidedIntake: GuidedIntakeReadEvidence | null = null;
    let guidedIntakeAvailability: GuidedIntakeAvailability = "NOT_AUTHORIZED";
    if (hasGuidedIntakeGrant) {
      try {
        guidedIntake = await api.guidedIntake(tenantId, campaign.id);
        if (
          guidedIntake.intake.tenant_id !== tenantId ||
          guidedIntake.intake.campaign_id !== campaign.id
        ) {
          return {
            kind: "unavailable",
            code: "GUIDED_INTAKE_SCOPE_MISMATCH",
            correlationId: null,
            configuration: false,
          };
        }
        guidedIntakeAvailability = "AVAILABLE";
      } catch (error) {
        if (error instanceof CampaignOsApiError && error.status === 404) {
          guidedIntakeAvailability = "NOT_STARTED";
        } else if (error instanceof CampaignOsApiError && error.status === 503) {
          guidedIntakeAvailability = "DEPENDENCY_UNAVAILABLE";
        } else {
          throw error;
        }
      }
    }

    const hasCandidateWorkspaceGrant = tenantIdentity.application_memberships.some(
      (membership) =>
        membership.grants.some(
          (grant) =>
            grant.action === "read" &&
            grant.resource_type === "candidate_workspace" &&
            grant.resource_id === campaign.id &&
            grant.campaign_id === campaign.id &&
            grant.workspace_id === null &&
            grant.purpose === "Review candidate evidence workspace",
        ),
    );
    let candidateWorkspace: CandidateWorkspaceReadEvidence | null = null;
    let candidateWorkspaceAvailability: CandidateWorkspaceAvailability = "NOT_AUTHORIZED";
    if (hasCandidateWorkspaceGrant) {
      try {
        candidateWorkspace = await api.candidateWorkspace(tenantId, campaign.id);
        if (
          candidateWorkspace.workspace.tenant_id !== tenantId ||
          candidateWorkspace.workspace.campaign_id !== campaign.id
        ) {
          return {
            kind: "unavailable",
            code: "CANDIDATE_WORKSPACE_SCOPE_MISMATCH",
            correlationId: null,
            configuration: false,
          };
        }
        candidateWorkspaceAvailability = "AVAILABLE";
      } catch (error) {
        if (error instanceof CampaignOsApiError && error.status === 404) {
          candidateWorkspaceAvailability = "NOT_STARTED";
        } else if (error instanceof CampaignOsApiError && error.status === 503) {
          candidateWorkspaceAvailability = "DEPENDENCY_UNAVAILABLE";
        } else {
          throw error;
        }
      }
    }

    return {
      kind: "authorized",
      demo: false,
      identity: tenantIdentity,
      memberships: tenantIdentity.application_memberships,
      campaign,
      campaigns: page.items,
      readiness,
      readinessUnavailable,
      guidedIntake,
      guidedIntakeAvailability,
      candidateWorkspace,
      candidateWorkspaceAvailability,
    };
  } catch (error) {
    if (error instanceof CampaignOsApiError) {
      if (error.status === 401) return { kind: "unauthenticated" };
      return {
        kind: "unavailable",
        code: error.code,
        correlationId: error.correlationId,
        configuration: false,
      };
    }
    throw error;
  }
}
