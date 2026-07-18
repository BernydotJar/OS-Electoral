#!/usr/bin/env python3
"""Pure append-only persistence intent and deterministic in-memory audit adapter."""
from __future__ import annotations
import copy, hashlib, json, re
from typing import Any

SCHEMA_VERSION="1.0"
SAFE_ID=re.compile(r"^[a-z][a-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9._-]*$")
WRITE_OPERATIONS={"APPEND_EVENT","CREATE_ARTIFACT","UPDATE_PROJECTION"}
READ_ONLY_RESOURCES={"GOVERNANCE_SNAPSHOT","EVIDENCE_SOURCE","AUDIT_EVENT"}
PROHIBITED_OPERATIONS={"PUBLISH","SPEND","ACTIVATE_PAID_MEDIA","MOBILIZE","CONTACT_CITIZEN"}

class PersistenceContractError(ValueError): pass

def _require(condition:bool,message:str)->None:
    if not condition: raise PersistenceContractError(message)

def canonical(value:Any)->str: return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"))
def digest(value:Any)->str: return hashlib.sha256(canonical(value).encode()).hexdigest()
def event_hash(event:dict[str,Any])->str: return digest({key:value for key,value in event.items() if key!="event_hash"})

def validate_store(store:dict[str,Any])->dict[str,Any]:
    required={"schema_version","store_id","tenant_id","campaign_id","workspace_id","aggregate_version","last_event_hash","events","idempotency_keys","metadata"}
    _require(isinstance(store,dict) and set(store)==required,"store fields mismatch")
    _require(store["schema_version"]==SCHEMA_VERSION,"unsupported store schema version")
    for field in ("store_id","tenant_id","campaign_id","workspace_id"):
        _require(SAFE_ID.fullmatch(store[field]) is not None,f"invalid store field: {field}")
    _require(isinstance(store["aggregate_version"],int) and store["aggregate_version"]>=0,"invalid aggregate version")
    _require(isinstance(store["events"],list) and isinstance(store["idempotency_keys"],list),"events and idempotency keys must be lists")
    _require(len(store["idempotency_keys"])==len(set(store["idempotency_keys"])),"duplicate persisted idempotency key")
    previous="GENESIS"
    for index,event in enumerate(store["events"],start=1):
        required_event={"id","intent_id","idempotency_key","operation","resource_type","resource_id","principal_id","authorization_request_id","aggregate_version","occurred_at","payload_digest","previous_hash","event_hash","tenant_id","campaign_id","workspace_id"}
        _require(set(event)==required_event,f"audit event fields mismatch: {event.get('id')}")
        for field in ("tenant_id","campaign_id","workspace_id"):
            _require(event[field]==store[field],f"cross-scope audit event: {event['id']} ({field})")
        _require(event["aggregate_version"]==index,f"audit version sequence broken: {event['id']}")
        _require(event["previous_hash"]==previous,f"audit hash chain broken: {event['id']}")
        _require(event["event_hash"]==event_hash(event),f"audit event hash mismatch: {event['id']}")
        previous=event["event_hash"]
    _require(store["aggregate_version"]==len(store["events"]),"store aggregate version disagrees with event count")
    _require(store["last_event_hash"]==previous,"store last_event_hash mismatch")
    return store

