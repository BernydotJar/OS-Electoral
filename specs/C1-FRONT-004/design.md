# C1-FRONT-004 — Premium Slate Design

## Architecture

The increment is additive and framework-free:

- `web/premium-slate.css` — visual tokens, shell hierarchy, glow surfaces and View Transition styling.
- `web/premium-slate.js` — ambient canvas, pointer-aware glow coordinates and module metadata synchronization.
- `web/index.html` — loads the two assets and declares one decorative canvas plus one concise shell metadata strip.
- `scripts/frontend/validate_premium_slate.py` — static contract validator.

The existing application, data snapshots and module rendering remain the source of truth.

## Layering model

1. `body::before` renders the 20px dotted pixel grid.
2. `#ambientCanvas` renders a sparse node network behind all application content.
3. Existing topbar, navigation, modules and drawers remain semantic and interactive.
4. Glow surfaces use a pseudo-element driven by `--glow-x` and `--glow-y`; pseudo-elements have `pointer-events: none`.
5. Drawers stay above all decorative layers.

## Token model

The premium layer overrides existing tokens rather than duplicating component rules:

- canvas: `#070708`, `#09090b`;
- surfaces: progressively lighter slate-black layers;
- border: white at 8–14% opacity;
- text: cool white, muted slate and subtle slate;
- accent: HSL variables exposed as hue/saturation/lightness;
- risk, warning and approval remain semantically distinct;
- focus ring remains stronger than hover effects.

## Ambient canvas

The canvas is decorative only:

- fixed to the viewport;
- `aria-hidden="true"`;
- CSS `pointer-events: none`;
- DPR-aware backing store;
- deterministic seeded nodes for stable visual review;
- low-density edges based on distance;
- no animation under reduced motion;
- animation paused when `document.hidden`;
- resize throttled through `requestAnimationFrame`.

## Glow primitive

Eligible surfaces receive `.premium-glow` at runtime. Pointer movement updates local coordinates in CSS pixels. The CSS pseudo-element renders a restrained radial light.

Disabled when:

- `prefers-reduced-motion: reduce`;
- `pointer: coarse`;
- the element is not connected or visible.

Keyboard focus continues to use the existing focus ring and does not depend on pointer position.

## Module transition

The existing `document.startViewTransition()` lifecycle remains authoritative. The premium CSS styles `::view-transition-old(root)` and `::view-transition-new(root)` with a circular clip-path originating from `--transition-x` and `--transition-y`.

The application already places focus on the destination heading only after `transition.finished`; the visual layer must not override this lifecycle.

## Module hierarchy

- `body[data-active-module="war-room"]`: stronger accent and operational depth.
- `body[data-active-module="team"]`: authority/orchestration emphasis.
- `body[data-active-module="evidence"]`: cooler provenance emphasis.

The JavaScript mirrors the active module into `body.dataset.activeModule` and updates the metadata strip with labels derived only from existing UI state.

## Accessibility

- canvas and all pseudo-elements are non-interactive;
- no animation is required to understand state;
- reduced-motion disables canvas motion, glow movement and View Transition animation;
- contrast remains at least as strong as the existing design;
- no new controls are introduced;
- semantic headings, buttons, list roles and dialogs are unchanged.

## Failure containment

If `premium-slate.js` fails, the existing frontend remains functional because all behavior is additive. The static validator verifies asset links, canvas semantics, reduced-motion contracts and absence of forbidden political capabilities.
