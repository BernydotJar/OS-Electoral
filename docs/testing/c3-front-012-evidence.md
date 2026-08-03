# C3-FRONT-012 evidence

Status: `REVIEWED_LOCAL`; complete repository gate passes.

## Implemented

- sidebar sequence begins with Resumen and Preparación inicial;
- duplicated Preparación menu item removed;
- Base operativa moved into chapter 1;
- candidate progress and “Qué hacer ahora” moved to Resumen;
- candidacy chapter reduced to Perfil y riesgos plus subordinate evidence;
- “Workspace ejecutivo” replaced by plain-language labels in ES/EN.

## Focused verification

- 21 focused frontend tests: PASS;
- ESLint: PASS;
- strict TypeScript: PASS;
- dynamic Chromium review: PASS;
- desktop ES/EN: PASS;
- mobile ES: PASS;
- keyboard skip link and chapter navigation: PASS;
- reduced motion: PASS;
- horizontal overflow: NONE;
- axe WCAG 2.2 AA violations: ZERO;
- browser storage: EMPTY;
- unexpected outbound hosts: NONE;
- console/page errors: NONE.

## Complete repository gate

- `make verify`: PASS;
- Python: 821 passed, 12 controlled skips, 90.11% coverage;
- frontend: 33 files / 145 tests, lint, strict TypeScript, production build and audit PASS;
- npm audit: zero vulnerabilities;
- Terraform: validate/test plan-only PASS;
- program, release, security, eval, supply-chain and safety validators PASS.

## Boundary

No authorization, API, data, dependency, production or external political behavior changed.

## First hosted exact-head finding and repair

The first exact-head CampaignOS CI run `30685228471` preserved one browser-contract failure while the other nine jobs and Runtime Visual Review `30685228478` passed. The dynamic reviewer still searched for the retired copy `Siguiente paso` inside the candidacy chapter. That expectation contradicted the approved information architecture; the product correctly rendered `Qué hacer ahora` in Resumen only.

The repair:

- requires `Resumen de candidatura` and `Qué hacer ahora` in the Spanish overview;
- requires `Candidacy summary` and `What to do now` in the English overview;
- rejects those summary/action labels inside the candidacy chapter;
- requires `Perfil y riesgos` / `Profile and risks` as the chapter heading;
- updates the API/PostgreSQL functional journey to verify the same ownership after dossier and evidence persistence.

A clean local build and dynamic Chromium review pass after the repair. The local functional Docker harness could not start because nested Docker rejected layer ownership for `/var/empty`; it did not reach application execution. Hosted exact-head functional CI remains the independent verifier.
