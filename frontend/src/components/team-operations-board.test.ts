import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { TeamOperationsBoard } from "@/components/team-operations-board";
import { TeamWorkItemEditor } from "@/components/team-work-item-editor";
import type { TeamRoleCard, TeamWorkItem } from "@/lib/contracts";
import { dictionaryFor } from "@/lib/i18n";

const dictionary = dictionaryFor("es");
const role: TeamRoleCard = {
  id: "11111111-1111-4111-8111-111111111111",
  title: "Jefatura de campaña",
  area: "Dirección de campaña",
  purpose: "Coordinar decisiones y prioridades humanas.",
  responsibilities: ["Mantener prioridades", "Escalar decisiones"],
  decision_scope: ["Preparar prioridades"],
  deliverables: ["Agenda semanal"],
  collaboration_points: ["Investigación"],
  success_signals: ["Bloqueos visibles"],
  status: "VACANT",
  principal_id: null,
  availability_status: "UNASSESSED",
  weekly_capacity_hours: null,
  onboarding_status: "NOT_STARTED",
  vacancy_plan: "Seleccionar y aprobar humanamente a la persona responsable.",
};
const workItem: TeamWorkItem = {
  id: "22222222-2222-4222-8222-222222222222",
  name: "Preparar agenda semanal",
  description: "Consolidar decisiones, entregables y bloqueos.",
  status: "PLANNED",
  work_type: "DELIVERABLE",
  priority: "HIGH",
  health: "NOT_REPORTED",
  target_date: "2026-08-05",
  next_action: "Validar alcance con dirección.",
  blocker: null,
  evidence: ["Registro de decisiones", "Mapa de bloqueos"],
  cadence: "WEEKLY",
  check_in_note: null,
  last_check_in_at: null,
  assignments: [
    { role_id: role.id, responsibility: "ACCOUNTABLE" },
    { role_id: role.id, responsibility: "RESPONSIBLE" },
  ],
};

describe("team operations board", () => {
  it("renders a planned-work creator bound to one existing function", () => {
    const html = renderToStaticMarkup(
      createElement(TeamWorkItemEditor, {
        locale: "es",
        dictionary,
        roles: [role],
        workspaceVersion: 3,
        canUpdate: true,
        openByDefault: true,
      }),
    );

    expect(html).toContain("/api/ui/team-workspace/work-item");
    expect(html).toContain('name="work_item_id"');
    expect(html).toContain('name="role_id"');
    expect(html).toContain('name="next_action"');
    expect(html).toContain("El trabajo nace planificado");
    expect(html).not.toContain("permission");
  });

  it("renders operational columns, evidence, RACI, and governed check-in", () => {
    const html = renderToStaticMarkup(
      createElement(TeamOperationsBoard, {
        locale: "es",
        dictionary,
        roles: [role],
        workItems: [workItem],
        workspaceVersion: 3,
        canUpdate: true,
      }),
    );

    expect(html).toContain('id="team-operations-board"');
    expect(html).toContain("Planificado");
    expect(html).toContain("En curso");
    expect(html).toContain("Bloqueado");
    expect(html).toContain("Completado");
    expect(html).toContain("Preparar agenda semanal");
    expect(html).toContain('data-status="PLANNED"');
    expect(html).toContain('class="team-work-card-topline"');
    expect(html).toContain('data-kind="type"');
    expect(html).toContain('data-kind="priority" data-value="HIGH"');
    expect(html).toContain('class="team-work-card-facts"');
    expect(html).toContain('class="team-work-next-action"');
    expect(html).toContain("Registro de decisiones");
    expect(html).toContain("Jefatura de campaña");
    expect(html).toContain("/api/ui/team-workspace/work-item-status");
    expect(html).toContain("Para activar, bloquear o completar trabajo");
    expect(html).toContain('value="ACTIVE" disabled=""');
    expect(html).toContain('value="COMPLETE" disabled=""');
    expect(html).not.toContain("productivity score");
  });

  it("does not expose write controls without update authority", () => {
    const html = renderToStaticMarkup(
      createElement(TeamOperationsBoard, {
        locale: "es",
        dictionary,
        roles: [role],
        workItems: [workItem],
        workspaceVersion: 3,
        canUpdate: false,
      }),
    );

    expect(html).not.toContain("/api/ui/team-workspace/work-item-status");
    expect(html).toContain("Preparar agenda semanal");
  });
});
