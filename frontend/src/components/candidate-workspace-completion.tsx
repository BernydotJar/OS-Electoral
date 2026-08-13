import { randomUUID } from "node:crypto";
import type { ReactNode } from "react";

import type {
  CandidateAttribute,
  CandidateClaim,
  CandidateContradiction,
  CandidateDevelopmentGoal,
  CandidateEvidence,
  CandidateReputationRisk,
  CandidateSection,
  CandidateWorkspaceProjection,
} from "@/lib/contracts";
import type { Dictionary, Locale } from "@/lib/i18n";
import type { CandidateWorkspaceCapabilities } from "@/lib/journey-capabilities";

type Props = Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  demo: boolean;
  workspace: CandidateWorkspaceProjection;
  capabilities: CandidateWorkspaceCapabilities;
}>;

const CLAIM_SECTIONS = ["identity", "biography", "purpose"] as const;
const CLAIM_STATUSES = [
  "UNKNOWN",
  "SELF_REPORTED",
  "UNDER_REVIEW",
  "EVIDENCE_PARTIAL",
  "VERIFIED",
  "REJECTED",
  "CONTRADICTED",
] as const;
const CLASSIFICATIONS = [
  "OFFICIAL_SOURCE",
  "CAMPAIGN_RESEARCH",
  "PERCEPTION",
  "HYPOTHESIS",
  "UNKNOWN",
] as const;

function HiddenFields({
  locale,
  workspace,
  section,
  recordId,
}: Readonly<{
  locale: Locale;
  workspace: CandidateWorkspaceProjection;
  section: CandidateSection;
  recordId?: string | null;
}>) {
  return (
    <>
      <input type="hidden" name="locale" value={locale} />
      <input type="hidden" name="version" value={workspace.version} />
      <input
        type="hidden"
        name="idempotency_key"
        value={`candidate-${section}:${randomUUID()}`}
      />
      <input type="hidden" name="section" value={section} />
      <input type="hidden" name="section_action" value="save" />
      <input type="hidden" name="record_id" value={recordId ?? ""} />
    </>
  );
}

function EvidenceChoices({
  dictionary,
  evidence,
  name,
  selected,
  perceptionOnly = false,
}: Readonly<{
  dictionary: Dictionary;
  evidence: readonly CandidateEvidence[];
  name: string;
  selected: readonly string[];
  perceptionOnly?: boolean;
}>) {
  const options = perceptionOnly
    ? evidence.filter((item) => item.classification === "PERCEPTION")
    : evidence;
  if (options.length === 0) {
    return <p className="candidate-option-empty">{dictionary.candidate.notAssessed}</p>;
  }
  return (
    <div className="candidate-evidence-options">
      {options.map((item) => (
        <label key={`${name}-${item.id}`}>
          <input
            type="checkbox"
            name={name}
            value={item.id}
            defaultChecked={selected.includes(item.id)}
          />
          <span>
            <strong>{item.title}</strong>
            <small>
              {dictionary.candidate.evidenceClassificationLabels[item.classification]}
              {item.source_authority ? ` · ${item.source_authority}` : ""}
            </small>
          </span>
        </label>
      ))}
    </div>
  );
}

