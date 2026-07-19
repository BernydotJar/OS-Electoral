from __future__ import annotations

import copy
import unittest

from core.extraction_citation import (
    EvidenceExtractionValidationError,
    LocalExtractionEngine,
    claim_digest,
)


def reviewed_claim(
    *,
    evidence_id: str,
    claim_text: str,
    disposition: str,
    reviewed_by: str,
    method: str,
    scope: dict[str, str],
) -> dict:
    reviewed_at = "2026-07-18"
    suffix = evidence_id.split(":", 1)[-1]
    return {
        "claim_text": claim_text,
        "disposition": disposition,
        "reviewed_by": reviewed_by,
        "reviewed_at": reviewed_at,
        "method": method,
        "authorization_receipt": {
            "receipt_id": f"authorization-receipt:{suffix}",
            "decision": "ALLOW",
            "principal_id": reviewed_by,
            "permission": "REVIEW_EVIDENCE_CLAIM",
            **scope,
            "evidence_id": evidence_id,
            "claim_digest": claim_digest(claim_text),
            "disposition": disposition,
            "evaluated_at": reviewed_at,
            "authentication_evidence_id": f"authn-evidence:{suffix}",
            "authorization_grant_refs": [f"grant:{suffix}"],
            "trust_source": "OIDC_VERIFIED_SESSION",
        },
    }


class ExtractionCitationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = LocalExtractionEngine()
        self.scope = {
            "tenant_id": "tenant:bernydotjar",
            "campaign_id": "campaign:antigua-guatemala-exploratory",
            "workspace_id": "workspace:antigua-2026",
        }
        self.verified_claim = "Berny graduated from Antigua University"
        self.contradicted_claim = "Corporate donations are present"
        self.evidence = [
            {
                "id": "evidence:biography-official",
                **self.scope,
                "classification": "OFFICIAL_SOURCE",
                "status": "VERIFIED",
                "text": "Berny graduated with honors in public administration from Antigua University in 2015.",
                "source_or_provenance": "Antigua University Registrar",
                "claim_reviews": [reviewed_claim(
                    evidence_id="evidence:biography-official",
                    claim_text=self.verified_claim,
                    disposition="SUPPORTS",
                    reviewed_by="human:research-reviewer",
                    method="Registrar record comparison",
                    scope=self.scope,
                )],
            },
            {
                "id": "evidence:funding-report",
                **self.scope,
                "classification": "OFFICIAL_SOURCE",
                "status": "ACCEPTED",
                "text": "The campaign has received no corporate donations.",
                "source_or_provenance": "Electoral Authority Audit",
                "claim_reviews": [reviewed_claim(
                    evidence_id="evidence:funding-report",
                    claim_text=self.contradicted_claim,
                    disposition="CONTRADICTS",
                    reviewed_by="human:finance-reviewer",
                    method="Audited funding report comparison",
                    scope=self.scope,
                )],
            },
        ]

    def verify(self, claim: str, evidence: list[dict] | None = None) -> dict:
        return self.engine.verify_claim(claim, self.evidence if evidence is None else evidence, **self.scope)

    def test_verified_claim_requires_explicit_human_review(self) -> None:
        result = self.verify(self.verified_claim)
        self.assertEqual(result["status"], "VERIFIED")
        self.assertEqual(result["review_blockers"], [])
        self.assertEqual(result["citations"][0]["source_id"], "evidence:biography-official")
        self.assertEqual(result["citations"][0]["reviewed_by"], "human:research-reviewer")

    def test_contradicted_claim_returns_reviewed_citation(self) -> None:
        result = self.verify(self.contradicted_claim)
        self.assertEqual(result["status"], "CONTRADICTED")
        self.assertEqual(result["citations"][0]["source_id"], "evidence:funding-report")

    def test_ungrounded_claim_returns_empty_citations(self) -> None:
        result = self.verify("Candidate previously lived in Switzerland for ten years")
        self.assertEqual(result["status"], "UNGROUNDED")
        self.assertEqual(result["citations"], [])

    def test_lexical_overlap_never_verifies_without_explicit_review(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence[0]["claim_reviews"] = []
        result = self.verify(self.verified_claim, evidence)
        self.assertEqual(result["status"], "REVIEW_REQUIRED")
        self.assertEqual(result["citations"], [])

    def test_unknown_or_unready_evidence_never_verifies(self) -> None:
        for field, value in (("classification", "UNKNOWN"), ("status", "UNDER_REVIEW")):
            with self.subTest(field=field):
                evidence = copy.deepcopy(self.evidence)
                evidence[0][field] = value
                result = self.verify(self.verified_claim, evidence)
                self.assertEqual(result["status"], "REVIEW_REQUIRED")
                self.assertIn("EVIDENCE_NOT_VERIFIABLE_OR_NOT_READY", result["review_blockers"])

    def test_unready_evidence_cannot_contradict(self) -> None:
        for field, value in (("classification", "HYPOTHESIS"), ("status", "REJECTED")):
            with self.subTest(field=field):
                evidence = copy.deepcopy(self.evidence)
                evidence[1][field] = value
                result = self.verify(self.contradicted_claim, evidence)
                self.assertEqual(result["status"], "REVIEW_REQUIRED")
                self.assertIn("EVIDENCE_NOT_VERIFIABLE_OR_NOT_READY", result["review_blockers"])

    def test_contradiction_wins_over_support(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        contradictory = copy.deepcopy(evidence[0])
        contradictory["id"] = "evidence:biography-contradiction"
        contradictory["claim_reviews"] = [reviewed_claim(
            evidence_id=contradictory["id"],
            claim_text=self.verified_claim,
            disposition="CONTRADICTS",
            reviewed_by="human:research-reviewer",
            method="Contradiction review",
            scope=self.scope,
        )]
        evidence.append(contradictory)
        result = self.verify(self.verified_claim, evidence)
        self.assertEqual(result["status"], "CONTRADICTED")

    def test_cross_tenant_and_campaign_evidence_are_rejected(self) -> None:
        for field, value in (("tenant_id", "tenant:other"), ("campaign_id", "campaign:other")):
            with self.subTest(field=field):
                evidence = copy.deepcopy(self.evidence)
                evidence[0][field] = value
                with self.assertRaisesRegex(EvidenceExtractionValidationError, "cross-scope"):
                    self.verify(self.verified_claim, evidence)

    def test_review_requires_human_reviewer(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence[0]["claim_reviews"][0]["reviewed_by"] = "agent:researcher"
        with self.assertRaisesRegex(EvidenceExtractionValidationError, "human reviewer"):
            self.verify(self.verified_claim, evidence)

    def test_review_requires_exact_authorization_receipt(self) -> None:
        mutations = (
            ("decision", "DENY", "authorization denied"),
            ("principal_id", "human:other", "principal mismatch"),
            ("evidence_id", "evidence:other", "evidence mismatch"),
            ("claim_digest", "0" * 64, "claim mismatch"),
            ("disposition", "CONTRADICTS", "disposition mismatch"),
            ("tenant_id", "tenant:other", "scope mismatch"),
        )
        for field, value, message in mutations:
            with self.subTest(field=field):
                evidence = copy.deepcopy(self.evidence)
                evidence[0]["claim_reviews"][0]["authorization_receipt"][field] = value
                with self.assertRaisesRegex(EvidenceExtractionValidationError, message):
                    self.verify(self.verified_claim, evidence)

    def test_exact_claim_matching_preserves_meaning_bearing_symbols(self) -> None:
        evidence = copy.deepcopy(self.evidence)
        evidence[0]["claim_reviews"] = [reviewed_claim(
            evidence_id=evidence[0]["id"],
            claim_text="Budget > 100",
            disposition="SUPPORTS",
            reviewed_by="human:research-reviewer",
            method="Budget comparison",
            scope=self.scope,
        )]
        evidence[0]["text"] = "Budget values include 100."
        result = self.verify("Budget < 100", evidence)
        self.assertNotEqual(result["status"], "VERIFIED")

    def test_empty_or_whitespace_claim_is_ungrounded(self) -> None:
        result = self.verify("   ")
        self.assertEqual(result["status"], "UNGROUNDED")

    def test_inputs_are_immutable(self) -> None:
        evidence_copy = copy.deepcopy(self.evidence)
        self.verify(self.verified_claim, evidence_copy)
        self.assertEqual(evidence_copy, self.evidence)


if __name__ == "__main__":
    unittest.main()
