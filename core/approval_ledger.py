#!/usr/bin/env python3
"""Append-only Approval Inbox and Decision Ledger domain core."""
from __future__ import annotations
import copy, hashlib, json, re
from typing import Any

SCHEMA_VERSION="1.0"
SAFE_ID=re.compile(r"^[a-z][a-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9._-]*$")
REQUEST_STATUSES={"PENDING","APPROVED","REJECTED","REVOKED","EXPIRED"}
EVENT_TYPES={"REQUESTED","APPROVED","REJECTED","REVOKED","EXPIRED"}
TRANSITIONS={"APPROVE":"APPROVED","REJECT":"REJECTED","REVOKE":"REVOKED","EXPIRE":"EXPIRED"}
SCOPE_TYPES={"GATE","BRAND_SECTION","DECISION"}
HUMAN_EVENTS={"APPROVED","REJECTED","REVOKED"}

class ApprovalLedgerValidationError(ValueError): pass

def _require(condition:bool,message:str)->None:
    if not condition: raise ApprovalLedgerValidationError(message)

def canonical_json(value:Any)->str: return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def digest(value:Any)->str: return hashlib.sha256(canonical_json(value).encode()).hexdigest()
def _entry_hash(entry:dict[str,Any])->str: return digest({k:v for k,v in entry.items() if k!="entry_hash"})

def _scope(record:dict[str,Any],state:dict[str,Any],label:str)->None:
    for field in ("tenant_id","campaign_id","workspace_id"):
        _require(record.get(field)==state[field],f"cross-scope {label}: {record.get('id')} ({field})")

def validate_approval_state(state:dict[str,Any])->dict[str,Any]:
    required={"schema_version","inbox_id","tenant_id","campaign_id","workspace_id","requests","ledger","metadata"}
    _require(isinstance(state,dict) and set(state)==required,f"approval state fields mismatch: expected {sorted(required)}")
    _require(state["schema_version"]==SCHEMA_VERSION,"unsupported approval ledger schema version")
    for field in ("inbox_id","tenant_id","campaign_id","workspace_id"):
        _require(isinstance(state[field],str) and SAFE_ID.fullmatch(state[field]) is not None,f"invalid stable ID: {field}")
    _require(isinstance(state["requests"],list) and isinstance(state["ledger"],list),"requests and ledger must be lists")
    request_ids=set(); request_by_id={}
    for request in state["requests"]:
        required_fields={"id","status","title","scope_type","scope_id","required_roles","evidence_refs","risk_refs","options","recommendation","created_at","owner","source_or_provenance","tenant_id","campaign_id","workspace_id"}
        _require(required_fields<=set(request),f"approval request missing fields: {request.get('id')}")
        _require(SAFE_ID.fullmatch(request["id"]) is not None and request["id"] not in request_ids,f"invalid or duplicate approval request ID: {request['id']}")
        request_ids.add(request["id"]); request_by_id[request["id"]]=request; _scope(request,state,"approval request")
        _require(request["status"] in REQUEST_STATUSES,f"invalid approval request status: {request['id']}")
        _require(request["scope_type"] in SCOPE_TYPES and SAFE_ID.fullmatch(request["scope_id"]) is not None,f"invalid approval scope: {request['id']}")
        _require(isinstance(request["required_roles"],list) and request["required_roles"] and len(request["required_roles"])==len(set(request["required_roles"])),f"required roles must be unique: {request['id']}")
        _require(isinstance(request["options"],list) and len(request["options"])>=2,f"approval request requires at least two options: {request['id']}")
        option_ids=[item.get("id") for item in request["options"]]
        _require(all(isinstance(item,str) and SAFE_ID.fullmatch(item) is not None for item in option_ids) and len(option_ids)==len(set(option_ids)),f"invalid or duplicate option IDs: {request['id']}")
        _require(request["recommendation"] is None or request["recommendation"] in option_ids,f"recommendation must reference an option: {request['id']}")
    previous="GENESIS"; event_ids=set(); transition_ids=set(); last_status={}
    for entry in state["ledger"]:
        fields={"id","transition_id","event_type","request_ref","actor_type","actor_id","role","scope_type","scope_id","selected_option_ref","occurred_at","reason","previous_hash","entry_hash","tenant_id","campaign_id","workspace_id"}
        _require(fields<=set(entry),f"ledger entry missing fields: {entry.get('id')}")
        _require(entry["id"] not in event_ids,f"duplicate ledger event ID: {entry['id']}")
        _require(entry["transition_id"] not in transition_ids,f"replayed transition ID: {entry['transition_id']}")
        event_ids.add(entry["id"]); transition_ids.add(entry["transition_id"]); _scope(entry,state,"ledger entry")
        _require(entry["request_ref"] in request_by_id,f"unknown request reference: {entry['id']}")
        request=request_by_id[entry["request_ref"]]
        _require(entry["event_type"] in EVENT_TYPES,f"invalid event type: {entry['id']}")
        _require(entry["scope_type"]==request["scope_type"] and entry["scope_id"]==request["scope_id"],f"cross-purpose ledger event: {entry['id']}")
        _require(entry["previous_hash"]==previous,f"ledger hash chain broken at {entry['id']}")
        _require(entry["entry_hash"]==_entry_hash(entry),f"ledger entry hash mismatch: {entry['id']}")
        if entry["event_type"] in HUMAN_EVENTS:
            _require(entry["actor_type"]=="HUMAN",f"human decision event requires human actor: {entry['id']}")
            _require(entry["role"] in request["required_roles"],f"unauthorized decision role: {entry['id']}")
        if entry["event_type"]=="APPROVED":
            _require(entry["selected_option_ref"] in {item["id"] for item in request["options"]},f"approved event requires valid selected option: {entry['id']}")
        else: _require(entry["selected_option_ref"] is None,f"selected option only allowed for approval: {entry['id']}")
        prior=last_status.get(request["id"])
        if entry["event_type"]=="REQUESTED": _require(prior is None,f"duplicate requested event: {entry['id']}"); last_status[request["id"]]="PENDING"
        elif entry["event_type"] in {"APPROVED","REJECTED","EXPIRED"}: _require(prior=="PENDING",f"invalid transition from {prior}: {entry['id']}"); last_status[request["id"]]=entry["event_type"]
        else: _require(prior=="APPROVED",f"only approved decision can be revoked: {entry['id']}"); last_status[request["id"]]="REVOKED"
        previous=entry["entry_hash"]
    for request in state["requests"]:
        _require(request["status"]==last_status.get(request["id"],"PENDING"),f"request status disagrees with ledger: {request['id']}")
    return state

