import {
  parseStrategyWorkspaceStartForm,
  StrategyWorkspaceFormError,
} from "@/lib/strategy-workspace-form";
import { deriveStrategyWorkspaceCapabilities } from "@/lib/journey-capabilities";
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
    const parsed = parseStrategyWorkspaceStartForm(await request.formData());
    locale = parsed.locale;
    const context = await loadLiveCampaignContext();
    const capabilities = deriveStrategyWorkspaceCapabilities(
      context.identity.application_memberships,
      context.campaign.id,
    );
    if (!capabilities.canStart || !capabilities.canRead) {
      throw new UiContextError("authorization_denied");
    }
    const [candidate, team] = await Promise.all([
      context.api.candidateWorkspace(context.tenantId, context.campaign.id),
      context.api.teamWorkspace(context.tenantId, context.campaign.id),
    ]);
    if (
      candidate.workspace.status !== "INTERNALLY_APPROVED" ||
      team.workspace.status !== "READY_FOR_HUMAN_REVIEW"
    ) {
      throw new UiContextError("conflict");
    }
    await context.api.startStrategyWorkspace(
      context.tenantId,
      context.campaign.id,
      parsed.idempotencyKey,
      parsed.create,
    );
    return noticeRedirect(request, locale, "strategy_started", "strategy-room");
  } catch (error) {
    const notice =
      error instanceof StrategyWorkspaceFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "strategy-room");
  }
}
