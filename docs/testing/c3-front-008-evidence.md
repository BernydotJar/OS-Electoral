# C3-FRONT-008 evidence — organic role-aware campaign flow

## Scope

- guided team presets and removable chips while preserving the existing intake contract;
- candidate action brief separated from profile/risk and source/evidence work;
- physically interleaved operations-board and follow-up-creation cards with one inert layer behind;
- guided starting route first in authorized navigation;
- mission hero restricted to the command overview; chapter workspaces contain only their own task surface;
- completed guided intake collapsed into a revisable one-time setup;
- template confirmation elevated beside the preview summary so missing vacancies can be applied without searching below the catalog;
- explicit command-view boundary and deferred server-enforced personal views.

## Local evidence

```text
Python: 732 tests PASS / 10 controlled skips / 90.38% coverage
frontend: 27 test files / 119 tests PASS
ESLint: PASS
strict TypeScript: PASS
Next.js 16 production build: PASS
npm audit: 0 vulnerabilities
demo browser ES/EN/mobile/keyboard/reduced motion: PASS
candidate tabs and route isolation: PASS
overview mission hero height: PASS_COMPACT
chapter mission hero leakage: NONE
completed guided setup default: COLLAPSED_REVISABLE
team operation card geometry: PASS_INTERLEAVED_FRONT_BACK
template apply action: PASS_VISIBLE_BEFORE_CATALOG
axe WCAG 2.2 AA: 0 violations
horizontal overflow: NONE
unexpected external hosts: NONE
console/page errors: NONE
```

The API/PostgreSQL/browser journey was updated for chips, candidate views, one-time setup collapse, interleaved operation-card geometry, keyboard front/back exchange and visible template application. The local nested Docker daemon stopped before CampaignOS startup while registering an upstream Alpine layer (`lchown /var/empty: permission denied`). Hosted exact-head CI remains the authoritative persistence proof.

## Human-review feedback closure — local checkpoint

The latest product review identified three interaction gaps on top of the previously green PR head:

1. `MISIÓN ACTIVA` still appeared inside candidate and team chapters; it is now restricted to the command overview.
2. Guided intake looked permanent after completion; it now remains large during setup and collapses into a native, keyboard-operable review disclosure after reaching `READY_FOR_RESEARCH`.
3. Team operations behaved like a tab toggle; both cards now occupy the same visual stack, the inactive card remains visible but inert behind the active card, and keyboard navigation exchanges their depth.
4. Template application was technically present but buried after the detailed role catalog; the version/digest-bound confirmation now appears immediately beside the preview summary and states the number of missing vacancies to apply.

Local Chromium proved the overview/chapter hero boundary, desktop team-card geometry, keyboard depth exchange, ES/EN, mobile, reduced motion, zero axe violations and no horizontal overflow. The full repository gate passed with 732 Python tests, 10 controlled skips, 90.38% coverage and 119 frontend tests. The nested local Docker daemon still stops before CampaignOS startup at `lchown /var/empty`; hosted exact-head CI remains required for the PostgreSQL mutation and persistence proof.

The last remotely validated PR head before this feedback closure is `dfea5f21952c9b91f34879fdc4b6051e58cedc09` (`CampaignOS CI 30400505954`, `Runtime Visual Review 30400506057`). The feedback closure is `TESTED_LOCAL` until a new exact-head run succeeds.

## Safety and authority

- presets and chips do not create identity, membership, permission or authority;
- candidate insights derive only from persisted workspace state and create no strategy or public-use approval;
- command view uses existing exact grants;
- personal work visibility is not claimed and remains blocked until server-side principal/function projection exists;
- no contact, publishing, spend, mobilization, deployment or external political effect occurs.

## Exact-head hosted evidence

Implementation head `1db72a82a147d8ca9402c370814331879c1ac3a5` passed CampaignOS CI `30400102360` and Runtime Visual Review `30400102373` on draft PR `#126`.

The hosted PostgreSQL/API/browser job `90412547652` proved current-team preset and chip persistence, candidate action/profile/evidence views, keyboard tab navigation, the board/create operating deck, role-work persistence, Spanish/English, desktop/mobile, reduced motion and accessibility.

Retained artifacts:

- frontend review: `8704422692`, `sha256:4dde2a099e466975f6a52dfe68b3211e9dd414ae122646f4f974a674ece5832e`
- PostgreSQL recovery: `8704363674`, `sha256:1b747ce675a6abb76f6871fdc4be051f5b04e83ff0e80c29f7aaa74ff1a4f15d`
- supply chain: `8704350702`, `sha256:0071bf94b9c976ba93f878c2ba0f333b4f9ad815edb0ddfa577f3d793d5917f8`
- visual review: `8704377666`, `sha256:c51e9a700c31161971397faea259c7951f3139c5a11d35a3266026a5e8695a1e`
- Gitleaks SARIF: `8704353530`, `sha256:0e7156ab221627ea216416bc769757a8a9bbb045e03f652a0d16c5520ad30f6b`

Production remains `BLOCKED`, release remains `DENY_RELEASE`, and external effects remain `NONE`.
