import { randomUUID } from "node:crypto";

import type { TeamWorkspaceProjection } from "@/lib/contracts";
import type { Dictionary, Locale } from "@/lib/i18n";
import type { TeamWorkspaceCapabilities } from "@/lib/journey-capabilities";
import type { TeamWorkspaceAvailability } from "@/lib/shell-view-model";

export function TeamWorkspaceEditor({
  locale,
  dictionary,
  demo,
  availability,
  workspace,
  capabilities,
  prerequisiteReady,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  demo: boolean;
  availability: TeamWorkspaceAvailability;
  workspace: TeamWorkspaceProjection | null;
  capabilities: TeamWorkspaceCapabilities;
  prerequisiteReady: boolean;
}>) {
  if (demo) return null;
  if (
    availability === "NOT_STARTED" &&
    capabilities.canStart &&
    prerequisiteReady
  ) {
    return (
      <form
        className="candidate-start-card team-start-card"
        action="/api/ui/team-workspace/start"
        method="post"
      >
        <input type="hidden" name="locale" value={locale} />
        <input
          type="hidden"
          name="idempotency_key"
          value={`team-start:${randomUUID()}`}
        />
        <div>
          <p className="eyebrow">{dictionary.teamWorkspace.startEyebrow}</p>
          <h3>{dictionary.teamWorkspace.startTitle}</h3>
          <p>{dictionary.teamWorkspace.startBody}</p>
        </div>
        <label>
          <span>{dictionary.teamWorkspace.organizationTemplate}</span>
          <select name="organization_template" defaultValue="LEAN_CAMPAIGN">
            {Object.entries(dictionary.teamWorkspace.templateLabels).map(
              ([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ),
            )}
          </select>
          <small>{dictionary.teamWorkspace.organizationTemplateHelp}</small>
        </label>
        <button type="submit">{dictionary.teamWorkspace.startAction}</button>
      </form>
    );
  }
  if (
    availability !== "AVAILABLE" ||
    workspace === null ||
    !capabilities.canRead ||
    !capabilities.canUpdate
  ) {
    return null;
  }
  const areaOptions = Object.values(dictionary.teamWorkspace.areaOptions);
  return (
    <section
      className="candidate-evidence-editor team-role-editor"
      aria-labelledby="team-role-editor-title"
    >
      <div className="editor-heading">
        <div>
          <p className="eyebrow">{dictionary.teamWorkspace.roleEditorEyebrow}</p>
          <h3 id="team-role-editor-title">
            {dictionary.teamWorkspace.roleEditorTitle}
          </h3>
          <p>{dictionary.teamWorkspace.roleEditorBody}</p>
        </div>
        <span className="version-chip">
          {dictionary.dashboard.version} {workspace.version}
        </span>
      </div>
      <form action="/api/ui/team-workspace/role" method="post">
        <input type="hidden" name="locale" value={locale} />
        <input type="hidden" name="version" value={workspace.version} />
        <input
          type="hidden"
          name="idempotency_key"
          value={`team-role:${randomUUID()}`}
        />
        <div className="candidate-evidence-grid">
          <label>
            <span>{dictionary.teamWorkspace.roleTitle}</span>
            <input
              name="title"
              maxLength={160}
              required
              placeholder={dictionary.teamWorkspace.roleTitlePlaceholder}
            />
          </label>
          <label>
            <span>{dictionary.teamWorkspace.roleArea}</span>
            <input
              name="area"
              list="team-area-options"
              maxLength={160}
              required
              placeholder={dictionary.teamWorkspace.roleAreaPlaceholder}
            />
            <datalist id="team-area-options">
              {areaOptions.map((area) => (
                <option key={area} value={area} />
              ))}
            </datalist>
          </label>
          <label className="field-wide">
            <span>{dictionary.teamWorkspace.rolePurpose}</span>
            <textarea
              name="purpose"
              maxLength={1000}
              rows={3}
              required
              placeholder={dictionary.teamWorkspace.rolePurposePlaceholder}
            />
          </label>
          <label className="field-wide">
            <span>{dictionary.teamWorkspace.roleResponsibilities}</span>
            <textarea
              name="responsibilities"
              maxLength={10000}
              rows={5}
              required
              placeholder={
                dictionary.teamWorkspace.roleResponsibilitiesPlaceholder
              }
            />
            <small>{dictionary.teamWorkspace.oneResponsibilityPerLine}</small>
          </label>
          <label className="field-wide">
            <span>{dictionary.teamWorkspace.vacancyPlan}</span>
            <textarea
              name="vacancy_plan"
              maxLength={1000}
              rows={3}
              required
              placeholder={dictionary.teamWorkspace.vacancyPlanPlaceholder}
            />
          </label>
        </div>
        <div className="form-actions">
          <p>{dictionary.teamWorkspace.roleBoundary}</p>
          <button type="submit">{dictionary.teamWorkspace.addRoleAction}</button>
        </div>
      </form>
    </section>
  );
}
