import { describe, expect, it } from "vitest";

import type { EffectiveMembership } from "@/lib/contracts";
import { deriveGuidedIntakeCapabilities } from "@/lib/journey-capabilities";

const CAMPAIGN = "22222222-2222-4222-8222-222222222222";

function membership(
  action: string,
  purpose: string,
  campaignId: string | null = CAMPAIGN,
): EffectiveMembership {
  return {
    membership_id: "33333333-3333-4333-8333-333333333333",
    campaign_id: null,
    roles: ["administrator_label_only"],
    grants: [
      {
        grant_id: "44444444-4444-4444-8444-444444444444",
        campaign_id: campaignId,
        workspace_id: null,
        action,
        resource_type: "guided_intake",
        resource_id: CAMPAIGN,
        purpose,
        approval_receipt_id: "approval",
      },
    ],
  };
}

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
