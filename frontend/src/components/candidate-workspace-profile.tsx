import type { CandidateWorkspaceProjection } from "@/lib/contracts";
import type { Dictionary } from "@/lib/i18n";

function EmptyValue({ dictionary }: { dictionary: Dictionary }) {
  return <p className="intake-empty">{dictionary.candidate.notAssessed}</p>;
}

export function CandidateWorkspaceProfile({
  dictionary,
  workspace,
}: Readonly<{
  dictionary: Dictionary;
  workspace: CandidateWorkspaceProjection;
}>) {
  return (
    <div className="candidate-profile-view">
      <div className="intake-status-row">
        <div>
          <span>{dictionary.candidate.status}</span>
          <strong>{dictionary.candidate.statusLabels[workspace.status]}</strong>
        </div>
        <div>
          <span>{dictionary.candidate.nextAction}</span>
          <strong>
            {dictionary.candidate.nextActionLabels[workspace.next_action]}
          </strong>
        </div>
      </div>

      <div className="candidate-boundary" role="note">
        <strong>{dictionary.candidate.publicBoundary}</strong>
        <p>{dictionary.candidate.publicBoundaryBody}</p>
        <code>{workspace.public_use_status}</code>
      </div>

      <section aria-labelledby="candidate-profile-checks-title">
        <h3 id="candidate-profile-checks-title">{dictionary.candidate.sections}</h3>
        <ol className="intake-checks">
          {workspace.checks.map((check, index) => (
            <li key={check.key} data-complete={check.complete}>
              <span className="intake-step" aria-hidden="true">
                {String(index + 1).padStart(2, "0")}
              </span>
              <div>
                <strong>{dictionary.candidate.checkLabels[check.key]}</strong>
                <small className="intake-check-state">
                  {check.complete
                    ? dictionary.intake.checkComplete
                    : dictionary.intake.checkPending}
                </small>
              </div>
              <span className="intake-check-mark" aria-hidden="true">
                {check.complete ? "✓" : "·"}
              </span>
            </li>
          ))}
        </ol>
      </section>

      <div className="candidate-summary-grid">
        <article>
          <span>{dictionary.candidate.identity}</span>
          <strong>{workspace.identity?.claim ?? dictionary.candidate.notAssessed}</strong>
        </article>
        <article>
          <span>{dictionary.candidate.biography}</span>
          <strong>{workspace.biography?.claim ?? dictionary.candidate.notAssessed}</strong>
        </article>
        <article>
          <span>{dictionary.candidate.purpose}</span>
          <strong>{workspace.purpose?.claim ?? dictionary.candidate.notAssessed}</strong>
        </article>
        <article>
          <span>{dictionary.candidate.evidenceInventory}</span>
          <strong>{workspace.evidence.length}</strong>
        </article>
        <article>
          <span>{dictionary.candidate.approvedSections}</span>
          <strong>{workspace.current_approved_sections.length}</strong>
        </article>
        <article>
          <span>{dictionary.candidate.pendingApprovals}</span>
          <strong>{workspace.approvals_required.length}</strong>
        </article>
        <article>
          <span>{dictionary.candidate.criticalHighRisks}</span>
          <strong>{workspace.open_critical_high_risks}</strong>
        </article>
      </div>

      <div className="candidate-detail-grid">
        <article>
          <h4>{dictionary.candidate.values}</h4>
          {workspace.values === null ? (
            <EmptyValue dictionary={dictionary} />
          ) : workspace.values.length === 0 ? (
            <p className="intake-empty">{dictionary.candidate.noItems}</p>
          ) : (
            <ul className="intake-items">
              {workspace.values.map((item) => (
                <li key={item.id}>{item.claim}</li>
              ))}
            </ul>
          )}
        </article>
        <article>
          <h4>{dictionary.candidate.attributes}</h4>
          {workspace.attributes === null ? (
            <EmptyValue dictionary={dictionary} />
          ) : workspace.attributes.length === 0 ? (
            <p className="intake-empty">{dictionary.candidate.noItems}</p>
          ) : (
            <ul className="intake-items">
              {workspace.attributes.map((item) => (
                <li key={item.id}>{item.claim}</li>
              ))}
            </ul>
          )}
        </article>
        <article>
          <h4>{dictionary.candidate.contradictions}</h4>
          {workspace.contradictions === null ? (
            <EmptyValue dictionary={dictionary} />
          ) : workspace.contradictions.length === 0 ? (
            <p className="intake-empty">{dictionary.candidate.noItems}</p>
          ) : (
            <ul className="intake-items">
              {workspace.contradictions.map((item) => (
                <li key={item.id}>{item.description}</li>
              ))}
            </ul>
          )}
        </article>
        <article>
          <h4>{dictionary.candidate.developmentGoals}</h4>
          {workspace.development_goals === null ? (
            <EmptyValue dictionary={dictionary} />
          ) : workspace.development_goals.length === 0 ? (
            <p className="intake-empty">{dictionary.candidate.noItems}</p>
          ) : (
            <ul className="intake-items">
              {workspace.development_goals.map((item) => (
                <li key={item.id}>{item.objective}</li>
              ))}
            </ul>
          )}
        </article>
        <article>
          <h4>{dictionary.candidate.reputationRisks}</h4>
          {workspace.reputation_risks === null ? (
            <EmptyValue dictionary={dictionary} />
          ) : workspace.reputation_risks.length === 0 ? (
            <p className="intake-empty">{dictionary.candidate.noItems}</p>
          ) : (
            <ul className="intake-items">
              {workspace.reputation_risks.map((item) => (
                <li key={item.id}>
                  {item.severity} · {item.title}
                </li>
              ))}
            </ul>
          )}
        </article>
      </div>
    </div>
  );
}
