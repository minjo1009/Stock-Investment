from __future__ import annotations

import unittest

import pandas as pd

from backtest.analysis_max_return_regime_510 import detect_regime_strength


class TestAnalysisMaxReturnRegime510(unittest.TestCase):
    def test_detect_regime_strength_no_lookahead_prefix(self) -> None:
        n = 280
        base = pd.DataFrame(
            {
                "close": [100.0 + i * 0.1 for i in range(n)],
                "ma200": [90.0 + i * 0.08 for i in range(n)],
            }
        )
        mutated = base.copy()
        mutated.loc[n - 8 :, "close"] = mutated.loc[n - 8 :, "close"] * 0.5
        s1 = detect_regime_strength(base)
        s2 = detect_regime_strength(mutated)
        self.assertTrue((s1.iloc[: n - 20] == s2.iloc[: n - 20]).all())

    def test_detect_regime_strength_labels(self) -> None:
        df = pd.DataFrame({"close": [100.0] * 260, "ma200": [100.0] * 260})
        out = detect_regime_strength(df)
        self.assertTrue(set(out.unique()).issubset({"STRONG_TREND", "WEAK_TREND", "RANGE"}))


if __name__ == "__main__":
    unittest.main()

