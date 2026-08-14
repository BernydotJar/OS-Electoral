import { randomUUID } from "node:crypto";

import type {
  StrategyAssumptionRecord,
  StrategyContradictionRecord,
  StrategyEvidenceRecord,
  StrategyHypothesisRecord,
  StrategyObjectiveRecord,
  StrategyOptionRecord,
  StrategyRedTeamFindingRecord,
  StrategyWorkspaceProjection,
  StrategyWorkspaceUpdateInput,
  TeamWorkspaceProjection,
} from "@/lib/contracts";
import { deriveStrategyWorkspaceCapabilities } from "@/lib/journey-capabilities";
import {
  parseStrategySectionForm,
  type StrategySectionMutation,
  StrategyWorkspaceFormError,
} from "@/lib/strategy-workspace-form";
import {
  loadLiveCampaignContext,
  noticeForError,
  requireSameOrigin,
  UiContextError,
} from "@/lib/server-context";
import { noticeRedirect } from "@/lib/ui-response";

function stableId(recordId: string | null): string {
  return recordId ?? randomUUID();
}

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

function requireKnown(refs: readonly string[], known: ReadonlySet<string>): void {
  if (refs.some((ref) => !known.has(ref))) throw new UiContextError("conflict");
}

function updateForMutation(
  workspace: StrategyWorkspaceProjection,
  team: TeamWorkspaceProjection,
  mutation: StrategySectionMutation,
): StrategyWorkspaceUpdateInput {
  const evidenceIds = new Set((workspace.evidence ?? []).map((item) => item.id));
  const assumptionIds = new Set((workspace.assumptions ?? []).map((item) => item.id));
  const hypothesisIds = new Set((workspace.hypotheses ?? []).map((item) => item.id));
  const optionIds = new Set((workspace.options ?? []).map((item) => item.id));
  const objectiveIds = new Set((workspace.objectives ?? []).map((item) => item.id));
  const roleIds = new Set((team.roles ?? []).map((item) => item.id));
  const referenceable = new Set([
    ...evidenceIds,
    ...assumptionIds,
    ...hypothesisIds,
    ...optionIds,
    ...objectiveIds,
  ]);

  if (mutation.kind === "review_empty") {
    const current = workspace[mutation.section];
    if ((current ?? []).length > 0) throw new UiContextError("conflict");
    return mutation.section === "contradictions"
      ? { contradictions: [] }
      : { red_team_findings: [] };
  }

  if (mutation.kind === "evidence") {
    const record: StrategyEvidenceRecord = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    return {
      evidence: replaceOrAppend(workspace.evidence, mutation.recordId, record),
    };
  }

  if (mutation.kind === "assumption") {
    requireKnown(mutation.record.evidence_refs, evidenceIds);
    const record: StrategyAssumptionRecord = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    return {
      assumptions: replaceOrAppend(workspace.assumptions, mutation.recordId, record),
    };
  }

  if (mutation.kind === "hypothesis") {
    requireKnown(mutation.record.evidence_refs, evidenceIds);
    requireKnown(mutation.record.assumption_refs, assumptionIds);
    const record: StrategyHypothesisRecord = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    return {
      hypotheses: replaceOrAppend(workspace.hypotheses, mutation.recordId, record),
    };
  }

  if (mutation.kind === "option") {
    requireKnown(mutation.record.hypothesis_refs, hypothesisIds);
    requireKnown(mutation.record.evidence_refs, evidenceIds);
    const record: StrategyOptionRecord = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    return {
      options: replaceOrAppend(workspace.options, mutation.recordId, record),
    };
  }

  if (mutation.kind === "objective") {
    requireKnown(mutation.record.evidence_refs, evidenceIds);
    if (!roleIds.has(mutation.record.owner_role_id)) throw new UiContextError("conflict");
    const record: StrategyObjectiveRecord = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    return {
      objectives: replaceOrAppend(workspace.objectives, mutation.recordId, record),
    };
  }

  if (mutation.kind === "contradiction") {
    requireKnown([mutation.record.left_ref, mutation.record.right_ref], referenceable);
    requireKnown(mutation.record.evidence_refs, evidenceIds);
    if (mutation.record.left_ref === mutation.record.right_ref) {
      throw new UiContextError("conflict");
    }
    const record: StrategyContradictionRecord = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    return {
      contradictions: replaceOrAppend(workspace.contradictions, mutation.recordId, record),
    };
  }

  requireKnown(mutation.record.option_refs, optionIds);
  const record: StrategyRedTeamFindingRecord = {
    id: stableId(mutation.recordId),
    ...mutation.record,
  };
  return {
    red_team_findings: replaceOrAppend(
      workspace.red_team_findings,
      mutation.recordId,
      record,
    ),
  };
}

export async function POST(request: Request) {
  let locale: "es" | "en" = "es";
  try {
    requireSameOrigin(request);
    const parsed = parseStrategySectionForm(await request.formData());
    locale = parsed.locale;
    const context = await loadLiveCampaignContext();
    const capabilities = deriveStrategyWorkspaceCapabilities(
      context.identity.application_memberships,
      context.campaign.id,
    );
    if (!capabilities.canRead || !capabilities.canUpdate) {
      throw new UiContextError("authorization_denied");
    }
    const [current, team] = await Promise.all([
      context.api.strategyWorkspace(context.tenantId, context.campaign.id),
      context.api.teamWorkspace(context.tenantId, context.campaign.id),
    ]);
    if (
      current.workspace.tenant_id !== context.tenantId ||
      current.workspace.campaign_id !== context.campaign.id ||
      team.workspace.tenant_id !== context.tenantId ||
      team.workspace.campaign_id !== context.campaign.id
    ) {
      throw new UiContextError("dependency_failure");
    }
    if (
      current.workspace.version !== parsed.expectedVersion ||
      team.workspace.status !== "READY_FOR_HUMAN_REVIEW"
    ) {
      throw new UiContextError("conflict");
    }
    await context.api.updateStrategyWorkspace(
      context.tenantId,
      context.campaign.id,
      parsed.expectedVersion,
      parsed.idempotencyKey,
      updateForMutation(current.workspace, team.workspace, parsed.mutation),
    );
    return noticeRedirect(
      request,
      locale,
      "strategy_section_saved",
      "strategy-room",
    );
  } catch (error) {
    const notice =
      error instanceof StrategyWorkspaceFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "strategy-room");
  }
}
