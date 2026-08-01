import { describe, expect, it } from "vitest";

import {
  parseTrainingAssignForm,
  parseTrainingAttemptForm,
  parseTrainingStartForm,
  TrainingFormError,
} from "@/lib/training-form";

const DIGEST = "a".repeat(64);
const ASSIGNMENT_ID = "11111111-1111-4111-8111-111111111111";

function form(values: Record<string, string | readonly string[]>): FormData {
  const data = new FormData();
  for (const [key, value] of Object.entries(values)) {
    for (const item of Array.isArray(value) ? value : [value])
      data.append(key, item);
  }
  return data;
}

describe("Training Academy forms", () => {
  it("parses assign and start forms with bounded identifiers", () => {
    const assigned = parseTrainingAssignForm(
      form({
        locale: "es",
        path_id: "research_foundations_path",
        path_version: "1.0.0",
        catalog_digest: DIGEST,
        role_slug: "electoral_research",
      }),
    );
    expect(assigned.input.path_id).toBe("research_foundations_path");
    expect(assigned.input.catalog_digest).toBe(DIGEST);

    const started = parseTrainingStartForm(
      form({
        locale: "en",
        assignment_id: ASSIGNMENT_ID,
        module_id: "research_foundations",
        expected_assignment_version: "2",
        expected_progress_version: "3",
        catalog_digest: DIGEST,
      }),
    );
    expect(started.locale).toBe("en");
    expect(started.input.expected_progress_version).toBe(3);
  });

  it("parses multiple assessment questions and preserves selected option ids", () => {
    const parsed = parseTrainingAttemptForm(
      form({
        locale: "es",
        assignment_id: ASSIGNMENT_ID,
        module_id: "research_foundations",
        expected_assignment_version: "2",
        expected_progress_version: "2",
        catalog_digest: DIGEST,
        "answer:knowledge_check": "correct",
        "answer:privacy_check": ["aggregate", "purpose_limited"],
      }),
    );
    expect(parsed.input.answers).toEqual([
      { question_id: "knowledge_check", option_ids: ["correct"] },
      {
        question_id: "privacy_check",
        option_ids: ["aggregate", "purpose_limited"],
      },
    ]);
  });

  it("rejects unexpected fields, invalid digests, duplicate answers and missing questions", () => {
    expect(() =>
      parseTrainingAssignForm(
        form({
          locale: "es",
          path_id: "research_foundations_path",
          path_version: "1.0.0",
          catalog_digest: DIGEST,
          role_slug: "electoral_research",
          ranking: "99",
        }),
      ),
    ).toThrow(TrainingFormError);

    expect(() =>
      parseTrainingStartForm(
        form({
          locale: "es",
          assignment_id: ASSIGNMENT_ID,
          module_id: "research_foundations",
          expected_assignment_version: "1",
          expected_progress_version: "1",
          catalog_digest: "not-a-digest",
        }),
      ),
    ).toThrow(/catalog_digest/);

    expect(() =>
      parseTrainingAttemptForm(
        form({
          locale: "es",
          assignment_id: ASSIGNMENT_ID,
          module_id: "research_foundations",
          expected_assignment_version: "1",
          expected_progress_version: "1",
          catalog_digest: DIGEST,
        }),
      ),
    ).toThrow(/out of bounds/);

    expect(() =>
      parseTrainingAttemptForm(
        form({
          locale: "es",
          assignment_id: ASSIGNMENT_ID,
          module_id: "research_foundations",
          expected_assignment_version: "1",
          expected_progress_version: "1",
          catalog_digest: DIGEST,
          "answer:knowledge_check": ["correct", "correct"],
        }),
      ),
    ).toThrow(/option ids/);
  });
});
