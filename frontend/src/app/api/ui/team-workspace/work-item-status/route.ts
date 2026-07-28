import {
  parseTeamWorkItemUpdateForm,
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
    const parsed = parseTeamWorkItemUpdateForm(await request.formData());
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
    const workItems = current.workspace.work_items ?? [];
    const selected = workItems.find((item) => item.id === parsed.workItemId);
    if (!selected) throw new UiContextError("not_found");

    if (
      parsed.updates.status === "ACTIVE" ||
      parsed.updates.status === "BLOCKED" ||
      parsed.updates.status === "COMPLETE"
    ) {
      const rolesById = new Map(
        (current.workspace.roles ?? []).map((role) => [role.id, role]),
      );
      const hasVacantExecutionRole = selected.assignments.some(
        (assignment) =>
          (assignment.responsibility === "ACCOUNTABLE" ||
            assignment.responsibility === "RESPONSIBLE") &&
          rolesById.get(assignment.role_id)?.status !== "FILLED",
      );
      if (hasVacantExecutionRole) throw new UiContextError("conflict");
    }

    const updated = {
      ...selected,
      ...parsed.updates,
      last_check_in_at: new Date().toISOString(),
    };
    await context.api.updateTeamWorkspace(
      context.tenantId,
      context.campaign.id,
      parsed.expectedVersion,
      parsed.idempotencyKey,
      {
        work_items: workItems.map((item) =>
          item.id === parsed.workItemId ? updated : item,
        ),
      },
    );
    return noticeRedirect(
      request,
      locale,
      "team_work_item_updated",
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
