from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_961_970_external_audit_redesign_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_961_970_external_audit_redesign"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain961970ExternalAuditRedesignTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_weakness_flags_are_diagnostic_only(self) -> None:
        semantic = rows("task962_weakness_semantic_reclassification.csv")
        self.assertTrue(semantic)
        self.assertEqual({"diagnostic_only"}, {row["use_mode"] for row in semantic})
        self.assertEqual({"0"}, {row["standalone_hard_block_allowed"] for row in semantic})

    def test_duplicate_ledger_is_prior_only(self) -> None:
        seen: dict[str, int] = {}
        for row in rows("task963_asof_duplicate_thesis_meaning_ledger.csv"):
            cluster = row["thesis_cluster_key"]
            expected = seen.get(cluster, 0)
            self.assertEqual(expected, int(row["prior_duplicate_count"]))
            seen[cluster] = expected + 1

    def test_trader_actions_do_not_use_weakness_flags_as_hard_blocks(self) -> None:
        forbidden = {"source_gap_heavy", "stale_source", "duplicate_thesis", "thin_packet", "low_independent_evidence"}
        for row in rows("task967_trader_action_taxonomy.csv"):
            if row["trader_action"] == "hard_block":
                self.assertNotIn(row["hard_block_reason"], forbidden)

    def test_shadow_ranking_does_not_execute_replay(self) -> None:
        ranking = rows("task969_shadow_trader_ranking.csv")
        self.assertTrue(ranking)
        self.assertEqual({"0"}, {row["changes_executed_trade"] for row in ranking})
        comparison = rows("task969_shadow_vs_baseline_comparison.csv")[0]
        self.assertEqual("0", comparison["replay_executed"])

    def test_statuses_remain_diagnostic_only(self) -> None:
        summary = json.loads((ART / "task961_970_external_audit_redesign_summary.json").read_text(encoding="utf-8"))
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", summary["deployment_readiness"])
        self.assertEqual("FORBIDDEN", summary["real_capital"])


if __name__ == "__main__":
    unittest.main()
