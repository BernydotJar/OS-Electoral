import { deriveCandidateActionInsights } from "@/lib/candidate-action-insights";
import type { CandidateWorkspaceProjection } from "@/lib/contracts";
import type { Dictionary } from "@/lib/i18n";

export function CandidateActionBrief({
  dictionary,
  workspace,
}: Readonly<{
  dictionary: Dictionary;
  workspace: CandidateWorkspaceProjection;
}>) {
  const insights = deriveCandidateActionInsights(workspace);

  return (
    <section
      className="candidate-action-brief"
      aria-labelledby="candidate-action-brief-title"
    >
      <div className="candidate-action-brief-heading">
        <div>
          <p className="eyebrow">{dictionary.candidate.actionBriefEyebrow}</p>
          <h3 id="candidate-action-brief-title">
            {dictionary.candidate.actionBriefTitle}
          </h3>
          <p>{dictionary.candidate.actionBriefBody}</p>
        </div>
        <span>{dictionary.candidate.publicBoundary}</span>
      </div>

      <div className="candidate-action-grid">
        {insights.map((insight) => (
          <article key={insight.code} data-tone={insight.tone}>
            <span>
              {dictionary.candidate.actionInsightLabels[insight.code]}
            </span>
            <strong>
              {insight.code === "NEXT_ACTION"
                ? dictionary.candidate.nextActionLabels[workspace.next_action]
                : insight.code === "EVIDENCE_GAP"
                  ? dictionary.candidate.zeroVerifiedSources
                  : insight.count}
            </strong>
            <p>{dictionary.candidate.actionInsightBodies[insight.code]}</p>
          </article>
        ))}
      </div>

      <p className="candidate-action-boundary" role="note">
        {dictionary.candidate.actionBriefBoundary}
      </p>
    </section>
  );
}
