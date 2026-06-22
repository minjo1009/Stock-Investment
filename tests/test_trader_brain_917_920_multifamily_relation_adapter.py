from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

from scripts.trader_brain_917_920_multifamily_relation_adapter_validate import validate


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "data/artifacts/task_917_920_multifamily_relation_adapter"


def rows(name: str) -> list[dict[str, str]]:
    with (ART / name).open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain917920MultifamilyRelationAdapterTest(unittest.TestCase):
    def test_validator_passes(self) -> None:
        self.assertEqual([], validate())

    def test_all_six_source_families_are_attached(self) -> None:
        manifest = rows("task917_source_family_attachment_manifest.csv")
        attached = {row["source_family"] for row in manifest if row["attachment_state"] == "attached"}
        self.assertEqual(
            {
                "company_filings_ir",
                "earnings_guidance",
                "macro_policy_official",
                "supply_chain_customer_capex_cross_read",
                "positioning_liquidity_volatility",
                "sector_specialist_official_docs",
            },
            attached,
        )

    def test_relation_primitive_system_is_bounded_and_has_core_coverage(self) -> None:
        catalog = rows("task919_relation_primitive_catalog.csv")
        self.assertEqual(
            {
                "reinforces",
                "weakens",
                "invalidates",
                "conditions",
                "sequences",
                "explains",
                "contradicts",
                "source_gap_for",
                "noise_for",
            },
            {row["relation_primitive"] for row in catalog},
        )
        self.assertEqual({"do_not_synthesize_edge_without_source_backed_trigger"}, {row["absence_policy"] for row in catalog})
        relations = rows("task919_relation_edges_9primitive.csv")
        used = {row["relation_primitive"] for row in relations}
        self.assertLessEqual(
            used,
            {
                "reinforces",
                "weakens",
                "invalidates",
                "conditions",
                "sequences",
                "explains",
                "contradicts",
                "source_gap_for",
                "noise_for",
            },
        )
        self.assertLessEqual({"reinforces", "weakens", "conditions", "explains", "source_gap_for", "noise_for"}, used)

    def test_l4_contains_contradiction_and_invalidation_fields(self) -> None:
        candidates = rows("task919_l4_candidate_bundles_contradiction.csv")
        self.assertTrue(any(row["contradiction_state"] == "contradiction_present" for row in candidates))
        self.assertTrue(all(row["invalidation_conditions"] for row in candidates))
        self.assertTrue(all(row["weakest_layer"] for row in candidates))

    def test_adapter_design_is_separate_and_not_backtest_ready(self) -> None:
        adapter_rows = rows("task920_adapter_input_design_rows.csv")
        self.assertTrue(adapter_rows)
        self.assertEqual({"0"}, {row["ready_for_backtest"] for row in adapter_rows})
        self.assertEqual({""}, {row["side"] for row in adapter_rows})
        self.assertEqual({""}, {row["entry_rule"] for row in adapter_rows})
        self.assertEqual({""}, {row["exit_rule"] for row in adapter_rows})
        self.assertEqual({""}, {row["position_size_rule"] for row in adapter_rows})
        summary = json.loads((ART / "task917_920_summary.json").read_text(encoding="utf-8"))
        self.assertEqual("not_run_adapter_design_only", summary["diagnostic_replay_status"])
        self.assertEqual("NOT_ACCEPTED", summary["strategy_acceptance"])


if __name__ == "__main__":
    unittest.main()
