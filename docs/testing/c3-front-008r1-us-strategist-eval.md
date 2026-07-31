# Candidate Workspace evaluation — United States campaign strategist

## Evaluation question

Could an experienced United States campaign strategist use the current Candidate Workspace productively and safely?

## Evidence reviewed

- `docs/product/candidate-workspace.md`
- candidate action, profile/risk and evidence views
- exact-authorized dossier creation and source append workflow
- bilingual ES/EN contracts
- current automated contract and browser gates

## Verdict

**Qualified yes for internal candidate research and decision preparation; no for complete United States campaign operations or production deployment.**

A strategist can use the current workspace to organize a defensible candidate brief, preserve source provenance, separate verified evidence from perception and hypothesis, surface contradictions and reputation risks, and identify pending human decisions. That is a real operational job and the interface is materially safer than a generic candidate-scoring or AI recommendation surface.

The workspace is not yet a complete United States strategist workbench. It lacks jurisdiction-configurable compliance, editable governed claim/risk workflows in the live shell, real identity-provider evidence, campaign-calendar and filing integrations, reviewer assignment/disposition, and independent acceptance by an operating campaign team.

## Rubric

| Dimension | Result | Evaluation |
|---|---|---|
| Executive orientation | PASS | The three views separate immediate work, profile/risk context, and source entry instead of presenting one undifferentiated dossier. |
| Evidence provenance | PASS | Sources preserve classification, HTTPS reference, authority, jurisdiction, observed date, note, version and idempotency. |
| Epistemic discipline | PASS | Candidate assertions, campaign research, perception, hypothesis, contradiction and verified evidence remain distinct. |
| Risk visibility | PASS | Open critical/high reputation risks and contradictions remain visible and block premature completion. |
| Human authority | PASS | Internal approval does not authorize public positioning, strategy, content, spending, publication or contact. |
| Anti-profiling boundary | PASS | Unknown fields and attempted profiling-score fields fail closed; the product does not infer voter response or candidate electability. |
| English-language usability | PASS WITH HUMAN ACCEPTANCE PENDING | English contracts and automated browser journeys exist; independent review by a United States strategist has not been recorded. |
| Live editing completeness | PARTIAL | The shell can create a dossier and append sources, but cannot yet edit claims, biography, purpose, values, attributes, contradictions, development goals or reputation risks. |
| Review workflow | PARTIAL | Backend version-bound approvals exist, while reviewer assignment, disposition and complete live approval UX remain unfinished. |
| United States jurisdiction support | NOT IMPLEMENTED | No federal/state/local configuration, filing calendar, disclaimer policy, legal-review template or jurisdiction-specific evidence pack exists. |
| Real operational integrations | NOT IMPLEMENTED | No production identity, document repository, calendar, compliance, CRM, finance, field or media system is integrated or approved. |
| Production readiness | BLOCKED | Staging, live identity, managed operations, independent security/privacy/legal review and production approval remain absent. |

## What a strategist can do now

1. create an internal candidate dossier after the campaign foundation is ready;
2. register official, campaign-research, perception, hypothesis or unknown sources;
3. inspect the current evidence inventory, pending checks, contradictions, risks and approvals;
4. use the deterministic action brief to decide what research or human review is required next;
5. keep public-use status blocked while preparing a defensible internal recommendation.

## What the product must not imply

- that attributes predict voter behavior;
- that a risk score determines electability;
- that an internal approval permits a public claim;
- that a source automatically verifies a statement;
- that this workspace replaces campaign counsel, compliance, security, communications or political judgment.

## Highest-value completion path

1. add exact-authorized editing for the canonical candidate sections with optimistic concurrency and evidence-reference validation;
2. add governed reviewer assignment and section disposition in the live shell;
3. add jurisdiction-configurable policy packs rather than hard-coding United States assumptions;
4. validate English terminology and workflow with an independent United States strategist and counsel;
5. integrate production identity and approved document/calendar boundaries before any live campaign claim.

## Release decision

`PASS_INTERNAL_RESEARCH_AND_DECISION_PREP`

`DENY_COMPLETE_US_CAMPAIGN_OPERATIONS_CLAIM`

`DENY_PRODUCTION_RELEASE`
