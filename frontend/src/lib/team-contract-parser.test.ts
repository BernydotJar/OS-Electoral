import { describe, expect, it } from "vitest";

import {
  parseTeamWorkspaceReadEvidence,
  parseTeamWorkspaceTemplateApplyEvidence,
  parseTeamWorkspaceTemplatePreview,
} from "@/lib/team-contract-parser";

const TENANT_ID = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN_ID = "22222222-2222-4222-8222-222222222222";
const TEAM_ID = "33333333-3333-4333-8333-333333333333";
const DIRECTOR_ID = "44444444-4444-4444-8444-444444444444";
const RESEARCH_ID = "55555555-5555-4555-8555-555555555555";
const VACANCY_ID = "66666666-6666-4666-8666-666666666666";

function fixture() {
  return {
    audit_event_id: "77777777-7777-4777-8777-777777777777",
    workspace: {
      id: TEAM_ID,
      tenant_id: TENANT_ID,
      campaign_id: CAMPAIGN_ID,
      campaign_version: 4,
      campaign_status: "ACTIVE",
      campaign_name: "Campaña sintética Antigua",
      organization_template: "LEAN_CAMPAIGN",
      roles: [
        {
          id: DIRECTOR_ID,
          title: "Dirección de campaña",
          area: "Dirección",
          purpose: "Coordinar decisiones humanas y accountability.",
          responsibilities: ["Coordinar prioridades"],
          decision_scope: [],
          deliverables: [],
          collaboration_points: [],
          success_signals: [],
          status: "FILLED",
          principal_id: "88888888-8888-4888-8888-888888888888",
          availability_status: "AVAILABLE",
          weekly_capacity_hours: 40,
          onboarding_status: "COMPLETE",
          vacancy_plan: null,
        },
        {
          id: RESEARCH_ID,
          title: "Investigación",
          area: "Evidencia",
          purpose: "Mantener evidencia verificable.",
          responsibilities: ["Validar fuentes"],
          decision_scope: [],
          deliverables: [],
          collaboration_points: [],
          success_signals: [],
          status: "FILLED",
          principal_id: "99999999-9999-4999-8999-999999999999",
          availability_status: "LIMITED",
          weekly_capacity_hours: 20,
          onboarding_status: "COMPLETE",
          vacancy_plan: null,
        },
        {
          id: VACANCY_ID,
          title: "Coordinación territorial",
          area: "Organización",
          purpose: "Diseñar coordinación territorial agregada.",
          responsibilities: ["Definir estructura territorial"],
          decision_scope: [],
          deliverables: [],
          collaboration_points: [],
          success_signals: [],
          status: "VACANT",
          principal_id: null,
          availability_status: "UNASSESSED",
          weekly_capacity_hours: null,
          onboarding_status: "NOT_STARTED",
          vacancy_plan: "Reclutar y revisar antes de recomendar acceso.",
        },
      ],
      work_items: [
        {
          id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
          name: "Diagnóstico inicial",
          description: "Organizar evidencia y decisiones requeridas.",
          status: "ACTIVE",
          assignments: [
            { role_id: DIRECTOR_ID, responsibility: "ACCOUNTABLE" },
            { role_id: RESEARCH_ID, responsibility: "RESPONSIBLE" },
            { role_id: VACANCY_ID, responsibility: "INFORMED" },
          ],
        },
      ],
      training_requirements: [
        {
          id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
          role_id: RESEARCH_ID,
          title: "Evidence and provenance",
          description: "Apply evidence boundaries.",
          status: "COMPLETE",
        },
      ],
      access_recommendations: [
        {
          id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
          role_id: RESEARCH_ID,
          campaign_id: CAMPAIGN_ID,
          workspace_id: null as string | null,
          action: "read",
          resource_type: "candidate_workspace",
          resource_id: CAMPAIGN_ID,
          purpose: "Review candidate evidence workspace",
          status: "REVIEWED",
          authority_effect: "NONE",
        },
      ],
      status: "READY_FOR_HUMAN_REVIEW",
      checks: [
        {
          key: "organization_template",
          complete: true,
          reason_code: "ORGANIZATION_TEMPLATE_SELECTED",
        },
        {
          key: "role_cards",
          complete: true,
          reason_code: "ROLE_CARDS_DEFINED",
        },
        {
          key: "accountability",
          complete: true,
          reason_code: "RACI_ACCOUNTABILITY_DEFINED",
        },
        {
          key: "availability",
          complete: true,
          reason_code: "AVAILABILITY_ASSESSED",
        },
        {
          key: "vacancies",
          complete: true,
          reason_code: "VACANCIES_IDENTIFIED",
        },
        {
          key: "onboarding",
          complete: true,
          reason_code: "FILLED_ROLES_ONBOARDED",
        },
        { key: "training", complete: true, reason_code: "TRAINING_COMPLETE" },
        {
          key: "access_review",
          complete: true,
          reason_code: "ACCESS_RECOMMENDATIONS_REVIEWED",
        },
      ],
      completed_checks: 8,
      total_checks: 8,
      filled_role_count: 2,
      vacant_role_count: 1,
      total_weekly_capacity_hours: 60,
      next_action: "CONTINUE_HUMAN_GOVERNANCE",
      authority_effect: "NONE",
      external_effects: "NONE",
      limitation_codes: [
        "ROLE_LABELS_ARE_NOT_PERMISSIONS",
        "ACCESS_RECOMMENDATIONS_REQUIRE_HUMAN_AUTHORIZATION",
        "NO_VOTER_PROFILING",
        "NO_EXTERNAL_EFFECTS",
      ],
      version: 2,
      created_at: "2026-07-21T23:00:00Z",
      updated_at: "2026-07-21T23:30:00Z",
    },
  };
}

