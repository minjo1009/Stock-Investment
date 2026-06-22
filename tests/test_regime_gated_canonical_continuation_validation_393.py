from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_regime_gated_canonical_continuation_validation_393 import (
    build_regime_gated_canonical_continuation_validation_393,
)


class TestRegimeGatedCanonicalContinuationValidation393(unittest.TestCase):
    def test_regime_gates_reduce_validation_collapse_without_inference(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            panel = root / "lifecycle_regime_panel.csv"
            _write_fixture(panel)

            artifacts = build_regime_gated_canonical_continuation_validation_393(
                task392_lifecycle_regime_panel_path=panel,
                out_dir=root / "out",
            )

            decision = artifacts.task_393_decision.iloc[0]
            self.assertEqual(str(decision["task_393_verdict"]), "COMPLETE_PASS")
            self.assertEqual(str(decision["evaluation_status"]), "REGIME_GATE_DIAGNOSTIC_COMPLETE")
            self.assertEqual(int(decision["reconstruction_used_flag"]), 0)
            self.assertEqual(int(decision["symbol_session_inference_used_flag"]), 0)
            self.assertEqual(int(decision["threshold_relaxation_flag"]), 0)
            self.assertEqual(int(decision["deployment_claim_flag"]), 0)

            gated = artifacts.regime_gated_lifecycle_panel
            self.assertIn("strict_regime_gate_flag", gated.columns)
            self.assertGreater(int(gated["strict_regime_gate_flag"].sum()), 0)

            audit = artifacts.regime_gate_validation_audit
            risk_on = audit[audit["gate_name"].eq("risk_on_gate")].iloc[0]
            self.assertEqual(int(risk_on["diagnostic_gate_pass_flag"]), 1)
            self.assertGreater(float(risk_on["validation_avg_lift_vs_ungated"]), 0.0)

            split = artifacts.gate_split_quality
            baseline_val = split[
                split["gate_name"].eq("ungated_baseline") & split["anchored_split"].eq("validation")
            ].iloc[0]
            risk_on_val = split[
                split["gate_name"].eq("risk_on_gate") & split["anchored_split"].eq("validation")
            ].iloc[0]
            self.assertLess(float(baseline_val["avg_return_from_entry"]), 0.0)
            self.assertGreater(float(risk_on_val["avg_return_from_entry"]), 0.0)

            self.assertTrue((root / "out" / "task_393_regime_gated_canonical_continuation_validation.md").exists())
            self.assertTrue((root / "out" / "gate_monthly_quality.csv").exists())


def _write_fixture(path: Path) -> None:
    rows = []
    for split in ["train", "validation", "recent_oos"]:
        for idx in range(220):
            good_regime = idx < 120
            if split == "validation" and not good_regime:
                ret = -0.03
            elif split == "validation":
                ret = 0.02
            elif split == "recent_oos" and good_regime:
                ret = 0.018
            elif split == "recent_oos":
                ret = -0.005
            elif good_regime:
                ret = 0.015
            else:
                ret = -0.006
            rows.append(
                {
                    "lifecycle_id": f"L-{split}-{idx}",
                    "symbol": "NVDA" if good_regime else "MSFT",
                    "entry_ts": f"2026-01-{(idx % 20) + 1:02d}T14:30:00Z",
                    "exit_ts": f"2026-01-{(idx % 20) + 1:02d}T18:30:00Z",
                    "bars_held": 16,
                    "add_flag": 1 if good_regime else 0,
                    "scale_flag": 1 if good_regime else 0,
                    "reduce_flag": 0 if good_regime else 1,
                    "exit_reason": "intraday_time_exit" if good_regime else "intraday_drawdown_exit",
                    "return_from_entry": ret,
                    "theme": "ai_semiconductors" if good_regime else "cloud_ai_platforms",
                    "role": "leader",
                    "lifecycle_path": "ENTRY_ADD_SCALE_EXIT" if good_regime else "ENTRY_REDUCE_EXIT",
                    "positive_return_flag": 1 if ret > 0 else 0,
                    "add_scale_flag": 1 if good_regime else 0,
                    "anchored_split": split,
                    "entry_date": f"2026-01-{(idx % 20) + 1:02d}",
                    "breadth_regime": "broad_participation" if good_regime else "weak_breadth",
                    "volatility_regime": "high_vol" if good_regime else "mid_vol",
                    "liquidity_regime": "liquidity_expansion" if good_regime else "liquidity_tightening",
                    "market_regime": "risk_on_broad" if good_regime else "risk_off_weak",
                    "theme_day_return": 0.02 if good_regime else -0.01,
                    "theme_rank": 1 if good_regime else 8,
                    "theme_leadership_regime": "theme_leader" if good_regime else "theme_laggard",
                    "breadth_positive_rate": 0.7 if good_regime else 0.3,
                    "avg_intraday_range": 0.03,
                    "liquidity_ratio_20d": 1.2 if good_regime else 0.8,
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    unittest.main()
