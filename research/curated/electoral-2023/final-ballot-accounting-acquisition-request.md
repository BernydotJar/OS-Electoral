# Definitive Ballot Accounting Acquisition Request

Program: `C1-ELEC-2023-005`
Territory: Antigua Guatemala, Sacatepequez
Election: Corporacion Municipal, 2023
Status: `BLOCKED_PENDING_DEFINITIVE_AUTHORITY_RECORD`

## Purpose

Obtain a definitive official record that resolves the final ballot accounting for Antigua Guatemala and the final treatment of preliminary TREP mesa/JRV `5401`.

This request does not seek voter-level records, signatures, fiscal identities, DPI numbers, or any other personal data.

## Accepted baseline

- registered electorate: `39,099`;
- definitive EV-0112 visible organization-row sum: `26,091`;
- preliminary TREP valid/party-vote-like total: `25,827`;
- preliminary TREP null votes: `912`;
- preliminary TREP blank votes: `89`;
- preliminary TREP emitted total: `26,828`;
- preliminary TREP actas: `100 total`, `100 captured`, `99 counted`;
- identified non-counted preliminary mesa: `5401`, seccion `538`;
- preliminary observation: `Acta ilegible`;
- electoral roll assigned to mesa `5401`: `380`;
- definitive-vs-preliminary visible-vote difference: `264`.

The TREP values remain `PRELIMINARY_CONFLICT_NOT_PROMOTED`.

## Preferred competent authorities

Request the record from one or more of:

1. Tribunal Supremo Electoral de Guatemala;
2. Junta Electoral Departamental de Sacatepequez;
3. Junta Electoral Municipal de Antigua Guatemala;
4. official electoral archive or public-information unit holding the definitive scrutiny record.

## Exact records requested

Priority order:

1. `Acta Final de Cierre de Escrutinio - Documento No. 4` for the 2023 Corporacion Municipal election in Antigua Guatemala;
2. definitive municipal consolidation or adjudication worksheet showing valid, null, blank, challenged/other and total ballots;
3. competent final resolution, correction, recount or adjudication record for JRV/mesa `5401`;
4. official table-level result record for JRV `5401`, with personal signatures and identities redacted when supplied;
5. official explanation of the difference between the preliminary TREP total and the definitive municipal result.

## Required scope identifiers

A responsive record must explicitly match:

```text
year = 2023
election = Corporacion Municipal
department = Sacatepequez
municipality = Antigua Guatemala
mesa/JRV = 5401 when the record is table-specific
```

## Required accounting fields

Capture only fields printed or explicitly supplied by the competent authority:

- registered electorate;
- ballots issued or delivered, when defined;
- ballots deposited / votes cast / emitted total, using the authority's exact label;
- valid votes;
- votes by organization;
- null votes;
- blank votes;
- challenged, impugned or other official categories;
- unused, destroyed or missing ballots when part of the official accounting identity;
- total actas/JRV included;
- final treatment of mesa `5401`;
- date, authority, record identifier, page/table/row and final/preliminary status.

## Privacy constraint

Do not request or commit:

- voter names;
- voter identifiers;
- signatures;
- names or identifiers of polling-table staff or party fiscales when not necessary for provenance;
- unredacted acta images containing personal data.

A redacted official copy or certified aggregate transcription is sufficient.

## Acceptance criteria

The source may be promoted only when all applicable checks pass:

1. competent official authority;
2. definitive rather than preliminary status;
3. exact election and territorial scope;
4. stable URL, official response identifier or portable source path;
5. source hash when a file is obtained;
6. page, table, row, acta or record provenance;
7. explicit category definitions;
8. arithmetic identity reproducible from printed fields;
9. treatment of mesa `5401` stated or demonstrably included;
10. no reliance on residual inference.

## Reconciliation tests after acquisition

```text
final_valid_vote_total ?= 26,091
final_ballots_cast ?= final_valid_votes + final_null + final_blank + final_other
final_participation ?= final_ballots_cast / 39,099
final_abstention ?= 1 - final_participation
```

The equations may be evaluated only with matched definitive inputs from the same scope.

## Current decision

`PARTIAL_RECONCILIATION_WITH_IDENTIFIED_MISSING_ACTA`

## Resume condition

Resume the implementation loop when at least one exact requested record is available through an authenticated official URL, an official public-information response, or a portable file under `POLITICS_ROOT`.

Until then:

- preliminary TREP values remain unpromoted;
- participation and abstention remain uncalculated;
- the `264` difference remains bounded but unexplained;
- political gates remain closed.