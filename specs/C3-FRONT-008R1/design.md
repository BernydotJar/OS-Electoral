# C3-FRONT-008R1 Design

## Repair boundary

This increment repairs presentation hierarchy, chapter orientation and local diagnostics. It does not redesign the CampaignOS domain model, Graph Harness runtime, authorization contracts, persistence, team workflow or candidate evidence semantics.

## Command overview

Replace the former two-layer overview—cinematic active-mission hero followed by the campaign path—with one command surface:

- a single large campaign-path heading;
- explicit progress and current stage;
- a current-decision card containing status, expected outcome and one primary action;
- compact stage shortcuts;
- a closed-by-default disclosure for the complete five-stage path.

The visual direction is institutional, restrained and operational: strong typography, controlled density, thin borders, low-noise depth and no decorative stock or generated media. The product should feel credible to municipal and national leadership without simulating authority or hiding incomplete stages.

## Chapter routes

A chapter route begins with a compact command bar, not a hero or full horizontal journey. The bar contains:

- back to overview;
- current chapter number, title and status;
- previous/next controls;
- a closed-by-default full campaign map.

The requested workspace follows immediately. The full map remains available to keyboard and screen-reader users but no longer pushes the primary task below the fold.

## Local readiness

The functional launcher already chooses unique ephemeral loopback ports. The repair makes the result unambiguous by printing:

- Spanish and English frontend URLs;
- same-origin browser readiness URL;
- backend API base URL;
- backend readiness URL;
- Mailpit UI URL.

The frontend implements `GET /api/v1/ready` as a no-store same-origin proxy. It resolves the server-only API base URL, applies the configured timeout, parses a JSON object, returns the upstream status and fails closed with stable sanitized codes. It never exposes tokens, tenant identifiers, raw connection errors or database details.

## Files allowed to change

- `frontend/src/components/campaign-launch-roadmap.tsx`
- `frontend/src/components/campaign-chapter-navigation.tsx`
- `frontend/src/components/shell.tsx`
- `frontend/src/app/globals.css`
- `frontend/src/lib/i18n.ts`
- `frontend/src/app/api/v1/ready/**`
- focused frontend tests
- `scripts/dev/functional_frontend.sh`
- frontend browser-review scripts
- documentation and Graph Harness evidence for this repair

## Files and effects excluded

- Graph Harness framework source;
- backend domain, authorization, rate-limit or database behavior;
- campaign publishing, contact, persuasion, targeting, spending or mobilization;
- live social, identity, AI, media or research providers;
- Terraform apply/state and production configuration;
- dependency manifests and lockfiles.

## Verification

1. lint, strict TypeScript, all frontend tests, production build and dependency audit;
2. focused readiness proxy failure-path tests;
3. dynamic demo browser review;
4. real PostgreSQL/API/browser functional journey;
5. ES/EN, mobile, keyboard, reduced-motion, overflow and axe checks;
6. program, security, release and supply-chain gates;
7. exact-head hosted CI and runtime visual review.

## Localized repair rule

A failure is repaired only in the affected component, route, launcher, evaluator or assertion. Timing, accessibility, authorization and safety gates are not weakened to make the interface pass.
