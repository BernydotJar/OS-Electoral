import { describe, expect, it } from "vitest";

import type { EffectiveMembership } from "@/lib/contracts";
import {
  deriveCampaignContextCapabilities,
  deriveCandidateWorkspaceCapabilities,
  deriveGuidedIntakeCapabilities,
  deriveOperationsWorkspaceCapabilities,
  deriveStrategyWorkspaceCapabilities,
  deriveTeamWorkspaceCapabilities,
} from "@/lib/journey-capabilities";

const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";

function membership(
  action: string,
  purpose: string,
  campaignId: string | null = CAMPAIGN,
  resourceType = "guided_intake",
  resourceId = CAMPAIGN,
  workspaceId: string | null = null,
): EffectiveMembership {
  return {
    membership_id: "33333333-3333-4333-8333-333333333333",
    campaign_id: null,
    roles: ["administrator_label_only"],
    grants: [
      {
        grant_id: "44444444-4444-4444-8444-444444444444",
        campaign_id: campaignId,
        workspace_id: workspaceId,
        action,
        resource_type: resourceType,
        resource_id: resourceId,
        purpose,
        approval_receipt_id: "approval",
      },
    ],
  };
}

describe("deriveCampaignContextCapabilities", () => {
  it("requires the exact tenant collection grant and never trusts role labels", () => {
    const exact = membership(
      "create",
      "Create tenant campaign",
      null,
      "campaign_collection",
      TENANT,
    );
    expect(deriveCampaignContextCapabilities([exact], TENANT)).toEqual({
      canCreateCampaign: true,
    });

    const roleOnly = { ...exact, grants: [] };
    expect(deriveCampaignContextCapabilities([roleOnly], TENANT)).toEqual({
      canCreateCampaign: false,
    });
    expect(
      deriveCampaignContextCapabilities(
        [
          membership(
            "create",
            "Create tenant campaign",
            CAMPAIGN,
            "campaign_collection",
            TENANT,
          ),
          membership(
            "create",
            "Wrong purpose",
            null,
            "campaign_collection",
            TENANT,
          ),
          membership(
            "create",
            "Create tenant campaign",
            null,
            "campaign_collection",
            CAMPAIGN,
          ),
        ],
        TENANT,
      ),
    ).toEqual({ canCreateCampaign: false });
  });
});


describe("deriveGuidedIntakeCapabilities", () => {
  it("never converts role labels into mutation authority", () => {
    const value = { ...membership("read", "wrong"), grants: [] };
    expect(deriveGuidedIntakeCapabilities([value], CAMPAIGN)).toEqual({
      canStart: false,
      canRead: false,
      canUpdate: false,
    });
  });

  it("requires exact action, purpose and campaign scope", () => {
    const capabilities = deriveGuidedIntakeCapabilities(
      [
        membership("create", "Begin guided campaign intake"),
        membership("read", "Review guided campaign intake"),
        membership("update", "Maintain guided campaign intake"),
        membership("update", "Maintain guided campaign intake", null),
      ],
      CAMPAIGN,
    );
    expect(capabilities).toEqual({
      canStart: true,
      canRead: true,
      canUpdate: true,
    });
    expect(
      deriveGuidedIntakeCapabilities(
        [membership("update", "Maintain guided campaign intake")],
        "55555555-5555-4555-8555-555555555555",
      ).canUpdate,
    ).toBe(false);
  });
});


describe("deriveCandidateWorkspaceCapabilities", () => {
  it("requires exact candidate-workspace mutation grants", () => {
    expect(
      deriveCandidateWorkspaceCapabilities(
        [
          membership(
            "create",
            "Create candidate evidence workspace",
            CAMPAIGN,
            "candidate_workspace",
          ),
          membership(
            "read",
            "Review candidate evidence workspace",
            CAMPAIGN,
            "candidate_workspace",
          ),
          membership(
            "update",
            "Maintain candidate evidence workspace",
            CAMPAIGN,
            "candidate_workspace",
          ),
          membership(
            "approve",
            "Approve candidate evidence section",
            CAMPAIGN,
            "candidate_workspace",
          ),
        ],
        CAMPAIGN,
      ),
    ).toEqual({
      canStart: true,
      canRead: true,
      canUpdate: true,
      canApprove: true,
    });

    expect(
      deriveCandidateWorkspaceCapabilities(
        [
          membership(
            "create",
            "Create candidate evidence workspace",
            null,
            "candidate_workspace",
          ),
        ],
        CAMPAIGN,
      ).canStart,
    ).toBe(false);

    expect(
      deriveCandidateWorkspaceCapabilities(
        [
          membership(
            "approve",
            "Wrong approval purpose",
            CAMPAIGN,
            "candidate_workspace",
          ),
        ],
        CAMPAIGN,
      ).canApprove,
    ).toBe(false);
  });
});


