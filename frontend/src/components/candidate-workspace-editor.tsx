import { randomUUID } from "node:crypto";

import type { CandidateWorkspaceProjection } from "@/lib/contracts";
import type { Dictionary, Locale } from "@/lib/i18n";
import type { CandidateWorkspaceCapabilities } from "@/lib/journey-capabilities";
import type { CandidateWorkspaceAvailability } from "@/lib/shell-view-model";

export function CandidateWorkspaceEditor({
  locale,
  dictionary,
  demo,
  availability,
  workspace,
  capabilities,
  prerequisiteReady,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  demo: boolean;
  availability: CandidateWorkspaceAvailability;
  workspace: CandidateWorkspaceProjection | null;
  capabilities: CandidateWorkspaceCapabilities;
  prerequisiteReady: boolean;
}>) {
  if (demo) return null;
  if (
    availability === "NOT_STARTED" &&
    capabilities.canStart &&
    prerequisiteReady
  ) {
    return (
      <form className="candidate-start-card" action="/api/ui/candidate-workspace/start" method="post">
        <input type="hidden" name="locale" value={locale} />
        <input type="hidden" name="idempotency_key" value={`candidate-start:${randomUUID()}`} />
        <div>
          <p className="eyebrow">{dictionary.candidate.startEyebrow}</p>
          <h3>{dictionary.candidate.startTitle}</h3>
          <p>{dictionary.candidate.startBody}</p>
        </div>
        <label>
          <span>{dictionary.candidate.displayName}</span>
          <input
            name="display_name"
            maxLength={255}
            required
            autoComplete="name"
            placeholder={dictionary.candidate.displayNamePlaceholder}
          />
          <small>{dictionary.candidate.displayNameHelp}</small>
        </label>
        <button type="submit">{dictionary.candidate.startAction}</button>
      </form>
    );
  }
  if (
    availability !== "AVAILABLE" ||
    workspace === null ||
    !capabilities.canRead ||
    !capabilities.canUpdate
  ) {
    return null;
  }
  return (
    <section className="candidate-evidence-editor" aria-labelledby="candidate-evidence-editor-title">
      <div className="editor-heading">
        <div>
          <p className="eyebrow">{dictionary.candidate.evidenceEditorEyebrow}</p>
          <h3 id="candidate-evidence-editor-title">{dictionary.candidate.evidenceEditorTitle}</h3>
          <p>{dictionary.candidate.evidenceEditorBody}</p>
        </div>
        <span className="version-chip">{dictionary.dashboard.version} {workspace.version}</span>
      </div>
      <form action="/api/ui/candidate-workspace/evidence" method="post">
        <input type="hidden" name="locale" value={locale} />
        <input type="hidden" name="version" value={workspace.version} />
        <input type="hidden" name="idempotency_key" value={`candidate-evidence:${randomUUID()}`} />
        <div className="candidate-evidence-grid">
          <label>
            <span>{dictionary.candidate.evidenceClassification}</span>
            <select name="classification" defaultValue="OFFICIAL_SOURCE">
              {Object.entries(dictionary.candidate.evidenceClassificationLabels).map(([value, label]) => (
                <option key={value} value={value}>{label}</option>
              ))}
            </select>
          </label>
          <label>
            <span>{dictionary.candidate.evidenceTitle}</span>
            <input name="title" maxLength={255} required placeholder={dictionary.candidate.evidenceTitlePlaceholder} />
          </label>
          <label className="field-wide">
            <span>{dictionary.candidate.sourceReference}</span>
            <input name="source_reference" type="url" inputMode="url" maxLength={2048} required placeholder="https://" />
            <small>{dictionary.candidate.sourceReferenceHelp}</small>
          </label>
          <label>
            <span>{dictionary.candidate.sourceAuthority}</span>
            <input name="source_authority" maxLength={255} placeholder={dictionary.candidate.sourceAuthorityPlaceholder} />
          </label>
          <label>
            <span>{dictionary.candidate.evidenceJurisdiction}</span>
            <input name="jurisdiction" maxLength={255} placeholder={dictionary.candidate.evidenceJurisdictionPlaceholder} />
          </label>
          <label>
            <span>{dictionary.candidate.observedAt}</span>
            <input name="observed_at" type="date" />
          </label>
          <label className="field-wide">
            <span>{dictionary.candidate.evidenceExcerpt}</span>
            <textarea name="excerpt" maxLength={2000} rows={3} placeholder={dictionary.candidate.evidenceExcerptPlaceholder} />
          </label>
        </div>
        <div className="form-actions">
          <p>{dictionary.candidate.evidenceBoundary}</p>
          <button type="submit">{dictionary.candidate.addEvidenceAction}</button>
        </div>
      </form>
      {workspace.evidence.length > 0 ? (
        <div className="candidate-source-register">
          <h4>{dictionary.candidate.sourceRegister}</h4>
          <ol>
            {workspace.evidence.map((item) => (
              <li key={item.id}>
                <div>
                  <span>{dictionary.candidate.evidenceClassificationLabels[item.classification]}</span>
                  <strong>{item.title}</strong>
                  <small>{item.source_authority ?? dictionary.candidate.sourceAuthorityUnknown}</small>
                </div>
                <a href={item.source_reference} target="_blank" rel="noreferrer">
                  {dictionary.candidate.openSource}
                </a>
              </li>
            ))}
          </ol>
        </div>
      ) : null}
    </section>
  );
}
