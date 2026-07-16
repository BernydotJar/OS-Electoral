# C1-FRONT-002 Design — Campaign Team Command Center

Status: APPROVED_BY_HUMAN_REQUEST  
Mode: MVP

## Architecture

The feature extends the existing dependency-free static application.

```text
web/index.html
  shell, human-authority hierarchy, module navigation, team canvas, drawer, existing evidence module

web/styles.css
  obsidian-slate tokens, responsive layout, focus, drawer, progressive transitions

web/app.js
  safe rendering, module switching, team loading, drawer behavior, focus management

web/data/team.json
  operational team snapshot

web/data/status.json
  existing evidence snapshot; unchanged

scripts/frontend/validate_campaign_team_command_center.py
  fail-closed product and safety validation
```

## Information architecture

```text
Campaign Team Command Center
├── Candidate / Human Mandate Owner
├── AI Campaign Chief of Staff
├── module navigation
│   ├── Team Command Center
│   └── Evidence Control Room
├── Team Canvas
│   └── 10 department cards
├── Political Gates
└── Department Detail Drawer
```

## Human authority model

The candidate node is the highest visual and semantic authority. The Chief of Staff is labeled as an AI coordinator with bounded autonomy. Department cards are subordinate operational roles.

## Team data contract

```json
{
  "version": "c1-front-002.0",
  "snapshotDate": "YYYY-MM-DD",
  "candidate": {
    "title": "Candidate / Human Mandate Owner",
    "authority": "FINAL_HUMAN_DECISION_OWNER"
  },
  "chiefOfStaff": {
    "title": "AI Campaign Chief of Staff",
    "authority": "COORDINATION_ONLY"
  },
  "departments": [
    {
      "id": "research-evidence",
      "name": "Research and Evidence",
      "mission": "...",
      "status": "ACTIVE",
      "skills": ["..."],
      "evidenceInputs": ["..."],
      "blockers": ["..."],
      "approvalOwner": "Human Campaign Owner",
      "autonomy": "READ_ANALYZE_DRAFT",
      "lastReviewed": "YYYY-MM-DD"
    }
  ],
  "closedGates": ["..."],
  "safetyStatement": "..."
}
```

## Department-state mapping

- Research and Evidence: `ACTIVE`.
- Strategy and War Room: `RESEARCH_ONLY`.
- Candidate Brand and Reputation: `SETUP_REQUIRED`.
- Policy and Municipal Government: `RESEARCH_ONLY`.
- Communications and Media: `LOCKED`.
- Legal and Electoral Compliance: `ACTIVE` for research/checklists only.
- Finance and Administration: `SETUP_REQUIRED`.
- Operations and Team: `SETUP_REQUIRED`.
- Security and Information Protection: `SETUP_REQUIRED`.
- Performance and Learning: `ACTIVE` for process metrics only.

These states describe operational readiness, not political value or electoral probability.

## Interaction design

- The team module is default.
- Module buttons switch between Team and Evidence sections.
- When supported, a circular reveal transition may originate from the selected module button.
- The transition is enhancement-only and disabled under reduced motion.
- Cards are native buttons or contain native buttons.
- Opening a department stores the invoking element, populates the dialog, and focuses the close button or dialog heading.
- Closing restores focus to the invoker.

## Accessibility

- `role="dialog"`, `aria-modal="true"`, labelled title;
- body scroll lock while drawer is open;
- Escape handling;
- focus trap limited to drawer controls;
- visible focus ring;
- card status includes text, not color only;
- module views use `hidden` and `aria-current`/`aria-selected` semantics;
- reduced-motion media query and JS check.

## Security and privacy

- all dynamic strings are HTML-escaped;
- no innerHTML from untrusted external data without escaping;
- no network calls beyond local JSON assets;
- no user tracking;
- no PII fields;
- no global-skill path in shipped assets.

## Verification

```text
python3 scripts/frontend/validate_evidence_control_room.py
python3 scripts/frontend/validate_campaign_team_command_center.py
python3 -m http.server 4173 --directory web
git diff --check
```

Visual review targets:

- desktop 1440×1000;
- mobile 390×844;
- keyboard navigation;
- reduced-motion emulation;
- drawer open/close and focus return;
- Team/Evidence module switching.
