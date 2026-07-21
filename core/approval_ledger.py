#!/usr/bin/env python3
"""Append-only Approval Inbox and Decision Ledger domain core."""
from __future__ import annotations
import copy, datetime as dt, hashlib, json, re
from dataclasses import dataclass
from typing import Any

from core.authorization_policy import AuthorizationPolicyError, authorize, validate_principal_context

SCHEMA_VERSION="1.0"
SAFE_ID=re.compile(r"^[a-z][a-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9._-]*$")
REQUEST_STATUSES={"PENDING","APPROVED","REJECTED","REVOKED","EXPIRED"}
EVENT_TYPES={"REQUESTED","APPROVED","REJECTED","REVOKED","EXPIRED"}
TRANSITIONS={"APPROVE":"APPROVED","REJECT":"REJECTED","REVOKE":"REVOKED","EXPIRE":"EXPIRED"}
SCOPE_TYPES={"GATE","BRAND_SECTION","DECISION"}
HUMAN_EVENTS={"APPROVED","REJECTED","REVOKED"}
TRUSTED_AUTHENTICATION_SOURCES={"OIDC_VERIFIED_SESSION","INTERNAL_SERVICE_IDENTITY"}
TRANSITION_PERMISSION="PROPOSE_TRANSITION"
TRANSITION_RESOURCE_TYPE="APPROVAL_REQUEST"
GENERIC_AUTHORIZATION_FIELDS={"schema_version","request_id","principal_id","tenant_id","campaign_id","workspace_id","permission","resource_type","resource_id","evaluation_date"}
TRANSITION_AUTHORIZATION_FIELDS=GENERIC_AUTHORIZATION_FIELDS|{"transition_action","selected_option_ref","transition_payload_digest"}
AUTHORIZATION_BINDING_FIELDS={"authorization_request_id","authentication_session_id","authentication_evidence_id","authorization_grant_refs","authorization_payload_digest","trust_source"}

class ApprovalLedgerValidationError(ValueError): pass

@dataclass(frozen=True,slots=True)
class AuthenticatedPrincipalBinding:
    """Immutable output of an authentication adapter, separate from client data."""

    principal_id:str
    actor_type:str
    authentication_session_id:str
    authentication_evidence_id:str
    trust_source:str

    def __post_init__(self)->None:
        _require(isinstance(self.principal_id,str) and SAFE_ID.fullmatch(self.principal_id) is not None,"invalid authenticated principal_id")
        _require(self.actor_type in {"HUMAN","AGENT","SYSTEM"},"invalid authenticated actor_type")
        _require(_actor_prefix_matches(self.actor_type,self.principal_id),"authenticated actor identity mismatch")
        _require(isinstance(self.authentication_session_id,str) and self.authentication_session_id.startswith("session:") and SAFE_ID.fullmatch(self.authentication_session_id) is not None,"verified session_id is required")
        _require(isinstance(self.authentication_evidence_id,str) and self.authentication_evidence_id.startswith("authn-evidence:") and SAFE_ID.fullmatch(self.authentication_evidence_id) is not None,"authentication evidence binding is required")
        _require(self.trust_source in TRUSTED_AUTHENTICATION_SOURCES,"principal trust source is not accepted")

def _require(condition:bool,message:str)->None:
    if not condition: raise ApprovalLedgerValidationError(message)

def canonical_json(value:Any)->str: return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def digest(value:Any)->str: return hashlib.sha256(canonical_json(value).encode()).hexdigest()
def _entry_hash(entry:dict[str,Any])->str: return digest({k:v for k,v in entry.items() if k!="entry_hash"})

def transition_authorization_digest(state:dict[str,Any],request:dict[str,Any],command:dict[str,Any])->str:
    """Bind authorization to the exact action, option, reason, date and target version."""
    return digest({
        "action":command.get("action"),
        "request_ref":command.get("request_ref"),
        "selected_option_ref":command.get("selected_option_ref"),
        "occurred_at":command.get("occurred_at"),
        "reason":command.get("reason"),
        "scope":{field:state.get(field) for field in ("tenant_id","campaign_id","workspace_id")},
        "target_request_digest":digest(request),
    })

