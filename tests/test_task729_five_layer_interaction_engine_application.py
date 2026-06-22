from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from src.backtest.build_task729_five_layer_interaction_engine_application import build_task729
from src.backtest.five_layer_interaction_engine import evaluate_interaction_frame


def base_row(**overrides: object) -> dict[str, object]:
    row = {
        "lifecycle_id": "L1",
        "symbol": "TEST",
        "theme_id": "THEME",
        "entry_ts": "2026-01-02T09:30:00Z",
        "split_name": "unit",
        "source_type_state": "company_direct_source",
        "source_directness_state": "direct_company_economic_detail",
        "novelty_state": "new_or_not_obviously_stale",
        "evidence_strength_state": "strong_multi_signal_company_evidence",
        "source_gap_state": "source_available",
        "evidence_brain_state": "certified_company_direct_strong_evidence",
        "financing_context_state": "not_financing",
        "economic_transmission_state": "revenue_margin_reinforcing",
        "funding_path_state": "no_funding_event",
        "dilution_overhang_state": "no_dilution_overhang_claim",
        "pricing_acceptance_state": "accepted_by_price_and_tape_proxy",
        "market_pricing_brain_state": "market_accepts_economic_path",
        "acceptance_failure_state": "no_primary_acceptance_failure",
        "slot_competition_state": "same_timestamp_slot_leader",
        "exposure_cluster_state": "theme_cluster_low",
        "portfolio_brain_state": "distinct_driver_slot_leader_review",
        "review_decision_state": "normal_size_review_candidate_not_approved",
        "invalidation_condition": "invalid_if_price_acceptance_breaks_or_theme_leadership_fades",
        "risk_budget_state": "normal_review_budget_not_approved",
        "final_brain_state": "normal_size_review_candidate_not_approved__normal_review_budget_not_approved",
    }
    row.update(overrides)
    return row


