import { beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));
vi.mock("@/lib/server-context", () => {
  class UiContextError extends Error {
    constructor(readonly notice: string) {
      super(notice);
    }
  }
  return {
    UiContextError,
    requireSameOrigin: vi.fn(),
    loadLiveTenantContext: vi.fn(),
    noticeForError: vi.fn(() => "request_failed"),
  };
});

import { POST } from "@/app/api/ui/campaign-context/create/route";
import { loadLiveTenantContext } from "@/lib/server-context";

const TENANT = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN = "22222222-2222-4222-8222-222222222222";

function request(overrides: Readonly<Record<string, string>> = {}): Request {
  const form = new FormData();
  form.set("locale", overrides.locale ?? "es");
  form.set(
    "idempotency_key",
    overrides.idempotency_key ??
      "campaign-create:12345678-1234-4234-8234-123456789abc",
  );
  form.set("name", overrides.name ?? "Nueva candidatura");
  form.set("jurisdiction", overrides.jurisdiction ?? "Antigua Guatemala");
  return new Request("https://campaign.example.test/api/ui/campaign-context/create", {
    method: "POST",
    headers: {
      origin: "https://campaign.example.test",
      host: "campaign.example.test",
    },
    body: form,
  });
}

describe("POST /api/ui/campaign-context/create", () => {
  beforeEach(() => vi.clearAllMocks());

  it("creates one internal draft and preserves the active campaign context", async () => {
    const createCampaign = vi.fn(async () => ({
      campaign: {
        id: CAMPAIGN,
        tenant_id: TENANT,
        slug: "nueva-candidatura-123456781234",
        name: "Nueva candidatura",
        jurisdiction: "Antigua Guatemala",
        stage: "PREPARATION",
        status: "DRAFT" as const,
        version: 1,
      },
      audit_event_id: "33333333-3333-4333-8333-333333333333",
      outbox_event_id: "44444444-4444-4444-8444-444444444444",
    }));
    vi.mocked(loadLiveTenantContext).mockResolvedValue({
      tenantId: TENANT,
      campaigns: [],
      api: { createCampaign } as never,
      identity: {
        principal_id: "55555555-5555-4555-8555-555555555555",
        tenant_id: TENANT,
        subject: "operator",
        issuer: "https://identity.example.test/",
        display_name: "Operator",
        email: null,
        authenticated_at: "2026-07-31T18:00:00Z",
        evaluated_at: "2026-07-31T18:00:00Z",
        authorization_status: "LOADED",
        application_memberships: [
          {
            membership_id: "66666666-6666-4666-8666-666666666666",
            campaign_id: null,
            roles: ["portfolio_operator"],
            grants: [
              {
                grant_id: "77777777-7777-4777-8777-777777777777",
                campaign_id: null,
                workspace_id: null,
                action: "create",
                resource_type: "campaign_collection",
                resource_id: TENANT,
                purpose: "Create tenant campaign",
                approval_receipt_id: "approval-1",
              },
            ],
          },
        ],
      },
    });

    const response = await POST(request());
    const destination = new URL(response.headers.get("location")!);

    expect(response.status).toBe(303);
    expect(destination.pathname).toBe("/es");
    expect(destination.searchParams.get("notice")).toBe("campaign_created");
    expect(destination.hash).toBe("#campaigns");
    expect(response.headers.get("set-cookie")).toBeNull();
    expect(createCampaign).toHaveBeenCalledWith(
      TENANT,
      "campaign-create:12345678-1234-4234-8234-123456789abc",
      {
        slug: "nueva-candidatura-123456781234",
        name: "Nueva candidatura",
        jurisdiction: "Antigua Guatemala",
        stage: "PREPARATION",
      },
    );
  });

  it("fails closed before loading tenant context for invalid form data", async () => {
    const response = await POST(request({ name: " " }));
    const destination = new URL(response.headers.get("location")!);

    expect(destination.searchParams.get("notice")).toBe("validation_error");
    expect(loadLiveTenantContext).not.toHaveBeenCalled();
  });
});
