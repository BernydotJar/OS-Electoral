# C3-FRONT-011 — Requirements

## Objective

Make the campaign workspace understandable to a candidate or campaign director without product jargon: one clear candidate profile, visible chapter orientation, a governed way to start another draft candidacy, and compact technical metadata.

## Human authorization

The user explicitly requested and authorized this bounded SHIP repair on 2026-07-31 at 15:35 -06:00. The scope is internal product UX, evaluation, tests and a temporary authenticated demo only. It does not authorize production deployment, publication, citizen contact, voter profiling, targeting, spending or mobilization.

## Required behavior

1. Candidate chapter exposes **Perfil y riesgos** as its only primary view.
2. “Qué hacer ahora” becomes an inline next-step panel inside the profile rather than a competing top-level tab.
3. “Fuentes y evidencia” becomes a profile section/disclosure while preserving the existing authorized source-add flow.
4. Every chapter route shows a visible orientation panel with chapter number, chapter name, status, purpose and next step; chapter 3 remains the reference pattern.
5. The campaign context surface offers **Nueva candidatura** only when the current identity has the exact tenant campaign-create grant.
6. Creating a candidacy calls the existing protected campaign-create API with one idempotency key and creates only an internal `DRAFT` campaign.
7. Campaign creation never grants access to the newly created campaign and never silently changes context. The user receives a clear message that access/context may require separate authorization.
8. Formation, access recommendations, read receipt and update timestamp move into a compact details disclosure.
9. Spanish and English labels use plain language; technical identifiers remain available only in disclosures.
10. Desktop/mobile, ES/EN, keyboard, reduced-motion, WCAG, authorization and functional-browser contracts remain green.

## Evaluation basis

The attached Campol podcast transcript emphasizes a practical sequence: investigate first, then plan strategy, organize the team, communicate and measure results. The product should make that order visible and show the next decision instead of presenting parallel unexplained tabs.

Safe adaptation only:

- aggregate, consented, source-backed research;
- human decisions and accountable ownership;
- measurable internal progress;
- no person-level voter databases, persuasion scores, individualized targeting or contact execution.

## Non-goals

- no new election-research or polling capability;
- no individual voter profiling or segmentation;
- no external messaging, ads, outreach or publication;
- no production deployment or infrastructure;
- no new dependency or generated media.
