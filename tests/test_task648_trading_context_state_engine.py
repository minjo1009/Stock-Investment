from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from src.backtest.build_task648_trading_context_state_engine import build_task648


class Task648TradingContextStateEngineTest(unittest.TestCase):
    def test_context_state_engine_outputs_diagnostic_only_panel(self) -> None:
        with TemporaryDirectory() as tmp:
            result = build_task648(out_dir=Path(tmp))
            panel = result["state_panel"]
            decision = result["decision"].iloc[0]
            pass_fail = result["pass_fail"]
            coverage = result["coverage"]

            self.assertGreater(len(panel), 0)
            self.assertIn("provisional_trading_context_state", panel.columns)
            self.assertIn("suggested_action_bucket_diagnostic", panel.columns)
            self.assertTrue(panel["macro_raw_source_gap_flag"].eq(1).all())
            self.assertTrue(panel["label_used_in_state_assignment_flag"].eq(0).all())
            self.assertTrue(panel["outcome_used_in_state_assignment_flag"].eq(0).all())
            self.assertTrue(panel["strategy_promotion_flag"].eq(0).all())

            self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
            self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
            self.assertEqual(int(decision["strategy_promotion_flag"]), 0)

            gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}
            self.assertEqual(gates["state_panel_created"], 1)
            self.assertEqual(gates["no_label_or_outcome_assignment"], 1)
            self.assertEqual(gates["macro_source_gap_reported"], 1)
            self.assertEqual(gates["trading_promotion"], 0)

            macro = coverage[coverage["layer"].eq("macro_raw_sources")].iloc[0]
            self.assertEqual(int(macro["available_flag"]), 0)
            self.assertEqual(int(macro["source_gap_blocks_promotion"]), 1)


if __name__ == "__main__":
    unittest.main()
