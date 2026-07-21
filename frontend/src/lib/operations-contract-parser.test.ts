import { describe, expect, it } from "vitest";

import {
  parseCampaignRoadmapReadEvidence,
  parseWarRoomSnapshotReadEvidence,
  reconcileWarRoomSnapshot,
} from "@/lib/operations-contract-parser";

const TENANT_ID = "11111111-1111-4111-8111-111111111111";
const CAMPAIGN_ID = "22222222-2222-4222-8222-222222222222";
const ROADMAP_ID = "33333333-3333-4333-8333-333333333333";
const PHASE_ID = "44444444-4444-4444-8444-444444444444";
const WORKSTREAM_ID = "55555555-5555-4555-8555-555555555555";
const TASK_A = "66666666-6666-4666-8666-666666666661";
const TASK_B = "66666666-6666-4666-8666-666666666662";
const TASK_C = "66666666-6666-4666-8666-666666666663";
const DECISION_ID = "77777777-7777-4777-8777-777777777777";

function roadmapFixture() {
  return {
    audit_event_id: "88888888-8888-4888-8888-888888888888",
    roadmap: {
      id: ROADMAP_ID,
      tenant_id: TENANT_ID,
      campaign_id: CAMPAIGN_ID,
      campaign_version: 5,
      campaign_status: "ACTIVE",
      campaign_name: "Campaña sintética Antigua",
      title: "Roadmap de campaña",
      phases: [
        {
          id: PHASE_ID,
          name: "Foundation",
          sequence: 1,
          start_date: "2026-07-21",
          end_date: "2026-08-15",
          status: "ACTIVE",
        },
      ],
      workstreams: [
        {
          id: WORKSTREAM_ID,
          name: "Evidence",
          purpose: "Build verified evidence.",
          accountable_role_id: "99999999-9999-4999-8999-999999999999",
          status: "ACTIVE",
        },
      ],
      milestones: [],
      tasks: [
        {
          id: TASK_A,
          phase_id: PHASE_ID,
          workstream_id: WORKSTREAM_ID,
          milestone_id: null,
          title: "Inventory evidence",
          owner_role_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
          execution_status: "COMPLETE",
          dependency_ids: [],
          due_date: "2026-07-22",
          evidence_refs: ["bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"],
        },
        {
          id: TASK_B,
          phase_id: PHASE_ID,
          workstream_id: WORKSTREAM_ID,
          milestone_id: null,
          title: "Verify biography",
          owner_role_id: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
          execution_status: "PLANNED",
          dependency_ids: [TASK_A],
          due_date: "2026-07-24",
          evidence_refs: [],
        },
        {
          id: TASK_C,
          phase_id: PHASE_ID,
          workstream_id: WORKSTREAM_ID,
          milestone_id: null,
          title: "Prepare human review",
          owner_role_id: "99999999-9999-4999-8999-999999999999",
          execution_status: "PLANNED",
          dependency_ids: [TASK_B],
          due_date: "2026-07-26",
          evidence_refs: [],
        },
      ],
      blockers: [],
      decisions: [
        {
          id: DECISION_ID,
          title: "Confirm biography scope",
          human_role_id: "99999999-9999-4999-8999-999999999999",
          options: ["Narrow internal record", "Request more evidence"],
          due_date: "2026-07-23",
          status: "REQUIRED",
          decision: null,
        },
      ],
      follow_up_items: [],
      learning_notes: [],
      status: "READY_FOR_DAILY_OPERATION",
      execution_order: [TASK_A, TASK_B, TASK_C],
      ready_task_ids: [TASK_B],
      blocked_task_ids: [],
      critical_path_task_ids: [TASK_B, TASK_C],
      open_blocker_count: 0,
      required_decision_count: 1,
      next_action: "MAKE_HUMAN_DECISIONS",
      authority_effect: "NONE",
      external_effects: "NONE",
      limitation_codes: [
        "HUMAN_DECISIONS_REQUIRED",
        "NO_AUTONOMOUS_TASK_EXECUTION",
        "NO_CITIZEN_CONTACT",
        "NO_EXTERNAL_EFFECTS",
      ],
      version: 2,
      created_at: "2026-07-21T23:00:00Z",
      updated_at: "2026-07-21T23:45:00Z",
    },
  };
}

