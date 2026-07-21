# Approval Inbox and Decision Ledger

C2-PROD-002 separates the mutable operational question “what is pending?” from the append-only record “what was requested and decided?”.

## Core model

- `requests` contain decision context, options, evidence and risk references, required human roles and exact scope.
- `ledger` contains hash-chained events: `REQUESTED`, `APPROVED`, `REJECTED`, `REVOKED` and `EXPIRED`.
- every event repeats tenant, campaign, workspace, request and scope identifiers;
- approval, rejection and revocation require an authorized human role;
- expiration may be proposed by a human or deterministic system process;
- revocation appends an event and never rewrites the original approval;
- transition IDs are unique and replay attempts fail closed.

## No implicit persistence

`propose_transition` returns a proposed ledger event and projected request status. It does not mutate the state, append the event, open a campaign gate or execute the approved option. Persistence remains an explicit future adapter with authorization and audit controls.

## Run

```bash
python3 scripts/campaign/validate_c2_prod_002.py

python3 scripts/campaign/run_approval_ledger.py \
  --state fixtures/approval-ledger/antigua.json \
  --output artifacts/approval-ledger/antigua-inbox.json

python3 scripts/campaign/run_approval_ledger.py \
  --state fixtures/approval-ledger/antigua.json \
  --command fixtures/approval-ledger/antigua-approve-command.json \
  --principal fixtures/approval-ledger/antigua-trusted-principal.json \
  --authorization-request fixtures/approval-ledger/antigua-transition-authorization-request.json \
  --authentication-binding fixtures/approval-ledger/antigua-authenticated-binding.json \
  --output artifacts/approval-ledger/antigua-transition-proposal.json
```

The CLI is read-only and writes only beneath `artifacts/approval-ledger/`. The
authentication binding is deterministic fixture evidence for contract testing;
it is not a login mechanism or production authentication proof. Runtime code
must construct `AuthenticatedPrincipalBinding` only after a real authentication
adapter verifies the external principal and session.

## Antigua safety state

The operator fixture contains one pending decision about whether to conduct a governed Candidate Identity Interview. Approval of that research step does not approve an attribute, positioning, content, publication, spending, paid media, mobilization or citizen contact. `metadata.opens_gate` remains false.

## Integrity controls

The validator rejects hash tampering, broken previous-hash links, duplicate event IDs, replayed transition IDs, request/ledger status drift, cross-purpose events, invalid selected options, unauthorized roles and cross-tenant/campaign/workspace records.
