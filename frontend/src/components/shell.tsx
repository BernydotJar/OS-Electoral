import { LocaleSwitcher } from "@/components/locale-switcher";
import { OperationsWorkspace } from "@/components/operations-workspace";
import type { Dictionary, Locale } from "@/lib/i18n";
import { deriveNavigation } from "@/lib/navigation";
import type { ShellViewModel } from "@/lib/shell-view-model";

function StatePanel({
  title,
  body,
  code,
}: {
  title: string;
  body: string;
  code?: string;
}) {
  return (
    <main id="main" className="state-panel" tabIndex={-1}>
      <p className="eyebrow">FAIL CLOSED</p>
      <h1>{title}</h1>
      <p>{body}</p>
      {code ? <code>{code}</code> : null}
    </main>
  );
}

function IntakeItems({
  items,
  dictionary,
}: {
  items: readonly string[] | null;
  dictionary: Dictionary;
}) {
  if (items === null)
    return <p className="intake-empty">{dictionary.intake.notAssessed}</p>;
  if (items.length === 0)
    return <p className="intake-empty">{dictionary.intake.noItems}</p>;
  return (
    <ul className="intake-items">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
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
        <StatePanel
          title={dictionary.states.contextTitle}
          body={dictionary.states.contextBody}
        />
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
        <StatePanel
          title={dictionary.states.emptyTitle}
          body={dictionary.states.emptyBody}
        />
      </div>
    );
  }

  const navigation = deriveNavigation(
    locale,
    model.memberships,
    model.campaign.id,
  );
  const readiness = model.readiness?.readiness ?? null;
  const guidedIntake = model.guidedIntake?.intake ?? null;
  const guidedIntakeStateMessage = {
    AVAILABLE: "",
    NOT_STARTED: dictionary.intake.notStarted,
    NOT_AUTHORIZED: dictionary.intake.notAuthorized,
    DEPENDENCY_UNAVAILABLE: dictionary.intake.unavailable,
  }[model.guidedIntakeAvailability];
  const candidateWorkspace = model.candidateWorkspace?.workspace ?? null;
  const candidateWorkspaceStateMessage = {
    AVAILABLE: "",
    NOT_STARTED: dictionary.candidate.notStarted,
    NOT_AUTHORIZED: dictionary.candidate.notAuthorized,
    DEPENDENCY_UNAVAILABLE: dictionary.candidate.unavailable,
  }[model.candidateWorkspaceAvailability];
  const teamWorkspace = model.teamWorkspace?.workspace ?? null;
  const teamWorkspaceStateMessage = {
    AVAILABLE: "",
    NOT_STARTED: dictionary.teamWorkspace.notStarted,
    NOT_AUTHORIZED: dictionary.teamWorkspace.notAuthorized,
    DEPENDENCY_UNAVAILABLE: dictionary.teamWorkspace.unavailable,
  }[model.teamWorkspaceAvailability];
  const roles = [
    ...new Set(model.memberships.flatMap((membership) => membership.roles)),
  ];
  const grantCount = model.memberships.reduce(
    (count, membership) => count + membership.grants.length,
    0,
  );
  const readinessLimitations = readiness?.limitation_codes ?? [
    "NOT_A_HUMAN_APPROVAL",
    "NO_STRATEGY_EVIDENCE_OR_CITIZEN_ASSESSMENT",
  ];
  const limitationCodes = [
    ...new Set([
      ...readinessLimitations,
      ...(guidedIntake?.limitation_codes ?? []),
      ...(candidateWorkspace?.limitation_codes ?? []),
      ...(teamWorkspace?.limitation_codes ?? []),
      ...(model.campaignRoadmap?.roadmap.limitation_codes ?? []),
    ]),
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
            <small>
              {model.demo ? dictionary.common.demo : dictionary.common.live}
            </small>
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
            <span
              className={`mode-badge ${model.demo ? "mode-demo" : "mode-live"}`}
            >
              {model.demo ? dictionary.common.demo : dictionary.common.live}
            </span>
            <LocaleSwitcher locale={locale} dictionary={dictionary} />
          </div>
        </header>

        <section
          className="context-strip"
          aria-label={dictionary.shell.currentContext}
        >
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
            <strong>
              {model.identity.display_name ?? model.identity.subject}
            </strong>
          </div>
        </section>

        <main id="main" className="main-content" tabIndex={-1}>
          <section className="hero-panel">
            <div>
              <p className="eyebrow">
                {model.demo
                  ? "SYNTHETIC DATA · NO REAL CAMPAIGN"
                  : "SERVER-VERIFIED CONTEXT"}
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

          <section
            id="guided-intake"
            className="guided-intake-panel"
            aria-labelledby="guided-intake-title"
          >
            <div className="intake-heading">
              <div>
                <p className="eyebrow">{dictionary.intake.eyebrow}</p>
                <h2 id="guided-intake-title">{dictionary.intake.title}</h2>
                <p>{dictionary.intake.body}</p>
              </div>
              {guidedIntake ? (
                <div
                  className="intake-progress"
                  aria-label={dictionary.intake.progress}
                >
                  <strong>
                    {guidedIntake.completed_checks}/{guidedIntake.total_checks}
                  </strong>
                  <span>{dictionary.intake.progress}</span>
                  <progress
                    max={guidedIntake.total_checks}
                    value={guidedIntake.completed_checks}
                  >
                    {guidedIntake.completed_checks}/{guidedIntake.total_checks}
                  </progress>
                </div>
              ) : null}
            </div>

            {guidedIntake ? (
              <>
                <div className="intake-status-row">
                  <div>
                    <span>{dictionary.intake.status}</span>
                    <strong>
                      {dictionary.intake.statusLabels[guidedIntake.status]}
                    </strong>
                  </div>
                  <div>
                    <span>{dictionary.intake.nextAction}</span>
                    <strong>
                      {
                        dictionary.intake.nextActionLabels[
                          guidedIntake.next_action
                        ]
                      }
                    </strong>
                  </div>
                </div>

                <div className="intake-layout">
                  <section aria-labelledby="intake-checks-title">
                    <h3 id="intake-checks-title">{dictionary.intake.checks}</h3>
                    <ol className="intake-checks">
                      {guidedIntake.checks.map((check, index) => (
                        <li key={check.key} data-complete={check.complete}>
                          <span className="intake-step" aria-hidden="true">
                            {String(index + 1).padStart(2, "0")}
                          </span>
                          <div>
                            <strong>
                              {dictionary.intake.checkLabels[check.key]}
                            </strong>
                            <code>{check.reason_code}</code>
                          </div>
                          <span
                            className="intake-check-mark"
                            aria-hidden="true"
                          >
                            {check.complete ? "✓" : "·"}
                          </span>
                        </li>
                      ))}
                    </ol>
                  </section>

                  <section aria-labelledby="intake-context-title">
                    <h3 id="intake-context-title">
                      {dictionary.shell.currentContext}
                    </h3>
                    <dl className="intake-data">
                      <div>
                        <dt>{dictionary.intake.office}</dt>
                        <dd>
                          {guidedIntake.office ?? dictionary.intake.notAssessed}
                        </dd>
                      </div>
                      <div>
                        <dt>{dictionary.intake.candidateProject}</dt>
                        <dd>
                          {guidedIntake.candidate_project ??
                            dictionary.intake.notAssessed}
                        </dd>
                      </div>
                      <div>
                        <dt>{dictionary.intake.currentTeam}</dt>
                        <dd>
                          <IntakeItems
                            items={guidedIntake.current_team}
                            dictionary={dictionary}
                          />
                        </dd>
                      </div>
                      <div>
                        <dt>{dictionary.intake.currentAssets}</dt>
                        <dd>
                          <IntakeItems
                            items={guidedIntake.current_assets}
                            dictionary={dictionary}
                          />
                        </dd>
                      </div>
                      <div>
                        <dt>{dictionary.intake.budgetStatus}</dt>
                        <dd>
                          {
                            dictionary.intake.budgetStatusLabels[
                              guidedIntake.budget_status
                            ]
                          }
                        </dd>
                      </div>
                      <div>
                        <dt>{dictionary.intake.knownUnknowns}</dt>
                        <dd>
                          <IntakeItems
                            items={guidedIntake.known_unknowns}
                            dictionary={dictionary}
                          />
                        </dd>
                      </div>
                      <div>
                        <dt>{dictionary.intake.evidenceRequirements}</dt>
                        <dd>
                          <IntakeItems
                            items={guidedIntake.evidence_requirements}
                            dictionary={dictionary}
                          />
                        </dd>
                      </div>
                    </dl>
                  </section>
                </div>

                <section
                  className="research-actions"
                  aria-labelledby="research-actions-title"
                >
                  <div>
                    <h3 id="research-actions-title">
                      {dictionary.intake.researchActions}
                    </h3>
                    <p>{dictionary.common.notApproval}</p>
                  </div>
                  {guidedIntake.research_first_actions.length > 0 ? (
                    <ol>
                      {guidedIntake.research_first_actions.map((action) => (
                        <li key={action}>
                          {dictionary.intake.researchActionLabels[action]}
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <p className="intake-empty">
                      {
                        dictionary.intake.nextActionLabels[
                          guidedIntake.next_action
                        ]
                      }
                    </p>
                  )}
                </section>

                <dl className="intake-evidence">
                  <div>
                    <dt>{dictionary.intake.readReceipt}</dt>
                    <dd>{model.guidedIntake?.audit_event_id}</dd>
                  </div>
                  <div>
                    <dt>{dictionary.intake.updatedAt}</dt>
                    <dd>{guidedIntake.updated_at}</dd>
                  </div>
                </dl>
              </>
            ) : (
              <p className="intake-state" role="status">
                {guidedIntakeStateMessage}
              </p>
            )}
          </section>

          <section
            id="candidate-workspace"
            className="candidate-workspace-panel"
            aria-labelledby="candidate-workspace-title"
          >
            <div className="intake-heading">
              <div>
                <p className="eyebrow">{dictionary.candidate.eyebrow}</p>
                <h2 id="candidate-workspace-title">
                  {dictionary.candidate.title}
                </h2>
                <p>{dictionary.candidate.body}</p>
              </div>
              {candidateWorkspace ? (
                <div
                  className="intake-progress"
                  aria-label={dictionary.candidate.progress}
                >
                  <strong>
                    {candidateWorkspace.completed_checks}/
                    {candidateWorkspace.total_checks}
                  </strong>
                  <span>{dictionary.candidate.progress}</span>
                  <progress
                    max={candidateWorkspace.total_checks}
                    value={candidateWorkspace.completed_checks}
                  >
                    {candidateWorkspace.completed_checks}/
                    {candidateWorkspace.total_checks}
                  </progress>
                </div>
              ) : null}
            </div>

            {candidateWorkspace ? (
              <>
                <div className="intake-status-row">
                  <div>
                    <span>{dictionary.candidate.status}</span>
                    <strong>
                      {
                        dictionary.candidate.statusLabels[
                          candidateWorkspace.status
                        ]
                      }
                    </strong>
                  </div>
                  <div>
                    <span>{dictionary.candidate.nextAction}</span>
                    <strong>
                      {
                        dictionary.candidate.nextActionLabels[
                          candidateWorkspace.next_action
                        ]
                      }
                    </strong>
                  </div>
                </div>

                <div className="candidate-boundary" role="note">
                  <strong>{dictionary.candidate.publicBoundary}</strong>
                  <p>{dictionary.candidate.publicBoundaryBody}</p>
                  <code>{candidateWorkspace.public_use_status}</code>
                </div>

                <div className="candidate-layout">
                  <section aria-labelledby="candidate-checks-title">
                    <h3 id="candidate-checks-title">
                      {dictionary.candidate.sections}
                    </h3>
                    <ol className="intake-checks">
                      {candidateWorkspace.checks.map((check, index) => (
                        <li key={check.key} data-complete={check.complete}>
                          <span className="intake-step" aria-hidden="true">
                            {String(index + 1).padStart(2, "0")}
                          </span>
                          <div>
                            <strong>
                              {dictionary.candidate.checkLabels[check.key]}
                            </strong>
                            <code>{check.reason_code}</code>
                          </div>
                          <span
                            className="intake-check-mark"
                            aria-hidden="true"
                          >
                            {check.complete ? "✓" : "·"}
                          </span>
                        </li>
                      ))}
                    </ol>
                  </section>

                  <section aria-labelledby="candidate-summary-title">
                    <h3 id="candidate-summary-title">
                      {candidateWorkspace.display_name}
                    </h3>
                    <div className="candidate-summary-grid">
                      <article>
                        <span>{dictionary.candidate.identity}</span>
                        <strong>
                          {candidateWorkspace.identity?.claim ??
                            dictionary.candidate.notAssessed}
                        </strong>
                      </article>
                      <article>
                        <span>{dictionary.candidate.biography}</span>
                        <strong>
                          {candidateWorkspace.biography?.claim ??
                            dictionary.candidate.notAssessed}
                        </strong>
                      </article>
                      <article>
                        <span>{dictionary.candidate.purpose}</span>
                        <strong>
                          {candidateWorkspace.purpose?.claim ??
                            dictionary.candidate.notAssessed}
                        </strong>
                      </article>
                      <article>
                        <span>{dictionary.candidate.evidenceInventory}</span>
                        <strong>{candidateWorkspace.evidence.length}</strong>
                      </article>
                      <article>
                        <span>{dictionary.candidate.approvedSections}</span>
                        <strong>
                          {candidateWorkspace.current_approved_sections.length}
                        </strong>
                      </article>
                      <article>
                        <span>{dictionary.candidate.pendingApprovals}</span>
                        <strong>
                          {candidateWorkspace.approvals_required.length}
                        </strong>
                      </article>
                      <article>
                        <span>{dictionary.candidate.criticalHighRisks}</span>
                        <strong>
                          {candidateWorkspace.open_critical_high_risks}
                        </strong>
                      </article>
                    </div>

                    <div className="candidate-detail-grid">
                      <article>
                        <h4>{dictionary.candidate.values}</h4>
                        {candidateWorkspace.values === null ? (
                          <p className="intake-empty">
                            {dictionary.candidate.notAssessed}
                          </p>
                        ) : candidateWorkspace.values.length === 0 ? (
                          <p className="intake-empty">
                            {dictionary.candidate.noItems}
                          </p>
                        ) : (
                          <ul className="intake-items">
                            {candidateWorkspace.values.map((item) => (
                              <li key={item.id}>{item.claim}</li>
                            ))}
                          </ul>
                        )}
                      </article>
                      <article>
                        <h4>{dictionary.candidate.attributes}</h4>
                        {candidateWorkspace.attributes === null ? (
                          <p className="intake-empty">
                            {dictionary.candidate.notAssessed}
                          </p>
                        ) : candidateWorkspace.attributes.length === 0 ? (
                          <p className="intake-empty">
                            {dictionary.candidate.noItems}
                          </p>
                        ) : (
                          <ul className="intake-items">
                            {candidateWorkspace.attributes.map((item) => (
                              <li key={item.id}>{item.claim}</li>
                            ))}
                          </ul>
                        )}
                      </article>
                      <article>
                        <h4>{dictionary.candidate.contradictions}</h4>
                        {candidateWorkspace.contradictions === null ? (
                          <p className="intake-empty">
                            {dictionary.candidate.notAssessed}
                          </p>
                        ) : candidateWorkspace.contradictions.length === 0 ? (
                          <p className="intake-empty">
                            {dictionary.candidate.noItems}
                          </p>
                        ) : (
                          <ul className="intake-items">
                            {candidateWorkspace.contradictions.map((item) => (
                              <li key={item.id}>{item.description}</li>
                            ))}
                          </ul>
                        )}
                      </article>
                      <article>
                        <h4>{dictionary.candidate.developmentGoals}</h4>
                        {candidateWorkspace.development_goals === null ? (
                          <p className="intake-empty">
                            {dictionary.candidate.notAssessed}
                          </p>
                        ) : candidateWorkspace.development_goals.length ===
                          0 ? (
                          <p className="intake-empty">
                            {dictionary.candidate.noItems}
                          </p>
                        ) : (
                          <ul className="intake-items">
                            {candidateWorkspace.development_goals.map(
                              (item) => (
                                <li key={item.id}>{item.objective}</li>
                              ),
                            )}
                          </ul>
                        )}
                      </article>
                      <article>
                        <h4>{dictionary.candidate.reputationRisks}</h4>
                        {candidateWorkspace.reputation_risks === null ? (
                          <p className="intake-empty">
                            {dictionary.candidate.notAssessed}
                          </p>
                        ) : candidateWorkspace.reputation_risks.length === 0 ? (
                          <p className="intake-empty">
                            {dictionary.candidate.noItems}
                          </p>
                        ) : (
                          <ul className="intake-items">
                            {candidateWorkspace.reputation_risks.map((item) => (
                              <li key={item.id}>
                                {item.severity} · {item.title}
                              </li>
                            ))}
                          </ul>
                        )}
                      </article>
                    </div>
                  </section>
                </div>

                <dl className="intake-evidence">
                  <div>
                    <dt>{dictionary.candidate.readReceipt}</dt>
                    <dd>{model.candidateWorkspace?.audit_event_id}</dd>
                  </div>
                  <div>
                    <dt>{dictionary.candidate.updatedAt}</dt>
                    <dd>{candidateWorkspace.updated_at}</dd>
                  </div>
                </dl>
              </>
            ) : (
              <p className="intake-state" role="status">
                {candidateWorkspaceStateMessage}
              </p>
            )}
          </section>

          <section
            id="team-workspace"
            className="team-workspace-panel"
            aria-labelledby="team-workspace-title"
          >
            <div className="intake-heading">
              <div>
                <p className="eyebrow">{dictionary.teamWorkspace.eyebrow}</p>
                <h2 id="team-workspace-title">
                  {dictionary.teamWorkspace.title}
                </h2>
                <p>{dictionary.teamWorkspace.body}</p>
              </div>
              {teamWorkspace ? (
                <div
                  className="intake-progress"
                  aria-label={dictionary.teamWorkspace.progress}
                >
                  <strong>
                    {teamWorkspace.completed_checks}/
                    {teamWorkspace.total_checks}
                  </strong>
                  <span>{dictionary.teamWorkspace.progress}</span>
                  <progress
                    max={teamWorkspace.total_checks}
                    value={teamWorkspace.completed_checks}
                  >
                    {teamWorkspace.completed_checks}/
                    {teamWorkspace.total_checks}
                  </progress>
                </div>
              ) : null}
            </div>

            {teamWorkspace ? (
              <>
                <div className="intake-status-row">
                  <div>
                    <span>{dictionary.teamWorkspace.status}</span>
                    <strong>
                      {
                        dictionary.teamWorkspace.statusLabels[
                          teamWorkspace.status
                        ]
                      }
                    </strong>
                  </div>
                  <div>
                    <span>{dictionary.teamWorkspace.nextAction}</span>
                    <strong>
                      {
                        dictionary.teamWorkspace.nextActionLabels[
                          teamWorkspace.next_action
                        ]
                      }
                    </strong>
                  </div>
                </div>

                <div className="team-authority-boundary" role="note">
                  <strong>{dictionary.teamWorkspace.authorityBoundary}</strong>
                  <p>{dictionary.teamWorkspace.authorityBody}</p>
                  <code>{teamWorkspace.authority_effect}</code>
                </div>

                <div className="team-metrics">
                  <article>
                    <span>{dictionary.teamWorkspace.filledRoles}</span>
                    <strong>{teamWorkspace.filled_role_count}</strong>
                  </article>
                  <article>
                    <span>{dictionary.teamWorkspace.vacantRoles}</span>
                    <strong>{teamWorkspace.vacant_role_count}</strong>
                  </article>
                  <article>
                    <span>{dictionary.teamWorkspace.capacity}</span>
                    <strong>
                      {teamWorkspace.total_weekly_capacity_hours}{" "}
                      {dictionary.teamWorkspace.hours}
                    </strong>
                  </article>
                </div>

                <div className="team-layout">
                  <section aria-labelledby="team-checks-title">
                    <h3 id="team-checks-title">
                      {dictionary.teamWorkspace.progress}
                    </h3>
                    <ol className="intake-checks">
                      {teamWorkspace.checks.map((check, index) => (
                        <li key={check.key} data-complete={check.complete}>
                          <span className="intake-step" aria-hidden="true">
                            {String(index + 1).padStart(2, "0")}
                          </span>
                          <div>
                            <strong>
                              {dictionary.teamWorkspace.checkLabels[check.key]}
                            </strong>
                            <code>{check.reason_code}</code>
                          </div>
                          <span
                            className="intake-check-mark"
                            aria-hidden="true"
                          >
                            {check.complete ? "✓" : "·"}
                          </span>
                        </li>
                      ))}
                    </ol>
                  </section>

                  <section aria-labelledby="team-roles-title">
                    <h3 id="team-roles-title">
                      {dictionary.teamWorkspace.roles}
                    </h3>
                    {teamWorkspace.roles === null ? (
                      <p className="intake-empty">
                        {dictionary.teamWorkspace.notAssessed}
                      </p>
                    ) : teamWorkspace.roles.length === 0 ? (
                      <p className="intake-empty">
                        {dictionary.teamWorkspace.noItems}
                      </p>
                    ) : (
                      <div className="team-role-grid">
                        {teamWorkspace.roles.map((role) => (
                          <article key={role.id} data-status={role.status}>
                            <div>
                              <span>{role.area}</span>
                              <h4>{role.title}</h4>
                            </div>
                            <p>{role.purpose}</p>
                            <dl>
                              <div>
                                <dt>{dictionary.teamWorkspace.capacity}</dt>
                                <dd>
                                  {role.weekly_capacity_hours === null
                                    ? "—"
                                    : `${role.weekly_capacity_hours} ${dictionary.teamWorkspace.hours}`}
                                </dd>
                              </div>
                              <div>
                                <dt>{dictionary.teamWorkspace.status}</dt>
                                <dd>{role.status}</dd>
                              </div>
                            </dl>
                            {role.vacancy_plan ? (
                              <p className="team-vacancy-plan">
                                {role.vacancy_plan}
                              </p>
                            ) : null}
                          </article>
                        ))}
                      </div>
                    )}
                  </section>
                </div>

                <div className="team-detail-grid">
                  <article>
                    <h3>{dictionary.teamWorkspace.workItems}</h3>
                    {teamWorkspace.work_items === null ? (
                      <p className="intake-empty">
                        {dictionary.teamWorkspace.notAssessed}
                      </p>
                    ) : teamWorkspace.work_items.length === 0 ? (
                      <p className="intake-empty">
                        {dictionary.teamWorkspace.noItems}
                      </p>
                    ) : (
                      <ul className="team-work-items">
                        {teamWorkspace.work_items.map((item) => (
                          <li key={item.id}>
                            <strong>{item.name}</strong>
                            <p>{item.description}</p>
                            <ul>
                              {item.assignments.map((assignment) => {
                                const role = teamWorkspace.roles?.find(
                                  (candidate) =>
                                    candidate.id === assignment.role_id,
                                );
                                return (
                                  <li
                                    key={`${item.id}-${assignment.role_id}-${assignment.responsibility}`}
                                  >
                                    <span>
                                      {
                                        dictionary.teamWorkspace
                                          .responsibilityLabels[
                                          assignment.responsibility
                                        ]
                                      }
                                    </span>
                                    {role?.title ?? assignment.role_id}
                                  </li>
                                );
                              })}
                            </ul>
                          </li>
                        ))}
                      </ul>
                    )}
                  </article>
                  <article>
                    <h3>{dictionary.teamWorkspace.training}</h3>
                    {teamWorkspace.training_requirements === null ? (
                      <p className="intake-empty">
                        {dictionary.teamWorkspace.notAssessed}
                      </p>
                    ) : teamWorkspace.training_requirements.length === 0 ? (
                      <p className="intake-empty">
                        {dictionary.teamWorkspace.noItems}
                      </p>
                    ) : (
                      <ul className="intake-items">
                        {teamWorkspace.training_requirements.map((item) => (
                          <li key={item.id}>
                            {item.status} · {item.title}
                          </li>
                        ))}
                      </ul>
                    )}
                  </article>
                  <article>
                    <h3>{dictionary.teamWorkspace.accessRecommendations}</h3>
                    {teamWorkspace.access_recommendations === null ? (
                      <p className="intake-empty">
                        {dictionary.teamWorkspace.notAssessed}
                      </p>
                    ) : teamWorkspace.access_recommendations.length === 0 ? (
                      <p className="intake-empty">
                        {dictionary.teamWorkspace.noItems}
                      </p>
                    ) : (
                      <ul className="intake-items">
                        {teamWorkspace.access_recommendations.map((item) => (
                          <li key={item.id}>
                            {item.status} · {item.action} · {item.resource_type}{" "}
                            · {item.purpose}
                          </li>
                        ))}
                      </ul>
                    )}
                  </article>
                </div>

                <dl className="intake-evidence">
                  <div>
                    <dt>{dictionary.teamWorkspace.readReceipt}</dt>
                    <dd>{model.teamWorkspace?.audit_event_id}</dd>
                  </div>
                  <div>
                    <dt>{dictionary.teamWorkspace.updatedAt}</dt>
                    <dd>{teamWorkspace.updated_at}</dd>
                  </div>
                </dl>
              </>
            ) : (
              <p className="intake-state" role="status">
                {teamWorkspaceStateMessage}
              </p>
            )}
          </section>

          <OperationsWorkspace
            dictionary={dictionary}
            roadmapEvidence={model.campaignRoadmap}
            roadmapAvailability={model.campaignRoadmapAvailability}
            snapshotEvidence={model.warRoomSnapshot}
            snapshotAvailability={model.warRoomSnapshotAvailability}
          />

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
                        <span aria-hidden="true">
                          {check.complete ? "✓" : "·"}
                        </span>
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
                  {model.readinessUnavailable
                    ? "DEPENDENCY_UNAVAILABLE"
                    : "NOT_AUTHORIZED"}
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

          <section
            className="limitation-panel"
            aria-labelledby="limitations-title"
          >
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
