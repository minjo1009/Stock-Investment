from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_1031_1040_l1_l4_golden_set_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_1031_1040_l1_l4_golden_set"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain10311040L1L4GoldenSetTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_golden_set_has_10_buckets_x_2_cases(self) -> None:
        golden = rows("task1035_source_to_thesis_golden_set.csv")
        self.assertEqual(20, len(golden))
        counts: dict[str, int] = {}
        for row in golden:
            counts[row["case_bucket"]] = counts.get(row["case_bucket"], 0) + 1
        self.assertEqual(
            {
                "macro": 2,
                "policy": 2,
                "semiconductors": 2,
                "ai": 2,
                "energy_power": 2,
                "space": 2,
                "cyber": 2,
                "contradiction": 2,
                "stale_thesis": 2,
                "cross_read": 2,
            },
            counts,
        )

    def test_every_case_has_l1_l2_l3_l4_chain(self) -> None:
        golden = rows("task1035_source_to_thesis_golden_set.csv")
        for table_name, id_name in [
            ("task1031_l1_golden_source_contract_rows.csv", "l1_id"),
            ("task1032_l2_golden_primitive_rows.csv", "l2_id"),
            ("task1033_l3_golden_mechanism_rows.csv", "l3_id"),
            ("task1034_l4_golden_thesis_card_rows.csv", "l4_id"),
        ]:
            by_case = {row["case_id"]: row[id_name] for row in rows(table_name)}
            self.assertEqual({row["case_id"] for row in golden}, set(by_case))
            for row in golden:
                self.assertEqual(row[id_name], by_case[row["case_id"]])

    def test_golden_set_is_review_only_not_replay_or_selection(self) -> None:
        for table_name in [
            "task1031_l1_golden_source_contract_rows.csv",
            "task1035_source_to_thesis_golden_set.csv",
            "task1037_l1_l4_golden_validation_results.csv",
        ]:
            table = rows(table_name)
            self.assertEqual({"0"}, {row["selection_use_allowed"] for row in table})
            self.assertEqual({"0"}, {row["replay_use_allowed"] for row in table})
        l4 = rows("task1034_l4_golden_thesis_card_rows.csv")
        self.assertEqual({"0"}, {row["outcome_used_for_assignment_flag"] for row in l4})
        self.assertEqual({"0"}, {row["trade_instruction_allowed"] for row in l4})

    def test_negative_fixtures_are_expected_failures(self) -> None:
        negatives = rows("task1037_negative_golden_failure_cases.csv")
        self.assertGreaterEqual(len(negatives), 6)
        self.assertEqual({"fail"}, {row["expected_validator_action"] for row in negatives})

    def test_statuses_remain_diagnostic_only(self) -> None:
        summary = json.loads((ART / "task1031_1040_summary.json").read_text(encoding="utf-8"))
        self.assertEqual(20, summary["golden_case_count"])
        self.assertEqual("10_buckets_x_2_cases", summary["bucket_contract"])
        self.assertEqual("0", summary["replay_executed"])
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])
        self.assertEqual("DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY", summary["deployment_readiness"])
        self.assertEqual("FORBIDDEN", summary["real_capital"])


if __name__ == "__main__":
    unittest.main()