function ClaimFields({
  dictionary,
  workspace,
  record,
  defaultLabel,
}: Readonly<{
  dictionary: Dictionary;
  workspace: CandidateWorkspaceProjection;
  record: CandidateClaim | null;
  defaultLabel: string;
}>) {
  return (
    <div className="candidate-form-grid">
      <label>
        <span>{dictionary.candidate.claimLabel}</span>
        <input
          name="label"
          required
          maxLength={120}
          defaultValue={record?.label ?? defaultLabel}
        />
      </label>
      <label>
        <span>{dictionary.candidate.claimStatus}</span>
        <select name="status" defaultValue={record?.status ?? "UNDER_REVIEW"}>
          {CLAIM_STATUSES.map((status) => (
            <option key={status} value={status}>
              {dictionary.candidate.claimStatusLabels[status]}
            </option>
          ))}
        </select>
      </label>
      <label className="field-wide">
        <span>{dictionary.candidate.claimText}</span>
        <textarea
          name="claim"
          required
          maxLength={2000}
          rows={4}
          defaultValue={record?.claim ?? ""}
        />
      </label>
      <label>
        <span>{dictionary.candidate.claimClassification}</span>
        <select
          name="classification"
          defaultValue={record?.classification ?? "OFFICIAL_SOURCE"}
        >
          {CLASSIFICATIONS.map((classification) => (
            <option key={classification} value={classification}>
              {dictionary.candidate.evidenceClassificationLabels[classification]}
            </option>
          ))}
        </select>
      </label>
      <fieldset className="candidate-evidence-fieldset field-wide">
        <legend>{dictionary.candidate.linkedEvidence}</legend>
        <EvidenceChoices
          dictionary={dictionary}
          evidence={workspace.evidence}
          name="evidence_refs"
          selected={record?.evidence_refs ?? []}
        />
        <small>{dictionary.candidate.evidenceHelp}</small>
      </fieldset>
    </div>
  );
}

function Footer({ dictionary }: { dictionary: Dictionary }) {
  return (
    <div className="candidate-form-actions">
      <p>{dictionary.candidate.approvalResetWarning}</p>
      <button type="submit">{dictionary.candidate.saveSectionAction}</button>
    </div>
  );
}

function ClaimEditor({
  locale,
  dictionary,
  workspace,
  section,
  record,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  workspace: CandidateWorkspaceProjection;
  section: (typeof CLAIM_SECTIONS)[number];
  record: CandidateClaim | null;
}>) {
  return (
    <details id={`candidate-edit-${section}`} className="candidate-section-editor">
      <summary>
        <span>{dictionary.candidate.checkLabels[section]}</span>
        <small>{record ? dictionary.candidate.savedRecord : dictionary.candidate.editSection}</small>
      </summary>
      <form action="/api/ui/candidate-workspace/section" method="post">
        <HiddenFields
          locale={locale}
          workspace={workspace}
          section={section}
          recordId={record?.id}
        />
        <ClaimFields
          dictionary={dictionary}
          workspace={workspace}
          record={record}
          defaultLabel={dictionary.candidate.sectionLabels[section]}
        />
        <Footer dictionary={dictionary} />
      </form>
    </details>
  );
}

function ValueForm({
  locale,
  dictionary,
  workspace,
  record,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  workspace: CandidateWorkspaceProjection;
  record: CandidateClaim | null;
}>) {
  return (
    <form action="/api/ui/candidate-workspace/section" method="post">
      <HiddenFields
        locale={locale}
        workspace={workspace}
        section="values"
        recordId={record?.id}
      />
      <h4>{record ? record.label : dictionary.candidate.newRecord}</h4>
      <ClaimFields
        dictionary={dictionary}
        workspace={workspace}
        record={record}
        defaultLabel=""
      />
      <Footer dictionary={dictionary} />
    </form>
  );
}

