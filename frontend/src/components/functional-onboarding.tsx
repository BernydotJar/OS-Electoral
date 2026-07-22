import { randomUUID } from "node:crypto";

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
  demo,
}: {
  locale: Locale;
  dictionary: Dictionary;
  campaigns: readonly CampaignProjection[];
  currentCampaignId: string;
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
      {demo ? (
        <div className="selected-campaign-card">
          <span>{dictionary.campaigns.current}</span>
          <strong>{campaigns[0]?.name ?? "—"}</strong>
        </div>
      ) : (
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
      )}
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
          <input name="office" defaultValue={intake.office ?? ""} maxLength={255} />
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
        </label>
        <label className="field-wide">
          <span>{dictionary.intake.candidateProject}</span>
          <textarea
            name="candidate_project"
            defaultValue={intake.candidate_project ?? ""}
            maxLength={2000}
            rows={4}
          />
        </label>
        {(
          [
            ["current_team", dictionary.intake.currentTeam, intake.current_team],
            ["current_assets", dictionary.intake.currentAssets, intake.current_assets],
            ["known_unknowns", dictionary.intake.knownUnknowns, intake.known_unknowns],
            [
              "evidence_requirements",
              dictionary.intake.evidenceRequirements,
              intake.evidence_requirements,
            ],
          ] as const
        ).map(([name, label, items]) => (
          <label key={name}>
            <span>{label}</span>
            <textarea name={name} defaultValue={lines(items)} rows={4} />
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
