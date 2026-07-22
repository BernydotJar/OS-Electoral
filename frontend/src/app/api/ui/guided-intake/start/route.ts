import { deriveGuidedIntakeCapabilities } from "@/lib/journey-capabilities";
import {
  UiContextError,
  loadLiveCampaignContext,
  noticeForError,
  requireSameOrigin,
  validLocale,
} from "@/lib/server-context";
import { noticeRedirect } from "@/lib/ui-response";
import { validIdempotencyKey } from "@/lib/guided-intake-form";

export async function POST(request: Request) {
  let locale: "es" | "en" = "es";
  try {
    requireSameOrigin(request);
    const form = await request.formData();
    const localeValue = form.get("locale");
    if (!validLocale(localeValue)) throw new UiContextError("validation_error");
    locale = localeValue;
    const key = form.get("idempotency_key");
    if (!validIdempotencyKey(key)) {
      throw new UiContextError("validation_error");
    }
    const context = await loadLiveCampaignContext();
    const capabilities = deriveGuidedIntakeCapabilities(
      context.identity.application_memberships,
      context.campaign.id,
    );
    if (!capabilities.canStart) throw new UiContextError("authorization_denied");
    await context.api.startGuidedIntake(
      context.tenantId,
      context.campaign.id,
      key,
    );
    return noticeRedirect(
      request,
      locale,
      "intake_started",
      "guided-intake",
    );
  } catch (error) {
    return noticeRedirect(
      request,
      locale,
      noticeForError(error),
      "guided-intake",
    );
  }
}
