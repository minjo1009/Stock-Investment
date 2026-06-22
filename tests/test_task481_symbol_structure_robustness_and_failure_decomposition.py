from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task481_symbol_structure_robustness_and_failure_decomposition import (
    build_task481_symbol_structure_robustness_and_failure_decomposition,
)


class TestTask481SymbolStructureRobustnessAndFailureDecomposition(unittest.TestCase):
    def test_task481_generates_decomposition_without_label_overwrite(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            task480 = root / "task480"
            out = root / "out"
            task480.mkdir()
            snapshot_rows = []
            for i in range(80):
                outcome = "add_scale_success" if i < 30 else "entry_reduce_failure" if i < 55 else "add_only_weak"
                snapshot_rows.append(
                    {
                        "lifecycle_id": f"L{i}",
                        "entry_decision_id": f"D{i}",
                        "symbol": "AAA" if i < 60 else "BBB",
                        "theme_id": "theme_a" if i < 60 else "theme_b",
                        "entry_ts": f"2026-01-{1 + (i % 20):02d}T16:00:00Z",
                        "exit_ts": f"2026-01-{1 + (i % 20):02d}T18:00:00Z",
                        "lifecycle_outcome_class": outcome,
                        "event_path": "ENTRY_ADD_SCALE_EXIT" if outcome == "add_scale_success" else "ENTRY_REDUCE_EXIT",
                        "add_flag": int(outcome != "entry_reduce_failure"),
                        "scale_flag": int(outcome == "add_scale_success"),
                        "reduce_flag": int(outcome == "entry_reduce_failure"),
                        "exit_flag": 1,
                        "return_from_entry": 0.02 if outcome == "add_scale_success" else -0.01 if outcome == "entry_reduce_failure" else 0.004,
                        "net_return_from_entry": 0.017 if outcome == "add_scale_success" else -0.013 if outcome == "entry_reduce_failure" else 0.001,
                        "entry_bar_quality_state": "mixed_bar",
                        "breakout_structure_state": "overextended_breakout" if i < 40 else "thin_breakout",
                        "momentum_structure_state": "steady_momentum" if i < 40 else "one_bar_pop",
                        "pullback_reclaim_state": "upper_range_hold" if i < 40 else "failed_reclaim",
                        "volatility_structure_state": "exhaustion_extension" if i < 40 else "shock_bar",
                        "volume_confirmation_state": "volume_climax" if i < 40 else "quiet_breakout",
                        "vwap_acceptance_state": "below_or_at_vwap",
                        "timing_state": "midday_continuation",
                        "inferred_lifecycle_matching_used_flag": 0,
                        "symbol_date_price_time_fallback_used_flag": 0,
                    }
                )
            snapshot = pd.DataFrame(snapshot_rows)
            good_bad = pd.DataFrame(
                [
                    {
                        "interaction_family": "entry_breakout_volume",
                        "configuration": "mixed_bar x overextended_breakout x volume_climax",
                        "configuration_class": "good_candidate",
                        "lifecycle_count": 40,
                        "avg_net_return_pct": 1.0,
                    }
                ]
            )
            snapshot.to_csv(task480 / "symbol_structure_snapshot_log.csv", index=False)
            good_bad.to_csv(task480 / "good_bad_configuration_audit.csv", index=False)

            artifacts = build_task481_symbol_structure_robustness_and_failure_decomposition(
                task480_dir=task480,
                out_dir=out,
            )

            self.assertEqual(int(artifacts.task_481_decision["label_overwrite_flag"].iloc[0]), 0)
            self.assertEqual(int(artifacts.task_481_decision["inferred_lifecycle_matching_used_flag"].iloc[0]), 0)
            self.assertGreater(len(artifacts.overextension_quality_audit), 0)
            self.assertGreater(len(artifacts.top_config_split_quality), 0)
            self.assertGreater(len(artifacts.add_only_weak_decomposition), 0)
            self.assertGreater(len(artifacts.entry_reduce_failure_root_cause_audit), 0)
            self.assertIn("policy_candidate_name", artifacts.policy_candidate_backtest_diagnostic.columns)
            self.assertTrue((out / "task_481_symbol_structure_robustness_and_failure_decomposition.md").exists())


if __name__ == "__main__":
    unittest.main()
