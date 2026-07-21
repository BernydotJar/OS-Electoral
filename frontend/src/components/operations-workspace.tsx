import type {
  CampaignRoadmapReadEvidence,
  WarRoomSnapshotReadEvidence,
} from "@/lib/contracts";
import type { Dictionary } from "@/lib/i18n";

type Availability =
  "AVAILABLE" | "NOT_STARTED" | "NOT_AUTHORIZED" | "DEPENDENCY_UNAVAILABLE";

function StateMessage({ message }: { message: string }) {
  return (
    <p className="intake-state" role="status">
      {message}
    </p>
  );
}

export function OperationsWorkspace({
  dictionary,
  roadmapEvidence,
  roadmapAvailability,
  snapshotEvidence,
  snapshotAvailability,
}: {
  dictionary: Dictionary;
  roadmapEvidence: CampaignRoadmapReadEvidence | null;
  roadmapAvailability: Availability;
  snapshotEvidence: WarRoomSnapshotReadEvidence | null;
  snapshotAvailability: Availability;
}) {
  const roadmap = roadmapEvidence?.roadmap ?? null;
  const snapshot = snapshotEvidence?.snapshot ?? null;
  const roadmapMessage = {
    AVAILABLE: "",
    NOT_STARTED: dictionary.operations.notStarted,
    NOT_AUTHORIZED: dictionary.operations.notAuthorized,
    DEPENDENCY_UNAVAILABLE: dictionary.operations.unavailable,
  }[roadmapAvailability];
  const snapshotMessage = {
    AVAILABLE: "",
    NOT_STARTED: dictionary.operations.snapshotNotStarted,
    NOT_AUTHORIZED: dictionary.operations.snapshotNotAuthorized,
    DEPENDENCY_UNAVAILABLE: dictionary.operations.snapshotUnavailable,
  }[snapshotAvailability];
  const taskById = new Map(
    (roadmap?.tasks ?? []).map((task) => [task.id, task]),
  );
  const decisionById = new Map(
    (roadmap?.decisions ?? []).map((item) => [item.id, item]),
  );

  return (
    <section
      id="war-room"
      className="operations-workspace-panel"
      aria-labelledby="operations-workspace-title"
    >
      <div className="intake-heading">
        <div>
          <p className="eyebrow">{dictionary.operations.eyebrow}</p>
          <h2 id="operations-workspace-title">{dictionary.operations.title}</h2>
          <p>{dictionary.operations.body}</p>
        </div>
        {roadmap ? (
          <div className="operations-version">
            <span>{dictionary.operations.roadmapVersion}</span>
            <strong>{roadmap.version}</strong>
          </div>
        ) : null}
      </div>

      {roadmap ? (
        <>
          <div className="intake-status-row">
            <div>
              <span>{dictionary.operations.status}</span>
              <strong>
                {dictionary.operations.statusLabels[roadmap.status]}
              </strong>
            </div>
            <div>
              <span>{dictionary.operations.nextAction}</span>
              <strong>
                {dictionary.operations.nextActionLabels[roadmap.next_action]}
              </strong>
            </div>
          </div>

          <div className="operations-authority-boundary" role="note">
            <strong>{dictionary.operations.authorityBoundary}</strong>
            <p>{dictionary.operations.authorityBody}</p>
            <code>{roadmap.authority_effect}</code>
          </div>

          <div className="operations-metrics">
            <article>
              <span>{dictionary.operations.readyTasks}</span>
              <strong>{roadmap.ready_task_ids.length}</strong>
            </article>
            <article>
              <span>{dictionary.operations.blockedTasks}</span>
              <strong>{roadmap.blocked_task_ids.length}</strong>
            </article>
            <article>
              <span>{dictionary.operations.blockers}</span>
              <strong>{roadmap.open_blocker_count}</strong>
            </article>
            <article>
              <span>{dictionary.operations.decisions}</span>
              <strong>{roadmap.required_decision_count}</strong>
            </article>
          </div>

          <div className="operations-layout">
            <article>
              <h3>{dictionary.operations.criticalPath}</h3>
              {roadmap.critical_path_task_ids.length === 0 ? (
                <p className="intake-empty">{dictionary.operations.noItems}</p>
              ) : (
                <ol className="operations-path">
                  {roadmap.critical_path_task_ids.map((taskId, index) => (
                    <li key={taskId}>
                      <span>{String(index + 1).padStart(2, "0")}</span>
                      <div>
                        <strong>{taskById.get(taskId)?.title ?? taskId}</strong>
                        <small>{taskById.get(taskId)?.due_date ?? "—"}</small>
                      </div>
                    </li>
                  ))}
                </ol>
              )}
            </article>

            <article>
              <h3>{dictionary.operations.readyTasks}</h3>
              {roadmap.ready_task_ids.length === 0 ? (
                <p className="intake-empty">{dictionary.operations.noItems}</p>
              ) : (
                <ul className="operations-items">
                  {roadmap.ready_task_ids.map((taskId) => (
                    <li key={taskId}>
                      {taskById.get(taskId)?.title ?? taskId}
                    </li>
                  ))}
                </ul>
              )}

              <h3>{dictionary.operations.decisions}</h3>
              {(roadmap.decisions ?? []).filter(
                (item) => item.status === "REQUIRED",
              ).length === 0 ? (
                <p className="intake-empty">{dictionary.operations.noItems}</p>
              ) : (
                <ul className="operations-items">
                  {(roadmap.decisions ?? [])
                    .filter((item) => item.status === "REQUIRED")
                    .map((item) => (
                      <li key={item.id}>
                        <strong>{item.title}</strong>
                        <small>{item.due_date}</small>
                      </li>
                    ))}
                </ul>
              )}
            </article>
          </div>

          <section
            className="war-room-snapshot"
            aria-labelledby="war-room-snapshot-title"
          >
            <div>
              <p className="eyebrow">IMMUTABLE INTERNAL EVIDENCE</p>
              <h3 id="war-room-snapshot-title">
                {dictionary.operations.snapshot}
              </h3>
            </div>
            {snapshot ? (
              <>
                <dl className="operations-snapshot-meta">
                  <div>
                    <dt>{dictionary.operations.snapshotDate}</dt>
                    <dd>{snapshot.snapshot_date}</dd>
                  </div>
                  <div>
                    <dt>{dictionary.operations.roadmapVersion}</dt>
                    <dd>{snapshot.roadmap_version}</dd>
                  </div>
                  <div>
                    <dt>{dictionary.operations.readReceipt}</dt>
                    <dd>{snapshotEvidence?.audit_event_id}</dd>
                  </div>
                </dl>
                <div className="operations-layout">
                  <article>
                    <h4>{dictionary.operations.priorities}</h4>
                    {snapshot.priorities.length === 0 ? (
                      <p className="intake-empty">
                        {dictionary.operations.noItems}
                      </p>
                    ) : (
                      <ul className="operations-items">
                        {snapshot.priorities.map((priority) => (
                          <li key={priority}>{priority}</li>
                        ))}
                      </ul>
                    )}
                  </article>
                  <article>
                    <h4>{dictionary.operations.followUp}</h4>
                    {snapshot.follow_up_notes.length === 0 ? (
                      <p className="intake-empty">
                        {dictionary.operations.noItems}
                      </p>
                    ) : (
                      <ul className="operations-items">
                        {snapshot.follow_up_notes.map((note) => (
                          <li key={note}>{note}</li>
                        ))}
                      </ul>
                    )}
                  </article>
                </div>
                {snapshot.required_decision_ids.length > 0 ? (
                  <ul className="operations-decision-receipts">
                    {snapshot.required_decision_ids.map((decisionId) => (
                      <li key={decisionId}>
                        {decisionById.get(decisionId)?.title ?? decisionId}
                      </li>
                    ))}
                  </ul>
                ) : null}
              </>
            ) : (
              <StateMessage message={snapshotMessage} />
            )}
          </section>

          <dl className="intake-evidence">
            <div>
              <dt>{dictionary.operations.readReceipt}</dt>
              <dd>{roadmapEvidence?.audit_event_id}</dd>
            </div>
            <div>
              <dt>{dictionary.operations.roadmapVersion}</dt>
              <dd>{roadmap.version}</dd>
            </div>
          </dl>
        </>
      ) : (
        <StateMessage message={roadmapMessage} />
      )}
    </section>
  );
}
