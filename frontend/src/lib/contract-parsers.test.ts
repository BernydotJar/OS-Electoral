import { describe, expect, it } from "vitest";

import {
  ContractValidationError,
  parseCampaignPage,
  parseGuidedIntakeReadEvidence,
  parseMe,
  parseReadinessEvidence,
  parseTenantMe,
} from "@/lib/contract-parsers";

const TENANT_ID = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN_ID = "22222222-2222-4222-8222-222222222222";

function tenantIdentity() {
  return {
    principal_id: "33333333-3333-4333-8333-333333333333",
    tenant_id: TENANT_ID,
    subject: "operator",
    issuer: "https://identity.example.test/",
    display_name: "Operator",
    email: null,
    authenticated_at: "2026-07-21T09:00:00+00:00",
    evaluated_at: "2026-07-21T09:01:00+00:00",
    application_memberships: [
      {
        membership_id: "44444444-4444-4444-8444-444444444444",
        campaign_id: CAMPAIGN_ID,
        roles: ["operator"],
        grants: [
          {
            grant_id: "55555555-5555-4555-8555-555555555555",
            campaign_id: CAMPAIGN_ID,
            workspace_id: null,
            action: "read",
            resource_type: "campaign_readiness",
            resource_id: CAMPAIGN_ID,
            purpose: "Assess assigned campaign readiness",
            approval_receipt_id: "approval-1",
          },
        ],
      },
    ],
    authorization_status: "LOADED",
  };
}

function readinessEvidence() {
  return {
    audit_event_id: "66666666-6666-4666-8666-666666666666",
    readiness: {
      tenant_id: TENANT_ID,
      campaign_id: CAMPAIGN_ID,
      campaign_version: 2,
      campaign_status: "ACTIVE",
      readiness_scope: "OPERATIONAL_SETUP_ONLY",
      status: "READY_FOR_GUIDED_INTAKE",
      ready_for_guided_intake: true,
      completed_checks: 4,
      total_checks: 4,
      active_workspace_count: 1,
      next_action: "BEGIN_GUIDED_INTAKE",
      checks: [
        { key: "campaign_name", complete: true, reason_code: "CAMPAIGN_NAME_PRESENT" },
        { key: "jurisdiction", complete: true, reason_code: "JURISDICTION_PRESENT" },
        { key: "campaign_stage", complete: true, reason_code: "CAMPAIGN_STAGE_PRESENT" },
        { key: "active_workspace", complete: true, reason_code: "ACTIVE_WORKSPACE_PRESENT" },
      ],
      limitation_codes: [
        "NOT_A_HUMAN_APPROVAL",
        "NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT",
      ],
    },
  };
}


function guidedIntakeEvidence() {
  return {
    audit_event_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    intake: {
      id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      tenant_id: TENANT_ID,
      campaign_id: CAMPAIGN_ID,
      campaign_version: 2,
      campaign_status: "ACTIVE",
      campaign_name: "Campaign A",
      jurisdiction: "Antigua Guatemala",
      stage: "PRECAMPAIGN",
      active_workspace_count: 1,
      readiness_scope: "GUIDED_INTAKE_ONLY",
      status: "READY_FOR_RESEARCH",
      ready_for_research: true,
      office: "Alcaldía Municipal" as string | null,
      candidate_project: "Proyecto ciudadano sujeto a evidencia.",
      current_team: ["Directora de campaña"],
      current_assets: [],
      budget_status: "DOCUMENTED",
      known_unknowns: ["Requisitos de inscripción"],
      evidence_requirements: ["Identidad", "Biografía verificable"],
      completed_checks: 8,
      total_checks: 8,
      next_action: "BEGIN_RESEARCH",
      checks: [
        {
          key: "campaign_operational_setup",
          complete: true,
          reason_code: "CAMPAIGN_OPERATIONAL_SETUP_COMPLETE",
        },
        { key: "office", complete: true, reason_code: "TARGET_OFFICE_DEFINED" },
        {
          key: "candidate_project",
          complete: true,
          reason_code: "CANDIDATE_PROJECT_DESCRIBED",
        },
        { key: "current_team", complete: true, reason_code: "CURRENT_TEAM_ASSESSED" },
        {
          key: "current_assets",
          complete: true,
          reason_code: "CURRENT_ASSETS_ASSESSED",
        },
        {
          key: "budget_status",
          complete: true,
          reason_code: "BUDGET_EVIDENCE_ASSESSED",
        },
        {
          key: "known_unknowns",
          complete: true,
          reason_code: "KNOWN_UNKNOWNS_RECORDED",
        },
        {
          key: "evidence_requirements",
          complete: true,
          reason_code: "EVIDENCE_REQUIREMENTS_DEFINED",
        },
      ],
      research_first_actions: [
        "VERIFY_OFFICE_AND_JURISDICTION_EVIDENCE",
        "VALIDATE_CANDIDATE_PROJECT_EVIDENCE",
        "ASSESS_TEAM_CAPACITY_GAPS",
        "INVENTORY_ASSET_PROVENANCE",
        "DOCUMENT_BUDGET_ASSUMPTIONS",
        "RESEARCH_KNOWN_UNKNOWNS",
        "COLLECT_REQUIRED_EVIDENCE",
      ],
      limitation_codes: [
        "NOT_A_STRATEGY",
        "NOT_A_HUMAN_APPROVAL",
        "NO_CITIZEN_CONTACT_OR_PROFILING",
        "NO_EXTERNAL_EFFECTS",
      ],
      version: 2,
      created_at: "2026-07-21T09:00:00+00:00",
      updated_at: "2026-07-21T10:00:00+00:00",
    },
  };
}

