# C1-ELEC-2023-004 — Partial Ballot Accounting Report

Date: 2026-07-15  
Branch: `agent/c1-elec-2023-ballot-accounting-partial`  
Primary station: Electoral Research  
State: `PARTIAL_RECONCILIATION`

## Objective

Advance the official 2023 Antigua Guatemala ballot-accounting workstream without inferring missing categories.

## Result

The previously empty official accounting CSV now contains one authenticated field:

```text
registered_electorate = 39,099
source = EV-0139 / Tribunal Supremo Electoral
```

The figure is accepted as the 2023 municipality-level registered electorate and may serve as a denominator only after an official ballots-cast numerator is authenticated.

## Preserved evidence boundary

```text
visible_organization_vote_sum = 26,091
status = DERIVED_FROM_14_CONFIRMED_VISIBLE_ROWS
```

`26,091` is not promoted to ballots cast, printed valid votes, turnout, participation, or any ballot category.

## Task ledger

| Task | State | Result |
|---|---|---|
| Verify merged geography baseline | PASS | PR #18 merge commit `cacf50a...` confirmed |
| Inspect prior ballot-accounting artifact | PASS | CSV was header-only; outcome `NOT_RECONCILED` |
| Authenticate 2023 electorate denominator | PASS | EV-0139 = 39,099 |
| Populate official accounting CSV | PASS | One authenticated row added |
| Reconcile 26,091 | PARTIAL | Visible-row sum preserved; printed role unresolved |
| Resolve ballots cast | BLOCKED | No authenticated municipality-specific official record found |
| Resolve null/blank/other categories | BLOCKED | No authenticated municipality-specific official record found |
| Calculate participation/abstention | BLOCKED | Official ballots-cast numerator unavailable |
| Correct global program status | PASS | Geography marked reconciled; accounting marked partial |
| Add fail-closed validation | PASS | Validator prohibits unsupported rates and identities |
| Political-gate review | PASS | All gates remain closed |

## Validation contract

The validator requires:

- exactly one populated official accounting row;
- field `registered_electorate`;
- value `39099`;
- `OFFICIAL_SOURCE_AUTHENTICATED` status;
- blank `election_date` because the cited source row does not print it;
- 14 visible result rows summing to `26,091`;
- `PARTIAL_RECONCILIATION` status;
- no asserted participation, abstention, ballots-cast, or printed-valid-vote total.

## Remaining authoritative inputs

- ballots cast;
- printed valid-vote total;
- null votes;
- blank votes;
- challenged or other categories;
- complete accounting identity.

## Resume condition

Resume when a TSE or legally equivalent record explicitly identifies Antigua Guatemala, the 2023 municipal election, and one or more unresolved accounting fields with stable provenance.

## Political gate

No segment, ranking, narrative, paid media, targeting, microtargeting, mobilization, public promise, attack, or voter-level action is authorized.
