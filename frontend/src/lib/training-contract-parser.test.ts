import { describe, expect, it, vi } from "vitest";

vi.mock("server-only", () => ({}));

import {
  DEMO_CAMPAIGN_ID,
  DEMO_TENANT_ID,
  demoTenantIdentity,
  demoTrainingAssignments,
  demoTrainingCatalog,
  demoTrainingReceipts,
} from "@/lib/demo-data";
import {
  parseTrainingAssignmentCreateEvidence,
  parseTrainingAssignmentListEvidence,
  parseTrainingAttemptEvidence,
  parseTrainingCatalogProjection,
  parseTrainingReceiptListEvidence,
  TrainingContractValidationError,
} from "@/lib/training-contract-parser";

const clone = <T>(value: T): T => structuredClone(value);

function assignmentCreatePayload() {
  return {
    assignment: clone(demoTrainingAssignments.assignments[0]!),
    audit_event_id: "39393939-3939-4939-8939-393939393939",
    outbox_event_id: "40404040-4040-4040-8040-404040404040",
  };
}

function attemptPayload() {
  return {
    assignment: {
      ...clone(demoTrainingAssignments.assignments[0]!),
      version: 3,
      status: "COMPLETED",
      completed_modules: 1,
      next_module_id: null,
      completed_at: "2026-08-01T06:00:00Z",
      modules: [
        {
          ...clone(demoTrainingAssignments.assignments[0]!.modules[0]!),
          status: "COMPLETED",
          attempt_count: 1,
          latest_result: "PASS",
          completed_at: "2026-08-01T06:00:00Z",
          version: 3,
        },
      ],
    },
    outcome: {
      result: "PASS",
      correct_count: 1,
      total_questions: 1,
      passing_percent: 100,
      feedback: [
        {
          question_id: "knowledge_check",
          correct: true,
          explanation: "La evidencia precede a la acción.",
        },
      ],
      authority_effect: "NONE",
    },
    receipt: {
      id: "41414141-4141-4141-8141-414141414141",
      assignment_id: demoTrainingAssignments.assignments[0]!.id,
      module_progress_id:
        demoTrainingAssignments.assignments[0]!.modules[0]!.id,
      principal_id: demoTenantIdentity.principal_id,
      module_id: "research_foundations",
      module_version: "1.0.0",
      result: "PASS",
      completed_at: "2026-08-01T06:00:00Z",
      catalog_digest: demoTrainingCatalog.catalog_digest,
      audit_event_id: "42424242-4242-4242-8242-424242424242",
      authority_effect: "NONE",
      external_effects: "NONE",
    },
    audit_event_id: "42424242-4242-4242-8242-424242424242",
  };
}

