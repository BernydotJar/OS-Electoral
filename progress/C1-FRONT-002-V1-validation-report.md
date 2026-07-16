# C1-FRONT-002-V1 — Runtime Validation and Visual Review

Status: `CI_PENDING`

Base commit: `d13b67591ba3f07e71eff18094d0b0901ce71af9`  
Working branch: `agent/c1-front-002-v1-runtime-validation`  
Tracking issue: `#28`

## Objective

Execute the browser, accessibility, responsive and visual review that remained blocked when C1-FRONT-002 was merged.

## Static review findings

Three accessibility risks were identified before runtime execution:

1. native department buttons used `role="listitem"`, overriding their button semantics;
2. the drawer backdrop could enter the keyboard focus cycle;
3. module headings were focused programmatically without explicit programmatic focus targets.

## Fixes implemented

- department buttons retain native button semantics;
- semantic `role="listitem"` wrappers are added around rendered cards;
- drawer backdrop is excluded from sequential keyboard focus;
- Team and Evidence headings use `tabindex="-1"` for programmatic focus;
- the fail-closed validator now requires these accessibility behaviors.

## Automated runtime review

Workflow:

`.github/workflows/c1-front-002-v1.yml`

Browser suite:

`scripts/frontend/runtime_visual_review.py`

The suite verifies:

- desktop viewport `1440x1000`;
- mobile viewport `390x844`;
- candidate and AI Chief of Staff hierarchy;
- ten department buttons inside ten semantic list items;
- no role override on native buttons;
- drawer opening, focus trap, Escape close and focus return;
- backdrop removal from keyboard tab order;
- Team/Evidence module switching and heading focus;
- reduced-motion behavior;
- page-level horizontal overflow;
- Chromium page scale at 200%;
- unexpected console and page errors.

## Expected artifacts

The workflow uploads `c1-front-002-v1-visual-review` containing:

- `desktop-team.png`;
- `desktop-drawer.png`;
- `desktop-evidence.png`;
- `mobile-team.png`;
- `mobile-drawer.png`;
- `runtime-review.json`;
- `server.log`.

## Validation commands

```bash
python3 scripts/frontend/validate_evidence_control_room.py
python3 scripts/frontend/validate_campaign_team_command_center.py
python3 scripts/frontend/runtime_visual_review.py
git diff --check origin/main...HEAD
```

## Current evidence

At the time this report was created:

- static fixes are committed;
- workflow and browser suite are committed;
- GitHub Actions execution is pending;
- no runtime result is marked PASS before the workflow completes;
- no screenshot is claimed before the artifact is generated.

## Safety

- no electoral evidence was changed;
- no campaign data snapshot was changed;
- no political gate was opened;
- no targeting, scoring, messaging, publishing, spending or mobilization capability was added;
- no merge or deployment is authorized by this increment.

## Completion rule

Change this report to `COMPLETED` only when:

1. both Python validators pass;
2. diff whitespace validation passes;
3. the Chromium runtime suite passes;
4. screenshot artifacts are present;
5. any discovered defect is fixed and revalidated.
