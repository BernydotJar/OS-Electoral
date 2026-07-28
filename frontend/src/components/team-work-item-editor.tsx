import { randomUUID } from "node:crypto";

import type { TeamRoleCard } from "@/lib/contracts";
import type { Dictionary, Locale } from "@/lib/i18n";

export function TeamWorkItemEditor({
  locale,
  dictionary,
  roles,
  workspaceVersion,
  canUpdate,
  openByDefault,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  roles: readonly TeamRoleCard[];
  workspaceVersion: number;
  canUpdate: boolean;
  openByDefault: boolean;
}>) {
  if (!canUpdate || roles.length === 0) return null;
  const workItemId = randomUUID();
  const idempotencyKey = `team-work-item:${randomUUID()}`;

  return (
    <details className="team-work-item-creator" open={openByDefault}>
      <summary>
        <span>{dictionary.teamWorkspace.createWorkItem}</span>
        <small>{dictionary.teamWorkspace.plannedBoundary}</small>
      </summary>
      <form action="/api/ui/team-workspace/work-item" method="post">
        <input type="hidden" name="locale" value={locale} />
        <input type="hidden" name="version" value={workspaceVersion} />
        <input type="hidden" name="work_item_id" value={workItemId} />
        <input type="hidden" name="idempotency_key" value={idempotencyKey} />
        <div className="team-work-item-form-grid">
          <label>
            <span>{dictionary.teamWorkspace.workRole}</span>
            <select name="role_id" required defaultValue={roles[0]?.id}>
              {roles.map((role) => (
                <option key={role.id} value={role.id}>
                  {role.title} · {role.area}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>{dictionary.teamWorkspace.workType}</span>
            <select name="work_type" defaultValue="TASK">
              {Object.entries(dictionary.teamWorkspace.workTypeLabels).map(
                ([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ),
              )}
            </select>
          </label>
          <label>
            <span>{dictionary.teamWorkspace.priority}</span>
            <select name="priority" defaultValue="MEDIUM">
              {Object.entries(dictionary.teamWorkspace.priorityLabels).map(
                ([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ),
              )}
            </select>
          </label>
          <label>
            <span>{dictionary.teamWorkspace.cadence}</span>
            <select name="cadence" defaultValue="WEEKLY">
              {Object.entries(dictionary.teamWorkspace.cadenceLabels).map(
                ([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ),
              )}
            </select>
          </label>
          <label className="field-wide">
            <span>{dictionary.teamWorkspace.workName}</span>
            <input name="name" maxLength={255} required />
          </label>
          <label className="field-wide">
            <span>{dictionary.teamWorkspace.workDescription}</span>
            <textarea name="description" maxLength={2000} rows={3} required />
          </label>
          <label>
            <span>{dictionary.teamWorkspace.targetDate}</span>
            <input name="target_date" type="date" />
          </label>
          <label className="field-wide">
            <span>{dictionary.teamWorkspace.workNextAction}</span>
            <textarea name="next_action" maxLength={1000} rows={2} required />
          </label>
          <label className="field-wide">
            <span>{dictionary.teamWorkspace.workEvidence}</span>
            <textarea name="evidence" maxLength={6000} rows={3} />
            <small>{dictionary.teamWorkspace.workEvidenceHelp}</small>
          </label>
        </div>
        <div className="form-actions">
          <p>{dictionary.teamWorkspace.plannedBoundary}</p>
          <button type="submit">{dictionary.teamWorkspace.addWorkItem}</button>
        </div>
      </form>
    </details>
  );
}
