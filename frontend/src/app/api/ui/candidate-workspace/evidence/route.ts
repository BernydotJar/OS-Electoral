import { randomUUID } from "node:crypto";

import {
  CandidateWorkspaceFormError,
  parseCandidateEvidenceForm,
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
    const parsed = parseCandidateEvidenceForm(await request.formData(), randomUUID());
    locale = parsed.locale;
    const context = await loadLiveCampaignContext();
    const capabilities = deriveCandidateWorkspaceCapabilities(
      context.identity.application_memberships,
      context.campaign.id,
    );
    if (!capabilities.canRead || !capabilities.canUpdate) {
      throw new UiContextError("authorization_denied");
    }
    const current = await context.api.candidateWorkspace(
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
    const duplicate = current.workspace.evidence.some(
      (item) => item.source_reference === parsed.evidence.source_reference,
    );
    if (duplicate) throw new UiContextError("conflict");
    await context.api.updateCandidateWorkspace(
      context.tenantId,
      context.campaign.id,
      parsed.expectedVersion,
      parsed.idempotencyKey,
      { evidence: [...current.workspace.evidence, parsed.evidence] },
    );
    return noticeRedirect(request, locale, "candidate_evidence_saved", "candidate-workspace");
  } catch (error) {
    const notice =
      error instanceof CandidateWorkspaceFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "candidate-workspace");
  }
}
