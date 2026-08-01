import { describe, expect, it } from "vitest";

import {
  CampaignCreateFormError,
  parseCampaignCreateForm,
} from "@/lib/campaign-create-form";

const KEY = "campaign-create:a1b2c3d4-1234-4234-8234-123456789abc";

function campaignForm(
  overrides: Readonly<Record<string, string>> = {},
): FormData {
  const form = new FormData();
  form.set("locale", overrides.locale ?? "es");
  form.set("idempotency_key", overrides.idempotency_key ?? KEY);
  form.set("name", overrides.name ?? "  Candidatura   Municipal Ágil  ");
  form.set("jurisdiction", overrides.jurisdiction ?? "  Antigua   Guatemala  ");
  return form;
}

describe("parseCampaignCreateForm", () => {
  it("normalizes text and derives a stable slug from the submitted operation", () => {
    expect(parseCampaignCreateForm(campaignForm())).toEqual({
      locale: "es",
      idempotencyKey: KEY,
      create: {
        slug: "candidatura-municipal-agil-a1b2c3d41234",
        name: "Candidatura Municipal Ágil",
        jurisdiction: "Antigua Guatemala",
        stage: "PREPARATION",
      },
    });
  });

  it("uses a safe fallback slug when the name has no Latin letters", () => {
    const parsed = parseCampaignCreateForm(
      campaignForm({
        name: "選挙",
        idempotency_key:
          "campaign-create:deadbeef-1234-4234-8234-123456789abc",
      }),
    );

    expect(parsed.create.slug).toBe("campaign-deadbeef1234");
    expect(parsed.create.name).toBe("選挙");
  });

  it.each([
    campaignForm({ locale: "fr" }),
    campaignForm({ name: " " }),
    campaignForm({ jurisdiction: " " }),
    campaignForm({ idempotency_key: "not-safe" }),
  ])("rejects malformed or incomplete input", (form) => {
    expect(() => parseCampaignCreateForm(form)).toThrow(
      CampaignCreateFormError,
    );
  });

  it("rejects values beyond the backend contract", () => {
    expect(() =>
      parseCampaignCreateForm(campaignForm({ name: "x".repeat(256) })),
    ).toThrow(CampaignCreateFormError);
  });
});
