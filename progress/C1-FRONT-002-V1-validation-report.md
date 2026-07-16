# C1-FRONT-002-V1 — Runtime Validation and Visual Review

Status: `LOCAL_RUNTIME_REVIEW_IN_PROGRESS`

Base commit: `bb27a1574423cfc99e527ff366929529ee65d3bd`
Working branch: `agent/c1-front-002-v1-r1-resolve-runtime-findings`
Tracking issue: `#30`

## Objective

Complete the browser, accessibility, responsive and visual review after PR #29 merged.

## Verified local evidence

The human operator executed the merged validation branch locally and reported:

- `python3 scripts/frontend/validate_evidence_control_room.py`: PASS;
- `python3 scripts/frontend/validate_campaign_team_command_center.py`: PASS;
- `git diff --check origin/main...HEAD`: FAIL because this report contained trailing whitespace on three metadata lines;
- `runtime_visual_review.py`: BLOCKED because Python Playwright was not installed in the active environment;
- `python3 -m http.server 4173 --directory web`: port 4173 was already in use, which indicates an existing local process.

No Chromium result or screenshot is marked PASS from those logs.

## Findings resolved in R1

1. Trailing whitespace was removed from this report.
2. Runtime dependency is declared in `scripts/frontend/requirements-runtime.txt`.
3. Missing Playwright now returns concise installation instructions instead of a raw traceback.
4. The runner checks whether `CAMPAIGNOS_URL` is already healthy and reuses the existing server.
5. When the URL is an unavailable localhost endpoint, the runner starts and later stops its own static server.
6. Server startup failures point to the generated server log.

## Reproducible local execution

Activate the project environment, then run:

```bash
python3 -m pip install -r scripts/frontend/requirements-runtime.txt
python3 -m playwright install chromium

python3 scripts/frontend/validate_evidence_control_room.py
python3 scripts/frontend/validate_campaign_team_command_center.py
git diff --check origin/main...HEAD

CAMPAIGNOS_ARTIFACT_DIR=artifacts/c1-front-002-v1 \
python3 scripts/frontend/runtime_visual_review.py
```

The runner will reuse a healthy server at `http://127.0.0.1:4173`. If none exists, it will start a temporary server automatically.

## Expected artifacts

```text
artifacts/c1-front-002-v1/
├── desktop-team.png
├── desktop-drawer.png
├── desktop-evidence.png
├── mobile-team.png
├── mobile-drawer.png
├── runtime-review.json
└── server.log        # present when the runner starts the server
```

## Completion rule

Change this report to `COMPLETED` only when:

1. both Python validators pass;
2. `git diff --check origin/main...HEAD` passes;
3. the Chromium runtime suite passes;
4. screenshot artifacts are present and visually inspected;
5. any discovered runtime defect is fixed and revalidated.

## Safety

- no electoral evidence was changed;
- no campaign data snapshot was changed;
- no political gate was opened;
- no targeting, scoring, messaging, publishing, spending or mobilization capability was added;
- no deployment is authorized by this increment.
