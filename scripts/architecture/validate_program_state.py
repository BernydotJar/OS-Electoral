#!/usr/bin/env python3
"""Validate CampaignOS architecture, stack and roadmap state."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
MANIFEST=ROOT/"architecture/program-state.json"
ALLOWED={"IMPLEMENTED_IN_STACK","ACTIVE","EXECUTABLE_NEXT","HUMAN_BLOCKED","DEFERRED"}
PROHIBITED={"VOTER_LEVEL_PROFILING","PERSUADABILITY_SCORING","SENSITIVE_MICROTARGETING","DISINFORMATION","AUTOMATED_PUBLISHING","AUTOMATED_SPENDING","AUTOMATED_MOBILIZATION","CITIZEN_SURVEILLANCE","UNAUTHORIZED_CONTACT"}

def require(condition:bool,message:str)->None:
    if not condition: raise AssertionError(message)

def main()->int:
    data=json.loads(MANIFEST.read_text(encoding="utf-8"))
    require(data["schema_version"]=="1.0","unsupported program-state schema")
    stack=data["stack"]; stack_ids=[item["id"] for item in stack]
    require(len(stack_ids)==len(set(stack_ids)),"duplicate stack increment")
    branches={item["branch"] for item in stack}
    require(len(branches)==len(stack),"duplicate stack branch")
    previous="main"
    for item in stack:
        require(item["status"]=="IMPLEMENTED_IN_STACK",f"invalid stack status: {item['id']}")
        require(item["base"]==previous,f"stack base mismatch: {item['id']} expected {previous}")
        require(isinstance(item["validation_run"],int) and item["validation_run"]>0,f"missing validation run: {item['id']}")
        require(item["external_effects"]=="NONE",f"external effects forbidden in stack: {item['id']}")
        previous=item["branch"]
    context_ids=set()
    for context in data["bounded_contexts"]:
        require(context["id"] not in context_ids,"duplicate bounded context")
        context_ids.add(context["id"])
        require(context["status"]=="IMPLEMENTED_IN_STACK",f"context status mismatch: {context['id']}")
        require(context["code"] and context["validators"],f"context lacks code or validators: {context['id']}")
        for relative in [*context["code"],*context["validators"]]:
            require((ROOT/relative).is_file(),f"missing architecture artifact: {relative}")
    roadmap_ids={item["id"] for item in data["roadmap"]}
    known=set(stack_ids)|roadmap_ids
    require(len(roadmap_ids)==len(data["roadmap"]),"duplicate roadmap item")
    graph={item["id"]:item["depends_on"] for item in data["roadmap"]}
    for item in data["roadmap"]:
        require(item["status"] in ALLOWED,f"invalid roadmap status: {item['id']}")
        for dependency in item["depends_on"]:
            require(dependency in known,f"unknown roadmap dependency {dependency} from {item['id']}")
    visiting=set(); complete=set()
    def walk(node:str)->None:
        if node in complete:return
        require(node not in visiting,f"roadmap dependency cycle: {node}")
        visiting.add(node)
        for dependency in graph.get(node,[]):
            if dependency in graph: walk(dependency)
        visiting.remove(node); complete.add(node)
    for node in graph: walk(node)
    require(set(data["prohibited_capabilities"])==PROHIBITED,"prohibited capability set drift")
    require(data["known_critical_or_high_findings"]==0,"unresolved CRITICAL/HIGH findings")
    campaign=data["campaign_state"]
    for field in ("public_positioning","budget_ceiling","political_content","paid_media","field_mobilization"):
        require(campaign[field]=="BLOCKED",f"campaign gate unexpectedly opened: {field}")
    require("MERGE_STACK" in data["human_gates"] and "DEPLOYMENT" in data["human_gates"],"release human gates missing")
    require(any(item["status"]=="EXECUTABLE_NEXT" for item in data["roadmap"]),"program lacks executable next increment")
    print("[OK] CampaignOS executable architecture, stack, gates and roadmap state")
    return 0
if __name__=="__main__": raise SystemExit(main())
