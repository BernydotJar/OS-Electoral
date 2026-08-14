import { randomUUID } from "node:crypto";

import type {
  StrategyAssumptionRecord,
  StrategyContradictionRecord,
  StrategyEvidenceRecord,
  StrategyHypothesisRecord,
  StrategyObjectiveRecord,
  StrategyOptionRecord,
  StrategyRedTeamFindingRecord,
  StrategyWorkspaceProjection,
  TeamRoleCard,
} from "@/lib/contracts";
import type { Dictionary, Locale } from "@/lib/i18n";
import type { StrategyWorkspaceCapabilities } from "@/lib/journey-capabilities";
import type { StrategyWorkspaceAvailability } from "@/lib/shell-view-model";

type ReferenceItem = Readonly<{ id: string; label: string }>;

type Props = Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  demo: boolean;
  availability: StrategyWorkspaceAvailability;
  workspace: StrategyWorkspaceProjection | null;
  capabilities: StrategyWorkspaceCapabilities;
  prerequisiteReady: boolean;
  teamRoles: readonly TeamRoleCard[];
}>;

function HiddenFields({ locale, workspace, section, action = "save", recordId = "", prefix }: Readonly<{
  locale: Locale;
  workspace: StrategyWorkspaceProjection;
  section: "evidence" | "assumptions" | "hypotheses" | "options" | "objectives" | "contradictions" | "red_team_findings";
  action?: "save" | "review_empty";
  recordId?: string;
  prefix: string;
}>) {
  return <>
    <input type="hidden" name="locale" value={locale} />
    <input type="hidden" name="version" value={workspace.version} />
    <input type="hidden" name="idempotency_key" value={`${prefix}:${randomUUID()}`} />
    <input type="hidden" name="section" value={section} />
    <input type="hidden" name="strategy_action" value={action} />
    <input type="hidden" name="record_id" value={recordId} />
  </>;
}

function ReferenceChecklist({ dictionary, name, items, selected = [] }: Readonly<{
  dictionary: Dictionary;
  name: string;
  items: readonly ReferenceItem[];
  selected?: readonly string[];
}>) {
  const active = new Set(selected);
  return <fieldset className="strategy-reference-list">
    <legend>{dictionary.strategyRoom.referenceHelp}</legend>
    {items.length === 0 ? <p className="intake-empty">{dictionary.strategyRoom.noItems}</p> : items.map((item) => (
      <label key={`${name}-${item.id}`}>
        <input type="checkbox" name={name} value={item.id} defaultChecked={active.has(item.id)} />
        <span>{item.label}</span>
      </label>
    ))}
  </fieldset>;
}

function RecordShell({ id, title, help, children, open = false }: Readonly<{
  id: string;
  title: string;
  help: string;
  children: React.ReactNode;
  open?: boolean;
}>) {
  return <details id={id} className="team-readiness-section strategy-authoring-record" open={open}>
    <summary><span>{title}</span><small>{help}</small></summary>
    <div className="team-readiness-section-body">{children}</div>
  </details>;
}

