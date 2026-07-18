#!/usr/bin/env python3
"""Bounded context: Evidence-Grounded Extraction and Citation Contracts."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class EvidenceGroundedExtractionService(ABC):
    @abstractmethod
    def verify_claim(self, claim_text: str, evidence_list: list[dict[str, Any]]) -> dict[str, Any]:
        """Verify a candidate claim against a list of evidence documents."""
        pass


class LocalExtractionEngine(EvidenceGroundedExtractionService):
    def verify_claim(self, claim_text: str, evidence_list: list[dict[str, Any]]) -> dict[str, Any]:
        if not isinstance(claim_text, str) or not claim_text.strip():
            return {
                "status": "UNGROUNDED",
                "citations": []
            }

        claim_lower = claim_text.lower()

        # Simple extraction rules for verification
        citations = []
        contradicted = False

        for ev in evidence_list:
            ev_id = ev.get("id", "evidence:unknown")
            # We look for content keys: "text", "description", or "source_or_provenance"
            content_sources = [ev.get("text", ""), ev.get("description", ""), ev.get("source_or_provenance", "")]
            combined_text = " ".join([str(s) for s in content_sources if s]).lower()

            if not combined_text:
                continue

            # Check if there is an explicit contradiction
            # e.g., if the evidence states "never", "not", or "false" regarding the key term
            words = [w.strip(",.?!") for w in claim_lower.split()]
            key_words = [w for w in words if len(w) > 4]

            if not key_words:
                continue

            # Look for contradiction phrases
            for kw in key_words:
                if kw in combined_text:
                    # Check if surrounded by negative qualifiers in the evidence
                    negations = [f"no {kw}", f"not {kw}", f"never {kw}", f"false {kw}", f"incorrect {kw}"]
                    if any(neg in combined_text for neg in negations):
                        contradicted = True
                        citations.append({
                            "source_id": ev_id,
                            "text_snippet": f"Contradiction detected matching key term '{kw}'",
                            "confidence_score": 0.95
                        })
                    else:
                        citations.append({
                            "source_id": ev_id,
                            "text_snippet": f"Found reference matching '{kw}'",
                            "confidence_score": 0.85
                        })

        if contradicted:
            return {
                "status": "CONTRADICTED",
                "citations": citations
            }
        elif citations:
            return {
                "status": "VERIFIED",
                "citations": citations
            }
        else:
            return {
                "status": "UNGROUNDED",
                "citations": []
            }
