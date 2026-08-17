import { describe, expect, it } from "vitest";

import {
  OperationsWorkspaceFormError,
  parseOperationsSectionForm,
  parseOperationsStartForm,
  parseWarRoomSnapshotForm,
} from "@/lib/operations-workspace-form";

const ID = "11111111-1111-4111-8111-111111111111";
const ID2 = "22222222-2222-4222-8222-222222222222";

function base(section: string): FormData {
  const form = new FormData();
  form.set("locale", "es");
  form.set("version", "3");
  form.set("idempotency_key", `operations-${section}-12345678`);
  form.set("section", section);
  form.set("record_id", "");
  return form;
}

describe("operations workspace forms", () => {
  it("parses bounded roadmap creation", () => {
    const form = new FormData();
    form.set("locale", "es");
    form.set("idempotency_key", "operations-start-12345678");
    form.set("title", "  Operación municipal   2026 ");
    expect(parseOperationsStartForm(form)).toEqual({
      locale: "es",
      idempotencyKey: "operations-start-12345678",
      create: { title: "Operación municipal 2026" },
    });
  });

  it("parses a task using selected existing references", () => {
    const form = base("tasks");
    form.set("phase_id", ID);
    form.set("workstream_id", ID2);
    form.set("milestone_id", "");
    form.set("title", "Preparar revisión diaria");
    form.set("owner_role_id", ID);
    form.set("execution_status", "PLANNED");
    form.append("dependency_ids", ID2);
    form.set("due_date", "2026-08-20");
    form.append("evidence_refs", ID);

    const parsed = parseOperationsSectionForm(form);
    expect(parsed.mutation.kind).toBe("task");
    if (parsed.mutation.kind !== "task") throw new Error("unexpected mutation");
    expect(parsed.mutation.record.dependency_ids).toEqual([ID2]);
    expect(parsed.mutation.record.evidence_refs).toEqual([ID]);
    expect(parsed.mutation.record.milestone_id).toBeNull();
  });

  it("requires an explicit human decision selected from the listed options", () => {
    const form = base("decisions");
    form.set("title", "Confirmar prioridad operativa");
    form.set("human_role_id", ID);
    form.set("options", "Opción A\nOpción B");
    form.set("due_date", "2026-08-20");
    form.set("status", "DECIDED");
    form.set("decision", "");
    expect(() => parseOperationsSectionForm(form)).toThrow(
      "decided item requires a listed option",
    );

    form.set("decision", "Opción B");
    const parsed = parseOperationsSectionForm(form);
    expect(parsed.mutation.kind).toBe("decision");
    if (parsed.mutation.kind !== "decision") throw new Error("unexpected mutation");
    expect(parsed.mutation.record.decision).toBe("Opción B");
  });

  it("rejects impossible dates, duplicate references, and unknown sections", () => {
    const phase = base("phases");
    phase.set("name", "Fase 1");
    phase.set("sequence", "1");
    phase.set("start_date", "2026-02-31");
    phase.set("end_date", "2026-03-10");
    phase.set("status", "PLANNED");
    expect(() => parseOperationsSectionForm(phase)).toThrow("start_date is invalid");

    const task = base("tasks");
    task.set("phase_id", ID);
    task.set("workstream_id", ID2);
    task.set("milestone_id", "");
    task.set("title", "Tarea");
    task.set("owner_role_id", ID);
    task.set("execution_status", "PLANNED");
    task.append("dependency_ids", ID2);
    task.append("dependency_ids", ID2);
    task.set("due_date", "2026-08-20");
    expect(() => parseOperationsSectionForm(task)).toThrow("dependency_ids is invalid");

    const unknown = base("execute_now");
    expect(() => parseOperationsSectionForm(unknown)).toThrow(OperationsWorkspaceFormError);
  });

  it("parses a version-bound snapshot with priorities and follow-up notes", () => {
    const form = new FormData();
    form.set("locale", "en");
    form.set("version", "4");
    form.set("idempotency_key", "war-room-12345678");
    form.set("snapshot_date", "2026-08-16");
    form.set("priorities", "Resolve blockers\nPrepare human decision");
    form.set("follow_up_notes", "Director review at 17:00");
    expect(parseWarRoomSnapshotForm(form)).toEqual({
      locale: "en",
      expectedVersion: 4,
      idempotencyKey: "war-room-12345678",
      create: {
        snapshot_date: "2026-08-16",
        priorities: ["Resolve blockers", "Prepare human decision"],
        follow_up_notes: ["Director review at 17:00"],
      },
    });
  });
});
