import type { CampaignReadinessProjection } from "@/lib/contracts";
import type { Dictionary } from "@/lib/i18n";

export function CampaignReadinessPanel({
  dictionary,
  readiness,
  unavailable,
}: Readonly<{
  dictionary: Dictionary;
  readiness: CampaignReadinessProjection | null;
  unavailable: boolean;
}>) {
  return (
    <section
      id="readiness"
      className="panel readiness-panel preparation-foundation-panel"
      aria-labelledby="readiness-title"
    >
      <div className="preparation-foundation-heading">
        <div>
          <p className="eyebrow">{dictionary.dashboard.readinessEyebrow}</p>
          <h2 id="readiness-title">{dictionary.dashboard.readinessTitle}</h2>
          <p>{dictionary.dashboard.readinessBody}</p>
        </div>
        {readiness ? (
          <div className="preparation-foundation-progress">
            <strong>
              {readiness.completed_checks}/{readiness.total_checks}
            </strong>
            <span>{dictionary.dashboard.checks}</span>
          </div>
        ) : null}
      </div>

      {readiness ? (
        <div className="preparation-foundation-body">
          <ul className="check-list">
            {readiness.checks.map((check) => (
              <li key={check.key} data-complete={check.complete}>
                <span aria-hidden="true">{check.complete ? "✓" : "·"}</span>
                {dictionary.dashboard.readinessCheckLabels[check.key]}
              </li>
            ))}
          </ul>
          <dl className="compact-data">
            <div>
              <dt>{dictionary.dashboard.workspaceCount}</dt>
              <dd>{readiness.active_workspace_count}</dd>
            </div>
            <div>
              <dt>{dictionary.dashboard.nextAction}</dt>
              <dd>
                {
                  dictionary.dashboard.readinessNextActionLabels[
                    readiness.next_action
                  ]
                }
              </dd>
            </div>
          </dl>
        </div>
      ) : (
        <p className="muted">
          {unavailable
            ? dictionary.states.unavailableTitle
            : dictionary.intake.notAuthorized}
        </p>
      )}
    </section>
  );
}
