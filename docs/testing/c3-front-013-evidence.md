# C3-FRONT-013 evidence

Status: `REVIEWED_LOCAL`; implementation commit `7c3994ee36d3d5b16cb1df66c31139850483ae95`; exact-head hosted review pending.

## Implemented

- candidate chapter now contains a progressive **Completar expediente** workflow between profile and supporting sources;
- all eight existing candidate evidence sections are editable through same-origin, exact-authorized controls;
- verified claims require linked independent evidence and stable record IDs are preserved on edits;
- contradictions and reputation can be explicitly reviewed as empty rather than inferred absent;
- current-version section approvals require the existing exact `approve` grant and a human reason;
- saves preserve unrelated candidate sections and intentionally invalidate stale version-bound approvals;
- read-only mode renders no candidate mutation endpoints or forms and exposes no user-facing review-mode label;
- ES/EN, mobile, keyboard, reduced motion and chapter-return anchors remain intact.

## Producer and focused verification

- candidate capability/seed, parser/client, form, component, chapter and route tests: PASS;
- stale version, missing exact grant, non-required approval and subanchor routing adversarial cases: PASS;
- ESLint: PASS;
- strict TypeScript: PASS;
- optimized Next.js build: PASS;
- npm audit: 0 vulnerabilities.

## Critic / Red Team findings

1. Candidate mutation redirects initially used subanchors not mapped to the `evidence` chapter. Fix: map all candidate edit/approval subanchors to the candidacy chapter and test them.
2. The functional verifier initially required literal `9/9` copy that the candidate chapter does not render. PostgreSQL already contained all eight current-version approvals and the projection was `INTERNALLY_APPROVED`. Fix: verify the nine rendered governed checks semantically instead of asserting nonexistent copy.
3. Graph Harness validator tests were hard-coded to the superseded Firmes-only checkpoint. Fix: validate the current active increment and build explicit pending-Firmes fixtures for the fail-closed negative tests.
4. A local port test leaked a socket when bind failed under Python 3.14 `-W error`. Fix: close the reservation on bind failure.

No finding required weakening authorization, evidence, RLS, release, production or safety gates.

## Functional PostgreSQL/API/browser verification

The repository host harness ran against an isolated PostgreSQL database and optimized frontend build. Result: PASS.

- candidate dossier completion: `PASS_9_OF_9_CURRENT_VERSION_APPROVED`;
- all eight section approvals persisted at the current candidate version;
- persistence after reload: PASS;
- exact authorization controls: PASS;
- desktop Spanish / English: PASS;
- mobile Spanish: PASS;
- WCAG 2.2 AA axe violations: ZERO;
- horizontal overflow: NONE;
- browser storage: EMPTY;
- unexpected outbound hosts: NONE;
- console/page errors: NONE;
- external effects: NONE.

The marked PostgreSQL suite was also run with an ephemeral local cluster administrator, because the suite creates constrained roles to prove RLS. Result: **12 passed / 5 deselected** across migration, campaign creation, identity, intake, candidate approvals, team, operations, strategy, agents, append-only security, rate limiting and training.

## Complete local repository verification

- backend: 865 passed, 13 controlled PostgreSQL skips in the non-PostgreSQL unit target;
- coverage: 90.03% (required floor 90%);
- frontend: 39 files / 174 tests passed;
- dynamic read-only Chromium review: PASS ES/EN/mobile/keyboard/reduced-motion/WCAG;
- supply-chain policy: PASS;
- security/privacy policy: PASS;
- program truth: PASS with production `BLOCKED`;
- release readiness validator: PASS with decision `DENY_RELEASE`;
- eval catalog and C2 safety scanner: PASS;
- Terraform 1.15.8: SHA-256 verified download, fmt/validate/test for bootstrap and platform PASS; policy remains `PLAN_ONLY_NO_APPLY`.

Docker Compose v2 is not installed in this sandbox, so the aggregate `make verify` entrypoint cannot execute its initial Compose config command here. Equal-or-broader individual repository gates plus the repository host PostgreSQL/API/browser harness passed. Hosted exact-head CI remains the independent publication verifier.

## Boundary and release gate

This increment creates no Firmes integration, production deployment, cloud resource, spend, publication, citizen contact, targeting, persuasion or mobilization. `C3-FIRMES-001` remains human-approval-pending. Production remains `BLOCKED`; release remains `DENY_RELEASE`.

## Hosted exact-head verification

- exact head: `127d90e05c7c2b83a34d1dc6cb839bcc3a5600ed`;
- CampaignOS CI run `31658468438` / #255: `SUCCESS`;
- Runtime Visual Review run `31658468359` / #231: `SUCCESS`;
- API-backed functional onboarding on the exact head: `SUCCESS`;
- exact-head release status: merge-ready for the reviewed increment; production remains `BLOCKED` and global release remains `DENY_RELEASE`.
