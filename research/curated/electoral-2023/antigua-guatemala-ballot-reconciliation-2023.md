# Antigua Guatemala 2023 Ballot Reconciliation

Program: `C1-ELEC-2023-002`  
Workstream: Official ballot accounting  
Territory: Antigua Guatemala, Sacatepéquez  
Election: Municipal corporation, 2023  
Status: `PARTIAL_RECONCILIATION`

## Established Inputs

| Field | Value | Status | Source |
|---|---:|---|---|
| Confirmed visible organization-vote rows | 14 | `CONFIRMED_SECOND_REVIEW_FOR_VISIBLE_FIELDS` | EV-0112 page 1 |
| Derived visible organization-vote sum | 26,091 | `DERIVED` | Sum of the 14 independently confirmed rows |
| Registered electorate | 39,099 | `OFFICIAL_SOURCE_AUTHENTICATED` | EV-0139, TSE `Juntas Receptoras de Votos por Municipio`, Antigua Guatemala row |

The value `26,091` is not treated as ballots cast, participation, a printed valid-vote total, null votes, blank votes, or abstention.

The value `39,099` is accepted as the official 2023 municipality-level registered electorate. It supplies a valid denominator for a future participation calculation, but no participation rate is calculated because the matching official ballots-cast numerator remains unavailable.

## Authoritative Fields Required

| Field | Current state | Required authority |
|---|---|---|
| Registered electorate for the 2023 municipal election | `CONFIRMED: 39,099` | EV-0139 / TSE |
| Ballots cast | `UNRESOLVED` | TSE or competent electoral authority |
| Printed valid-vote total | `UNRESOLVED` | TSE or competent electoral authority |
| Null votes | `UNRESOLVED` | TSE or competent electoral authority |
| Blank votes | `UNRESOLVED` | TSE or competent electoral authority |
| Challenged or other categories | `UNRESOLVED` | TSE or competent electoral authority |
| Participation rate | `NOT_CALCULATED` | Matching official ballots-cast numerator |
| Abstention rate | `NOT_CALCULATED` | Matching official ballots-cast numerator |

## Discovery Result

The TSE municipality-level JRV summary resolved the registered-electorate denominator. Directed searches of official TSE pages, the preliminary first-election portal, acta/result terms, and repository references did not produce an authenticated Antigua Guatemala municipal ballot-accounting record with ballots cast, printed valid votes, null votes, blank votes, or complete accounting categories.

The preliminary TREP portal was inspected as a discovery lead. Its first-election `tc4` JSON identifies the Antigua Guatemala municipal-corporation scope and contains preliminary accounting-like fields, but it is not promoted into the official accounting CSV.

Recorded TREP preliminary values:

| Field | Value | Status |
|---|---:|---|
| Actas total | 100 | Preliminary TREP |
| Actas captured | 100 | Preliminary TREP |
| Actas counted | 99 | Preliminary TREP |
| Registered electorate | 39,099 | Matches EV-0139 denominator |
| Ballots cast-like field | 26,828 | `PRELIMINARY_CONFLICT_NOT_PROMOTED` |
| Valid votes-like field | 25,827 | `PRELIMINARY_CONFLICT_NOT_PROMOTED` |
| Null votes-like field | 912 | `PRELIMINARY_CONFLICT_NOT_PROMOTED` |
| Blank votes-like field | 89 | `PRELIMINARY_CONFLICT_NOT_PROMOTED` |

The TREP preliminary valid/party-vote total is `25,827`, while the final EV-0112 confirmed visible organization rows sum to `26,091`. Because the TREP record is preliminary and differs from the final legal agreement, its accounting-like fields remain documented in `research/electoral-2023/trep-preliminary-ballot-accounting-audit.csv` only.

Secondary national summaries, records for other municipalities, news reports, and campaign dashboards remain excluded from the official accounting dataset.

## Reconciliation Tests

Confirmed visible organization rows:

```text
organization_vote_sum = 6,543 + 5,850 + 5,645 + 1,712 + 1,566 + 1,210
                      + 989 + 837 + 484 + 360 + 353 + 236 + 229 + 77
                      = 26,091
```

Confirmed electorate denominator:

```text
registered_electorate = 39,099
```

The following identities remain unevaluable:

```text
printed_valid_vote_total ?= 26,091
ballots_cast ?= valid_votes + null_votes + blank_votes + other_categories
participation_rate ?= ballots_cast / 39,099
abstention_rate ?= 1 - participation_rate
```

No residual category is inferred by subtracting `26,091` from `39,099` because registered electorate is not equivalent to ballots cast.

## Outcome

`PARTIAL_RECONCILIATION`

Resolved:

- official registered electorate: `39,099`;
- 14 visible organization-vote rows;
- derived visible-row sum: `26,091`.

Still blocked:

- ballots cast;
- printed valid-vote total;
- null votes;
- blank votes;
- challenged or other categories;
- participation;
- abstention.
- final reconciliation between preliminary TREP accounting-like fields and the definitive EV-0112 agreement.

## Resume Condition

Resume when an official record explicitly identifying Antigua Guatemala and the 2023 municipal election provides one or more unresolved accounting fields. Record authority, title, date, election and territorial scope, stable URL or portable path, page/table/row provenance, and content hash before ingestion.

## Political Gate

This artifact does not authorize segment selection, territorial ranking, narrative, paid media, targeting, field mobilization, public promises, or attacks.
