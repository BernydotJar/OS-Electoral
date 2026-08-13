import { randomUUID } from "node:crypto";

import type {
  TeamAccessRecommendation,
  TeamTrainingRequirement,
  TeamWorkspaceProjection,
} from "@/lib/contracts";
import type { Dictionary, Locale } from "@/lib/i18n";
import type { TeamWorkspaceCapabilities } from "@/lib/journey-capabilities";

type Props = Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  demo: boolean;
  workspace: TeamWorkspaceProjection;
  capabilities: TeamWorkspaceCapabilities;
}>;

function HiddenFields({
  locale,
  workspace,
  section,
  action,
  recordId = "",
  prefix,
}: Readonly<{
  locale: Locale;
  workspace: TeamWorkspaceProjection;
  section: "training_requirements" | "access_recommendations";
  action: "save" | "review_empty";
  recordId?: string;
  prefix: string;
}>) {
  return (
    <>
      <input type="hidden" name="locale" value={locale} />
      <input type="hidden" name="version" value={workspace.version} />
      <input
        type="hidden"
        name="idempotency_key"
        value={`${prefix}:${randomUUID()}`}
      />
      <input type="hidden" name="section" value={section} />
      <input type="hidden" name="readiness_action" value={action} />
      <input type="hidden" name="record_id" value={recordId} />
    </>
  );
}

function RoleSelect({
  dictionary,
  workspace,
  defaultValue,
}: Readonly<{
  dictionary: Dictionary;
  workspace: TeamWorkspaceProjection;
  defaultValue?: string;
}>) {
  const roles = workspace.roles ?? [];
  return (
    <label>
      <span>{dictionary.teamWorkspace.readinessRole}</span>
      <select name="role_id" required defaultValue={defaultValue ?? roles[0]?.id}>
        {roles.map((role) => (
          <option key={role.id} value={role.id}>
            {role.title} · {role.area}
          </option>
        ))}
      </select>
    </label>
  );
}

