# Spec: C1-ELEC-2023-005 — Final Ballot Accounting Reconciliation

Status: Draft  
Owner: Electoral Research  
Parent: `C1-ELEC-2023-004`

## Purpose

Resolve, or precisely bound, the conflict between the preliminary TREP municipal accounting for Antigua Guatemala and the definitive visible organization-vote rows confirmed in EV-0112.

This workstream is evidence and governance only. It does not authorize political segmentation, territorial ranking, narrative, targeting, paid media, mobilization, public promises, attacks, or individual-voter records.

## Accepted Baseline

Treat the following as established:

- official registered electorate: `39,099`;
- EV-0112 final visible organization-vote sum: `26,091`;
- preliminary TREP `tc4` valid/party-vote-like total: `25,827`;
- difference: `264`;
- preliminary TREP emitted/ballots-cast-like: `26,828`;
- preliminary TREP null votes: `912`;
- preliminary TREP blank votes: `89`;
- preliminary TREP actas: `100 total`, `100 captured`, `99 counted`;
- TREP status: `PRELIMINARY_CONFLICT_NOT_PROMOTED`;
- current ballot-accounting outcome: `PARTIAL_RECONCILIATION`;
- electoral geography: reconciled at center and JRV level;
- political gates: closed.

## Central Research Questions

1. Which acta or JRV record was captured but not counted in the TREP snapshot?
2. Does that record explain the `264`-vote difference between preliminary TREP and EV-0112 final visible rows?
3. Is there a definitive TSE/JED consolidated record publishing ballots cast, valid votes, null votes, blank votes, challenged votes, or complete accounting for Antigua Guatemala municipal corporation 2023?
4. Can preliminary categories be reconciled to definitive categories without inference?

## Workstream A — TREP Snapshot Authentication

Record and preserve:

- `ultimoCorte.json` metadata;
- exact JSON URL and path;
- compressed and decoded SHA-256 hashes;
- election type `tc4` identity;
- department and municipality identifiers;
- acta totals and accounting fields;
- retrieval date and limitations.

The TREP snapshot remains preliminary evidence unless a definitive source explicitly validates it.

## Workstream B — Missing Acta Identification

Identify the one acta represented by:

```text
actas_total = 100
actas_captured = 100
actas_counted = 99
```

Required evidence may include:

- official acta index;
- official JRV-level result JSON;
- acta image or PDF;
- official incident/status field;
- definitive JED/TSE resolution.

Do not infer the missing acta from arithmetic alone.

## Workstream C — Definitive Accounting Discovery

Search authoritative sources for:

- final municipal consolidated acta;
- Documento No. 4 or equivalent municipal consolidation;
- final JED agreement annex;
- TSE definitive downloadable result dataset;
- electoral memory with municipality-level accounting;
- official acta/JRV records sufficient to aggregate all 100 JRV.

Every accepted record must identify:

```text
year = 2023
election = corporacion municipal
department = Sacatepequez
municipality = Antigua Guatemala
```

## Workstream D — Reconciliation

Allowed outcomes:

- `RECONCILED_DEFINITIVE_ACCOUNTING`
- `RECONCILED_WITH_DOCUMENTED_FINAL_ADJUSTMENT`
- `PARTIAL_RECONCILIATION_WITH_IDENTIFIED_MISSING_ACTA`
- `PRELIMINARY_CONFLICT_UNRESOLVED`
- `OFFICIAL_SOURCE_CONFLICT`

A reconciliation must show equations and source provenance.

No residual category may be inferred from:

```text
39,099 - 26,091
26,828 - 26,091
26,091 - 25,827
```

unless an authoritative source explicitly defines the relevant categories.

## Required Artifacts

```text
research/curated/electoral-2023/
├── final-ballot-accounting-reconciliation-2023.md
├── final-ballot-accounting-fields-2023.csv
├── missing-trep-acta-investigation-2023.csv
└── C1-ELEC-2023-005-implementation-report.md

research/electoral-2023/
├── final-ballot-source-audit.csv
├── official-source-register.md
└── source-acquisition-log.md

scripts/evidence/
└── validate_final_ballot_reconciliation.py
```

## Data Rules

### Final accounting fields

Required columns:

```text
evidence_id,field_name,field_value,unit,source_id,source_record,source_location,source_status,verification_status,limitations
```

### Missing-acta investigation

Required columns:

```text
record_key,jrv_id,acta_id,center_code,trep_status,official_source_id,source_location,investigation_status,observed_values,limitations
```

Allowed investigation statuses:

- `IDENTIFIED_OFFICIAL`
- `CANDIDATE_NOT_CONFIRMED`
- `NOT_IDENTIFIED`
- `CONFLICT`

## Acceptance Criteria

1. The merged PR #19 baseline remains unchanged unless stronger evidence supersedes it.
2. TREP preliminary values are not promoted silently.
3. The missing acta is identified only from an official record.
4. Every accepted numeric field has authority, scope, location, and status.
5. Definitive and preliminary values remain distinguishable.
6. Any `264` reconciliation is equation-backed and source-backed.
7. Participation and abstention are calculated only from matched definitive numerator and denominator.
8. No individual voter data is collected.
9. No personal absolute paths are committed.
10. Political gates remain closed.

## Validation

At minimum:

- parse all CSVs;
- validate required columns and enums;
- verify `26,091 - 25,827 = 264`;
- verify preliminary identity `25,827 + 912 + 89 = 26,828` only as a TREP preliminary equation;
- reject promotion of preliminary values without definitive support;
- verify every final field has definitive provenance;
- reject unsupported participation or abstention;
- scan for `/Users/`, voter-level PII, and prohibited political recommendations;
- run `git diff --check`.

## Stop Conditions

Stop with a documented blocker when:

- the TREP acta-level endpoint cannot be authenticated;
- the missing acta cannot be identified from official records;
- a definitive consolidated source is unavailable;
- sources conflict and no competent final authority resolves them;
- continuing would require residual inference.

A blocker affects only its workstream. Continue independent acquisition, validation, and governance updates while productive work remains.

## Definition of Done

The loop is complete when the preliminary TREP conflict is either reconciled to a definitive official accounting record or bounded by an exact, reproducible blocker; the missing-acta investigation is documented; accounting fields are promoted only with definitive provenance; validation passes; and political gates remain closed.
