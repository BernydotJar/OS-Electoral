import { deriveOperationsWorkspaceCapabilities } from "@/lib/journey-capabilities";
import {
  OperationsWorkspaceFormError,
  parseWarRoomSnapshotForm,
} from "@/lib/operations-workspace-form";
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
    const parsed = parseWarRoomSnapshotForm(await request.formData());
    locale = parsed.locale;
    const context = await loadLiveCampaignContext();
    const capabilities = deriveOperationsWorkspaceCapabilities(
      context.identity.application_memberships,
      context.campaign.id,
    );
    if (
      !capabilities.canRead ||
      !capabilities.canCreateSnapshot ||
      !capabilities.canReadSnapshot
    ) {
      throw new UiContextError("authorization_denied");
    }
    const [roadmap, strategy] = await Promise.all([
      context.api.campaignRoadmap(context.tenantId, context.campaign.id),
      context.api.strategyWorkspace(context.tenantId, context.campaign.id),
    ]);
    if (
      roadmap.roadmap.tenant_id !== context.tenantId ||
      roadmap.roadmap.campaign_id !== context.campaign.id ||
      strategy.workspace.tenant_id !== context.tenantId ||
      strategy.workspace.campaign_id !== context.campaign.id
    ) {
      throw new UiContextError("dependency_failure");
    }
    if (
      roadmap.roadmap.version !== parsed.expectedVersion ||
      strategy.workspace.status !== "DECIDED_INTERNAL"
    ) {
      throw new UiContextError("conflict");
    }
    const created = await context.api.createWarRoomSnapshot(
      context.tenantId,
      context.campaign.id,
      parsed.expectedVersion,
      parsed.idempotencyKey,
      parsed.create,
    );
    if (
      created.snapshot.tenant_id !== context.tenantId ||
      created.snapshot.campaign_id !== context.campaign.id ||
      created.snapshot.roadmap_id !== roadmap.roadmap.id ||
      created.snapshot.roadmap_version !== parsed.expectedVersion
    ) {
      throw new UiContextError("dependency_failure");
    }
    return noticeRedirect(request, locale, "war_room_snapshot_created", "war-room");
  } catch (error) {
    const notice =
      error instanceof OperationsWorkspaceFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "war-room");
  }
}
