from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_forward_live_regime_detectability_395 import (
    build_forward_live_regime_detectability_395,
)


class TestForwardLiveRegimeDetectability395(unittest.TestCase):
    def test_forward_live_strict_gate_uses_entry_available_intraday_state(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            intraday = root / "intraday"
            intraday.mkdir()
            panel = root / "lifecycle_regime_panel.csv"
            _write_intraday_fixture(intraday)
            _write_lifecycle_fixture(panel)

            artifacts = build_forward_live_regime_detectability_395(
                intraday_dir=intraday,
                task392_lifecycle_regime_panel_path=panel,
                out_dir=root / "out",
            )

            decision = artifacts.task_395_decision.iloc[0]
            self.assertEqual(str(decision["task_395_verdict"]), "COMPLETE_PASS")
            self.assertEqual(str(decision["evaluation_status"]), "FORWARD_LIVE_REGIME_DETECTABILITY_DIAGNOSTIC_COMPLETE")
            self.assertEqual(int(decision["full_day_regime_used_flag"]), 0)
            self.assertEqual(int(decision["future_outcome_used_for_regime_flag"]), 0)
            self.assertEqual(int(decision["symbol_session_inference_used_flag"]), 0)
            self.assertEqual(int(decision["forward_live_gate_diagnostic_pass_flag"]), 1)

            lifecycle = artifacts.forward_live_lifecycle_regime_panel
            self.assertIn("forward_live_strict_regime_gate_flag", lifecycle.columns)
            self.assertGreater(int(lifecycle["forward_live_strict_regime_gate_flag"].sum()), 0)

            leakage = artifacts.forward_live_leakage_audit
            blocked = leakage[leakage["allowed"].eq(0)]
            self.assertTrue((blocked["used_for_forward_live_regime"] == 0).all())
            self.assertTrue((root / "out" / "task_395_forward_live_regime_detectability.md").exists())


def _write_intraday_fixture(intraday: Path) -> None:
    symbols = ["NVDA", "AMD", "MSFT", "AAPL"]
    for day in range(1, 8):
        for symbol in symbols:
            rows = []
            base = 100.0
            for minute, close in [
                (30, base),
                (45, base * (1.03 if symbol != "AAPL" else 0.99)),
                (60, base * (0.97 if symbol != "AAPL" else 1.01)),
            ]:
                ts = pd.Timestamp(f"2026-01-{day:02d}T14:{minute % 60:02d}:00Z")
                if minute == 60:
                    ts = pd.Timestamp(f"2026-01-{day:02d}T15:00:00Z")
                rows.append(
                    {
                        "timestamp": ts.isoformat().replace("+00:00", "Z"),
                        "open": base,
                        "high": max(base, close),
                        "low": min(base, close),
                        "close": close,
                        "volume": 1000 + day,
                    }
                )
            existing = intraday / f"{symbol}.csv"
            frame = pd.DataFrame(rows)
            if existing.exists():
                frame = pd.concat([pd.read_csv(existing), frame], ignore_index=True)
            frame.to_csv(existing, index=False, encoding="utf-8-sig")


def _write_lifecycle_fixture(panel: Path) -> None:
    rows = []
    for split in ["train", "validation", "recent_oos"]:
        for idx in range(160):
            strict = idx < 110
            day = (idx % 7) + 1
            entry_ts = f"2026-01-{day:02d}T14:45:00Z" if strict else f"2026-01-{day:02d}T15:00:00Z"
            ret = 0.02 if strict else -0.02
            rows.append(
                {
                    "lifecycle_id": f"L-{split}-{idx}",
                    "symbol": "NVDA" if strict else "MSFT",
                    "entry_ts": entry_ts,
                    "exit_ts": entry_ts,
                    "bars_held": 4,
                    "add_flag": 1 if strict else 0,
                    "scale_flag": 1 if strict else 0,
                    "reduce_flag": 0 if strict else 1,
                    "exit_reason": "fixture",
                    "return_from_entry": ret,
                    "theme": "ai_semiconductors" if strict else "cloud_ai_platforms",
                    "role": "fixture",
                    "lifecycle_path": "ENTRY_ADD_SCALE_EXIT" if strict else "ENTRY_REDUCE_EXIT",
                    "positive_return_flag": 1 if ret > 0 else 0,
                    "add_scale_flag": 1 if strict else 0,
                    "anchored_split": split,
                    "entry_date": f"2026-01-{day:02d}",
                    "breadth_regime": "broad_participation" if strict else "weak_breadth",
                    "volatility_regime": "high_vol",
                    "liquidity_regime": "liquidity_neutral",
                    "market_regime": "risk_on_broad" if strict else "risk_off_weak",
                    "theme_day_return": 0.02 if strict else -0.01,
                    "theme_rank": 1 if strict else 8,
                    "theme_leadership_regime": "theme_leader" if strict else "theme_laggard",
                    "breadth_positive_rate": 0.75 if strict else 0.25,
                    "avg_intraday_range": 0.03,
                    "liquidity_ratio_20d": 1.0,
                }
            )
    pd.DataFrame(rows).to_csv(panel, index=False, encoding="utf-8-sig")


if __name__ == "__main__":
    unittest.main()
