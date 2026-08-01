import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

import { CampaignContextForm } from "@/components/functional-onboarding";
import type { CampaignProjection } from "@/lib/contracts";
import { dictionaryFor } from "@/lib/i18n";

const campaign: CampaignProjection = {
  id: "22222222-2222-4222-8222-222222222222",
  tenant_id: "11111111-1111-4111-8111-111111111111",
  slug: "campana-local",
  name: "Campaña local",
  jurisdiction: "Antigua Guatemala",
  stage: "PREPARATION",
  status: "DRAFT",
  version: 1,
};
const dictionary = dictionaryFor("es");

function render(canCreateCampaign: boolean, demo = false): string {
  return renderToStaticMarkup(
    createElement(CampaignContextForm, {
      locale: "es",
      dictionary,
      campaigns: [campaign],
      currentCampaignId: campaign.id,
      canCreateCampaign,
      demo,
    }),
  );
}

describe("CampaignContextForm", () => {
  it("shows governed draft creation beside the existing context selector", () => {
    const html = render(true);

    expect(html).toContain('action="/api/ui/campaign-context"');
    expect(html).toContain("Usar esta campaña");
    expect(html).toContain('class="campaign-create-disclosure"');
    expect(html).toContain("Nueva candidatura");
    expect(html).toContain('action="/api/ui/campaign-context/create"');
    expect(html).toContain("borrador interno");
    expect(html).toContain("no cambia la campaña actual");
  });

  it("offers the first governed draft when no campaigns exist", () => {
    const html = renderToStaticMarkup(
      createElement(CampaignContextForm, {
        locale: "es",
        dictionary,
        campaigns: [],
        currentCampaignId: "",
        canCreateCampaign: true,
        demo: false,
      }),
    );

    expect(html).toContain("Aún no hay candidaturas");
    expect(html).toContain("Crea el primer borrador para comenzar");
    expect(html).not.toContain('action="/api/ui/campaign-context"');
    expect(html).toContain('action="/api/ui/campaign-context/create"');
  });

  it("hides campaign creation without the exact grant or in demo mode", () => {
    expect(render(false)).not.toContain("/api/ui/campaign-context/create");
    expect(render(true, true)).not.toContain("/api/ui/campaign-context/create");
  });
});
