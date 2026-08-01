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
  parseTrainingAttemptForm,
  TrainingFormError,
} from "@/lib/training-form";
import { noticeRedirect } from "@/lib/ui-response";

export async function POST(request: Request): Promise<NextResponse> {
  let locale: "es" | "en" = "es";
  try {
    requireSameOrigin(request);
    const parsed = parseTrainingAttemptForm(await request.formData());
    locale = parsed.locale;
    const context = await loadLiveCampaignContext();
    const capabilities = deriveTrainingCapabilities(
      context.identity.application_memberships,
      context.campaign.id,
    );
    if (!capabilities.canCompleteSelf) {
      throw new UiContextError("authorization_denied");
    }
    const evidence = await context.api.submitTrainingAttempt(
      context.tenantId,
      context.campaign.id,
      parsed.assignmentId,
      parsed.moduleId,
      context.identity.principal_id,
      randomUUID(),
      parsed.input,
    );
    return noticeRedirect(
      request,
      locale,
      evidence.outcome.result === "PASS" ? "training_passed" : "training_retry",
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
