import { describe, expect, it } from "vitest";

import {
  CandidateWorkspaceFormError,
  parseCandidateEvidenceForm,
  parseCandidateWorkspaceStartForm,
} from "@/lib/candidate-workspace-form";

const EVIDENCE_ID = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";

describe("candidate workspace forms", () => {
  it("normalizes the bounded candidate workspace start intent", () => {
    const form = new FormData();
    form.set("locale", "es");
    form.set("idempotency_key", "candidate-start-1234");
    form.set("display_name", "  Ana   Pérez  ");

    expect(parseCandidateWorkspaceStartForm(form)).toEqual({
      locale: "es",
      idempotencyKey: "candidate-start-1234",
      create: { display_name: "Ana Pérez" },
    });
  });

  it("builds one provenance-preserving evidence record", () => {
    const form = new FormData();
    form.set("locale", "es");
    form.set("version", "3");
    form.set("idempotency_key", "candidate-evidence-1234");
    form.set("classification", "OFFICIAL_SOURCE");
    form.set("title", "  Acuerdo   de convocatoria  ");
    form.set("source_reference", "https://example.test/convocatoria");
    form.set("source_authority", "Tribunal Electoral");
    form.set("jurisdiction", "Municipio de ejemplo");
    form.set("excerpt", "Documento oficial que confirma el calendario.");
    form.set("observed_at", "2026-07-24");

    expect(parseCandidateEvidenceForm(form, EVIDENCE_ID)).toEqual({
      locale: "es",
      expectedVersion: 3,
      idempotencyKey: "candidate-evidence-1234",
      evidence: {
        id: EVIDENCE_ID,
        classification: "OFFICIAL_SOURCE",
        status: "ACCEPTED",
        title: "Acuerdo de convocatoria",
        source_reference: "https://example.test/convocatoria",
        source_authority: "Tribunal Electoral",
        jurisdiction: "Municipio de ejemplo",
        excerpt: "Documento oficial que confirma el calendario.",
        observed_at: "2026-07-24T00:00:00.000Z",
      },
    });
  });

  it("rejects unsafe source references and stale versions", () => {
    const form = new FormData();
    form.set("locale", "es");
    form.set("version", "0");
    form.set("idempotency_key", "candidate-evidence-1234");
    form.set("classification", "OFFICIAL_SOURCE");
    form.set("title", "Fuente");
    form.set("source_reference", "javascript:alert(1)");
    form.set("source_authority", "");
    form.set("jurisdiction", "");
    form.set("excerpt", "");
    form.set("observed_at", "");

    expect(() => parseCandidateEvidenceForm(form, EVIDENCE_ID)).toThrow(
      CandidateWorkspaceFormError,
    );
  });
});
