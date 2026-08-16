import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

import { OperationsWorkspaceEditor } from "@/components/operations-workspace-editor";
import type { TeamRoleCard } from "@/lib/contracts";
import { demoCampaignRoadmap } from "@/lib/demo-data";
import { dictionaryFor } from "@/lib/i18n";

const ROLE = "21212121-2121-4121-8121-212121212121";
const EVIDENCE = "23232323-2323-4323-8323-232323232323";

const role: TeamRoleCard = {
  id: ROLE,
  title: "Dirección de campaña",
  area: "Dirección",
  purpose: "Coordinar",
  responsibilities: ["Coordinar"],
  decision_scope: ["Decidir internamente"],
  deliverables: ["Agenda"],
  collaboration_points: ["Equipo"],
  success_signals: ["Cadencia"],
  status: "FILLED",
  principal_id: "88888888-8888-4888-8888-888888888888",
  availability_status: "AVAILABLE",
  weekly_capacity_hours: 40,
  onboarding_status: "COMPLETE",
  vacancy_plan: null,
};

const fullCaps = {
  canStart: true,
  canRead: true,
  canUpdate: true,
  canCreateSnapshot: true,
  canReadSnapshot: true,
};

const common = {
  locale: "es" as const,
  dictionary: dictionaryFor("es"),
  demo: false,
  capabilities: fullCaps,
  prerequisiteReady: true,
  teamRoles: [role],
  evidenceReferences: [{ id: EVIDENCE, label: "Estrategia: evidencia verificada" }],
};

describe("OperationsWorkspaceEditor", () => {
  it("shows roadmap creation only when Strategy/Team prerequisites and exact grants allow it", () => {
    const html = renderToStaticMarkup(
      createElement(OperationsWorkspaceEditor, {
        ...common,
        availability: "NOT_STARTED",
        roadmap: null,
      }),
    );
    expect(html).toContain('action="/api/ui/operations-workspace/start"');

    const locked = renderToStaticMarkup(
      createElement(OperationsWorkspaceEditor, {
        ...common,
        availability: "NOT_STARTED",
        roadmap: null,
        prerequisiteReady: false,
      }),
    );
    expect(locked).not.toContain("<form");
  });

  it("renders progressive authoring with bounded selectors instead of free UUID inputs", () => {
    const html = renderToStaticMarkup(
      createElement(OperationsWorkspaceEditor, {
        ...common,
        availability: "AVAILABLE",
        roadmap: demoCampaignRoadmap.roadmap,
      }),
    );
    expect(html).toContain('id="operations-authoring"');
    expect(html).toContain('id="operations-phases"');
    expect(html).toContain('id="operations-tasks"');
    expect(html).toContain('name="dependency_ids"');
    expect(html).toContain('name="evidence_refs"');
    expect(html).toContain('<select name="owner_role_id"');
    expect(html).not.toContain('<input name="owner_role_id"');
    expect(html).not.toContain('<input name="phase_id"');
    expect(html).not.toContain('<input name="workstream_id"');
    expect(html).toContain('id="operations-snapshot-create"');
  });

  it("requires a second explicit human step to select a decision option", () => {
    const html = renderToStaticMarkup(
      createElement(OperationsWorkspaceEditor, {
        ...common,
        availability: "AVAILABLE",
        roadmap: demoCampaignRoadmap.roadmap,
      }),
    );
    expect(html).toContain('<input type="hidden" name="status" value="REQUIRED"');
    expect(html).toContain('<input type="hidden" name="decision" value=""');
    expect(html).toContain('<select name="decision"');
    expect(html).toContain('value="" selected="">Aún sin decisión</option>');
  });

  it("keeps an existing roadmap read-only when the Strategy prerequisite is no longer current", () => {
    const html = renderToStaticMarkup(
      createElement(OperationsWorkspaceEditor, {
        ...common,
        availability: "AVAILABLE",
        roadmap: demoCampaignRoadmap.roadmap,
        prerequisiteReady: false,
      }),
    );
    expect(html).toBe("");
  });

  it("renders no mutation controls for static review or without update authority", () => {
    const demo = renderToStaticMarkup(
      createElement(OperationsWorkspaceEditor, {
        ...common,
        demo: true,
        availability: "AVAILABLE",
        roadmap: demoCampaignRoadmap.roadmap,
      }),
    );
    expect(demo).toBe("");

    const readOnly = renderToStaticMarkup(
      createElement(OperationsWorkspaceEditor, {
        ...common,
        capabilities: { ...fullCaps, canUpdate: false },
        availability: "AVAILABLE",
        roadmap: demoCampaignRoadmap.roadmap,
      }),
    );
    expect(readOnly).toBe("");
  });
});
