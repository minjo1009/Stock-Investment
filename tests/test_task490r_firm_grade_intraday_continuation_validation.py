from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task490r_firm_grade_intraday_continuation_validation import (
    BLOCKED_ASSIGNMENT_FIELDS,
    build_task490r_firm_grade_intraday_continuation_validation,
)


class Task490RFirmGradeIntradayContinuationValidationTest(unittest.TestCase):
    def test_task490r_uses_exact_lifecycle_and_reports_missing_microstructure(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            panel_path = root / "task487_panel.csv"
            market_path = root / "broad_market.csv"
            selected_cells_path = root / "task489_selected_cells.csv"
            out_dir = root / "out"

            dates = pd.date_range("2024-01-01", periods=60).strftime("%Y-%m-%d")
            market = pd.DataFrame(
                {
                    "score_date": dates,
                    "broad_market_score": [40 + (idx % 5) for idx in range(60)],
                    "broad_market_stress": [30 + (idx % 5) for idx in range(60)],
                }
            )
            market.to_csv(market_path, index=False)
            pd.DataFrame(
                {
                    "cell_dims": ["broad_market_score"] * 5,
                    "cell_values": [str(idx) for idx in range(5)],
                    "selected_cell_order": [1, 2, 3, 4, 5],
                }
            ).to_csv(selected_cells_path, index=False)

            rows = []
            for idx in range(140):
                raw = {
                    "forward_live_breadth_positive_rate": 0.60 + (idx % 5) * 0.01,
                    "forward_live_avg_symbol_return": 0.01,
                    "forward_live_liquidity_ratio": 1.0,
                    "forward_live_theme_breadth_positive_rate": 0.65,
                    "forward_live_theme_return": 0.01 + (idx % 5) * 0.001,
                    "forward_live_theme_rank": 2,
                }
                good = idx % 4 != 0
                rows.append(
                    {
                        "lifecycle_id": f"L{idx}",
                        "symbol": f"S{idx % 7}",
                        "theme_id": "theme_a" if idx % 3 else "theme_b",
                        "entry_ts": pd.Timestamp("2024-01-01") + pd.Timedelta(days=idx),
                        "score_date": dates[idx % len(dates)],
                        "exact_regime_join_flag": 1,
                        "raw_factors_json": json.dumps(raw),
                        "payoff_theme_score": 50 + (idx % 5),
                        "payoff_theme_stress_score": 25 + (idx % 5),
                        "entry_bar_quality_state": "mixed_bar",
                        "breakout_structure_state": "overextended_breakout",
                        "momentum_structure_state": "exhaustion_extension" if idx % 2 else "momentum_sustain",
                        "pullback_reclaim_state": "no_pullback",
                        "volatility_structure_state": "healthy_expansion",
                        "volume_confirmation_state": "volume_climax",
                        "vwap_acceptance_state": "above_vwap",
                        "timing_state": "midday_continuation",
                        "net_return_from_entry": 0.04 if good else -0.02,
                        "win_flag": int(good),
                        "add_scale_success_flag": int(good),
                        "entry_reduce_failure_flag": int(not good),
                        "false_positive_flag": int(not good),
                        "quarter": "2024Q1",
                    }
                )
            pd.DataFrame(rows).to_csv(panel_path, index=False)

            artifacts = build_task490r_firm_grade_intraday_continuation_validation(
                task487_panel_path=panel_path,
                task489_selected_cells_path=selected_cells_path,
                broad_market_cache=market_path,
                broad_daily_dir=root / "missing",
                out_dir=out_dir,
            )

            self.assertTrue((out_dir / "task_490r_firm_grade_intraday_continuation_validation.md").exists())
            self.assertTrue((out_dir / "firm_grade_intraday_cost_stress_quality.csv").exists())
            self.assertGreaterEqual(len(artifacts.firm_grade_intraday_archetype_rulebook), 1)
            leakage = artifacts.firm_grade_intraday_leakage_audit.iloc[0]
            self.assertEqual(int(leakage["leakage_pass_flag"]), 1)
            self.assertEqual(int(leakage["inferred_lifecycle_matching_used_flag"]), 0)
            self.assertEqual(int(leakage["missing_raw_source_approximated_flag"]), 0)
            self.assertIn("quote", str(leakage["missing_raw_sources_reported"]))
            assignment_fields = set(str(leakage["assignment_fields"]).split("|"))
            self.assertFalse(assignment_fields & BLOCKED_ASSIGNMENT_FIELDS)
            decision = artifacts.task_decision.iloc[0]
            self.assertGreaterEqual(int(decision["recent_oos_count"]), 1)


if __name__ == "__main__":
    unittest.main()
