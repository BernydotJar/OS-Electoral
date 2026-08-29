# C3-RELEASE-002 — Design

## Decision model

CampaignOS now carries two independent readiness decisions:

```text
Controlled internal use
  -> repository + local runtime evidence
  -> all controlled-use gates PASS
  -> READY_FOR_CONTROLLED_INTERNAL_USE

Production release
  -> managed environments + live identity + resilience + independent reviews
  -> all production gates PASS + human production approval
  -> production may become READY
```

The first decision can be positive while the second remains fail-closed. Neither decision grants political authority or an external-effect capability.

## Evidence contract

`program/controlled-use-readiness.json` is the machine-readable controlled-use record. It binds to the reconciled protected-main baseline, requires an exact gate inventory, and records allowed/prohibited use boundaries plus unresolved production blockers.

`scripts/release/validate_controlled_use_readiness.py` validates the record and is part of `make program-verify`.

## Main reconciliation guard

The architecture validator will expose a small Git helper. When the current checkout branch is exactly `main`, `architecture/program-state.json -> github_state.cumulative_merge.main_sha` must equal `git rev-parse HEAD`. Feature branches and detached PR checkouts are intentionally not forced to equal the baseline SHA.

## Safety boundaries

Controlled use is limited to isolated internal review/training/operator workflows. The development verifier remains development-only. No public dev-auth exposure, production deployment, Firmes sync, citizen-level political data workflow, targeting, persuasion, publication, spend, or mobilization is enabled by this increment.
