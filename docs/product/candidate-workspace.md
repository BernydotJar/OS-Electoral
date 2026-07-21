# Candidate evidence workspace

The candidate workspace is an internal, evidence-governed surface for understanding a candidate before strategy, positioning, content, outreach or external execution. It preserves the distinction between what the candidate says, what campaign research supports, what remains perception or hypothesis, what contradicts the record, what development is required and what risks still need a human decision.

## Users and job

Primary users are candidates, campaign directors, political advisers and authorized reviewers. Their job is to build a verifiable internal record and decide what still requires evidence or development. The workspace is designed for non-technical users and presents an ordered executive route rather than a generic profile or score.

```yaml
design_variance: 4
motion_intensity: 2
visual_density: 7
```

The current dynamic shell is read-only, responsive and bilingual. It preserves technical reason codes and audit receipts as secondary evidence while using plain-language labels for the primary journey.

## Canonical sections

1. identity;
2. biography;
3. purpose;
4. values;
5. attributes;
6. contradictions;
7. development goals;
8. reputation risks;
9. current version-bound section approvals.

Each factual claim marked `VERIFIED` requires accepted independent evidence classified as `OFFICIAL_SOURCE` or `CAMPAIGN_RESEARCH`. Candidate self-assessment cannot verify an attribute by itself. Perception references must point only to `PERCEPTION` evidence. Attribute contradiction references must point to candidate-workspace contradiction records, not to arbitrary evidence IDs.

## States

- `SETUP_REQUIRED`: identity, biography or purpose is absent;
- `UNDER_REVIEW`: at least one evidence section is incomplete or a critical/high reputation risk remains open;
- `AWAITING_APPROVAL`: all evidence sections are complete but one or more current-version section approvals are missing;
- `INTERNALLY_APPROVED`: every evidence section is complete and has a receipt for the exact current workspace version.

`INTERNALLY_APPROVED` never changes `public_use_status`, which remains `BLOCKED`. It is not public-positioning approval, strategy approval, legal approval, spending approval, publication approval or production approval.

## Approval semantics

Approvals are append-only receipts bound to:

- tenant;
- campaign;
- candidate workspace;
- exact section;
- exact workspace version;
- principal;
- exact authorization grant;
- approval receipt;
- reason;
- timestamp.

Updating any evidence or display field increments the workspace version. Earlier receipts remain in history but no longer satisfy current approval completeness. A section cannot be approved until its evidence check is complete.

## Evidence and risk rules

- unknown evidence or contradiction references fail closed;
- duplicate or colliding record IDs are rejected;
- lists and text are bounded;
- unknown fields are forbidden, including attempted profiling-score fields;
- open `CRITICAL` or `HIGH` reputation risks keep the reputation section incomplete;
- empty contradiction and reputation lists mean those sections were reviewed and no items were recorded;
- `null` means the section is not yet assessed;
- all successful writes produce atomic audit and internal outbox evidence with `external_effects=NONE`.

## Mandatory limitations

```text
NOT_PUBLIC_POSITIONING_APPROVAL
NOT_A_STRATEGY
NO_VOTER_PROFILING
NO_EXTERNAL_EFFECTS
HUMAN_REVIEW_REQUIRED
```

## Non-goals

The workspace does not:

- infer political preference or sensitive traits;
- score voters, persuadability, electability or psychological susceptibility;
- recommend strategy from candidate attributes;
- approve public claims or content;
- contact citizens;
- activate media, field work, spending or mobilization;
- call an external AI, research provider or publication system;
- replace legal, political, security or communications review.

## Current limitation

The backend supports exact-authorized create/read/update and current-version section approval. The current shell displays a verified read-only executive projection. Authenticated editing, dedicated reviewer assignment, human user-acceptance testing and live identity/environment evidence remain future work.