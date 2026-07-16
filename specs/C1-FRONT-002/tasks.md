# C1-FRONT-002 Tasks — Campaign Team Command Center

Status: PARTIAL_WITH_DOCUMENTED_ENVIRONMENT_BLOCKER

| Task | State | Verification |
|---|---|---|
| Register feature and file boundaries | PASS | `feature_list.json` reviewed |
| Create requirements, design, tasks, and prompt | PASS | artifacts published |
| Define structured team snapshot | PASS | `web/data/team.json` published |
| Add candidate and Chief of Staff hierarchy | PASS | HTML structure reviewed |
| Render ten department cards | PASS | data and rendering code reviewed |
| Implement accessible detail drawer | PASS | dialog, Escape, trap and focus-return hooks reviewed |
| Preserve Evidence Control Room as internal module | PASS | Team/Evidence modules present |
| Apply obsidian-slate responsive design | PASS | CSS breakpoints and local tokens present |
| Add reduced-motion and transition fallback | PASS | CSS media query and View Transition feature detection present |
| Extend fail-closed validation | PASS | new validator published |
| Update frontend documentation | PASS | README updated |
| Execute validators in repository checkout | BLOCKED | no local checkout and GitHub DNS unavailable in runtime |
| Produce desktop/mobile screenshots | BLOCKED | app cannot be served without checkout/source download |
| Produce implementation report | PASS | report published |
| Open/update draft PR and issue | PASS | Issue #26 and draft PR created |

## Blocker

The active runtime has Python, Node, Chromium and Python Playwright, but does not contain an `OS-Electoral` checkout, does not contain `gh`, and cannot resolve `raw.githubusercontent.com`. Therefore it cannot execute the committed validators or serve the committed branch for screenshots.

## Resume condition

Run from a synchronized checkout of the branch:

```bash
python3 scripts/frontend/validate_evidence_control_room.py
python3 scripts/frontend/validate_campaign_team_command_center.py
python3 -m http.server 4173 --directory web
git diff --check
```

Then review desktop `1440x1000`, mobile `390x844`, keyboard navigation, Escape/focus return, Team/Evidence switching and reduced-motion behavior.

## Stop conditions

- Do not merge.
- Do not deploy.
- Do not modify electoral evidence artifacts.
- Do not activate targeting, messaging, mobilization, paid media, spending, or real agent execution.
