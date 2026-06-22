from __future__ import annotations

import unittest
from datetime import date, timedelta
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from src.backtest.build_task649_macro_context_state_engine import SERIES_CONFIGS, build_task649


class Task649MacroContextStateEngineTest(unittest.TestCase):
    def test_macro_context_state_engine_blocks_promotion_with_vintage_gap(self) -> None:
        with TemporaryDirectory() as tmp:
            macro_raw_path = Path(tmp) / "macro_raw.csv"
            rows = []
            start = date(2023, 1, 1)
            for config in SERIES_CONFIGS:
                for index in range(80):
                    day = start + timedelta(days=index * (30 if config.frequency == "monthly" else 7 if config.frequency == "weekly" else 3))
                    rows.append(
                        {
                            "observation_date": day.isoformat(),
                            "value": 100.0 + index,
                            "series_id": config.series_id,
                            "category": config.category,
                            "description": config.description,
                            "frequency": config.frequency,
                            "conservative_lag_days": config.conservative_lag_days,
                            "source_url": "fixture",
                            "fetch_status": "FETCHED",
                            "latest_vintage_only_flag": 1,
                            "exact_release_timestamp_available_flag": 0,
                        }
                    )
            pd.DataFrame(rows).to_csv(macro_raw_path, index=False)

            result = build_task649(out_dir=Path(tmp) / "report", raw_dir=Path(tmp) / "raw", macro_raw_path=macro_raw_path)
            augmented = result["augmented"]
            decision = result["decision"].iloc[0]
            pass_fail = result["pass_fail"]

        self.assertGreater(len(augmented), 0)
        self.assertIn("macro_overall_state", augmented.columns)
        self.assertIn("augmented_trading_context_state", augmented.columns)
        self.assertTrue(augmented["macro_vintage_source_gap_flag"].eq(1).all())
        self.assertTrue(augmented["macro_release_calendar_gap_flag"].eq(1).all())
        self.assertTrue(augmented["label_used_in_macro_assignment_flag"].eq(0).all())
        self.assertTrue(augmented["outcome_used_in_macro_assignment_flag"].eq(0).all())
        self.assertTrue(augmented["strategy_promotion_flag"].eq(0).all())

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["strategy_promotion_flag"]), 0)

        gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}
        self.assertEqual(gates["macro_sources_fetched"], 1)
        self.assertEqual(gates["macro_attached_to_entries"], 1)
        self.assertEqual(gates["no_label_or_outcome_assignment"], 1)
        self.assertEqual(gates["vintage_gap_reported"], 1)
        self.assertEqual(gates["release_calendar_gap_reported"], 1)
        self.assertEqual(gates["trading_promotion"], 0)


if __name__ == "__main__":
    unittest.main()
