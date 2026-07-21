import "server-only";

import type {
  CampaignProjection,
  CampaignReadinessEvidence,
  EffectiveMembership,
  TenantMeResponse,
} from "@/lib/contracts";

export const DEMO_TENANT_ID = "11111111-1111-4111-8111-111111111111";
export const DEMO_CAMPAIGN_ID = "22222222-2222-4222-8222-222222222222";

export const demoMemberships: readonly EffectiveMembership[] = [
  {
    membership_id: "33333333-3333-4333-8333-333333333333",
    campaign_id: null,
    roles: ["portfolio_operator"],
    grants: [
      {
        grant_id: "44444444-4444-4444-8444-444444444444",
        campaign_id: null,
        workspace_id: null,
        action: "create",
        resource_type: "campaign_collection",
        resource_id: DEMO_TENANT_ID,
        purpose: "Create tenant campaign",
        approval_receipt_id: "synthetic-demo-approval",
      },
      {
        grant_id: "55555555-5555-4555-8555-555555555555",
        campaign_id: DEMO_CAMPAIGN_ID,
        workspace_id: null,
        action: "read",
        resource_type: "campaign",
        resource_id: DEMO_CAMPAIGN_ID,
        purpose: "Operate assigned campaign",
        approval_receipt_id: "synthetic-demo-approval",
      },
      {
        grant_id: "66666666-6666-4666-8666-666666666666",
        campaign_id: DEMO_CAMPAIGN_ID,
        workspace_id: null,
        action: "read",
        resource_type: "campaign_readiness",
        resource_id: DEMO_CAMPAIGN_ID,
        purpose: "Assess assigned campaign readiness",
        approval_receipt_id: "synthetic-demo-approval",
      },
    ],
  },
];

export const demoTenantIdentity: TenantMeResponse = {
  principal_id: "77777777-7777-4777-8777-777777777777",
  tenant_id: DEMO_TENANT_ID,
  subject: "synthetic-demo-operator",
  issuer: "https://demo.invalid/",
  display_name: "Operadora Demo",
  email: null,
  authenticated_at: "2026-07-21T00:00:00Z",
  evaluated_at: "2026-07-21T00:00:00Z",
  application_memberships: demoMemberships,
  authorization_status: "LOADED",
};

export const demoCampaign: CampaignProjection = {
  id: DEMO_CAMPAIGN_ID,
  tenant_id: DEMO_TENANT_ID,
  slug: "antigua-demo",
  name: "Campaña sintética Antigua",
  jurisdiction: "Antigua Guatemala",
  stage: "PRECAMPAIGN",
  status: "DRAFT",
  version: 1,
};

export const demoReadiness: CampaignReadinessEvidence = {
  audit_event_id: "88888888-8888-4888-8888-888888888888",
  readiness: {
    tenant_id: DEMO_TENANT_ID,
    campaign_id: DEMO_CAMPAIGN_ID,
    campaign_version: 1,
    campaign_status: "DRAFT",
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
