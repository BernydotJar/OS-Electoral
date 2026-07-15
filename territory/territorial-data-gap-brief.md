# Territorial Data-Gap Brief

Review date: 2026-07-14  
Spec: `C1-TERR-001`  
Scope: Antigua Guatemala municipality  
Owner: Electoral Research  
Reviewers: Territory; Tracking, Risks, and Learning  
Decision status: Research only

## Executive Summary

The four-source pilot now supports a limited curated territorial baseline:

- an official municipality-level electoral-roll snapshot for Antigua Guatemala;
- a campaign-research inventory of seven named communities with two retained numeric fields;
- a partial legal-election source whose three substantive pages still require controlled capture;
- a table-level catalog of eight validated PDM-OT table detections.

This baseline is sufficient to define the next research gaps. It is not sufficient to select a priority segment, rank communities, approve a geographic mobilization priority, produce public narrative, define paid-media audiences, or authorize field operations.

## Evidence Classification

| Evidence ID | Class | Curated status | Safe current use | Main limitation |
|---|---|---|---|---|
| EV-0111 | Official source | Curated, pending decision approval | Municipality-level aggregate electoral-roll baseline | No turnout, preference, support, or community-level electorate |
| EV-0105 | Campaign research | Curated, pending decision approval | Community inventory and source-field assessment | Methodology, estimates, access labels, and strategic-priority labels remain unverified |
| EV-0112 | Official source | Partial, curated subset available | Document identity, visible agreement number, page extent, and known extraction limitation | Three substantive pages remain untranscribed |
| EV-0114 | Official source | Partial, curated subset available | Location of eight validated table candidates and page-provenanced text | No fully normalized validated table dataset; planning period must be preserved |

## Confirmed Territorial Units

### Confirmed by EV-0105 campaign-research inventory

The reviewed workbook contains the following seven community names:

1. San Felipe de Jesús;
2. San Juan del Obispo;
3. San Bartolomé Becerra;
4. Santa Ana;
5. Santa Inés Monte Pulciano;
6. Santa Catarina Bobadilla;
7. San Pedro Las Huertas.

These names are confirmed as entries in the workbook, not yet as a complete or official municipal geography.

### Confirmed municipal scope

EV-0111 provides official aggregate electoral-roll values for the municipality of Antigua Guatemala.

EV-0114 provides municipal and regional planning context, but this loop did not produce a canonical crosswalk between:

- municipal boundaries;
- aldeas, barrios, colonias, caseríos, and zones;
- census geography;
- electoral districts, centers, or polling geography;
- campaign-operational territories.

## Confirmed Aggregate Electoral Facts

For the row `ANTIGUA GUATEMALA` on source page 2, as of April 30, 2026:

| Field | Value | Source |
|---|---:|---|
| Ciudadanos alfabetos - varones | 19,520 | EV-0111, page 2 |
| Ciudadanos alfabetos - mujeres | 20,420 | EV-0111, page 2 |
| Ciudadanos alfabetos - total | 39,940 | EV-0111, page 2 |
| Ciudadanos analfabetos - varones | 378 | EV-0111, page 2 |
| Ciudadanos analfabetos - mujeres | 1,266 | EV-0111, page 2 |
| Ciudadanos analfabetos - total | 1,644 | EV-0111, page 2 |
| Vigentes - total | 41,584 | EV-0111, page 2 |
| Fallecidos | 7,568 | EV-0111, page 2 |

These figures are registration statistics. They are not turnout, preference, candidate support, persuasion potential, or voting intention.

## Available Community Attributes

EV-0105 contains the following source fields:

- `Población (INE 2018)`;
- `Empadronados Est. (2023)`;
- `Nivel de Acceso`;
- `Prioridad Estratégica`.

The curated inventory retains only:

- community name and original spelling;
- workbook, sheet, and source-row provenance;
- population value labeled by the workbook as INE 2018;
- estimated registered electorate labeled as 2023;
- evidence class and verification status.

`Nivel de Acceso` and `Prioridad Estratégica` were not promoted because their methodology, date, reviewer, and scoring rules were not established, and because strategic-priority values could be mistaken for approved ranking.

## Available PDM-OT Structured Candidates

The deterministic EV-0114 table gate promoted eight table detections into a table-level curated catalog:

- education coverage, page 17 table 2;
- projection and planning, page 94 table 1;
- threshold and range, page 128 table 1;
- roadway classification, page 160 table 1;
- actions/programs/projects, page 205 table 2;
- execution/efficiency/effectiveness, page 210 table 1;
- priorities/targets/indicators, page 218 table 1;
- acronyms and abbreviations, page 221 table 1.

These entries identify validated table candidates. They do not yet constitute fully normalized, reconciled quantitative tables.

## Missing Demographic Fields

