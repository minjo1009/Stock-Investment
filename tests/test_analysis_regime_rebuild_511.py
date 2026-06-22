from __future__ import annotations

import unittest

import pandas as pd

from backtest.analysis_regime_rebuild_511 import apply_regime_hysteresis, detect_regime_strength_raw


class TestAnalysisRegimeRebuild511(unittest.TestCase):
    def test_detect_regime_raw_no_lookahead_prefix(self) -> None:
        n = 280
        base = pd.DataFrame(
            {
                "close": [100.0 + i * 0.1 for i in range(n)],
                "ma200": [95.0 + i * 0.08 for i in range(n)],
            }
        )
        changed = base.copy()
        changed.loc[n - 6 :, "close"] = changed.loc[n - 6 :, "close"] * 0.5
        s1 = detect_regime_strength_raw(base)
        s2 = detect_regime_strength_raw(changed)
        self.assertTrue((s1.iloc[: n - 20] == s2.iloc[: n - 20]).all())

    def test_hysteresis_blocks_single_bar_switch(self) -> None:
        raw = pd.Series(["RANGE", "STRONG_TREND", "RANGE", "RANGE", "RANGE"])
        out = apply_regime_hysteresis(raw, confirm_bars=2)
        # single-bar STRONG_TREND spike should not switch
        self.assertEqual(list(out), ["RANGE", "RANGE", "RANGE", "RANGE", "RANGE"])

    def test_hysteresis_allows_confirmed_switch(self) -> None:
        raw = pd.Series(["RANGE", "STRONG_TREND", "STRONG_TREND", "STRONG_TREND"])
        out = apply_regime_hysteresis(raw, confirm_bars=2)
        self.assertEqual(out.iloc[0], "RANGE")
        self.assertEqual(out.iloc[-1], "STRONG_TREND")


if __name__ == "__main__":
    unittest.main()

