import { randomUUID } from "node:crypto";

import {
  parseTeamRoleForm,
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
    const parsed = parseTeamRoleForm(await request.formData(), randomUUID());
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
    const duplicate = (current.workspace.roles ?? []).some(
      (role) =>
        role.title.toLocaleLowerCase() === parsed.role.title.toLocaleLowerCase() &&
        role.area.toLocaleLowerCase() === parsed.role.area.toLocaleLowerCase(),
    );
    if (duplicate) throw new UiContextError("conflict");
    await context.api.updateTeamWorkspace(
      context.tenantId,
      context.campaign.id,
      parsed.expectedVersion,
      parsed.idempotencyKey,
      { roles: [...(current.workspace.roles ?? []), parsed.role] },
    );
    return noticeRedirect(request, locale, "team_role_saved", "team-workspace");
  } catch (error) {
    const notice =
      error instanceof TeamWorkspaceFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "team-workspace");
  }
}
