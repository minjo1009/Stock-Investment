from __future__ import annotations

import unittest

from src.backtest.build_task496_500_goal_revalidation import build_task496, build_task497, build_task498, load_base_panel
from tests.task496_500_fixture import fixture_panel


class Task498EntryReduceFailureDecompositionTest(unittest.TestCase):
    def test_entry_reduce_failure_is_decomposed(self) -> None:
        panel = load_base_panel_from_frame(fixture_panel())
        regime, *_ = build_task496(panel, panel.iloc[0:0])
        intraday, *_ = build_task497(regime)
        failure, by_state, contrast, decision = build_task498(intraday)
        self.assertGreater(int(decision.iloc[0]["entry_reduce_failure_count"]), 0)
        self.assertFalse(failure.empty)
        self.assertFalse(by_state.empty)
        self.assertIn("contrast_group", contrast.columns)


def load_base_panel_from_frame(frame):
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "panel.csv"
        frame.to_csv(path, index=False)
        return load_base_panel(path)


if __name__ == "__main__":
    unittest.main()
