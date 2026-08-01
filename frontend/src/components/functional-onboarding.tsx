import { randomUUID } from "node:crypto";

import { GuidedTeamSelector } from "@/components/guided-team-selector";
import type {
  CampaignProjection,
  GuidedIntakeProjection,
} from "@/lib/contracts";
import type { Dictionary, Locale } from "@/lib/i18n";
import type { GuidedIntakeCapabilities } from "@/lib/journey-capabilities";
import type { GuidedIntakeAvailability } from "@/lib/shell-view-model";

export function CampaignContextForm({
  locale,
  dictionary,
  campaigns,
  currentCampaignId,
  canCreateCampaign,
  demo,
}: {
  locale: Locale;
  dictionary: Dictionary;
  campaigns: readonly CampaignProjection[];
  currentCampaignId: string;
  canCreateCampaign: boolean;
  demo: boolean;
}) {
  return (
    <section
      id="campaigns"
      className="campaign-context-panel"
      aria-labelledby="campaign-context-title"
    >
      <div>
        <p className="eyebrow">{dictionary.campaigns.eyebrow}</p>
        <h2 id="campaign-context-title">{dictionary.campaigns.title}</h2>
        <p>{dictionary.campaigns.body}</p>
      </div>
      <div className="campaign-context-actions">
        {demo ? (
          <div className="selected-campaign-card">
            <span>{dictionary.campaigns.current}</span>
            <strong>{campaigns[0]?.name ?? "—"}</strong>
          </div>
        ) : campaigns.length > 0 ? (
          <form
            className="campaign-context-form"
            action="/api/ui/campaign-context"
            method="post"
          >
            <input type="hidden" name="locale" value={locale} />
            <label htmlFor="campaign-context-select">
              {dictionary.campaigns.selectLabel}
            </label>
            <div className="inline-control">
              <select
                id="campaign-context-select"
                name="campaign_id"
                defaultValue={currentCampaignId}
              >
                {campaigns.map((campaign) => (
                  <option key={campaign.id} value={campaign.id}>
                    {campaign.name} · {campaign.status}
                  </option>
                ))}
              </select>
              <button type="submit">{dictionary.campaigns.apply}</button>
            </div>
            <p className="field-help">{dictionary.campaigns.help}</p>
          </form>
        ) : (
          <div className="selected-campaign-card campaign-context-empty">
            <span>{dictionary.campaigns.emptyLabel}</span>
            <strong>{dictionary.campaigns.emptyBody}</strong>
          </div>
        )}
        {!demo && canCreateCampaign ? (
          <details className="campaign-create-disclosure">
            <summary>
              <span>{dictionary.campaigns.createTitle}</span>
              <small>{dictionary.campaigns.createBody}</small>
            </summary>
            <form
              className="campaign-create-form"
              action="/api/ui/campaign-context/create"
              method="post"
            >
              <input type="hidden" name="locale" value={locale} />
              <input
                type="hidden"
                name="idempotency_key"
                value={`campaign-create:${randomUUID()}`}
              />
              <div className="campaign-create-field">
                <label htmlFor="campaign-create-name">
                  {dictionary.campaigns.createName}
                </label>
                <input
                  id="campaign-create-name"
                  name="name"
                  type="text"
                  required
                  maxLength={255}
                  autoComplete="off"
                  placeholder={dictionary.campaigns.createNamePlaceholder}
                />
              </div>
              <div className="campaign-create-field">
                <label htmlFor="campaign-create-jurisdiction">
                  {dictionary.campaigns.createJurisdiction}
                </label>
                <input
                  id="campaign-create-jurisdiction"
                  name="jurisdiction"
                  type="text"
                  required
                  maxLength={255}
                  autoComplete="off"
                  placeholder={dictionary.campaigns.createJurisdictionPlaceholder}
                />
              </div>
              <div className="campaign-create-actions">
                <button type="submit">{dictionary.campaigns.createAction}</button>
                <p className="field-help">{dictionary.campaigns.createBoundary}</p>
              </div>
            </form>
          </details>
        ) : null}
      </div>
    </section>
  );
}

function lines(items: readonly string[] | null): string {
  return items?.join("\n") ?? "";
}

