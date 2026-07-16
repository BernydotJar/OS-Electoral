# C1-FRONT-002 Requirements — Campaign Team Command Center

Status: APPROVED_BY_HUMAN_REQUEST  
Mode: MVP  
Issue: #26

## Objective

Evolve the merged Evidence Control Room into a read-only Campaign Team Command Center that presents the candidate as the human mandate owner, an AI Campaign Chief of Staff as coordinator, and ten governed departmental agents.

## Functional requirements

1. The primary page must present a candidate/human-owner node above the AI Chief of Staff.
2. The page must render exactly ten departments from structured JSON data.
3. Each department must expose:
   - id;
   - name;
   - mission;
   - status;
   - skills;
   - evidence inputs;
   - blockers;
   - approval owner;
   - autonomy level;
   - last reviewed date.
4. Allowed department states are `ACTIVE`, `RESEARCH_ONLY`, `SETUP_REQUIRED`, `LOCKED`, and `BLOCKED`.
5. A keyboard-accessible detail drawer must open from each department card and close with a close button, Escape, or backdrop action; focus must return to the invoking card.
6. The Evidence Control Room must remain reachable as an internal module on the same static site.
7. The UI must expose closed political gates and the no-outbound-execution boundary.
8. The team canvas must have a semantic grid/list representation and must not be the only navigation mechanism.
9. The design should use an obsidian-slate command-center direction and may use circular view transitions as progressive enhancement.
10. The application must remain static and dependency-free.

## Data requirements

- `web/data/team.json` is an operational product snapshot, not electoral evidence.
- It must not contain voter-level records, support scores, segment rankings, or sensitive traits.
- Department states must derive from the current repository mandate and visible gates.
- Unknown configuration must use `SETUP_REQUIRED` or `BLOCKED`, not invented completion percentages.
- Existing `web/data/status.json` evidence values and classifications must remain unchanged.

## Accessibility requirements

- semantic headings, landmarks, buttons, dialog semantics, and visible focus;
- complete keyboard operation;
- Escape closes the drawer;
- focus returns to the trigger;
- content remains understandable without color;
- responsive behavior at mobile widths;
- `prefers-reduced-motion` disables nonessential motion;
- interactive canvas has list/grid parity.

## Safety requirements

The frontend must not enable or imply:

- segment selection;
- territorial ranking;
- voter targeting or persuasion scoring;
- sensitive-trait profiling;
- paid-media activation;
- mobilization;
- automatic publishing;
- public promises or attacks;
- disinformation;
- citizen surveillance;
- budget spending;
- legal conclusions without human counsel.

## Non-functional requirements

- no external scripts, analytics, cookies, fonts, trackers, or runtime secrets;
- no personal absolute paths;
- no dependency on `~/.gemini` at runtime;
- HTML/CSS/JS must work under a basic local HTTP server;
- existing Evidence Control Room validator must continue to pass;
- a new fail-closed validator must enforce schema, department count, allowed states, safety boundaries, and required UI hooks.

## Acceptance criteria

- candidate appears as human authority above AI;
- exactly ten department cards render;
- all required metadata is visible in cards or drawer;
- drawer is accessible and focus-safe;
- Evidence Control Room remains available;
- closed gates are visible;
- reduced-motion fallback exists;
- both validators pass;
- desktop and mobile review evidence is documented;
- no merge or deployment occurs in this feature session.
