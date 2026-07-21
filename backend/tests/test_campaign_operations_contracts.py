from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from campaignos.operations.contracts import (
    CampaignRoadmapAssessmentInput,
    CampaignRoadmapContractError,
    CampaignRoadmapCreate,
    CampaignRoadmapUpdate,
    WarRoomSnapshotCreate,
    assess_campaign_roadmap,
    build_war_room_snapshot,
)

TENANT_ID = UUID("11111111-1111-4111-8111-111111111111")
CAMPAIGN_ID = UUID("22222222-2222-4222-8222-222222222222")
ROADMAP_ID = UUID("33333333-3333-4333-8333-333333333333")
DIRECTOR_ID = UUID("44444444-4444-4444-8444-444444444444")
RESEARCH_ID = UUID("55555555-5555-4555-8555-555555555555")
NOW = datetime(2026, 7, 21, 23, 50, tzinfo=UTC)


def _payload() -> dict[str, object]:
    phase_id = UUID("60000000-0000-4000-8000-000000000001")
    workstream_id = UUID("70000000-0000-4000-8000-000000000001")
    task_a = UUID("80000000-0000-4000-8000-000000000001")
    task_b = UUID("80000000-0000-4000-8000-000000000002")
    task_c = UUID("80000000-0000-4000-8000-000000000003")
    return {
        "id": ROADMAP_ID,
        "tenant_id": TENANT_ID,
        "campaign_id": CAMPAIGN_ID,
        "campaign_version": 5,
        "campaign_status": "ACTIVE",
        "campaign_name": "Campaña sintética Antigua",
        "team_role_ids": [DIRECTOR_ID, RESEARCH_ID],
        "phases": [
            {
                "id": phase_id,
                "name": "Foundation",
                "sequence": 1,
                "start_date": "2026-07-21",
                "end_date": "2026-08-15",
                "status": "ACTIVE",
            }
        ],
        "workstreams": [
            {
                "id": workstream_id,
                "name": "Evidence",
                "purpose": "Build verified campaign evidence.",
                "accountable_role_id": DIRECTOR_ID,
                "status": "ACTIVE",
            }
        ],
        "milestones": [
            {
                "id": UUID("90000000-0000-4000-8000-000000000001"),
                "phase_id": phase_id,
                "name": "Evidence baseline",
                "completion_criteria": "Required claims have accepted evidence.",
                "owner_role_id": DIRECTOR_ID,
                "due_date": "2026-08-01",
                "status": "IN_PROGRESS",
            }
        ],
        "tasks": [
            {
                "id": task_a,
                "phase_id": phase_id,
                "workstream_id": workstream_id,
                "milestone_id": None,
                "title": "Inventory current evidence",
                "owner_role_id": RESEARCH_ID,
                "execution_status": "COMPLETE",
                "dependency_ids": [],
                "due_date": "2026-07-22",
                "evidence_refs": [uuid4()],
            },
            {
                "id": task_b,
                "phase_id": phase_id,
                "workstream_id": workstream_id,
                "milestone_id": None,
                "title": "Verify biography",
                "owner_role_id": RESEARCH_ID,
                "execution_status": "PLANNED",
                "dependency_ids": [task_a],
                "due_date": "2026-07-24",
                "evidence_refs": [],
            },
            {
                "id": task_c,
                "phase_id": phase_id,
                "workstream_id": workstream_id,
                "milestone_id": None,
                "title": "Prepare human review",
                "owner_role_id": DIRECTOR_ID,
                "execution_status": "PLANNED",
                "dependency_ids": [task_b],
                "due_date": "2026-07-26",
                "evidence_refs": [],
            },
        ],
        "blockers": [],
        "decisions": [
            {
                "id": UUID("a0000000-0000-4000-8000-000000000001"),
                "title": "Confirm biography scope",
                "human_role_id": DIRECTOR_ID,
                "options": ["Narrow internal record", "Request more evidence"],
                "due_date": "2026-07-23",
                "status": "REQUIRED",
                "decision": None,
            }
        ],
        "follow_up_items": [
            {
                "id": UUID("b0000000-0000-4000-8000-000000000001"),
                "title": "Review missing evidence",
                "owner_role_id": RESEARCH_ID,
                "due_date": "2026-07-23",
                "status": "OPEN",
            }
        ],
        "learning_notes": [
            {
                "id": UUID("c0000000-0000-4000-8000-000000000001"),
                "title": "Evidence discipline",
                "note": "Claims require provenance before human disposition.",
                "evidence_refs": [uuid4()],
            }
        ],
        "version": 2,
        "created_at": NOW,
        "updated_at": NOW,
    }


def test_create_update_and_snapshot_inputs_are_bounded() -> None:
    assert CampaignRoadmapCreate(title="Campaign roadmap").title == "Campaign roadmap"
    update = CampaignRoadmapUpdate.model_validate({"tasks": [], "blockers": []})
    assert update.tasks == ()
    assert update.model_fields_set == {"tasks", "blockers"}
    with pytest.raises(ValidationError, match="at least one field"):
        CampaignRoadmapUpdate.model_validate({})
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        CampaignRoadmapUpdate.model_validate({"autonomous_actions": ["publish"]})
    snapshot = WarRoomSnapshotCreate(
        snapshot_date=date(2026, 7, 22),
        priorities=["Verify biography"],
        follow_up_notes=["Ask the authorized director for a decision."],
    )
    assert snapshot.snapshot_date == date(2026, 7, 22)


