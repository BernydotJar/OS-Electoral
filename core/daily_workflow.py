#!/usr/bin/env python3
"""Deterministic, read-only Daily Operating Workflow."""
from __future__ import annotations
import copy, datetime as dt, json, re
from typing import Any

SCHEMA_VERSION="1.0"
SAFE_ID=re.compile(r"^[a-z][a-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9._-]*$")
WORK_TYPES={"RESEARCH","REVIEW","PREP","DOCUMENTATION","INTERNAL_COORDINATION"}
STATUSES={"TODO","IN_PROGRESS","BLOCKED","DONE","CANCELLED"}

class DailyWorkflowValidationError(ValueError): pass

def _require(condition:bool,message:str)->None:
    if not condition: raise DailyWorkflowValidationError(message)

def _scope(item:dict[str,Any],state:dict[str,Any],label:str)->None:
    for field in ("tenant_id","campaign_id","workspace_id"):
        _require(item.get(field)==state[field],f"cross-scope {label}: {item.get('id')} ({field})")

def _date(value:str,label:str)->dt.date:
    try: return dt.date.fromisoformat(value)
    except Exception as exc: raise DailyWorkflowValidationError(f"invalid {label}: {value}") from exc

def validate_daily_workflow(state:dict[str,Any])->dict[str,Any]:
    required={"schema_version","workflow_id","tenant_id","campaign_id","workspace_id","evaluation_date","people","assignments","blockers","meetings","commitments","events","learning_records","metadata"}
    _require(isinstance(state,dict) and set(state)==required,"daily workflow fields mismatch")
    _require(state["schema_version"]==SCHEMA_VERSION,"unsupported daily workflow schema version")
    _date(state["evaluation_date"],"evaluation_date")
    for field in ("workflow_id","tenant_id","campaign_id","workspace_id"):
        _require(isinstance(state[field],str) and SAFE_ID.fullmatch(state[field]) is not None,f"invalid stable ID: {field}")
    ids=set(); people=set()
    for person in state["people"]:
        _scope(person,state,"person")
        _require(SAFE_ID.fullmatch(person["id"]) is not None and person["id"] not in ids,"invalid or duplicate person")
        ids.add(person["id"]); people.add(person["id"])
        _require(person.get("actor_type")=="HUMAN","workflow owner must be human")
    assignment_ids=set()
    for assignment in state["assignments"]:
        _scope(assignment,state,"assignment")
        _require(SAFE_ID.fullmatch(assignment["id"]) is not None and assignment["id"] not in ids,"invalid or duplicate assignment")
        ids.add(assignment["id"]); assignment_ids.add(assignment["id"])
        _require(assignment.get("work_type") in WORK_TYPES,f"unsafe work type: {assignment.get('id')}")
        _require(assignment.get("status") in STATUSES,f"invalid assignment status: {assignment.get('id')}")
        _require(assignment.get("owner_ref") in people,f"orphan assignment owner: {assignment.get('id')}")
        _date(assignment["due_date"],"due_date")
        _require(isinstance(assignment.get("dependency_refs"),list) and isinstance(assignment.get("blocker_refs"),list),"assignment refs must be lists")
    for assignment in state["assignments"]:
        for ref in assignment["dependency_refs"]: _require(ref in assignment_ids,f"unknown assignment dependency: {ref}")
    graph={item["id"]:item["dependency_refs"] for item in state["assignments"]}; visiting=set(); complete=set()
    def walk(node:str)->None:
        _require(node not in visiting,f"assignment dependency cycle: {node}")
        if node in complete: return
        visiting.add(node)
        for child in graph[node]: walk(child)
        visiting.remove(node); complete.add(node)
    for node in graph: walk(node)
    blocker_ids=set()
    for blocker in state["blockers"]:
        _scope(blocker,state,"blocker")
        _require(blocker["id"] not in ids,"duplicate blocker ID")
        ids.add(blocker["id"]); blocker_ids.add(blocker["id"])
        _require(blocker.get("assignment_ref") in assignment_ids,f"orphan blocker assignment: {blocker.get('id')}")
    for assignment in state["assignments"]:
        for ref in assignment["blocker_refs"]: _require(ref in blocker_ids,f"unknown blocker: {ref}")
    for meeting in state["meetings"]:
        _scope(meeting,state,"meeting")
        _require(meeting["id"] not in ids,"duplicate meeting ID"); ids.add(meeting["id"])
        _require(isinstance(meeting.get("evidence_refs"),list) and meeting["evidence_refs"],f"meeting prep requires evidence: {meeting.get('id')}")
        _require(isinstance(meeting.get("decision_refs"),list),f"meeting decision_refs must be list: {meeting.get('id')}")
    for commitment in state["commitments"]:
        _scope(commitment,state,"commitment")
        _require(commitment["id"] not in ids,"duplicate commitment ID"); ids.add(commitment["id"])
        _require(commitment.get("owner_ref") in people,f"orphan commitment owner: {commitment.get('id')}")
        _date(commitment["due_date"],"commitment due_date")
    for record in [*state["events"],*state["learning_records"]]:
        _scope(record,state,"history record")
        _require(record["id"] not in ids,"duplicate history ID"); ids.add(record["id"])
    return state

def build_daily_operating_brief(state:dict[str,Any])->dict[str,Any]:
    before=copy.deepcopy(state); validate_daily_workflow(state); today=_date(state["evaluation_date"],"evaluation_date")
    assignments=[]
    for item in state["assignments"]:
        overdue=item["status"] not in {"DONE","CANCELLED"} and _date(item["due_date"],"due_date")<today
        assignments.append({"id":item["id"],"title":item["title"],"owner_ref":item["owner_ref"],"status":item["status"],"due_date":item["due_date"],"overdue":overdue,"blocked":bool(item["blocker_refs"]),"dependency_refs":item["dependency_refs"],"evidence_refs":item.get("evidence_refs",[])})
    result={
        "schema_version":SCHEMA_VERSION,"tenant_id":state["tenant_id"],"campaign_id":state["campaign_id"],"workspace_id":state["workspace_id"],"workflow_id":state["workflow_id"],"evaluation_date":state["evaluation_date"],
        "assignments":assignments,
        "kpis":{"total":len(assignments),"done":sum(item["status"]=="DONE" for item in assignments),"blocked":sum(item["blocked"] for item in assignments),"overdue":sum(item["overdue"] for item in assignments)},
        "meeting_preparation":[{"id":item["id"],"title":item["title"],"evidence_refs":item["evidence_refs"],"decision_refs":item["decision_refs"],"questions":item["questions"]} for item in state["meetings"]],
        "commitments":[{"id":item["id"],"owner_ref":item["owner_ref"],"due_date":item["due_date"],"status":item["status"]} for item in state["commitments"]],
        "learning_records":state["learning_records"],"external_effects":"NONE",
        "warnings":["Assignments are internal and non-executing.","Political decisions remain in the Approval Inbox.","No publication, spending, targeting, mobilization or citizen contact is authorized."]
    }
    _require(state==before,"daily workflow mutated input")
    return result

def pretty(value:Any)->str: return json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
