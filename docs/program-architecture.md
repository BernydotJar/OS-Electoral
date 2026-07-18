# CampaignOS Executable Program Architecture

`architecture/program-state.json` is the machine-readable source of truth for the current C2 program stack. It distinguishes code that exists in draft branches from code merged to `main`, human-blocked release actions, executable next increments and deliberately deferred work.

## Current stack

```text
main
└── #42 C2-PLAT-001 approval binding hardening
    └── #44 C2-PROD-001 Candidate Brand
        └── #46 C2-PROD-002 Approval Inbox and Decision Ledger
            └── #48 C2-PROD-003 Daily Operating Workflow
                └── #50 C2-FRONT-001 Governance Workspace
                    └── #52 C2-SAAS-001A Authorization Policy Boundary
                        └── #54 C2-ARCH-001 Executable Program State
                            └── #56 C2-SAAS-001B Persistence and Audit
                                └── C2-SAAS-001C Repository and Transaction Boundary
```

Every layer is draft, independently validated and blocked from merge or deployment pending human approval.

## Bounded contexts

- Campaign Workspace: governed tenant/campaign/workspace state and strategic gates.
- Candidate Brand: identity, biography, purpose, attributes, evidence and reputation risks.
- Approval Ledger: pending requests plus immutable, hash-chained decision history.
- Daily Operations: internal assignments, meeting preparation, blockers and learning.
- Governance Frontend: display-only projection of brand, approvals and operations.
- Authorization Policy: exact-scope allow/deny decision without authentication or execution.
- Persistence Audit: pure persistence boundary, optimistic concurrency, cryptographic hash chaining and idempotency keys.
- Repository Transaction: tenant-scoped repositories and unit of work context manager for transaction coordination.

## Program-state validation

```bash
python3 scripts/architecture/validate_program_state.py
```

The validator rejects unknown dependencies, dependency cycles, missing code or validators, stack-base drift, missing CI evidence, prohibited-capability drift, unresolved CRITICAL/HIGH findings and any unexpected opening of Antigua tactical gates.

## Current executable next work

The manifest identifies C2-SAAS-001C as implemented. C2-OBS-001 (Audit Observability and Integrity Read Model) or C2-AI-001A (Evidence-grounded extraction and citation contracts) may follow.

Real authentication, billing, deployment, tactical activation and public campaign actions remain deferred or human-blocked.
