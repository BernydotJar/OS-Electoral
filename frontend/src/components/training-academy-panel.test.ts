import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

import { TrainingAcademyPanel } from "@/components/training-academy-panel";
import {
  demoTrainingAssignments,
  demoTrainingCatalog,
  demoTrainingReceipts,
} from "@/lib/demo-data";
import { dictionaryFor } from "@/lib/i18n";
import type { TrainingCapabilities } from "@/lib/journey-capabilities";

const allCapabilities: TrainingCapabilities = {
  canReadCatalog: true,
  canReadSelf: true,
  canCompleteSelf: true,
  canManageAssignments: true,
  canReadReceipts: true,
};

function render(
  overrides: Partial<Parameters<typeof TrainingAcademyPanel>[0]> = {},
): string {
  return renderToStaticMarkup(
    createElement(TrainingAcademyPanel, {
      locale: "es",
      dictionary: dictionaryFor("es"),
      catalog: demoTrainingCatalog,
      assignments: demoTrainingAssignments,
      receipts: demoTrainingReceipts,
      availability: "AVAILABLE",
      capabilities: allCapabilities,
      demo: false,
      ...overrides,
    }),
  );
}

describe("TrainingAcademyPanel", () => {
  it("renders the active lesson, progress, assessment and authority boundary", () => {
    const html = render();
    expect(html).toContain("Academia de campaña");
    expect(html).toContain("Investigar antes de actuar");
    expect(html).toContain("Comprobación de aprendizaje");
    expect(html).toContain('action="/api/ui/training/attempt"');
    expect(html).toContain('name="answer:knowledge_check"');
    expect(html).toContain("La formación no concede permisos");
  });

  it("shows assignable paths when the principal has no assignment", () => {
    const html = render({
      assignments: { ...demoTrainingAssignments, assignments: [] },
    });
    expect(html).toContain("Elige una ruta para comenzar");
    expect(html).toContain('action="/api/ui/training/assign"');
    expect(html).toContain("Asignarme esta ruta");
  });

  it("keeps the demo read-only even when synthetic grants exist", () => {
    const html = render({ demo: true });
    expect(html).toContain("respuestas y avances deshabilitados");
    expect(html).not.toContain('action="/api/ui/training/attempt"');
    expect(html).not.toContain('action="/api/ui/training/start"');
    expect(html).not.toContain('action="/api/ui/training/assign"');
  });

  it("renders nothing without catalog access and an honest unavailable state", () => {
    expect(render({ availability: "NOT_AUTHORIZED" })).toBe("");
    const unavailable = render({
      availability: "DEPENDENCY_UNAVAILABLE",
      catalog: null,
      assignments: null,
      receipts: null,
    });
    expect(unavailable).toContain("La academia no está disponible");
    expect(unavailable).not.toContain("Comprobación de aprendizaje");
  });
});
