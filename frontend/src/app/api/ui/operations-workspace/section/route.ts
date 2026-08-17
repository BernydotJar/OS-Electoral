import { randomUUID } from "node:crypto";

import type {
  CampaignMilestone,
  CampaignOperationsBlocker,
  CampaignOperationsDecision,
  CampaignOperationsFollowUp,
  CampaignOperationsLearningNote,
  CampaignOperationsTask,
  CampaignOperationsWorkstream,
  CampaignPhase,
  CampaignRoadmapProjection,
  CampaignRoadmapUpdateInput,
} from "@/lib/contracts";
import { deriveOperationsWorkspaceCapabilities } from "@/lib/journey-capabilities";
import {
  OperationsWorkspaceFormError,
  parseOperationsSectionForm,
  type OperationsSectionMutation,
} from "@/lib/operations-workspace-form";
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
  roadmap: CampaignRoadmapProjection,
  mutation: OperationsSectionMutation,
  roleIds: ReadonlySet<string>,
  evidenceIds: ReadonlySet<string>,
): CampaignRoadmapUpdateInput {
  const phaseIds = new Set((roadmap.phases ?? []).map((item) => item.id));
  const workstreamIds = new Set((roadmap.workstreams ?? []).map((item) => item.id));
  const milestoneIds = new Set((roadmap.milestones ?? []).map((item) => item.id));
  const taskIds = new Set((roadmap.tasks ?? []).map((item) => item.id));

  if (mutation.kind === "phase") {
    const record: CampaignPhase = { id: stableId(mutation.recordId), ...mutation.record };
    return { phases: replaceOrAppend(roadmap.phases, mutation.recordId, record) };
  }

  if (mutation.kind === "workstream") {
    requireKnown([mutation.record.accountable_role_id], roleIds);
    const record: CampaignOperationsWorkstream = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    return {
      workstreams: replaceOrAppend(roadmap.workstreams, mutation.recordId, record),
    };
  }

  if (mutation.kind === "milestone") {
    requireKnown([mutation.record.phase_id], phaseIds);
    requireKnown([mutation.record.owner_role_id], roleIds);
    const record: CampaignMilestone = { id: stableId(mutation.recordId), ...mutation.record };
    return {
      milestones: replaceOrAppend(roadmap.milestones, mutation.recordId, record),
    };
  }

  if (mutation.kind === "task") {
    requireKnown([mutation.record.phase_id], phaseIds);
    requireKnown([mutation.record.workstream_id], workstreamIds);
    requireKnown([mutation.record.owner_role_id], roleIds);
    if (mutation.record.milestone_id !== null) {
      requireKnown([mutation.record.milestone_id], milestoneIds);
    }
    requireKnown(mutation.record.dependency_ids, taskIds);
    requireKnown(mutation.record.evidence_refs, evidenceIds);
    if (
      mutation.recordId !== null &&
      mutation.record.dependency_ids.includes(mutation.recordId)
    ) {
      throw new UiContextError("conflict");
    }
    const record: CampaignOperationsTask = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    return { tasks: replaceOrAppend(roadmap.tasks, mutation.recordId, record) };
  }

  if (mutation.kind === "blocker") {
    requireKnown([mutation.record.owner_role_id], roleIds);
    if (mutation.record.task_id !== null) requireKnown([mutation.record.task_id], taskIds);
    const record: CampaignOperationsBlocker = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    return { blockers: replaceOrAppend(roadmap.blockers, mutation.recordId, record) };
  }

  if (mutation.kind === "decision") {
    requireKnown([mutation.record.human_role_id], roleIds);
    if (mutation.record.decision !== null) {
      if (mutation.recordId === null) throw new UiContextError("conflict");
      const existing = (roadmap.decisions ?? []).find(
        (item) => item.id === mutation.recordId,
      );
      if (
        existing === undefined ||
        existing.options.length !== mutation.record.options.length ||
        !existing.options.every(
          (option, index) => mutation.record.options[index] === option,
        ) ||
        !existing.options.includes(mutation.record.decision)
      ) {
        throw new UiContextError("conflict");
      }
    }
    const record: CampaignOperationsDecision = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    return { decisions: replaceOrAppend(roadmap.decisions, mutation.recordId, record) };
  }

  if (mutation.kind === "follow_up") {
    requireKnown([mutation.record.owner_role_id], roleIds);
    const record: CampaignOperationsFollowUp = {
      id: stableId(mutation.recordId),
      ...mutation.record,
    };
    return {
      follow_up_items: replaceOrAppend(
        roadmap.follow_up_items,
        mutation.recordId,
        record,
      ),
    };
  }

  requireKnown(mutation.record.evidence_refs, evidenceIds);
  const record: CampaignOperationsLearningNote = {
    id: stableId(mutation.recordId),
    ...mutation.record,
  };
  return {
    learning_notes: replaceOrAppend(roadmap.learning_notes, mutation.recordId, record),
  };
}

export async function POST(request: Request) {
  let locale: "es" | "en" = "es";
  try {
    requireSameOrigin(request);
    const parsed = parseOperationsSectionForm(await request.formData());
    locale = parsed.locale;
    const context = await loadLiveCampaignContext();
    const capabilities = deriveOperationsWorkspaceCapabilities(
      context.identity.application_memberships,
      context.campaign.id,
    );
    if (!capabilities.canRead || !capabilities.canUpdate) {
      throw new UiContextError("authorization_denied");
    }
    const [current, team, strategy, candidate] = await Promise.all([
      context.api.campaignRoadmap(context.tenantId, context.campaign.id),
      context.api.teamWorkspace(context.tenantId, context.campaign.id),
      context.api.strategyWorkspace(context.tenantId, context.campaign.id),
      context.api.candidateWorkspace(context.tenantId, context.campaign.id),
    ]);
    for (const scoped of [current.roadmap, team.workspace, strategy.workspace, candidate.workspace]) {
      if (scoped.tenant_id !== context.tenantId || scoped.campaign_id !== context.campaign.id) {
        throw new UiContextError("dependency_failure");
      }
    }
    if (
      current.roadmap.version !== parsed.expectedVersion ||
      strategy.workspace.status !== "DECIDED_INTERNAL" ||
      team.workspace.status !== "READY_FOR_HUMAN_REVIEW"
    ) {
      throw new UiContextError("conflict");
    }
    const roleIds = new Set(
      (team.workspace.roles ?? [])
        .filter((role) => role.status === "FILLED")
        .map((role) => role.id),
    );
    if (roleIds.size === 0) throw new UiContextError("conflict");
    const evidenceIds = new Set([
      ...(candidate.workspace.evidence ?? []).map((item) => item.id),
      ...(strategy.workspace.evidence ?? []).map((item) => item.id),
    ]);
    const saved = await context.api.updateCampaignRoadmap(
      context.tenantId,
      context.campaign.id,
      parsed.expectedVersion,
      parsed.idempotencyKey,
      updateForMutation(current.roadmap, parsed.mutation, roleIds, evidenceIds),
    );
    if (
      saved.roadmap.tenant_id !== context.tenantId ||
      saved.roadmap.campaign_id !== context.campaign.id ||
      saved.roadmap.version !== parsed.expectedVersion + 1
    ) {
      throw new UiContextError("dependency_failure");
    }
    return noticeRedirect(request, locale, "operations_section_saved", "war-room");
  } catch (error) {
    const notice =
      error instanceof OperationsWorkspaceFormError
        ? "validation_error"
        : noticeForError(error);
    return noticeRedirect(request, locale, notice, "war-room");
  }
}
