import {
  parseTeamTemplateApplyForm,
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
    const parsed = parseTeamTemplateApplyForm(await request.formData());
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
    await context.api.applyTeamWorkspaceTemplate(
      context.tenantId,
      context.campaign.id,
      parsed.expectedVersion,
      parsed.idempotencyKey,
      parsed.apply,
    );
    return noticeRedirect(
      request,
      locale,
      "team_template_applied",
      "team-workspace",
    );
  } catch (error) {
    const notice =
      error instanceof TeamWorkspaceFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "team-workspace");
  }
}
