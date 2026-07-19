#!/usr/bin/env python3
"""Fail-closed evidence-grounded claim review contracts.

This module does not infer truth from lexical similarity.  A claim is verified
only when an in-scope, independently reviewable evidence record contains an
explicit human claim review that supports that exact normalized claim.
"""
from __future__ import annotations

import copy
import datetime as dt
import hashlib
import re
import unicodedata
from abc import ABC, abstractmethod
from typing import Any


SAFE_ID = re.compile(r"^[a-z][a-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9._-]*$")
EVIDENCE_CLASSES = {
    "OFFICIAL_SOURCE",
    "CAMPAIGN_RESEARCH",
    "PERCEPTION",
    "HYPOTHESIS",
    "UNKNOWN",
}
VERIFIABLE_CLASSES = {"OFFICIAL_SOURCE", "CAMPAIGN_RESEARCH"}
EVIDENCE_STATUSES = {
    "ACCEPTED",
    "VERIFIED",
    "READY",
    "PENDING",
    "UNDER_REVIEW",
    "UNKNOWN",
    "REJECTED",
    "CONTRADICTED",
}
ENABLING_STATUSES = {"ACCEPTED", "VERIFIED", "READY"}
REVIEW_DISPOSITIONS = {"SUPPORTS", "CONTRADICTS", "UNKNOWN"}
REVIEW_FIELDS = {
    "claim_text",
    "disposition",
    "reviewed_by",
    "reviewed_at",
    "method",
    "authorization_receipt",
}
REVIEW_AUTHORIZATION_FIELDS = {
    "receipt_id",
    "decision",
    "principal_id",
    "permission",
    "tenant_id",
    "campaign_id",
    "workspace_id",
    "evidence_id",
    "claim_digest",
    "disposition",
    "evaluated_at",
    "authentication_evidence_id",
    "authorization_grant_refs",
    "trust_source",
}
REVIEW_PERMISSION = "REVIEW_EVIDENCE_CLAIM"
TRUSTED_AUTHENTICATION_SOURCES = {"OIDC_VERIFIED_SESSION", "INTERNAL_SERVICE_IDENTITY"}
STOP_WORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "in", "is", "it", "of", "on", "or", "the", "to", "was", "were", "with",
}


