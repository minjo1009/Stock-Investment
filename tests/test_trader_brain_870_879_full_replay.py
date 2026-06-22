from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_870_879_full_replay_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data/artifacts/task_870_879_full_controlled_replay"


def rows(name: str) -> list[dict[str, str]]:
    with (ARTIFACT_DIR / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain870879FullReplayTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_explicit_universe_data_is_complete(self) -> None:
        daily = rows("daily_canonical_manifest.csv")
        intraday = rows("intraday_15m_canonical_manifest.csv")
        self.assertEqual(16, len(daily))
        self.assertEqual(16, len(intraday))
        self.assertTrue(all(row["canonical_status"] == "ok" for row in daily))
        self.assertTrue(all(row["canonical_status"] == "ok" for row in intraday))

    def test_trade_specs_have_required_replay_fields(self) -> None:
        specs = rows("controlled_trade_specs.csv")
        self.assertEqual(22, len(specs))
        required = {"symbol", "side", "tradable_after_ts", "entry_policy_id", "exit_policy_id", "position_policy_id", "allocated_capital"}
        self.assertTrue(required.issubset(specs[0]))

    def test_replay_remains_diagnostic_not_accepted(self) -> None:
        summary = rows("controlled_replay_summary.csv")[0]
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", summary["deployment_readiness"])
        self.assertEqual("FORBIDDEN", summary["real_capital"])
        self.assertEqual("22", summary["trade_count"])

    def test_cycle_summary_covers_full_explicit_universe(self) -> None:
        cycle = json.loads((ARTIFACT_DIR / "full_cycle_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(16, cycle["symbol_count"])
        self.assertEqual("READY_FOR_CONTROLLED_REPLAY_PLAN", cycle["market_data_gate_status"])


if __name__ == "__main__":
    unittest.main()