function snapshotFixture() {
  return {
    audit_event_id: "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
    snapshot: {
      id: "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
      tenant_id: TENANT_ID,
      campaign_id: CAMPAIGN_ID,
      roadmap_id: ROADMAP_ID,
      roadmap_version: 2,
      snapshot_date: "2026-07-22",
      priorities: ["Verify biography"],
      ready_task_ids: [TASK_B],
      blocked_task_ids: [],
      required_decision_ids: [DECISION_ID],
      follow_up_notes: ["Human director decision remains required."],
      learning_note_ids: [],
      authority_effect: "NONE",
      external_effects: "NONE",
      created_at: "2026-07-22T08:00:00Z",
    },
  };
}

describe("campaign operations parsers", () => {
  it("accepts a canonical roadmap and reconciled latest snapshot", () => {
    const roadmap = parseCampaignRoadmapReadEvidence(roadmapFixture());
    const snapshot = parseWarRoomSnapshotReadEvidence(snapshotFixture());
    expect(roadmap.roadmap.ready_task_ids).toEqual([TASK_B]);
    expect(roadmap.roadmap.critical_path_task_ids).toEqual([TASK_B, TASK_C]);
    expect(
      reconcileWarRoomSnapshot(roadmap.roadmap, snapshot.snapshot)
        .roadmap_version,
    ).toBe(2);
  });

  it("rejects cycles, unknown references, and completed work before dependencies", () => {
    const cycle = structuredClone(roadmapFixture());
    cycle.roadmap.tasks![0]!.dependency_ids = [TASK_C];
    expect(() => parseCampaignRoadmapReadEvidence(cycle)).toThrow("cycle");

    const unknown = structuredClone(roadmapFixture());
    unknown.roadmap.tasks![1]!.workstream_id =
      "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee";
    expect(() => parseCampaignRoadmapReadEvidence(unknown)).toThrow(
      "unknown workstream",
    );

    const impossibleCompletion = structuredClone(roadmapFixture());
    impossibleCompletion.roadmap.tasks![1]!.execution_status = "COMPLETE";
    impossibleCompletion.roadmap.tasks![0]!.execution_status = "PLANNED";
    expect(() =>
      parseCampaignRoadmapReadEvidence(impossibleCompletion),
    ).toThrow("complete task requires complete dependencies");
  });

  it("rejects contradictory derived views and authority promotion", () => {
    const wrongReady = structuredClone(roadmapFixture());
    wrongReady.roadmap.ready_task_ids = [TASK_C];
    expect(() => parseCampaignRoadmapReadEvidence(wrongReady)).toThrow(
      "ready tasks are inconsistent",
    );

    const wrongCritical = structuredClone(roadmapFixture());
    wrongCritical.roadmap.critical_path_task_ids = [TASK_C];
    expect(() => parseCampaignRoadmapReadEvidence(wrongCritical)).toThrow(
      "critical path is inconsistent",
    );

    const authority = structuredClone(roadmapFixture());
    authority.roadmap.authority_effect = "EXECUTE";
    expect(() => parseCampaignRoadmapReadEvidence(authority)).toThrow();
  });

  it("rejects stale, cross-scope, or contradictory snapshots", () => {
    const roadmap = parseCampaignRoadmapReadEvidence(roadmapFixture()).roadmap;

    const stale = parseWarRoomSnapshotReadEvidence({
      ...snapshotFixture(),
      snapshot: { ...snapshotFixture().snapshot, roadmap_version: 1 },
    }).snapshot;
    expect(() => reconcileWarRoomSnapshot(roadmap, stale)).toThrow(
      "roadmap version",
    );

    const crossCampaign = parseWarRoomSnapshotReadEvidence({
      ...snapshotFixture(),
      snapshot: {
        ...snapshotFixture().snapshot,
        campaign_id: "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
      },
    }).snapshot;
    expect(() => reconcileWarRoomSnapshot(roadmap, crossCampaign)).toThrow(
      "scope mismatch",
    );

    const wrongReady = parseWarRoomSnapshotReadEvidence({
      ...snapshotFixture(),
      snapshot: { ...snapshotFixture().snapshot, ready_task_ids: [TASK_C] },
    }).snapshot;
    expect(() => reconcileWarRoomSnapshot(roadmap, wrongReady)).toThrow(
      "ready tasks contradict roadmap",
    );
  });
});