function TrainingForm({
  locale,
  dictionary,
  workspace,
  record,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  workspace: TeamWorkspaceProjection;
  record: TeamTrainingRequirement | null;
}>) {
  return (
    <form action="/api/ui/team-workspace/readiness" method="post">
      <HiddenFields
        locale={locale}
        workspace={workspace}
        section="training_requirements"
        action="save"
        recordId={record?.id}
        prefix="team-training-review"
      />
      <h4>{record?.title ?? dictionary.teamWorkspace.newReadinessRecord}</h4>
      <div className="candidate-evidence-grid">
        <RoleSelect
          dictionary={dictionary}
          workspace={workspace}
          defaultValue={record?.role_id}
        />
        <label>
          <span>{dictionary.teamWorkspace.trainingRequirementStatus}</span>
          <select name="status" defaultValue={record?.status ?? "NOT_STARTED"}>
            {Object.entries(
              dictionary.teamWorkspace.trainingRequirementStatusLabels,
            ).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
        <label className="field-wide">
          <span>{dictionary.teamWorkspace.trainingRequirementTitle}</span>
          <input name="title" required maxLength={255} defaultValue={record?.title ?? ""} />
        </label>
        <label className="field-wide">
          <span>{dictionary.teamWorkspace.trainingRequirementDescription}</span>
          <textarea
            name="description"
            required
            maxLength={2000}
            rows={4}
            defaultValue={record?.description ?? ""}
          />
        </label>
      </div>
      <div className="form-actions">
        <p>{dictionary.teamWorkspace.readinessBoundary}</p>
        <button type="submit">
          {record
            ? dictionary.teamWorkspace.saveTrainingRequirement
            : dictionary.teamWorkspace.addTrainingRequirement}
        </button>
      </div>
    </form>
  );
}

function AccessForm({
  locale,
  dictionary,
  workspace,
  record,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  workspace: TeamWorkspaceProjection;
  record: TeamAccessRecommendation | null;
}>) {
  return (
    <form action="/api/ui/team-workspace/readiness" method="post">
      <HiddenFields
        locale={locale}
        workspace={workspace}
        section="access_recommendations"
        action="save"
        recordId={record?.id}
        prefix="team-access-review"
      />
      <h4>{record?.purpose ?? dictionary.teamWorkspace.newReadinessRecord}</h4>
      <div className="candidate-evidence-grid">
        <RoleSelect
          dictionary={dictionary}
          workspace={workspace}
          defaultValue={record?.role_id}
        />
        <label>
          <span>{dictionary.teamWorkspace.accessReviewStatus}</span>
          <select name="status" defaultValue={record?.status ?? "PROPOSED"}>
            {Object.entries(dictionary.teamWorkspace.accessReviewStatusLabels).map(
              ([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ),
            )}
          </select>
        </label>
        <label>
          <span>{dictionary.teamWorkspace.accessAction}</span>
          <input
            name="access_action"
            required
            maxLength={100}
            defaultValue={record?.action ?? "read"}
          />
        </label>
        <label>
          <span>{dictionary.teamWorkspace.accessResourceType}</span>
          <input
            name="resource_type"
            required
            maxLength={100}
            defaultValue={record?.resource_type ?? "campaign"}
          />
        </label>
        <label className="field-wide">
          <span>{dictionary.teamWorkspace.accessPurpose}</span>
          <textarea
            name="purpose"
            required
            maxLength={500}
            rows={3}
            defaultValue={record?.purpose ?? ""}
          />
        </label>
      </div>
      <div className="form-actions">
        <p>{dictionary.teamWorkspace.readinessBoundary}</p>
        <button type="submit">
          {record
            ? dictionary.teamWorkspace.saveAccessRecommendation
            : dictionary.teamWorkspace.addAccessRecommendation}
        </button>
      </div>
    </form>
  );
}

function EmptyReview({
  locale,
  dictionary,
  workspace,
  section,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  workspace: TeamWorkspaceProjection;
  section: "training_requirements" | "access_recommendations";
}>) {
  return (
    <form
      className="candidate-empty-review"
      action="/api/ui/team-workspace/readiness"
      method="post"
    >
      <HiddenFields
        locale={locale}
        workspace={workspace}
        section={section}
        action="review_empty"
        prefix={`team-${section}-empty-review`}
      />
      <p>{dictionary.teamWorkspace.readinessBoundary}</p>
      <button type="submit">
        {section === "training_requirements"
          ? dictionary.teamWorkspace.reviewNoTraining
          : dictionary.teamWorkspace.reviewNoAccess}
      </button>
    </form>
  );
}

export function TeamReadinessCompletion({
  locale,
  dictionary,
  demo,
  workspace,
  capabilities,
}: Props) {
  if (
    demo ||
    !capabilities.canRead ||
    !capabilities.canUpdate ||
    (workspace.roles ?? []).length === 0
  ) {
    return null;
  }
  const training = workspace.training_requirements;
  const access = workspace.access_recommendations;
  return (
    <section
      id="team-readiness-completion"
      className="candidate-evidence-editor team-readiness-completion"
      aria-labelledby="team-readiness-title"
    >
      <div className="editor-heading">
        <div>
          <p className="eyebrow">{dictionary.teamWorkspace.readinessEyebrow}</p>
          <h3 id="team-readiness-title">{dictionary.teamWorkspace.readinessTitle}</h3>
          <p>{dictionary.teamWorkspace.readinessBody}</p>
        </div>
        <span className="version-chip">
          {dictionary.dashboard.version} {workspace.version}
        </span>
      </div>
      <p className="team-template-boundary">{dictionary.teamWorkspace.readinessBoundary}</p>

      <div className="team-readiness-grid">
        <details className="team-readiness-section" open={training === null}>
          <summary>
            <span>{dictionary.teamWorkspace.trainingReviewTitle}</span>
            <small>{dictionary.teamWorkspace.trainingReviewBody}</small>
          </summary>
          <div className="team-readiness-section-body">
            {training === null ? (
              <EmptyReview
                locale={locale}
                dictionary={dictionary}
                workspace={workspace}
                section="training_requirements"
              />
            ) : training.length === 0 ? (
              <p className="intake-empty">{dictionary.teamWorkspace.reviewedEmpty}</p>
            ) : null}
            {(training ?? []).map((record) => (
              <TrainingForm
                key={record.id}
                locale={locale}
                dictionary={dictionary}
                workspace={workspace}
                record={record}
              />
            ))}
            <TrainingForm
              locale={locale}
              dictionary={dictionary}
              workspace={workspace}
              record={null}
            />
          </div>
        </details>

        <details className="team-readiness-section" open={access === null}>
          <summary>
            <span>{dictionary.teamWorkspace.accessReviewTitle}</span>
            <small>{dictionary.teamWorkspace.accessReviewBody}</small>
          </summary>
          <div className="team-readiness-section-body">
            {access === null ? (
              <EmptyReview
                locale={locale}
                dictionary={dictionary}
                workspace={workspace}
                section="access_recommendations"
              />
            ) : access.length === 0 ? (
              <p className="intake-empty">{dictionary.teamWorkspace.reviewedEmpty}</p>
            ) : null}
            {(access ?? []).map((record) => (
              <AccessForm
                key={record.id}
                locale={locale}
                dictionary={dictionary}
                workspace={workspace}
                record={record}
              />
            ))}
            <AccessForm
              locale={locale}
              dictionary={dictionary}
              workspace={workspace}
              record={null}
            />
          </div>
        </details>
      </div>
    </section>
  );
}
