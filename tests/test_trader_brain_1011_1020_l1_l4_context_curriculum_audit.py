from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1011_1020_l1_l4_context_curriculum_audit_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1011_1020_l1_l4_context_curriculum_audit"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain10111020L1L4ContextCurriculumAuditTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_sources_are_research_only(self) -> None:
        source_rows = rows("task1011_l1_l4_source_context_manifest.csv")
        self.assertTrue(source_rows)
        self.assertEqual({"0"}, {row["selection_use_allowed"] for row in source_rows})
        self.assertEqual({"0"}, {row["replay_use_allowed"] for row in source_rows})

    def test_each_layer_has_gap_rows(self) -> None:
        for name in [
            "task1012_l1_source_gap_audit.csv",
            "task1013_l2_economic_meaning_gap_audit.csv",
            "task1014_l3_relation_ontology_gap_audit.csv",
            "task1015_l4_candidate_bundle_gap_audit.csv",
        ]:
            self.assertGreaterEqual(len(rows(name)), 3)

    def test_backlog_has_ten_items(self) -> None:
        self.assertEqual(10, len(rows("task1017_l1_l4_upgrade_backlog.csv")))

    def test_statuses_remain_diagnostic_only(self) -> None:
        summary = json.loads((ART / "task1011_1020_summary.json").read_text(encoding="utf-8"))
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", summary["deployment_readiness"])
        self.assertEqual("FORBIDDEN", summary["real_capital"])


if __name__ == "__main__":
    unittest.main()
