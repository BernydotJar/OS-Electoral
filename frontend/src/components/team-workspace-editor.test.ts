import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

import { TeamWorkspaceEditor } from "@/components/team-workspace-editor";
import type { TeamRoleCard } from "@/lib/contracts";
import { demoTeamWorkspace } from "@/lib/demo-data";
import { dictionaryFor } from "@/lib/i18n";

const ROLE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";

const vacancy: TeamRoleCard = {
  id: ROLE,
  title: "Dirección de campaña",
  area: "Dirección",
  purpose: "Coordinar trabajo interno.",
  responsibilities: ["Coordinar"],
  decision_scope: ["Preparar decisiones"],
  deliverables: ["Agenda"],
  collaboration_points: ["Equipo"],
  success_signals: ["Cadencia"],
  status: "VACANT",
  principal_id: null,
  availability_status: "UNASSESSED",
  weekly_capacity_hours: null,
  onboarding_status: "NOT_STARTED",
  vacancy_plan: "Cubrir mediante decisión humana.",
};

const fullCaps = { canStart: true, canRead: true, canUpdate: true };

function render(demo = false, canUpdate = true) {
  return renderToStaticMarkup(
    createElement(TeamWorkspaceEditor, {
      locale: "es",
      dictionary: dictionaryFor("es"),
      demo,
      availability: "AVAILABLE",
      workspace: {
        ...demoTeamWorkspace.workspace,
        roles: [vacancy],
        version: 4,
      },
      templatePreview: null,
      templatePreviewUnavailable: false,
      capabilities: { ...fullCaps, canUpdate },
      prerequisiteReady: true,
    }),
  );
}

describe("TeamWorkspaceEditor role coverage", () => {
  it("offers bounded current-session self-coverage without a principal-id field", () => {
    const html = render();
    expect(html).toContain('id="team-role-coverage"');
    expect(html).toContain('action="/api/ui/team-workspace/role-coverage"');
    expect(html).toContain('<select name="role_id"');
    expect(html).toContain(`value="${ROLE}"`);
    expect(html).toContain('name="weekly_capacity_hours"');
    expect(html).toContain('name="onboarding_confirmed"');
    expect(html).not.toContain('name="principal_id"');
  });

  it("renders no governed mutation controls in demo or without update authority", () => {
    expect(render(true)).toBe("");
    expect(render(false, false)).toBe("");
  });
});
