# C1-FRONT-003 Design — Daily War Room

## Product model

The Daily War Room is a governed decision surface, not an activity feed.

```text
Signals
  ↓
Evidence
  ↓
Assessment
  ↓
Options
  ↓
Human Approval
  ↓
Assignment
  ↓
Follow-up
  ↓
Learning
```

## Architecture

- `web/data/war-room.json`: read-only operational snapshot.
- `web/war-room.js`: fetch, render and accessible signal detail lifecycle.
- `web/war-room.css`: isolated layout and responsive styles.
- `web/index.html`: third module and detail dialog hooks.
- `scripts/frontend/validate_daily_war_room.py`: fail-closed schema and safety validator.
- `scripts/frontend/runtime_visual_review.py`: browser coverage for navigation, detail, desktop and mobile.

## Information hierarchy

1. Daily operating summary.
2. Decision pipeline metrics.
3. Signal queue.
4. Pending human approvals.
5. Internal assignments and follow-up.
6. Risks and learning.
7. Closed political gates.

## Governance

- AI may organize, summarize and prepare options.
- Only a human owner may approve a sensitive decision.
- Assignments describe internal work; they do not trigger external actions.
- Evidence class and provenance remain visible at item level.
- Unknowns and hypotheses are never promoted to facts.

## Accessibility

- signal cards remain native buttons inside semantic list items;
- detail uses a modal dialog with Escape, focus trap and focus return;
- module headings accept programmatic focus;
- reduced motion disables nonessential animation;
- layout collapses to one column on mobile.

## Non-goals

No runtime agents, RAG calls, publication, messaging, targeting, media buying, field mobilization, financial execution, authentication or deployment.