class Task729FiveLayerInteractionEngineApplicationTest(unittest.TestCase):
    def test_engine_emits_required_edges_and_keeps_backtest_zero(self) -> None:
        frame = pd.DataFrame([base_row()])
        edges, resolution = evaluate_interaction_frame(frame)

        self.assertEqual(len(edges), 7)
        self.assertEqual(len(resolution), 1)
        self.assertEqual(int(resolution.iloc[0]["backtest_eligible_flag"]), 0)
        self.assertEqual(resolution.iloc[0]["primitive_fact_gate_state"], "not_ready")
        self.assertEqual(int(resolution.iloc[0]["primitive_fact_gate_pass_flag"]), 0)
        self.assertNotIn("approved", resolution.iloc[0]["final_actionability_state"].lower())
        self.assertNotIn("trade", resolution.iloc[0]["final_actionability_state"].lower())

    def test_primitive_gate_pass_uses_adapter_without_backtest_eligibility(self) -> None:
        frame = pd.DataFrame(
            [
                base_row(
                    primitive_fact_adapter_gate_state="pass",
                    adapter_source_task="Task742",
                    adapter_source_packet_id="T761_REPLAY_01",
                    adapter_gate_reason="source_backed_directional_packet",
                    invalidation_condition="no_specific_invalidation_required",
                )
            ]
        )
        _, resolution = evaluate_interaction_frame(frame)

        self.assertEqual(resolution.iloc[0]["primitive_fact_gate_state"], "pass")
        self.assertEqual(int(resolution.iloc[0]["primitive_fact_gate_pass_flag"]), 1)
        self.assertEqual(int(resolution.iloc[0]["backtest_eligible_flag"]), 0)
        self.assertEqual(int(resolution.iloc[0]["interaction_engine_assignment_allowed_flag"]), 0)
        self.assertEqual(resolution.iloc[0]["primitive_fact_adapter_source_task"], "Task742")
        self.assertEqual(resolution.iloc[0]["primitive_fact_adapter_source_packet_id"], "T761_REPLAY_01")
        self.assertEqual(resolution.iloc[0]["primitive_fact_gate_reason"], "source_backed_directional_packet")
        self.assertEqual(resolution.iloc[0]["final_actionability_state"], "REVIEW_ONLY_PRIMITIVE_FACTS_READY")
        self.assertNotIn("backtest", resolution.iloc[0]["final_actionability_state"].lower())

    def test_primitive_gate_pass_does_not_override_invalidation(self) -> None:
        frame = pd.DataFrame([base_row(primitive_fact_adapter_gate_state="pass")])
        _, resolution = evaluate_interaction_frame(frame)

        self.assertEqual(resolution.iloc[0]["primitive_fact_gate_state"], "pass")
        self.assertEqual(int(resolution.iloc[0]["primitive_fact_gate_pass_flag"]), 1)
        self.assertEqual(int(resolution.iloc[0]["backtest_eligible_flag"]), 0)
        self.assertEqual(resolution.iloc[0]["final_actionability_state"], "WATCH_CONFIRMATION_WITH_INVALIDATION_TRACE")

    def test_invalid_primitive_gate_defaults_to_not_ready(self) -> None:
        frame = pd.DataFrame([base_row(primitive_fact_adapter_gate_state="surprise_me")])
        _, resolution = evaluate_interaction_frame(frame)

        self.assertEqual(resolution.iloc[0]["primitive_fact_gate_state"], "not_ready")
        self.assertEqual(int(resolution.iloc[0]["primitive_fact_gate_pass_flag"]), 0)
        self.assertEqual(resolution.iloc[0]["final_actionability_state"], "WATCH_CONFIRMATION_WITH_INVALIDATION_TRACE")

    def test_context_only_primitive_gate_cannot_create_directional_permission(self) -> None:
        frame = pd.DataFrame(
            [
                base_row(
                    primitive_fact_adapter_gate_state="context_only",
                    invalidation_condition="no_specific_invalidation_required",
                )
            ]
        )
        _, resolution = evaluate_interaction_frame(frame)

        self.assertEqual(resolution.iloc[0]["primitive_fact_gate_state"], "context_only")
        self.assertEqual(int(resolution.iloc[0]["primitive_fact_gate_pass_flag"]), 0)
        self.assertEqual(int(resolution.iloc[0]["backtest_eligible_flag"]), 0)
        self.assertEqual(resolution.iloc[0]["final_actionability_state"], "RESEARCH_ONLY_CONTEXT_ONLY_PRIMITIVE_FACTS")

    def test_price_acceptance_cannot_rescue_source_gap(self) -> None:
        frame = pd.DataFrame(
            [
                base_row(
                    source_type_state="source_gap",
                    source_directness_state="no_source_directness_claim",
                    evidence_strength_state="no_source_evidence",
                    evidence_brain_state="source_gap_unknown_not_negative",
                    pricing_acceptance_state="accepted_by_price_and_tape_proxy",
                    market_pricing_brain_state="market_accepts_economic_path",
                )
            ]
        )
        edges, resolution = evaluate_interaction_frame(frame)
        self.assertIn("L1_L2_GATE_001", set(edges["rule_family_id"]))
        self.assertEqual(resolution.iloc[0]["final_actionability_state"], "RESEARCH_ONLY_SOURCE_GAP_BLOCKED")
        self.assertEqual(int(resolution.iloc[0]["backtest_eligible_flag"]), 0)

    def test_blocker_overrides_reinforcing_edges(self) -> None:
        frame = pd.DataFrame(
            [
                base_row(
                    funding_path_state="funding_need_with_overhang",
                    dilution_overhang_state="dilution_overhang_unabsorbed",
                    market_pricing_brain_state="market_accepts_economic_path",
                    slot_competition_state="same_timestamp_slot_leader",
                )
            ]
        )
        edges, resolution = evaluate_interaction_frame(frame)
        self.assertIn("blocker", set(edges["relation_type"]))
        self.assertIn("reinforcing", set(edges["relation_type"]))
        self.assertEqual(resolution.iloc[0]["dominant_relation_type"], "blocker")
        self.assertIn("BLOCKER", resolution.iloc[0]["final_actionability_state"])

    def test_cluster_high_caps_budget_not_approval(self) -> None:
        frame = pd.DataFrame([base_row(exposure_cluster_state="theme_cluster_high", risk_budget_state="cluster_capped_review_budget")])
        edges, resolution = evaluate_interaction_frame(frame)
        self.assertIn("L4_L5_RISK_017", set(edges["rule_family_id"]))
        self.assertIn("cluster_capped_budget", set(edges["output_state"]))
        self.assertEqual(int(resolution.iloc[0]["backtest_eligible_flag"]), 0)

    def test_task729_build_outputs_and_audits(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out_dir = Path(tmp)
            artifacts = build_task729(out_dir=out_dir)

            for filename in [
                "task729_interaction_edge_panel.csv",
                "task729_interaction_resolution_panel.csv",
                "task729_code_review_audit.csv",
                "task729_gpt_institutional_review_summary.csv",
                "task_729_decision.csv",
                "task_729_pass_fail_matrix.csv",
                "task_729_five_layer_interaction_engine_application.md",
                "artifact_manifest.csv",
            ]:
                self.assertTrue((out_dir / filename).exists(), filename)

            merged = artifacts["merged"]
            edge_panel = artifacts["edge_panel"]
            resolution_panel = artifacts["resolution_panel"]
            self.assertEqual(len(edge_panel), len(merged) * 7)
            self.assertEqual(len(resolution_panel), len(merged))
            self.assertEqual(int(resolution_panel["backtest_eligible_flag"].sum()), 0)

            code_review = artifacts["code_review_audit"]
            fallback = code_review[code_review["gate_name"] != "coderabbit_plugin_available"]
            self.assertEqual(int(fallback["pass_flag"].min()), 1)

            decision = artifacts["decision"].iloc[0]
            self.assertEqual(decision["backtest_permission"], "FAIL")
            self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
            self.assertEqual(decision["coderabbit_plugin_status"], "NOT_AVAILABLE_LOCAL_REVIEW_USED")


if __name__ == "__main__":
    unittest.main()
