import {
  CandidateWorkspaceFormError,
  parseCandidateApprovalForm,
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
    const parsed = parseCandidateApprovalForm(await request.formData());
    locale = parsed.locale;
    const context = await loadLiveCampaignContext();
    const capabilities = deriveCandidateWorkspaceCapabilities(
      context.identity.application_memberships,
      context.campaign.id,
    );
    if (!capabilities.canRead || !capabilities.canApprove) {
      throw new UiContextError("authorization_denied");
    }
    const current = await context.api.candidateWorkspace(
      context.tenantId,
      context.campaign.id,
    );
    if (current.workspace.version !== parsed.expectedVersion) {
      throw new UiContextError("conflict");
    }
    if (!current.workspace.approvals_required.includes(parsed.section)) {
      throw new UiContextError("conflict");
    }
    await context.api.approveCandidateWorkspaceSection(
      context.tenantId,
      context.campaign.id,
      parsed.expectedVersion,
      parsed.idempotencyKey,
      parsed.section,
      parsed.reason,
    );
    return noticeRedirect(
      request,
      locale,
      "candidate_section_approved",
      "candidate-approvals",
    );
  } catch (error) {
    const notice =
      error instanceof CandidateWorkspaceFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "candidate-approvals");
  }
}
