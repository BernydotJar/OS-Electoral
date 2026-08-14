
import { CandidateActionBrief } from "@/components/candidate-action-brief";
import { campaignChapterHref } from "@/lib/campaign-chapters";
import type { CandidateWorkspaceProjection } from "@/lib/contracts";
import type { Dictionary, Locale } from "@/lib/i18n";

export function CandidateOverviewPanel({
  locale,
  dictionary,
  workspace,
  stateMessage,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  workspace: CandidateWorkspaceProjection | null;
  stateMessage: string;
}>) {
  return (
    <article
      id="candidate-summary"
      className="panel candidate-overview-panel"
      aria-labelledby="candidate-summary-title"
    >
      <div className="candidate-overview-heading">
        <div>
          <p className="eyebrow">{dictionary.candidate.eyebrow}</p>
          <h2 id="candidate-summary-title">{dictionary.candidate.title}</h2>
          <p>{dictionary.candidate.body}</p>
        </div>
        {workspace ? (
          <div
            className="intake-progress"
            aria-label={dictionary.candidate.progress}
          >
            <strong>
              {workspace.completed_checks}/{workspace.total_checks}
            </strong>
            <span>{dictionary.candidate.progress}</span>
            <progress
              max={workspace.total_checks}
              value={workspace.completed_checks}
            >
              {workspace.completed_checks}/{workspace.total_checks}
            </progress>
          </div>
        ) : null}
      </div>

      {workspace ? (
        <>
          <CandidateActionBrief dictionary={dictionary} workspace={workspace} />
          <a
            className="candidate-overview-link"
            href={campaignChapterHref(locale, "evidence")}
          >
            <span>{dictionary.candidate.profileViewLabel}</span>
            <span aria-hidden="true">→</span>
          </a>
        </>
      ) : (
        <p className="intake-state" role="status">
          {stateMessage}
        </p>
      )}
    </article>
  );
}
