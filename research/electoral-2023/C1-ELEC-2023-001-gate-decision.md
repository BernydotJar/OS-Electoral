# C1-ELEC-2023-001 and C1-TERR-DQ-001 — Gate Decision

Decision date: 2026-07-15
Decision owner: Tracking, Risks, and Learning
Source implementation: merged PR #9
Merge commit: `14e01ff7b039b06bf556f67819027af155cc02e4`

## Overall Decision

**Program:** `PASS WITH DOCUMENTED PARTIAL ELECTORAL SOURCES`

The merged implementation advances the official 2023 electoral baseline without authorizing strategy, targeting, narrative, paid media, mobilization, or territorial prioritization.

## Workstream Decisions

| Workstream | Decision | Basis |
|---|---|---|
| `C1-TERR-DQ-001` | `PASS — EV-0105_CANONICAL` | EV-0105 and EV-0106 have different package hashes but equivalent reviewed worksheet content across 40 extracted cells; EV-0106 adds no material field or row. |
| `C1-ELEC-2023-001` | `CONFIRMED_SECOND_REVIEW_FOR_VISIBLE_FIELDS` | EV-0112 has three rendered-source reviewed pages and 14 second-review-confirmed organization vote rows, but still lacks complete ballot-accounting and electoral-geography records. |

## Confirmed Electoral Facts

- Election date is not confirmed from the reviewed EV-0112 pages and remains pending a separate official source.
- Municipality: Antigua Guatemala, Sacatepequez.
- Fourteen organization vote rows are present in the reviewed page-1 table.
- Derived sum of the fourteen visible rows: `26,091`, now reconciled as a sum of second-review-confirmed visible rows.
- The winning organization visible in EV-0112 is `COMITE CIVICO FUTURO` with `6,543` votes.
- The agreement declares the validity of the municipal corporation election and identifies elected offices and names.

The value `26,091` is a derived sum of visible organization rows. It is not automatically ballots cast, total valid votes, turnout, or registered electorate.

## Remaining Electoral Blockers

The current evidence does not establish:

- registered electorate for the 2023 election;
- ballots cast;
- printed total valid votes;
- null votes;
- blank votes;
- abstention;
- official participation rate;
- polling-center inventory;
- voting-table inventory;
- official community-to-electoral-geography crosswalk.

## Workbook Decision

`EV-0105_CANONICAL` is approved for the current curated campaign-research layer.

EV-0106 remains a package-distinct alternate copy with equivalent extracted worksheet content.

This decision does not promote:

- estimated registered electorate;
- access labels;
- strategic-priority labels;
- community rankings;
- any workbook value into official TSE evidence.

## Validation Note

The merged PR body preserves an intermediate validator failure caused by resolving `${POLITICS_ROOT}` in an environment where that variable was unavailable. The final local run was reported as passing with five manifests after the authoritative local inputs were available.

Repository evidence confirms:

- EV-0106 manifest exists and records a complete extraction;
- the extractor run records one sheet, eight rows, zero PII redactions, and zero errors;
- the validator expects five evidence IDs and supports `POLITICS_ROOT` expansion;
- created curated artifacts use portable paths.

This gate accepts the final local validation report while retaining the stale PR-body log as an audit artifact rather than treating it as the final execution state.

## Political Gates

The following remain closed:

- priority segment;
- territorial ranking;
- narrative;
- paid-media audience;
- targeting;
- field mobilization;
- public promises;
- attacks.

## Final State

**C1-TERR-DQ-001:** COMPLETE
**C1-ELEC-2023-001:** VISIBLE EV-0112 FIELDS CONFIRMED — CONTINUE FOR BALLOT ACCOUNTING AND GEOGRAPHY
**Next loop:** `C1-ELEC-2023-002 — Ballot Accounting, Second Review, and Electoral Geography`