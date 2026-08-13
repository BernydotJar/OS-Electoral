import { describe, expect, it } from "vitest";

import {
  CandidateWorkspaceFormError,
  parseCandidateApprovalForm,
  parseCandidateSectionForm,
} from "@/lib/candidate-workspace-form";

const VERSION = "3";
const IDEMPOTENCY = "candidate-section:11111111-1111-4111-8111-111111111111";
const EVIDENCE = "22222222-2222-4222-8222-222222222222";

function base(section: string) {
  const form = new FormData();
  form.set("locale", "es");
  form.set("version", VERSION);
  form.set("idempotency_key", IDEMPOTENCY);
  form.set("section", section);
  form.set("section_action", "save");
  form.set("record_id", "");
  return form;
}

describe("candidate section forms", () => {
  it("parses an evidence-linked verified identity claim", () => {
    const form = base("identity");
    form.set("label", "Identidad");
    form.set("claim", "Nombre legal verificado");
    form.set("status", "VERIFIED");
    form.set("classification", "OFFICIAL_SOURCE");
    form.append("evidence_refs", EVIDENCE);
    const parsed = parseCandidateSectionForm(form);
    expect(parsed.mutation.kind).toBe("claim");
    if (parsed.mutation.kind !== "claim") throw new Error("wrong mutation");
    expect(parsed.mutation.record.evidence_refs).toEqual([EVIDENCE]);
  });

  it("parses an attribute and keeps perception references distinct", () => {
    const form = base("attributes");
    form.set("name", "Capacidad");
    form.set("claim", "Ha gestionado equipos complejos");
    form.set("status", "VERIFIED");
    form.set("candidate_self_assessment", "YES");
    form.set("team_assessment", "YES");
    form.set("citizen_evidence", "UNRESOLVED");
    form.set("risk", "No generalizar más allá de la evidencia");
    form.append("evidence_refs", EVIDENCE);
    const parsed = parseCandidateSectionForm(form);
    expect(parsed.mutation.kind).toBe("attribute");
  });

  it("allows an explicit empty contradictions review but not for claims", () => {
    const form = base("contradictions");
    form.set("section_action", "review_empty");
    expect(parseCandidateSectionForm(form).mutation).toMatchObject({
      kind: "review_empty",
      section: "contradictions",
    });
    form.set("section", "identity");
    expect(() => parseCandidateSectionForm(form)).toThrow(
      CandidateWorkspaceFormError,
    );
  });

  it("parses a version-bound approval reason", () => {
    const form = new FormData();
    form.set("locale", "en");
    form.set("version", "8");
    form.set("idempotency_key", "candidate-approval:aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa");
    form.set("section", "purpose");
    form.set("reason", "Evidence reviewed by the authorized campaign lead.");
    expect(parseCandidateApprovalForm(form)).toMatchObject({
      locale: "en",
      expectedVersion: 8,
      section: "purpose",
    });
  });
});
