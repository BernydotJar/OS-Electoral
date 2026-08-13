export const UI_NOTICES = [
  "campaign_selected",
  "campaign_created",
  "intake_started",
  "intake_saved",
  "candidate_started",
  "candidate_evidence_saved",
  "candidate_section_saved",
  "candidate_section_approved",
  "team_started",
  "team_role_saved",
  "team_work_item_saved",
  "team_work_item_updated",
  "team_readiness_saved",
  "team_template_applied",
  "training_assigned",
  "training_started",
  "training_passed",
  "training_retry",
  "authorization_denied",
  "conflict",
  "validation_error",
  "dependency_failure",
  "unauthenticated",
  "not_found",
  "request_failed",
] as const;

export type UiNotice = (typeof UI_NOTICES)[number];

export function parseUiNotice(
  value: string | string[] | undefined,
): UiNotice | null {
  const candidate = Array.isArray(value) ? value[0] : value;
  return UI_NOTICES.includes(candidate as UiNotice)
    ? (candidate as UiNotice)
    : null;
}
