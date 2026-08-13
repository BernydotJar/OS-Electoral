import { randomUUID } from "node:crypto";

import {
  parseTeamReadinessForm,
  TeamWorkspaceFormError,
} from "@/lib/team-workspace-form";
import { deriveTeamWorkspaceCapabilities } from "@/lib/journey-capabilities";
import {
  loadLiveCampaignContext,
  noticeForError,
  requireSameOrigin,
  UiContextError,
} from "@/lib/server-context";
import { noticeRedirect } from "@/lib/ui-response";

export async function POST(request: Request) {
  let locale: "es" | "en" = "es";
  try {
    requireSameOrigin(request);
    const parsed = parseTeamReadinessForm(await request.formData(), randomUUID());
    locale = parsed.locale;
    const context = await loadLiveCampaignContext();
    const capabilities = deriveTeamWorkspaceCapabilities(
      context.identity.application_memberships,
      context.campaign.id,
    );
    if (!capabilities.canRead || !capabilities.canUpdate) {
      throw new UiContextError("authorization_denied");
    }
    const current = await context.api.teamWorkspace(
      context.tenantId,
      context.campaign.id,
    );
    if (
      current.workspace.tenant_id !== context.tenantId ||
      current.workspace.campaign_id !== context.campaign.id
    ) {
      throw new UiContextError("dependency_failure");
    }
    if (current.workspace.version !== parsed.expectedVersion) {
      throw new UiContextError("conflict");
    }

    const roleIds = new Set((current.workspace.roles ?? []).map((role) => role.id));
    if (parsed.action === "review_empty") {
      const existing = current.workspace[parsed.section];
      if (existing !== null && existing.length > 0) {
        throw new UiContextError("conflict");
      }
      await context.api.updateTeamWorkspace(
        context.tenantId,
        context.campaign.id,
        parsed.expectedVersion,
        parsed.idempotencyKey,
        { [parsed.section]: [] },
      );
    } else if (parsed.section === "training_requirements") {
      if (!roleIds.has(parsed.requirement.role_id)) {
        throw new UiContextError("conflict");
      }
      const items = [...(current.workspace.training_requirements ?? [])];
      const index = items.findIndex((item) => item.id === parsed.requirement.id);
      if (index >= 0) {
        items[index] = parsed.requirement;
      } else {
        const duplicate = items.some(
          (item) =>
            item.role_id === parsed.requirement.role_id &&
            item.title.toLocaleLowerCase() === parsed.requirement.title.toLocaleLowerCase(),
        );
        if (duplicate) throw new UiContextError("conflict");
        items.push(parsed.requirement);
      }
      await context.api.updateTeamWorkspace(
        context.tenantId,
        context.campaign.id,
        parsed.expectedVersion,
        parsed.idempotencyKey,
        { training_requirements: items },
      );
    } else {
      if (!roleIds.has(parsed.recommendation.role_id)) {
        throw new UiContextError("conflict");
      }
      const recommendation = {
        ...parsed.recommendation,
        campaign_id: context.campaign.id,
        workspace_id: null,
        resource_id: context.campaign.id,
        authority_effect: "NONE" as const,
      };
      const items = [...(current.workspace.access_recommendations ?? [])];
      const index = items.findIndex((item) => item.id === recommendation.id);
      if (index >= 0) {
        items[index] = recommendation;
      } else {
        const duplicate = items.some(
          (item) =>
            item.role_id === recommendation.role_id &&
            item.action === recommendation.action &&
            item.resource_type === recommendation.resource_type &&
            item.purpose.toLocaleLowerCase() === recommendation.purpose.toLocaleLowerCase(),
        );
        if (duplicate) throw new UiContextError("conflict");
        items.push(recommendation);
      }
      await context.api.updateTeamWorkspace(
        context.tenantId,
        context.campaign.id,
        parsed.expectedVersion,
        parsed.idempotencyKey,
        { access_recommendations: items },
      );
    }
    return noticeRedirect(
      request,
      locale,
      "team_readiness_saved",
      "team-readiness-completion",
    );
  } catch (error) {
    const notice =
      error instanceof TeamWorkspaceFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "team-readiness-completion");
  }
}
