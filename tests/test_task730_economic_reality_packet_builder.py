from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task730_economic_reality_packet_builder import build_task730
from src.backtest.economic_reality_packet import build_event_reality_packet, extract_primitive_facts


class Task730EconomicRealityPacketBuilderTest(unittest.TestCase):
    def test_non_operational_source_does_not_extract_boilerplate_numbers(self) -> None:
        row = pd.Series(
            {
                "lifecycle_id": "L1",
                "symbol": "ROK",
                "theme_id": "industrial",
                "entry_ts": "2024-01-02T14:30:00Z",
                "split_name": "unit",
                "source_form_family": "form4_insider",
                "interpretation_blocker": "ownership_or_insider_filing_blocker",
                "source_text_certified_flag": 1,
                "economic_evidence_certified_flag": 0,
                "content_interpretation_evidence_span": "FORM 4 conversion price lower table $100 million",
            }
        )
        packet = build_event_reality_packet(row)

        self.assertEqual(packet["evidence_viability_state"], "blocked_or_non_operational_source")
        self.assertEqual(packet["primitive_fact_state"], "primitive_fact_missing")
        self.assertEqual(packet["stated_amount_count"], 0)
        self.assertEqual(packet["guidance_direction_state"], "source_non_operational_not_extracted")
        self.assertEqual(packet["backtest_eligible_flag"], 0)

    def test_financing_context_stays_review_only_with_terms(self) -> None:
        row = pd.Series(
            {
                "lifecycle_id": "L2",
                "symbol": "TER",
                "theme_id": "industrial",
                "entry_ts": "2024-05-20T13:30:00Z",
                "split_name": "unit",
                "source_form_family": "financing_8k",
                "interpretation_blocker": "financing_context_requires_separate_review",
                "source_text_certified_flag": 1,
                "economic_evidence_certified_flag": 0,
                "content_interpretation_evidence_span": "Credit Agreement borrowed $185.0 million under a five year facility for general corporate purposes.",
            }
        )
        packet = build_event_reality_packet(row)

        self.assertEqual(packet["evidence_viability_state"], "source_certified_financing_context_review_required")
        self.assertEqual(packet["financing_terms_state"], "credit_or_note_purchase_terms")
        self.assertEqual(packet["primitive_fact_state"], "primitive_fact_partial")
        self.assertEqual(packet["task729_injection_state"], "task729_reality_packet_review_only")
        self.assertEqual(packet["backtest_eligible_flag"], 0)

    def test_primitive_fact_extraction_reads_operational_span(self) -> None:
        row = pd.Series({"content_named_customer_or_counterparty": 1})
        facts = extract_primitive_facts(
            row,
            "Customer signed a funded $250 million contract over 5 years with margin expansion.",
        )

        self.assertEqual(facts.stated_amount_usd, 250_000_000)
        self.assertEqual(facts.duration_months, 60)
        self.assertEqual(facts.named_counterparty_flag, 1)
        self.assertEqual(facts.funded_status, "funded")
        self.assertEqual(facts.margin_language_state, "margin_positive_language")

    def test_task730_build_outputs_and_governance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task730(out_dir=out_dir)

            for filename in [
                "task730_event_economic_reality_packets.csv",
                "task730_candidate_economic_reality_bundle.csv",
                "task730_task729_injected_resolution.csv",
                "task730_gpt_institutional_review_summary.csv",
                "task730_coderabbit_review_audit.csv",
                "task_730_decision.csv",
                "task_730_pass_fail_matrix.csv",
                "task_730_economic_reality_packet_builder.md",
                "artifact_manifest.csv",
            ]:
                self.assertTrue((out_dir / filename).exists(), filename)

            event_packets = artifacts["event_packets"]
            injected = artifacts["injected"]
            governance = artifacts["governance"]
            pass_fail = artifacts["pass_fail"]
            decision = artifacts["decision"].iloc[0]

            self.assertEqual(len(event_packets), 5302)
            self.assertEqual(len(injected), 5265)
            self.assertGreaterEqual(event_packets["economic_meaning_state"].nunique(), 3)
            self.assertEqual(int(injected["task730_backtest_eligible_flag"].sum()), 0)
            self.assertEqual(int(governance["pass_flag"].min()), 1)
            self.assertEqual(decision["backtest_permission"], "FAIL")
            self.assertEqual(decision["coderabbit_plugin_status"], "REQUESTED_BUT_CALLABLE_TOOL_UNAVAILABLE")
            plugin_row = pass_fail[pass_fail["gate_name"] == "coderabbit_plugin_available"].iloc[0]
            self.assertEqual(int(plugin_row["pass_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
