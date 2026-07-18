# C2-PLAT-001 — Campaign Workspace and Governed Decision Loop Core

## Objective

Create a reusable, deterministic Campaign Operating System core that moves from evidence to a draft decision artifact while preserving tenant isolation and human authority. Issue: #40.

## Requirements traceability

| ID | Requirement | Priority | Acceptance criteria | Artifact | Validation | Status |
|---|---|---:|---|---|---|---|
| REQ-C2-001 | Versioned workspace contract | Must | Required aggregates, stable IDs, strict top-level fields and v1 rejection | `schemas/`, `core/` | TEST-011–013 | Implemented |
| REQ-C2-002 | Explicit evidence classification | Must | Every evidence record has one allowed class | core + fixtures | TEST-011 | Implemented |
| REQ-C2-003 | Tenant/campaign/workspace isolation | Must | Objects and references cannot cross scope | core | TEST-009, unknown-ref tests | Implemented |
| REQ-C2-004 | Human authority separation | Must | Cycle request cannot approve, authorize, publish, fund or activate | core | TEST-008 | Implemented |
| REQ-C2-005 | Seven fail-closed strategic gates | Must | Missing, contradicted or unsupported sources close or reject gate; eligible is not approved | core | TEST-003–007, semantic-source test | Implemented |
| REQ-C2-006 | Eight canonical stations | Must | Each workspace configures all canonical stations and allowed states | fixtures + core | TEST-001–002 | Implemented |
| REQ-C2-007 | Pure governed loop | Must | <=5 summary lines, exactly one artifact, no mutation/effects, deterministic JSON | core | TEST-014–015, determinism | Implemented |
| REQ-C2-008 | Antigua operator seed | Must | Approved baseline, limited evidence refs, tactical gates blocked | `campaigns/` | TEST-001 | Implemented |
| REQ-C2-009 | Portable synthetic tenant | Must | Same engine, distinct IDs/territory, different gate state | `fixtures/` | TEST-002 | Implemented |
| REQ-C2-010 | Reproducible safe CLI | Must | Nonzero/no success output on failure; inputs not overwritten | `scripts/campaign/` | CLI tests | Implemented |
| REQ-C2-011 | Governance reconciliation | Must | Stage, territory and 90-day objective recorded approved; segment/budget/positioning remain gated | campaign docs | consistency review | Implemented |
| REQ-C2-012 | Adversarial evals and frontend preservation | Must | TEST-001–018, path/secret scan and current validators | tests/scripts | release command | Implemented |
| REQ-C2-013 | Operational documentation | Must | Create/validate/run/extend and interpret errors | `docs/campaign-workspaces.md` | documentation review | Implemented |

## Safety and non-goals

No individual targeting, voter records, profiling, persuasion scoring, publication, citizen contact, spending, ad activation, mobilization, segment selection, production auth, billing or deployment. `ELIGIBLE_FOR_HUMAN_APPROVAL` only means prerequisites are evidenced; it never changes an approval or performs an action.

## Definition of done

All requirements map to executable checks; Antigua and Rio Claro load through one core; gate signals cite semantically bound, in-scope sources; cycles are deterministic and immutable; governance is reconciled; frontend regressions pass; no CRITICAL/HIGH finding remains; branch is published only as a draft PR requiring human merge approval.
