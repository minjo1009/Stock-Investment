from __future__ import annotations

import unittest

from src.backtest.build_task496_500_goal_revalidation import build_task496, build_task497, load_base_panel
from tests.task496_500_fixture import fixture_panel


class Task497IntradayContinuationStructureTest(unittest.TestCase):
    def test_intraday_assignment_uses_entry_safe_states(self) -> None:
        panel = load_base_panel_from_frame(fixture_panel())
        regime, *_ = build_task496(panel, panel.iloc[0:0])
        intraday, _, _, leakage, decision = build_task497(regime)
        self.assertIn("volume_climax_continuation", set(intraday["intraday_entry_state_v4"]))
        self.assertEqual(int(leakage.iloc[0]["leakage_pass_flag"]), 1)
        self.assertEqual(int(decision.iloc[0]["label_used_in_assignment_flag"]), 0)


def load_base_panel_from_frame(frame):
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "panel.csv"
        frame.to_csv(path, index=False)
        return load_base_panel(path)


if __name__ == "__main__":
    unittest.main()