def _scope(record:dict[str,Any],state:dict[str,Any],label:str)->None:
    for field in ("tenant_id","campaign_id","workspace_id"):
        _require(record.get(field)==state[field],f"cross-scope {label}: {record.get('id')} ({field})")

def _date(value:Any,label:str)->None:
    _require(isinstance(value,str) and value.strip(),f"{label} is required")
    try: dt.date.fromisoformat(value)
    except ValueError as exc: raise ApprovalLedgerValidationError(f"invalid {label}: {value}") from exc

def _actor_prefix_matches(actor_type:str,actor_id:str)->bool:
    return actor_id.startswith({"HUMAN":"human:","AGENT":"agent:","SYSTEM":"system:"}.get(actor_type,"invalid:"))

def _role_key(role_id:str)->str:
    _require(role_id.startswith("role:"),f"role_id namespace mismatch: {role_id}")
    return role_id.split(":",1)[1].replace("-","_")

def _trusted_transition_actor(
    state:dict[str,Any],
    request:dict[str,Any],
    command:dict[str,Any],
    principal_context:dict[str,Any] | None,
    authorization_request:dict[str,Any] | None,
    authenticated_principal:AuthenticatedPrincipalBinding | None,
)->dict[str,Any]:
    _require(isinstance(principal_context,dict),"trusted principal context is required")
    _require(isinstance(authorization_request,dict),"authorization request is required")
    _require(isinstance(authenticated_principal,AuthenticatedPrincipalBinding),"authenticated principal binding is required")
    try: validate_principal_context(principal_context)
    except AuthorizationPolicyError as exc: raise ApprovalLedgerValidationError(f"invalid principal context: {exc}") from exc
    _require(set(authorization_request)==TRANSITION_AUTHORIZATION_FIELDS,"transition authorization request fields mismatch")
    _require(authenticated_principal.principal_id==principal_context["principal_id"],"authenticated principal mismatch")
    _require(authenticated_principal.actor_type==principal_context["actor_type"],"authenticated actor type mismatch")

    for field in ("tenant_id","campaign_id","workspace_id"):
        _require(authorization_request.get(field)==state[field],f"authorization request {field} mismatch")
    _require(authorization_request.get("principal_id")==principal_context["principal_id"],"authorization principal mismatch")
    _require(authorization_request.get("permission")==TRANSITION_PERMISSION,"transition authorization permission mismatch")
    _require(authorization_request.get("resource_type")==TRANSITION_RESOURCE_TYPE,"transition authorization resource type mismatch")
    _require(authorization_request.get("resource_id")==request["id"],"transition authorization resource mismatch")
    _require(authorization_request.get("evaluation_date")==command["occurred_at"],"authorization evaluation date must match transition date")
    _require(authorization_request.get("transition_action")==command["action"],"transition authorization action mismatch")
    _require(authorization_request.get("selected_option_ref")==command["selected_option_ref"],"transition authorization option mismatch")
    expected_payload_digest=transition_authorization_digest(state,request,command)
    _require(authorization_request.get("transition_payload_digest")==expected_payload_digest,"transition authorization payload mismatch")
    base_authorization_request={field:authorization_request[field] for field in GENERIC_AUTHORIZATION_FIELDS}
    try: decision=authorize(principal_context,base_authorization_request)
    except AuthorizationPolicyError as exc: raise ApprovalLedgerValidationError(f"authorization evaluation failed: {exc}") from exc
    _require(decision["decision"]=="ALLOW","transition authorization denied")

    matching_ids=set(decision["matching_grants"])
    matching_grants=[grant for grant in principal_context["grants"] if grant["id"] in matching_ids]
    _require(matching_grants,"transition requires an exact active grant")
    actor_type=principal_context["actor_type"]
    if command["action"]!="EXPIRE":
        _require(actor_type=="HUMAN","decision transition requires authenticated human actor")
        roles={_role_key(grant["role_id"]) for grant in matching_grants}
        eligible=roles & set(request["required_roles"])
        _require(len(eligible)==1,"trusted principal lacks one unambiguous required role")
        role=next(iter(eligible))
    else:
        _require(actor_type in {"HUMAN","SYSTEM"},"expiration requires authenticated human or system actor")
        roles=sorted({_role_key(grant["role_id"]) for grant in matching_grants})
        _require(len(roles)==1,"trusted expiration principal role is ambiguous")
        role=roles[0]

    # These untrusted command fields are compatibility assertions only.  The
    # actor and role written to the ledger are derived from trusted inputs.
    _require(command["actor_type"]==actor_type,"command actor_type assertion mismatch")
    _require(command["actor_id"]==principal_context["principal_id"],"command actor_id assertion mismatch")
    _require(command["role"]==role,"command role assertion mismatch")
    return {
        "actor_type":actor_type,
        "actor_id":principal_context["principal_id"],
        "role":role,
        "authorization_request_id":decision["request_id"],
        "authentication_session_id":authenticated_principal.authentication_session_id,
        "authentication_evidence_id":authenticated_principal.authentication_evidence_id,
        "authorization_grant_refs":sorted(matching_ids),
        "authorization_payload_digest":expected_payload_digest,
        "trust_source":authenticated_principal.trust_source,
    }

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
        _require(SAFE_ID.fullmatch(entry["id"]) is not None and SAFE_ID.fullmatch(entry["transition_id"]) is not None,f"invalid ledger event identity: {entry.get('id')}")
        _require(entry.get("actor_type") in {"HUMAN","AGENT","SYSTEM"},f"invalid ledger actor type: {entry['id']}")
        _require(isinstance(entry.get("actor_id"),str) and SAFE_ID.fullmatch(entry["actor_id"]) is not None and _actor_prefix_matches(entry["actor_type"],entry["actor_id"]),f"ledger actor identity mismatch: {entry['id']}")
        _require(isinstance(entry.get("role"),str) and entry["role"].strip(),f"ledger role required: {entry['id']}")
        _date(entry.get("occurred_at"),f"occurred_at for {entry['id']}")
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
        if entry["event_type"]!="REQUESTED":
            _require(AUTHORIZATION_BINDING_FIELDS<=set(entry),f"transition lacks trusted authorization binding: {entry['id']}")
            _require(isinstance(entry["authorization_request_id"],str) and SAFE_ID.fullmatch(entry["authorization_request_id"]) is not None,f"invalid authorization request binding: {entry['id']}")
            _require(isinstance(entry["authentication_session_id"],str) and entry["authentication_session_id"].startswith("session:") and SAFE_ID.fullmatch(entry["authentication_session_id"]) is not None,f"invalid authentication session binding: {entry['id']}")
            _require(isinstance(entry["authentication_evidence_id"],str) and entry["authentication_evidence_id"].startswith("authn-evidence:") and SAFE_ID.fullmatch(entry["authentication_evidence_id"]) is not None,f"invalid authentication evidence binding: {entry['id']}")
            _require(isinstance(entry["authorization_grant_refs"],list) and entry["authorization_grant_refs"],f"authorization grant binding required: {entry['id']}")
            _require(isinstance(entry["authorization_payload_digest"],str) and re.fullmatch(r"[0-9a-f]{64}",entry["authorization_payload_digest"]) is not None,f"invalid authorization payload digest: {entry['id']}")
            _require(entry["trust_source"] in TRUSTED_AUTHENTICATION_SOURCES,f"invalid transition trust source: {entry['id']}")
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
    return {"schema_version":SCHEMA_VERSION,"tenant_id":state["tenant_id"],"campaign_id":state["campaign_id"],"workspace_id":state["workspace_id"],"inbox_id":state["inbox_id"],"pending_count":len(pending),"requests":[{"id":item["id"],"title":item["title"],"scope_type":item["scope_type"],"scope_id":item["scope_id"],"required_roles":copy.deepcopy(item["required_roles"]),"evidence_refs":copy.deepcopy(item["evidence_refs"]),"risk_refs":copy.deepcopy(item["risk_refs"]),"options":copy.deepcopy(item["options"]),"recommendation":item["recommendation"],"status":item["status"]} for item in pending],"external_effects":"NONE","warnings":["Inbox projection does not constitute approval.","Only an authorized human transition can append a decision event."]}