function EvidenceForm({ locale, dictionary, workspace, record }: Readonly<{
  locale: Locale; dictionary: Dictionary; workspace: StrategyWorkspaceProjection; record: StrategyEvidenceRecord | null;
}>) {
  return <form action="/api/ui/strategy-workspace/section" method="post">
    <HiddenFields locale={locale} workspace={workspace} section="evidence" recordId={record?.id} prefix="strategy-evidence" />
    <div className="candidate-evidence-grid">
      <label><span>{dictionary.strategyRoom.classification}</span><select name="classification" defaultValue={record?.classification ?? "VERIFIED"}>
        {Object.entries(dictionary.strategyRoom.classificationLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select></label>
      <label><span>{dictionary.strategyRoom.collectedAt}</span><input name="collected_at" type="date" required defaultValue={record?.collected_at.slice(0, 10) ?? ""} /></label>
      <label className="field-wide"><span>{dictionary.strategyRoom.statement}</span><textarea name="statement" rows={4} maxLength={2000} required defaultValue={record?.statement ?? ""} /></label>
      <label className="field-wide"><span>{dictionary.strategyRoom.sourceReference}</span><input name="source_reference" type="url" inputMode="url" maxLength={500} defaultValue={record?.source_reference ?? ""} placeholder="https://" /></label>
      <label><span>{dictionary.strategyRoom.authority}</span><input name="authority" maxLength={180} defaultValue={record?.authority ?? ""} /></label>
      <label><span>{dictionary.strategyRoom.jurisdiction}</span><input name="jurisdiction" maxLength={180} defaultValue={record?.jurisdiction ?? ""} /></label>
    </div>
    <div className="form-actions"><p>{dictionary.strategyRoom.evidenceHelp}</p><button type="submit">{dictionary.strategyRoom.saveSection}</button></div>
  </form>;
}

function AssumptionForm({ locale, dictionary, workspace, record, evidenceItems }: Readonly<{
  locale: Locale; dictionary: Dictionary; workspace: StrategyWorkspaceProjection; record: StrategyAssumptionRecord | null; evidenceItems: readonly ReferenceItem[];
}>) {
  return <form action="/api/ui/strategy-workspace/section" method="post">
    <HiddenFields locale={locale} workspace={workspace} section="assumptions" recordId={record?.id} prefix="strategy-assumption" />
    <div className="candidate-evidence-grid">
      <label className="field-wide"><span>{dictionary.strategyRoom.statement}</span><textarea name="statement" required maxLength={2000} rows={4} defaultValue={record?.statement ?? ""} /></label>
      <label><span>{dictionary.strategyRoom.assumptionStatus}</span><select name="status" defaultValue={record?.status ?? "ACTIVE"}>
        {Object.entries(dictionary.strategyRoom.assumptionStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select></label>
      <label className="field-wide"><span>{dictionary.strategyRoom.invalidationSignals}</span><textarea name="invalidation_signals" required rows={3} defaultValue={record?.invalidation_signals.join("\n") ?? ""} /><small>{dictionary.strategyRoom.lineHelp}</small></label>
    </div>
    <span className="strategy-reference-heading">{dictionary.strategyRoom.evidenceRefs}</span>
    <ReferenceChecklist dictionary={dictionary} name="evidence_refs" items={evidenceItems} selected={record?.evidence_refs} />
    <div className="form-actions"><p>{dictionary.strategyRoom.assumptionHelp}</p><button type="submit">{dictionary.strategyRoom.saveSection}</button></div>
  </form>;
}

function HypothesisForm({ locale, dictionary, workspace, record, evidenceItems, assumptionItems }: Readonly<{
  locale: Locale; dictionary: Dictionary; workspace: StrategyWorkspaceProjection; record: StrategyHypothesisRecord | null; evidenceItems: readonly ReferenceItem[]; assumptionItems: readonly ReferenceItem[];
}>) {
  return <form action="/api/ui/strategy-workspace/section" method="post">
    <HiddenFields locale={locale} workspace={workspace} section="hypotheses" recordId={record?.id} prefix="strategy-hypothesis" />
    <div className="candidate-evidence-grid">
      <label><span>{dictionary.strategyRoom.hypothesisTitle}</span><input name="title" required maxLength={180} defaultValue={record?.title ?? ""} /></label>
      <label><span>{dictionary.strategyRoom.hypothesisStatus}</span><select name="status" defaultValue={record?.status ?? "IN_REVIEW"}>
        {Object.entries(dictionary.strategyRoom.hypothesisStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </select></label>
      <label className="field-wide"><span>{dictionary.strategyRoom.statement}</span><textarea name="statement" required maxLength={2000} rows={4} defaultValue={record?.statement ?? ""} /></label>
      <label className="field-wide"><span>{dictionary.strategyRoom.invalidationSignals}</span><textarea name="invalidation_signals" required rows={3} defaultValue={record?.invalidation_signals.join("\n") ?? ""} /><small>{dictionary.strategyRoom.lineHelp}</small></label>
    </div>
    <span className="strategy-reference-heading">{dictionary.strategyRoom.evidenceRefs}</span>
    <ReferenceChecklist dictionary={dictionary} name="evidence_refs" items={evidenceItems} selected={record?.evidence_refs} />
    <span className="strategy-reference-heading">{dictionary.strategyRoom.assumptionRefs}</span>
    <ReferenceChecklist dictionary={dictionary} name="assumption_refs" items={assumptionItems} selected={record?.assumption_refs} />
    <div className="form-actions"><p>{dictionary.strategyRoom.hypothesisHelp}</p><button type="submit">{dictionary.strategyRoom.saveSection}</button></div>
  </form>;
}

function OptionForm({ locale, dictionary, workspace, record, evidenceItems, hypothesisItems }: Readonly<{
  locale: Locale; dictionary: Dictionary; workspace: StrategyWorkspaceProjection; record: StrategyOptionRecord | null; evidenceItems: readonly ReferenceItem[]; hypothesisItems: readonly ReferenceItem[];
}>) {
  return <form action="/api/ui/strategy-workspace/section" method="post">
    <HiddenFields locale={locale} workspace={workspace} section="options" recordId={record?.id} prefix="strategy-option" />
    <div className="candidate-evidence-grid">
      <label><span>{dictionary.strategyRoom.optionTitle}</span><input name="title" required maxLength={180} defaultValue={record?.title ?? ""} /></label>
      <label className="field-wide"><span>{dictionary.strategyRoom.optionSummary}</span><textarea name="summary" required maxLength={2000} rows={4} defaultValue={record?.summary ?? ""} /></label>
      <label><span>{dictionary.strategyRoom.benefitsLines}</span><textarea name="benefits" required rows={4} defaultValue={record?.benefits.join("\n") ?? ""} /></label>
      <label><span>{dictionary.strategyRoom.risksLines}</span><textarea name="risks" required rows={4} defaultValue={record?.risks.join("\n") ?? ""} /></label>
      <label className="field-wide"><span>{dictionary.strategyRoom.tradeoffsLines}</span><textarea name="tradeoffs" required rows={4} defaultValue={record?.tradeoffs.join("\n") ?? ""} /><small>{dictionary.strategyRoom.lineHelp}</small></label>
    </div>
    <span className="strategy-reference-heading">{dictionary.strategyRoom.hypothesisRefs}</span>
    <ReferenceChecklist dictionary={dictionary} name="hypothesis_refs" items={hypothesisItems} selected={record?.hypothesis_refs} />
    <span className="strategy-reference-heading">{dictionary.strategyRoom.evidenceRefs}</span>
    <ReferenceChecklist dictionary={dictionary} name="evidence_refs" items={evidenceItems} selected={record?.evidence_refs} />
    <div className="form-actions"><p>{dictionary.strategyRoom.optionHelp}</p><button type="submit">{dictionary.strategyRoom.saveSection}</button></div>
  </form>;
}

function ObjectiveForm({ locale, dictionary, workspace, record, evidenceItems, teamRoles }: Readonly<{
  locale: Locale; dictionary: Dictionary; workspace: StrategyWorkspaceProjection; record: StrategyObjectiveRecord | null; evidenceItems: readonly ReferenceItem[]; teamRoles: readonly TeamRoleCard[];
}>) {
  return <form action="/api/ui/strategy-workspace/section" method="post">
    <HiddenFields locale={locale} workspace={workspace} section="objectives" recordId={record?.id} prefix="strategy-objective" />
    <div className="candidate-evidence-grid">
      <label className="field-wide"><span>{dictionary.strategyRoom.outcome}</span><textarea name="outcome" required maxLength={2000} rows={3} defaultValue={record?.outcome ?? ""} /></label>
      <label><span>{dictionary.strategyRoom.metric}</span><input name="metric" required maxLength={180} defaultValue={record?.metric ?? ""} /></label>
      <label><span>{dictionary.strategyRoom.baseline}</span><input name="baseline" required maxLength={180} defaultValue={record?.baseline ?? ""} /></label>
      <label><span>{dictionary.strategyRoom.target}</span><input name="target" required maxLength={180} defaultValue={record?.target ?? ""} /></label>
      <label><span>{dictionary.strategyRoom.deadline}</span><input name="deadline" type="date" required defaultValue={record?.deadline ?? ""} /></label>
      <label><span>{dictionary.strategyRoom.ownerRole}</span><select name="owner_role_id" required defaultValue={record?.owner_role_id ?? ""}>
        <option value="" disabled>{dictionary.strategyRoom.selectRole}</option>
        {teamRoles.map((role) => <option key={role.id} value={role.id}>{role.title} · {role.area}</option>)}
      </select></label>
    </div>
    <span className="strategy-reference-heading">{dictionary.strategyRoom.evidenceRefs}</span>
    <ReferenceChecklist dictionary={dictionary} name="evidence_refs" items={evidenceItems} selected={record?.evidence_refs} />
    <div className="form-actions"><p>{dictionary.strategyRoom.objectiveHelp}</p><button type="submit">{dictionary.strategyRoom.saveSection}</button></div>
  </form>;
}

function ContradictionForm({ locale, dictionary, workspace, record, referenceable, evidenceItems }: Readonly<{
  locale: Locale; dictionary: Dictionary; workspace: StrategyWorkspaceProjection; record: StrategyContradictionRecord | null; referenceable: readonly ReferenceItem[]; evidenceItems: readonly ReferenceItem[];
}>) {
  return <form action="/api/ui/strategy-workspace/section" method="post">
    <HiddenFields locale={locale} workspace={workspace} section="contradictions" recordId={record?.id} prefix="strategy-contradiction" />
    <div className="candidate-evidence-grid">
      <label><span>{dictionary.strategyRoom.leftReference}</span><select name="left_ref" required defaultValue={record?.left_ref ?? referenceable[0]?.id}>{referenceable.map((item) => <option key={`left-${item.id}`} value={item.id}>{item.label}</option>)}</select></label>
      <label><span>{dictionary.strategyRoom.rightReference}</span><select name="right_ref" required defaultValue={record?.right_ref ?? referenceable[1]?.id}>{referenceable.map((item) => <option key={`right-${item.id}`} value={item.id}>{item.label}</option>)}</select></label>
      <label><span>{dictionary.strategyRoom.recordStatus}</span><select name="status" defaultValue={record?.status ?? "OPEN"}>{Object.entries(dictionary.strategyRoom.contradictionStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label className="field-wide"><span>{dictionary.strategyRoom.description}</span><textarea name="description" required maxLength={2000} rows={3} defaultValue={record?.description ?? ""} /></label>
      <label className="field-wide"><span>{dictionary.strategyRoom.resolution}</span><textarea name="resolution" maxLength={2000} rows={3} defaultValue={record?.resolution ?? ""} /></label>
    </div>
    <span className="strategy-reference-heading">{dictionary.strategyRoom.evidenceRefs}</span>
    <ReferenceChecklist dictionary={dictionary} name="evidence_refs" items={evidenceItems} selected={record?.evidence_refs} />
    <div className="form-actions"><p>{dictionary.strategyRoom.contradictionHelp}</p><button type="submit">{dictionary.strategyRoom.saveSection}</button></div>
  </form>;
}

function FindingForm({ locale, dictionary, workspace, record, optionItems }: Readonly<{
  locale: Locale; dictionary: Dictionary; workspace: StrategyWorkspaceProjection; record: StrategyRedTeamFindingRecord | null; optionItems: readonly ReferenceItem[];
}>) {
  return <form action="/api/ui/strategy-workspace/section" method="post">
    <HiddenFields locale={locale} workspace={workspace} section="red_team_findings" recordId={record?.id} prefix="strategy-red-team" />
    <div className="candidate-evidence-grid">
      <label><span>{dictionary.strategyRoom.severity}</span><select name="severity" defaultValue={record?.severity ?? "MEDIUM"}>{Object.entries(dictionary.strategyRoom.severityLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label><span>{dictionary.strategyRoom.recordStatus}</span><select name="status" defaultValue={record?.status ?? "OPEN"}>{Object.entries(dictionary.strategyRoom.findingStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label className="field-wide"><span>{dictionary.strategyRoom.description}</span><textarea name="description" required maxLength={2000} rows={3} defaultValue={record?.description ?? ""} /></label>
      <label className="field-wide"><span>{dictionary.strategyRoom.mitigation}</span><textarea name="mitigation" required maxLength={2000} rows={3} defaultValue={record?.mitigation ?? ""} /></label>
    </div>
    <span className="strategy-reference-heading">{dictionary.strategyRoom.affectedOptions}</span>
    <ReferenceChecklist dictionary={dictionary} name="option_refs" items={optionItems} selected={record?.option_refs} />
    <div className="form-actions"><p>{dictionary.strategyRoom.redTeamHelp}</p><button type="submit">{dictionary.strategyRoom.saveSection}</button></div>
  </form>;
}

function EmptyReview({ locale, dictionary, workspace, section }: Readonly<{
  locale: Locale; dictionary: Dictionary; workspace: StrategyWorkspaceProjection; section: "contradictions" | "red_team_findings";
}>) {
  return <form className="candidate-empty-review" action="/api/ui/strategy-workspace/section" method="post">
    <HiddenFields locale={locale} workspace={workspace} section={section} action="review_empty" prefix={`strategy-${section}-empty-review`} />
    <p>{section === "contradictions" ? dictionary.strategyRoom.contradictionHelp : dictionary.strategyRoom.redTeamHelp}</p>
    <button type="submit">{section === "contradictions" ? dictionary.strategyRoom.noContradictionsAction : dictionary.strategyRoom.noFindingsAction}</button>
  </form>;
}

function DecisionForm({ locale, dictionary, workspace, teamRoles }: Readonly<{
  locale: Locale; dictionary: Dictionary; workspace: StrategyWorkspaceProjection; teamRoles: readonly TeamRoleCard[];
}>) {
  const options = workspace.options ?? [];
  return <section id="strategy-decision" className="candidate-evidence-editor" aria-labelledby="strategy-decision-form-title">
    <div className="editor-heading"><div><p className="eyebrow">{dictionary.strategyRoom.decisionEyebrow}</p><h3 id="strategy-decision-form-title">{dictionary.strategyRoom.decisionTitle}</h3><p>{dictionary.strategyRoom.decisionBody}</p></div><span className="version-chip">{dictionary.dashboard.version} {workspace.version}</span></div>
    <form action="/api/ui/strategy-workspace/decision" method="post">
      <input type="hidden" name="locale" value={locale} /><input type="hidden" name="version" value={workspace.version} /><input type="hidden" name="idempotency_key" value={`strategy-decision:${randomUUID()}`} />
      <div className="candidate-evidence-grid">
        <label><span>{dictionary.strategyRoom.selectedOption}</span><select name="selected_option_id" required defaultValue=""><option value="" disabled>{dictionary.strategyRoom.selectOption}</option>{options.map((option) => <option key={option.id} value={option.id}>{option.title}</option>)}</select></label>
        <label><span>{dictionary.strategyRoom.decisionRole}</span><select name="human_role_id" required defaultValue=""><option value="" disabled>{dictionary.strategyRoom.selectRole}</option>{teamRoles.map((role) => <option key={role.id} value={role.id}>{role.title} · {role.area}</option>)}</select></label>
        <label className="field-wide"><span>{dictionary.strategyRoom.decisionReason}</span><textarea name="reason" required maxLength={2000} rows={4} /></label>
      </div>
      <div className="form-actions"><p>{dictionary.strategyRoom.authorityBody}</p><button type="submit">{dictionary.strategyRoom.decideAction}</button></div>
    </form>
  </section>;
}

export function StrategyWorkspaceEditor({ locale, dictionary, demo, availability, workspace, capabilities, prerequisiteReady, teamRoles }: Props) {
  if (demo) return null;
  if (availability === "NOT_STARTED" && prerequisiteReady && capabilities.canStart && capabilities.canRead) {
    return <form className="candidate-start-card" action="/api/ui/strategy-workspace/start" method="post">
      <input type="hidden" name="locale" value={locale} />
      <input type="hidden" name="idempotency_key" value={`strategy-start:${randomUUID()}`} />
      <div><p className="eyebrow">{dictionary.strategyRoom.startEyebrow}</p><h3>{dictionary.strategyRoom.startTitle}</h3><p>{dictionary.strategyRoom.startBody}</p></div>
      <label><span>{dictionary.strategyRoom.startLabel}</span><input name="title" required maxLength={180} /></label>
      <button type="submit">{dictionary.strategyRoom.startAction}</button>
    </form>;
  }
  if (availability !== "AVAILABLE" || workspace === null || !capabilities.canRead || !capabilities.canUpdate) return null;

  const evidenceItems = (workspace.evidence ?? []).map((item) => ({ id: item.id, label: `${dictionary.strategyRoom.evidence}: ${item.statement}` }));
  const assumptionItems = (workspace.assumptions ?? []).map((item) => ({ id: item.id, label: `${dictionary.strategyRoom.assumptions}: ${item.statement}` }));
  const hypothesisItems = (workspace.hypotheses ?? []).map((item) => ({ id: item.id, label: `${dictionary.strategyRoom.hypotheses}: ${item.title}` }));
  const optionItems = (workspace.options ?? []).map((item) => ({ id: item.id, label: `${dictionary.strategyRoom.options}: ${item.title}` }));
  const objectiveItems = (workspace.objectives ?? []).map((item) => ({ id: item.id, label: `${dictionary.strategyRoom.objectives}: ${item.outcome}` }));
  const referenceable = [...evidenceItems, ...assumptionItems, ...hypothesisItems, ...optionItems, ...objectiveItems];

  return <section id="strategy-authoring" className="candidate-evidence-editor" aria-labelledby="strategy-authoring-title">
    <div className="editor-heading"><div><p className="eyebrow">{dictionary.strategyRoom.buildEyebrow}</p><h3 id="strategy-authoring-title">{dictionary.strategyRoom.buildTitle}</h3><p>{dictionary.strategyRoom.buildBody}</p></div><span className="version-chip">{dictionary.dashboard.version} {workspace.version}</span></div>
    <p className="team-template-boundary">{dictionary.strategyRoom.mutationBoundary}</p>
    <div className="team-readiness-grid strategy-authoring-grid">
      <RecordShell id="strategy-evidence" title={dictionary.strategyRoom.evidenceRegister} help={dictionary.strategyRoom.evidenceHelp} open={workspace.evidence === null}>
        {(workspace.evidence ?? []).map((record) => <EvidenceForm key={record.id} locale={locale} dictionary={dictionary} workspace={workspace} record={record} />)}
        <h4>{dictionary.strategyRoom.newRecord}</h4><EvidenceForm locale={locale} dictionary={dictionary} workspace={workspace} record={null} />
      </RecordShell>
      <RecordShell id="strategy-assumptions" title={dictionary.strategyRoom.assumptions} help={dictionary.strategyRoom.assumptionHelp}>
        {(workspace.assumptions ?? []).map((record) => <AssumptionForm key={record.id} locale={locale} dictionary={dictionary} workspace={workspace} record={record} evidenceItems={evidenceItems} />)}
        <h4>{dictionary.strategyRoom.newRecord}</h4><AssumptionForm locale={locale} dictionary={dictionary} workspace={workspace} record={null} evidenceItems={evidenceItems} />
      </RecordShell>
      <RecordShell id="strategy-hypotheses" title={dictionary.strategyRoom.hypotheses} help={dictionary.strategyRoom.hypothesisHelp}>
        {(workspace.hypotheses ?? []).map((record) => <HypothesisForm key={record.id} locale={locale} dictionary={dictionary} workspace={workspace} record={record} evidenceItems={evidenceItems} assumptionItems={assumptionItems} />)}
        <h4>{dictionary.strategyRoom.newRecord}</h4><HypothesisForm locale={locale} dictionary={dictionary} workspace={workspace} record={null} evidenceItems={evidenceItems} assumptionItems={assumptionItems} />
      </RecordShell>
      <RecordShell id="strategy-options" title={dictionary.strategyRoom.options} help={dictionary.strategyRoom.optionHelp}>
        {(workspace.options ?? []).map((record) => <OptionForm key={record.id} locale={locale} dictionary={dictionary} workspace={workspace} record={record} evidenceItems={evidenceItems} hypothesisItems={hypothesisItems} />)}
        <h4>{dictionary.strategyRoom.newRecord}</h4><OptionForm locale={locale} dictionary={dictionary} workspace={workspace} record={null} evidenceItems={evidenceItems} hypothesisItems={hypothesisItems} />
      </RecordShell>
      <RecordShell id="strategy-objectives" title={dictionary.strategyRoom.objectives} help={dictionary.strategyRoom.objectiveHelp}>
        {(workspace.objectives ?? []).map((record) => <ObjectiveForm key={record.id} locale={locale} dictionary={dictionary} workspace={workspace} record={record} evidenceItems={evidenceItems} teamRoles={teamRoles} />)}
        <h4>{dictionary.strategyRoom.newRecord}</h4><ObjectiveForm locale={locale} dictionary={dictionary} workspace={workspace} record={null} evidenceItems={evidenceItems} teamRoles={teamRoles} />
      </RecordShell>
      <RecordShell id="strategy-contradictions" title={dictionary.strategyRoom.contradictionReview} help={dictionary.strategyRoom.contradictionHelp} open={workspace.contradictions === null}>
        {workspace.contradictions === null ? <EmptyReview locale={locale} dictionary={dictionary} workspace={workspace} section="contradictions" /> : null}
        {(workspace.contradictions ?? []).map((record) => <ContradictionForm key={record.id} locale={locale} dictionary={dictionary} workspace={workspace} record={record} referenceable={referenceable} evidenceItems={evidenceItems} />)}
        {referenceable.length >= 2 ? <><h4>{dictionary.strategyRoom.newRecord}</h4><ContradictionForm locale={locale} dictionary={dictionary} workspace={workspace} record={null} referenceable={referenceable} evidenceItems={evidenceItems} /></> : null}
      </RecordShell>
      <RecordShell id="strategy-red-team" title={dictionary.strategyRoom.redTeamReview} help={dictionary.strategyRoom.redTeamHelp} open={workspace.red_team_findings === null}>
        {workspace.red_team_findings === null ? <EmptyReview locale={locale} dictionary={dictionary} workspace={workspace} section="red_team_findings" /> : null}
        {(workspace.red_team_findings ?? []).map((record) => <FindingForm key={record.id} locale={locale} dictionary={dictionary} workspace={workspace} record={record} optionItems={optionItems} />)}
        {optionItems.length > 0 ? <><h4>{dictionary.strategyRoom.newRecord}</h4><FindingForm locale={locale} dictionary={dictionary} workspace={workspace} record={null} optionItems={optionItems} /></> : null}
      </RecordShell>
    </div>
    {workspace.status === "READY_FOR_HUMAN_DECISION" && workspace.human_decision_required && workspace.decision === null && capabilities.canApprove && (workspace.options ?? []).length > 0 && teamRoles.length > 0 ? <DecisionForm locale={locale} dictionary={dictionary} workspace={workspace} teamRoles={teamRoles} /> : null}
  </section>;
}
