# Team role operations board

## Product intent

The role directory answers who the campaign needs. The operations board answers what requires attention now, what outcome is expected, what blocks progress and what evidence proves completion.

```yaml
design_variance: 7
motion_intensity: 3
visual_density: 6
```

The surface prioritizes operating signal over decoration. It uses one compact pulse, explicit filters and four status columns. Role dossiers are progressive disclosures beneath the operational layer.

## Information hierarchy

1. operating pulse: planned, active, blocked, complete and attention;
2. create planned follow-up;
3. status board and check-ins;
4. role workload and attention summaries;
5. expanded job descriptions, consulting dossiers, training and access review.

## Interaction contract

- pulse controls filter the same authoritative work collection;
- attention includes blocked, at-risk and off-track work across statuses;
- role and state filters may be combined;
- evidence, RACI and check-in history are available through keyboard-operable disclosures;
- status/health changes use a separate explicit form;
- active/blocked/complete options are disabled while executing functions remain vacant;
- mobile reflows pulse, forms, filters, columns and role cards to one column;
- no drag-and-drop is required for keyboard parity or persistence correctness.

## UX states

- empty: explains how to create the first follow-up;
- partial: planned work may exist before human role coverage;
- success: persisted card, current version and notice are visible;
- validation error: inconsistent blocker, health, date or note fails closed;
- authorization denied: all mutation controls are absent or rejected server-side;
- conflict: stale version or duplicate follow-up requires reload/review;
- degraded dependency: no partial write is claimed;
- read-only: board and evidence remain visible without forms;
- reduced motion: filtering changes immediately; no meaning depends on movement.

## Safety and authority

The board measures work-state visibility, not people. It does not calculate productivity, rank personnel, infer political preferences or treat role labels as grants. Planning against a vacancy is allowed; claiming active execution without a filled human role is not.
