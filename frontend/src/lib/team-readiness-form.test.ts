import { describe, expect, it } from "vitest";

import {
  parseTeamReadinessForm,
  TeamWorkspaceFormError,
} from "@/lib/team-workspace-form";

const RECORD = "11111111-1111-4111-8111-111111111111";
const ROLE = "22222222-2222-4222-8222-222222222222";

function base(section: string, action = "save") {
  const form = new FormData();
  form.set("locale", "es");
  form.set("version", "4");
  form.set("idempotency_key", "team-readiness:12345678-1234-4234-8234-123456789abc");
  form.set("section", section);
  form.set("readiness_action", action);
  form.set("record_id", "");
  return form;
}

describe("parseTeamReadinessForm", () => {
  it("parses a training requirement with a server-generated stable ID", () => {
    const form = base("training_requirements");
    form.set("role_id", ROLE);
    form.set("title", "Revisión jurídica");
    form.set("description", "Completar la orientación interna antes de asumir la función.");
    form.set("status", "COMPLETE");

    expect(parseTeamReadinessForm(form, RECORD)).toMatchObject({
      section: "training_requirements",
      action: "save",
      requirement: {
        id: RECORD,
        role_id: ROLE,
        title: "Revisión jurídica",
        status: "COMPLETE",
      },
    });
  });

  it("parses a campaign-scoped access recommendation payload without creating authority", () => {
    const form = base("access_recommendations");
    form.set("record_id", RECORD);
    form.set("role_id", ROLE);
    form.set("access_action", "read");
    form.set("resource_type", "candidate_workspace");
    form.set("purpose", "Review candidate evidence workspace");
    form.set("status", "REVIEWED");

    expect(parseTeamReadinessForm(form, RECORD)).toMatchObject({
      section: "access_recommendations",
      action: "save",
      recommendation: {
        id: RECORD,
        role_id: ROLE,
        action: "read",
        resource_type: "candidate_workspace",
        status: "REVIEWED",
      },
    });
  });

  it("supports explicit reviewed-empty state without fabricating a record", () => {
    const form = base("training_requirements", "review_empty");
    expect(parseTeamReadinessForm(form, RECORD)).toEqual({
      locale: "es",
      expectedVersion: 4,
      idempotencyKey: "team-readiness:12345678-1234-4234-8234-123456789abc",
      section: "training_requirements",
      action: "review_empty",
    });
  });

  it("fails closed for unsupported sections and roles", () => {
    const unsupported = base("roles", "review_empty");
    expect(() => parseTeamReadinessForm(unsupported, RECORD)).toThrow(
      TeamWorkspaceFormError,
    );

    const invalidRole = base("training_requirements");
    invalidRole.set("role_id", "not-a-uuid");
    invalidRole.set("title", "X");
    invalidRole.set("description", "Y");
    invalidRole.set("status", "COMPLETE");
    expect(() => parseTeamReadinessForm(invalidRole, RECORD)).toThrow(
      /role_id is invalid/,
    );
  });
});
