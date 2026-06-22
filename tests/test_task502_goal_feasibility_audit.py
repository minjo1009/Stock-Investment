from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task502_goal_feasibility_audit import build_task502_goal_feasibility_audit


class Task502GoalFeasibilityAuditTest(unittest.TestCase):
    def test_feasibility_audit_reports_blocker_when_count_band_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            task501 = root / "task501"
            task501.mkdir()
            pd.DataFrame(
                [
                    {
                        "policy_name": "p1",
                        "lifecycle_count": 400,
                        "avg_net_return_pct": 4.0,
                        "win_rate": 0.55,
                        "entry_reduce_failure_rate": 0.35,
                        "median_holding_days": 10.0,
                    }
                ]
            ).to_csv(task501 / "multiday_policy_candidate_pool.csv", index=False)
            rows = []
            for idx in range(400):
                rows.append(
                    {
                        "lifecycle_id": f"L{idx}",
                        "multi_day_market_state_v4": "constructive",
                        "theme_regime_state_v4": "theme",
                        "intraday_entry_state_v4": "entry",
                        "microstructure_state_v4": "clean",
                        "net_return_from_entry": 0.04 if idx % 2 else -0.03,
                        "win_flag": int(idx % 2),
                        "entry_reduce_failure_flag": int(not idx % 2),
                        "holding_days": 10.0,
                    }
                )
            pd.DataFrame(rows).to_csv(task501 / "selected_multiday_lifecycle_panel.csv", index=False)
            _, _, decision = build_task502_goal_feasibility_audit(task501_out=task501, out_dir=root / "out")
            self.assertEqual(str(decision.iloc[0]["current_goal_status"]), "BLOCKED_BY_ENTRY_POPULATION_QUALITY")
            self.assertTrue((root / "out" / "artifact_manifest.csv").exists())


if __name__ == "__main__":
    unittest.main()