def validate_write_intent(intent:dict[str,Any],authorization:dict[str,Any],store:dict[str,Any])->None:
    allowed={"schema_version","intent_id","idempotency_key","tenant_id","campaign_id","workspace_id","principal_id","authorization_request_id","required_permission","operation","resource_type","resource_id","expected_version","expected_previous_hash","payload","occurred_at"}
    _require(isinstance(intent,dict) and set(intent)==allowed,"write intent fields mismatch")
    _require(intent["schema_version"]==SCHEMA_VERSION,"unsupported write intent schema version")
    for field in ("intent_id","tenant_id","campaign_id","workspace_id","principal_id","authorization_request_id","resource_id"):
        _require(SAFE_ID.fullmatch(intent[field]) is not None,f"invalid write intent field: {field}")
    _require(intent["operation"] in WRITE_OPERATIONS,f"unsupported or prohibited write operation: {intent['operation']}")
    _require(intent["operation"] not in PROHIBITED_OPERATIONS,"prohibited external operation")
    _require(intent["resource_type"] not in READ_ONLY_RESOURCES,f"resource is read-only: {intent['resource_type']}")
    _require(isinstance(intent["payload"],dict),"payload must be an object")
    _require(authorization.get("decision")=="ALLOW","write intent requires ALLOW authorization decision")
    _require(authorization.get("external_effects")=="NONE","authorization decision contract mismatch")
    _require(authorization.get("request_id")==intent["authorization_request_id"],"authorization request reference mismatch")
    _require(authorization.get("principal_id")==intent["principal_id"],"authorization principal mismatch")
    _require(authorization.get("permission")==intent["required_permission"],"authorization permission mismatch")
    scope=authorization.get("scope",{})
    for field in ("tenant_id","campaign_id","workspace_id"):
        _require(intent[field]==store[field],f"write intent {field} mismatch with store")
        _require(intent[field]==scope.get(field),f"write intent {field} mismatch with authorization")
    resource=authorization.get("resource",{})
    _require(resource.get("id")==intent["resource_id"],"authorization resource mismatch")
    _require(intent["expected_version"]==store["aggregate_version"],"stale aggregate version")
    _require(intent["expected_previous_hash"]==store["last_event_hash"],"stale previous event hash")
    _require(intent["idempotency_key"] not in store["idempotency_keys"],"idempotency replay rejected")

def plan_append(store:dict[str,Any],intent:dict[str,Any],authorization:dict[str,Any])->dict[str,Any]:
    before=copy.deepcopy(store); validate_store(store); validate_write_intent(intent,authorization,store)
    version=store["aggregate_version"]+1
    event={"id":f"audit-event:{intent['intent_id'].split(':',1)[-1]}","intent_id":intent["intent_id"],"idempotency_key":intent["idempotency_key"],"operation":intent["operation"],"resource_type":intent["resource_type"],"resource_id":intent["resource_id"],"principal_id":intent["principal_id"],"authorization_request_id":intent["authorization_request_id"],"aggregate_version":version,"occurred_at":intent["occurred_at"],"payload_digest":digest(intent["payload"]),"previous_hash":store["last_event_hash"],"tenant_id":store["tenant_id"],"campaign_id":store["campaign_id"],"workspace_id":store["workspace_id"]}
    event["event_hash"]=event_hash(event)
    result={"schema_version":SCHEMA_VERSION,"intent_id":intent["intent_id"],"outcome":"ACCEPTABLE_FOR_ADAPTER","planned_event":event,"projected_store":{"aggregate_version":version,"last_event_hash":event["event_hash"],"idempotency_key":intent["idempotency_key"]},"persistence_performed":False,"external_effects":"NONE","warning":"This plan does not write to a database, filesystem, network service or domain aggregate."}
    _require(store==before,"persistence planning mutated store")
    return result

def apply_in_memory(store:dict[str,Any],plan:dict[str,Any])->dict[str,Any]:
    """Test-only deterministic adapter returning a new store; input remains immutable."""
    before=copy.deepcopy(store); validate_store(store)
    _require(plan.get("outcome")=="ACCEPTABLE_FOR_ADAPTER" and plan.get("persistence_performed") is False,"invalid persistence plan")
    event=copy.deepcopy(plan["planned_event"])
    _require(event["aggregate_version"]==store["aggregate_version"]+1,"planned event version mismatch")
    _require(event["previous_hash"]==store["last_event_hash"],"planned event previous hash mismatch")
    _require(event["idempotency_key"] not in store["idempotency_keys"],"adapter idempotency replay rejected")
    projected=copy.deepcopy(store); projected["events"].append(event); projected["idempotency_keys"].append(event["idempotency_key"]); projected["aggregate_version"]=event["aggregate_version"]; projected["last_event_hash"]=event["event_hash"]
    validate_store(projected); _require(store==before,"in-memory adapter mutated input store")
    return projected

def pretty(value:Any)->str: return json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
