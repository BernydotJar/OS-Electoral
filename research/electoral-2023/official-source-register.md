# Official 2023 Electoral Source Register

Program: `C1-ELEC-2023-001`  
Review date: 2026-07-14  
Territory: Antigua Guatemala, Sacatepequez  
Status: Discovery active; numerical baseline blocked pending authoritative detailed records

## Source authority rule

Only the Tribunal Supremo Electoral de Guatemala or another legally authoritative official record may support official vote totals, ballot accounting, adjudication, polling-center identifiers, or electoral-geography facts.

Secondary pages, news reports, campaign posts, encyclopedias, and social media may be used only as discovery aids. They cannot populate the official results table.

## Registered sources

| Source ID | Evidence ID | Authority | Title or description | Type | Location | Scope | Fields available | Status | Limitations |
|---|---|---|---|---|---|---|---|---|---|
| ELEC23-SRC-001 | EV-0112 | Tribunal Supremo Electoral | Acuerdo Numero 01-2023 declaring validity of the municipal corporation election for Antigua Guatemala | Official legal PDF | Local source under `POLITICS_ROOT`; raw extraction at `research/extracted/territorio/EV-0112.md` | Antigua Guatemala municipal election | Agreement number; page count; visible legal and result-table content | `PARTIAL` | Three substantive image-based pages require controlled OCR or reviewed transcription; detailed values are not yet machine-readable |
| ELEC23-SRC-002 | Pending | Tribunal Supremo Electoral | Detailed 2023 municipal results record or downloadable dataset | Official results record | Not yet authenticated | Antigua Guatemala municipal election | Organization or slate; votes; valid, null, blank, challenged, total ballots when published | `BLOCKED_DISCOVERY` | No authenticated, repository-accessible detailed record has yet been registered |
| ELEC23-SRC-003 | Pending | Tribunal Supremo Electoral | 2023 polling-center and voting-table inventory | Official electoral-geography record | Not yet authenticated | Antigua Guatemala | Center identifiers, addresses or locality labels, table identifiers, assigned electorate when published | `BLOCKED_DISCOVERY` | No authenticated, repository-accessible geography record has yet been registered |
| ELEC23-SRC-004 | EV-0111 | Tribunal Supremo Electoral | Electoral-roll statistics as of 2026-04-30 | Official aggregate PDF | Curated baseline at `research/curated/territorio/EV-0111-baseline.md` | Antigua Guatemala municipality | Aggregate registered electorate and literacy-status breakdown | `CURATED_REFERENCE` | 2026 roll is context only; it cannot be substituted for the 2023 election denominator |

## Discovery attempts

Official-domain and exact-title searches were initiated for:

- Antigua Guatemala municipal results for the 2023 general election;
- the exact title of the municipal validity agreement;
- polling-center and voting-table records for Antigua Guatemala;
- Sacatepequez municipal-result datasets.

No detailed numerical or geography source is promoted by this register until its authority, exact scope, and record identity are authenticated.

## Required intake evidence

A newly discovered source is not accepted until the register records:

1. official authority;
2. stable URL or repository path;
3. title and date;
4. territorial and election scope;
5. available fields;
6. content hash when downloaded;
7. extraction status;
8. limitations and missing fields.

## Current decision

`OFFICIAL_NUMERICAL_BASELINE: BLOCKED`

Reason: EV-0112 supports the existence and legal validation of the election, but detailed official vote totals and electoral-geography records have not yet been authenticated and ingested.

This blocker does not authorize inference from secondary sources.