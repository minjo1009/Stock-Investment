from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1191_1200_l0_l3_candidate_compression_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1191_1200_l0_l3_candidate_compression"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain11911200L0L3CandidateCompressionTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_l0_filters_are_nontrivial_and_no_future(self) -> None:
        l0 = rows("task1191_l0_security_filter.csv")
        pass_count = sum(1 for row in l0 if row["l0_tradable_pass"] == "1")
        self.assertGreater(pass_count, 1000)
        self.assertLess(pass_count, len(l0))
        self.assertEqual({"0"}, {row["assignment_uses_future_outcome"] for row in l0[:500]})

    def test_l3_edges_and_candidates_exist(self) -> None:
        l0 = rows("task1191_l0_security_filter.csv")
        edges = rows("task1196_l3_relation_edges.csv")
        self.assertEqual(len(l0) * 4, len(edges))
        candidates = rows("task1197_compressed_candidates.csv")
        self.assertGreater(len(candidates), 0)
        self.assertEqual({"0"}, {row["assignment_uses_future_outcome"] for row in candidates[:500]})

    def test_negative_fixtures_are_blocked(self) -> None:
        negatives = rows("task1198_negative_fixtures.csv")
        self.assertGreaterEqual(len(negatives), 10)
        self.assertEqual({"0"}, {row["appears_in_compressed_candidates"] for row in negatives})

    def test_closeout_statuses_are_unchanged(self) -> None:
        closeout = json.loads((ART / "task1200_l0_l3_candidate_compression_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("0", closeout["replay_executed"])
        self.assertEqual("0", closeout["selection_promoted"])
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
