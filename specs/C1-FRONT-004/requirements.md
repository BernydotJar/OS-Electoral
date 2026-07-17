# C1-FRONT-004 — Premium Slate Design System Requirements

## Objective

Transform the existing static CampaignOS frontend into a premium civic-intelligence interface while preserving all current evidence, governance, accessibility and human-approval boundaries.

## Product constraints

- Static `HTML + CSS + JavaScript`; no framework or build step.
- No changes to evidence values, classifications, political gates or campaign decisions.
- No targeting, profiling, persuasion scoring, mobilization, publishing, spending or citizen contact.
- Decorative effects must never intercept pointer or keyboard input.
- Existing semantic HTML, dialog focus management, keyboard behavior and responsive behavior remain intact.

## Functional requirements

### R1 — Shared premium slate tokens

The frontend must define a coherent token layer for:

- obsidian canvas and layered slate surfaces;
- low-opacity borders and elevation;
- foreground, muted and subtle text;
- accent, approval, warning and risk states;
- spacing, radius, focus and motion.

### R2 — Ambient civic-intelligence canvas

A restrained decorative canvas must render a low-density node network behind the application shell.

- `aria-hidden="true"` and non-interactive;
- respects `prefers-reduced-motion`;
- pauses when the document is hidden;
- scales for device pixel ratio without causing layout overflow.

### R3 — Pointer-aware glow cards

Operational cards and panels must expose subtle cursor-aware light using CSS custom properties.

- no content obstruction;
- no pointer interception;
- disabled for reduced motion and coarse pointers;
- keyboard focus remains visually stronger than hover glow.

### R4 — Circular module reveal

Module changes must use the View Transitions API when available and produce a circular reveal from the interaction coordinates.

- module heading receives focus only after the transition completes;
- strict fallback for reduced motion or unsupported browsers;
- no stale snapshots in runtime screenshots.

### R5 — Hierarchy by module

- Daily War Room has the strongest operational emphasis.
- Team Command Center communicates governed orchestration and authority.
- Evidence Control Room communicates provenance and reconciliation.
- Closed political gates remain visible without dominating every screen.

### R6 — Coordinate and state metadata

The shell must expose concise, non-sensitive operating metadata such as mode, snapshot and module coordinate tags without inventing political information.

### R7 — Responsive and accessible parity

- no page-level horizontal overflow at 390px or 1440px;
- usable at 200% page scale;
- complete reduced-motion fallback;
- decorative layers do not appear in the accessibility tree;
- focus traps, Escape close and focus return remain correct.

## Acceptance gate

The increment is acceptable only when:

1. all existing static validators pass;
2. `git diff --check origin/main...HEAD` passes;
3. Playwright desktop, mobile and reduced-motion checks pass;
4. `runtime-review.json` reports `overall: PASS`;
5. all generated screenshots are manually inspected;
6. PR remains draft until human merge instruction.
