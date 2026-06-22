from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task576_microstructure_aware_continuation_backtest import build_task576


class Task576MicrostructureAwareContinuationBacktestTest(unittest.TestCase):
    def test_microstructure_candidates_use_entry_safe_fields_and_not_live_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task573 = root / "task573.csv"
            task567 = root / "task567.csv"
            pd.DataFrame(
                [
                    {
                        "lifecycle_id": "L1",
                        "quote_match_available_flag": 1,
                        "spread_bps": 4.0,
                        "nbbo_size_dollar": 100000.0,
                        "nbbo_imbalance": 0.1,
                        "pullback_sleeve_v1": "controlled_pullback_only",
                        "net_return_from_entry": 0.05,
                        "win_flag": 1,
                        "entry_reduce_failure_flag": 0,
                        "add_scale_success_flag": 1,
                        "split_name": "validation",
                        "quarter": "2026Q1",
                        "inferred_lifecycle_matching_used_flag_micro": 0,
                        "symbol_date_price_time_fallback_used_flag": 0,
                    },
                    {
                        "lifecycle_id": "L2",
                        "quote_match_available_flag": 1,
                        "spread_bps": 80.0,
                        "nbbo_size_dollar": 1000.0,
                        "nbbo_imbalance": -0.8,
                        "pullback_sleeve_v1": "near_high_absorption_only",
                        "net_return_from_entry": -0.02,
                        "win_flag": 0,
                        "entry_reduce_failure_flag": 1,
                        "add_scale_success_flag": 0,
                        "split_name": "recent_oos",
                        "quarter": "2026Q2",
                        "inferred_lifecycle_matching_used_flag_micro": 0,
                        "symbol_date_price_time_fallback_used_flag": 0,
                    },
                ]
            ).to_csv(task573, index=False)
            pd.DataFrame(
                [
                    {"lifecycle_id": "L1", "capital_flow_regime_v6": "capital_flow_expansion", "capital_flow_score_v6": 1.0},
                    {"lifecycle_id": "L2", "capital_flow_regime_v6": "capital_flow_expansion", "capital_flow_score_v6": 1.0},
                ]
            ).to_csv(task567, index=False)
            artifacts = build_task576(task573, task567)
            panel = artifacts["task576_microstructure_assignment_panel.csv"]
            decision = artifacts["task_576_decision.csv"].iloc[0]
            self.assertEqual(int(panel["microstructure_assignment_used_outcome_flag"].max()), 0)
            self.assertEqual(int(panel["historical_microstructure_live_ready_flag"].max()), 0)
            self.assertEqual(decision["strategy_acceptance_status"], "DIAGNOSTIC_PASS_MICROSTRUCTURE_AWARE_BACKTESTED")
            self.assertGreater(len(artifacts["task576_candidate_set_quality.csv"]), 0)


if __name__ == "__main__":
    unittest.main()
