import { deriveStrategyWorkspaceCapabilities } from "@/lib/journey-capabilities";
import {
  parseStrategyDecisionForm,
  StrategyWorkspaceFormError,
} from "@/lib/strategy-workspace-form";
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
    const parsed = parseStrategyDecisionForm(await request.formData());
    locale = parsed.locale;
    const context = await loadLiveCampaignContext();
    const capabilities = deriveStrategyWorkspaceCapabilities(
      context.identity.application_memberships,
      context.campaign.id,
    );
    if (!capabilities.canRead || !capabilities.canApprove) {
      throw new UiContextError("authorization_denied");
    }
    const [current, team] = await Promise.all([
      context.api.strategyWorkspace(context.tenantId, context.campaign.id),
      context.api.teamWorkspace(context.tenantId, context.campaign.id),
    ]);
    if (
      current.workspace.version !== parsed.expectedVersion ||
      current.workspace.status !== "READY_FOR_HUMAN_DECISION" ||
      current.workspace.decision !== null ||
      team.workspace.status !== "READY_FOR_HUMAN_REVIEW"
    ) {
      throw new UiContextError("conflict");
    }
    if (
      !(current.workspace.options ?? []).some(
        (option) => option.id === parsed.decision.selected_option_id,
      ) ||
      !(team.workspace.roles ?? []).some(
        (role) => role.id === parsed.decision.human_role_id,
      )
    ) {
      throw new UiContextError("conflict");
    }
    await context.api.decideStrategyWorkspace(
      context.tenantId,
      context.campaign.id,
      parsed.expectedVersion,
      parsed.idempotencyKey,
      parsed.decision,
    );
    return noticeRedirect(request, locale, "strategy_decided", "strategy-room");
  } catch (error) {
    const notice =
      error instanceof StrategyWorkspaceFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "strategy-room");
  }
}
