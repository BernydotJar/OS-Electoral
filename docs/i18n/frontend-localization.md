# CampaignOS frontend localization baseline

## Scope

`C3-FRONT-001` provides Spanish and English parity for the dynamic application shell only. It does not establish complete product localization for guided intake, Candidate Workspace, Team Builder, War Room, Training Academy, administration, or future integrations.

## Locale contract

Supported locale identifiers are:

```text
es
en
```

The root route selects a language from `Accept-Language`, defaulting to Spanish. Unsupported first path segments redirect to one of the supported locale roots.

Every localized document must have:

- the matching `html[lang]` value;
- localized title and description metadata;
- identical dictionary structure;
- an explicit language selector;
- no hidden locale fallback that mixes languages on one route.

## Dictionary ownership

`frontend/src/lib/i18n.ts` is the current shell dictionary source. Its structural parity is tested by `frontend/src/lib/i18n.test.ts`.

Dictionary keys are grouped by:

- metadata;
- common classification and authority language;
- shell context;
- fail-closed states;
- dashboard projections;
- module navigation.

User-facing strings must not be embedded in authorization logic or used as permission identifiers. Backend action/resource/purpose values remain stable application contracts and can be shown as evidence codes where translation would obscure exact authority.

## Document navigation

Next.js App Router preserves root layouts during client transitions. A language change therefore uses a dedicated locale button that calls `window.location.assign` so a new document is loaded and both `html[lang]` and metadata are recomputed.

This behavior is verified in Chromium for Spanish-to-English navigation. It is not implemented as a client-only label swap.

## Formatting baseline

The shell currently renders server-provided timestamps and evidence identifiers without localized human formatting because those values are audit evidence. Future user-facing dates, money, percentages, and numbers must use locale-aware `Intl` formatters while preserving raw evidence in accessible details or receipts.

## Accessibility and language

The browser review verifies:

- Spanish and English document language;
- localized level-one heading;
- keyboard-accessible locale controls;
- zero axe-core WCAG 2.2 A/AA violations in the tested shell;
- no horizontal overflow on desktop or mobile.

## Completion boundary

`EVAL-I18N-001` remains `PARTIAL` until every production-critical journey has:

- complete ES/EN dictionary coverage;
- locale-aware validation and formatting;
- no untranslated hard-coded UI copy;
- parity tests for error, loading, empty, and success states;
- human language review;
- accessible browser verification.
