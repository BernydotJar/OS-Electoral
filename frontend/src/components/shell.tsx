import { CampaignChapterNavigation } from "@/components/campaign-chapter-navigation";
import { ChapterOrientation } from "@/components/chapter-orientation";
import { CampaignReadinessPanel } from "@/components/campaign-readiness-panel";
import { CampaignLaunchRoadmap } from "@/components/campaign-launch-roadmap";
import { CandidateOverviewPanel } from "@/components/candidate-overview-panel";
import { CandidateWorkspaceCompletion } from "@/components/candidate-workspace-completion";
import { CandidateWorkspaceDeck } from "@/components/candidate-workspace-deck";
import { CandidateWorkspaceProfile } from "@/components/candidate-workspace-profile";
import { CandidateWorkspaceEditor } from "@/components/candidate-workspace-editor";
import {
  CampaignContextForm,
  GuidedIntakeEditor,
} from "@/components/functional-onboarding";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { NoticeDismissLink } from "@/components/notice-dismiss-link";
import { OperationsWorkspace } from "@/components/operations-workspace";
import { StrategyWorkspace } from "@/components/strategy-workspace";
import { TeamOperationsBoard } from "@/components/team-operations-board";
import { TeamOperationsDeck } from "@/components/team-operations-deck";
import { TeamRoleDossier } from "@/components/team-role-dossier";
import { TeamWorkItemEditor } from "@/components/team-work-item-editor";
import { TeamWorkspaceEditor } from "@/components/team-workspace-editor";
import { TrainingAcademyPanel } from "@/components/training-academy-panel";
import {
  campaignChapterHref,
  resolveCampaignChapter,
} from "@/lib/campaign-chapters";
import { deriveCampaignJourney } from "@/lib/campaign-journey";
import type { CampaignJourneyPhaseKey } from "@/lib/campaign-journey";
import type { Dictionary, Locale } from "@/lib/i18n";
import {
  deriveCampaignContextCapabilities,
  deriveCandidateWorkspaceCapabilities,
  deriveGuidedIntakeCapabilities,
  deriveTeamWorkspaceCapabilities,
  deriveTrainingCapabilities,
} from "@/lib/journey-capabilities";
import { deriveNavigation } from "@/lib/navigation";
import type { ShellViewModel } from "@/lib/shell-view-model";
import type { UiNotice } from "@/lib/ui-notices";
import { ViewTransition } from "react";

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