describe("contract parsers", () => {
  it("accepts a complete exact tenant authorization projection", () => {
    const parsed = parseTenantMe(tenantIdentity());
    expect(parsed.tenant_id).toBe(TENANT_ID);
    expect(parsed.application_memberships[0]?.grants[0]?.campaign_id).toBe(CAMPAIGN_ID);
  });

  it("rejects unexpected fields and cross-campaign grants", () => {
    expect(() => parseTenantMe({ ...tenantIdentity(), caller_role: "admin" })).toThrow(
      ContractValidationError,
    );
    const corrupted = structuredClone(tenantIdentity());
    corrupted.application_memberships[0]!.grants[0]!.campaign_id =
      "77777777-7777-4777-8777-777777777777";
    expect(() => parseTenantMe(corrupted)).toThrow("cross-campaign grant");
  });

  it("rejects identity-only responses that smuggle membership data", () => {
    expect(() =>
      parseMe({
        principal_id: "issuer:subject",
        subject: "subject",
        issuer: "https://identity.example.test/",
        display_name: null,
        email: null,
        authenticated_at: "2026-07-21T09:00:00Z",
        application_memberships: [{ role: "admin" }],
        authorization_status: "NOT_LOADED",
      }),
    ).toThrow("must not contain memberships");
  });

  it("validates campaign pages and refuses unsupported aggregate states", () => {
    const page = parseCampaignPage(
      {
        items: [
        {
          id: CAMPAIGN_ID,
          tenant_id: TENANT_ID,
          slug: "campaign-a",
          name: "Campaign A",
          jurisdiction: "Antigua Guatemala",
          stage: "PRECAMPAIGN",
          status: "DRAFT",
          version: 1,
        },
        ],
        next_cursor: null,
      },
      TENANT_ID,
    );
    expect(page.items).toHaveLength(1);
    expect(() =>
      parseCampaignPage({
        items: [{ ...page.items[0], status: "ARCHIVED" }],
        next_cursor: null,
      }),
    ).toThrow("not supported");
    expect(() =>
      parseCampaignPage(
        {
          items: [
            {
              ...page.items[0],
              tenant_id: "77777777-7777-4777-8777-777777777777",
            },
          ],
          next_cursor: null,
        },
        TENANT_ID,
      ),
    ).toThrow("cross-tenant campaign");
  });

  it("reconciles readiness totals, order, status, and mandatory limitations", () => {
    const parsed = parseReadinessEvidence(readinessEvidence());
    expect(parsed.readiness.ready_for_guided_intake).toBe(true);

    const wrongStatus = structuredClone(readinessEvidence());
    wrongStatus.readiness.status = "NEEDS_CAMPAIGN_WORKSPACE";
    expect(() => parseReadinessEvidence(wrongStatus)).toThrow("status and boolean disagree");

    const missingLimit = structuredClone(readinessEvidence());
    missingLimit.readiness.limitation_codes = ["NOT_A_HUMAN_APPROVAL"];
    expect(() => parseReadinessEvidence(missingLimit)).toThrow("mandatory limitations");

    const wrongOrder = structuredClone(readinessEvidence());
    wrongOrder.readiness.checks.reverse();
    expect(() => parseReadinessEvidence(wrongOrder)).toThrow("not canonical");
  });


  it("validates canonical guided intake progress, research actions, and limits", () => {
    const parsed = parseGuidedIntakeReadEvidence(guidedIntakeEvidence());
    expect(parsed.intake.status).toBe("READY_FOR_RESEARCH");
    expect(parsed.intake.current_assets).toEqual([]);
    expect(parsed.intake.research_first_actions).toHaveLength(7);

    const wrongSummary = structuredClone(guidedIntakeEvidence());
    wrongSummary.intake.completed_checks = 7;
    expect(() => parseGuidedIntakeReadEvidence(wrongSummary)).toThrow(
      "summary does not match checks",
    );

    const wrongOrder = structuredClone(guidedIntakeEvidence());
    wrongOrder.intake.checks.reverse();
    expect(() => parseGuidedIntakeReadEvidence(wrongOrder)).toThrow("not canonical");

    const wrongStatus = structuredClone(guidedIntakeEvidence());
    wrongStatus.intake.status = "IN_PROGRESS";
    expect(() => parseGuidedIntakeReadEvidence(wrongStatus)).toThrow(
      "status and boolean disagree",
    );

    const wrongNextAction = structuredClone(guidedIntakeEvidence());
    wrongNextAction.intake.next_action = "DEFINE_TARGET_OFFICE";
    expect(() => parseGuidedIntakeReadEvidence(wrongNextAction)).toThrow(
      "next action is inconsistent",
    );

    const missingResearchAction = structuredClone(guidedIntakeEvidence());
    missingResearchAction.intake.research_first_actions.pop();
    expect(() => parseGuidedIntakeReadEvidence(missingResearchAction)).toThrow(
      "research actions are not canonical",
    );

    const missingLimit = structuredClone(guidedIntakeEvidence());
    missingLimit.intake.limitation_codes.pop();
    expect(() => parseGuidedIntakeReadEvidence(missingLimit)).toThrow(
      "mandatory limitations are missing",
    );
  });

  it("rejects guided intake checks contradicted by source fields", () => {
    const missingOffice = structuredClone(guidedIntakeEvidence());
    missingOffice.intake.office = null;
    expect(() => parseGuidedIntakeReadEvidence(missingOffice)).toThrow(
      "checks contradict source fields",
    );

    const unassessedBudget = structuredClone(guidedIntakeEvidence());
    unassessedBudget.intake.budget_status = "NOT_ASSESSED";
    expect(() => parseGuidedIntakeReadEvidence(unassessedBudget)).toThrow(
      "checks contradict source fields",
    );

    const emptyUnknowns = structuredClone(guidedIntakeEvidence());
    emptyUnknowns.intake.known_unknowns = [];
    expect(() => parseGuidedIntakeReadEvidence(emptyUnknowns)).toThrow(
      "checks contradict source fields",
    );

    const setupDrift = structuredClone(guidedIntakeEvidence());
    setupDrift.intake.active_workspace_count = 0;
    expect(() => parseGuidedIntakeReadEvidence(setupDrift)).toThrow(
      "checks contradict source fields",
    );
  });

  it("rejects research actions before guided intake is ready", () => {
    const inProgress = structuredClone(guidedIntakeEvidence());
    inProgress.intake.status = "IN_PROGRESS";
    inProgress.intake.ready_for_research = false;
    inProgress.intake.office = null;
    inProgress.intake.completed_checks = 7;
    inProgress.intake.next_action = "DEFINE_TARGET_OFFICE";
    inProgress.intake.checks[1] = {
      key: "office",
      complete: false,
      reason_code: "TARGET_OFFICE_MISSING",
    };
    inProgress.intake.research_first_actions = [];
    const parsed = parseGuidedIntakeReadEvidence(inProgress);
    expect(parsed.intake.status).toBe("IN_PROGRESS");

    inProgress.intake.research_first_actions = [
      "VERIFY_OFFICE_AND_JURISDICTION_EVIDENCE",
    ];
    expect(() => parseGuidedIntakeReadEvidence(inProgress)).toThrow(
      "research actions require ready intake",
    );
  });
});
