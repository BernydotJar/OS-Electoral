import { randomUUID } from "node:crypto";

import type {
  CampaignMilestone,
  CampaignOperationsBlocker,
  CampaignOperationsDecision,
  CampaignOperationsFollowUp,
  CampaignOperationsLearningNote,
  CampaignOperationsTask,
  CampaignOperationsWorkstream,
  CampaignPhase,
  CampaignRoadmapProjection,
  TeamRoleCard,
} from "@/lib/contracts";
import type { Dictionary, Locale } from "@/lib/i18n";
import type { OperationsWorkspaceCapabilities } from "@/lib/journey-capabilities";
import type { CampaignRoadmapAvailability } from "@/lib/shell-view-model";

type ReferenceItem = Readonly<{ id: string; label: string }>;

type Props = Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  demo: boolean;
  availability: CampaignRoadmapAvailability;
  roadmap: CampaignRoadmapProjection | null;
  capabilities: OperationsWorkspaceCapabilities;
  prerequisiteReady: boolean;
  teamRoles: readonly TeamRoleCard[];
  evidenceReferences: readonly ReferenceItem[];
}>;

type SectionName =
  | "phases"
  | "workstreams"
  | "milestones"
  | "tasks"
  | "blockers"
  | "decisions"
  | "follow_up_items"
  | "learning_notes";