describe("deriveTeamWorkspaceCapabilities", () => {
  it("requires exact team-workspace grants and never trusts role labels", () => {
    expect(
      deriveTeamWorkspaceCapabilities(
        [
          membership(
            "create",
            "Create campaign team workspace",
            CAMPAIGN,
            "team_workspace",
          ),
          membership(
            "read",
            "Review campaign team workspace",
            CAMPAIGN,
            "team_workspace",
          ),
          membership(
            "update",
            "Maintain campaign team workspace",
            CAMPAIGN,
            "team_workspace",
          ),
        ],
        CAMPAIGN,
      ),
    ).toEqual({ canStart: true, canRead: true, canUpdate: true });

    expect(
      deriveTeamWorkspaceCapabilities(
        [
          membership(
            "create",
            "Create campaign team workspace",
            null,
            "team_workspace",
          ),
        ],
        CAMPAIGN,
      ).canStart,
    ).toBe(false);
  });
});


describe("deriveStrategyWorkspaceCapabilities", () => {
  it("requires exact strategy grants and never trusts role labels", () => {
    expect(
      deriveStrategyWorkspaceCapabilities(
        [
          membership("create", "Create campaign strategy workspace", CAMPAIGN, "strategy_workspace"),
          membership("read", "Review campaign strategy workspace", CAMPAIGN, "strategy_workspace"),
          membership("update", "Maintain campaign strategy workspace", CAMPAIGN, "strategy_workspace"),
          membership("approve", "Approve internal campaign strategy option", CAMPAIGN, "strategy_workspace"),
        ],
        CAMPAIGN,
      ),
    ).toEqual({ canStart: true, canRead: true, canUpdate: true, canApprove: true });

    expect(
      deriveStrategyWorkspaceCapabilities(
        [membership("approve", "Wrong purpose", CAMPAIGN, "strategy_workspace")],
        CAMPAIGN,
      ).canApprove,
    ).toBe(false);
    expect(
      deriveStrategyWorkspaceCapabilities(
        [membership("create", "Create campaign strategy workspace", null, "strategy_workspace")],
        CAMPAIGN,
      ).canStart,
    ).toBe(false);
    expect(deriveStrategyWorkspaceCapabilities([], CAMPAIGN)).toEqual({
      canStart: false, canRead: false, canUpdate: false, canApprove: false,
    });
  });
});


describe("deriveOperationsWorkspaceCapabilities", () => {
  it("requires exact roadmap and snapshot grants and never trusts role labels", () => {
    expect(
      deriveOperationsWorkspaceCapabilities(
        [
          membership("create", "Create campaign operations roadmap", CAMPAIGN, "campaign_roadmap"),
          membership("read", "Review campaign operations roadmap", CAMPAIGN, "campaign_roadmap"),
          membership("update", "Maintain campaign operations roadmap", CAMPAIGN, "campaign_roadmap"),
          membership("create", "Create daily campaign war room snapshot", CAMPAIGN, "war_room_snapshot"),
          membership("read", "Review daily campaign war room snapshot", CAMPAIGN, "war_room_snapshot"),
        ],
        CAMPAIGN,
      ),
    ).toEqual({
      canStart: true,
      canRead: true,
      canUpdate: true,
      canCreateSnapshot: true,
      canReadSnapshot: true,
    });

    expect(
      deriveOperationsWorkspaceCapabilities(
        [membership("create", "Wrong purpose", CAMPAIGN, "campaign_roadmap")],
        CAMPAIGN,
      ).canStart,
    ).toBe(false);
    expect(
      deriveOperationsWorkspaceCapabilities(
        [membership("create", "Create campaign operations roadmap", null, "campaign_roadmap")],
        CAMPAIGN,
      ).canStart,
    ).toBe(false);
    expect(deriveOperationsWorkspaceCapabilities([], CAMPAIGN)).toEqual({
      canStart: false,
      canRead: false,
      canUpdate: false,
      canCreateSnapshot: false,
      canReadSnapshot: false,
    });
  });
});
