# C3-FIRMES-001 - Tasks

Status: `SPEC_READY_APPROVAL_PENDING`

No implementation task may start before explicit Graph Harness approval.

## Proposed implementation tasks

1. Define strict aggregate/reference contracts and prohibited-field adversarial fixtures.
2. Add a read-only source snapshot model with provenance and freshness semantics.
3. Add a transport interface that exposes only `read_snapshot`; no mutation methods.
4. Add synthetic/demo data and parser tests for allowed and rejected payloads.
5. Add exact CampaignOS authorization for reading external operational context.
6. Add a compact ES/EN external-operations pulse with source/freshness labels and FIRMES handoff link.
7. Add browser tests for desktop/mobile, keyboard, reduced motion, accessibility and no unexpected outbound hosts.
8. Add security tests proving no DPI, contact fields, registrant records, active invitation links or external-effect operations are accepted.
9. Run complete repository gates and publish only for review.

## Deferred tasks

- Direct authenticated FIRMES API transport until its supported API/credential contract is independently reviewed.
- Any write-back or bidirectional synchronization.
- Any person-level political/affiliation data integration.
