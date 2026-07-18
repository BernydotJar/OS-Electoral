# Daily Operating Workflow

C2-PROD-003 converts approved or research-only internal work into accountable assignments, grounded meeting preparation, follow-up commitments and learning projections.

## Boundary

The workflow is read-only and non-executing. Allowed work types are `RESEARCH`, `REVIEW`, `PREP`, `DOCUMENTATION` and `INTERNAL_COORDINATION`. Publication, spending, paid media, field mobilization, voter targeting and citizen contact are not representable work types.

Political decisions remain in the Approval Inbox and Decision Ledger. An assignment cannot approve its own scope or open a campaign gate.

## Deterministic projections

The workflow receives an explicit `evaluation_date`. Overdue status is derived from that date, due date and assignment status; the engine does not backdate or mutate assignments. Dependency cycles, missing owners, orphan blockers, invalid dates and cross-scope records fail closed.

Meeting preparation requires at least one evidence reference and preserves decision references and critical questions. It does not synthesize unsupported claims.

## Run

```bash
python3 scripts/campaign/validate_c2_prod_003.py

python3 scripts/campaign/run_daily_workflow.py \
  --state fixtures/daily-workflow/antigua.json \
  --output artifacts/daily-workflow/antigua-daily-brief.json
```

The CLI writes only below `artifacts/daily-workflow/`.

## Antigua operator outcome

The initial assignment prepares a governed Candidate Identity Interview. It is internal preparation only, owned by a human research role, grounded in the campaign governance baseline and connected to the pending approval request from C2-PROD-002. No external campaign action is authorized.
