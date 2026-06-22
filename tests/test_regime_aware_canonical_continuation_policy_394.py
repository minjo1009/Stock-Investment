from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_regime_aware_canonical_continuation_policy_394 import (
    build_regime_aware_canonical_continuation_policy_394,
)


class TestRegimeAwareCanonicalContinuationPolicy394(unittest.TestCase):
    def test_regime_policy_blocks_weak_scale_and_preserves_canonical_flags(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            panel = root / "lifecycle_regime_panel.csv"
            _write_fixture(panel)

            artifacts = build_regime_aware_canonical_continuation_policy_394(
                task392_lifecycle_regime_panel_path=panel,
                out_dir=root / "out",
            )

            decision = artifacts.task_394_decision.iloc[0]
            self.assertEqual(str(decision["task_394_verdict"]), "COMPLETE_PASS")
            self.assertEqual(str(decision["evaluation_status"]), "REGIME_AWARE_POLICY_DIAGNOSTIC_COMPLETE")
            self.assertEqual(int(decision["reconstruction_used_flag"]), 0)
            self.assertEqual(int(decision["symbol_session_inference_used_flag"]), 0)
            self.assertEqual(int(decision["threshold_relaxation_flag"]), 0)
            self.assertEqual(int(decision["deployment_claim_flag"]), 0)

            simulation = artifacts.policy_lifecycle_simulation_panel
            new_policy = simulation[simulation["policy_name"].eq("new_regime_aware_policy")]
            weak_scaled = new_policy[(new_policy["weak_regime_flag"].eq(1)) & (new_policy["scale_flag"].eq(1))]
            self.assertTrue((weak_scaled["policy_accepted_lifecycle_flag"] == 0).all())
            self.assertTrue((weak_scaled["policy_scale_allowed_flag"] == 0).all())

            audit = artifacts.policy_validation_audit
            policy = audit[audit["policy_name"].eq("new_regime_aware_policy")].iloc[0]
            self.assertEqual(int(policy["policy_diagnostic_pass_flag"]), 1)
            self.assertGreater(float(policy["validation_avg_lift_vs_ungated"]), 0.0)
            self.assertGreater(float(policy["recent_oos_avg_return"]), 0.0)

            self.assertTrue((root / "out" / "regime_policy_rulebook.csv").exists())
            self.assertTrue((root / "out" / "task_394_regime_aware_canonical_continuation_policy.md").exists())


def _write_fixture(path: Path) -> None:
    rows = []
    for split in ["train", "validation", "recent_oos"]:
        for idx in range(260):
            strict = idx < 110
            constrained = 110 <= idx < 160
            weak = idx >= 160
            if strict:
                ret = 0.018 if split != "recent_oos" else 0.02
                add = scale = 1
                reduce = 0
                market = "risk_on_broad"
                breadth = "broad_participation"
                liquidity = "liquidity_expansion"
                leadership = "theme_leader"
            elif constrained:
                ret = 0.004
                add = 1
                scale = 0
                reduce = 1
                market = "mixed_market"
                breadth = "mixed_breadth"
                liquidity = "liquidity_neutral"
                leadership = "theme_middle"
            else:
                ret = -0.025 if split == "validation" else -0.01
                add = 1
                scale = 1
                reduce = 1
                market = "risk_off_weak"
                breadth = "weak_breadth"
                liquidity = "liquidity_tightening"
                leadership = "theme_laggard"
            rows.append(
                {
                    "lifecycle_id": f"L-{split}-{idx}",
                    "symbol": "NVDA",
                    "entry_ts": f"2026-01-{(idx % 20) + 1:02d}T14:30:00Z",
                    "exit_ts": f"2026-01-{(idx % 20) + 1:02d}T18:30:00Z",
                    "bars_held": 16,
                    "add_flag": add,
                    "scale_flag": scale,
                    "reduce_flag": reduce,
                    "exit_reason": "intraday_time_exit",
                    "return_from_entry": ret,
                    "theme": "ai_semiconductors",
                    "role": "leader",
                    "lifecycle_path": "ENTRY_ADD_SCALE_EXIT" if scale else "ENTRY_ADD_REDUCE_EXIT",
                    "positive_return_flag": 1 if ret > 0 else 0,
                    "add_scale_flag": 1 if add and scale else 0,
                    "anchored_split": split,
                    "entry_date": f"2026-01-{(idx % 20) + 1:02d}",
                    "breadth_regime": breadth,
                    "volatility_regime": "high_vol",
                    "liquidity_regime": liquidity,
                    "market_regime": market,
                    "theme_day_return": 0.02,
                    "theme_rank": 1 if leadership == "theme_leader" else 8,
                    "theme_leadership_regime": leadership,
                    "breadth_positive_rate": 0.7 if not weak else 0.3,
                    "avg_intraday_range": 0.03,
                    "liquidity_ratio_20d": 1.2,
                }
            )
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    unittest.main()
