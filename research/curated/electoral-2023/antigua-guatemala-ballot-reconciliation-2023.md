# Antigua Guatemala 2023 Ballot Reconciliation

Program: `C1-ELEC-2023-002`  
Workstream: Official ballot accounting  
Territory: Antigua Guatemala, Sacatepéquez  
Election: Municipal corporation, 2023  
Status: `NOT_RECONCILED`

## Established Input

| Field | Value | Status | Source |
|---|---:|---|---|
| Confirmed visible organization-vote rows | 14 | `CONFIRMED_SECOND_REVIEW_FOR_VISIBLE_FIELDS` | EV-0112 page 1 |
| Derived visible organization-vote sum | 26,091 | `DERIVED` | Sum of the 14 independently confirmed rows |

The value `26,091` is not treated as ballots cast, participation, a printed valid-vote total, registered electorate, null votes, blank votes, or abstention.

## Authoritative Fields Required

| Field | Current state | Required authority |
|---|---|---|
| Registered electorate for the 2023 municipal election | `UNRESOLVED` | TSE or competent electoral authority |
| Ballots cast | `UNRESOLVED` | TSE or competent electoral authority |
| Printed valid-vote total | `UNRESOLVED` | TSE or competent electoral authority |
| Null votes | `UNRESOLVED` | TSE or competent electoral authority |
| Blank votes | `UNRESOLVED` | TSE or competent electoral authority |
| Challenged or other categories | `UNRESOLVED` | TSE or competent electoral authority |
| Participation rate | `NOT_CALCULATED` | Matching official numerator and denominator |
| Abstention rate | `NOT_CALCULATED` | Matching official numerator and denominator |

## Discovery Result

Official-domain and general web searches did not identify an authenticated, municipality-specific TSE dataset or official record containing the missing ballot-accounting fields for Antigua Guatemala.

Secondary national summaries and records for other municipalities were excluded because they do not match the municipality and election scope. Local campaign dashboards were retained only as `DERIVED_DISCOVERY_AID_ONLY` and do not populate the official accounting dataset.

## Reconciliation Test

Current equation:

```text
organization_vote_sum = 6,543 + 5,850 + 5,645 + 1,712 + 1,566 + 1,210
                      + 989 + 837 + 484 + 360 + 353 + 236 + 229 + 77
                      = 26,091
```

This equation reproduces the visible organization rows only.

The following identities cannot yet be evaluated:

```text
printed_valid_vote_total ?= 26,091
ballots_cast ?= valid_votes + null_votes + blank_votes + other_categories
participation_rate ?= ballots_cast / registered_electorate
abstention_rate ?= 1 - participation_rate
```

## Outcome

`NOT_RECONCILED`

Reason: no authoritative Antigua Guatemala ballot-accounting record has been authenticated and ingested beyond the visible organization vote rows in EV-0112.

## Resume Condition

Resume when an official record is available that explicitly identifies Antigua Guatemala and provides one or more of the missing accounting fields. Record authority, title, date, scope, stable URL or portable path, page/table/row provenance, and content hash before populating the CSV.

## Political Gate

This artifact does not authorize segment selection, territorial ranking, narrative, paid media, targeting, field mobilization, public promises, or attacks.
