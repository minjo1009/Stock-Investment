from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task506_507_analyst_team_harmonization import (
    build_task506_analyst_team_source_audit,
    build_task507_analyst_harmonized_trading_logic,
)


class Task506507AnalystTeamHarmonizationTest(unittest.TestCase):
    def test_missing_analyst_sources_are_blockers_not_approximations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "raw" / "us_daily_breadth_top500").mkdir(parents=True)
            (root / "raw" / "us_intraday").mkdir(parents=True)
            artifacts = build_task506_analyst_team_source_audit(data_raw=root / "raw", out_dir=root / "out506")
            audit = artifacts.analyst_team_source_audit
            self.assertEqual(int(artifacts.task_506_decision.iloc[0]["available_team_count"]), 1)
            self.assertEqual(int(artifacts.task_506_decision.iloc[0]["missing_sources_are_approximated_flag"]), 0)
            self.assertEqual(set(audit[audit["usable_for_scoring_flag"].eq(0)]["analyst_team"]), {"fundamental", "psychology", "news"})

    def test_harmonization_uses_available_technical_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "raw" / "us_daily_breadth_top500").mkdir(parents=True)
            (root / "raw" / "us_intraday").mkdir(parents=True)
            build_task506_analyst_team_source_audit(data_raw=root / "raw", out_dir=root / "out506")
            panel = pd.DataFrame(
                [
                    {
                        "lifecycle_id": "L1",
                        "net_return_from_entry": 0.05,
                        "win_flag": 1,
                        "add_scale_success_flag": 1,
                        "entry_reduce_failure_flag": 0,
                        "false_positive_flag": 0,
                        "holding_days": 10.0,
                        "same_day_exit_flag": 0,
                        "split_name": "recent_oos",
                    }
                ]
            )
            panel_path = root / "task505_panel.csv"
            panel.to_csv(panel_path, index=False)
            artifacts = build_task507_analyst_harmonized_trading_logic(
                task505_panel_path=panel_path,
                task506_out=root / "out506",
                out_dir=root / "out507",
            )
            decision = artifacts.task_507_decision.iloc[0]
            self.assertEqual(int(decision["four_analyst_full_harmonization_ready_flag"]), 0)
            self.assertEqual(int(decision["missing_analyst_source_approximation_used_flag"]), 0)
            self.assertEqual(int(decision["blocked_analyst_team_count"]), 3)
            self.assertTrue((root / "out507" / "artifact_manifest.csv").exists())


if __name__ == "__main__":
    unittest.main()
