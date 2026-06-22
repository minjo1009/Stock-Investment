from __future__ import annotations

import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_1408_1427_ruler_acquisition_replay"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


class Task1408To1427RulerAcquisitionReplayTest(unittest.TestCase):
    def test_core_panel_shapes(self) -> None:
        self.assertEqual(len(read_csv(OUT_DIR / "task1410_companyfacts_denominator_panel.csv")), 3100)
        self.assertEqual(len(read_csv(OUT_DIR / "task1413_materiality_ruler_panel.csv")), 3100)
        self.assertEqual(len(read_csv(OUT_DIR / "task1424_integrated_ruler_panel.csv")), 3100)
        self.assertEqual(len(read_csv(OUT_DIR / "task1425_payoff_ranker_v3.csv")), 3100)

    def test_missing_denominator_does_not_raise_materiality(self) -> None:
        denom = {row["candidate_source_id"]: row for row in read_csv(OUT_DIR / "task1410_companyfacts_denominator_panel.csv")}
        materiality = read_csv(OUT_DIR / "task1413_materiality_ruler_panel.csv")
        for row in materiality:
            if denom[row["candidate_source_id"]]["denominator_source_gap"] == "1":
                self.assertEqual(row["materiality_ruler_state"], "materiality_source_gap")
                self.assertEqual(float(row["materiality_ruler_score"]), 0.0)

    def test_policy_counts_and_status(self) -> None:
        specs = read_csv(OUT_DIR / "task1426_policy_specs.csv")
        counts: dict[str, int] = {}
        for row in specs:
            counts[row["policy_variant_id"]] = counts.get(row["policy_variant_id"], 0) + 1
            self.assertEqual(row["assignment_uses_future_outcome"], "0")
        self.assertEqual(counts, {"ruler_top3_v1": 186, "ruler_top5_v1": 310, "ruler_top10_v1": 620})
        metrics = read_csv(OUT_DIR / "task1426_replay_metrics.csv")
        self.assertEqual(len(metrics), 3)
        for row in metrics:
            self.assertEqual(row["strategy_acceptance"], "NOT_ACCEPTED")
            self.assertEqual(row["deployment_readiness"], "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
            self.assertEqual(row["real_capital"], "FORBIDDEN")

    def test_exit_families_are_split(self) -> None:
        source_rows = read_csv(OUT_DIR / "task1421_source_receipt_exit_panel.csv")
        price_rows = read_csv(OUT_DIR / "task1422_price_path_risk_exit_panel.csv")
        self.assertTrue(any(row["source_receipt_exit_ready"] == "1" for row in source_rows))
        self.assertTrue(any(row["price_path_risk_exit_ready"] == "1" for row in price_rows))
        self.assertTrue(all(row["exit_family"] == "source_receipt_exit" for row in source_rows))
        self.assertTrue(all(row["exit_family"] == "price_path_risk_exit" for row in price_rows))


if __name__ == "__main__":
    unittest.main()
