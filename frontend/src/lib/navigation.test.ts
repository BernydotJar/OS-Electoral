import { describe, expect, it } from "vitest";

import type { EffectiveMembership } from "@/lib/contracts";
import { deriveNavigation } from "@/lib/navigation";

function membership(resourceType: string, action = "read"): EffectiveMembership {
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
        resource_id: "33333333-3333-4333-8333-333333333333",
        purpose: "Test exact navigation projection",
        approval_receipt_id: "test-approval",
      },
    ],
  };
}

describe("deriveNavigation", () => {
  it("does not treat role labels as permission", () => {
    const navigation = deriveNavigation("es", [{ ...membership("unrelated"), grants: [] }]);
    expect(navigation.filter((item) => item.enabled).map((item) => item.key)).toEqual([
      "overview",
    ]);
  });

  it("reveals only modules backed by relevant server-owned grants", () => {
    const navigation = deriveNavigation("en", [
      membership("campaign_readiness"),
      membership("campaign_collection", "create"),
    ]);
    expect(navigation.find((item) => item.key === "readiness")?.enabled).toBe(true);
    expect(navigation.find((item) => item.key === "administration")?.enabled).toBe(true);
    expect(navigation.find((item) => item.key === "warRoom")?.enabled).toBe(false);
  });
});