def project_inbox(state:dict[str,Any])->dict[str,Any]:
    validate_approval_state(state); pending=[item for item in state["requests"] if item["status"]=="PENDING"]
    return {"schema_version":SCHEMA_VERSION,"tenant_id":state["tenant_id"],"campaign_id":state["campaign_id"],"workspace_id":state["workspace_id"],"inbox_id":state["inbox_id"],"pending_count":len(pending),"requests":[{"id":item["id"],"title":item["title"],"scope_type":item["scope_type"],"scope_id":item["scope_id"],"required_roles":item["required_roles"],"evidence_refs":item["evidence_refs"],"risk_refs":item["risk_refs"],"options":item["options"],"recommendation":item["recommendation"],"status":item["status"]} for item in pending],"external_effects":"NONE","warnings":["Inbox projection does not constitute approval.","Only an authorized human transition can append a decision event."]}

def propose_transition(state:dict[str,Any],command:dict[str,Any])->dict[str,Any]:
    before=copy.deepcopy(state); validate_approval_state(state)
    allowed={"schema_version","transition_id","request_ref","action","actor_type","actor_id","role","selected_option_ref","occurred_at","reason","tenant_id","campaign_id","workspace_id"}
    _require(isinstance(command,dict) and set(command)==allowed,"transition command fields mismatch")
    _require(command["schema_version"]==SCHEMA_VERSION,"unsupported transition schema version")
    for field in ("tenant_id","campaign_id","workspace_id"): _require(command[field]==state[field],f"transition {field} mismatch")
    _require(command["action"] in TRANSITIONS,"unsupported transition action")
    request=next((item for item in state["requests"] if item["id"]==command["request_ref"]),None)
    _require(request is not None,"unknown or cross-scope approval request")
    _require(command["actor_type"]=="HUMAN" if command["action"]!="EXPIRE" else command["actor_type"] in {"HUMAN","SYSTEM"},"decision transition requires authorized human actor")
    if command["action"]!="EXPIRE": _require(command["role"] in request["required_roles"],"unauthorized transition role")
    _require(command["transition_id"] not in {entry["transition_id"] for entry in state["ledger"]},"transition replay rejected")
    current=request["status"]
    if command["action"] in {"APPROVE","REJECT","EXPIRE"}: _require(current=="PENDING",f"cannot {command['action'].lower()} request in {current}")
    else: _require(current=="APPROVED","only approved request can be revoked")
    if command["action"]=="APPROVE": _require(command["selected_option_ref"] in {item["id"] for item in request["options"]},"approval requires valid selected option")
    else: _require(command["selected_option_ref"] is None,"selected option only allowed for approval")
    entry={"id":f"ledger-event:{command['transition_id'].split(':',1)[-1]}","transition_id":command["transition_id"],"event_type":TRANSITIONS[command["action"]],"request_ref":request["id"],"actor_type":command["actor_type"],"actor_id":command["actor_id"],"role":command["role"],"scope_type":request["scope_type"],"scope_id":request["scope_id"],"selected_option_ref":command["selected_option_ref"],"occurred_at":command["occurred_at"],"reason":command["reason"],"previous_hash":state["ledger"][-1]["entry_hash"] if state["ledger"] else "GENESIS","tenant_id":state["tenant_id"],"campaign_id":state["campaign_id"],"workspace_id":state["workspace_id"]}
    entry["entry_hash"]=_entry_hash(entry)
    result={"schema_version":SCHEMA_VERSION,"transition_id":command["transition_id"],"request_ref":request["id"],"current_status":current,"projected_status":TRANSITIONS[command["action"]],"proposed_ledger_entry":entry,"persistence_required":True,"external_effects":"NONE","warning":"This proposal does not mutate the ledger or execute the approved action."}
    _require(state==before,"transition proposal mutated approval state")
    return result
