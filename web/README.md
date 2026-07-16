# Evidence Control Room

Static, dependency-free frontend for the OS Electoral evidence baseline.

## Purpose

The interface exposes a read-only operational view of:

- verified electoral metrics;
- evidence class and source identifiers;
- workstream status;
- political gates;
- unresolved blockers;
- preliminary-versus-definitive reconciliation boundaries.

It is not a campaign activation interface. It does not select segments, rank territories, produce political messaging, configure paid-media audiences, target voters, or activate field mobilization.

## Run locally

From the repository root:

```bash
python3 -m http.server 4173 --directory web
```

Then open:

```text
http://localhost:4173
```

A local HTTP server is required because the app loads `data/status.json` with `fetch`.

## Validate

```bash
python3 scripts/frontend/validate_evidence_control_room.py
```

The validator checks:

- required frontend files;
- status snapshot schema;
- official values already accepted by the evidence program;
- preliminary and derived classification boundaries;
- reconciliation arithmetic;
- all political gates remain represented as closed;
- prohibited activation concepts are listed in the safety policy;
- no voter-level records or personal filesystem paths are present.

## Data update policy

`web/data/status.json` is a curated frontend snapshot, not a new evidence source.

When updating it:

1. read the current program-status and evidence-register artifacts;
2. update only values already accepted in repository evidence;
3. retain source IDs and evidence classes;
4. never convert `PRELIMINARY` or `DERIVED` values to `OFFICIAL` without a recorded gate decision;
5. run the validator;
6. document the source commit or PR in the update.

## Deployment

The app can be served by any static hosting provider. No runtime secrets, API keys, database, authentication, analytics, cookies, or third-party scripts are required for this first increment.
