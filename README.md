# OS Electoral

OS Electoral is a War Room operating system for building an evidence-led campaign workflow.

The repository is currently in **Cycle 1: Electoral Evidence Baseline**. Cycle 0 established the governed War Room; Cycle 1 builds a shared, verifiable evidence state before producing content, paid media, or field operations.

## Current Gate

The campaign has an approved 90-day research objective, exploratory stage and initial municipal territory. It cannot move into tactics until the remaining strategic lines are researched and approved:

```text
Priority segment:
Public positioning/message:
Budget ceiling:
Geographic mobilization priority:
```

## Repository Map

```text
campaign/    Campaign charter, current state, decisions, risks
research/    Evidence register, baseline, segments, sources
territory/   Geographic prioritization and field reports
strategy/    Objectives, narrative, message house
operations/  Weekly plan, dashboard, approvals
content/     Draft-only content assets after gates are approved
media/       Paid media and creative assets after gates are approved
prompts/     Agent loop prompts and operating instructions
archive/     Superseded decisions and old artifacts
```

## First Workflow

1. Fill `campaign/charter.md`.
2. Update `campaign/current-state.md`.
3. Register known evidence in `research/evidence-register.md`.
4. Approve or block gates in `operations/approvals.md`.
5. Run the loop in `prompts/war-room-loop.md`.

The reusable governed workspace core and CLI are documented in `docs/campaign-workspaces.md`. Eligibility produced by the core never constitutes human approval or execution authorization.
