from __future__ import annotations

import unittest

from tests.test_l3_evidence_edge_graph import _meaning
from src.brain.contracts import MeaningDirection
from src.brain.l3.contradiction import detect_contradictions
from src.brain.l3.evidence_edge import build_evidence_edge


class L3ContradictionDetectionTest(unittest.TestCase):
    def test_supportive_and_risk_same_dimension_are_contradiction(self) -> None:
        support = build_evidence_edge(_meaning("support", MeaningDirection.SUPPORTIVE))
        risk = build_evidence_edge(_meaning("risk", MeaningDirection.RISK))
        contradictions = detect_contradictions((support, risk), min_edge_weight=0.01)
        self.assertEqual(len(contradictions), 1)
        self.assertTrue(contradictions[0].resolution_required)


if __name__ == "__main__":
    unittest.main()
