# Official 2023 Electoral Source Register

Program: `C1-ELEC-2023-001`  
Review date: 2026-07-15  
Territory: Antigua Guatemala, Sacatepequez  
Status: EV-0112 visible fields confirmed; electoral geography reconciled at center/JRV level; ballot accounting partial with preliminary TREP conflict documented

## Source authority rule

Only the Tribunal Supremo Electoral de Guatemala or another legally authoritative official record may support official vote totals, ballot accounting, adjudication, polling-center identifiers, or electoral-geography facts.

Secondary pages, news reports, campaign posts, encyclopedias, social media, and campaign dashboards may be used only as discovery aids.

## Registered sources

| Source ID | Evidence ID | Authority | Title or description | Type | Location | Scope | Fields available | Status | Limitations |
|---|---|---|---|---|---|---|---|---|---|
| ELEC23-SRC-001 | EV-0112 | Tribunal Supremo Electoral | Acuerdo Numero 01-2023 declaring validity of the municipal corporation election for Antigua Guatemala | Official legal PDF | Local source under `POLITICS_ROOT`; second-review manifest committed | Antigua Guatemala municipal election | Agreement number; legal validity; winning slate; elected offices; visible organization vote rows | `CONFIRMED_SECOND_REVIEW_FOR_VISIBLE_FIELDS` | No turnout, blank, null, or complete ballot accounting |
| ELEC23-SRC-002 | Pending | Tribunal Supremo Electoral | Detailed 2023 municipal results or ballot-accounting record | Official results record | Not yet authenticated beyond EV-0112 | Antigua Guatemala municipal election | Valid, null, blank, challenged, ballots cast, participation when published | `BLOCKED_DISCOVERY` | No complete official accounting identity ingested |
| ELEC23-SRC-004 | EV-0111 | Tribunal Supremo Electoral | Electoral-roll statistics as of 2026-04-30 | Official aggregate PDF | Curated baseline | Antigua Guatemala municipality | Aggregate registered electorate | `CURATED_REFERENCE` | 2026 roll cannot substitute for 2023 election denominator |
| ELEC23-SRC-005 | Derived | Campaign dashboard / derived model | Territorio electoral dashboard | Derived local HTML | Source-audit CSV | Antigua Guatemala | Derived source pointers | `DERIVED_DISCOVERY_AID_ONLY` | Dashboard value `centros=19` rejected in favor of official `18` |
| ELEC23-SRC-006 | EV-0139 | Tribunal Supremo Electoral | Juntas Receptoras de Votos por Municipio | Official PDF | `electoral-geography-source-audit.csv` | Antigua Guatemala municipality | 39,099 registered; 100 JRV; range 5,337-5,436; 18 centers | `OFFICIAL_SOURCE_AUTHENTICATED` | Municipality summary only |
| ELEC23-SRC-007 | EV-0140 | Tribunal Supremo Electoral | Mapa descentralizacion del voto — Antigua Guatemala | Official cartography image | `electoral-geography-source-audit.csv` | Antigua Guatemala municipality | Cartographic labels and boundaries | `OFFICIAL_SOURCE_AUTHENTICATED_PARTIAL` | New OCR pass blocked by unavailable image bytes in runtime; no OCR row promoted |
| ELEC23-SRC-008 | EV-0141 | Tribunal Supremo Electoral | Listado de Circunscripciones Electorales Municipales | Official PDF | `electoral-geography-source-audit.csv` | Antigua Guatemala | Four CEM identities | `OFFICIAL_SOURCE_AUTHENTICATED_AND_VISUALLY_REVIEWED` | CEM labels are not voting-center identities |
| ELEC23-SRC-009 | EV-0142 | Tribunal Supremo Electoral | Centros de Votación 2023 por Agrupación — primera vuelta | Official PDF | `electoral-geography-source-audit.csv` | Antigua Guatemala | 18 center identities; locations; 19 assignment records; 100 JRV; 39,099 registered; explicit grouping/CEM labels | `OFFICIAL_SOURCE_AUTHENTICATED_AND_INGESTED` | Center 7 has two explicit assignment records and is deduplicated only in the identity inventory |
| ELEC23-SRC-010 | EV-0143 | Tribunal Supremo Electoral | TREP primera elección 2023 `tc4` Corporación Municipal | Official preliminary JSON | `trep-preliminary-ballot-accounting-audit.csv` | Antigua Guatemala municipal corporation | Preliminary emitted, valid-like, null, blank, registered-electorate, and acta-count fields | `PRELIMINARY_CONFLICT_NOT_PROMOTED` | Preliminary record has 99 counted actas and conflicts with final EV-0112 visible-row sum; not used for final accounting fields |

## Geography decision

```text
CENTER_CAPTURE = RECONCILED_18_CONFIRMED_CENTERS
JRV_ASSIGNMENT = RECONCILED_100_JRV_ASSIGNED
CARTOGRAPHY_OCR = PARTIAL_SOURCE_BYTES_UNAVAILABLE_IN_RUNTIME
```

Confirmed crosswalks are limited to relationships explicitly printed by TSE: center to grouping and grouping to Cabecera Municipal or named CEM. No campaign-community, voter-support, priority, or mobilization relationship is authorized.

## Current decision

`EV-0112_SECOND_REVIEW: CONFIRMED_VISIBLE_FIELDS`

`OFFICIAL_ELECTORAL_GEOGRAPHY: RECONCILED_CENTER_AND_JRV_LEVEL`

`OFFICIAL_BALLOT_ACCOUNTING: PARTIAL_RECONCILIATION`

`PRELIMINARY_TREP_ACCOUNTING: CONFLICT_DOCUMENTED_NOT_PROMOTED`

Political gates remain closed.
