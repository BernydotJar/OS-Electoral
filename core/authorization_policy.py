#!/usr/bin/env python3
"""Pure tenant-scoped authorization policy boundary; no authentication or effects."""
from __future__ import annotations
import copy, json, re
from typing import Any

SCHEMA_VERSION="1.0"
SAFE_ID=re.compile(r"^[a-z][a-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9._-]*$")
ACTOR_TYPES={"HUMAN","AGENT","SYSTEM"}
PERMISSIONS={"READ_WORKSPACE","CREATE_DRAFT","REQUEST_APPROVAL","PROPOSE_TRANSITION","MANAGE_INTERNAL_ASSIGNMENTS","APPROVE_POLITICAL","APPROVE_LEGAL","APPROVE_FINANCIAL","APPROVE_PUBLICATION","APPROVE_SPENDING","APPROVE_MOBILIZATION"}
HUMAN_ONLY={"APPROVE_POLITICAL","APPROVE_LEGAL","APPROVE_FINANCIAL","APPROVE_PUBLICATION","APPROVE_SPENDING","APPROVE_MOBILIZATION"}
GRANT_STATUSES={"ACTIVE","REVOKED","EXPIRED"}

class AuthorizationPolicyError(ValueError): pass

def _require(condition:bool,message:str)->None:
    if not condition: raise AuthorizationPolicyError(message)

def validate_principal_context(context:dict[str,Any])->dict[str,Any]:
    required={"schema_version","principal_id","actor_type","display_name","grants","metadata"}
    _require(isinstance(context,dict) and set(context)==required,"principal context fields mismatch")
    _require(context["schema_version"]==SCHEMA_VERSION,"unsupported principal schema version")
    _require(SAFE_ID.fullmatch(context["principal_id"]) is not None,"invalid principal_id")
    _require(context["actor_type"] in ACTOR_TYPES,"invalid actor_type")
    _require(isinstance(context["display_name"],str),"display_name must be text")
    ids=set()
    for grant in context["grants"]:
        fields={"id","status","tenant_id","campaign_id","workspace_id","role_id","permissions","valid_from","valid_until","source_or_provenance"}
        _require(fields==set(grant),f"grant fields mismatch: {grant.get('id')}")
        _require(SAFE_ID.fullmatch(grant["id"]) is not None and grant["id"] not in ids,f"invalid or duplicate grant: {grant.get('id')}")
        ids.add(grant["id"])
        for field in ("tenant_id","campaign_id","workspace_id","role_id"):
            _require(SAFE_ID.fullmatch(grant[field]) is not None,f"invalid grant scope: {grant['id']} ({field})")
        _require(grant["status"] in GRANT_STATUSES,f"invalid grant status: {grant['id']}")
        _require(isinstance(grant["permissions"],list) and grant["permissions"] and len(grant["permissions"])==len(set(grant["permissions"])),f"grant permissions must be unique: {grant['id']}")
        _require(all(item in PERMISSIONS for item in grant["permissions"]),f"unknown permission in grant: {grant['id']}")
        if context["actor_type"]!="HUMAN":
            _require(not (set(grant["permissions"]) & HUMAN_ONLY),f"non-human principal cannot receive approval permission: {grant['id']}")
        _require(grant["source_or_provenance"] not in (None,""),f"grant provenance required: {grant['id']}")
    return context

def authorize(context:dict[str,Any],request:dict[str,Any])->dict[str,Any]:
    before=copy.deepcopy(context); validate_principal_context(context)
    allowed={"schema_version","request_id","principal_id","tenant_id","campaign_id","workspace_id","permission","resource_type","resource_id","evaluation_date"}
    _require(isinstance(request,dict) and set(request)==allowed,"authorization request fields mismatch")
    _require(request["schema_version"]==SCHEMA_VERSION,"unsupported authorization request schema version")
    _require(request["principal_id"]==context["principal_id"],"principal mismatch")
    _require(request["permission"] in PERMISSIONS,"unknown permission")
    for field in ("request_id","tenant_id","campaign_id","workspace_id","resource_id"):
        _require(SAFE_ID.fullmatch(request[field]) is not None,f"invalid request field: {field}")
    matching=[]; rejected=[]
    for grant in context["grants"]:
        if (grant["tenant_id"],grant["campaign_id"],grant["workspace_id"])!=(request["tenant_id"],request["campaign_id"],request["workspace_id"]):
            rejected.append({"grant_id":grant["id"],"reason":"SCOPE_MISMATCH"}); continue
        if grant["status"]!="ACTIVE": rejected.append({"grant_id":grant["id"],"reason":grant["status"]}); continue
        if request["permission"] not in grant["permissions"]: rejected.append({"grant_id":grant["id"],"reason":"PERMISSION_MISSING"}); continue
        if grant["valid_from"] and request["evaluation_date"]<grant["valid_from"]: rejected.append({"grant_id":grant["id"],"reason":"NOT_YET_VALID"}); continue
        if grant["valid_until"] and request["evaluation_date"]>grant["valid_until"]: rejected.append({"grant_id":grant["id"],"reason":"EXPIRED_BY_DATE"}); continue
        matching.append(grant["id"])
    if context["actor_type"]!="HUMAN" and request["permission"] in HUMAN_ONLY:
        decision="DENY"; reasons=["HUMAN_AUTHORITY_REQUIRED"]
    elif matching:
        decision="ALLOW"; reasons=["EXACT_ACTIVE_GRANT"]
    else:
        decision="DENY"; reasons=["NO_EXACT_ACTIVE_GRANT"]
    result={"schema_version":SCHEMA_VERSION,"request_id":request["request_id"],"principal_id":context["principal_id"],"actor_type":context["actor_type"],"decision":decision,"permission":request["permission"],"scope":{"tenant_id":request["tenant_id"],"campaign_id":request["campaign_id"],"workspace_id":request["workspace_id"]},"resource":{"type":request["resource_type"],"id":request["resource_id"]},"matching_grants":matching,"rejected_grants":rejected,"reasons":reasons,"external_effects":"NONE","warning":"Authorization is a policy decision only; it does not execute the requested action."}
    _require(context==before,"authorization mutated principal context")
    return result

def pretty(value:Any)->str: return json.dumps(value,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
