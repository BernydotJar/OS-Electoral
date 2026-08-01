import type { Dictionary } from "@/lib/i18n";
import type { ReactNode } from "react";

export function CandidateWorkspaceDeck({
  dictionary,
  actions,
  profile,
  evidence,
}: Readonly<{
  dictionary: Dictionary;
  actions: ReactNode;
  profile: ReactNode;
  evidence: ReactNode;
}>) {
  return (
    <section
      className="candidate-workspace-deck candidate-workspace-single"
      aria-labelledby="candidate-profile-view-title"
    >
      <header className="candidate-workspace-single-heading">
        <h3 id="candidate-profile-view-title">
          {dictionary.candidate.profileViewLabel}
        </h3>
      </header>

      <div className="candidate-profile-flow">
        {profile}
        {actions}
      </div>

      <details className="candidate-evidence-disclosure">
        <summary>
          <span>{dictionary.candidate.evidenceViewLabel}</span>
          <small>{dictionary.candidate.evidenceDisclosureHint}</small>
        </summary>
        <div className="candidate-evidence-disclosure-body">{evidence}</div>
      </details>
    </section>
  );
}
