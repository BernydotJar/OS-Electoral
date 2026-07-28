import {
  parseTeamWorkItemForm,
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
    const parsed = parseTeamWorkItemForm(await request.formData());
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
    const roleIds = new Set(
      (current.workspace.roles ?? []).map((role) => role.id),
    );
    if (
      parsed.workItem.assignments.some(
        (assignment) => !roleIds.has(assignment.role_id),
      )
    ) {
      throw new UiContextError("conflict");
    }
    const duplicate = (current.workspace.work_items ?? []).some(
      (item) =>
        item.name.toLocaleLowerCase() ===
          parsed.workItem.name.toLocaleLowerCase() &&
        item.assignments.some(
          (assignment) =>
            assignment.responsibility === "ACCOUNTABLE" &&
            assignment.role_id === parsed.workItem.assignments[0]?.role_id,
        ),
    );
    if (duplicate) throw new UiContextError("conflict");
    await context.api.updateTeamWorkspace(
      context.tenantId,
      context.campaign.id,
      parsed.expectedVersion,
      parsed.idempotencyKey,
      {
        work_items: [...(current.workspace.work_items ?? []), parsed.workItem],
      },
    );
    return noticeRedirect(
      request,
      locale,
      "team_work_item_saved",
      "team-operations-board",
    );
  } catch (error) {
    const notice =
      error instanceof TeamWorkspaceFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "team-operations-board");
  }
}
