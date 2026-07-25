import { describe, expect, it } from "vitest";

import {
  TeamWorkspaceFormError,
  parseTeamRoleForm,
  parseTeamWorkspaceStartForm,
} from "@/lib/team-workspace-form";

const ROLE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";

describe("team workspace forms", () => {
  it("parses one bounded organization template selection", () => {
    const form = new FormData();
    form.set("locale", "es");
    form.set("idempotency_key", "team-start-1234");
    form.set("organization_template", "LEAN_CAMPAIGN");

    expect(parseTeamWorkspaceStartForm(form)).toEqual({
      locale: "es",
      idempotencyKey: "team-start-1234",
      create: { organization_template: "LEAN_CAMPAIGN" },
    });
  });

  it("builds one vacant role card without creating identity or permission", () => {
    const form = new FormData();
    form.set("locale", "es");
    form.set("version", "2");
    form.set("idempotency_key", "team-role-1234");
    form.set("title", "  Coordinación   territorial ");
    form.set("area", "Territorio");
    form.set(
      "purpose",
      "Convertir el objetivo territorial en cobertura organizada y verificable.",
    );
    form.set(
      "responsibilities",
      "Diseñar coordinaciones\nDar seguimiento a cobertura\nEscalar bloqueos",
    );
    form.set(
      "vacancy_plan",
      "Definir perfil, entrevistar responsables y aprobar la asignación humana.",
    );

    expect(parseTeamRoleForm(form, ROLE_ID)).toEqual({
      locale: "es",
      expectedVersion: 2,
      idempotencyKey: "team-role-1234",
      role: {
        id: ROLE_ID,
        title: "Coordinación territorial",
        area: "Territorio",
        purpose:
          "Convertir el objetivo territorial en cobertura organizada y verificable.",
        responsibilities: [
          "Diseñar coordinaciones",
          "Dar seguimiento a cobertura",
          "Escalar bloqueos",
        ],
        status: "VACANT",
        principal_id: null,
        availability_status: "UNASSESSED",
        weekly_capacity_hours: null,
        onboarding_status: "NOT_STARTED",
        vacancy_plan:
          "Definir perfil, entrevistar responsables y aprobar la asignación humana.",
      },
    });
  });

  it("rejects duplicate responsibilities and stale versions", () => {
    const form = new FormData();
    form.set("locale", "es");
    form.set("version", "0");
    form.set("idempotency_key", "team-role-1234");
    form.set("title", "Coordinación");
    form.set("area", "Territorio");
    form.set("purpose", "Organizar el trabajo.");
    form.set("responsibilities", "Coordinar\nCoordinar");
    form.set("vacancy_plan", "Cubrir la vacante.");

    expect(() => parseTeamRoleForm(form, ROLE_ID)).toThrow(
      TeamWorkspaceFormError,
    );
  });
});
