# Campaign roadmap and Daily War Room

`C3-OPS-001` adds a campaign-scoped internal coordination system. It orders work and records evidence; it does not create political authority, execute tasks, contact citizens, publish, spend, mobilize, or invoke an external provider.

## Product jobs

The surface is designed for campaign directors and non-technical operators who need to answer:

1. Which phase and workstream owns the current work?
2. Which tasks are ready, blocked, active, or complete?
3. Which dependency chain is currently critical?
4. Which blockers and human decisions need attention?
5. What was the immutable internal War Room view for a specific day?

## Aggregate boundaries

One `CampaignRoadmap` exists per tenant and campaign. It owns:

- ordered phases;
- accountable workstreams;
- milestones;
- dependency-linked tasks;
- blockers;
- human decisions;
- follow-up items;
- learning notes;
- a version used for optimistic concurrency.

`WarRoomSnapshot` is append-only, bound to an exact roadmap version and unique per tenant/campaign/date. It stores the derived ready, blocked and required-decision views together with human-entered priorities and follow-up notes.

## Deterministic operating rules

- Tasks form a directed acyclic graph.
- Every dependency must resolve inside the same roadmap.
- A completed task requires all dependencies to be complete.
- Ready tasks are planned, unblocked, and have complete dependencies.
- Open blockers remove their task from the ready set.
- Every operational owner must be a role already present in the Team Builder aggregate.
- A decision marked `DECIDED` must select one of its declared options.
- Snapshot ready, blocked, decision, and learning references must match the exact roadmap version.
- Roadmap and snapshot always project `authority_effect=NONE` and `external_effects=NONE`.

## Human authority boundary

The roadmap may recommend the next coordination action, but only a human changes task state, resolves blockers, selects a decision option, authorizes contact, approves spending, or performs another campaign action. The dynamic shell intentionally exposes no execution controls in this increment.

## Status model

Roadmap status is derived:

- `SETUP_REQUIRED`: no operational tasks exist;
- `IN_PROGRESS`: work exists but nothing is currently ready or active;
- `READY_FOR_DAILY_OPERATION`: at least one task is ready or active;
- `COMPLETE`: every task is complete and still requires human review.

Next action is derived in this order:

1. resolve open blockers;
2. make required human decisions;
3. start ready tasks;
4. continue active work;
5. review completion;
6. define the roadmap.

## User experience

The ES/EN read-only surface presents:

- roadmap status and next human action;
- ready and blocked counts;
- open blocker and required-decision counts;
- the critical path in execution order;
- ready task names and due dates;
- required human decisions;
- the latest immutable Daily War Room snapshot;
- audit receipts and mandatory limitations.

The UI fails closed for missing authorization, missing roadmap/snapshot, dependency failure, scope mismatch, stale snapshot version, or invalid upstream data.

## Explicitly out of scope

- autonomous task execution;
- strategy generation or approval;
- citizen outreach;
- content publication;
- media activation;
- spending;
- mobilization;
- voter profiling;
- live provider calls;
- merge or deployment;
- production approval.
