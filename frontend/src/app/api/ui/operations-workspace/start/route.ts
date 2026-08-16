import {
  parseOperationsStartForm,
  OperationsWorkspaceFormError,
} from "@/lib/operations-workspace-form";
import { deriveOperationsWorkspaceCapabilities } from "@/lib/journey-capabilities";
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
    const parsed = parseOperationsStartForm(await request.formData());
    locale = parsed.locale;
    const context = await loadLiveCampaignContext();
    const capabilities = deriveOperationsWorkspaceCapabilities(
      context.identity.application_memberships,
      context.campaign.id,
    );
    if (!capabilities.canStart || !capabilities.canRead) {
      throw new UiContextError("authorization_denied");
    }
    const [strategy, team] = await Promise.all([
      context.api.strategyWorkspace(context.tenantId, context.campaign.id),
      context.api.teamWorkspace(context.tenantId, context.campaign.id),
    ]);
    if (
      strategy.workspace.tenant_id !== context.tenantId ||
      strategy.workspace.campaign_id !== context.campaign.id ||
      team.workspace.tenant_id !== context.tenantId ||
      team.workspace.campaign_id !== context.campaign.id
    ) {
      throw new UiContextError("dependency_failure");
    }
    if (
      strategy.workspace.status !== "DECIDED_INTERNAL" ||
      team.workspace.status !== "READY_FOR_HUMAN_REVIEW" ||
      !(team.workspace.roles ?? []).some((role) => role.status === "FILLED")
    ) {
      throw new UiContextError("conflict");
    }
    const created = await context.api.startCampaignRoadmap(
      context.tenantId,
      context.campaign.id,
      parsed.idempotencyKey,
      parsed.create,
    );
    if (
      created.roadmap.tenant_id !== context.tenantId ||
      created.roadmap.campaign_id !== context.campaign.id ||
      created.roadmap.version !== 1
    ) {
      throw new UiContextError("dependency_failure");
    }
    return noticeRedirect(request, locale, "operations_started", "war-room");
  } catch (error) {
    const notice =
      error instanceof OperationsWorkspaceFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "war-room");
  }
}
