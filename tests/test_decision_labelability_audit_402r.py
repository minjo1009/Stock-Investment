from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_decision_labelability_audit_402r import build_decision_labelability_audit_402r


class TestDecisionLabelabilityAudit402R(unittest.TestCase):
    def test_exact_overlap_and_unlabeled_are_separated(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            decisions = root / "task401.csv"
            labels = root / "labels.csv"
            pd.DataFrame(
                [
                    _decision("D1", "L1", "ALLOW"),
                    _decision("D2", "L2", "ALLOW"),
                    _decision("D3", "", "REJECT"),
                ]
            ).to_csv(decisions, index=False, encoding="utf-8-sig")
            pd.DataFrame(
                [
                    {"lifecycle_id": "L1", "failure_group": "add_scale_success"},
                    {"lifecycle_id": "OTHER", "failure_group": "entry_reduce_failure"},
                ]
            ).to_csv(labels, index=False, encoding="utf-8-sig")

            artifacts = build_decision_labelability_audit_402r(
                task401_entry_candidates_path=decisions,
                label_source_path=labels,
                out_dir=root / "out",
            )

            pop = artifacts.population_consistency_audit.iloc[0]
            self.assertEqual(int(pop["exact_lifecycle_id_overlap_count"]), 1)
            self.assertEqual(int(pop["symbol_date_price_time_fallback_used_flag"]), 0)
            self.assertEqual(int(pop["unlabeled_treated_as_negative_flag"]), 0)

            unlabeled = artifacts.unlabeled_candidate_audit
            self.assertIn("L2", set(unlabeled["lifecycle_id"].astype(str)))
            self.assertIn("non_lifecycle_candidate", set(unlabeled["label_status"].astype(str)))
            self.assertTrue((root / "out" / "task_402r_decision_labelability_audit.md").exists())


def _decision(decision_id: str, lifecycle_id: str, bucket: str) -> dict:
    return {
        "decision_id": decision_id,
        "candidate_id": f"C|{decision_id}",
        "lifecycle_id": lifecycle_id,
        "bucket": bucket,
        "symbol": "AAA",
        "theme_id": "theme",
        "decision_ts_utc": "2026-01-01T15:00:00Z",
    }


if __name__ == "__main__":
    unittest.main()
