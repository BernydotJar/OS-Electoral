# OS Electoral

OS Electoral is a War Room operating system for building an evidence-led campaign workflow.

The repository is currently in **Cycle 0: War Room Initialization**. The goal is to create a shared, verifiable campaign state before producing content, paid media, or field operations.

## Current Gate

The campaign cannot move into tactics until these five lines are completed and approved:

```text
90-day political objective:
Current campaign stage:
Electoral territory:
Priority segment:
Available evidence or documents:
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

