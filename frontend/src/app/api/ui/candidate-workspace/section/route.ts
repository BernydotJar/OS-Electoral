import { randomUUID } from "node:crypto";

import {
  CandidateWorkspaceFormError,
  parseCandidateSectionForm,
  type CandidateSectionMutation,
} from "@/lib/candidate-workspace-form";
import type {
  CandidateAttribute,
  CandidateClaim,
  CandidateContradiction,
  CandidateDevelopmentGoal,
  CandidateReputationRisk,
  CandidateWorkspaceProjection,
  CandidateWorkspaceUpdateInput,
} from "@/lib/contracts";
import { deriveCandidateWorkspaceCapabilities } from "@/lib/journey-capabilities";
import {
  UiContextError,
  loadLiveCampaignContext,
  noticeForError,
  requireSameOrigin,
} from "@/lib/server-context";
import { noticeRedirect } from "@/lib/ui-response";

function replaceOrAppend<T extends { readonly id: string }>(
  current: readonly T[] | null,
  recordId: string | null,
  record: T,
): readonly T[] {
  const items = current ?? [];
  if (recordId === null) return [...items, record];
  const index = items.findIndex((item) => item.id === recordId);
  if (index < 0) throw new UiContextError("conflict");
  return items.map((item, itemIndex) => (itemIndex === index ? record : item));
}

function stableId(recordId: string | null): string {
  return recordId ?? randomUUID();
}

function singleClaimUpdate(
  current: CandidateClaim | null,
  mutation: Extract<CandidateSectionMutation, { kind: "claim" }>,
): CandidateClaim {
  if (mutation.recordId === null && current !== null) {
    throw new UiContextError("conflict");
  }
  if (
    mutation.recordId !== null &&
    (current === null || current.id !== mutation.recordId)
  ) {
    throw new UiContextError("conflict");
  }
  return { id: stableId(mutation.recordId), ...mutation.record };
}

function updateForMutation(
  workspace: CandidateWorkspaceProjection,
  mutation: CandidateSectionMutation,
): CandidateWorkspaceUpdateInput {
  if (mutation.kind === "review_empty") {
    if (mutation.section === "contradictions") {
      if ((workspace.contradictions ?? []).length > 0) {
        throw new UiContextError("conflict");
      }
      return { contradictions: [] };
    }
    if ((workspace.reputation_risks ?? []).length > 0) {
      throw new UiContextError("conflict");
    }
    return { reputation_risks: [] };
  }
  if (mutation.kind === "claim") {
    const record: CandidateClaim = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    if (mutation.section === "identity") {
      return { identity: singleClaimUpdate(workspace.identity, mutation) };
    }
    if (mutation.section === "biography") {
      return { biography: singleClaimUpdate(workspace.biography, mutation) };
    }
    if (mutation.section === "purpose") {
      return { purpose: singleClaimUpdate(workspace.purpose, mutation) };
    }
    return {
      values: replaceOrAppend(workspace.values, mutation.recordId, record),
    };
  }
  if (mutation.kind === "attribute") {
    const record: CandidateAttribute = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    return {
      attributes: replaceOrAppend(
        workspace.attributes,
        mutation.recordId,
        record,
      ),
    };
  }
  if (mutation.kind === "contradiction") {
    const record: CandidateContradiction = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    return {
      contradictions: replaceOrAppend(
        workspace.contradictions,
        mutation.recordId,
        record,
      ),
    };
  }
  if (mutation.kind === "development_goal") {
    const record: CandidateDevelopmentGoal = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    return {
      development_goals: replaceOrAppend(
        workspace.development_goals,
        mutation.recordId,
        record,
      ),
    };
  }
  const record: CandidateReputationRisk = {
    id: stableId(mutation.recordId),
    ...mutation.record,
  };
  return {
    reputation_risks: replaceOrAppend(
      workspace.reputation_risks,
      mutation.recordId,
      record,
    ),
  };
}

export async function POST(request: Request) {
  let locale: "es" | "en" = "es";
  try {
    requireSameOrigin(request);
    const parsed = parseCandidateSectionForm(await request.formData());
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
    await context.api.updateCandidateWorkspace(
      context.tenantId,
      context.campaign.id,
      parsed.expectedVersion,
      parsed.idempotencyKey,
      updateForMutation(current.workspace, parsed.mutation),
    );
    return noticeRedirect(
      request,
      locale,
      "candidate_section_saved",
      `candidate-edit-${parsed.mutation.section}`,
    );
  } catch (error) {
    const notice =
      error instanceof CandidateWorkspaceFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "candidate-completion");
  }
}
