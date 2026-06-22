from __future__ import annotations

import unittest

from src.backtest.build_task548_555_quant_doc_alignment import (
    build_task548,
    build_task549,
    build_task550,
    build_task551,
    build_task552,
    build_task553,
    build_task554,
    build_task555,
    load_task545_panel,
)


class Task548To555QuantDocAlignmentTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.panel = load_task545_panel()

    def test_task548_regime_expansion_uses_no_outcome_and_blocks_missing_macro(self) -> None:
        artifacts = build_task548(self.panel)
        panel = artifacts["market_regime_v5_panel"]
        audit = artifacts["market_regime_feature_source_audit"]
        self.assertIn("regime_v5_state", panel.columns)
        self.assertEqual(int(panel["assignment_uses_outcome_flag"].max()), 0)
        self.assertGreater(int(audit["source_status"].astype(str).str.contains("missing|not_available").sum()), 0)
        self.assertEqual(int(audit["approximation_used_flag"].max()), 0)

    def test_task549_theme_universe_is_versioned_and_keeps_missing_sources_visible(self) -> None:
        artifacts = build_task549(self.panel)
        audit = artifacts["theme_universe_contract_audit"]
        self.assertIn("theme_universe_version_present_flag", audit.columns)
        self.assertEqual(int(audit["theme_universe_version_present_flag"].min()), 1)
        self.assertEqual(int(audit["missing_options_news_source_flag"].max()), 1)
        self.assertIn("theme_id", artifacts["theme_leadership_panel"].columns)

    def test_task550_continuation_factors_are_entry_safe_diagnostics(self) -> None:
        artifacts = build_task550(self.panel)
        panel = artifacts["symbol_continuation_structure_v2_panel"]
        audit = artifacts["anchored_vwap_factor_audit"]
        self.assertIn("continuation_structure_v2", panel.columns)
        self.assertEqual(int(panel["label_used_in_assignment_flag"].max()), 0)
        self.assertEqual(int(audit["label_used_flag"].max()), 0)
        self.assertIn("entry_reduce_failure_rate", artifacts["entry_reduce_separation_v2"].columns)

    def test_task551_microstructure_sources_do_not_approximate_missing_depth(self) -> None:
        artifacts = build_task551()
        contract = artifacts["microstructure_source_contract_v2"]
        depth = contract[contract["source_name"].eq("full_depth_book")].iloc[0]
        self.assertEqual(int(depth["blocked_flag"]), 1)
        self.assertEqual(int(contract["approximation_used_flag"].max()), 0)

    def test_task552_broker_truth_contract_keeps_historical_rows_non_deployment(self) -> None:
        artifacts = build_task552()
        contract = artifacts["broker_order_fill_archive_contract"]
        decision = artifacts["task_552_decision"].iloc[0]
        self.assertIn("filled_avg_price", set(contract["field_name"]))
        self.assertEqual(int(decision["broker_truth_available_flag"]), 0)
        self.assertEqual(int(decision["deployment_ready_flag"]), 0)

    def test_task553_portfolio_realism_is_proxy_until_broker_truth(self) -> None:
        artifacts = build_task553(self.panel)
        quality = artifacts["portfolio_risk_quality"].iloc[0]
        self.assertGreater(int(quality["trade_count"]), 0)
        self.assertEqual(int(quality["broker_truth_fill_used_flag"]), 0)
        self.assertIn("gross_exposure", artifacts["exposure_overlap_audit"].columns)

    def test_task554_and_555_contracts_keep_existing_governance(self) -> None:
        task554 = build_task554()
        self.assertIn("schema_version", set(task554["artifact_manifest_v2_sample"].columns))
        self.assertEqual(int(task554["task_554_decision"].iloc[0]["manifest_v2_contract_defined_flag"]), 1)
        task555 = build_task555()
        self.assertEqual(int(task555["task_555_decision"].iloc[0]["frontend_reads_catalog_only_flag"]), 1)
        self.assertEqual(int(task555["task_555_decision"].iloc[0]["fake_marker_allowed_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
