# C1-ELEC-2023-002 Source Acquisition Log

Program: `C1-ELEC-2023-002`  
Active workstreams: EV-0112 independent second review; official ballot accounting  
Session date: 2026-07-14  
Agent station: Electoral Research  
Status: `EV-0112_SOURCE_RESOLVED; BALLOT_ACCOUNTING_BLOCKED`

## EV-0112 Source

| Field | Value |
|---|---|
| Evidence ID | `EV-0112` |
| Authority | Junta Electoral Departamental de Sacatepéquez |
| Document | `ACUERDO NUMERO 01-2023` |
| Expected pages | 3 substantive image-based pages |
| Portable path | `${POLITICS_ROOT}/07_Fichas_Comunitarias/ACUERDO 1-2023 Declarar la validez de la elección de la Corporación Municipal de ANTIGUA GUATEMALA, del Departamento de Sacatepéquez..pdf` |
| Alternative workspace path | `${POLITICS_ROOT}/EV-0112.pdf` |
| Required use | Independent visual second review; OCR is assistive only |

## EV-0112 Acquisition Attempts

| Attempt | Channel | Query or check | Result | Decision |
|---:|---|---|---|---|
| 1 | Workspace filesystem | Searched `external/politics/` recursively | PDF initially absent | Source unavailable in thin workspace |
| 2 | Thin Git checkout | Searched tracked files for EV-0112 source PDF | Repository contained derived text/CSV only | Do not treat derivatives as independent visual source |
| 3 | GitHub connector | Repository code search for the exact agreement title and number | No committed PDF match | Source not versioned in GitHub |
| 4 | ChatGPT File Library | Exact title, agreement number, authority, mayor name, and vote-table terms | No matching PDF | Source not available through File Library |
| 5 | Official-domain web discovery | Exact-title and authority searches restricted to `tse.org.gt` | No indexed official document found | No authenticated public copy acquired |
| 6 | Broad web discovery | Agreement number, organization names, and visible vote values | Secondary summaries found; no source document | Secondary material is not promoted to official evidence |
| 7 | Local source root | `POLITICS_ROOT` expected EV-0112 path | Source PDF found and prepared; SHA-256 recorded in committed manifest | Source blocker resolved for visual second review |
| 8 | Local derived dashboards | `Padron_Electoral` and `Eduardo_Sacahui_Campaign/public/territorio_electoral` | Derived Antigua values and source pointers found | Registered as discovery aids only; not official source material |

## EV-0112 Decision

- all 14 visible organization vote rows were independently confirmed;
- no vote row was corrected;
- the structured election date `2023-06-25` is `NOT_PRESENT` on the reviewed EV-0112 pages;
- the derived visible-row sum remains `26,091`;
- no turnout, ballot-accounting, geography, segment, narrative, paid media, targeting, or mobilization decision is authorized.

## Derived Dashboard Audit

The local dashboards are recorded in:

`research/electoral-2023/derived-territorio-electoral-source-audit.csv`

They preserve pointers to likely underlying sources, but are not sufficient to close ballot-accounting or geography blockers because they are campaign dashboards rather than original official datasets or PDFs.

---

## Official Ballot-Accounting Workstream

### Required Record

An authoritative TSE or competent electoral-authority record for the 2023 Antigua Guatemala municipal election containing one or more of:

- registered electorate;
- ballots cast;
- printed valid-vote total;
- null votes;
- blank votes;
- challenged or other ballot categories;
- participation or abstention;
- a complete printed accounting identity.

### Discovery Attempts

| Attempt | Channel | Query or check | Result | Decision |
|---:|---|---|---|---|
| BA-01 | Official-domain search | `site:tse.org.gt` queries for Antigua Guatemala municipal results, null votes, blank votes, participation, centers, and JRV | No indexed municipality-specific record returned | Do not populate accounting dataset |
| BA-02 | Historical-result portal search | Queries for TSE/result portal records and downloadable 2023 municipal data | No authenticated Antigua Guatemala record resolved | Keep source status unresolved |
| BA-03 | General web discovery | TSE Guatemala 2023 municipal result and downloadable dataset queries | Secondary national summaries and unrelated municipal examples found | Discovery aid only; wrong scope |
| BA-04 | Existing EV-0112 | Reviewed the three-page validity agreement | Provides 14 organization vote rows, but no printed registered electorate, ballots cast, null, blank, participation, or abstention fields | Preserve `26,091` as derived visible-row sum only |
| BA-05 | Local dashboards | Reviewed source audit for derived campaign dashboards | Derived values and pointers exist, but no underlying official record was authenticated | `DERIVED_DISCOVERY_AID_ONLY` |

### Excluded Sources

The following may help locate official records but cannot populate the official dataset:

- Wikipedia or other encyclopedic summaries;
- news reports;
- national-level election totals;
- ballot accounting for Ciudad de Guatemala or any other municipality;
- campaign dashboards and derived territorial models;
- values inferred as arithmetic residuals.

### Current Blocker

No authenticated official record has been ingested that matches all required dimensions:

```text
year = 2023
election = municipal corporation
municipality = Antigua Guatemala
department = Sacatepéquez
```

Until such a record is available:

- `antigua-guatemala-ballot-accounting-2023.csv` remains header-only;
- reconciliation outcome remains `NOT_RECONCILED`;
- participation and abstention remain uncalculated;
- `26,091` remains a derived sum of confirmed visible organization rows.

### Resume Condition

Resume when an official source is available with a stable URL or portable path and explicit Antigua Guatemala scope. Before ingestion, record:

1. authority;
2. title and date;
3. election and territorial scope;
4. stable URL or portable path;
5. content hash when downloaded;
6. page, table, acta, dataset-row, or record provenance;
7. limitations and missing fields.

## Remaining Work

The EV-0112 visual second review is complete. Remaining acquisition work should focus independently on:

1. official ballot accounting;
2. official electoral geography and explicit crosswalks.