describe("Training Academy response contracts", () => {
  it("accepts the governed catalog and hides answer keys by construction", () => {
    const parsed = parseTrainingCatalogProjection(clone(demoTrainingCatalog));
    expect(parsed.locale).toBe("es");
    expect(parsed.modules).toHaveLength(1);
    expect(JSON.stringify(parsed)).not.toContain("correct_option_ids");
    expect(parsed.authority_effect).toBe("NONE");
  });

  it("rejects catalog unknown fields, authority effects, and unknown path modules", () => {
    const unknown = clone(demoTrainingCatalog) as unknown as Record<
      string,
      unknown
    >;
    unknown.ranking = 99;
    expect(() => parseTrainingCatalogProjection(unknown)).toThrow(
      TrainingContractValidationError,
    );

    const authority = clone(demoTrainingCatalog) as unknown as {
      authority_effect: string;
    };
    authority.authority_effect = "GRANT";
    expect(() => parseTrainingCatalogProjection(authority)).toThrow(
      /must be NONE/,
    );

    const pathDrift = clone(demoTrainingCatalog) as unknown as {
      paths: { modules: { module_id: string }[] }[];
    };
    pathDrift.paths[0]!.modules[0]!.module_id = "missing_module";
    expect(() => parseTrainingCatalogProjection(pathDrift)).toThrow(
      /unknown module/,
    );
  });

  it("enforces tenant, campaign, and principal scope for assignment lists", () => {
    const parsed = parseTrainingAssignmentListEvidence(
      clone(demoTrainingAssignments),
      DEMO_TENANT_ID,
      DEMO_CAMPAIGN_ID,
      demoTenantIdentity.principal_id,
    );
    expect(parsed.assignments[0]!.next_module_id).toBe("research_foundations");

    const escaped = clone(demoTrainingAssignments) as unknown as {
      assignments: { principal_id: string }[];
    };
    escaped.assignments[0]!.principal_id =
      "43434343-4343-4343-8343-434343434343";
    expect(() =>
      parseTrainingAssignmentListEvidence(
        escaped,
        DEMO_TENANT_ID,
        DEMO_CAMPAIGN_ID,
        demoTenantIdentity.principal_id,
      ),
    ).toThrow(/escaped/);
  });

  it("rejects inconsistent progress totals and invalid next module pointers", () => {
    const inconsistent = clone(demoTrainingAssignments) as unknown as {
      assignments: { completed_modules: number }[];
    };
    inconsistent.assignments[0]!.completed_modules = 1;
    expect(() => parseTrainingAssignmentListEvidence(inconsistent)).toThrow(
      /progress totals/,
    );

    const nextDrift = clone(demoTrainingAssignments) as unknown as {
      assignments: { next_module_id: string }[];
    };
    nextDrift.assignments[0]!.next_module_id = "unknown_module";
    expect(() => parseTrainingAssignmentListEvidence(nextDrift)).toThrow(
      /next training module/,
    );
  });

  it("validates assignment creation and assessment evidence without authority", () => {
    const created = parseTrainingAssignmentCreateEvidence(
      assignmentCreatePayload(),
      DEMO_TENANT_ID,
      DEMO_CAMPAIGN_ID,
      demoTenantIdentity.principal_id,
    );
    expect(created.assignment.authority_effect).toBe("NONE");

    const attempted = parseTrainingAttemptEvidence(
      attemptPayload(),
      DEMO_TENANT_ID,
      DEMO_CAMPAIGN_ID,
      demoTenantIdentity.principal_id,
    );
    expect(attempted.outcome.result).toBe("PASS");
    expect(attempted.receipt?.authority_effect).toBe("NONE");
  });

  it("rejects non-pass receipts, cross-principal receipts, and answer leakage fields", () => {
    const invalidResult = attemptPayload();
    invalidResult.receipt.result = "FAIL";
    expect(() => parseTrainingAttemptEvidence(invalidResult)).toThrow(
      /passing completion/,
    );

    const escaped = attemptPayload();
    escaped.receipt.principal_id = "44444444-4444-4444-8444-444444444444";
    expect(() =>
      parseTrainingAttemptEvidence(
        escaped,
        DEMO_TENANT_ID,
        DEMO_CAMPAIGN_ID,
        demoTenantIdentity.principal_id,
      ),
    ).toThrow(/escaped/);

    const leaked = attemptPayload() as unknown as {
      outcome: Record<string, unknown>;
    };
    leaked.outcome.answers = ["secret"];
    expect(() => parseTrainingAttemptEvidence(leaked)).toThrow(
      /unexpected or missing/,
    );
  });

  it("accepts empty receipt lists and rejects receipt authority drift", () => {
    expect(
      parseTrainingReceiptListEvidence(
        clone(demoTrainingReceipts),
        demoTenantIdentity.principal_id,
      ).receipts,
    ).toEqual([]);

    const drift = {
      ...attemptPayload().receipt,
      authority_effect: "GRANT",
    };
    expect(() =>
      parseTrainingReceiptListEvidence(
        {
          receipts: [drift],
          audit_event_id: "45454545-4545-4545-8545-454545454545",
          authority_effect: "NONE",
        },
        demoTenantIdentity.principal_id,
      ),
    ).toThrow(/must be NONE/);
  });
});
