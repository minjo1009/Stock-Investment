from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1101_1110_winner_concentration_audit_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1101_1110_winner_concentration_audit"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain11011110WinnerConcentrationAuditTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_winner_concentration_confirmed(self) -> None:
        summary = rows("task1101_winner_concentration_summary.csv")[0]
        self.assertEqual("winner_basket_concentration_confirmed", summary["verdict"])
        self.assertEqual("6", summary["selected_symbols"])
        self.assertGreater(float(summary["top3_pnl_share_pct"]), 90.0)
        self.assertEqual("ASTS;VRT;ARM", summary["top3_symbols"])

    def test_selected_scores_are_static(self) -> None:
        stability = rows("task1103_selected_score_stability.csv")
        self.assertEqual({"1"}, {row["static_score_flag"] for row in stability})

    def test_static_universe_gap_is_recorded(self) -> None:
        universe = rows("task1105_universe_pit_audit.csv")[0]
        self.assertEqual("0", universe["has_point_in_time_columns"])
        self.assertEqual("pit_universe_gap", universe["audit_state"])

    def test_statuses_remain_diagnostic_only(self) -> None:
        closeout = json.loads((ART / "task1110_winner_concentration_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
