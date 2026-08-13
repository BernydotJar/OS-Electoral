import type { Dictionary } from "@/lib/i18n";
import type { ReactNode } from "react";

export function CandidateWorkspaceDeck({
  dictionary,
  profile,
  completion,
  evidence,
}: Readonly<{
  dictionary: Dictionary;
  profile: ReactNode;
  completion: ReactNode;
  evidence: ReactNode;
}>) {
  return (
    <section
      className="candidate-workspace-deck candidate-workspace-single"
      aria-label={dictionary.candidate.profileViewLabel}
    >
      <div className="candidate-profile-flow">{profile}</div>
      <div className="candidate-completion-flow">{completion}</div>

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
