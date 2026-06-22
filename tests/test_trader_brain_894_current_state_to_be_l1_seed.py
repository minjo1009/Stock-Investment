from __future__ import annotations

import csv
import unittest
from pathlib import Path

from scripts.trader_brain_894_current_state_to_be_l1_seed_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_894_current_state_to_be_l1_seed"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain894CurrentStateToBeL1SeedTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_symbol_coverage_has_70_symbols(self) -> None:
        coverage = rows("source_time_symbol_coverage_matrix.csv")
        self.assertEqual(70, len(coverage))
        self.assertEqual(70, len({row["symbol"] for row in coverage}))
        self.assertTrue(any(row["coverage_state"] == "l1_seed_available" for row in coverage))
        self.assertTrue(any(row["coverage_state"] == "missing_l1_source_seed" for row in coverage))

    def test_l1_seed_does_not_generate_l2_l3_or_trades(self) -> None:
        l1_states = rows("l1_source_evidence_seed_state.csv")
        self.assertGreater(len(l1_states), 0)
        forbidden = {"side", "entry", "exit", "position_size", "rank", "score"}
        self.assertTrue(forbidden.isdisjoint(l1_states[0].keys()))
        self.assertEqual({"not_generated"}, {row["primitive_fact_state"] for row in l1_states})
        self.assertEqual({"not_generated"}, {row["economic_meaning_state"] for row in l1_states})
        self.assertEqual({"not_generated"}, {row["relation_state"] for row in l1_states})

    def test_decision_panel_is_asof_grid(self) -> None:
        panel = rows("source_time_decision_coverage_panel.csv")
        self.assertEqual(4410, len(panel))
        self.assertTrue(all("trade signal" in row["does_not_mean"] for row in panel))


if __name__ == "__main__":
    unittest.main()
