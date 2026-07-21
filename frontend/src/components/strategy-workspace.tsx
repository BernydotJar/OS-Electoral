import type { StrategyWorkspaceReadEvidence } from "@/lib/contracts";
import type { Dictionary } from "@/lib/i18n";

type Availability =
  "AVAILABLE" | "NOT_STARTED" | "NOT_AUTHORIZED" | "DEPENDENCY_UNAVAILABLE";

export function StrategyWorkspace({
  dictionary,
  evidence,
  availability,
}: {
  dictionary: Dictionary;
  evidence: StrategyWorkspaceReadEvidence | null;
  availability: Availability;
}) {
  const workspace = evidence?.workspace ?? null;
  const stateMessage = {
    AVAILABLE: "",
    NOT_STARTED: dictionary.strategyRoom.notStarted,
    NOT_AUTHORIZED: dictionary.strategyRoom.notAuthorized,
    DEPENDENCY_UNAVAILABLE: dictionary.strategyRoom.unavailable,
  }[availability];

  return (
    <section
      id="strategy-room"
      className="strategy-workspace-panel"
      aria-labelledby="strategy-workspace-title"
    >
      <div className="intake-heading">
        <div>
          <p className="eyebrow">{dictionary.strategyRoom.eyebrow}</p>
          <h2 id="strategy-workspace-title">{dictionary.strategyRoom.title}</h2>
          <p>{dictionary.strategyRoom.body}</p>
        </div>
        {workspace ? (
          <div className="operations-version">
            <span>{dictionary.strategyRoom.version}</span>
            <strong>{workspace.version}</strong>
          </div>
        ) : null}
      </div>

      {workspace ? (
        <>
          <div className="intake-status-row">
            <div>
              <span>{dictionary.strategyRoom.status}</span>
              <strong>
                {dictionary.strategyRoom.statusLabels[workspace.status]}
              </strong>
            </div>
            <div>
              <span>{dictionary.strategyRoom.nextAction}</span>
              <strong>
                {
                  dictionary.strategyRoom.nextActionLabels[
                    workspace.next_action
                  ]
                }
              </strong>
            </div>
          </div>

          <div className="strategy-authority-boundary" role="note">
            <div>
              <strong>{dictionary.strategyRoom.authorityBoundary}</strong>
              <p>{dictionary.strategyRoom.authorityBody}</p>
            </div>
            <div>
              <span>{dictionary.strategyRoom.humanDecision}</span>
              <code>{workspace.authority_effect}</code>
            </div>
          </div>

          <div
            className="strategy-evidence-summary"
            aria-label={dictionary.strategyRoom.evidence}
          >
            <article data-classification="verified">
              <span>{dictionary.strategyRoom.verified}</span>
              <strong>{workspace.verified_evidence_count}</strong>
            </article>
            <article data-classification="inferred">
              <span>{dictionary.strategyRoom.inferred}</span>
              <strong>{workspace.inferred_evidence_count}</strong>
            </article>
            <article data-classification="unknown">
              <span>{dictionary.strategyRoom.unknown}</span>
              <strong>{workspace.unknown_evidence_count}</strong>
            </article>
            <article>
              <span>{dictionary.strategyRoom.contradictions}</span>
              <strong>{workspace.open_contradiction_count}</strong>
            </article>
            <article>
              <span>{dictionary.strategyRoom.findings}</span>
              <strong>{workspace.open_high_risk_count}</strong>
            </article>
          </div>

          <div className="strategy-comparison-grid">
            <section aria-labelledby="strategy-options-title">
              <h3 id="strategy-options-title">
                {dictionary.strategyRoom.options}
              </h3>
              {(workspace.options ?? []).length === 0 ? (
                <p className="intake-empty">
                  {dictionary.strategyRoom.noItems}
                </p>
              ) : (
                <div className="strategy-options">
                  {(workspace.options ?? []).map((option) => (
                    <article key={option.id}>
                      <h4>{option.title}</h4>
                      <p>{option.summary}</p>
                      <dl>
                        <div>
                          <dt>{dictionary.strategyRoom.benefits}</dt>
                          <dd>{option.benefits.join(" · ")}</dd>
                        </div>
                        <div>
                          <dt>{dictionary.strategyRoom.risks}</dt>
                          <dd>{option.risks.join(" · ")}</dd>
                        </div>
                        <div>
                          <dt>{dictionary.strategyRoom.tradeoffs}</dt>
                          <dd>{option.tradeoffs.join(" · ")}</dd>
                        </div>
                      </dl>
                    </article>
                  ))}
                </div>
              )}
            </section>

            <section aria-labelledby="strategy-objectives-title">
              <h3 id="strategy-objectives-title">
                {dictionary.strategyRoom.objectives}
              </h3>
              {(workspace.objectives ?? []).length === 0 ? (
                <p className="intake-empty">
                  {dictionary.strategyRoom.noItems}
                </p>
              ) : (
                <ol className="strategy-objectives">
                  {(workspace.objectives ?? []).map((objective) => (
                    <li key={objective.id}>
                      <strong>{objective.outcome}</strong>
                      <dl>
                        <div>
                          <dt>{dictionary.strategyRoom.metric}</dt>
                          <dd>{objective.metric}</dd>
                        </div>
                        <div>
                          <dt>{dictionary.strategyRoom.target}</dt>
                          <dd>
                            {objective.baseline} → {objective.target}
                          </dd>
                        </div>
                        <div>
                          <dt>{dictionary.strategyRoom.deadline}</dt>
                          <dd>{objective.deadline}</dd>
                        </div>
                      </dl>
                    </li>
                  ))}
                </ol>
              )}
            </section>
          </div>

          {workspace.decision ? (
            <section
              className="strategy-decision"
              aria-labelledby="strategy-decision-title"
            >
              <div>
                <p className="eyebrow">VERSION-BOUND HUMAN RECEIPT</p>
                <h3 id="strategy-decision-title">
                  {dictionary.strategyRoom.decision}
                </h3>
              </div>
              <p>{workspace.decision.reason}</p>
              <dl>
                <div>
                  <dt>{dictionary.strategyRoom.version}</dt>
                  <dd>{workspace.decision.workspace_version}</dd>
                </div>
                <div>
                  <dt>{dictionary.strategyRoom.readReceipt}</dt>
                  <dd>{workspace.decision.approval_receipt_id}</dd>
                </div>
              </dl>
            </section>
          ) : null}

          <dl className="intake-evidence">
            <div>
              <dt>{dictionary.strategyRoom.readReceipt}</dt>
              <dd>{evidence?.audit_event_id}</dd>
            </div>
            <div>
              <dt>{dictionary.strategyRoom.version}</dt>
              <dd>{workspace.version}</dd>
            </div>
          </dl>
        </>
      ) : (
        <p className="intake-state" role="status">
          {stateMessage}
        </p>
      )}
    </section>
  );
}
