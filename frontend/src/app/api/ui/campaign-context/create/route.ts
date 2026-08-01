import {
  CampaignCreateFormError,
  parseCampaignCreateForm,
} from "@/lib/campaign-create-form";
import { deriveCampaignContextCapabilities } from "@/lib/journey-capabilities";
import {
  UiContextError,
  loadLiveTenantContext,
  noticeForError,
  requireSameOrigin,
} from "@/lib/server-context";
import { noticeRedirect } from "@/lib/ui-response";

export async function POST(request: Request) {
  let locale: "es" | "en" = "es";
  try {
    requireSameOrigin(request);
    const parsed = parseCampaignCreateForm(await request.formData());
    locale = parsed.locale;
    const context = await loadLiveTenantContext();
    const capabilities = deriveCampaignContextCapabilities(
      context.identity.application_memberships,
      context.tenantId,
    );
    if (!capabilities.canCreateCampaign) {
      throw new UiContextError("authorization_denied");
    }
    await context.api.createCampaign(
      context.tenantId,
      parsed.idempotencyKey,
      parsed.create,
    );
    return noticeRedirect(request, locale, "campaign_created", "campaigns");
  } catch (error) {
    const notice =
      error instanceof CampaignCreateFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "campaigns");
  }
}