function ChapterSurface({
  chapter,
  children,
}: Readonly<{
  chapter: CampaignJourneyPhaseKey;
  children: React.ReactNode;
}>) {
  return (
    <ViewTransition
      name="campaign-chapter-content"
      enter={{
        "chapter-forward": "chapter-forward",
        "chapter-back": "chapter-back",
        default: "none",
      }}
      exit={{
        "chapter-forward": "chapter-forward",
        "chapter-back": "chapter-back",
        default: "none",
      }}
      default="none"
    >
      <div className="chapter-route-content" data-chapter={chapter}>
        {children}
      </div>
    </ViewTransition>
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
  notice = null,
  selectedChapter = null,
}: {
  locale: Locale;
  dictionary: Dictionary;
  model: ShellViewModel;
  notice?: UiNotice | null;
  selectedChapter?: CampaignJourneyPhaseKey | null;
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
    const emptyContextCapabilities = deriveCampaignContextCapabilities(
      model.identity.application_memberships,
      model.identity.tenant_id,
    );
    if (!emptyContextCapabilities.canCreateCampaign) {
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
    return (
      <div className="state-page">
        <LocaleSwitcher locale={locale} dictionary={dictionary} />
        <main id="main" className="empty-campaign-page" tabIndex={-1}>
          <CampaignContextForm
            locale={locale}
            dictionary={dictionary}
            campaigns={[]}
            currentCampaignId=""
            canCreateCampaign
            demo={false}
          />
        </main>
      </div>
    );
  }

  const navigation = deriveNavigation(
    locale,
    model.memberships,
    model.campaign.id,
  ).filter((item) => item.enabled);
  const campaignContextCapabilities = deriveCampaignContextCapabilities(
    model.memberships,
    model.identity.tenant_id,
  );
  const intakeCapabilities = deriveGuidedIntakeCapabilities(
    model.memberships,
    model.campaign.id,
  );
  const candidateCapabilities = deriveCandidateWorkspaceCapabilities(
    model.memberships,
    model.campaign.id,
  );
  const teamCapabilities = deriveTeamWorkspaceCapabilities(
    model.memberships,
    model.campaign.id,
  );
  const trainingCapabilities = deriveTrainingCapabilities(
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
  const candidatePrerequisiteReady =
    guidedIntake?.status === "READY_FOR_RESEARCH";
  const candidateWorkspaceStateMessage = {
    AVAILABLE: "",
    NOT_STARTED: candidatePrerequisiteReady
      ? dictionary.candidate.notStarted
      : dictionary.candidate.prerequisitePending,
    NOT_AUTHORIZED: dictionary.candidate.notAuthorized,
    DEPENDENCY_UNAVAILABLE: dictionary.candidate.unavailable,
  }[model.candidateWorkspaceAvailability];
  const teamWorkspace = model.teamWorkspace?.workspace ?? null;
  const teamPrerequisiteReady = candidateWorkspace !== null;
  const teamPreparationAvailable =
    model.teamWorkspaceAvailability === "AVAILABLE" ||
    (model.teamWorkspaceAvailability === "NOT_STARTED" &&
      teamCapabilities.canStart &&
      teamPrerequisiteReady);
  const teamWorkspaceStateMessage = {
    AVAILABLE: "",
    NOT_STARTED: teamPrerequisiteReady
      ? dictionary.teamWorkspace.notStarted
      : dictionary.teamWorkspace.prerequisitePending,
    NOT_AUTHORIZED: dictionary.teamWorkspace.notAuthorized,
    DEPENDENCY_UNAVAILABLE: dictionary.teamWorkspace.unavailable,
  }[model.teamWorkspaceAvailability];
  const campaignJourney = deriveCampaignJourney({
    readinessStatus: readiness?.status ?? null,
    intakeStatus: guidedIntake?.status ?? null,
    candidateStatus: candidateWorkspace?.status ?? null,
    teamStatus: teamWorkspace?.status ?? null,
    strategyStatus: model.strategyWorkspace?.workspace.status ?? null,
    operationsStatus: model.campaignRoadmap?.roadmap.status ?? null,
    availablePhases: {
      foundation:
        model.guidedIntakeAvailability === "AVAILABLE" ||
        model.guidedIntakeAvailability === "NOT_STARTED",
      evidence:
        model.candidateWorkspaceAvailability === "AVAILABLE" ||
        (model.candidateWorkspaceAvailability === "NOT_STARTED" &&
          candidateCapabilities.canStart &&
          candidatePrerequisiteReady),
      team: teamPreparationAvailable,
      strategy: model.strategyWorkspaceAvailability === "AVAILABLE",
      operations: model.campaignRoadmapAvailability === "AVAILABLE",
    },
    parallelPreparation: {
      team: teamPreparationAvailable && teamPrerequisiteReady,
    },
  });
  const currentJourneyPhase = resolveCampaignChapter(
    campaignJourney,
    selectedChapter,
  );
  const chapterRouteActive = selectedChapter !== null;
  const requestedLockedChapter =
    selectedChapter !== null && currentJourneyPhase.key !== selectedChapter;
  const chapterTitle = {
    foundation: dictionary.nav.intake,
    evidence: dictionary.nav.candidate,
    team: dictionary.nav.team,
    strategy: dictionary.nav.strategy,
    operations: dictionary.nav.warRoom,
  }[currentJourneyPhase.key];
  const cleanCurrentHref = chapterRouteActive
    ? campaignChapterHref(locale, currentJourneyPhase.key)
    : `/${locale}`;

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
      ...(model.strategyWorkspace?.workspace.limitation_codes ?? []),
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
            <small>{model.campaign.jurisdiction}</small>
          </div>
        </div>
        <nav className="module-navigation">
          <ul>
            {navigation.map((item) => (
              <li key={item.key}>
                <a href={item.href}>{dictionary.nav[item.key]}</a>
              </li>
            ))}
          </ul>
        </nav>
        <p className="sidebar-boundary">{dictionary.shell.authority}</p>
      </aside>

      <div className="workspace">
        <header
          className={`topbar ${chapterRouteActive ? "topbar-compact" : "topbar-overview"}`}
        >
          {chapterRouteActive ? (
            <>
              <div className="topbar-context">
                <span className="topbar-context-step" aria-hidden="true">
                  {String(
                    campaignJourney.phases.findIndex(
                      (phase) => phase.key === currentJourneyPhase.key,
                    ) + 1,
                  ).padStart(2, "0")}
                </span>
                <div>
                  <p className="topbar-title">{chapterTitle}</p>
                  <p className="topbar-subtitle">
                    {
                      dictionary.journey.phaseDescriptions[
                        currentJourneyPhase.key
                      ]
                    }
                  </p>
                </div>
              </div>
              <div className="topbar-actions">
                <details className="session-context-menu">
                  <summary>
                    <span
                      className={`session-state-dot ${model.demo ? "session-read-only" : "session-live"}`}
                      aria-hidden="true"
                    />
                    <span>{dictionary.shell.sessionContext}</span>
                  </summary>
                  <dl>
                    <div>
                      <dt>{dictionary.shell.tenant}</dt>
                      <dd>{model.identity.tenant_id}</dd>
                    </div>
                    <div>
                      <dt>{dictionary.shell.campaign}</dt>
                      <dd>{model.campaign.name}</dd>
                    </div>
                    <div>
                      <dt>{dictionary.shell.principal}</dt>
                      <dd>
                        {model.identity.display_name ?? model.identity.subject}
                      </dd>
                    </div>
                    <div>
                      <dt>{dictionary.shell.sessionState}</dt>
                      <dd>
                        {model.demo
                          ? dictionary.common.readOnly
                          : dictionary.common.live}
                      </dd>
                    </div>
                  </dl>
                </details>
                <LocaleSwitcher locale={locale} dictionary={dictionary} />
              </div>
            </>
          ) : (
            <>
              <div>
                <p className="eyebrow">{dictionary.shell.eyebrow}</p>
                <p className="topbar-title">{dictionary.shell.title}</p>
              </div>
              <div className="topbar-actions">
                {!model.demo ? (
                  <span className="mode-badge mode-live">
                    {dictionary.common.live}
                  </span>
                ) : null}
                <LocaleSwitcher locale={locale} dictionary={dictionary} />
              </div>
            </>
          )}
        </header>

        {chapterRouteActive ? null : (
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
        )}

        <main id="main" className="main-content" tabIndex={-1}>
          {notice ? (
            <div
              className="notice-banner"
              data-notice={notice}
              role="status"
              aria-live="polite"
            >
              <span className="notice-indicator" aria-hidden="true" />
              <p>{dictionary.notices[notice]}</p>
              <NoticeDismissLink
                fallbackHref={cleanCurrentHref}
                label={dictionary.shell.dismissNotice}
              />
            </div>
          ) : null}
          {chapterRouteActive ? null : (
            <CampaignLaunchRoadmap
              locale={locale}
              dictionary={dictionary}
              journey={campaignJourney}
            />
          )}

          {chapterRouteActive ? (
            <>
              {requestedLockedChapter ? (
                <p className="chapter-route-notice" role="status">
                  {dictionary.journey.chapterUnavailable}
                </p>
              ) : null}
              <CampaignChapterNavigation
                locale={locale}
                dictionary={dictionary}
                journey={campaignJourney}
                selected={currentJourneyPhase}
              />
              <ChapterOrientation
                dictionary={dictionary}
                journey={campaignJourney}
                selected={currentJourneyPhase}
              />
            </>
          ) : null}

          {chapterRouteActive ? null : (
            <>
              <CampaignContextForm
                locale={locale}
                dictionary={dictionary}
                campaigns={model.campaigns}
                currentCampaignId={model.campaign.id}
                canCreateCampaign={
                  campaignContextCapabilities.canCreateCampaign
                }
                demo={model.demo}
              />

              <details className="context-details technical-details">
                <summary>{dictionary.shell.technicalDetails}</summary>
                <div>
                  <p className="eyebrow">
                    {dictionary.shell.authorizationContext}
                  </p>
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
              </details>
            </>
          )}

          {chapterRouteActive && currentJourneyPhase.key === "foundation" ? (
            <ChapterSurface chapter="foundation">
              <CampaignReadinessPanel
                dictionary={dictionary}
                readiness={readiness}
                unavailable={model.readinessUnavailable}
              />
              <section
                id="guided-intake"
                className="guided-intake-panel"
                aria-labelledby="guided-intake-title"
                data-complete={guidedIntake?.status === "READY_FOR_RESEARCH"}
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
                        {guidedIntake.completed_checks}/
                        {guidedIntake.total_checks}
                      </strong>
                      <span>{dictionary.intake.progress}</span>
                      <progress
                        max={guidedIntake.total_checks}
                        value={guidedIntake.completed_checks}
                      >
                        {guidedIntake.completed_checks}/
                        {guidedIntake.total_checks}
                      </progress>
                    </div>
                  ) : null}
                </div>

                <details
                  className="guided-intake-review"
                  open={guidedIntake?.status !== "READY_FOR_RESEARCH"}
                >
                  <summary>
                    <span>{dictionary.intake.completedTitle}</span>
                    <small>{dictionary.intake.completedBody}</small>
                  </summary>
                  <div className="guided-intake-review-body">
                    <GuidedIntakeEditor
                      locale={locale}
                      dictionary={dictionary}
                      demo={model.demo}
                      availability={model.guidedIntakeAvailability}
                      intake={guidedIntake}
                      capabilities={intakeCapabilities}
                    />

                    {guidedIntake ? (
                      <>
                        <div className="intake-status-row">
                          <div>
                            <span>{dictionary.intake.status}</span>
                            <strong>
                              {
                                dictionary.intake.statusLabels[
                                  guidedIntake.status
                                ]
                              }
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
                            <h3 id="intake-checks-title">
                              {dictionary.intake.checks}
                            </h3>
                            <ol className="intake-checks">
                              {guidedIntake.checks.map((check, index) => (
                                <li
                                  key={check.key}
                                  data-complete={check.complete}
                                >
                                  <span
                                    className="intake-step"
                                    aria-hidden="true"
                                  >
                                    {String(index + 1).padStart(2, "0")}
                                  </span>
                                  <div>
                                    <strong>
                                      {dictionary.intake.checkLabels[check.key]}
                                    </strong>
                                    <small className="intake-check-state">
                                      {check.complete
                                        ? dictionary.intake.checkComplete
                                        : dictionary.intake.checkPending}
                                    </small>
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
                                  {guidedIntake.office ??
                                    dictionary.intake.notAssessed}
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
                                <dt>
                                  {dictionary.intake.evidenceRequirements}
                                </dt>
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
                              {guidedIntake.research_first_actions.map(
                                (action) => (
                                  <li key={action}>
                                    {
                                      dictionary.intake.researchActionLabels[
                                        action
                                      ]
                                    }
                                  </li>
                                ),
                              )}
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
                  </div>
                </details>
              </section>
            </ChapterSurface>
          ) : null}

          {chapterRouteActive && currentJourneyPhase.key === "evidence" ? (
            <ChapterSurface chapter="evidence">
              <section
                id="candidate-workspace"
                className="candidate-workspace-panel"
                aria-labelledby="candidate-workspace-title"
              >
                <div className="candidate-profile-heading">
                  <p className="eyebrow">{dictionary.candidate.eyebrow}</p>
                  <h2 id="candidate-workspace-title">
                    {dictionary.candidate.profileViewLabel}
                  </h2>
                  <p>{dictionary.candidate.profileBody}</p>
                </div>

                {candidateWorkspace ? (
                  <>
                    <CandidateWorkspaceDeck
                      dictionary={dictionary}
                      profile={
                        <CandidateWorkspaceProfile
                          dictionary={dictionary}
                          workspace={candidateWorkspace}
                        />
                      }
                      completion={
                        <CandidateWorkspaceCompletion
                          locale={locale}
                          dictionary={dictionary}
                          demo={model.demo}
                          workspace={candidateWorkspace}
                          capabilities={candidateCapabilities}
                        />
                      }
                      evidence={
                        <CandidateWorkspaceEditor
                          locale={locale}
                          dictionary={dictionary}
                          demo={model.demo}
                          availability={model.candidateWorkspaceAvailability}
                          workspace={candidateWorkspace}
                          capabilities={candidateCapabilities}
                          prerequisiteReady={candidatePrerequisiteReady}
                        />
                      }
                    />

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
                ) : model.candidateWorkspaceAvailability === "NOT_STARTED" &&
                  candidateCapabilities.canStart &&
                  candidatePrerequisiteReady ? (
                  <CandidateWorkspaceEditor
                    locale={locale}
                    dictionary={dictionary}
                    demo={model.demo}
                    availability={model.candidateWorkspaceAvailability}
                    workspace={candidateWorkspace}
                    capabilities={candidateCapabilities}
                    prerequisiteReady={candidatePrerequisiteReady}
                  />
                ) : (
                  <p className="intake-state" role="status">
                    {candidateWorkspaceStateMessage}
                  </p>
                )}
              </section>
            </ChapterSurface>
          ) : null}

          {chapterRouteActive && currentJourneyPhase.key === "team" ? (
            <ChapterSurface chapter="team">
              <section
                id="team-workspace"
                className="team-workspace-panel"
                aria-labelledby="team-workspace-title"
              >
                <div className="intake-heading">
                  <div>
                    <p className="eyebrow">
                      {dictionary.teamWorkspace.eyebrow}
                    </p>
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

                {teamWorkspace &&
                teamWorkspace.completed_checks < teamWorkspace.total_checks ? (
                  <div className="team-progress-guidance" role="status">
                    <strong>
                      {dictionary.teamWorkspace.progressGuidanceTitle}
                    </strong>
                    <p>{dictionary.teamWorkspace.progressGuidanceBody}</p>
                    <ul>
                      {teamWorkspace.checks
                        .filter((check) => !check.complete)
                        .map((check) => (
                          <li key={check.key}>
                            {dictionary.teamWorkspace.checkLabels[check.key]}
                          </li>
                        ))}
                    </ul>
                  </div>
                ) : null}

                <TeamWorkspaceEditor
                  locale={locale}
                  dictionary={dictionary}
                  demo={model.demo}
                  availability={model.teamWorkspaceAvailability}
                  workspace={teamWorkspace}
                  templatePreview={model.teamTemplatePreview}
                  templatePreviewUnavailable={
                    model.teamTemplatePreviewUnavailable
                  }
                  capabilities={teamCapabilities}
                  prerequisiteReady={teamPrerequisiteReady}
                />

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
                      <strong>
                        {dictionary.teamWorkspace.authorityBoundary}
                      </strong>
                      <p>{dictionary.teamWorkspace.authorityBody}</p>
                      <small>{dictionary.common.notApproval}</small>
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

                    <TeamOperationsDeck
                      dictionary={dictionary}
                      hasWorkItems={(teamWorkspace.work_items ?? []).length > 0}
                      creator={
                        <TeamWorkItemEditor
                          locale={locale}
                          dictionary={dictionary}
                          roles={teamWorkspace.roles ?? []}
                          workspaceVersion={teamWorkspace.version}
                          canUpdate={teamCapabilities.canUpdate}
                          openByDefault
                        />
                      }
                      board={
                        <TeamOperationsBoard
                          locale={locale}
                          dictionary={dictionary}
                          roles={teamWorkspace.roles ?? []}
                          workItems={teamWorkspace.work_items ?? []}
                          workspaceVersion={teamWorkspace.version}
                          canUpdate={teamCapabilities.canUpdate}
                          embedded
                        />
                      }
                    />

                    <div className="team-layout">
                      <details className="team-progress-details">
                        <summary>
                          {dictionary.teamWorkspace.progressDetailsAction}
                        </summary>
                        <section aria-labelledby="team-checks-title">
                          <h3 id="team-checks-title">
                            {dictionary.teamWorkspace.progress}
                          </h3>
                          <ol className="intake-checks">
                            {teamWorkspace.checks.map((check, index) => (
                              <li
                                key={check.key}
                                data-complete={check.complete}
                              >
                                <span
                                  className="intake-step"
                                  aria-hidden="true"
                                >
                                  {String(index + 1).padStart(2, "0")}
                                </span>
                                <div>
                                  <strong>
                                    {
                                      dictionary.teamWorkspace.checkLabels[
                                        check.key
                                      ]
                                    }
                                  </strong>
                                  <small className="intake-check-state">
                                    {check.complete
                                      ? dictionary.intake.checkComplete
                                      : dictionary.intake.checkPending}
                                  </small>
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
                      </details>

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
                            {teamWorkspace.roles.map((role) => {
                              const relatedWork = (
                                teamWorkspace.work_items ?? []
                              ).filter((item) =>
                                item.assignments.some(
                                  (assignment) =>
                                    assignment.role_id === role.id,
                                ),
                              );
                              const attentionCount = relatedWork.filter(
                                (item) =>
                                  item.status === "BLOCKED" ||
                                  item.health === "AT_RISK" ||
                                  item.health === "OFF_TRACK",
                              ).length;
                              return (
                                <article
                                  key={role.id}
                                  data-status={role.status}
                                >
                                  <div className="team-role-card-heading">
                                    <div>
                                      <span>{role.area}</span>
                                      <h4>{role.title}</h4>
                                    </div>
                                    <div className="team-role-work-summary">
                                      <span>
                                        <strong>{relatedWork.length}</strong>{" "}
                                        {dictionary.teamWorkspace.roleWorkCount}
                                      </span>
                                      {attentionCount > 0 ? (
                                        <span data-attention="true">
                                          <strong>{attentionCount}</strong>{" "}
                                          {
                                            dictionary.teamWorkspace
                                              .roleAttentionCount
                                          }
                                        </span>
                                      ) : null}
                                    </div>
                                  </div>
                                  <p>{role.purpose}</p>
                                  <details className="team-role-card-details">
                                    <summary>
                                      {
                                        dictionary.teamWorkspace
                                          .roleDetailAction
                                      }
                                    </summary>
                                    <div className="team-role-responsibilities">
                                      <strong>
                                        {
                                          dictionary.teamWorkspace
                                            .roleResponsibilitiesLabel
                                        }
                                      </strong>
                                      <ul>
                                        {role.responsibilities.map(
                                          (responsibility) => (
                                            <li key={responsibility}>
                                              {responsibility}
                                            </li>
                                          ),
                                        )}
                                      </ul>
                                    </div>
                                    <TeamRoleDossier
                                      profile={role}
                                      dictionary={dictionary}
                                    />
                                    <dl>
                                      <div>
                                        <dt>
                                          {dictionary.teamWorkspace.capacity}
                                        </dt>
                                        <dd>
                                          {role.weekly_capacity_hours === null
                                            ? "—"
                                            : `${role.weekly_capacity_hours} ${dictionary.teamWorkspace.hours}`}
                                        </dd>
                                      </div>
                                      <div>
                                        <dt>
                                          {dictionary.teamWorkspace.status}
                                        </dt>
                                        <dd>
                                          {
                                            dictionary.teamWorkspace
                                              .roleStatusLabels[role.status]
                                          }
                                        </dd>
                                      </div>
                                    </dl>
                                    {role.vacancy_plan ? (
                                      <div className="team-vacancy-plan">
                                        <strong>
                                          {
                                            dictionary.teamWorkspace
                                              .vacancyPlanLabel
                                          }
                                        </strong>
                                        <p>{role.vacancy_plan}</p>
                                      </div>
                                    ) : null}
                                  </details>
                                </article>
                              );
                            })}
                          </div>
                        )}
                      </section>
                    </div>

                    <TrainingAcademyPanel
                      locale={locale}
                      dictionary={dictionary}
                      catalog={model.trainingCatalog}
                      assignments={model.trainingAssignments}
                      receipts={model.trainingReceipts}
                      availability={model.trainingAvailability}
                      capabilities={trainingCapabilities}
                      demo={model.demo}
                    />

                    <details className="governance-metadata">
                      <summary>
                        <span>
                          {dictionary.teamWorkspace.governanceDetails}
                        </span>
                        <small>
                          {dictionary.teamWorkspace.governanceDetailsBody}
                        </small>
                      </summary>
                      <div className="governance-metadata-body">
                        <div className="team-detail-grid">
                          <article>
                            <h3>{dictionary.teamWorkspace.training}</h3>
                            {teamWorkspace.training_requirements === null ? (
                              <p className="intake-empty">
                                {dictionary.teamWorkspace.notAssessed}
                              </p>
                            ) : teamWorkspace.training_requirements.length ===
                              0 ? (
                              <p className="intake-empty">
                                {dictionary.teamWorkspace.noItems}
                              </p>
                            ) : (
                              <ul className="intake-items">
                                {teamWorkspace.training_requirements.map(
                                  (item) => (
                                    <li key={item.id}>
                                      {item.status} · {item.title}
                                    </li>
                                  ),
                                )}
                              </ul>
                            )}
                          </article>
                          <article>
                            <h3>
                              {dictionary.teamWorkspace.accessRecommendations}
                            </h3>
                            {teamWorkspace.access_recommendations === null ? (
                              <p className="intake-empty">
                                {dictionary.teamWorkspace.notAssessed}
                              </p>
                            ) : teamWorkspace.access_recommendations.length ===
                              0 ? (
                              <p className="intake-empty">
                                {dictionary.teamWorkspace.noItems}
                              </p>
                            ) : (
                              <ul className="intake-items">
                                {teamWorkspace.access_recommendations.map(
                                  (item) => (
                                    <li key={item.id}>
                                      {item.status} · {item.action} ·{" "}
                                      {item.resource_type} · {item.purpose}
                                    </li>
                                  ),
                                )}
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
                      </div>
                    </details>
                  </>
                ) : model.teamWorkspaceAvailability === "NOT_STARTED" &&
                  teamCapabilities.canStart &&
                  teamPrerequisiteReady ? null : (
                  <p className="intake-state" role="status">
                    {teamWorkspaceStateMessage}
                  </p>
                )}
              </section>
            </ChapterSurface>
          ) : null}

          {chapterRouteActive && currentJourneyPhase.key === "strategy" ? (
            <ChapterSurface chapter="strategy">
              <StrategyWorkspace
                dictionary={dictionary}
                evidence={model.strategyWorkspace}
                availability={model.strategyWorkspaceAvailability}
              />
            </ChapterSurface>
          ) : null}

          {chapterRouteActive && currentJourneyPhase.key === "operations" ? (
            <ChapterSurface chapter="operations">
              <OperationsWorkspace
                dictionary={dictionary}
                roadmapEvidence={model.campaignRoadmap}
                roadmapAvailability={model.campaignRoadmapAvailability}
                snapshotEvidence={model.warRoomSnapshot}
                snapshotAvailability={model.warRoomSnapshotAvailability}
              />
            </ChapterSurface>
          ) : null}

          {chapterRouteActive ? null : (
            <>
              <section className="dashboard-grid">
                <CandidateOverviewPanel
                  locale={locale}
                  dictionary={dictionary}
                  workspace={candidateWorkspace}
                  stateMessage={candidateWorkspaceStateMessage}
                />

                <article className="panel">
                  <p className="eyebrow">
                    {dictionary.dashboard.authorityEyebrow}
                  </p>
                  <h2>{dictionary.dashboard.authorityTitle}</h2>
                  <p>{dictionary.dashboard.authorityBody}</p>
                  <div className="grant-count">
                    <strong>{grantCount}</strong>
                    <span>{dictionary.dashboard.grantCountLabel}</span>
                  </div>
                </article>

                <article id="evidence" className="panel">
                  <p className="eyebrow">
                    {dictionary.dashboard.evidenceEyebrow}
                  </p>
                  <h2>{dictionary.dashboard.evidenceTitle}</h2>
                  <p>{dictionary.dashboard.evidenceBody}</p>
                  <dl className="compact-data">
                    <div>
                      <dt>{dictionary.dashboard.auditReceipt}</dt>
                      <dd>{model.readiness?.audit_event_id ?? "—"}</dd>
                    </div>
                    <div>
                      <dt>{dictionary.dashboard.noExternal}</dt>
                      <dd>{dictionary.dashboard.confirmed}</dd>
                    </div>
                  </dl>
                </article>

                <article className="panel operations-panel">
                  <p className="eyebrow">
                    {dictionary.dashboard.operationsEyebrow}
                  </p>
                  <h2>{dictionary.dashboard.operationsTitle}</h2>
                  <p>{dictionary.dashboard.operationsBody}</p>
                  <ol className="sequence-list">
                    <li>
                      <span>01</span> {dictionary.dashboard.sequence.context}
                    </li>
                    <li>
                      <span>02</span> {dictionary.dashboard.sequence.workspace}
                    </li>
                    <li>
                      <span>03</span> {dictionary.dashboard.sequence.intake}
                    </li>
                    <li>
                      <span>04</span> {dictionary.dashboard.sequence.evidence}
                    </li>
                  </ol>
                </article>
              </section>

              <section
                className="limitation-panel"
                aria-labelledby="limitations-title"
              >
                <div>
                  <p className="eyebrow">
                    {dictionary.dashboard.limitationsEyebrow}
                  </p>
                  <h2 id="limitations-title">
                    {dictionary.dashboard.limitations}
                  </h2>
                </div>
                <ul>
                  {limitationCodes.map((code) => (
                    <li key={code}>
                      {dictionary.dashboard.limitationLabels[code]}
                    </li>
                  ))}
                </ul>
              </section>
              <p className="reference-note">{dictionary.shell.reference}</p>
            </>
          )}
        </main>
      </div>
    </div>
  );
}