export function GuidedIntakeEditor({
  locale,
  dictionary,
  demo,
  availability,
  intake,
  capabilities,
}: {
  locale: Locale;
  dictionary: Dictionary;
  demo: boolean;
  availability: GuidedIntakeAvailability;
  intake: GuidedIntakeProjection | null;
  capabilities: GuidedIntakeCapabilities;
}) {
  if (demo) return null;
  if (availability === "NOT_STARTED" && capabilities.canStart) {
    return (
      <div className="intake-action-card">
        <div>
          <h3>{dictionary.intake.startTitle}</h3>
          <p>{dictionary.intake.startBody}</p>
        </div>
        <form action="/api/ui/guided-intake/start" method="post">
          <input type="hidden" name="locale" value={locale} />
          <input
            type="hidden"
            name="idempotency_key"
            value={`intake-start:${randomUUID()}`}
          />
          <button type="submit">{dictionary.intake.startAction}</button>
        </form>
      </div>
    );
  }
  if (availability !== "AVAILABLE" || intake === null || !capabilities.canUpdate) {
    return null;
  }
  return (
    <form
      className="intake-editor"
      action="/api/ui/guided-intake/update"
      method="post"
      aria-labelledby="intake-editor-title"
    >
      <input type="hidden" name="locale" value={locale} />
      <input type="hidden" name="version" value={intake.version} />
      <input
        type="hidden"
        name="idempotency_key"
        value={`intake-update:${randomUUID()}`}
      />
      <div className="editor-heading">
        <div>
          <p className="eyebrow">{dictionary.intake.editEyebrow}</p>
          <h3 id="intake-editor-title">{dictionary.intake.editTitle}</h3>
          <p>{dictionary.intake.editBody}</p>
        </div>
        <span className="version-chip">
          {dictionary.dashboard.version} {intake.version}
        </span>
      </div>
      <div className="form-grid">
        <label>
          <span>{dictionary.intake.office}</span>
          <input
            name="office"
            defaultValue={intake.office ?? ""}
            maxLength={255}
            placeholder={dictionary.intake.officePlaceholder}
          />
          <small>{dictionary.intake.officeHelp}</small>
        </label>
        <label>
          <span>{dictionary.intake.budgetStatus}</span>
          <select name="budget_status" defaultValue={intake.budget_status}>
            {Object.entries(dictionary.intake.budgetStatusLabels).map(
              ([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ),
            )}
          </select>
          <small>{dictionary.intake.budgetHelp}</small>
        </label>
        <label className="field-wide">
          <span>{dictionary.intake.candidateProject}</span>
          <textarea
            name="candidate_project"
            defaultValue={intake.candidate_project ?? ""}
            maxLength={2000}
            rows={4}
            placeholder={dictionary.intake.candidateProjectPlaceholder}
          />
          <small>{dictionary.intake.candidateProjectHelp}</small>
        </label>
        <GuidedTeamSelector
          dictionary={dictionary}
          defaultValues={intake.current_team ?? []}
        />
        {(
          [
            [
              "current_assets",
              dictionary.intake.currentAssets,
              intake.current_assets,
              dictionary.intake.currentAssetsHelp,
              dictionary.intake.currentAssetsPlaceholder,
            ],
            [
              "known_unknowns",
              dictionary.intake.knownUnknowns,
              intake.known_unknowns,
              dictionary.intake.knownUnknownsHelp,
              dictionary.intake.knownUnknownsPlaceholder,
            ],
            [
              "evidence_requirements",
              dictionary.intake.evidenceRequirements,
              intake.evidence_requirements,
              dictionary.intake.evidenceRequirementsHelp,
              dictionary.intake.evidenceRequirementsPlaceholder,
            ],
          ] as const
        ).map(([name, label, items, help, placeholder]) => (
          <label key={name}>
            <span>{label}</span>
            <textarea
              name={name}
              defaultValue={lines(items)}
              rows={4}
              placeholder={placeholder}
            />
            <small>{help}</small>
            <small>{dictionary.intake.onePerLine}</small>
          </label>
        ))}
      </div>
      <div className="form-actions">
        <p>{dictionary.intake.saveBoundary}</p>
        <button type="submit">{dictionary.intake.saveAction}</button>
      </div>
    </form>
  );
}