describe("team workspace parser", () => {
  it("accepts canonical accountability while authority remains absent", () => {
    const parsed = parseTeamWorkspaceReadEvidence(fixture());
    expect(parsed.workspace.status).toBe("READY_FOR_HUMAN_REVIEW");
    expect(parsed.workspace.total_weekly_capacity_hours).toBe(60);
    expect(parsed.workspace.authority_effect).toBe("NONE");
    expect(parsed.workspace.external_effects).toBe("NONE");
  });

  it("rejects unknown, duplicate, or vacant active RACI assignments", () => {
    const unknown = structuredClone(fixture());
    unknown.workspace.work_items![0]!.assignments[0]!.role_id =
      "dddddddd-dddd-4ddd-8ddd-dddddddddddd";
    expect(() => parseTeamWorkspaceReadEvidence(unknown)).toThrow(
      "unknown role reference",
    );

    const duplicate = structuredClone(fixture());
    duplicate.workspace.work_items![0]!.assignments.push(
      structuredClone(duplicate.workspace.work_items![0]!.assignments[0]!),
    );
    expect(() => parseTeamWorkspaceReadEvidence(duplicate)).toThrow(
      "duplicate RACI assignment",
    );

    const vacant = structuredClone(fixture());
    vacant.workspace.work_items![0]!.assignments[0]!.role_id = VACANCY_ID;
    expect(() => parseTeamWorkspaceReadEvidence(vacant)).toThrow(
      "active accountability requires a filled role",
    );
  });

  it("rejects ambiguous accountability and inconsistent role lifecycle", () => {
    const noAccountable = structuredClone(fixture());
    noAccountable.workspace.work_items![0]!.assignments[0]!.responsibility =
      "CONSULTED";
    expect(() => parseTeamWorkspaceReadEvidence(noAccountable)).toThrow(
      "exactly one accountable",
    );

    const filledWithoutPrincipal = structuredClone(fixture());
    filledWithoutPrincipal.workspace.roles![0]!.principal_id = null;
    expect(() =>
      parseTeamWorkspaceReadEvidence(filledWithoutPrincipal),
    ).toThrow("filled role requires a principal");

    const vacantWithCapacity = structuredClone(fixture());
    vacantWithCapacity.workspace.roles![2]!.weekly_capacity_hours = 10;
    expect(() => parseTeamWorkspaceReadEvidence(vacantWithCapacity)).toThrow(
      "vacant role cannot have capacity",
    );
  });

  it("rejects non-canonical access resource scope", () => {
    const campaignScope = structuredClone(fixture());
    campaignScope.workspace.access_recommendations![0]!.resource_id =
      "dddddddd-dddd-4ddd-8ddd-dddddddddddd";
    expect(() => parseTeamWorkspaceReadEvidence(campaignScope)).toThrow(
      "campaign-scoped resource ID",
    );

    const workspaceScope = structuredClone(fixture());
    workspaceScope.workspace.access_recommendations![0]!.workspace_id =
      "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee";
    expect(() => parseTeamWorkspaceReadEvidence(workspaceScope)).toThrow(
      "workspace-scoped resource ID",
    );
  });

  it("rejects authority promotion and summary contradictions", () => {
    const authority = structuredClone(fixture());
    authority.workspace.access_recommendations![0]!.authority_effect = "GRANT";
    expect(() => parseTeamWorkspaceReadEvidence(authority)).toThrow();

    const crossCampaign = structuredClone(fixture());
    crossCampaign.workspace.access_recommendations![0]!.campaign_id =
      "dddddddd-dddd-4ddd-8ddd-dddddddddddd";
    expect(() => parseTeamWorkspaceReadEvidence(crossCampaign)).toThrow(
      "cross-campaign access recommendation",
    );

    const wrongCapacity = structuredClone(fixture());
    wrongCapacity.workspace.total_weekly_capacity_hours = 999;
    expect(() => parseTeamWorkspaceReadEvidence(wrongCapacity)).toThrow(
      "capacity summary is inconsistent",
    );

    const wrongStatus = structuredClone(fixture());
    wrongStatus.workspace.status = "STRUCTURE_IN_PROGRESS";
    expect(() => parseTeamWorkspaceReadEvidence(wrongStatus)).toThrow(
      "status is inconsistent",
    );
  });
});

