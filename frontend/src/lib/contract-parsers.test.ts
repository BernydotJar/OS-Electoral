import { describe, expect, it } from "vitest";

import {
  ContractValidationError,
  parseCampaignPage,
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
});
