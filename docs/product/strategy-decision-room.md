# Evidence-first Strategy and Decision Room

`C3-STRATEGY-001` adds a campaign-scoped internal decision room. It helps authorized campaign leadership compare evidence, assumptions, hypotheses, options, measurable objectives, contradictions, and adversarial findings. It does not create political authority or execute a campaign action.

## Product jobs

The surface answers five internal questions:

1. Which statements are verified, inferred, or still unknown?
2. Which assumptions and hypotheses could be falsified, and by what signal?
3. Which internal options are comparable on evidence, benefits, risks, and tradeoffs?
4. Which measurable objectives have an accountable Team Builder role?
5. Is the exact current version ready for an authorized human decision?

## Evidence classes

- `VERIFIED`: accepted evidence with an explicit source, authority, jurisdiction, and collection time.
- `INFERRED`: a reviewable inference with provenance; never presented as verified fact.
- `UNKNOWN`: an explicit evidence gap that cannot claim a source, authority, or jurisdiction.

Unknown evidence, rejected evidence, unsupported references, and false provenance fail closed.

## Readiness model

The status is deterministic:

- `EVIDENCE_REQUIRED`: no accepted verified evidence exists or an unknown remains;
- `CONTRADICTIONS_OPEN`: material contradictions remain unresolved;
- `RED_TEAM_BLOCKED`: an open CRITICAL or HIGH adversarial finding remains;
- `OPTIONS_INCOMPLETE`: fewer than two complete comparable options exist;
- `OBJECTIVES_INCOMPLETE`: no measurable objective exists;
- `READY_FOR_HUMAN_DECISION`: evidence, options, objectives, contradictions, and red-team gates are complete;
- `DECIDED_INTERNAL`: an authorized human decision receipt exists for the exact current version.

Readiness is not approval. Only the separate exact-authorized decision action creates an internal decision receipt.

## Version and provenance binding

A workspace persists the exact versions of Campaign, Candidate Workspace, and Team Builder that supported it, together with the exact set of known Team Builder role IDs. A decision receipt binds:

- strategy workspace ID and version;
- selected option;
- authorized human role;
- reason;
- approval receipt;
- decision timestamp.

Updating strategy content creates a new version and invalidates current decision completeness. Historical decision receipts remain append-only and continue to project the prerequisite versions and role snapshot that originally supported them.

## Human authority boundary

The Decision Room may organize and compare internal options. It cannot:

- approve public positioning;
- generate or activate targeting;
- infer individual political preferences;
- score voter likelihood or persuadability;
- create psychographic profiles;
- generate a contact list;
- contact citizens;
- publish content;
- approve or execute spending;
- mobilize;
- call an external provider;
- create any other external effect.

Every projection retains `authority_effect=NONE` and `external_effects=NONE`. A recorded decision is internal evidence only and does not authorize downstream execution.

## User experience

The ES/EN read-only surface presents:

- readiness and next human action;
- verified, inferred, and unknown evidence counts;
- open contradictions and CRITICAL/HIGH findings;
- comparable options with benefits, risks, and tradeoffs;
- measurable objectives with baseline, target, deadline, and owner;
- an exact-version human decision receipt when one exists;
- audit receipt and mandatory limitations.

The shell fails closed for missing exact authorization, absent workspace, dependency failure, invalid upstream data, tenant/campaign scope drift, false provenance, stale decisions, and hidden profiling fields.

## Explicitly out of scope

- public strategy or positioning approval;
- message or content generation;
- targeting or audience selection;
- citizen data, contact, outreach, or mobilization;
- external research/provider calls;
- authenticated browser mutation flows;
- live OIDC, cloud deployment, or production approval.
