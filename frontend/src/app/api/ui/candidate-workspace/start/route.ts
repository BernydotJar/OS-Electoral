import {
  CandidateWorkspaceFormError,
  parseCandidateWorkspaceStartForm,
} from "@/lib/candidate-workspace-form";
import { deriveCandidateWorkspaceCapabilities } from "@/lib/journey-capabilities";
import {
  UiContextError,
  loadLiveCampaignContext,
  noticeForError,
  requireSameOrigin,
} from "@/lib/server-context";
import { noticeRedirect } from "@/lib/ui-response";

export async function POST(request: Request) {
  let locale: "es" | "en" = "es";
  try {
    requireSameOrigin(request);
    const parsed = parseCandidateWorkspaceStartForm(await request.formData());
    locale = parsed.locale;
    const context = await loadLiveCampaignContext();
    const capabilities = deriveCandidateWorkspaceCapabilities(
      context.identity.application_memberships,
      context.campaign.id,
    );
    if (!capabilities.canStart) throw new UiContextError("authorization_denied");
    await context.api.startCandidateWorkspace(
      context.tenantId,
      context.campaign.id,
      parsed.idempotencyKey,
      parsed.create,
    );
    return noticeRedirect(request, locale, "candidate_started", "candidate-workspace");
  } catch (error) {
    const notice =
      error instanceof CandidateWorkspaceFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "candidate-workspace");
  }
}
