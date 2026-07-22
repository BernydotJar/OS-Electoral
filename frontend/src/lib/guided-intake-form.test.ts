import { describe, expect, it } from "vitest";

import {
  GuidedIntakeFormError,
  parseGuidedIntakeForm,
} from "@/lib/guided-intake-form";

function validForm(): FormData {
  const form = new FormData();
  form.set("locale", "es");
  form.set("version", "2");
  form.set("idempotency_key", "intake-update-1234");
  form.set("office", "  Alcaldía   Municipal ");
  form.set("candidate_project", "Proyecto interno sujeto a evidencia");
  form.set("current_team", "Dirección\nFinanzas");
  form.set("current_assets", "Base documental");
  form.set("budget_status", "ROUGH_RANGE");
  form.set("known_unknowns", "Calendario electoral");
  form.set("evidence_requirements", "Documento oficial\nRegistro interno");
  return form;
}

describe("parseGuidedIntakeForm", () => {
  it("normalizes the complete bounded patch", () => {
    expect(parseGuidedIntakeForm(validForm())).toEqual({
      locale: "es",
      expectedVersion: 2,
      idempotencyKey: "intake-update-1234",
      update: {
        office: "Alcaldía Municipal",
        candidate_project: "Proyecto interno sujeto a evidencia",
        current_team: ["Dirección", "Finanzas"],
        current_assets: ["Base documental"],
        budget_status: "ROUGH_RANGE",
        known_unknowns: ["Calendario electoral"],
        evidence_requirements: ["Documento oficial", "Registro interno"],
      },
    });
  });

  it("rejects stale metadata, duplicate lists and invalid budgets", () => {
    const stale = validForm();
    stale.set("version", "0");
    expect(() => parseGuidedIntakeForm(stale)).toThrow(GuidedIntakeFormError);

    const duplicate = validForm();
    duplicate.set("current_team", "Finanzas\nfinanzas");
    expect(() => parseGuidedIntakeForm(duplicate)).toThrow("duplicates");

    const budget = validForm();
    budget.set("budget_status", "APPROVED");
    expect(() => parseGuidedIntakeForm(budget)).toThrow("Budget status");
  });
});
