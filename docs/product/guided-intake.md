# Guided campaign intake product contract

The guided intake is the first operational roadmap for a campaign that is ready to begin structured work. It converts server-owned campaign setup into a bounded inventory of context, current capacity, unknowns and evidence needs. It deliberately stops before strategy.

## Users and job

Primary users are campaign directors, political advisers, candidates and authorized operators who may not be technically sophisticated. Their job is to understand where to begin, what information is missing and what evidence must be collected before strategic recommendations are considered.

The surface therefore prioritizes a plain-language ordered route rather than a generic dashboard. Technical reason codes and audit receipts remain visible as secondary evidence.

```yaml
design_variance: 4
motion_intensity: 2
visual_density: 7
```

The interface uses the existing Premium Slate design system, responsive two-column information density on larger screens and a single-column route on narrow screens. No new non-essential motion was introduced. Existing reduced-motion behavior remains authoritative.

## User outcome

An authorized operator can start or resume one intake, record the target office and candidate project, assess existing team, assets and budget evidence, identify known unknowns and define evidence requirements. CampaignOS then identifies the first incomplete section or, when all sections are complete, a fixed research-first sequence.

## Canonical route

1. confirm campaign operational setup;
2. define the target office;
3. describe the candidate project;
4. assess the current team;
5. assess current assets;
6. assess budget evidence;
7. record known unknowns;
8. define required evidence.

A list may be empty after assessment. `null` means the section has not been assessed. Known unknowns and evidence requirements require at least one item because an empty set cannot establish the research agenda.

## States

- `BLOCKED_BY_CAMPAIGN_SETUP`: campaign metadata or an active workspace is missing;
- `IN_PROGRESS`: campaign setup is valid but at least one intake section remains incomplete;
- `READY_FOR_RESEARCH`: all eight checks are complete and the bounded evidence-collection sequence is available.

`READY_FOR_RESEARCH` is a completeness state only. It is not strategy, candidate approval, political approval, legal approval, budget approval, publication approval or production approval.

The read-only shell separately represents:

- intake available;
- intake not started;
- exact review authorization absent;
- dependency temporarily unavailable.

It never substitutes synthetic or partial data in a live session.

## Research-first actions

When ready, the system exposes exactly these bounded activities:

1. verify office and jurisdiction evidence;
2. validate candidate-project evidence;
3. assess team-capacity gaps;
4. inventory asset provenance;
5. document budget assumptions;
6. research known unknowns;
7. collect required evidence.

These are internal research instructions. They do not contact citizens, profile voters, activate field work, spend, publish, mobilize or call an external AI/provider.

## Evidence and authority

Campaign name, jurisdiction, stage, version, status and active-workspace count come from server-owned CampaignOS records. Every API operation requires an exact tenant/campaign/action/resource/purpose grant. Roles and UI visibility never authorize.

The frontend validates the complete upstream contract at runtime. It rejects unknown fields, cross-scope identifiers, non-canonical order, inconsistent totals, contradictory source fields/checks, invalid next actions, early research actions and missing mandatory limitations.

Successful start, resume, read and update operations create audit evidence. Create and update emit internal no-effect outbox rows. No external effect is executed.

## Non-goals

The intake does not:

- recommend political strategy;
- infer or store voter preference;
- score persuadability;
- approve a candidate, budget or action;
- create roles, grants or authority;
- contact citizens;
- produce or publish content;
- activate paid media or field mobilization;
- duplicate municipal/legal evidence owned by LA Muni RAG.

## Current limitation

The backend supports authenticated exact-authorized create/resume/read/update. The current dynamic shell displays a verified read-only roadmap. A full non-technical editing journey, human user-acceptance review and live identity/tenant selection remain future increments.