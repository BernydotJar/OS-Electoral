import { describe, expect, it } from "vitest";

import {
  TeamWorkspaceFormError,
  parseTeamRoleForm,
  parseTeamTemplateApplyForm,
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
      create: {
        organization_template: "LEAN_CAMPAIGN",
        blueprint_locale: "es",
      },
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
      "decision_scope",
      "Preparar cobertura para decisión humana\nElevar bloqueos de seguridad",
    );
    form.set(
      "deliverables",
      "Mapa agregado\nPlan logístico\nReporte de brechas",
    );
    form.set(
      "collaboration_points",
      "Dirección de campaña\nInvestigación y legal",
    );
    form.set(
      "success_signals",
      "Zonas con responsables\nRiesgos escalados\nSin perfiles individuales",
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
        decision_scope: [
          "Preparar cobertura para decisión humana",
          "Elevar bloqueos de seguridad",
        ],
        deliverables: ["Mapa agregado", "Plan logístico", "Reporte de brechas"],
        collaboration_points: ["Dirección de campaña", "Investigación y legal"],
        success_signals: [
          "Zonas con responsables",
          "Riesgos escalados",
          "Sin perfiles individuales",
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
    form.set("decision_scope", "Preparar decisión");
    form.set("deliverables", "Plan");
    form.set("collaboration_points", "Dirección");
    form.set("success_signals", "Resultado observable");
    form.set("vacancy_plan", "Cubrir la vacante.");

    expect(() => parseTeamRoleForm(form, ROLE_ID)).toThrow(
      TeamWorkspaceFormError,
    );
  });

  it("rejects duplicate or missing consulting dossier entries", () => {
    const form = new FormData();
    form.set("locale", "es");
    form.set("version", "2");
    form.set("idempotency_key", "team-role-5678");
    form.set("title", "Investigación");
    form.set("area", "Evidencia");
    form.set("purpose", "Mantener hechos verificables.");
    form.set("responsibilities", "Validar fuentes");
    form.set("decision_scope", "Elevar contradicciones");
    form.set("deliverables", "Registro\nRegistro");
    form.set("collaboration_points", "Estrategia");
    form.set("success_signals", "Fuentes trazables");
    form.set(
      "vacancy_plan",
      "Seleccionar una persona mediante revisión humana.",
    );

    expect(() => parseTeamRoleForm(form, ROLE_ID)).toThrow(
      TeamWorkspaceFormError,
    );
  });

  it("parses one version-bound human template confirmation", () => {
    const form = new FormData();
    form.set("locale", "en");
    form.set("version", "7");
    form.set("idempotency_key", "team-template-1234");
    form.set("organization_template", "FULL_CAMPAIGN");
    form.set("preview_digest", "a".repeat(64));

    expect(parseTeamTemplateApplyForm(form)).toEqual({
      locale: "en",
      expectedVersion: 7,
      idempotencyKey: "team-template-1234",
      apply: {
        organization_template: "FULL_CAMPAIGN",
        blueprint_locale: "en",
        preview_digest: "a".repeat(64),
      },
    });
  });

  it("rejects custom templates and malformed preview digests", () => {
    const form = new FormData();
    form.set("locale", "es");
    form.set("version", "1");
    form.set("idempotency_key", "team-template-1234");
    form.set("organization_template", "CUSTOM");
    form.set("preview_digest", "not-a-digest");

    expect(() => parseTeamTemplateApplyForm(form)).toThrow(
      TeamWorkspaceFormError,
    );
  });
});
