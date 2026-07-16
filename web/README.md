# CampaignOS Frontend

Static, dependency-free frontend for the Campaign Team Command Center and the Evidence Control Room.

## Modules

### Team Command Center

The default module presents:

- candidate as `FINAL_HUMAN_DECISION_OWNER`;
- AI Campaign Chief of Staff as `COORDINATION_ONLY`;
- ten governed campaign departments;
- operational states, skills, evidence inputs, blockers, approval owners and autonomy levels;
- an accessible department-detail drawer;
- political gates and the read-only autonomy contract.

### Evidence Control Room

The internal evidence module preserves:

- verified electoral metrics;
- evidence class and source identifiers;
- workstream status;
- blockers;
- preliminary-versus-definitive reconciliation boundaries;
- explicit safety policy.

## Product boundaries

This frontend does not:

- execute agents;
- publish content or send messages;
- contact citizens;
- spend budget;
- select segments;
- rank territories;
- score persuasion or support;
- target voters;
- activate paid media;
- activate field mobilization;
- infer individual political preferences.

## Run locally

```bash
python3 -m http.server 4173 --directory web
```

Open `http://localhost:4173`.

A local HTTP server is required because the app loads local JSON snapshots with `fetch`.

## Static validation

```bash
python3 scripts/frontend/validate_evidence_control_room.py
python3 scripts/frontend/validate_campaign_team_command_center.py
git diff --check origin/main...HEAD
```

## Runtime and visual review

Inside the project virtual environment:

```bash
python3 -m pip install -r scripts/frontend/requirements-runtime.txt
python3 -m playwright install chromium

CAMPAIGNOS_ARTIFACT_DIR=artifacts/c1-front-002-v1 \
python3 scripts/frontend/runtime_visual_review.py
```

The runner first checks `CAMPAIGNOS_URL`, which defaults to `http://127.0.0.1:4173`.

- If a healthy CampaignOS server is already running, it is reused.
- If no server is running and the URL is local, the runner starts and stops a temporary static server.
- If Playwright is absent, the runner prints the exact installation commands rather than a Python traceback.

Expected outputs:

```text
artifacts/c1-front-002-v1/
├── desktop-team.png
├── desktop-drawer.png
├── desktop-evidence.png
├── mobile-team.png
├── mobile-drawer.png
├── runtime-review.json
└── server.log
```

`server.log` is generated when the runner starts the local server itself.

## Design capability

The implementation follows the documented obsidian-slate direction associated with the optional `premium-slate-ui` agent capability. The shipped application contains its own HTML, CSS and JavaScript and never reads from a developer-specific global skill directory.

Interactive motion is enhancement-only. The interface remains usable without View Transitions and when `prefers-reduced-motion` is enabled.

## Data update policy

- `web/data/team.json` is an operational product snapshot, not electoral evidence.
- `web/data/status.json` is a curated evidence snapshot, not a new source.
- Never convert preliminary or derived values to official without a recorded evidence decision.
- Never infer readiness, support or political priority from missing data.
- Run both validators after every snapshot or UI change.

## Deployment

No deployment is authorized by C1-FRONT-002. The app remains suitable for static hosting, but release, authentication, analytics, tenancy and production operations require separate approved features.
