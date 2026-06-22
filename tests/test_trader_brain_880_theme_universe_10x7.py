from __future__ import annotations

import csv
import unittest
from pathlib import Path

from scripts.trader_brain_880_theme_universe_10x7_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data/artifacts/task_880_theme_universe_10x7_replay"


def rows(name: str) -> list[dict[str, str]]:
    with (ARTIFACT_DIR / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain880ThemeUniverse10x7Test(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_contract_is_10_themes_by_7_symbols(self) -> None:
        contract = rows("theme_universe_10x7_contract.csv")
        self.assertEqual(10, len(contract))
        self.assertTrue(all(row["symbol_count"] == "7" for row in contract))

    def test_data_covers_universe_plus_benchmark(self) -> None:
        daily = rows("daily_canonical_manifest.csv")
        intraday = rows("intraday_15m_canonical_manifest.csv")
        self.assertEqual(71, len(daily))
        self.assertEqual(71, len(intraday))
        self.assertTrue(all(row["canonical_status"] == "ok" for row in daily))
        self.assertTrue(all(row["canonical_status"] == "ok" for row in intraday))

    def test_replay_has_70_diagnostic_trades(self) -> None:
        specs = rows("controlled_trade_specs.csv")
        trades = rows("controlled_replay_trades.csv")
        summary = rows("controlled_replay_summary.csv")[0]
        self.assertEqual(70, len(specs))
        self.assertEqual(70, len(trades))
        self.assertEqual("70", summary["trade_count"])

    def test_status_remains_diagnostic_only(self) -> None:
        summary = rows("controlled_replay_summary.csv")[0]
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", summary["deployment_readiness"])
        self.assertEqual("FORBIDDEN", summary["real_capital"])


if __name__ == "__main__":
    unittest.main()
