# C3-FRONT-014 iteration

## Goal

Make the existing evidence-first Strategy domain completable through CampaignOS UI, ending in an explicitly human, internal, version-bound strategy decision with no external effect.

## Graph selection

C3-TEAM-005 is merged to `main@f1dacd9625019664add60b89bff728f3f17d7cc9` and post-merge CampaignOS CI #262 is green. The Team prerequisite is therefore satisfied and C3-FRONT-014 remains the selected Graph Harness node through local review.

## Approval

`USER_EXPLICIT_APPROVAL` from the product-completion instruction. Scope is internal Strategy UI, same-origin API proxy, local development seed, tests and review evidence only. Firmes, production, paid cloud resources, spending and political external effects remain outside this approval.

## Lifecycle

- Producer: complete. Exact Strategy capabilities, typed mutation clients, bounded form parsers, same-origin routes and progressive ES/EN authoring controls are implemented.
- Critic / Red Team: complete. Five findings were recorded, including mutation redirect drift, implicit human selection and a client-navigation blank-body failure.
- Fixer: complete. All findings are repaired without weakening authorization, provenance, reference integrity, concurrency, RLS, decision semantics, accessibility or political-safety boundaries.
- Independent Verifier: complete locally. Frontend, backend, marked PostgreSQL, functional browser, read-only browser, supply-chain, Gitleaks, Compose, Terraform, security, program, release, eval and safety gates pass.
- Release Gate: review-branch publication is eligible; production remains `BLOCKED` and global release remains `DENY_RELEASE`.
- Persistent Evidence: `docs/testing/c3-front-014-evidence.md`, `program/validations/c3-front-014.json`, `progress/review_C3-FRONT-014.md`.
- Hosted exact-head: pending branch freeze, push and CI inspection.

## Functional result

The real PostgreSQL/API/browser journey reaches Candidate `INTERNALLY_APPROVED`, Team `READY_FOR_HUMAN_REVIEW`, Strategy `READY_FOR_HUMAN_DECISION`, and finally `DECIDED_INTERNAL`. The current-version decision persists after reload and cannot be submitted a second time from the UI.

## Deployment constraint discovered in the current session

The user requires a stable URL for the full product at strict cost `$0`. Firebase Hosting on Spark can host static content, but the existing server stack cannot be moved to Firebase App Hosting, Cloud Run or Functions without Cloud Billing/Blaze. No paid-cloud or production action is authorized by C3-FRONT-014; the zero-cost persistent full-product hosting question remains a separate platform/product-delivery constraint to evaluate after the active product node is integrated.
