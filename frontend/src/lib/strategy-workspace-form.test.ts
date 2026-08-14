import { describe, expect, it } from "vitest";
import {
  parseStrategyDecisionForm,
  parseStrategySectionForm,
  parseStrategyWorkspaceStartForm,
  StrategyWorkspaceFormError,
} from "@/lib/strategy-workspace-form";

const EVIDENCE = "11111111-1111-4111-8111-111111111111";
const ROLE = "22222222-2222-4222-8222-222222222222";
const OPTION = "33333333-3333-4333-8333-333333333333";

function base(section = "evidence") {
  const form = new FormData();
  form.set("locale", "es");
  form.set("version", "3");
  form.set("idempotency_key", "strategy:12345678-1234-4234-8234-123456789abc");
  form.set("section", section);
  form.set("strategy_action", "save");
  form.set("record_id", "");
  return form;
}

describe("strategy workspace form parser", () => {
  it("parses bounded start and accepted verified evidence", () => {
    const start = new FormData();
    start.set("locale", "es");
    start.set("idempotency_key", "strategy-start:12345678-1234-4234-8234-123456789abc");
    start.set("title", "Sala de decisión interna");
    expect(parseStrategyWorkspaceStartForm(start).create.title).toBe("Sala de decisión interna");

    const form = base();
    form.set("classification", "VERIFIED");
    form.set("statement", "El registro oficial confirma el calendario interno.");
    form.set("source_reference", "https://example.test/record");
    form.set("authority", "Autoridad pública");
    form.set("jurisdiction", "Guatemala");
    form.set("collected_at", "2026-08-12");
    const parsed = parseStrategySectionForm(form);
    expect(parsed.mutation.kind).toBe("evidence");
    if (parsed.mutation.kind === "evidence") {
      expect(parsed.mutation.record.status).toBe("ACCEPTED");
      expect(parsed.mutation.record.classification).toBe("VERIFIED");
    }
  });

  it("rejects verified evidence without complete provenance", () => {
    const form = base();
    form.set("classification", "VERIFIED");
    form.set("statement", "Afirmación que reclama verificación.");
    form.set("source_reference", "https://example.test/source");
    form.set("authority", "");
    form.set("jurisdiction", "Guatemala");
    form.set("collected_at", "2026-08-12");
    expect(() => parseStrategySectionForm(form)).toThrow(StrategyWorkspaceFormError);
  });

  it("rejects invalid versions, UUID references, and overlong bounded text", () => {
    const invalidVersion = base("objectives");
    invalidVersion.set("version", "0");
    invalidVersion.set("outcome", "Completar revisión interna.");
    invalidVersion.set("metric", "Registros aceptados");
    invalidVersion.set("baseline", "1");
    invalidVersion.set("target", "10");
    invalidVersion.set("deadline", "2026-09-01");
    invalidVersion.set("owner_role_id", ROLE);
    invalidVersion.append("evidence_refs", EVIDENCE);
    expect(() => parseStrategySectionForm(invalidVersion)).toThrow(StrategyWorkspaceFormError);

    const invalidReference = base("options");
    invalidReference.set("title", "Opción A");
    invalidReference.set("summary", "Secuenciar trabajo interno por evidencia.");
    invalidReference.append("hypothesis_refs", "not-a-uuid");
    invalidReference.append("evidence_refs", EVIDENCE);
    invalidReference.set("benefits", "Mantiene trazabilidad");
    invalidReference.set("risks", "Requiere revisión");
    invalidReference.set("tradeoffs", "Difiere trabajo posterior");
    expect(() => parseStrategySectionForm(invalidReference)).toThrow(StrategyWorkspaceFormError);

    const overlong = base("evidence");
    overlong.set("classification", "UNKNOWN");
    overlong.set("statement", "x".repeat(2001));
    overlong.set("collected_at", "2026-08-12");
    expect(() => parseStrategySectionForm(overlong)).toThrow(StrategyWorkspaceFormError);
  });

  it("does not allow unknown evidence to claim verified provenance", () => {
    const form = base();
    form.set("classification", "UNKNOWN");
    form.set("statement", "Dato todavía por comprobar.");
    form.set("source_reference", "https://example.test/unverified");
    form.set("authority", "No confirmada");
    form.set("jurisdiction", "Guatemala");
    form.set("collected_at", "2026-08-12");
    const parsed = parseStrategySectionForm(form);
    if (parsed.mutation.kind !== "evidence") throw new Error("wrong mutation");
    expect(parsed.mutation.record.status).toBe("NEEDS_REVIEW");
    expect(parsed.mutation.record.source_reference).toBeNull();
    expect(parsed.mutation.record.authority).toBeNull();
    expect(parsed.mutation.record.jurisdiction).toBeNull();
  });

  it("requires complete comparable options and measurable objectives", () => {
    const option = base("options");
    option.set("title", "Opción A");
    option.set("summary", "Secuenciar trabajo interno por evidencia.");
    option.append("hypothesis_refs", EVIDENCE);
    option.append("evidence_refs", EVIDENCE);
    option.set("benefits", "Mantiene trazabilidad");
    option.set("risks", "Requiere tiempo de revisión");
    option.set("tradeoffs", "Retrasa trabajo posterior");
    expect(parseStrategySectionForm(option).mutation.kind).toBe("option");

    const objective = base("objectives");
    objective.set("outcome", "Completar revisión interna.");
    objective.set("metric", "Registros aceptados");
    objective.set("baseline", "1");
    objective.set("target", "10");
    objective.set("deadline", "2026-09-01");
    objective.set("owner_role_id", ROLE);
    objective.append("evidence_refs", EVIDENCE);
    expect(parseStrategySectionForm(objective).mutation.kind).toBe("objective");
  });

  it("allows reviewed-empty only for contradiction and red-team sections", () => {
    const contradiction = base("contradictions");
    contradiction.set("strategy_action", "review_empty");
    expect(parseStrategySectionForm(contradiction).mutation).toEqual({
      kind: "review_empty",
      section: "contradictions",
      recordId: null,
    });

    const invalid = base("options");
    invalid.set("strategy_action", "review_empty");
    expect(() => parseStrategySectionForm(invalid)).toThrow(StrategyWorkspaceFormError);
  });

  it("parses a version-bound human decision request", () => {
    const form = new FormData();
    form.set("locale", "es");
    form.set("version", "7");
    form.set("idempotency_key", "strategy-decision:12345678-1234-4234-8234-123456789abc");
    form.set("selected_option_id", OPTION);
    form.set("human_role_id", ROLE);
    form.set("reason", "La persona autorizada comparó evidencia, riesgos y tradeoffs.");
    expect(parseStrategyDecisionForm(form)).toEqual(
      expect.objectContaining({ expectedVersion: 7, decision: expect.objectContaining({ selected_option_id: OPTION }) }),
    );
  });
});
