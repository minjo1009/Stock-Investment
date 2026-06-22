from __future__ import annotations

import unittest

import pandas as pd

from backtest.analysis_regime_switch_500 import _detect_regime_state


class TestAnalysisRegimeSwitch500(unittest.TestCase):
    def test_regime_state_prefix_invariant_no_lookahead(self) -> None:
        n = 260
        base = pd.DataFrame(
            {
                "close": [100.0 + i * 0.1 for i in range(n)],
                "ma200": [95.0 + i * 0.08 for i in range(n)],
            }
        )
        changed = base.copy()
        changed.loc[n - 10 :, "close"] = changed.loc[n - 10 :, "close"] * 0.6
        s1 = _detect_regime_state(base)
        s2 = _detect_regime_state(changed)
        # Earlier prefix should remain identical if future is changed.
        self.assertTrue((s1.iloc[: n - 20] == s2.iloc[: n - 20]).all())

    def test_regime_state_returns_known_labels(self) -> None:
        df = pd.DataFrame({"close": [100.0] * 220, "ma200": [100.0] * 220})
        s = _detect_regime_state(df)
        self.assertTrue(set(s.unique()).issubset({"TREND", "RANGE"}))


if __name__ == "__main__":
    unittest.main()

