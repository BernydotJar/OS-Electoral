from __future__ import annotations

import copy
import unittest
from core.extraction_citation import LocalExtractionEngine


class ExtractionCitationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = LocalExtractionEngine()
        self.evidence = [
            {
                "id": "evidence:biography-official",
                "text": "Berny graduated with honors in public administration from Antigua University in 2015.",
                "source_or_provenance": "Antigua University Registrar"
            },
            {
                "id": "evidence:funding-report",
                "text": "The campaign has received no corporate donations.",
                "source_or_provenance": "Electoral Authority Audit"
            }
        ]

    def test_verified_claim_returns_citations(self) -> None:
        claim = "Berny graduated from Antigua University"
        result = self.engine.verify_claim(claim, self.evidence)
        self.assertEqual(result["status"], "VERIFIED")
        self.assertGreater(len(result["citations"]), 0)
        self.assertEqual(result["citations"][0]["source_id"], "evidence:biography-official")

    def test_contradicted_claim_returns_citations(self) -> None:
        claim = "corporate donations are present"
        result = self.engine.verify_claim(claim, self.evidence)
        self.assertEqual(result["status"], "CONTRADICTED")
        self.assertGreater(len(result["citations"]), 0)
        self.assertEqual(result["citations"][0]["source_id"], "evidence:funding-report")

    def test_ungrounded_claim_returns_empty_citations(self) -> None:
        claim = "Candidate previously lived in Switzerland for ten years"
        result = self.engine.verify_claim(claim, self.evidence)
        self.assertEqual(result["status"], "UNGROUNDED")
        self.assertEqual(len(result["citations"]), 0)

    def test_empty_or_whitespace_claim_is_ungrounded(self) -> None:
        result = self.engine.verify_claim("   ", self.evidence)
        self.assertEqual(result["status"], "UNGROUNDED")
        self.assertEqual(len(result["citations"]), 0)

    def test_inputs_are_immutable(self) -> None:
        evidence_copy = copy.deepcopy(self.evidence)
        self.engine.verify_claim("corporate donations", evidence_copy)
        self.assertEqual(evidence_copy, self.evidence)


if __name__ == "__main__":
    unittest.main()
