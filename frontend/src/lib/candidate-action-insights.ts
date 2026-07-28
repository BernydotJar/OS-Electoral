import type { CandidateWorkspaceProjection } from "@/lib/contracts";

export type CandidateActionInsightCode =
  | "NEXT_ACTION"
  | "EVIDENCE_GAP"
  | "CONTRADICTIONS_OPEN"
  | "RISK_DECISION_REQUIRED"
  | "DEVELOPMENT_ACTIVE"
  | "APPROVALS_PENDING";

export type CandidateActionInsight = Readonly<{
  code: CandidateActionInsightCode;
  count: number;
  tone: "PRIMARY" | "WARNING" | "CRITICAL" | "INFO";
  externalEffects: "NONE";
}>;

export function deriveCandidateActionInsights(
  workspace: CandidateWorkspaceProjection,
): readonly CandidateActionInsight[] {
  const insights: CandidateActionInsight[] = [
    {
      code: "NEXT_ACTION",
      count: 1,
      tone: "PRIMARY",
      externalEffects: "NONE",
    },
  ];

  if (workspace.evidence.length === 0) {
    insights.push({
      code: "EVIDENCE_GAP",
      count: 0,
      tone: "WARNING",
      externalEffects: "NONE",
    });
  }

  const openContradictions = (workspace.contradictions ?? []).filter(
    (item) => item.status !== "RESOLVED",
  ).length;
  if (openContradictions > 0) {
    insights.push({
      code: "CONTRADICTIONS_OPEN",
      count: openContradictions,
      tone: "WARNING",
      externalEffects: "NONE",
    });
  }

  if (workspace.open_critical_high_risks > 0) {
    insights.push({
      code: "RISK_DECISION_REQUIRED",
      count: workspace.open_critical_high_risks,
      tone: "CRITICAL",
      externalEffects: "NONE",
    });
  }

  const activeDevelopment = (workspace.development_goals ?? []).filter(
    (item) => item.status !== "COMPLETE",
  ).length;
  if (activeDevelopment > 0) {
    insights.push({
      code: "DEVELOPMENT_ACTIVE",
      count: activeDevelopment,
      tone: "INFO",
      externalEffects: "NONE",
    });
  }

  if (workspace.approvals_required.length > 0) {
    insights.push({
      code: "APPROVALS_PENDING",
      count: workspace.approvals_required.length,
      tone: "INFO",
      externalEffects: "NONE",
    });
  }

  return insights;
}
