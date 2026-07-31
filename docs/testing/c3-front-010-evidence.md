# C3-FRONT-010 evidence — compact command chrome and liquid-glass operations

## Human QA defects

The authenticated Team chapter exposed global product copy and raw organization/campaign/session context before the requested workspace. Operational cards were readable but visually flat, badge-heavy and internally nested. An authorization denial appeared as a broad error even though the rest of the workspace remained valid.

## Implemented behavior

### Compact chapter chrome

- Internal chapter routes render a compact sticky command bar rather than the full product manifesto.
- The bar names the active module and provides one concise phase description.
- The chapter bar is browser-gated to a maximum rendered height of 80px on desktop.
- Tenant UUID, campaign name, principal and session status live in a collapsed native disclosure.
- The overview retains the fuller product header and context because it is the command-center entry surface.

### Calm authorization feedback

- `authorization_denied` is rendered as a compact, non-destructive notice.
- The notice explicitly states that the rest of the workspace remains available.
- A clean-route link removes the query notice while preserving the current chapter anchor.
- No permission check, write boundary or fail-closed behavior was weakened.

### Operational card hierarchy

- Work status, type, priority and health have separate semantic hooks and visual treatments.
- Priority controls the bounded card accent; status uses an independent state dot.
- Accountable function, target date and cadence use a compact facts grid.
- The next action is a slim executive band with a localized label.
- Evidence, RACI and check-in controls remain available through native disclosures.
- Liquid-glass styling uses bounded blur, saturation, thin borders and low-intensity glow; no animated or decorative media was added.

## Critic findings

- Default success notices were initially at risk of inheriting the warning palette. Fixed by scoping amber semantics to `authorization_denied` only.
- Status and priority initially shared one color source. Fixed by introducing independent state and priority variables.
- A mobile negative offset could have pushed the session disclosure toward viewport overflow. Removed.

## Local verification

```text
implementation commit: b14f0ae
base: main@d2ad6d5eaeb46208fc00ea5fb9eb0be81eae26ee
git diff --check: PASS
make verify: PASS
Python: 753 passed / 11 skipped / 90.39% coverage
frontend: 28 files / 121 tests PASS
TypeScript: PASS
ESLint: PASS
Next.js production build: PASS
npm audit: 0 vulnerabilities
Terraform: PASS_PLAN_ONLY_NO_APPLY
program truth: PASS / production BLOCKED
release gate: DENY_RELEASE
```

Dynamic browser review:

```text
desktop ES/EN: PASS
mobile ES: PASS
compact chapter chrome <= 80px: PASS
chapter context strip absent: PASS
session context collapsed by default: PASS
keyboard disclosure: PASS
reduced motion: PASS_STATIC_EQUIVALENT
axe WCAG 2.2 AA: zero violations
horizontal overflow: NONE
browser storage: EMPTY
unexpected outbound hosts: NONE
console/page errors: NONE
```

The nested-Docker functional command stopped before CampaignOS startup while Docker registered an upstream image layer:

```text
failed to register layer: lchown /var/empty: permission denied
```

This is an isolated workstation runtime limitation. The exact-head hosted workflow must pass the real PostgreSQL/API/browser journey before merge.

## Remaining gates

- exact-head CampaignOS CI;
- exact-head runtime visual review;
- hosted PostgreSQL 18 functional browser journey;
- review-thread closure;
- merge and post-merge CI;
- separate production and external-effect approvals.

Production remains `BLOCKED`, release remains `DENY_RELEASE`, and external effects remain `NONE`.

## Exact-head, merge and demo evidence

```text
pull request: 143
final implementation head: f4d5ab4d9c22917bf5bff37b5e368afda18b3406
exact-head CampaignOS CI: 30656019602 / SUCCESS
exact-head runtime visual review: 30656019685 / SUCCESS
merged main: 998072c64c976d8b2e559862df5dab0e84104b98
post-merge CampaignOS CI: 30656253464 / SUCCESS
public demo classification: TEMPORARY_AUTHENTICATED_NON_PRODUCTION
public demo readiness: PASS
public desktop compact chrome: 64px / PASS
public mobile viewport containment: PASS at 390px
```

The final critic pass also repaired exact-anchor preservation when dismissing notices and mobile session-menu containment. The authenticated demo serves the merged UI SHA; its backend runtime is byte-equivalent because no backend file changed between the prior and current UI builds.

## Authorization chronology correction

The initiating user instruction explicitly requested this bounded frontend repair before any implementation work. The chat runtime does not expose an immutable timestamp for that message, so the ledger uses the first durable authorized implementation commit (`2026-07-31T18:26:44Z`) as the receipt capture time rather than inventing a message timestamp. PR #143 was created at `18:30:14Z` and merged at the immutable Git committer time `18:42:51Z`.
