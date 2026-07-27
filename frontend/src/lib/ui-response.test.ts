import { describe, expect, it } from "vitest";

import { noticeRedirect } from "@/lib/ui-response";

describe("noticeRedirect", () => {
  it("returns workspace mutations to the canonical chapter route", () => {
    const response = noticeRedirect(
      new Request("https://campaignos.test/api/ui/team-workspace/role"),
      "es",
      "team_role_saved",
      "team-workspace",
    );

    expect(response.status).toBe(303);
    expect(response.headers.get("location")).toBe(
      "https://campaignos.test/es/campaign/team?notice=team_role_saved#team-workspace",
    );
  });

  it("keeps overview-only anchors on the locale root", () => {
    const response = noticeRedirect(
      new Request("https://campaignos.test/api/ui/campaign-context"),
      "en",
      "campaign_selected",
      "campaigns",
    );

    expect(response.headers.get("location")).toBe(
      "https://campaignos.test/en?notice=campaign_selected#campaigns",
    );
  });
});
