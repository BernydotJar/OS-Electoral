# C1-FRONT-003 Requirements — Daily War Room

Status: APPROVED_BY_HUMAN_REQUEST
Mode: MVP
Issue: #32

## Objective

Add a read-only Daily War Room to CampaignOS that converts current evidence and internal updates into a traceable decision workflow without activating political tactics or external execution.

## Functional requirements

1. Daily War Room must be a third module beside Team Command Center and Evidence Control Room.
2. The module must present the sequence `Signals → Evidence → Assessment → Options → Human Approval → Assignment → Follow-up → Learning`.
3. Structured data must include signals, pending decisions, assignments, risks, learning notes, closed gates and an explicit safety statement.
4. Every signal must expose id, title, summary, evidence class, source, confidence, status, assessment, decision required, owner, due date, gate and blockers.
5. Allowed evidence classes are `OFFICIAL`, `CAMPAIGN_RESEARCH`, `PERCEPTION`, `HYPOTHESIS`, and `UNKNOWN`.
6. Allowed signal states are `NEW`, `ASSESSING`, `BLOCKED`, `READY_FOR_HUMAN_REVIEW`, and `CLOSED`.
7. Sensitive decisions must remain `PENDING_HUMAN_APPROVAL` or `BLOCKED`.
8. Assignments must be internal, non-executing and attributable to a human or governed department.
9. A keyboard-accessible detail panel must expose complete signal provenance and decision context.
10. Team and Evidence modules must remain unchanged and reachable.

## Data boundaries

- `web/data/war-room.json` is an operational snapshot, not new electoral evidence.
- Existing `web/data/team.json` and `web/data/status.json` must not change.
- Unknowns must remain unknown; no missing value may be inferred.
- The snapshot must not contain voter-level data, support scores, persuasion scores, sensitive traits or personal contact data.
- Current political gates must remain closed.

## Accessibility

- semantic landmarks, headings, buttons and dialog/detail semantics;
- complete keyboard operation;
- visible focus;
- Escape closes detail and returns focus;
- content understandable without color;
- mobile layout and reduced-motion support;
- no page-level horizontal overflow.

## Safety

The feature must not enable or imply public narrative generation, targeting, microtargeting, persuasion scoring, territorial ranking, paid-media activation, field mobilization, automatic publishing, citizen contact, spending, public promises, attacks or autonomous political decisions.

## Acceptance criteria

- third module renders from structured JSON;
- all required fields and evidence classes validate fail-closed;
- human approval requirements are visible;
- assignments remain internal and non-executing;
- blocked gates remain visible;
- existing validators pass;
- new validator passes;
- Playwright review covers desktop/mobile navigation and detail lifecycle;
- screenshots are produced and reviewed;
- `git diff --check` passes;
- no merge or deployment in this session.