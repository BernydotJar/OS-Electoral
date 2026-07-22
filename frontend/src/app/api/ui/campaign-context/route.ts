import {
  UiContextError,
  loadLiveTenantContext,
  noticeForError,
  requireSameOrigin,
  validLocale,
} from "@/lib/server-context";
import { noticeRedirect } from "@/lib/ui-response";

export async function POST(request: Request) {
  let locale: "es" | "en" = "es";
  try {
    requireSameOrigin(request);
    const form = await request.formData();
    const localeValue = form.get("locale");
    if (!validLocale(localeValue)) throw new UiContextError("validation_error");
    locale = localeValue;
    const campaignId = form.get("campaign_id");
    if (typeof campaignId !== "string") {
      throw new UiContextError("validation_error");
    }
    const context = await loadLiveTenantContext();
    if (!context.campaigns.some((campaign) => campaign.id === campaignId)) {
      throw new UiContextError("authorization_denied");
    }
    const response = noticeRedirect(
      request,
      locale,
      "campaign_selected",
      "campaigns",
    );
    response.cookies.set("campaignos_campaign_id", campaignId, {
      httpOnly: true,
      sameSite: "lax",
      secure: new URL(request.url).protocol === "https:",
      path: "/",
      maxAge: 60 * 60 * 8,
    });
    return response;
  } catch (error) {
    return noticeRedirect(request, locale, noticeForError(error), "campaigns");
  }
}
