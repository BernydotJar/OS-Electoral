import { randomUUID } from "node:crypto";

import { TeamRoleDossier } from "@/components/team-role-dossier";
import type {
  TeamWorkspaceProjection,
  TeamWorkspaceTemplatePreview,
} from "@/lib/contracts";
import type { Dictionary, Locale } from "@/lib/i18n";
import type { TeamWorkspaceCapabilities } from "@/lib/journey-capabilities";
import type { TeamWorkspaceAvailability } from "@/lib/shell-view-model";

export function TeamWorkspaceEditor({
  locale,
  dictionary,
  demo,
  availability,
  workspace,
  templatePreview,
  templatePreviewUnavailable,
  capabilities,
  prerequisiteReady,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  demo: boolean;
  availability: TeamWorkspaceAvailability;
  workspace: TeamWorkspaceProjection | null;
  templatePreview: TeamWorkspaceTemplatePreview | null;
  templatePreviewUnavailable: boolean;
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
        <details className="team-template-guide">
          <summary>{dictionary.teamWorkspace.templateGuideTitle}</summary>
          <ul>
            {Object.entries(dictionary.teamWorkspace.templateDescriptions).map(
              ([template, description]) => (
                <li key={template}>
                  <strong>
                    {
                      dictionary.teamWorkspace.templateLabels[
                        template as keyof typeof dictionary.teamWorkspace.templateLabels
                      ]
                    }
                  </strong>
                  <span>{description}</span>
                </li>
              ),
            )}
          </ul>
        </details>
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
  const vacantRoles = (workspace.roles ?? []).filter(
    (role) => role.status === "VACANT",
  );
  const selectedTemplate =
    templatePreview?.organization_template ??
    (workspace.organization_template === "FULL_CAMPAIGN"
      ? "FULL_CAMPAIGN"
      : "LEAN_CAMPAIGN");

  return (
    <>
      <section
        id="team-template-preview"
        className="team-template-application"
        aria-labelledby="team-template-application-title"
      >
        <div className="editor-heading">
          <div>
            <p className="eyebrow">
              {dictionary.teamWorkspace.templateApplyEyebrow}
            </p>
            <h3 id="team-template-application-title">
              {dictionary.teamWorkspace.templateApplyTitle}
            </h3>
            <p>{dictionary.teamWorkspace.templateApplyBody}</p>
          </div>
          <span className="version-chip">
            {dictionary.dashboard.version} {workspace.version}
          </span>
        </div>

        <form
          className="team-template-preview-form"
          action={`/${locale}/campaign/team#team-template-preview`}
          method="get"
        >
          <label>
            <span>{dictionary.teamWorkspace.organizationTemplate}</span>
            <select name="team_template" defaultValue={selectedTemplate}>
              <option value="LEAN_CAMPAIGN">
                {dictionary.teamWorkspace.templateLabels.LEAN_CAMPAIGN}
              </option>
              <option value="FULL_CAMPAIGN">
                {dictionary.teamWorkspace.templateLabels.FULL_CAMPAIGN}
              </option>
            </select>
          </label>
          <button type="submit">
            {dictionary.teamWorkspace.templatePreviewAction}
          </button>
        </form>

        <p className="team-template-boundary">
          {dictionary.teamWorkspace.templateConfirmBoundary}
        </p>

        {templatePreviewUnavailable ? (
          <p className="intake-state" role="status">
            {dictionary.teamWorkspace.templatePreviewUnavailable}
          </p>
        ) : null}

        {templatePreview ? (
          <div className="team-template-preview-result" aria-live="polite">
            <div className="team-template-preview-summary">
              <div>
                <strong>{templatePreview.additions.length}</strong>
                <span>{dictionary.teamWorkspace.templateAddedCount}</span>
              </div>
              <div>
                <strong>{templatePreview.skipped.length}</strong>
                <span>{dictionary.teamWorkspace.templateSkippedCount}</span>
              </div>
              <div>
                <strong>{templatePreview.blueprint_version}</strong>
                <span>{dictionary.teamWorkspace.templatePreviewVersion}</span>
              </div>
            </div>

            {templatePreview.additions.length > 0 ? (
              <form
                className="team-template-confirm-form"
                action="/api/ui/team-workspace/template-apply"
                method="post"
              >
                <input type="hidden" name="locale" value={locale} />
                <input
                  type="hidden"
                  name="version"
                  value={templatePreview.workspace_version}
                />
                <input
                  type="hidden"
                  name="organization_template"
                  value={templatePreview.organization_template}
                />
                <input
                  type="hidden"
                  name="preview_digest"
                  value={templatePreview.preview_digest}
                />
                <input
                  type="hidden"
                  name="idempotency_key"
                  value={`team-template:${randomUUID()}`}
                />
                <p>{dictionary.teamWorkspace.templateConfirmBoundary}</p>
                <button type="submit">
                  {dictionary.teamWorkspace.templateConfirmAction} ·{" "}
                  {templatePreview.additions.length}
                </button>
              </form>
            ) : null}

            {templatePreview.additions.length > 0 ? (
              <div className="team-template-change-group">
                <h4>{dictionary.teamWorkspace.templateAdditionsTitle}</h4>
                <div className="team-template-role-grid">
                  {templatePreview.additions.map((role) => (
                    <article key={role.id} className="team-template-role-card">
                      <div>
                        <span>{role.area}</span>
                        <h5>{role.title}</h5>
                        <p>{role.purpose}</p>
                      </div>
                      <div className="team-template-responsibilities">
                        <strong>
                          {dictionary.teamWorkspace.roleResponsibilitiesLabel}
                        </strong>
                        <ul>
                          {role.responsibilities.map((responsibility) => (
                            <li key={responsibility}>{responsibility}</li>
                          ))}
                        </ul>
                      </div>
                      <TeamRoleDossier profile={role} dictionary={dictionary} />
                    </article>
                  ))}
                </div>
              </div>
            ) : (
              <p className="intake-state" role="status">
                {dictionary.teamWorkspace.templateNoChanges}
              </p>
            )}

            {templatePreview.skipped.length > 0 ? (
              <div className="team-template-change-group">
                <h4>{dictionary.teamWorkspace.templateSkippedTitle}</h4>
                <ul className="team-template-skipped-list">
                  {templatePreview.skipped.map((role) => (
                    <li key={`${role.blueprint_key}:${role.matched_role_id}`}>
                      <div>
                        <strong>{role.title}</strong>
                        <span>{role.area}</span>
                      </div>
                      <small>
                        {role.reason === "CANONICAL_BLUEPRINT_MATCH"
                          ? dictionary.teamWorkspace.templateCanonicalMatch
                          : dictionary.teamWorkspace.templateExactMatch}
                      </small>
                      <TeamRoleDossier profile={role} dictionary={dictionary} />
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}
          </div>
        ) : null}
      </section>

      {vacantRoles.length > 0 ? (
        <section
          id="team-role-coverage"
          className="candidate-evidence-editor team-role-coverage"
          aria-labelledby="team-role-coverage-title"
        >
          <div className="editor-heading">
            <div>
              <p className="eyebrow">{dictionary.teamWorkspace.coverageEyebrow}</p>
              <h3 id="team-role-coverage-title">
                {dictionary.teamWorkspace.coverageTitle}
              </h3>
              <p>{dictionary.teamWorkspace.coverageBody}</p>
            </div>
            <span className="version-chip">
              {dictionary.dashboard.version} {workspace.version}
            </span>
          </div>
          <form action="/api/ui/team-workspace/role-coverage" method="post">
            <input type="hidden" name="locale" value={locale} />
            <input type="hidden" name="version" value={workspace.version} />
            <input
              type="hidden"
              name="idempotency_key"
              value={`team-role-coverage:${randomUUID()}`}
            />
            <div className="candidate-evidence-grid">
              <label>
                <span>{dictionary.teamWorkspace.coverageRole}</span>
                <select name="role_id" required defaultValue="">
                  <option value="" disabled>
                    {dictionary.teamWorkspace.coverageSelectRole}
                  </option>
                  {vacantRoles.map((role) => (
                    <option key={role.id} value={role.id}>
                      {role.title} · {role.area}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>{dictionary.teamWorkspace.coverageAvailability}</span>
                <select name="availability_status" defaultValue="AVAILABLE">
                  {Object.entries(
                    dictionary.teamWorkspace.coverageAvailabilityLabels,
                  ).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <span>{dictionary.teamWorkspace.coverageCapacity}</span>
                <input
                  name="weekly_capacity_hours"
                  type="number"
                  min={1}
                  max={168}
                  required
                />
              </label>
              <label className="field-wide">
                <span>
                  <input
                    name="onboarding_confirmed"
                    type="checkbox"
                    value="confirmed"
                    required
                  />{" "}
                  {dictionary.teamWorkspace.coverageOnboardingConfirm}
                </span>
              </label>
            </div>
            <div className="form-actions">
              <p>{dictionary.teamWorkspace.coverageBoundary}</p>
              <button type="submit">{dictionary.teamWorkspace.coverageAction}</button>
            </div>
          </form>
        </section>
      ) : null}

      <section
        className="candidate-evidence-editor team-role-editor"
        aria-labelledby="team-role-editor-title"
      >
        <div className="editor-heading">
          <div>
            <p className="eyebrow">
              {dictionary.teamWorkspace.roleEditorEyebrow}
            </p>
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
              <span>{dictionary.teamWorkspace.decisionScopeLabel}</span>
              <textarea
                name="decision_scope"
                maxLength={6000}
                rows={3}
                required
                placeholder={dictionary.teamWorkspace.decisionScopePlaceholder}
              />
              <small>{dictionary.teamWorkspace.consultingListHelp}</small>
            </label>
            <label className="field-wide">
              <span>{dictionary.teamWorkspace.deliverablesLabel}</span>
              <textarea
                name="deliverables"
                maxLength={6000}
                rows={4}
                required
                placeholder={dictionary.teamWorkspace.deliverablesPlaceholder}
              />
              <small>{dictionary.teamWorkspace.consultingListHelp}</small>
            </label>
            <label className="field-wide">
              <span>{dictionary.teamWorkspace.collaborationPointsLabel}</span>
              <textarea
                name="collaboration_points"
                maxLength={6000}
                rows={3}
                required
                placeholder={
                  dictionary.teamWorkspace.collaborationPointsPlaceholder
                }
              />
              <small>{dictionary.teamWorkspace.consultingListHelp}</small>
            </label>
            <label className="field-wide">
              <span>{dictionary.teamWorkspace.successSignalsLabel}</span>
              <textarea
                name="success_signals"
                maxLength={6000}
                rows={4}
                required
                placeholder={dictionary.teamWorkspace.successSignalsPlaceholder}
              />
              <small>{dictionary.teamWorkspace.consultingListHelp}</small>
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
            <button type="submit">
              {dictionary.teamWorkspace.addRoleAction}
            </button>
          </div>
        </form>
      </section>
    </>
  );
}
