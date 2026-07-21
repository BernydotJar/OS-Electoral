import { describe, expect, it } from "vitest";

import type { EffectiveMembership } from "@/lib/contracts";
import { deriveNavigation } from "@/lib/navigation";

const CAMPAIGN_ID = "33333333-3333-4333-8333-333333333333";
const OTHER_CAMPAIGN_ID = "44444444-4444-4444-8444-444444444444";

function membership(
  resourceType: string,
  action = "read",
): EffectiveMembership {
  return {
    membership_id: "11111111-1111-4111-8111-111111111111",
    campaign_id: null,
    roles: ["admin_label_only"],
    grants: [
      {
        grant_id: "22222222-2222-4222-8222-222222222222",
        campaign_id: null,
        workspace_id: null,
        action,
        resource_type: resourceType,
        resource_id: CAMPAIGN_ID,
        purpose: "Test exact navigation projection",
        approval_receipt_id: "test-approval",
      },
    ],
  };
}

describe("deriveNavigation", () => {
  it("does not treat role labels as permission", () => {
    const navigation = deriveNavigation("es", [
      { ...membership("unrelated"), grants: [] },
    ]);
    expect(
      navigation.filter((item) => item.enabled).map((item) => item.key),
    ).toEqual(["overview"]);
  });

  it("requires the exact guided intake read purpose", () => {
    const wrongPurposeMembership = membership("guided_intake");
    const wrongPurpose = deriveNavigation(
      "es",
      [
        {
          ...wrongPurposeMembership,
          grants: wrongPurposeMembership.grants.map((grant) => ({
            ...grant,
            campaign_id: CAMPAIGN_ID,
          })),
        },
      ],
      CAMPAIGN_ID,
    );
    expect(wrongPurpose.find((item) => item.key === "intake")?.enabled).toBe(
      false,
    );

    const exactMembership = membership("guided_intake");
    const scopedMembership = {
      ...exactMembership,
      grants: exactMembership.grants.map((grant) => ({
        ...grant,
        campaign_id: CAMPAIGN_ID,
        purpose: "Review guided campaign intake",
      })),
    };
    const exact = deriveNavigation("es", [scopedMembership], CAMPAIGN_ID);
    expect(exact.find((item) => item.key === "intake")?.enabled).toBe(true);

    const crossCampaign = deriveNavigation(
      "es",
      [scopedMembership],
      OTHER_CAMPAIGN_ID,
    );
    expect(crossCampaign.find((item) => item.key === "intake")?.enabled).toBe(
      false,
    );
  });

  it("requires the exact current-campaign candidate workspace read grant", () => {
    const candidateMembership = membership("candidate_workspace");
    const scopedMembership = {
      ...candidateMembership,
      grants: candidateMembership.grants.map((grant) => ({
        ...grant,
        campaign_id: CAMPAIGN_ID,
        purpose: "Review candidate evidence workspace",
      })),
    };
    const exact = deriveNavigation("es", [scopedMembership], CAMPAIGN_ID);
    expect(exact.find((item) => item.key === "candidate")?.enabled).toBe(true);

    const crossCampaign = deriveNavigation(
      "es",
      [scopedMembership],
      OTHER_CAMPAIGN_ID,
    );
    expect(
      crossCampaign.find((item) => item.key === "candidate")?.enabled,
    ).toBe(false);

    const wrongPurpose = deriveNavigation(
      "es",
      [candidateMembership],
      CAMPAIGN_ID,
    );
    expect(wrongPurpose.find((item) => item.key === "candidate")?.enabled).toBe(
      false,
    );
  });

  it("requires the exact current-campaign team workspace read grant", () => {
    const teamMembership = membership("team_workspace");
    const exactMembership = {
      ...teamMembership,
      grants: teamMembership.grants.map((grant) => ({
        ...grant,
        campaign_id: CAMPAIGN_ID,
        purpose: "Review campaign team workspace",
      })),
    };
    const exact = deriveNavigation("es", [exactMembership], CAMPAIGN_ID);
    expect(exact.find((item) => item.key === "team")?.enabled).toBe(true);
    const crossCampaign = deriveNavigation(
      "es",
      [exactMembership],
      OTHER_CAMPAIGN_ID,
    );
    expect(crossCampaign.find((item) => item.key === "team")?.enabled).toBe(
      false,
    );
    const wrongPurpose = deriveNavigation("es", [teamMembership], CAMPAIGN_ID);
    expect(wrongPurpose.find((item) => item.key === "team")?.enabled).toBe(
      false,
    );
  });

  it("requires the exact current-campaign strategy read grant", () => {
    const strategyMembership = membership("strategy_workspace");
    const exactMembership = {
      ...strategyMembership,
      grants: strategyMembership.grants.map((grant) => ({
        ...grant,
        campaign_id: CAMPAIGN_ID,
        resource_id: CAMPAIGN_ID,
        purpose: "Review campaign strategy workspace",
      })),
    };
    const exact = deriveNavigation("es", [exactMembership], CAMPAIGN_ID);
    expect(exact.find((item) => item.key === "strategy")?.enabled).toBe(true);
    const crossCampaign = deriveNavigation(
      "es",
      [exactMembership],
      OTHER_CAMPAIGN_ID,
    );
    expect(crossCampaign.find((item) => item.key === "strategy")?.enabled).toBe(
      false,
    );
    const wrongPurpose = deriveNavigation(
      "es",
      [strategyMembership],
      CAMPAIGN_ID,
    );
    expect(wrongPurpose.find((item) => item.key === "strategy")?.enabled).toBe(
      false,
    );
  });

  it("requires the exact current-campaign roadmap read grant for War Room", () => {
    const roadmapMembership = membership("campaign_roadmap");
    const exactMembership = {
      ...roadmapMembership,
      grants: roadmapMembership.grants.map((grant) => ({
        ...grant,
        campaign_id: CAMPAIGN_ID,
        purpose: "Review campaign operations roadmap",
      })),
    };
    const exact = deriveNavigation("es", [exactMembership], CAMPAIGN_ID);
    expect(exact.find((item) => item.key === "warRoom")?.enabled).toBe(true);
    const crossCampaign = deriveNavigation(
      "es",
      [exactMembership],
      OTHER_CAMPAIGN_ID,
    );
    expect(crossCampaign.find((item) => item.key === "warRoom")?.enabled).toBe(
      false,
    );
    const wrongPurpose = deriveNavigation(
      "es",
      [roadmapMembership],
      CAMPAIGN_ID,
    );
    expect(wrongPurpose.find((item) => item.key === "warRoom")?.enabled).toBe(
      false,
    );
  });

  it("reveals only modules backed by relevant server-owned grants", () => {
    const navigation = deriveNavigation("en", [
      membership("campaign_readiness"),
      membership("campaign_collection", "create"),
    ]);
    expect(navigation.find((item) => item.key === "readiness")?.enabled).toBe(
      true,
    );
    expect(
      navigation.find((item) => item.key === "administration")?.enabled,
    ).toBe(true);
    expect(navigation.find((item) => item.key === "warRoom")?.enabled).toBe(
      false,
    );
  });
});
