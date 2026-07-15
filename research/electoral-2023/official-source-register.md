# Official 2023 Electoral Source Register

Program: `C1-ELEC-2023-001`  
Review date: 2026-07-14  
Territory: Antigua Guatemala, Sacatepequez  
Status: Discovery active; EV-0112 visible result rows second-review confirmed; participation and geography still blocked

## Source authority rule

Only the Tribunal Supremo Electoral de Guatemala or another legally authoritative official record may support official vote totals, ballot accounting, adjudication, polling-center identifiers, or electoral-geography facts.

Secondary pages, news reports, campaign posts, encyclopedias, and social media may be used only as discovery aids. They cannot populate the official results table.

## Registered sources

| Source ID | Evidence ID | Authority | Title or description | Type | Location | Scope | Fields available | Status | Limitations |
|---|---|---|---|---|---|---|---|---|---|
| ELEC23-SRC-001 | EV-0112 | Tribunal Supremo Electoral | Acuerdo Numero 01-2023 declaring validity of the municipal corporation election for Antigua Guatemala | Official legal PDF | Local source under `POLITICS_ROOT`; second-review manifest at `research/curated/electoral-2023/EV-0112-second-review-manifest.json` | Antigua Guatemala municipal election | Agreement number; legal validity; winning slate; elected offices; visible organization vote rows | `CONFIRMED_SECOND_REVIEW_FOR_VISIBLE_FIELDS` | Visible fields confirmed by rendered-source review; no turnout, blank, null, registered-electorate, polling-center, or voting-table fields captured |
| ELEC23-SRC-002 | Pending | Tribunal Supremo Electoral | Detailed 2023 municipal results record or downloadable dataset | Official results record | Not yet authenticated beyond EV-0112 legal agreement | Antigua Guatemala municipal election | Organization or slate; votes; valid, null, blank, challenged, total ballots when published | `PARTIAL_FROM_EV-0112` | EV-0112 supplies organization vote rows, but no separate detailed ballot-accounting dataset has yet been authenticated |
| ELEC23-SRC-003 | Pending | Tribunal Supremo Electoral | 2023 polling-center and voting-table inventory | Official electoral-geography record | Not yet authenticated | Antigua Guatemala | Center identifiers, addresses or locality labels, table identifiers, assigned electorate when published | `BLOCKED_DISCOVERY` | No authenticated, repository-accessible geography record has yet been registered |
| ELEC23-SRC-004 | EV-0111 | Tribunal Supremo Electoral | Electoral-roll statistics as of 2026-04-30 | Official aggregate PDF | Curated baseline at `research/curated/territorio/EV-0111-baseline.md` | Antigua Guatemala municipality | Aggregate registered electorate and literacy-status breakdown | `CURATED_REFERENCE` | 2026 roll is context only; it cannot be substituted for the 2023 election denominator |
| ELEC23-SRC-005 | Derived | Campaign dashboard / derived model | Territorio electoral dashboard values for Sacatepequez and Antigua Guatemala | Derived local HTML | `research/electoral-2023/derived-territorio-electoral-source-audit.csv` | Sacatepequez and Antigua Guatemala | Derived pointers: 2023 visible vote total, centers, JRV, claimed TSE/JED/cartography sources | `DERIVED_DISCOVERY_AID_ONLY` | Not an official source; do not populate official ballot accounting or geography from this dashboard without underlying official records |

## Discovery attempts

Official-domain and exact-title searches were initiated for:

- Antigua Guatemala municipal results for the 2023 general election;
- the exact title of the municipal validity agreement;
- polling-center and voting-table records for Antigua Guatemala;
- Sacatepequez municipal-result datasets.

For the independent EV-0112 review, the source PDF was later found through local `POLITICS_ROOT` access and prepared into rendered review materials. Local derived dashboard apps were also audited as discovery aids. Detailed attempts are recorded in `research/electoral-2023/source-acquisition-log.md`.

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

`EV-0112_SECOND_REVIEW: CONFIRMED_VISIBLE_FIELDS`

Reason: EV-0112 supports legal validation facts and visible organization vote rows confirmed through independent rendered-source review. Full ballot accounting and electoral-geography records have not yet been authenticated and ingested.

These remaining blockers do not authorize inference from secondary sources or derived campaign dashboards.
