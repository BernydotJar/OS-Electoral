import { describe, expect, it } from "vitest";

import {
  TeamWorkspaceFormError,
  parseTeamRoleForm,
  parseTeamTemplateApplyForm,
  parseTeamWorkItemForm,
  parseTeamWorkItemUpdateForm,
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

  it("creates one planned operational item without identity or authority", () => {
    const form = new FormData();
    form.set("locale", "es");
    form.set("version", "3");
    form.set("idempotency_key", "team-work-item-1234");
    form.set("work_item_id", "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb");
    form.set("role_id", ROLE_ID);
    form.set("work_type", "DELIVERABLE");
    form.set("priority", "HIGH");
    form.set("cadence", "WEEKLY");
    form.set("name", "  Agenda semanal de dirección ");
    form.set("description", "Consolidar prioridades, decisiones y bloqueos.");
    form.set("target_date", "2026-08-05");
    form.set("next_action", "Validar el alcance con la jefatura de campaña.");
    form.set("evidence", "Registro de decisiones\nMapa de bloqueos");

    expect(parseTeamWorkItemForm(form)).toEqual({
      locale: "es",
      expectedVersion: 3,
      idempotencyKey: "team-work-item-1234",
      workItem: {
        id: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
        name: "Agenda semanal de dirección",
        description: "Consolidar prioridades, decisiones y bloqueos.",
        status: "PLANNED",
        work_type: "DELIVERABLE",
        priority: "HIGH",
        health: "NOT_REPORTED",
        target_date: "2026-08-05",
        next_action: "Validar el alcance con la jefatura de campaña.",
        blocker: null,
        evidence: ["Registro de decisiones", "Mapa de bloqueos"],
        cadence: "WEEKLY",
        check_in_note: null,
        last_check_in_at: null,
        assignments: [
          { role_id: ROLE_ID, responsibility: "ACCOUNTABLE" },
          { role_id: ROLE_ID, responsibility: "RESPONSIBLE" },
        ],
      },
    });

    expect(parseTeamWorkItemForm(form).workItem.id).toBe(
      "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
    );
  });

  it("parses one human health check-in and blocks inconsistent state", () => {
    const form = new FormData();
    form.set("locale", "es");
    form.set("version", "4");
    form.set("idempotency_key", "team-work-update-1234");
    form.set("work_item_id", "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb");
    form.set("status", "BLOCKED");
    form.set("priority", "CRITICAL");
    form.set("health", "OFF_TRACK");
    form.set("target_date", "2026-08-07");
    form.set("next_action", "Elevar la decisión pendiente.");
    form.set("blocker", "Falta una aprobación humana de alcance.");
    form.set("cadence", "DAILY");
    form.set("check_in_note", "La ruta crítica permanece detenida.");

    expect(parseTeamWorkItemUpdateForm(form)).toEqual({
      locale: "es",
      expectedVersion: 4,
      idempotencyKey: "team-work-update-1234",
      workItemId: "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
      updates: {
        status: "BLOCKED",
        priority: "CRITICAL",
        health: "OFF_TRACK",
        target_date: "2026-08-07",
        next_action: "Elevar la decisión pendiente.",
        blocker: "Falta una aprobación humana de alcance.",
        cadence: "DAILY",
        check_in_note: "La ruta crítica permanece detenida.",
      },
    });

    form.set("blocker", "");
    expect(() => parseTeamWorkItemUpdateForm(form)).toThrow(
      TeamWorkspaceFormError,
    );

    form.set("status", "ACTIVE");
    form.set("health", "ON_TRACK");
    form.set("check_in_note", "");
    expect(() => parseTeamWorkItemUpdateForm(form)).toThrow(
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
