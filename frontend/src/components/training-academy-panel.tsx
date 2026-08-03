import type {
  TrainingAssignmentListEvidence,
  TrainingCatalogModule,
  TrainingCatalogPath,
  TrainingCatalogProjection,
  TrainingModuleProgressProjection,
  TrainingReceiptListEvidence,
  UUID,
} from "@/lib/contracts";
import type { Dictionary, Locale } from "@/lib/i18n";
import type { TrainingCapabilities } from "@/lib/journey-capabilities";
import type { TrainingAvailability } from "@/lib/shell-view-model";

function moduleForPath(
  catalog: TrainingCatalogProjection,
  path: TrainingCatalogPath,
): TrainingCatalogModule | null {
  const first = path.modules[0];
  if (!first) return null;
  return (
    catalog.modules.find(
      (module) =>
        module.module_id === first.module_id &&
        module.version === first.version,
    ) ?? null
  );
}

function progressLabel(
  dictionary: Dictionary,
  progress: TrainingModuleProgressProjection,
): string {
  return dictionary.trainingAcademy.statusLabels[progress.status];
}

function formatDate(locale: Locale, value: string): string {
  return new Intl.DateTimeFormat(locale === "es" ? "es-GT" : "en-US", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(new Date(value));
}

function HiddenContext({
  locale,
  assignmentId,
  moduleId,
  assignmentVersion,
  progressVersion,
  digest,
}: Readonly<{
  locale: Locale;
  assignmentId: UUID;
  moduleId: string;
  assignmentVersion: number;
  progressVersion: number;
  digest: string;
}>) {
  return (
    <>
      <input type="hidden" name="locale" value={locale} />
      <input type="hidden" name="assignment_id" value={assignmentId} />
      <input type="hidden" name="module_id" value={moduleId} />
      <input
        type="hidden"
        name="expected_assignment_version"
        value={assignmentVersion}
      />
      <input
        type="hidden"
        name="expected_progress_version"
        value={progressVersion}
      />
      <input type="hidden" name="catalog_digest" value={digest} />
    </>
  );
}

function AvailablePaths({
  locale,
  dictionary,
  catalog,
  capabilities,
  demo,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  catalog: TrainingCatalogProjection;
  capabilities: TrainingCapabilities;
  demo: boolean;
}>) {
  return (
    <div className="training-path-grid">
      {catalog.paths.map((path) => {
        const trainingModule = moduleForPath(catalog, path);
        if (!trainingModule || trainingModule.status !== "APPROVED") return null;
        return (
          <article
            className="training-path-card"
            key={`${path.path_id}@${path.version}`}
          >
            <p className="eyebrow">{dictionary.trainingAcademy.pathLabel}</p>
            <h4>{trainingModule.title}</h4>
            <p>{trainingModule.summary}</p>
            <dl className="compact-data training-path-meta">
              <div>
                <dt>{dictionary.trainingAcademy.roleLabel}</dt>
                <dd>{path.role_slugs[0]?.replaceAll("_", " ") ?? "—"}</dd>
              </div>
              <div>
                <dt>{dictionary.trainingAcademy.lesson}</dt>
                <dd>{trainingModule.lessons.length}</dd>
              </div>
            </dl>
            {capabilities.canManageAssignments && !demo ? (
              <form action="/api/ui/training/assign" method="post">
                <input type="hidden" name="locale" value={locale} />
                <input type="hidden" name="path_id" value={path.path_id} />
                <input type="hidden" name="path_version" value={path.version} />
                <input
                  type="hidden"
                  name="catalog_digest"
                  value={catalog.catalog_digest}
                />
                <input
                  type="hidden"
                  name="role_slug"
                  value={path.role_slugs[0] ?? ""}
                />
                <button className="button button-secondary" type="submit">
                  {dictionary.trainingAcademy.assignAction}
                </button>
              </form>
            ) : null}
          </article>
        );
      })}
    </div>
  );
}

export function TrainingAcademyPanel({
  locale,
  dictionary,
  catalog,
  assignments,
  receipts,
  availability,
  capabilities,
  demo,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  catalog: TrainingCatalogProjection | null;
  assignments: TrainingAssignmentListEvidence | null;
  receipts: TrainingReceiptListEvidence | null;
  availability: TrainingAvailability;
  capabilities: TrainingCapabilities;
  demo: boolean;
}>) {
  if (availability === "NOT_AUTHORIZED") return null;

  const assignment = assignments?.assignments[0] ?? null;
  const currentProgress =
    assignment?.modules.find(
      (item) => item.module_id === assignment.next_module_id,
    ) ??
    assignment?.modules[0] ??
    null;
  const currentModule =
    catalog && currentProgress
      ? (catalog.modules.find(
          (item) =>
            item.module_id === currentProgress.module_id &&
            item.version === currentProgress.module_version,
        ) ?? null)
      : null;

  return (
    <section
      id="training-academy"
      className="panel training-academy-panel"
      aria-labelledby="training-academy-title"
    >
      <div className="training-academy-heading">
        <div>
          <p className="eyebrow">{dictionary.trainingAcademy.eyebrow}</p>
          <h3 id="training-academy-title">
            {dictionary.trainingAcademy.title}
          </h3>
          <p>{dictionary.trainingAcademy.body}</p>
        </div>
        {assignment ? (
          <div className="training-progress-summary">
            <strong>
              {assignment.completed_modules}/{assignment.total_modules}
            </strong>
            <span>{dictionary.trainingAcademy.modulesLabel}</span>
            <progress
              max={assignment.total_modules}
              value={assignment.completed_modules}
            >
              {assignment.completed_modules}/{assignment.total_modules}
            </progress>
          </div>
        ) : null}
      </div>

      {availability === "DEPENDENCY_UNAVAILABLE" ? (
        <p className="intake-state" role="status">
          {dictionary.trainingAcademy.unavailable}
        </p>
      ) : catalog === null ? (
        <p className="intake-state" role="status">
          {dictionary.trainingAcademy.notAuthorized}
        </p>
      ) : assignment === null ? (
        <div className="training-empty-state">
          <h4>{dictionary.trainingAcademy.noAssignmentTitle}</h4>
          <p>{dictionary.trainingAcademy.noAssignmentBody}</p>
          <AvailablePaths
            locale={locale}
            dictionary={dictionary}
            catalog={catalog}
            capabilities={capabilities}
            demo={demo}
          />
        </div>
      ) : (
        <div className="training-assignment-layout">
          <aside
            className="training-module-list"
            aria-label={dictionary.trainingAcademy.progressLabel}
          >
            <p className="eyebrow">
              {dictionary.trainingAcademy.progressLabel}
            </p>
            <ol>
              {assignment.modules.map((item) => {
                const trainingModule = catalog.modules.find(
                  (candidate) =>
                    candidate.module_id === item.module_id &&
                    candidate.version === item.module_version,
                );
                return (
                  <li key={item.id} data-status={item.status}>
                    <span>
                      {trainingModule?.title ??
                        item.module_id.replaceAll("_", " ")}
                    </span>
                    <small>{progressLabel(dictionary, item)}</small>
                  </li>
                );
              })}
            </ol>
          </aside>

          <div className="training-learning-card">
            {assignment.status === "COMPLETED" ? (
              <div className="training-complete-state">
                <p className="eyebrow">
                  {dictionary.trainingAcademy.completed}
                </p>
                <h4>{dictionary.trainingAcademy.resultPass}</h4>
              </div>
            ) : currentProgress && currentModule ? (
              <>
                <div className="training-learning-heading">
                  <div>
                    <p className="eyebrow">
                      {dictionary.trainingAcademy.nextLesson}
                    </p>
                    <h4>{currentModule.title}</h4>
                    <p>{currentModule.summary}</p>
                  </div>
                  <span className="status-chip" data-tone="neutral">
                    {progressLabel(dictionary, currentProgress)}
                  </span>
                </div>

                <div className="training-objectives">
                  <h5>{dictionary.trainingAcademy.objectives}</h5>
                  <ul>
                    {currentModule.objectives.map((objective) => (
                      <li key={objective.id}>{objective.text}</li>
                    ))}
                  </ul>
                </div>

                {currentModule.lessons.map((lesson) => (
                  <article className="training-lesson" key={lesson.id}>
                    <p className="eyebrow">
                      {dictionary.trainingAcademy.lesson}
                    </p>
                    <h5>{lesson.title}</h5>
                    <p>{lesson.body}</p>
                    <details>
                      <summary>{dictionary.trainingAcademy.sources}</summary>
                      <ul>
                        {lesson.source_refs.map((source) => (
                          <li key={source}>
                            <code>{source}</code>
                          </li>
                        ))}
                      </ul>
                    </details>
                  </article>
                ))}

                {currentProgress.status === "NOT_STARTED" &&
                capabilities.canCompleteSelf &&
                !demo ? (
                  <form action="/api/ui/training/start" method="post">
                    <HiddenContext
                      locale={locale}
                      assignmentId={assignment.id}
                      moduleId={currentProgress.module_id}
                      assignmentVersion={assignment.version}
                      progressVersion={currentProgress.version}
                      digest={assignment.catalog_digest}
                    />
                    <button className="button" type="submit">
                      {dictionary.trainingAcademy.startAction}
                    </button>
                  </form>
                ) : null}

                {currentProgress.status === "IN_PROGRESS" &&
                capabilities.canCompleteSelf &&
                !demo ? (
                  <form
                    action="/api/ui/training/attempt"
                    className="training-assessment-form"
                    method="post"
                  >
                    <HiddenContext
                      locale={locale}
                      assignmentId={assignment.id}
                      moduleId={currentProgress.module_id}
                      assignmentVersion={assignment.version}
                      progressVersion={currentProgress.version}
                      digest={assignment.catalog_digest}
                    />
                    <div className="training-assessment-heading">
                      <h5>{dictionary.trainingAcademy.assessment}</h5>
                      <p>{dictionary.trainingAcademy.assessmentHelp}</p>
                    </div>
                    {currentModule.questions.map((question) => (
                      <fieldset key={question.id}>
                        <legend>{question.prompt}</legend>
                        {question.options.map((option) => (
                          <label key={option.id}>
                            <input
                              name={`answer:${question.id}`}
                              type="radio"
                              value={option.id}
                              required
                            />
                            <span>{option.label}</span>
                          </label>
                        ))}
                      </fieldset>
                    ))}
                    <p className="training-attempt-count">
                      {dictionary.trainingAcademy.attempts}:{" "}
                      {currentProgress.attempt_count}/10
                    </p>
                    <button className="button" type="submit">
                      {dictionary.trainingAcademy.submitAction}
                    </button>
                  </form>
                ) : null}
              </>
            ) : (
              <p className="intake-state">
                {dictionary.trainingAcademy.unavailable}
              </p>
            )}
          </div>
        </div>
      )}

      <div className="training-receipts">
        <h4>{dictionary.trainingAcademy.receipts}</h4>
        {receipts && receipts.receipts.length > 0 ? (
          <ul>
            {receipts.receipts.map((receipt) => {
              const trainingModule = catalog?.modules.find(
                (item) =>
                  item.module_id === receipt.module_id &&
                  item.version === receipt.module_version,
              );
              return (
                <li key={receipt.id}>
                  <strong>
                    {trainingModule?.title ??
                      receipt.module_id.replaceAll("_", " ")}
                  </strong>
                  <span>
                    {dictionary.trainingAcademy.receiptLabel} ·{" "}
                    {formatDate(locale, receipt.completed_at)}
                  </span>
                </li>
              );
            })}
          </ul>
        ) : (
          <p className="muted">{dictionary.trainingAcademy.noReceipts}</p>
        )}
      </div>

      <p className="training-authority-boundary">
        {demo
          ? dictionary.trainingAcademy.demoBoundary
          : dictionary.trainingAcademy.boundary}
      </p>
    </section>
  );
}
