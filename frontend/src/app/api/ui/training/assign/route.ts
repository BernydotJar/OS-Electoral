import { randomUUID } from "node:crypto";

import { NextResponse } from "next/server";

import { deriveTrainingCapabilities } from "@/lib/journey-capabilities";
import {
  loadLiveCampaignContext,
  noticeForError,
  requireSameOrigin,
  UiContextError,
} from "@/lib/server-context";
import {
  parseTrainingAssignForm,
  TrainingFormError,
} from "@/lib/training-form";
import { noticeRedirect } from "@/lib/ui-response";

export async function POST(request: Request): Promise<NextResponse> {
  let locale: "es" | "en" = "es";
  try {
    requireSameOrigin(request);
    const parsed = parseTrainingAssignForm(await request.formData());
    locale = parsed.locale;
    const context = await loadLiveCampaignContext();
    const capabilities = deriveTrainingCapabilities(
      context.identity.application_memberships,
      context.campaign.id,
    );
    if (!capabilities.canManageAssignments) {
      throw new UiContextError("authorization_denied");
    }
    await context.api.createTrainingAssignment(
      context.tenantId,
      context.campaign.id,
      context.identity.principal_id,
      randomUUID(),
      {
        ...parsed.input,
        principal_id: context.identity.principal_id,
      },
    );
    return noticeRedirect(
      request,
      locale,
      "training_assigned",
      "training-academy",
    );
  } catch (error) {
    const notice =
      error instanceof TrainingFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "training-academy");
  }
}
