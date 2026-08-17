import {
  parseTeamRoleCoverageForm,
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
    const parsed = parseTeamRoleCoverageForm(await request.formData());
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

    const roles = current.workspace.roles ?? [];
    const selected = roles.find((role) => role.id === parsed.roleId);
    if (
      selected === undefined ||
      selected.status !== "VACANT" ||
      selected.principal_id !== null ||
      selected.weekly_capacity_hours !== null
    ) {
      throw new UiContextError("conflict");
    }

    const updatedRoles = roles.map((role) =>
      role.id === selected.id
        ? {
            ...role,
            status: "FILLED" as const,
            principal_id: context.identity.principal_id,
            availability_status: parsed.availabilityStatus,
            weekly_capacity_hours: parsed.weeklyCapacityHours,
            onboarding_status: "COMPLETE" as const,
            vacancy_plan: null,
          }
        : role,
    );
    const saved = await context.api.updateTeamWorkspace(
      context.tenantId,
      context.campaign.id,
      parsed.expectedVersion,
      parsed.idempotencyKey,
      { roles: updatedRoles },
    );
    const savedRole = saved.workspace.roles?.find(
      (role) => role.id === selected.id,
    );
    if (
      saved.workspace.tenant_id !== context.tenantId ||
      saved.workspace.campaign_id !== context.campaign.id ||
      saved.workspace.version !== parsed.expectedVersion + 1 ||
      savedRole?.status !== "FILLED" ||
      savedRole.principal_id !== context.identity.principal_id ||
      savedRole.availability_status !== parsed.availabilityStatus ||
      savedRole.weekly_capacity_hours !== parsed.weeklyCapacityHours ||
      savedRole.onboarding_status !== "COMPLETE" ||
      savedRole.vacancy_plan !== null
    ) {
      throw new UiContextError("dependency_failure");
    }
    return noticeRedirect(
      request,
      locale,
      "team_role_covered",
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
