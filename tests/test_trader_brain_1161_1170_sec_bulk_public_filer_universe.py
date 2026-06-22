from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1161_1170_sec_bulk_public_filer_universe_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1161_1170_sec_bulk_public_filer_universe"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain11611170SecBulkPublicFilerUniverseTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_sec_bulk_download_completed(self) -> None:
        download = rows("task1161_sec_bulk_download_ledger.csv")[0]
        self.assertIn(download["download_status"], {"downloaded", "already_complete"})
        self.assertGreater(int(download["bytes_downloaded"]), 1_000_000_000)
        self.assertTrue(download["source_hash"])

    def test_public_filer_proxy_is_ready_but_not_true_exchange_listing(self) -> None:
        readiness = rows("task1169_public_filer_proxy_readiness.csv")[0]
        self.assertEqual("1", readiness["public_filer_proxy_universe_ready"])
        self.assertEqual("0", readiness["true_exchange_listed_universe_ready"])
        self.assertEqual("0", readiness["replay_executed"])
        self.assertEqual("0", readiness["selection_promoted"])

    def test_asof_panel_is_broad_and_blocks_replay(self) -> None:
        coverage = rows("task1167_public_filer_universe_coverage.csv")
        self.assertEqual(63, len(coverage))
        self.assertGreater(min(int(row["unique_symbol_count"]) for row in coverage), 1000)
        sample = rows("task1166_public_filer_asof_universe_panel.csv")[:500]
        self.assertEqual({"0"}, {row["replay_use_allowed"] for row in sample})

    def test_closeout_statuses_are_unchanged(self) -> None:
        closeout = json.loads((ART / "task1170_sec_bulk_public_filer_closeout.json").read_text(encoding="utf-8"))
        self.assertEqual("1", closeout["public_filer_proxy_universe_ready"])
        self.assertEqual("0", closeout["true_exchange_listed_universe_ready"])
        self.assertEqual("0", closeout["replay_executed"])
        self.assertEqual("NOT_ACCEPTED", closeout["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", closeout["deployment_readiness"])
        self.assertEqual("FORBIDDEN", closeout["real_capital"])


if __name__ == "__main__":
    unittest.main()
