from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_907_916_sec_l1_l5_pipeline_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_907_916_sec_l1_l5_pipeline"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain907916SecL1L5PipelineTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_raw_sec_sources_feed_l1_to_l5(self) -> None:
        corpus = rows("task907_source_corpus_manifest.csv")
        self.assertEqual(70, len(corpus))
        self.assertEqual({"raw_source_attached"}, {row["coverage_state"] for row in corpus})
        self.assertGreater(len(rows("task908_l1_sec_companyfacts_evidence.csv")), 0)
        self.assertGreater(len(rows("task911_l2_primitive_facts.csv")), 0)
        self.assertGreater(len(rows("task913_l3_relation_snapshots.csv")), 0)
        self.assertGreater(len(rows("task914_l4_candidate_bundles.csv")), 0)
        self.assertGreater(len(rows("task915_l5_dry_decisions.csv")), 0)

    def test_internal_events_do_not_enter_positive_path(self) -> None:
        l1 = rows("task908_l1_sec_companyfacts_evidence.csv")
        self.assertNotIn("internal_source_event_capture", {row["source_family"] for row in l1})
        admission = rows("task909_source_admission_audit.csv")
        self.assertEqual({"1"}, {row["can_enter_l2"] for row in admission})

    def test_l5_still_blocks_replay(self) -> None:
        decisions = rows("task915_l5_dry_decisions.csv")
        self.assertEqual({"0"}, {row["trade_spec_allowed"] for row in decisions})
        self.assertEqual({"0"}, {row["diagnostic_replay_allowed"] for row in decisions})
        gates = {row["gate"]: row["status"] for row in rows("task916_replay_gate.csv")}
        self.assertEqual("no_go", gates["l5_trade_spec_allowed"])
        summary = json.loads((ART / "task907_916_summary.json").read_text(encoding="utf-8"))
        self.assertEqual("not_run_l5_trade_spec_no_go", summary["diagnostic_replay_status"])
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])


if __name__ == "__main__":
    unittest.main()