class EvidenceExtractionValidationError(ValueError):
    """Raised when claim or evidence inputs cannot be trusted safely."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceExtractionValidationError(message)


def _canonical_claim(value: str) -> str:
    """Normalize Unicode and whitespace while retaining meaning-bearing symbols."""
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def claim_digest(value: str) -> str:
    return hashlib.sha256(_canonical_claim(value).encode("utf-8")).hexdigest()


def _normalize_tokens(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold()
    normalized = re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE)
    return " ".join(normalized.split())


def _tokens(value: str) -> set[str]:
    return {
        token
        for token in _normalize_tokens(value).split()
        if len(token) > 2 and token not in STOP_WORDS
    }


def _review_date(value: Any, label: str) -> None:
    _require(isinstance(value, str) and value.strip(), f"{label} is required")
    try:
        dt.date.fromisoformat(value)
    except ValueError as exc:
        raise EvidenceExtractionValidationError(f"invalid {label}: {value}") from exc


def _validate_scope(tenant_id: str, campaign_id: str, workspace_id: str) -> None:
    expected = {
        "tenant_id": (tenant_id, "tenant:"),
        "campaign_id": (campaign_id, "campaign:"),
        "workspace_id": (workspace_id, "workspace:"),
    }
    for field, (value, prefix) in expected.items():
        _require(isinstance(value, str) and SAFE_ID.fullmatch(value) is not None, f"invalid {field}")
        _require(value.startswith(prefix), f"{field} namespace mismatch")


def _validated_evidence(
    evidence_list: list[dict[str, Any]],
    *,
    tenant_id: str,
    campaign_id: str,
    workspace_id: str,
) -> list[dict[str, Any]]:
    _require(isinstance(evidence_list, list), "evidence_list must be a list")
    validated: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    expected_scope = {
        "tenant_id": tenant_id,
        "campaign_id": campaign_id,
        "workspace_id": workspace_id,
    }
    for evidence in evidence_list:
        _require(isinstance(evidence, dict), "evidence_list must contain objects")
        evidence_id = evidence.get("id")
        _require(
            isinstance(evidence_id, str)
            and SAFE_ID.fullmatch(evidence_id) is not None
            and evidence_id not in seen_ids,
            f"invalid or duplicate evidence id: {evidence_id}",
        )
        seen_ids.add(evidence_id)
        for field, expected in expected_scope.items():
            _require(evidence.get(field) == expected, f"cross-scope evidence rejected: {evidence_id} ({field})")
        _require(evidence.get("classification") in EVIDENCE_CLASSES, f"invalid evidence classification: {evidence_id}")
        _require(evidence.get("status") in EVIDENCE_STATUSES, f"invalid evidence status: {evidence_id}")
        _require(
            isinstance(evidence.get("source_or_provenance"), str)
            and evidence["source_or_provenance"].strip(),
            f"evidence provenance required: {evidence_id}",
        )
        reviews = evidence.get("claim_reviews")
        _require(isinstance(reviews, list), f"claim_reviews must be a list: {evidence_id}")
        for review in reviews:
            _require(
                isinstance(review, dict) and set(review) == REVIEW_FIELDS,
                f"claim review fields mismatch: {evidence_id}",
            )
            _require(
                isinstance(review["claim_text"], str) and review["claim_text"].strip(),
                f"reviewed claim text required: {evidence_id}",
            )
            _require(review["disposition"] in REVIEW_DISPOSITIONS, f"invalid claim review disposition: {evidence_id}")
            _require(
                isinstance(review["reviewed_by"], str)
                and SAFE_ID.fullmatch(review["reviewed_by"]) is not None
                and review["reviewed_by"].startswith("human:"),
                f"claim review requires a human reviewer: {evidence_id}",
            )
            _review_date(review["reviewed_at"], f"reviewed_at for {evidence_id}")
            _require(isinstance(review["method"], str) and review["method"].strip(), f"review method required: {evidence_id}")
            receipt = review["authorization_receipt"]
            _require(
                isinstance(receipt, dict) and set(receipt) == REVIEW_AUTHORIZATION_FIELDS,
                f"claim review authorization receipt fields mismatch: {evidence_id}",
            )
            _require(
                isinstance(receipt["receipt_id"], str)
                and SAFE_ID.fullmatch(receipt["receipt_id"]) is not None,
                f"invalid claim review authorization receipt: {evidence_id}",
            )
            _require(receipt["decision"] == "ALLOW", f"claim review authorization denied: {evidence_id}")
            _require(
                receipt["principal_id"] == review["reviewed_by"],
                f"claim review authorization principal mismatch: {evidence_id}",
            )
            _require(
                receipt["permission"] == REVIEW_PERMISSION,
                f"claim review authorization permission mismatch: {evidence_id}",
            )
            for field, expected in expected_scope.items():
                _require(
                    receipt[field] == expected,
                    f"claim review authorization scope mismatch: {evidence_id} ({field})",
                )
            _require(
                receipt["evidence_id"] == evidence_id,
                f"claim review authorization evidence mismatch: {evidence_id}",
            )
            _require(
                receipt["claim_digest"] == claim_digest(review["claim_text"]),
                f"claim review authorization claim mismatch: {evidence_id}",
            )
            _require(
                receipt["disposition"] == review["disposition"],
                f"claim review authorization disposition mismatch: {evidence_id}",
            )
            _require(
                receipt["evaluated_at"] == review["reviewed_at"],
                f"claim review authorization date mismatch: {evidence_id}",
            )
            _require(
                isinstance(receipt["authentication_evidence_id"], str)
                and receipt["authentication_evidence_id"].startswith("authn-evidence:")
                and SAFE_ID.fullmatch(receipt["authentication_evidence_id"]) is not None,
                f"claim review authentication evidence required: {evidence_id}",
            )
            _require(
                isinstance(receipt["authorization_grant_refs"], list)
                and receipt["authorization_grant_refs"]
                and all(
                    isinstance(item, str) and SAFE_ID.fullmatch(item) is not None
                    for item in receipt["authorization_grant_refs"]
                ),
                f"claim review authorization grants required: {evidence_id}",
            )
            _require(
                receipt["trust_source"] in TRUSTED_AUTHENTICATION_SOURCES,
                f"claim review trust source is not accepted: {evidence_id}",
            )
        validated.append(evidence)
    return validated


class EvidenceGroundedExtractionService(ABC):
    @abstractmethod
    def verify_claim(
        self,
        claim_text: str,
        evidence_list: list[dict[str, Any]],
        *,
        tenant_id: str,
        campaign_id: str,
        workspace_id: str,
    ) -> dict[str, Any]:
        """Verify a claim using explicit, reviewed, in-scope evidence only."""


class LocalExtractionEngine(EvidenceGroundedExtractionService):
    def verify_claim(
        self,
        claim_text: str,
        evidence_list: list[dict[str, Any]],
        *,
        tenant_id: str,
        campaign_id: str,
        workspace_id: str,
    ) -> dict[str, Any]:
        before = copy.deepcopy(evidence_list)
        _validate_scope(tenant_id, campaign_id, workspace_id)
        evidence = _validated_evidence(
            evidence_list,
            tenant_id=tenant_id,
            campaign_id=campaign_id,
            workspace_id=workspace_id,
        )
        if not isinstance(claim_text, str) or not claim_text.strip():
            return {"status": "UNGROUNDED", "citations": [], "review_blockers": ["CLAIM_TEXT_REQUIRED"]}

        normalized_claim = _canonical_claim(claim_text)
        claim_tokens = _tokens(claim_text)
        supporting: list[dict[str, Any]] = []
        contradicting: list[dict[str, Any]] = []
        unresolved: list[str] = []
        potentially_relevant = False

        for item in evidence:
            evidence_text = " ".join(
                str(item.get(field, "")) for field in ("text", "description") if item.get(field)
            )
            if claim_tokens and len(claim_tokens & _tokens(evidence_text)) >= min(2, len(claim_tokens)):
                potentially_relevant = True
            for review in item["claim_reviews"]:
                if _canonical_claim(review["claim_text"]) != normalized_claim:
                    continue
                citation = {
                    "source_id": item["id"],
                    "review_disposition": review["disposition"],
                    "reviewed_by": review["reviewed_by"],
                    "reviewed_at": review["reviewed_at"],
                    "method": review["method"],
                }
                evidence_is_ready = (
                    item["classification"] in VERIFIABLE_CLASSES
                    and item["status"] in ENABLING_STATUSES
                )
                if review["disposition"] == "CONTRADICTS":
                    if evidence_is_ready:
                        contradicting.append(citation)
                    else:
                        unresolved.append(item["id"])
                elif review["disposition"] == "SUPPORTS":
                    if evidence_is_ready:
                        supporting.append(citation)
                    else:
                        unresolved.append(item["id"])
                else:
                    unresolved.append(item["id"])

        _require(evidence_list == before, "claim verification mutated evidence inputs")
        if contradicting:
            return {
                "status": "CONTRADICTED",
                "citations": [*contradicting, *supporting],
                "review_blockers": ["CONTRADICTORY_REVIEW_REQUIRES_HUMAN_RESOLUTION"],
            }
        if supporting and not unresolved:
            return {"status": "VERIFIED", "citations": supporting, "review_blockers": []}
        if supporting or unresolved or potentially_relevant:
            blockers = ["HUMAN_CLAIM_REVIEW_REQUIRED"]
            if unresolved:
                blockers.append("EVIDENCE_NOT_VERIFIABLE_OR_NOT_READY")
            return {"status": "REVIEW_REQUIRED", "citations": supporting, "review_blockers": blockers}
        return {"status": "UNGROUNDED", "citations": [], "review_blockers": ["NO_REVIEWED_SUPPORTING_EVIDENCE"]}
