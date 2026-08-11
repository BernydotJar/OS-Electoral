# C3-FIRMES-001 - Design

## Architecture

Introduce an external-reference boundary, not a second field-operations system.

`FIRMES -> strict aggregate adapter -> source snapshot -> CampaignOS read model -> evidence/War Room references`

There is no reverse arrow in the baseline.

## Contracts

A snapshot is scoped to one tenant/campaign plus an external territorial scope and includes:

- `source_system = FIRMES`;
- `contract_version`;
- `external_district_id` / `external_municipality_id` and optional community reference;
- aggregate metrics from the approved allow-list;
- `observed_at` and `ingested_at`;
- `freshness = CURRENT | STALE | UNAVAILABLE`;
- provenance metadata without source credentials.

The parser rejects unknown fields so newly exposed FIRMES fields do not silently cross the boundary.

## UI

Use a compact read-only **External operations pulse** inside an appropriate internal CampaignOS surface. It should show:

- source owner (`FIRMES`);
- territorial scope;
- last observed timestamp/freshness;
- a few aggregate progress signals;
- a handoff link for authorized users to continue operational work in FIRMES.

Do not reproduce FIRMES assignment, event, alliance, nuclei or billboard mutation forms.

## Safety and privacy

The adapter does not model a person-level voter/member entity. Prohibited fields are rejected at the contract boundary. Aggregates cannot directly trigger a contact, publication, mobilization or targeting operation.

## Rollout

1. Contract and synthetic fixtures only.
2. Local/demo read model with synthetic aggregate snapshot.
3. Authenticated source transport only after a separate review of the actual supported FIRMES API/export contract and credential model.
4. No production activation without explicit approval.
