from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1081_1100_sec_asof_source_replay_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1081_1100_sec_asof_source_replay"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain10811100SecAsofSourceReplayTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_source_time_is_closed_for_sec_scope(self) -> None:
        audit = rows("task1081_sec_source_time_audit.csv")
        self.assertEqual(3689, len(audit))
        self.assertEqual({"1"}, {row["source_time_pass"] for row in audit})
        self.assertEqual({"0"}, {row["future_source_rows_used"] for row in audit})

    def test_sec_feature_panel_matches_adapter_surface(self) -> None:
        features = rows("task1082_sec_asof_adapter_feature_panel.csv")
        self.assertEqual(3689, len(features))
        self.assertEqual({"1"}, {row["source_time_pass"] for row in features})

    def test_replay_is_diagnostic_and_honest_about_mdd(self) -> None:
        closeout = json.loads((ART / "task1100_sec_asof_source_replay_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("sec_companyfacts_only", closeout["source_scope"])
        self.assertEqual("0", closeout["historical_source_time_gap"])
        self.assertEqual("1", closeout["non_sec_source_gap"])
        self.assertEqual("1", closeout["best_meets_cagr_30"])
        self.assertEqual("0", closeout["best_meets_mdd_minus30"])

    def test_statuses_remain_diagnostic_only(self) -> None:
        closeout = json.loads((ART / "task1100_sec_asof_source_replay_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
