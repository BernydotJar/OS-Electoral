# C3-FRONT-011 evidence — clear candidate guidance and governed campaign entry

## Scope

This bounded SHIP increment simplifies the internal candidate workspace, explains position and next work on all five campaign chapters, exposes governed creation of an internal candidacy draft, and subordinates team governance metadata without removing audit evidence.

It does not deploy production infrastructure, publish content, contact citizens, profile voters, target individuals, spend funds, mobilize people or create any external political effect.

## Source-based product evaluation

The product evaluation in `docs/testing/c3-front-011-campol-consultant-evaluation.md` is based on the user-provided Spanish Campol podcast auto-transcript. It preserves the source's practical sequence—research, strategy, organization, communication and measurement—while explicitly rejecting the transcript's person-level voter-database and persuasion-segmentation practices.

Pre-repair verdict:

```text
PARTIALLY_FUNCTIONAL_FOR_EXPERT_OPERATOR
```

The repair addresses the identified usability gaps without introducing any voter profile, persuasion score, individualized targeting or contact execution.

## Implemented behavior

- `Perfil y riesgos` is the only primary candidate view.
- The candidate profile is visible first; `Siguiente paso` follows as an inline action brief.
- `Fuentes y evidencia` remains available in a keyboard-operable disclosure and retains the existing authorized add-source flow.
- Every chapter renders the same orientation pattern: current chapter, status, purpose and next human action.
- `Nueva candidatura` appears only under the exact tenant-level `campaign_collection/create/Create tenant campaign` grant.
- The form carries one UUID-backed idempotency key; retries reuse the same operation and deterministic 12-hex slug suffix.
- Creation calls the existing protected backend endpoint and accepts only a version-one `DRAFT` response for the expected tenant.
- Creation never changes the active campaign cookie and never implies access to the new draft.
- An authorized tenant with no visible campaigns can create its first internal draft; a tenant without the exact grant remains fail closed.
- Training, access recommendations, read receipt and update timestamp remain auditable behind one compact disclosure.
- Spanish and English copy describes user decisions instead of internal architecture.

## Critic / red-team findings and repairs

1. **Duplicate draft risk — resolved.** The first proxy pass generated a new idempotency key for every POST, so a browser retry could create a second draft. The key is now generated in the rendered form, validated by the proxy and reused by the backend call; the slug is bound to the same key.
2. **Empty-tenant dead end — resolved.** A user with exact create authority but no visible campaigns originally received only the empty state. The first-draft form is now reachable while unauthorized empty tenants remain closed.
3. **Candidate hierarchy inversion — resolved.** The first single-view pass placed the action brief before the profile. The profile and risks now appear first, followed by the next-step brief and subordinate evidence.
4. **Campaign-context layout ambiguity — resolved.** Selector, empty state and draft creation now live in one action column; each label is grouped with its field and responsive behavior is explicit.
5. **Stale browser contracts — resolved.** Chromium reviewers no longer look for retired candidate tabs and instead enforce the visible profile, chapter orientation and keyboard evidence disclosure.
6. **Slug collision margin — strengthened.** The deterministic suffix was expanded from 8 to 12 hexadecimal characters while remaining below the backend's 100-character slug limit.
7. **Nested Docker limitation — documented.** The local PostgreSQL/API/browser runner stopped before product startup while Docker registered the PostgreSQL 18 layer: `lchown /var/empty: permission denied`. No product assertion executed in that failed run. Exact-head hosted CI remains mandatory.
8. **Hosted creation coverage gap — resolved.** The original functional fixture intentionally had no tenant campaign-create grant, so the new entry point would not run in PostgreSQL/browser CI. An opt-in E2E-only exact grant now exercises DRAFT creation, persistence evidence, unchanged current context and absence of implicit read access while the default 11-grant operator remains unchanged.
9. **Stale English functional selector — resolved.** The API-backed English journey still expected the retired candidate tab. It now validates the visible `Profile and risks`, `Next step`, zero tabs and the subordinate evidence disclosure.

Implementation commit: `8b835e1a64095e92136d5375026075581c8fe02a`.

## Local verification

```text
make verify: PASS
Python: 793 passed, 12 controlled skips
coverage: 90.22% (90% floor)
Ruff lint/format: PASS
strict mypy: PASS, 80 source files
Terraform: PASS, plan/test only; no apply
frontend: 33 files / 144 tests PASS
ESLint: PASS
TypeScript: PASS
Next.js production build: PASS
npm audit: 0 vulnerabilities
program/security/release/eval/safety validators: PASS
production: BLOCKED
release: DENY_RELEASE
```

Dynamic Chromium review:

```text
desktop Spanish: PASS
desktop English: PASS
mobile Spanish (390px): PASS
chapter route isolation and locale preservation: PASS
keyboard navigation and disclosure operation: PASS
reduced motion: PASS
axe WCAG 2.2 AA: zero violations
horizontal overflow: none
browser storage: empty
unexpected outbound hosts: none
console errors: none
page errors: none
```

The generated local review receipt had SHA-256:

```text
a9a8f18aa939103a3666cceba3916e5138aae84a13ad25d58c2af150649c5f84
```

Screenshots, server logs and the ephemeral local receipt are intentionally not committed.

## Hosted critic repair

- CampaignOS CI run `30678840392` passed every job except the API-backed frontend journey.
- PostgreSQL 18, migrations, the 12-grant E2E seed, static browser review, quality, CodeQL, recovery, supply chain, Terraform and stack E2E all completed successfully.
- The journey then timed out on a second Spanish selector for the retired `Fuentes y evidencia` tab after returning to the candidate chapter.
- Repair commit `43d5c3aad7f5b9214a547dcb416f5d8a8efeee6f` opens the current evidence disclosure and adds two static regression tests that reject every retired candidate-tab selector in both browser scripts.
- Local exact-tree verification after repair: `793 passed`, `12 skipped`, `90.22%` coverage; frontend remains `144 passed`.
- The node remains `REVIEWED` until the repaired exact head passes hosted CI.

## Remaining exact-head gate

Hosted CI must execute the PostgreSQL 18/API/browser journey on the final PR head because the local nested Docker daemon failed before application startup. Until that evidence exists, the increment is locally reviewed but not `CI_GREEN`.

Production remains `BLOCKED`, release remains `DENY_RELEASE`, and external effects remain `NONE`.
