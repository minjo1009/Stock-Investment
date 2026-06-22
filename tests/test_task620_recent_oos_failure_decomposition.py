from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task620_recent_oos_failure_decomposition import (
    build_task620_recent_oos_failure_decomposition,
)


class Task620RecentOosFailureDecompositionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.artifacts = build_task620_recent_oos_failure_decomposition()

    def test_recent_oos_panel_is_decomposed(self) -> None:
        panel = self.artifacts["recent_oos_failure_taxonomy"]
        decision = self.artifacts["task_620_decision"].iloc[0]

        self.assertEqual(len(panel), 109)
        self.assertEqual(int(decision["recent_oos_trade_count"]), 109)
        self.assertTrue(panel["primary_failure_taxonomy"].notna().all())
        self.assertEqual(int(panel["label_used_in_assignment_flag"].max()), 0)

    def test_recent_oos_stability_gate_fails(self) -> None:
        decision = self.artifacts["task_620_decision"].iloc[0]
        pass_fail = self.artifacts["task_620_pass_fail_matrix"]
        perf = pass_fail[pass_fail["gate"].eq("recent_oos_performance")].iloc[0]

        self.assertEqual(decision["decision"], "FAIL_RECENT_OOS_STABILITY_SOURCE_FLAGS_TOO_BROAD")
        self.assertEqual(int(perf["pass_flag"]), 0)
        self.assertLess(float(decision["recent_oos_win_rate"]), 0.50)
        self.assertGreater(float(decision["recent_oos_entry_reduce_failure_rate"]), 0.40)

    def test_source_flags_are_too_broad_in_recent_oos(self) -> None:
        findings = self.artifacts["recent_oos_source_findings"]
        broad = findings[findings["finding"].astype(str).eq("too_broad_in_recent_oos")]

        self.assertGreaterEqual(len(broad), 4)
        self.assertTrue((broad["discrimination_possible_flag"].astype(int) == 0).any())

    def test_degradation_matrix_shows_aerospace_damage(self) -> None:
        degradation = self.artifacts["recent_oos_degradation_matrix"]
        row = degradation[
            degradation["dimension"].astype(str).eq("theme_id")
            & degradation["bucket"].astype(str).eq("aerospace_defense_space")
        ].iloc[0]

        self.assertLess(float(row["recent_avg_net_return_pct"]), 0.0)
        self.assertGreater(float(row["recent_entry_reduce_failure_rate"]), 0.90)

    def test_report_artifacts_are_written(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task620_recent_oos_failure_decomposition(out_dir=out_dir)

            self.assertTrue((out_dir / "task_620_recent_oos_failure_decomposition.md").exists())
            self.assertTrue((out_dir / "recent_oos_failure_taxonomy.csv").exists())
            self.assertTrue((out_dir / "task_620_decision.csv").exists())
            self.assertTrue((out_dir / "artifact_manifest.csv").exists())
            self.assertGreater(len(artifacts["recent_oos_failure_taxonomy_summary"]), 3)


if __name__ == "__main__":
    unittest.main()