Before territorial comparison, the campaign lacks a verified community-level dataset containing:

- current population;
- age bands;
- sex distribution;
- literacy and education levels;
- employment and economic activity;
- household composition;
- migration and residence stability;
- language and identity variables where legally and ethically appropriate;
- disability and accessibility indicators;
- official source date and geographic crosswalk.

## Missing Electoral-History Fields

The current evidence does not provide:

- official detailed 2023 vote totals by candidate or party for Antigua Guatemala;
- valid, null, and blank vote breakdowns;
- turnout and abstention by election center or territorial unit;
- historical municipal-election series;
- polling-center or table-level geographic crosswalk;
- community-level official electorate;
- comparable boundary definitions across election years.

EV-0112 now provides a partial reviewed capture of the visible organization vote table and legal-adjudication facts. It still does not close gaps for turnout, abstention, null votes, blank votes, registered electorate, polling centers, voting tables, or electoral-geography crosswalks.

## Missing Field-Research Evidence

The current corpus lacks structured and auditable field evidence for:

- date and location of observation;
- respondent or stakeholder type;
- sample and recruitment method;
- interview or survey instrument;
- issue frequency and intensity;
- distinction between direct observation, testimony, perception, and hypothesis;
- corroboration across sources;
- resolution status and recency.

No community need should be treated as a verified current fact solely because it appears in campaign research.

## Missing Structure and Access Information

No approved operational baseline currently documents:

- volunteer count and verified availability;
- local coordinators;
- allied organizations;
- event or meeting access;
- field coverage capacity;
- transportation and logistics constraints;
- contact permissions and privacy basis;
- budget by territory;
- safe escalation and incident procedures.

These gaps block field mobilization planning.

## Source Conflicts and Version Ambiguity

### EV-0105 versus EV-0106

EV-0106 was extracted and compared against EV-0105. The files have different binary hashes, but the extracted `Resumen Comparativo` worksheet content is equivalent across:

- sheet names;
- dimensions;
- headers;
- formulas;
- blank flags;
- community names;
- all 40 extracted cells.

Current decision: `EV-0105_CANONICAL`.

This resolves the version ambiguity for the current curated inventory only. It does not validate the methodology behind estimated registered electorate, access labels, or strategic-priority labels.

### Official versus campaign-research values

EV-0105 estimated 2023 registered-elector values must not be reconciled silently with official 2026 municipality-level EV-0111 values. They differ in date, territorial granularity, evidence class, and likely methodology.

### PDM-OT period

EV-0114 is planning evidence. Every downstream claim must preserve the document's planning horizon and must not automatically be presented as a current 2026 condition.

## Decisions Still Blocked

The current evidence does not authorize:

- selecting a priority electoral segment;
- ranking or scoring communities;
- choosing a geographic mobilization priority;
- estimating political support or persuasion potential;
- approving public positioning or narrative;
- creating campaign claims or promises;
- defining paid-media audiences or budgets;
- initiating field operations.

## Recommended Next Research Actions

The following actions are ranked by decision value and evidence urgency, not by political target value.

| Research priority | Action | Decision value | Evidence urgency | Expected result |
|---:|---|---|---|---|
| 1 | Obtain official detailed 2023 municipal-election results and electoral-geography documentation | High | High | Establish historical electoral baseline and determine available geographic granularity |
| 2 | Complete controlled capture of EV-0112 pages 1-3 | Medium-High | High | Confirm legal effect, parties/slates, visible totals, and the document's actual limits |
| 3 | Preserve EV-0105 as canonical and keep EV-0106 as an equivalent alternate copy | Complete for current workbook content | Complete | Version ambiguity resolved for current curated inventory; campaign estimates and priority labels remain non-decision evidence |
| 4 | Obtain official community/census/electoral geography crosswalk | High | High | Define stable territorial units for later analysis |
| 5 | Extract and verify EV-0103 and EV-0104 | High | Medium-High | Build a traceable inventory of community needs and qualitative claims |
| 6 | Normalize selected EV-0114 validated tables at row level | Medium | Medium | Produce usable official planning indicators with exact page and cell provenance |
| 7 | Design a field-research evidence protocol | High | Medium | Enable future observations and interviews to be classified, dated, and auditable |

## Recommended Next Decision

The Campaign Chief should approve one research-only path:

1. official 2023 results and electoral-geography acquisition;
2. completion of the remaining Wave 1 community sources EV-0103 and EV-0104;
3. canonical-version review of EV-0105 and EV-0106.

No request for segment or territorial-priority approval should be made at this stage.

## Final Gate

**Territorial baseline:** Partial but reviewable  
**Evidence gaps:** Material  
**Territorial prioritization:** Blocked  
**Segment selection:** Blocked  
**Narrative, paid media, and mobilization:** Blocked
