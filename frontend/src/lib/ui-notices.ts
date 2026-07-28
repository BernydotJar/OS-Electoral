export const UI_NOTICES = [
  "campaign_selected",
  "intake_started",
  "intake_saved",
  "candidate_started",
  "candidate_evidence_saved",
  "team_started",
  "team_role_saved",
  "team_work_item_saved",
  "team_work_item_updated",
  "team_template_applied",
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