def test_dag_derives_ready_work_execution_order_and_critical_path() -> None:
    projection = assess_campaign_roadmap(CampaignRoadmapAssessmentInput.model_validate(_payload()))
    task_a, task_b, task_c = (task.id for task in projection.tasks or ())
    assert projection.execution_order == (task_a, task_b, task_c)
    assert projection.ready_task_ids == (task_b,)
    assert projection.blocked_task_ids == ()
    assert projection.critical_path_task_ids == (task_b, task_c)
    assert projection.next_action == "MAKE_HUMAN_DECISIONS"
    assert projection.authority_effect == "NONE"
    assert projection.external_effects == "NONE"


def test_cycles_self_dependencies_and_unknown_references_fail_closed() -> None:
    cycle = _payload()
    first = cycle["tasks"][0]  # type: ignore[index]
    last = cycle["tasks"][2]  # type: ignore[index]
    first["dependency_ids"] = [last["id"]]
    with pytest.raises(CampaignRoadmapContractError, match="cycle"):
        assess_campaign_roadmap(CampaignRoadmapAssessmentInput.model_validate(cycle))

    self_dependency = _payload()
    task = self_dependency["tasks"][1]  # type: ignore[index]
    task["dependency_ids"] = [task["id"]]
    with pytest.raises(CampaignRoadmapContractError, match="self-dependency"):
        assess_campaign_roadmap(CampaignRoadmapAssessmentInput.model_validate(self_dependency))

    unknown = _payload()
    unknown["tasks"][1]["workstream_id"] = uuid4()  # type: ignore[index]
    with pytest.raises(CampaignRoadmapContractError, match="unknown workstream"):
        assess_campaign_roadmap(CampaignRoadmapAssessmentInput.model_validate(unknown))


def test_every_operational_owner_must_exist_in_team_workspace() -> None:
    for collection, owner_field in (
        ("workstreams", "accountable_role_id"),
        ("milestones", "owner_role_id"),
        ("tasks", "owner_role_id"),
        ("decisions", "human_role_id"),
        ("follow_up_items", "owner_role_id"),
    ):
        payload = _payload()
        payload[collection][0][owner_field] = uuid4()  # type: ignore[index]
        with pytest.raises(CampaignRoadmapContractError, match="unknown team role"):
            assess_campaign_roadmap(CampaignRoadmapAssessmentInput.model_validate(payload))


def test_open_blocker_removes_task_from_ready_work_and_drives_next_action() -> None:
    payload = _payload()
    task_b = payload["tasks"][1]["id"]  # type: ignore[index]
    payload["decisions"][0]["status"] = "DECIDED"  # type: ignore[index]
    payload["decisions"][0]["decision"] = "Request more evidence"  # type: ignore[index]
    payload["blockers"] = [
        {
            "id": uuid4(),
            "task_id": task_b,
            "severity": "HIGH",
            "status": "OPEN",
            "owner_role_id": DIRECTOR_ID,
            "description": "Source authority remains unresolved.",
            "resolution_condition": "Verify the issuing authority.",
        }
    ]
    projection = assess_campaign_roadmap(CampaignRoadmapAssessmentInput.model_validate(payload))
    assert projection.ready_task_ids == ()
    assert projection.blocked_task_ids == (task_b,)
    assert projection.open_blocker_count == 1
    assert projection.next_action == "RESOLVE_BLOCKERS"


def test_decision_requires_selected_option_and_remains_human_owned() -> None:
    invalid = _payload()
    invalid["decisions"][0]["status"] = "DECIDED"  # type: ignore[index]
    with pytest.raises(
        CampaignRoadmapContractError, match="decided item requires a selected option"
    ):
        assess_campaign_roadmap(CampaignRoadmapAssessmentInput.model_validate(invalid))

    unsupported = _payload()
    unsupported["decisions"][0]["status"] = "DECIDED"  # type: ignore[index]
    unsupported["decisions"][0]["decision"] = "Autonomous publication"  # type: ignore[index]
    with pytest.raises(CampaignRoadmapContractError, match="selected option"):
        assess_campaign_roadmap(CampaignRoadmapAssessmentInput.model_validate(unsupported))


def test_daily_snapshot_is_derived_without_mutating_roadmap() -> None:
    projection = assess_campaign_roadmap(CampaignRoadmapAssessmentInput.model_validate(_payload()))
    snapshot = build_war_room_snapshot(
        projection,
        request=WarRoomSnapshotCreate(
            snapshot_date=date(2026, 7, 22),
            priorities=["Verify biography"],
            follow_up_notes=["Human director decision remains required."],
        ),
        snapshot_id=uuid4(),
        created_at=NOW,
    )
    assert snapshot.roadmap_id == ROADMAP_ID
    assert snapshot.roadmap_version == projection.version
    assert snapshot.ready_task_ids == projection.ready_task_ids
    assert snapshot.blocked_task_ids == projection.blocked_task_ids
    assert snapshot.required_decision_ids == tuple(
        item.id for item in projection.decisions or () if item.status == "REQUIRED"
    )
    assert snapshot.authority_effect == "NONE"
    assert snapshot.external_effects == "NONE"
