import { describe, expect, it } from "vitest";

import { parseTeamWorkspaceReadEvidence } from "@/lib/team-contract-parser";

const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";
const DIRECTOR = "33333333-3333-4333-8333-333333333333";
const RESEARCHER = "44444444-4444-4444-8444-444444444444";

function evidence() {
  return {
    audit_event_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
    workspace: {
      id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      tenant_id: TENANT,
      campaign_id: CAMPAIGN,
      campaign_version: 4,
      campaign_status: "ACTIVE",
      campaign_name: "Synthetic campaign",
      organization_template: "LEAN_CAMPAIGN",
      roles: [
        {
          id: DIRECTOR,
          title: "Campaign direction",
          area: "Direction",
          purpose: "Coordinate accountable human decisions.",
          responsibilities: ["Coordinate priorities"],
          status: "FILLED",
          principal_id: "55555555-5555-4555-8555-555555555555",
          availability_status: "AVAILABLE",
          weekly_capacity_hours: 40,
          onboarding_status: "COMPLETE",
          vacancy_plan: null,
        },
        {
          id: RESEARCHER,
          title: "Research",
          area: "Evidence",
          purpose: "Maintain verifiable evidence.",
          responsibilities: ["Validate sources"],
          status: "FILLED",
          principal_id: "66666666-6666-4666-8666-666666666666",
          availability_status: "LIMITED",
          weekly_capacity_hours: 20,
          onboarding_status: "COMPLETE",
          vacancy_plan: null,
        },
      ],
      work_items: [
        {
          id: "77777777-7777-4777-8777-777777777777",
          name: "Initial diagnosis",
          description: "Organize evidence and decisions.",
          status: "ACTIVE",
          assignments: [
            { role_id: DIRECTOR, responsibility: "ACCOUNTABLE" },
            { role_id: RESEARCHER, responsibility: "RESPONSIBLE" },
          ],
        },
      ],
      training_requirements: [],
      access_recommendations: [
        {
          id: "88888888-8888-4888-8888-888888888888",
          role_id: RESEARCHER,
          campaign_id: CAMPAIGN,
          workspace_id: null,
          action: "read",
          resource_type: "candidate_workspace",
          resource_id: CAMPAIGN,
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
      vacant_role_count: 0,
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
      created_at: "2026-07-21T00:00:00Z",
      updated_at: "2026-07-21T00:00:00Z",
    },
  };
}

describe("team workspace parser", () => {
  it("accepts canonical RACI and no-authority evidence", () => {
    const parsed = parseTeamWorkspaceReadEvidence(evidence());
    expect(parsed.workspace.status).toBe("READY_FOR_HUMAN_REVIEW");
    expect(parsed.workspace.total_weekly_capacity_hours).toBe(60);
    expect(parsed.workspace.authority_effect).toBe("NONE");
  });

  it("rejects recommendations that attempt to create authority", () => {
    const payload = evidence();
    payload.workspace.access_recommendations[0]!.authority_effect = "GRANT";
    expect(() => parseTeamWorkspaceReadEvidence(payload)).toThrow(
      "not supported",
    );
  });

  it("rejects broken RACI and cross-campaign access recommendations", () => {
    const brokenRaci = evidence();
    brokenRaci.workspace.work_items[0]!.assignments = [
      { role_id: RESEARCHER, responsibility: "RESPONSIBLE" },
    ];
    expect(() => parseTeamWorkspaceReadEvidence(brokenRaci)).toThrow(
      "exactly one accountable",
    );

    const foreign = evidence();
    foreign.workspace.access_recommendations[0]!.campaign_id =
      "99999999-9999-4999-8999-999999999999";
    expect(() => parseTeamWorkspaceReadEvidence(foreign)).toThrow(
      "cross-campaign access recommendation",
    );
  });

  it("rejects false progress, counts, status, and missing limitations", () => {
    const falseCheck = evidence();
    falseCheck.workspace.checks[1]!.complete = false;
    expect(() => parseTeamWorkspaceReadEvidence(falseCheck)).toThrow(
      "not canonical",
    );

    const falseCount = evidence();
    falseCount.workspace.total_weekly_capacity_hours = 61;
    expect(() => parseTeamWorkspaceReadEvidence(falseCount)).toThrow(
      "capacity summary is inconsistent",
    );

    const falseStatus = evidence();
    falseStatus.workspace.status = "STRUCTURE_IN_PROGRESS";
    expect(() => parseTeamWorkspaceReadEvidence(falseStatus)).toThrow(
      "status is inconsistent",
    );

    const missingLimit = evidence();
    missingLimit.workspace.limitation_codes.pop();
    expect(() => parseTeamWorkspaceReadEvidence(missingLimit)).toThrow(
      "mandatory limitations",
    );
  });
});
