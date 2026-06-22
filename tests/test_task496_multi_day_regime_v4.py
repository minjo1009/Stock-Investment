from __future__ import annotations

import unittest

from src.backtest.build_task496_500_goal_revalidation import build_task496, load_base_panel
from tests.task496_500_fixture import fixture_panel


class Task496MultiDayRegimeV4Test(unittest.TestCase):
    def test_regime_assignment_is_multi_day_and_outcome_free(self) -> None:
        panel = fixture_panel()
        regime, _, _, _, decision = build_task496(load_base_panel_from_frame(panel), panel.iloc[0:0])
        self.assertIn("persistent_broad_risk_on", set(regime["multi_day_market_state_v4"]))
        self.assertEqual(int(regime["lifecycle_outcome_used_for_regime_flag"].max()), 0)
        self.assertEqual(int(decision.iloc[0]["multi_day_only_flag"]), 1)


def load_base_panel_from_frame(frame):
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "panel.csv"
        frame.to_csv(path, index=False)
        return load_base_panel(path)


if __name__ == "__main__":
    unittest.main()