describe("team workspace template parsers", () => {
  it("accepts a bounded no-authority preview and apply receipt", () => {
    const role = {
      ...structuredClone(fixture().workspace.roles![2]!),
      id: "abababab-abab-4bab-8bab-abababababab",
      title: "Digital Strategy",
      area: "Digital",
      decision_scope: ["Prepare decisions", "Elevate approvals"],
      deliverables: ["Plan", "Register", "Checklist"],
      collaboration_points: ["Research", "Legal"],
      success_signals: ["Measured", "Traceable", "Human-gated"],
    };
    const preview = {
      audit_event_id: fixture().audit_event_id,
      workspace_id: TEAM_ID,
      tenant_id: TENANT_ID,
      campaign_id: CAMPAIGN_ID,
      workspace_version: 2,
      organization_template: "FULL_CAMPAIGN",
      blueprint_locale: "en",
      blueprint_version: "2026-07-27.1",
      additions: [role],
      skipped: [
        {
          blueprint_key: "campaign_direction",
          title: "Campaign Chief",
          area: "Campaign leadership",
          matched_role_id: DIRECTOR_ID,
          reason: "CANONICAL_BLUEPRINT_MATCH",
          decision_scope: ["Prepare priorities", "Elevate approvals"],
          deliverables: ["Agenda", "Decision register", "Blocker map"],
          collaboration_points: ["Research", "Operations"],
          success_signals: ["Owned", "Visible", "Human-gated"],
        },
      ],
      preview_digest: "a".repeat(64),
      authority_effect: "NONE",
      external_effects: "NONE",
    };

    const parsed = parseTeamWorkspaceTemplatePreview(preview);
    expect(parsed.additions[0]?.principal_id).toBeNull();
    expect(parsed.skipped[0]?.matched_role_id).toBe(DIRECTOR_ID);
    expect(parsed.additions[0]?.deliverables).toHaveLength(3);
    expect(parsed.skipped[0]?.success_signals).toHaveLength(3);
    expect(parsed.authority_effect).toBe("NONE");

    const apply = parseTeamWorkspaceTemplateApplyEvidence({
      workspace: fixture().workspace,
      audit_event_id: fixture().audit_event_id,
      outbox_event_id: "cdcdcdcd-cdcd-4dcd-8dcd-cdcdcdcdcdcd",
      preview_digest: preview.preview_digest,
      added_role_count: 1,
      skipped_role_count: 1,
    });
    expect(apply.preview_digest).toBe(preview.preview_digest);
    expect(apply.added_role_count).toBe(1);
  });

  it("rejects malformed digests, authority promotion, and unexpected fields", () => {
    const role = structuredClone(fixture().workspace.roles![2]!);
    const preview = {
      audit_event_id: fixture().audit_event_id,
      workspace_id: TEAM_ID,
      tenant_id: TENANT_ID,
      campaign_id: CAMPAIGN_ID,
      workspace_version: 2,
      organization_template: "FULL_CAMPAIGN",
      blueprint_locale: "es",
      blueprint_version: "2026-07-27.1",
      additions: [role],
      skipped: [],
      preview_digest: "bad",
      authority_effect: "NONE",
      external_effects: "NONE",
    };
    expect(() => parseTeamWorkspaceTemplatePreview(preview)).toThrow(
      "SHA-256 digest",
    );

    preview.preview_digest = "b".repeat(64);
    preview.authority_effect = "GRANT";
    expect(() => parseTeamWorkspaceTemplatePreview(preview)).toThrow();

    const unexpected = { ...preview, authority_effect: "NONE", extra: true };
    expect(() => parseTeamWorkspaceTemplatePreview(unexpected)).toThrow(
      "unexpected fields",
    );
  });
});