function HiddenFields({ locale, roadmap, section, recordId = "", prefix }: Readonly<{
  locale: Locale;
  roadmap: CampaignRoadmapProjection;
  section: SectionName;
  recordId?: string;
  prefix: string;
}>) {
  return <>
    <input type="hidden" name="locale" value={locale} />
    <input type="hidden" name="version" value={roadmap.version} />
    <input type="hidden" name="idempotency_key" value={`${prefix}:${randomUUID()}`} />
    <input type="hidden" name="section" value={section} />
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
    <legend>{dictionary.operations.referenceHelp}</legend>
    {items.length === 0 ? <p className="intake-empty">{dictionary.operations.noItems}</p> : items.map((item) => (
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

function RoleSelect({ dictionary, name, roles, selected }: Readonly<{
  dictionary: Dictionary;
  name: string;
  roles: readonly TeamRoleCard[];
  selected?: string | null;
}>) {
  return <select name={name} required defaultValue={selected ?? ""}>
    <option value="" disabled>{dictionary.operations.selectRole}</option>
    {roles.map((role) => <option key={`${name}-${role.id}`} value={role.id}>{role.title} · {role.area}</option>)}
  </select>;
}

function PhaseForm({ locale, dictionary, roadmap, record }: Readonly<{
  locale: Locale; dictionary: Dictionary; roadmap: CampaignRoadmapProjection; record: CampaignPhase | null;
}>) {
  return <form action="/api/ui/operations-workspace/section" method="post">
    <HiddenFields locale={locale} roadmap={roadmap} section="phases" recordId={record?.id} prefix="operations-phase" />
    <div className="candidate-evidence-grid">
      <label><span>{dictionary.operations.name}</span><input name="name" required maxLength={255} defaultValue={record?.name ?? ""} /></label>
      <label><span>{dictionary.operations.sequence}</span><input name="sequence" type="number" min={1} max={1000} required defaultValue={record?.sequence ?? ""} /></label>
      <label><span>{dictionary.operations.startDate}</span><input name="start_date" type="date" required defaultValue={record?.start_date ?? ""} /></label>
      <label><span>{dictionary.operations.endDate}</span><input name="end_date" type="date" required defaultValue={record?.end_date ?? ""} /></label>
      <label><span>{dictionary.operations.recordStatus}</span><select name="status" defaultValue={record?.status ?? "PLANNED"}>{Object.entries(dictionary.operations.phaseStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    </div>
    <div className="form-actions"><p>{dictionary.operations.phaseHelp}</p><button type="submit">{dictionary.operations.saveSection}</button></div>
  </form>;
}

function WorkstreamForm({ locale, dictionary, roadmap, record, roles }: Readonly<{
  locale: Locale; dictionary: Dictionary; roadmap: CampaignRoadmapProjection; record: CampaignOperationsWorkstream | null; roles: readonly TeamRoleCard[];
}>) {
  return <form action="/api/ui/operations-workspace/section" method="post">
    <HiddenFields locale={locale} roadmap={roadmap} section="workstreams" recordId={record?.id} prefix="operations-workstream" />
    <div className="candidate-evidence-grid">
      <label><span>{dictionary.operations.name}</span><input name="name" required maxLength={255} defaultValue={record?.name ?? ""} /></label>
      <label><span>{dictionary.operations.ownerRole}</span><RoleSelect dictionary={dictionary} name="accountable_role_id" roles={roles} selected={record?.accountable_role_id} /></label>
      <label className="field-wide"><span>{dictionary.operations.purpose}</span><textarea name="purpose" required maxLength={2000} rows={3} defaultValue={record?.purpose ?? ""} /></label>
      <label><span>{dictionary.operations.recordStatus}</span><select name="status" defaultValue={record?.status ?? "PLANNED"}>{Object.entries(dictionary.operations.workstreamStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    </div>
    <div className="form-actions"><p>{dictionary.operations.workstreamHelp}</p><button type="submit">{dictionary.operations.saveSection}</button></div>
  </form>;
}

function MilestoneForm({ locale, dictionary, roadmap, record, roles }: Readonly<{
  locale: Locale; dictionary: Dictionary; roadmap: CampaignRoadmapProjection; record: CampaignMilestone | null; roles: readonly TeamRoleCard[];
}>) {
  const phases = roadmap.phases ?? [];
  return <form action="/api/ui/operations-workspace/section" method="post">
    <HiddenFields locale={locale} roadmap={roadmap} section="milestones" recordId={record?.id} prefix="operations-milestone" />
    <div className="candidate-evidence-grid">
      <label><span>{dictionary.operations.phase}</span><select name="phase_id" required defaultValue={record?.phase_id ?? ""}><option value="" disabled>{dictionary.operations.selectPhase}</option>{phases.map((phase) => <option key={phase.id} value={phase.id}>{phase.sequence}. {phase.name}</option>)}</select></label>
      <label><span>{dictionary.operations.name}</span><input name="name" required maxLength={255} defaultValue={record?.name ?? ""} /></label>
      <label><span>{dictionary.operations.ownerRole}</span><RoleSelect dictionary={dictionary} name="owner_role_id" roles={roles} selected={record?.owner_role_id} /></label>
      <label><span>{dictionary.operations.dueDate}</span><input name="due_date" type="date" required defaultValue={record?.due_date ?? ""} /></label>
      <label className="field-wide"><span>{dictionary.operations.completionCriteria}</span><textarea name="completion_criteria" required maxLength={2000} rows={3} defaultValue={record?.completion_criteria ?? ""} /></label>
      <label><span>{dictionary.operations.recordStatus}</span><select name="status" defaultValue={record?.status ?? "PLANNED"}>{Object.entries(dictionary.operations.milestoneStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    </div>
    <div className="form-actions"><p>{dictionary.operations.milestoneHelp}</p><button type="submit">{dictionary.operations.saveSection}</button></div>
  </form>;
}

function TaskForm({ locale, dictionary, roadmap, record, roles, evidenceReferences }: Readonly<{
  locale: Locale; dictionary: Dictionary; roadmap: CampaignRoadmapProjection; record: CampaignOperationsTask | null; roles: readonly TeamRoleCard[]; evidenceReferences: readonly ReferenceItem[];
}>) {
  const phases = roadmap.phases ?? [];
  const workstreams = roadmap.workstreams ?? [];
  const milestones = roadmap.milestones ?? [];
  const dependencies = (roadmap.tasks ?? []).filter((task) => task.id !== record?.id).map((task) => ({ id: task.id, label: task.title }));
  return <form action="/api/ui/operations-workspace/section" method="post">
    <HiddenFields locale={locale} roadmap={roadmap} section="tasks" recordId={record?.id} prefix="operations-task" />
    <div className="candidate-evidence-grid">
      <label><span>{dictionary.operations.phase}</span><select name="phase_id" required defaultValue={record?.phase_id ?? ""}><option value="" disabled>{dictionary.operations.selectPhase}</option>{phases.map((phase) => <option key={phase.id} value={phase.id}>{phase.sequence}. {phase.name}</option>)}</select></label>
      <label><span>{dictionary.operations.workstream}</span><select name="workstream_id" required defaultValue={record?.workstream_id ?? ""}><option value="" disabled>{dictionary.operations.selectWorkstream}</option>{workstreams.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label><span>{dictionary.operations.milestone}</span><select name="milestone_id" defaultValue={record?.milestone_id ?? ""}><option value="">{dictionary.operations.noMilestone}</option>{milestones.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label><span>{dictionary.operations.ownerRole}</span><RoleSelect dictionary={dictionary} name="owner_role_id" roles={roles} selected={record?.owner_role_id} /></label>
      <label className="field-wide"><span>{dictionary.operations.taskTitle}</span><input name="title" required maxLength={500} defaultValue={record?.title ?? ""} /></label>
      <label><span>{dictionary.operations.dueDate}</span><input name="due_date" type="date" required defaultValue={record?.due_date ?? ""} /></label>
      <label><span>{dictionary.operations.executionStatus}</span><select name="execution_status" defaultValue={record?.execution_status ?? "PLANNED"}>{Object.entries(dictionary.operations.taskStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    </div>
    <span className="strategy-reference-heading">{dictionary.operations.dependencies}</span>
    <ReferenceChecklist dictionary={dictionary} name="dependency_ids" items={dependencies} selected={record?.dependency_ids} />
    <span className="strategy-reference-heading">{dictionary.operations.evidenceRefs}</span>
    <ReferenceChecklist dictionary={dictionary} name="evidence_refs" items={evidenceReferences} selected={record?.evidence_refs} />
    <div className="form-actions"><p>{dictionary.operations.taskHelp}</p><button type="submit">{dictionary.operations.saveSection}</button></div>
  </form>;
}

function BlockerForm({ locale, dictionary, roadmap, record, roles }: Readonly<{
  locale: Locale; dictionary: Dictionary; roadmap: CampaignRoadmapProjection; record: CampaignOperationsBlocker | null; roles: readonly TeamRoleCard[];
}>) {
  const tasks = roadmap.tasks ?? [];
  return <form action="/api/ui/operations-workspace/section" method="post">
    <HiddenFields locale={locale} roadmap={roadmap} section="blockers" recordId={record?.id} prefix="operations-blocker" />
    <div className="candidate-evidence-grid">
      <label><span>{dictionary.operations.task}</span><select name="task_id" defaultValue={record?.task_id ?? ""}><option value="">{dictionary.operations.generalBlocker}</option>{tasks.map((task) => <option key={task.id} value={task.id}>{task.title}</option>)}</select></label>
      <label><span>{dictionary.operations.ownerRole}</span><RoleSelect dictionary={dictionary} name="owner_role_id" roles={roles} selected={record?.owner_role_id} /></label>
      <label><span>{dictionary.operations.severity}</span><select name="severity" defaultValue={record?.severity ?? "MEDIUM"}>{Object.entries(dictionary.operations.severityLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label><span>{dictionary.operations.recordStatus}</span><select name="status" defaultValue={record?.status ?? "OPEN"}>{Object.entries(dictionary.operations.blockerStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
      <label className="field-wide"><span>{dictionary.operations.description}</span><textarea name="description" required maxLength={2000} rows={3} defaultValue={record?.description ?? ""} /></label>
      <label className="field-wide"><span>{dictionary.operations.resolutionCondition}</span><textarea name="resolution_condition" required maxLength={2000} rows={3} defaultValue={record?.resolution_condition ?? ""} /></label>
    </div>
    <div className="form-actions"><p>{dictionary.operations.blockerHelp}</p><button type="submit">{dictionary.operations.saveSection}</button></div>
  </form>;
}

function DecisionForm({ locale, dictionary, roadmap, record, roles }: Readonly<{
  locale: Locale; dictionary: Dictionary; roadmap: CampaignRoadmapProjection; record: CampaignOperationsDecision | null; roles: readonly TeamRoleCard[];
}>) {
  return <form action="/api/ui/operations-workspace/section" method="post">
    <HiddenFields locale={locale} roadmap={roadmap} section="decisions" recordId={record?.id} prefix="operations-decision" />
    <div className="candidate-evidence-grid">
      <label className="field-wide"><span>{dictionary.operations.decisionTitle}</span><input name="title" required maxLength={500} defaultValue={record?.title ?? ""} /></label>
      <label><span>{dictionary.operations.humanRole}</span><RoleSelect dictionary={dictionary} name="human_role_id" roles={roles} selected={record?.human_role_id} /></label>
      <label><span>{dictionary.operations.dueDate}</span><input name="due_date" type="date" required defaultValue={record?.due_date ?? ""} /></label>
      <label className="field-wide"><span>{dictionary.operations.options}</span><textarea name="options" required rows={4} defaultValue={record?.options.join("\n") ?? ""} /><small>{dictionary.operations.lineHelp}</small></label>
      {record === null ? <><input type="hidden" name="status" value="REQUIRED" /><input type="hidden" name="decision" value="" /></> : <>
        <label><span>{dictionary.operations.recordStatus}</span><select name="status" defaultValue={record.status}>{Object.entries(dictionary.operations.decisionStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
        <label><span>{dictionary.operations.selectedDecision}</span><select name="decision" defaultValue={record.decision ?? ""}><option value="">{dictionary.operations.noDecision}</option>{record.options.map((option) => <option key={option} value={option}>{option}</option>)}</select></label>
      </>}
    </div>
    <div className="form-actions"><p>{dictionary.operations.decisionHelp}</p><button type="submit">{dictionary.operations.saveSection}</button></div>
  </form>;
}

function FollowUpForm({ locale, dictionary, roadmap, record, roles }: Readonly<{
  locale: Locale; dictionary: Dictionary; roadmap: CampaignRoadmapProjection; record: CampaignOperationsFollowUp | null; roles: readonly TeamRoleCard[];
}>) {
  return <form action="/api/ui/operations-workspace/section" method="post">
    <HiddenFields locale={locale} roadmap={roadmap} section="follow_up_items" recordId={record?.id} prefix="operations-follow-up" />
    <div className="candidate-evidence-grid">
      <label className="field-wide"><span>{dictionary.operations.followUpTitle}</span><input name="title" required maxLength={500} defaultValue={record?.title ?? ""} /></label>
      <label><span>{dictionary.operations.ownerRole}</span><RoleSelect dictionary={dictionary} name="owner_role_id" roles={roles} selected={record?.owner_role_id} /></label>
      <label><span>{dictionary.operations.dueDate}</span><input name="due_date" type="date" required defaultValue={record?.due_date ?? ""} /></label>
      <label><span>{dictionary.operations.recordStatus}</span><select name="status" defaultValue={record?.status ?? "OPEN"}>{Object.entries(dictionary.operations.followUpStatusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    </div>
    <div className="form-actions"><p>{dictionary.operations.followUpHelp}</p><button type="submit">{dictionary.operations.saveSection}</button></div>
  </form>;
}

function LearningForm({ locale, dictionary, roadmap, record, evidenceReferences }: Readonly<{
  locale: Locale; dictionary: Dictionary; roadmap: CampaignRoadmapProjection; record: CampaignOperationsLearningNote | null; evidenceReferences: readonly ReferenceItem[];
}>) {
  return <form action="/api/ui/operations-workspace/section" method="post">
    <HiddenFields locale={locale} roadmap={roadmap} section="learning_notes" recordId={record?.id} prefix="operations-learning" />
    <div className="candidate-evidence-grid">
      <label className="field-wide"><span>{dictionary.operations.learningTitle}</span><input name="title" required maxLength={500} defaultValue={record?.title ?? ""} /></label>
      <label className="field-wide"><span>{dictionary.operations.learningNote}</span><textarea name="note" required maxLength={4000} rows={4} defaultValue={record?.note ?? ""} /></label>
    </div>
    <span className="strategy-reference-heading">{dictionary.operations.evidenceRefs}</span>
    <ReferenceChecklist dictionary={dictionary} name="evidence_refs" items={evidenceReferences} selected={record?.evidence_refs} />
    <div className="form-actions"><p>{dictionary.operations.learningHelp}</p><button type="submit">{dictionary.operations.saveSection}</button></div>
  </form>;
}

function SnapshotForm({ locale, dictionary, roadmap }: Readonly<{
  locale: Locale; dictionary: Dictionary; roadmap: CampaignRoadmapProjection;
}>) {
  return <section id="operations-snapshot-create" className="candidate-evidence-editor" aria-labelledby="operations-snapshot-create-title">
    <div className="editor-heading"><div><p className="eyebrow">{dictionary.operations.snapshotCreateEyebrow}</p><h3 id="operations-snapshot-create-title">{dictionary.operations.snapshotCreateTitle}</h3><p>{dictionary.operations.snapshotCreateBody}</p></div><span className="version-chip">{dictionary.operations.roadmapVersion} {roadmap.version}</span></div>
    <form action="/api/ui/operations-workspace/snapshot" method="post">
      <input type="hidden" name="locale" value={locale} />
      <input type="hidden" name="version" value={roadmap.version} />
      <input type="hidden" name="idempotency_key" value={`war-room-snapshot:${randomUUID()}`} />
      <div className="candidate-evidence-grid">
        <label><span>{dictionary.operations.snapshotDate}</span><input name="snapshot_date" type="date" required /></label>
        <label className="field-wide"><span>{dictionary.operations.priorities}</span><textarea name="priorities" required rows={4} /><small>{dictionary.operations.lineHelp}</small></label>
        <label className="field-wide"><span>{dictionary.operations.followUp}</span><textarea name="follow_up_notes" rows={4} /><small>{dictionary.operations.lineHelp}</small></label>
      </div>
      <div className="form-actions"><p>{dictionary.operations.snapshotBoundary}</p><button type="submit">{dictionary.operations.snapshotCreateAction}</button></div>
    </form>
  </section>;
}

export function OperationsWorkspaceEditor({ locale, dictionary, demo, availability, roadmap, capabilities, prerequisiteReady, teamRoles, evidenceReferences }: Props) {
  if (demo) return null;
  if (availability === "NOT_STARTED" && prerequisiteReady && capabilities.canStart && capabilities.canRead) {
    return <form className="candidate-start-card" action="/api/ui/operations-workspace/start" method="post">
      <input type="hidden" name="locale" value={locale} />
      <input type="hidden" name="idempotency_key" value={`operations-start:${randomUUID()}`} />
      <div><p className="eyebrow">{dictionary.operations.startEyebrow}</p><h3>{dictionary.operations.startTitle}</h3><p>{dictionary.operations.startBody}</p></div>
      <label><span>{dictionary.operations.startLabel}</span><input name="title" required maxLength={255} /></label>
      <button type="submit">{dictionary.operations.startAction}</button>
    </form>;
  }
  if (
    availability !== "AVAILABLE" ||
    roadmap === null ||
    !prerequisiteReady ||
    !capabilities.canRead ||
    !capabilities.canUpdate
  ) return null;

  const roles = teamRoles.filter((role) => role.status === "FILLED");
  if (roles.length === 0) return null;

  return <section id="operations-authoring" className="candidate-evidence-editor" aria-labelledby="operations-authoring-title">
    <div className="editor-heading"><div><p className="eyebrow">{dictionary.operations.buildEyebrow}</p><h3 id="operations-authoring-title">{dictionary.operations.buildTitle}</h3><p>{dictionary.operations.buildBody}</p></div><span className="version-chip">{dictionary.operations.roadmapVersion} {roadmap.version}</span></div>
    <p className="team-template-boundary">{dictionary.operations.mutationBoundary}</p>
    <div className="team-readiness-grid strategy-authoring-grid">
      <RecordShell id="operations-phases" title={dictionary.operations.phases} help={dictionary.operations.phaseHelp} open={(roadmap.phases ?? []).length === 0}>
        {(roadmap.phases ?? []).map((record) => <PhaseForm key={record.id} locale={locale} dictionary={dictionary} roadmap={roadmap} record={record} />)}
        <h4>{dictionary.operations.newRecord}</h4><PhaseForm locale={locale} dictionary={dictionary} roadmap={roadmap} record={null} />
      </RecordShell>
      <RecordShell id="operations-workstreams" title={dictionary.operations.workstreams} help={dictionary.operations.workstreamHelp} open={(roadmap.workstreams ?? []).length === 0}>
        {(roadmap.workstreams ?? []).map((record) => <WorkstreamForm key={record.id} locale={locale} dictionary={dictionary} roadmap={roadmap} record={record} roles={roles} />)}
        <h4>{dictionary.operations.newRecord}</h4><WorkstreamForm locale={locale} dictionary={dictionary} roadmap={roadmap} record={null} roles={roles} />
      </RecordShell>
      <RecordShell id="operations-milestones" title={dictionary.operations.milestones} help={dictionary.operations.milestoneHelp}>
        {(roadmap.milestones ?? []).map((record) => <MilestoneForm key={record.id} locale={locale} dictionary={dictionary} roadmap={roadmap} record={record} roles={roles} />)}
        {(roadmap.phases ?? []).length > 0 ? <><h4>{dictionary.operations.newRecord}</h4><MilestoneForm locale={locale} dictionary={dictionary} roadmap={roadmap} record={null} roles={roles} /></> : null}
      </RecordShell>
      <RecordShell id="operations-tasks" title={dictionary.operations.tasks} help={dictionary.operations.taskHelp} open={(roadmap.tasks ?? []).length === 0}>
        {(roadmap.tasks ?? []).map((record) => <TaskForm key={record.id} locale={locale} dictionary={dictionary} roadmap={roadmap} record={record} roles={roles} evidenceReferences={evidenceReferences} />)}
        {(roadmap.phases ?? []).length > 0 && (roadmap.workstreams ?? []).length > 0 ? <><h4>{dictionary.operations.newRecord}</h4><TaskForm locale={locale} dictionary={dictionary} roadmap={roadmap} record={null} roles={roles} evidenceReferences={evidenceReferences} /></> : null}
      </RecordShell>
      <RecordShell id="operations-blockers" title={dictionary.operations.blockers} help={dictionary.operations.blockerHelp}>
        {(roadmap.blockers ?? []).map((record) => <BlockerForm key={record.id} locale={locale} dictionary={dictionary} roadmap={roadmap} record={record} roles={roles} />)}
        <h4>{dictionary.operations.newRecord}</h4><BlockerForm locale={locale} dictionary={dictionary} roadmap={roadmap} record={null} roles={roles} />
      </RecordShell>
      <RecordShell id="operations-decisions" title={dictionary.operations.decisions} help={dictionary.operations.decisionHelp}>
        {(roadmap.decisions ?? []).map((record) => <DecisionForm key={record.id} locale={locale} dictionary={dictionary} roadmap={roadmap} record={record} roles={roles} />)}
        <h4>{dictionary.operations.newRecord}</h4><DecisionForm locale={locale} dictionary={dictionary} roadmap={roadmap} record={null} roles={roles} />
      </RecordShell>
      <RecordShell id="operations-follow-ups" title={dictionary.operations.followUp} help={dictionary.operations.followUpHelp}>
        {(roadmap.follow_up_items ?? []).map((record) => <FollowUpForm key={record.id} locale={locale} dictionary={dictionary} roadmap={roadmap} record={record} roles={roles} />)}
        <h4>{dictionary.operations.newRecord}</h4><FollowUpForm locale={locale} dictionary={dictionary} roadmap={roadmap} record={null} roles={roles} />
      </RecordShell>
      <RecordShell id="operations-learning" title={dictionary.operations.learning} help={dictionary.operations.learningHelp}>
        {(roadmap.learning_notes ?? []).map((record) => <LearningForm key={record.id} locale={locale} dictionary={dictionary} roadmap={roadmap} record={record} evidenceReferences={evidenceReferences} />)}
        <h4>{dictionary.operations.newRecord}</h4><LearningForm locale={locale} dictionary={dictionary} roadmap={roadmap} record={null} evidenceReferences={evidenceReferences} />
      </RecordShell>
    </div>
    {capabilities.canCreateSnapshot && capabilities.canReadSnapshot && (roadmap.tasks ?? []).length > 0 ? <SnapshotForm locale={locale} dictionary={dictionary} roadmap={roadmap} /> : null}
  </section>;
}
