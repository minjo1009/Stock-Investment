from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_macro_vol_theme_regime_overlay_392 import (
    build_macro_vol_theme_regime_overlay_392,
)


class TestMacroVolThemeRegimeOverlay392(unittest.TestCase):
    def test_regime_overlay_uses_canonical_lifecycle_panel(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            intraday = root / "intraday"
            intraday.mkdir()
            themes = root / "themes.csv"
            panel = root / "panel.csv"
            _write_fixture(intraday, themes, panel)

            artifacts = build_macro_vol_theme_regime_overlay_392(
                intraday_dir=intraday,
                theme_universe_path=themes,
                task391_panel_path=panel,
                out_dir=root / "out",
            )

            decision = artifacts.task_392_decision.iloc[0]
            self.assertEqual(str(decision["task_392_verdict"]), "COMPLETE_PASS")
            self.assertEqual(int(decision["reconstruction_used_flag"]), 0)
            self.assertEqual(int(decision["symbol_session_inference_used_flag"]), 0)
            self.assertGreater(len(artifacts.daily_regime_panel), 0)
            self.assertIn("market_regime", artifacts.lifecycle_regime_panel.columns)
            self.assertTrue((root / "out" / "task_392_macro_vol_theme_regime_overlay.md").exists())


def _write_fixture(intraday: Path, themes: Path, panel: Path) -> None:
    pd.DataFrame(
        [
            {"theme": "ai_semiconductors", "symbol": "NVDA", "role": "gpu_leader"},
            {"theme": "cloud_ai_platforms", "symbol": "MSFT", "role": "cloud_leader"},
        ]
    ).to_csv(themes, index=False)
    for symbol, base in [("NVDA", 100.0), ("MSFT", 200.0)]:
        rows = []
        for day in range(1, 8):
            for bar in range(4):
                ts = pd.Timestamp(f"2026-01-{day:02d}T14:30:00Z") + pd.Timedelta(minutes=15 * bar)
                close = base + day + bar * (1 if symbol == "NVDA" else -0.2)
                rows.append({"timestamp": ts.isoformat().replace("+00:00", "Z"), "open": close - 0.1, "high": close + 0.2, "low": close - 0.2, "close": close, "volume": 1000 + day})
        pd.DataFrame(rows).to_csv(intraday / f"{symbol}.csv", index=False)
    pd.DataFrame(
        [
            {"lifecycle_id": "L1", "symbol": "NVDA", "entry_ts": "2026-01-02T14:45:00Z", "exit_ts": "2026-01-02T15:15:00Z", "bars_held": 2, "add_flag": 1, "scale_flag": 1, "reduce_flag": 0, "exit_reason": "intraday_time_exit", "return_from_entry": 0.03, "theme": "ai_semiconductors", "role": "gpu_leader", "lifecycle_path": "ENTRY_ADD_SCALE_EXIT", "positive_return_flag": 1, "add_scale_flag": 1, "anchored_split": "train"},
            {"lifecycle_id": "L2", "symbol": "MSFT", "entry_ts": "2026-01-03T14:45:00Z", "exit_ts": "2026-01-03T15:15:00Z", "bars_held": 2, "add_flag": 0, "scale_flag": 0, "reduce_flag": 1, "exit_reason": "intraday_drawdown_exit", "return_from_entry": -0.01, "theme": "cloud_ai_platforms", "role": "cloud_leader", "lifecycle_path": "ENTRY_REDUCE_EXIT", "positive_return_flag": 0, "add_scale_flag": 0, "anchored_split": "recent_oos"},
        ]
    ).to_csv(panel, index=False)


if __name__ == "__main__":
    unittest.main()