function AttributeForm({
  locale,
  dictionary,
  workspace,
  record,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  workspace: CandidateWorkspaceProjection;
  record: CandidateAttribute | null;
}>) {
  return (
    <form action="/api/ui/candidate-workspace/section" method="post">
      <HiddenFields
        locale={locale}
        workspace={workspace}
        section="attributes"
        recordId={record?.id}
      />
      <h4>{record ? record.name : dictionary.candidate.newRecord}</h4>
      <div className="candidate-form-grid">
        <label>
          <span>{dictionary.candidate.attributeName}</span>
          <input name="name" required maxLength={160} defaultValue={record?.name ?? ""} />
        </label>
        <label>
          <span>{dictionary.candidate.claimStatus}</span>
          <select name="status" defaultValue={record?.status ?? "UNDER_REVIEW"}>
            {CLAIM_STATUSES.map((status) => (
              <option key={status} value={status}>
                {dictionary.candidate.claimStatusLabels[status]}
              </option>
            ))}
          </select>
        </label>
        <label className="field-wide">
          <span>{dictionary.candidate.claimText}</span>
          <textarea
            name="claim"
            required
            maxLength={2000}
            rows={4}
            defaultValue={record?.claim ?? ""}
          />
        </label>
        <label>
          <span>{dictionary.candidate.candidateAssessment}</span>
          <select
            name="candidate_self_assessment"
            defaultValue={record?.candidate_self_assessment ?? "UNKNOWN"}
          >
            {Object.entries(dictionary.candidate.yesNoUnknownLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label>
          <span>{dictionary.candidate.teamAssessment}</span>
          <select name="team_assessment" defaultValue={record?.team_assessment ?? "UNKNOWN"}>
            {Object.entries(dictionary.candidate.teamAssessmentLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label>
          <span>{dictionary.candidate.citizenEvidence}</span>
          <select name="citizen_evidence" defaultValue={record?.citizen_evidence ?? "UNRESOLVED"}>
            {Object.entries(dictionary.candidate.citizenEvidenceLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label>
          <span>{dictionary.candidate.attributeRisk}</span>
          <input name="risk" required maxLength={1000} defaultValue={record?.risk ?? ""} />
        </label>
        <fieldset className="candidate-evidence-fieldset field-wide">
          <legend>{dictionary.candidate.linkedEvidence}</legend>
          <EvidenceChoices
            dictionary={dictionary}
            evidence={workspace.evidence}
            name="evidence_refs"
            selected={record?.evidence_refs ?? []}
          />
          <small>{dictionary.candidate.evidenceHelp}</small>
        </fieldset>
        <fieldset className="candidate-evidence-fieldset field-wide">
          <legend>{dictionary.candidate.perceptionEvidence}</legend>
          <EvidenceChoices
            dictionary={dictionary}
            evidence={workspace.evidence}
            name="perception_refs"
            selected={record?.perception_refs ?? []}
            perceptionOnly
          />
        </fieldset>
        <fieldset className="candidate-evidence-fieldset field-wide">
          <legend>{dictionary.candidate.contradictionLinks}</legend>
          {(workspace.contradictions ?? []).length === 0 ? (
            <p className="candidate-option-empty">{dictionary.candidate.noItems}</p>
          ) : (
            <div className="candidate-evidence-options">
              {(workspace.contradictions ?? []).map((item) => (
                <label key={item.id}>
                  <input
                    type="checkbox"
                    name="contradiction_refs"
                    value={item.id}
                    defaultChecked={record?.contradiction_refs.includes(item.id) ?? false}
                  />
                  <span><strong>{item.description}</strong></span>
                </label>
              ))}
            </div>
          )}
        </fieldset>
      </div>
      <Footer dictionary={dictionary} />
    </form>
  );
}

function CollectionEditor({
  id,
  title,
  dictionary,
  children,
}: Readonly<{
  id: string;
  title: string;
  dictionary: Dictionary;
  children: ReactNode;
}>) {
  return (
    <details id={id} className="candidate-section-editor">
      <summary>
        <span>{title}</span>
        <small>{dictionary.candidate.editSection}</small>
      </summary>
      <div className="candidate-record-stack">{children}</div>
    </details>
  );
}

function candidateSubjects(
  dictionary: Dictionary,
  workspace: CandidateWorkspaceProjection,
): readonly Readonly<{ id: string; label: string }>[] {
  const options = [
    { id: workspace.candidate_id, label: workspace.display_name },
    ...workspace.evidence.map((item) => ({
      id: item.id,
      label: `${dictionary.candidate.evidenceViewLabel}: ${item.title}`,
    })),
  ];
  for (const [section, record] of [
    ["identity", workspace.identity],
    ["biography", workspace.biography],
    ["purpose", workspace.purpose],
  ] as const) {
    if (record) {
      options.push({
        id: record.id,
        label: `${dictionary.candidate.sectionLabels[section]}: ${record.label}`,
      });
    }
  }
  for (const record of workspace.values ?? []) {
    options.push({ id: record.id, label: `${dictionary.candidate.values}: ${record.label}` });
  }
  for (const record of workspace.attributes ?? []) {
    options.push({ id: record.id, label: `${dictionary.candidate.attributes}: ${record.name}` });
  }
  return options;
}

function ContradictionForm({
  locale,
  dictionary,
  workspace,
  record,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  workspace: CandidateWorkspaceProjection;
  record: CandidateContradiction | null;
}>) {
  return (
    <form action="/api/ui/candidate-workspace/section" method="post">
      <HiddenFields
        locale={locale}
        workspace={workspace}
        section="contradictions"
        recordId={record?.id}
      />
      <h4>{record ? dictionary.candidate.savedRecord : dictionary.candidate.newRecord}</h4>
      <div className="candidate-form-grid">
        <label>
          <span>{dictionary.candidate.contradictionSubject}</span>
          <select name="subject_ref" required defaultValue={record?.subject_ref ?? workspace.candidate_id}>
            {candidateSubjects(dictionary, workspace).map((subject) => (
              <option key={subject.id} value={subject.id}>{subject.label}</option>
            ))}
          </select>
        </label>
        <label>
          <span>{dictionary.candidate.riskStatus}</span>
          <select name="status" defaultValue={record?.status ?? "UNDER_REVIEW"}>
            {Object.entries(dictionary.candidate.contradictionStatusLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label className="field-wide">
          <span>{dictionary.candidate.contradictionDescription}</span>
          <textarea name="description" required maxLength={2000} rows={4} defaultValue={record?.description ?? ""} />
        </label>
        <fieldset className="candidate-evidence-fieldset field-wide">
          <legend>{dictionary.candidate.linkedEvidence}</legend>
          <EvidenceChoices
            dictionary={dictionary}
            evidence={workspace.evidence}
            name="evidence_refs"
            selected={record?.evidence_refs ?? []}
          />
        </fieldset>
      </div>
      <Footer dictionary={dictionary} />
    </form>
  );
}

function DevelopmentForm({
  locale,
  dictionary,
  workspace,
  record,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  workspace: CandidateWorkspaceProjection;
  record: CandidateDevelopmentGoal | null;
}>) {
  return (
    <form action="/api/ui/candidate-workspace/section" method="post">
      <HiddenFields
        locale={locale}
        workspace={workspace}
        section="development_goals"
        recordId={record?.id}
      />
      <h4>{record ? record.area : dictionary.candidate.newRecord}</h4>
      <div className="candidate-form-grid">
        <label>
          <span>{dictionary.candidate.developmentArea}</span>
          <input name="area" required maxLength={160} defaultValue={record?.area ?? ""} />
        </label>
        <label>
          <span>{dictionary.candidate.riskStatus}</span>
          <select name="status" defaultValue={record?.status ?? "OPEN"}>
            {Object.entries(dictionary.candidate.developmentStatusLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label className="field-wide">
          <span>{dictionary.candidate.developmentObjective}</span>
          <textarea name="objective" required maxLength={2000} rows={4} defaultValue={record?.objective ?? ""} />
        </label>
        <fieldset className="candidate-evidence-fieldset field-wide">
          <legend>{dictionary.candidate.linkedEvidence}</legend>
          <EvidenceChoices
            dictionary={dictionary}
            evidence={workspace.evidence}
            name="evidence_refs"
            selected={record?.evidence_refs ?? []}
          />
        </fieldset>
      </div>
      <Footer dictionary={dictionary} />
    </form>
  );
}

function RiskForm({
  locale,
  dictionary,
  workspace,
  record,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  workspace: CandidateWorkspaceProjection;
  record: CandidateReputationRisk | null;
}>) {
  return (
    <form action="/api/ui/candidate-workspace/section" method="post">
      <HiddenFields
        locale={locale}
        workspace={workspace}
        section="reputation"
        recordId={record?.id}
      />
      <h4>{record ? record.title : dictionary.candidate.newRecord}</h4>
      <div className="candidate-form-grid">
        <label>
          <span>{dictionary.candidate.riskTitle}</span>
          <input name="title" required maxLength={255} defaultValue={record?.title ?? ""} />
        </label>
        <label>
          <span>{dictionary.candidate.riskSeverity}</span>
          <select name="severity" defaultValue={record?.severity ?? "MEDIUM"}>
            {Object.entries(dictionary.candidate.riskSeverityLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label>
          <span>{dictionary.candidate.riskStatus}</span>
          <select name="status" defaultValue={record?.status ?? "OPEN"}>
            {Object.entries(dictionary.candidate.riskStatusLabels).map(([value, label]) => (
              <option key={value} value={value}>{label}</option>
            ))}
          </select>
        </label>
        <label className="candidate-check-control">
          <input type="checkbox" name="decision_required" value="true" defaultChecked={record?.decision_required ?? false} />
          <span>{dictionary.candidate.riskDecisionRequired}</span>
        </label>
        <label className="field-wide">
          <span>{dictionary.candidate.riskDescription}</span>
          <textarea name="description" required maxLength={2000} rows={4} defaultValue={record?.description ?? ""} />
        </label>
        <fieldset className="candidate-evidence-fieldset field-wide">
          <legend>{dictionary.candidate.linkedEvidence}</legend>
          <EvidenceChoices
            dictionary={dictionary}
            evidence={workspace.evidence}
            name="evidence_refs"
            selected={record?.evidence_refs ?? []}
          />
        </fieldset>
      </div>
      <Footer dictionary={dictionary} />
    </form>
  );
}

function EmptyReview({
  locale,
  dictionary,
  workspace,
  section,
  label,
}: Readonly<{
  locale: Locale;
  dictionary: Dictionary;
  workspace: CandidateWorkspaceProjection;
  section: "contradictions" | "reputation";
  label: string;
}>) {
  return (
    <form className="candidate-empty-review" action="/api/ui/candidate-workspace/section" method="post">
      <input type="hidden" name="locale" value={locale} />
      <input type="hidden" name="version" value={workspace.version} />
      <input type="hidden" name="idempotency_key" value={`candidate-${section}-review:${randomUUID()}`} />
      <input type="hidden" name="section" value={section} />
      <input type="hidden" name="section_action" value="review_empty" />
      <input type="hidden" name="record_id" value="" />
      <p>{dictionary.candidate.approvalResetWarning}</p>
      <button type="submit">{label}</button>
    </form>
  );
}

export function CandidateWorkspaceCompletion({
  locale,
  dictionary,
  demo,
  workspace,
  capabilities,
}: Props) {
  const canEdit = !demo && capabilities.canRead && capabilities.canUpdate;
  const incomplete = workspace.checks.filter((check) => !check.complete);
  return (
    <section id="candidate-completion" className="candidate-completion-panel" aria-labelledby="candidate-completion-title">
      <div className="candidate-completion-heading">
        <div>
          <p className="eyebrow">{dictionary.candidate.completionEyebrow}</p>
          <h3 id="candidate-completion-title">{dictionary.candidate.completionTitle}</h3>
          <p>{dictionary.candidate.completionBody}</p>
        </div>
        <span className="version-chip">{dictionary.candidate.currentVersion} {workspace.version}</span>
      </div>
      {incomplete.length > 0 ? (
        <nav className="candidate-completion-links" aria-label={dictionary.candidate.sections}>
          {incomplete.map((check) => (
            <a
              key={check.key}
              href={`#${check.key === "approvals" ? "candidate-approvals" : `candidate-edit-${check.key}`}`}
            >
              {dictionary.candidate.checkLabels[check.key]}
            </a>
          ))}
        </nav>
      ) : null}
      {!canEdit ? (
        <p className="candidate-completion-read-only" role="status">{dictionary.candidate.completionReadOnly}</p>
      ) : (
        <div className="candidate-editor-list">
          {CLAIM_SECTIONS.map((section) => (
            <ClaimEditor
              key={section}
              locale={locale}
              dictionary={dictionary}
              workspace={workspace}
              section={section}
              record={workspace[section]}
            />
          ))}
          <CollectionEditor id="candidate-edit-values" title={dictionary.candidate.checkLabels.values} dictionary={dictionary}>
            {(workspace.values ?? []).map((record) => (
              <ValueForm key={record.id} locale={locale} dictionary={dictionary} workspace={workspace} record={record} />
            ))}
            <ValueForm locale={locale} dictionary={dictionary} workspace={workspace} record={null} />
          </CollectionEditor>
          <CollectionEditor id="candidate-edit-attributes" title={dictionary.candidate.checkLabels.attributes} dictionary={dictionary}>
            {(workspace.attributes ?? []).map((record) => (
              <AttributeForm key={record.id} locale={locale} dictionary={dictionary} workspace={workspace} record={record} />
            ))}
            <AttributeForm locale={locale} dictionary={dictionary} workspace={workspace} record={null} />
          </CollectionEditor>
          <CollectionEditor id="candidate-edit-contradictions" title={dictionary.candidate.checkLabels.contradictions} dictionary={dictionary}>
            {workspace.contradictions === null ? (
              <EmptyReview locale={locale} dictionary={dictionary} workspace={workspace} section="contradictions" label={dictionary.candidate.reviewNoContradictions} />
            ) : null}
            {(workspace.contradictions ?? []).map((record) => (
              <ContradictionForm key={record.id} locale={locale} dictionary={dictionary} workspace={workspace} record={record} />
            ))}
            <ContradictionForm locale={locale} dictionary={dictionary} workspace={workspace} record={null} />
          </CollectionEditor>
          <CollectionEditor id="candidate-edit-development_goals" title={dictionary.candidate.checkLabels.development_goals} dictionary={dictionary}>
            {(workspace.development_goals ?? []).map((record) => (
              <DevelopmentForm key={record.id} locale={locale} dictionary={dictionary} workspace={workspace} record={record} />
            ))}
            <DevelopmentForm locale={locale} dictionary={dictionary} workspace={workspace} record={null} />
          </CollectionEditor>
          <CollectionEditor id="candidate-edit-reputation" title={dictionary.candidate.checkLabels.reputation} dictionary={dictionary}>
            {workspace.reputation_risks === null ? (
              <EmptyReview locale={locale} dictionary={dictionary} workspace={workspace} section="reputation" label={dictionary.candidate.reviewNoReputationRisks} />
            ) : null}
            {(workspace.reputation_risks ?? []).map((record) => (
              <RiskForm key={record.id} locale={locale} dictionary={dictionary} workspace={workspace} record={record} />
            ))}
            <RiskForm locale={locale} dictionary={dictionary} workspace={workspace} record={null} />
          </CollectionEditor>
          <details id="candidate-approvals" className="candidate-section-editor candidate-approvals-editor">
            <summary>
              <span>{dictionary.candidate.approvalsTitle}</span>
              <small>{workspace.current_approved_sections.length}/{workspace.approvable_sections.length}</small>
            </summary>
            <div className="candidate-approval-body">
              <p>{dictionary.candidate.approvalsBody}</p>
              {workspace.approvals_required.length === 0 ? (
                <p className="candidate-option-empty">{dictionary.candidate.noItems}</p>
              ) : !capabilities.canApprove ? (
                <p className="candidate-completion-read-only" role="status">{dictionary.candidate.approvalPermissionMissing}</p>
              ) : (
                <div className="candidate-approval-list">
                  {workspace.approvals_required.map((section) => (
                    <form key={section} action="/api/ui/candidate-workspace/approval" method="post">
                      <input type="hidden" name="locale" value={locale} />
                      <input type="hidden" name="version" value={workspace.version} />
                      <input type="hidden" name="idempotency_key" value={`candidate-approval:${randomUUID()}`} />
                      <input type="hidden" name="section" value={section} />
                      <strong>{dictionary.candidate.sectionLabels[section]}</strong>
                      <label>
                        <span>{dictionary.candidate.approvalReason}</span>
                        <textarea name="reason" required maxLength={1000} rows={3} placeholder={dictionary.candidate.approvalReasonPlaceholder} />
                      </label>
                      <button type="submit">{dictionary.candidate.approveSectionAction}</button>
                    </form>
                  ))}
                </div>
              )}
            </div>
          </details>
        </div>
      )}
    </section>
  );
}
