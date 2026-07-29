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

The feedback closure is exact-head validated at `92369e59162a134ed7c64188828fa15b5711a22e` with CampaignOS CI `30414864886` and Runtime Visual Review `30414864870`.

## Human-review feedback exact-head closure

Implementation head `92369e59162a134ed7c64188828fa15b5711a22e` passed CampaignOS CI `30414864886` and Runtime Visual Review `30414864870` on draft PR `#126`. The hosted PostgreSQL/API/browser job `90459048370` proved:

- completed guided intake starts collapsed in Spanish and English and reopens only for explicit review;
- the mission hero is absent from foundation, candidate and team chapter workspaces;
- both team-operation cards remain in one visual stack, exchange front/back state with keyboard navigation and preserve accessibility isolation;
- the governed template preview exposes `Aplicar funciones nuevas · 5` before the detailed catalog, applies only missing vacant functions and persists ten total functions;
- candidate and team data persist across chapter navigation and reload;
- desktop/mobile, ES/EN, reduced motion, zero axe violations, no overflow, no unexpected hosts and no console/page errors.

Retained artifacts:

- frontend review: `8709836555`, `sha256:96f68c284755d070635dabeace377dc4025ffeb08e768e6155d2e91e83ffca4a`
- PostgreSQL recovery: `8709775631`, `sha256:fe74f4569ee69b0a38e6196cb8e0e34a590ea077a652034c1335aa5804739594`
- supply chain: `8709766285`, `sha256:16ba977998a298c6c8e7c5e7d31c45631544b9b6b1402bbaa0cada7b5a205fa4`
- visual review: `8709781483`, `sha256:754d5df46a96301c911ef951f4101f242078a5a8c7811828542a56b06a704a24`
- Gitleaks SARIF: `8709767723`, `sha256:2b264fa00cc7421b66e7d04920fc6b2de11c3ab30f3fdcf0f24786bddfa2392d`

CampaignOS CI runs `30414156474` and `30414548165` remain preserved as historical failures. Each failed only because the evolving browser harness still asserted the removed chapter hero or an always-expanded completed setup. Both failed heads are ancestors of `92369e59162a134ed7c64188828fa15b5711a22e` and are explicitly superseded by successful run `30414864886`.

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
