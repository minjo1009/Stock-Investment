from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_intraday_universe_history_expansion_399 import (
    build_intraday_universe_history_expansion_399,
)


class TestIntradayUniverseHistoryExpansion399(unittest.TestCase):
    def test_expands_universe_and_audits_local_availability(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            themes = root / "themes.csv"
            intraday = root / "intraday"
            intraday.mkdir()
            pd.DataFrame(
                [
                    {"theme": "ai_semiconductors", "symbol": "NVDA", "role": "leader"},
                    {"theme": "cloud_ai_platforms", "symbol": "MSFT", "role": "leader"},
                ]
            ).to_csv(themes, index=False, encoding="utf-8-sig")
            pd.DataFrame(
                [
                    {"timestamp": "2026-01-01T14:30:00Z", "open": 1, "high": 1, "low": 1, "close": 1, "volume": 1}
                ]
            ).to_csv(intraday / "NVDA.csv", index=False, encoding="utf-8-sig")
            artifacts = build_intraday_universe_history_expansion_399(
                theme_universe_path=themes,
                intraday_dir=intraday,
                out_dir=root / "out",
                max_per_theme=3,
                run_download=False,
                run_canonical=False,
            )
            self.assertGreaterEqual(len(artifacts.expanded_theme_universe), 2)
            self.assertGreaterEqual(int(artifacts.task_399_decision.iloc[0]["available_symbol_count"]), 1)
            self.assertTrue((root / "out" / "task_399_intraday_universe_history_expansion.md").exists())


if __name__ == "__main__":
    unittest.main()
