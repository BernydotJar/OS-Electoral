import {
  GuidedIntakeFormError,
  parseGuidedIntakeForm,
} from "@/lib/guided-intake-form";
import { deriveGuidedIntakeCapabilities } from "@/lib/journey-capabilities";
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
    const parsed = parseGuidedIntakeForm(await request.formData());
    locale = parsed.locale;
    const context = await loadLiveCampaignContext();
    const capabilities = deriveGuidedIntakeCapabilities(
      context.identity.application_memberships,
      context.campaign.id,
    );
    if (!capabilities.canUpdate) {
      throw new UiContextError("authorization_denied");
    }
    await context.api.updateGuidedIntake(
      context.tenantId,
      context.campaign.id,
      parsed.expectedVersion,
      parsed.idempotencyKey,
      parsed.update,
    );
    return noticeRedirect(request, locale, "intake_saved", "guided-intake");
  } catch (error) {
    const notice =
      error instanceof GuidedIntakeFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "guided-intake");
  }
}
