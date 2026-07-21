import { LocaleSwitcher } from "@/components/locale-switcher";
import type { Dictionary, Locale } from "@/lib/i18n";
import { deriveNavigation } from "@/lib/navigation";
import type { ShellViewModel } from "@/lib/shell-view-model";

function StatePanel({ title, body, code }: { title: string; body: string; code?: string }) {
  return (
    <main id="main" className="state-panel" tabIndex={-1}>
      <p className="eyebrow">FAIL CLOSED</p>
      <h1>{title}</h1>
      <p>{body}</p>
      {code ? <code>{code}</code> : null}
    </main>
  );
}

export function CampaignShell({
  locale,
  dictionary,
  model,
}: {
  locale: Locale;
  dictionary: Dictionary;
  model: ShellViewModel;
}) {
  if (model.kind === "unauthenticated") {
    return (
      <div className="state-page">
        <LocaleSwitcher locale={locale} dictionary={dictionary} />
        <StatePanel
          title={dictionary.states.unauthenticatedTitle}
          body={dictionary.states.unauthenticatedBody}
        />
      </div>
    );
  }
  if (model.kind === "tenant_context_required") {
    return (
      <div className="state-page">
        <LocaleSwitcher locale={locale} dictionary={dictionary} />
        <StatePanel title={dictionary.states.contextTitle} body={dictionary.states.contextBody} />
      </div>
    );
  }
  if (model.kind === "unavailable") {
    const code = `${model.code}${model.correlationId ? ` · ${model.correlationId}` : ""}`;
    return (
      <div className="state-page">
        <LocaleSwitcher locale={locale} dictionary={dictionary} />
        <StatePanel
          title={dictionary.states.unavailableTitle}
          body={dictionary.states.unavailableBody}
          code={code}
        />
      </div>
    );
  }
  if (model.kind === "empty") {
    return (
      <div className="state-page">
        <LocaleSwitcher locale={locale} dictionary={dictionary} />
        <StatePanel title={dictionary.states.emptyTitle} body={dictionary.states.emptyBody} />
      </div>
    );
  }

  const navigation = deriveNavigation(locale, model.memberships);
  const readiness = model.readiness?.readiness ?? null;
  const roles = [...new Set(model.memberships.flatMap((membership) => membership.roles))];
  const grantCount = model.memberships.reduce(
    (count, membership) => count + membership.grants.length,
    0,
  );
  const limitationCodes = readiness?.limitation_codes ?? [
    "NOT_A_HUMAN_APPROVAL",
    "NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT",
  ];

  return (
    <div className="shell-grid">
      <a className="skip-link" href="#main">
        {dictionary.common.skip}
      </a>
      <aside className="sidebar" aria-label={dictionary.shell.modules}>
        <div className="brand-lockup">
          <span className="brand-mark" aria-hidden="true">
            CO
          </span>
          <div>
            <strong>{dictionary.common.product}</strong>
            <small>{model.demo ? dictionary.common.demo : dictionary.common.live}</small>
          </div>
        </div>
        <nav className="module-navigation">
          <ul>
            {navigation.map((item) => (
              <li key={item.key}>
                {item.enabled ? (
                  <a href={item.href}>{dictionary.nav[item.key]}</a>
                ) : (
                  <span aria-disabled="true">{dictionary.nav[item.key]}</span>
                )}
              </li>
            ))}
          </ul>
        </nav>
        <p className="sidebar-boundary">{dictionary.shell.authority}</p>
      </aside>

      <div className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">{dictionary.shell.eyebrow}</p>
            <p className="topbar-title">{dictionary.shell.title}</p>
          </div>
          <div className="topbar-actions">
            <span className={`mode-badge ${model.demo ? "mode-demo" : "mode-live"}`}>
              {model.demo ? dictionary.common.demo : dictionary.common.live}
            </span>
            <LocaleSwitcher locale={locale} dictionary={dictionary} />
          </div>
        </header>

        <section className="context-strip" aria-label={dictionary.shell.currentContext}>
          <div>
            <span>{dictionary.shell.tenant}</span>
            <strong>{model.identity.tenant_id}</strong>
          </div>
          <div>
            <span>{dictionary.shell.campaign}</span>
            <strong>{model.campaign.name}</strong>
          </div>
          <div>
            <span>{dictionary.shell.principal}</span>
            <strong>{model.identity.display_name ?? model.identity.subject}</strong>
          </div>
        </section>

        <main id="main" className="main-content" tabIndex={-1}>
          <section className="hero-panel">
            <div>
              <p className="eyebrow">
                {model.demo ? "SYNTHETIC DATA · NO REAL CAMPAIGN" : "SERVER-VERIFIED CONTEXT"}
              </p>
              <h1>{dictionary.shell.title}</h1>
              <p>{dictionary.shell.subtitle}</p>
            </div>
            <div className="authority-card">
              <span>HUMAN AUTHORITY</span>
              <strong>{dictionary.shell.authority}</strong>
              <small>{dictionary.common.notApproval}</small>
            </div>
          </section>

          <section className="context-details" aria-labelledby="context-title">
            <div>
              <p className="eyebrow">AUTHORIZATION CONTEXT</p>
              <h2 id="context-title">{dictionary.shell.currentContext}</h2>
            </div>
            <dl>
              <div>
                <dt>{dictionary.shell.roles}</dt>
                <dd>{roles.length ? roles.join(", ") : "—"}</dd>
              </div>
              <div>
                <dt>{dictionary.shell.authorizationFresh}</dt>
                <dd>{model.identity.evaluated_at}</dd>
              </div>
              <div>
                <dt>{dictionary.dashboard.campaignStatus}</dt>
                <dd>{model.campaign.status}</dd>
              </div>
              <div>
                <dt>{dictionary.dashboard.version}</dt>
                <dd>{model.campaign.version}</dd>
              </div>
            </dl>
          </section>

          <section className="dashboard-grid">
            <article id="readiness" className="panel readiness-panel">
              <p className="eyebrow">OPERATIONAL SETUP ONLY</p>
              <h2>{dictionary.dashboard.readinessTitle}</h2>
              <p>{dictionary.dashboard.readinessBody}</p>
              {readiness ? (
                <>
                  <div className="metric-line">
                    <strong>
                      {readiness.completed_checks}/{readiness.total_checks}
                    </strong>
                    <span>{dictionary.dashboard.checks}</span>
                  </div>
                  <ul className="check-list">
                    {readiness.checks.map((check) => (
                      <li key={check.key} data-complete={check.complete}>
                        <span aria-hidden="true">{check.complete ? "✓" : "·"}</span>
                        {check.reason_code}
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
                      <dd>{readiness.next_action}</dd>
                    </div>
                  </dl>
                </>
              ) : (
                <p className="muted">
                  {model.readinessUnavailable ? "DEPENDENCY_UNAVAILABLE" : "NOT_AUTHORIZED"}
                </p>
              )}
            </article>

            <article className="panel">
              <p className="eyebrow">EXACT GRANTS</p>
              <h2>{dictionary.dashboard.authorityTitle}</h2>
              <p>{dictionary.dashboard.authorityBody}</p>
              <div className="grant-count">
                <strong>{grantCount}</strong>
                <span>server-owned grants</span>
              </div>
            </article>

            <article id="evidence" className="panel">
              <p className="eyebrow">TRACEABILITY</p>
              <h2>{dictionary.dashboard.evidenceTitle}</h2>
              <p>{dictionary.dashboard.evidenceBody}</p>
              <dl className="compact-data">
                <div>
                  <dt>{dictionary.dashboard.auditReceipt}</dt>
                  <dd>{model.readiness?.audit_event_id ?? "—"}</dd>
                </div>
                <div>
                  <dt>{dictionary.dashboard.noExternal}</dt>
                  <dd>CONFIRMED</dd>
                </div>
              </dl>
            </article>

            <article className="panel operations-panel">
              <p className="eyebrow">GUIDED SEQUENCE</p>
              <h2>{dictionary.dashboard.operationsTitle}</h2>
              <p>{dictionary.dashboard.operationsBody}</p>
              <ol className="sequence-list">
                <li>
                  <span>01</span> Campaign metadata
                </li>
                <li>
                  <span>02</span> Governed workspace
                </li>
                <li>
                  <span>03</span> Guided intake
                </li>
                <li>
                  <span>04</span> Evidence before strategy
                </li>
              </ol>
            </article>
          </section>

          <section className="limitation-panel" aria-labelledby="limitations-title">
            <div>
              <p className="eyebrow">MANDATORY LIMITS</p>
              <h2 id="limitations-title">{dictionary.dashboard.limitations}</h2>
            </div>
            <ul>
              {limitationCodes.map((code) => (
                <li key={code}>{code}</li>
              ))}
            </ul>
          </section>
          <p className="reference-note">{dictionary.shell.reference}</p>
        </main>
      </div>
    </div>
  );
}