def propose_transition(
    state:dict[str,Any],
    command:dict[str,Any],
    *,
    principal_context:dict[str,Any] | None=None,
    authorization_request:dict[str,Any] | None=None,
    authenticated_principal:AuthenticatedPrincipalBinding | None=None,
)->dict[str,Any]:
    before=copy.deepcopy(state); validate_approval_state(state)
    allowed={"schema_version","transition_id","request_ref","action","actor_type","actor_id","role","selected_option_ref","occurred_at","reason","tenant_id","campaign_id","workspace_id"}
    _require(isinstance(command,dict) and set(command)==allowed,"transition command fields mismatch")
    _require(command["schema_version"]==SCHEMA_VERSION,"unsupported transition schema version")
    for field in ("tenant_id","campaign_id","workspace_id"): _require(command[field]==state[field],f"transition {field} mismatch")
    _require(command["action"] in TRANSITIONS,"unsupported transition action")
    for field in ("transition_id","request_ref","actor_id"):
        _require(isinstance(command.get(field),str) and SAFE_ID.fullmatch(command[field]) is not None,f"invalid transition command field: {field}")
    _date(command.get("occurred_at"),"transition occurred_at")
    _require(isinstance(command.get("reason"),str) and command["reason"].strip(),"transition reason is required")
    request=next((item for item in state["requests"] if item["id"]==command["request_ref"]),None)
    _require(request is not None,"unknown or cross-scope approval request")
    actor=_trusted_transition_actor(state,request,command,principal_context,authorization_request,authenticated_principal)
    _require(command["transition_id"] not in {entry["transition_id"] for entry in state["ledger"]},"transition replay rejected")
    current=request["status"]
    if command["action"] in {"APPROVE","REJECT","EXPIRE"}: _require(current=="PENDING",f"cannot {command['action'].lower()} request in {current}")
    else: _require(current=="APPROVED","only approved request can be revoked")
    if command["action"]=="APPROVE": _require(command["selected_option_ref"] in {item["id"] for item in request["options"]},"approval requires valid selected option")
    else: _require(command["selected_option_ref"] is None,"selected option only allowed for approval")
    entry={"id":f"ledger-event:{command['transition_id'].split(':',1)[-1]}","transition_id":command["transition_id"],"event_type":TRANSITIONS[command["action"]],"request_ref":request["id"],"actor_type":actor["actor_type"],"actor_id":actor["actor_id"],"role":actor["role"],"scope_type":request["scope_type"],"scope_id":request["scope_id"],"selected_option_ref":command["selected_option_ref"],"occurred_at":command["occurred_at"],"reason":command["reason"],"previous_hash":state["ledger"][-1]["entry_hash"] if state["ledger"] else "GENESIS","tenant_id":state["tenant_id"],"campaign_id":state["campaign_id"],"workspace_id":state["workspace_id"],"authorization_request_id":actor["authorization_request_id"],"authentication_session_id":actor["authentication_session_id"],"authentication_evidence_id":actor["authentication_evidence_id"],"authorization_grant_refs":actor["authorization_grant_refs"],"authorization_payload_digest":actor["authorization_payload_digest"],"trust_source":actor["trust_source"]}
    entry["entry_hash"]=_entry_hash(entry)
    result={"schema_version":SCHEMA_VERSION,"transition_id":command["transition_id"],"request_ref":request["id"],"current_status":current,"projected_status":TRANSITIONS[command["action"]],"proposed_ledger_entry":entry,"persistence_required":True,"external_effects":"NONE","warning":"This proposal does not mutate the ledger or execute the approved action."}
    _require(state==before,"transition proposal mutated approval state")
    return result
