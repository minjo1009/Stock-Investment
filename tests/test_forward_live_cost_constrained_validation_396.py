from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_forward_live_cost_constrained_validation_396 import (
    build_forward_live_cost_constrained_validation_396,
)


class TestForwardLiveCostConstrainedValidation396(unittest.TestCase):
    def test_cost_constrained_forward_live_edge_survives_with_capital_slots(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            panel = root / "forward_live_lifecycle_regime_panel.csv"
            _write_fixture(panel, max_concurrent_positions=20)

            artifacts = build_forward_live_cost_constrained_validation_396(
                task395_lifecycle_panel_path=panel,
                out_dir=root / "out",
                max_concurrent_positions=20,
            )

            decision = artifacts.task_396_decision.iloc[0]
            self.assertEqual(str(decision["task_396_verdict"]), "COMPLETE_PASS")
            self.assertEqual(str(decision["evaluation_status"]), "COST_CONSTRAINED_FORWARD_LIVE_DIAGNOSTIC_COMPLETE")
            self.assertEqual(int(decision["full_day_regime_used_for_realistic_policy_flag"]), 0)
            self.assertEqual(int(decision["symbol_session_inference_used_flag"]), 0)
            self.assertEqual(int(decision["deployment_claim_flag"]), 0)

            exposure = artifacts.capital_exposure_audit[
                artifacts.capital_exposure_audit["policy_name"].eq("cost_constrained_forward_live_strict")
            ].iloc[0]
            self.assertLessEqual(int(exposure["max_concurrent_accepted_entries"]), 20)
            self.assertGreaterEqual(int(exposure["capital_blocked_count"]), 1)

            transition = artifacts.cost_constrained_transition_quality
            add_scale = transition[
                transition["policy_name"].eq("cost_constrained_forward_live_strict")
                & transition["anchored_split"].eq("validation")
                & transition["reinforcement_group"].eq("add_scale")
            ].iloc[0]
            self.assertGreater(float(add_scale["avg_net_return_from_entry"]), 0.0)
            baseline = artifacts.cost_constrained_split_quality[
                artifacts.cost_constrained_split_quality["policy_name"].eq("ungated_baseline")
                & artifacts.cost_constrained_split_quality["anchored_split"].eq("validation")
            ].iloc[0]
            constrained = artifacts.cost_constrained_split_quality[
                artifacts.cost_constrained_split_quality["policy_name"].eq("cost_constrained_forward_live_strict")
                & artifacts.cost_constrained_split_quality["anchored_split"].eq("validation")
            ].iloc[0]
            self.assertGreater(float(constrained["avg_net_return_from_entry"]), float(baseline["avg_net_return_from_entry"]))

            self.assertTrue((root / "out" / "task_396_forward_live_cost_constrained_validation.md").exists())


def _write_fixture(path: Path, max_concurrent_positions: int = 20) -> None:
    rows = []
    for split in ["train", "validation", "recent_oos"]:
        for idx in range(220):
            live = idx < 150
            timestamp_bucket = idx % 40
            ret = 0.018 if live else -0.01
            rows.append(
                {
                    "lifecycle_id": f"L-{split}-{idx}",
                    "symbol": f"S{idx % 12}",
                    "entry_ts": f"2026-01-{(timestamp_bucket % 10) + 1:02d}T14:{30 + (timestamp_bucket % 2) * 15:02d}:00Z",
                    "exit_ts": f"2026-01-{(timestamp_bucket % 10) + 1:02d}T18:30:00Z",
                    "bars_held": 12,
                    "add_flag": 1 if live else 0,
                    "scale_flag": 1 if live else 0,
                    "reduce_flag": 0 if live else 1,
                    "exit_reason": "fixture",
                    "return_from_entry": ret,
                    "theme": "ai_semiconductors" if live else "cloud_ai_platforms",
                    "role": "fixture",
                    "lifecycle_path": "ENTRY_ADD_SCALE_EXIT" if live else "ENTRY_REDUCE_EXIT",
                    "positive_return_flag": 1 if ret > 0 else 0,
                    "add_scale_flag": 1 if live else 0,
                    "anchored_split": split,
                    "hindsight_strict_regime_gate_flag": 1 if live else 0,
                    "forward_live_strict_regime_gate_flag": 1 if live else 0,
                    "forward_live_avg_intraday_range": 0.01,
                    "forward_live_liquidity_ratio": 1.2 if live else 0.8,
                    "forward_live_theme_rank": (idx % 12) + 1,
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    unittest.main()
