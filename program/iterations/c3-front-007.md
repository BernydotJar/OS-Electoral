# C3-FRONT-007 — Guided chapter transitions and consultant-grade role dossiers

- `branch`: `agent/c3-front-007-guided-chapter-transitions`
- `base`: `agent/c3-team-003-template-application-preview@197ed14e4ebd9c98f744060e3b9bca4d9874a043`
- `status`: `TESTED_LOCAL`
- `production_status`: `BLOCKED`
- `release_decision`: `DENY_RELEASE`
- `external_effects`: `NONE`

## User problem

Human product review found three material experience gaps: campaign chapters still behaved like one long page; the cinematic hero had atmosphere but little operational motion; and role proposals behaved like text cards rather than consultant-grade operating briefs.

## Bounded objective

1. keep the locale root as a command overview rather than a container for every workspace;
2. expose one stable URL per campaign chapter with browser history and exact locale preservation;
3. render only the selected mission on chapter routes;
4. add short, directional and interruptible route transitions with a static reduced-motion equivalent;
5. make the hero communicate evidence → human decision → governed execution;
6. enrich every versioned role blueprint with decisions, deliverables, interactions and operating signals;
7. expose those profiles for proposed, preserved, applied and manually created functions;
8. preserve append-only application, exact authorization and zero external effects.

## Acceptance criteria

1. The command overview contains roadmap/context but no chapter workspace.
2. Every canonical chapter route contains exactly one mission and one current chapter.
3. Invalid slugs return `404`; locked routes fail closed to the available mission.
4. Form redirects, template preview, locale switching and browser back/forward preserve chapter context.
5. Desktop and mobile navigation have no document overflow; keyboard and visible focus remain functional.
6. Reduced motion disables transitions and pulse animation without removing the three-stage cadence.
7. Every new blueprint role has at least two decision-scope items, three deliverables, two interaction points and three operating signals in ES and EN.
8. Historical roles remain readable with empty profile defaults; the UI marks the missing dossier for human completion.
9. Manual function creation requires the same four consulting blocks and rejects empty or duplicate entries.
10. No role profile creates identity, permission, spending, publishing, contact, profiling, deployment or production authority.

## Local validation record

- Frontend: 106 tests, ESLint, strict TypeScript, production build and `npm audit` with zero vulnerabilities.
- Backend focused team suite: 64 PASS.
- Ruff, format and strict mypy: PASS across 69 source files.
- Demo browser: ES/EN/mobile, route isolation, locale preservation, keyboard, reduced motion, zero axe violations, no overflow, empty browser storage and no external hosts.
- Functional PostgreSQL/browser journey updated to prove command overview → foundation → evidence → team, browser back/forward, consultant dossiers, lean 5 → full 10 → manual 11 and persistence by chapter.
- Local functional startup is blocked before product execution by nested Docker image-layer registration: `lchown /var/empty: permission denied`. Hosted exact-head CI remains required.

## Product boundaries

This increment changes navigation, presentation and organizational role descriptions. It does not assign people, create RACI, assess capacity, complete onboarding, grant access, infer political preferences, activate media, publish content, contact citizens, spend funds, deploy infrastructure or approve production.
