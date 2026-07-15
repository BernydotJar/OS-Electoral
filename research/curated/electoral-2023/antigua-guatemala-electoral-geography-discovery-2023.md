# Antigua Guatemala 2023 Electoral Geography Discovery

Program: `C1-ELEC-2023-003`
Workstream: Official electoral-geography discovery and ingestion
Territory: Antigua Guatemala, Sacatepequez
Election year: 2023
Review date: 2026-07-14
Status: `PARTIAL_OFFICIAL_MUNICIPAL_SUMMARY_INGESTED`

## Discovery Outcome

This loop authenticated and ingested one official municipality-level electoral-geography summary for Antigua Guatemala:

| Field | Value | Source |
|---|---:|---|
| Registered electorate | 39,099 | `ELEC23-GEO-SRC-001` |
| JRV count | 100 | `ELEC23-GEO-SRC-001` |
| JRV initial range | 5,337 | `ELEC23-GEO-SRC-001` |
| JRV final range | 5,436 | `ELEC23-GEO-SRC-001` |
| Voting-center count | 18 | `ELEC23-GEO-SRC-001` |

The ingested row is stored in:

`research/curated/electoral-2023/antigua-guatemala-electoral-geography-2023.csv`

## Official Sources Audited

The source audit is stored in:

`research/electoral-2023/electoral-geography-source-audit.csv`

### ELEC23-GEO-SRC-001

Official TSE PDF:

`https://tse.org.gt/images/direlec/juntas_recep/Juntas%20Receptoras%20de%20Votos%20por%20Municipio.pdf`

Recorded SHA-256:

`673bd15990aa9dfe52e19443b19438ddbb5445cd418a9949eae4fb0ae6457889`

Decision:

`OFFICIAL_SOURCE_AUTHENTICATED`

This source is strong enough to populate municipality-level JRV summary fields, but not center names, addresses, communities, or center-to-JRV assignments.

### ELEC23-GEO-SRC-002

Official TSE cartography image for Antigua Guatemala:

`https://tse.org.gt/images/cartografia/02%20SACATEP%C3%89QUEZ/02-01%20ANTIGUA%20GUATEMALA-min.jpg`

Recorded SHA-256:

`1c6d2f8cbbd328a69c8eaf9d3b1282273c973465287d8c63bd151c649140c923`

Decision:

`OFFICIAL_SOURCE_AUTHENTICATED_PARTIAL`

The image confirms an official cartography source and visible electoral-area labels. This loop does not promote names, addresses, center codes, or community assignments from the image because doing so would require controlled OCR/manual transcription and a separate validation pass.

## Dashboard Conflict

The derived campaign dashboards previously audited as `DERIVED_DISCOVERY_AID_ONLY` reported:

```text
centros = 19
jrv = 100
```

The authenticated TSE PDF reports:

```text
centros = 18
jrv = 100
```

Decision:

`OFFICIAL_SOURCE_PREVAILS_FOR_INGESTED_MUNICIPAL_SUMMARY`

The dashboard value `19` is not promoted. The conflict remains documented because the dashboard may be pointing to a later internal model, a different definition of center, or an error; no correction is inferred without the underlying official record.

## Crosswalk State

Current crosswalk status:

`PARTIAL_NO_CENTER_OR_COMMUNITY_CROSSWALK`

Still missing:

- official center names;
- official center addresses or institutional locations;
- JRV-to-center assignments;
- community-to-center relationships;
- center-to-CEM or campaign-territory relationships;
- any row-level link to EV-0105 community units.

## Prohibited Use

This artifact does not authorize:

- community ranking;
- segment selection;
- persuasion scoring;
- turnout modeling;
- paid-media geofencing;
- mobilization planning;
- assignment of voters or volunteers to centers.

## Next Increment

The next increment should perform controlled extraction of the official Antigua Guatemala cartography image or obtain a TSE table/listing that explicitly provides center names, addresses, and JRV assignments.

Until that exists, the official geography baseline remains partial.
