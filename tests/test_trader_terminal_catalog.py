from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_trader_terminal_catalog import (
    _latest_row_by_time,
    _timestamp_after,
    build_catalog,
    build_paper_ops_runtime_catalog,
    write_catalog,
    write_paper_ops_runtime_catalog,
)


class TraderTerminalCatalogTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = build_catalog(Path("."))

    def test_catalog_has_required_contract_and_provenance(self) -> None:
        payload = self.payload
        self.assertEqual(payload["contract_version"], "trader-terminal-v1")
        self.assertTrue(payload["rules"]["ui_reads_catalog_only"])
        self.assertFalse(payload["rules"]["deployment_claim_allowed"])
        self.assertGreater(len(payload["tasks"]), 0)
        first_task = payload["tasks"][0]
        self.assertIn("task_id", first_task)
        self.assertIn("decision", first_task)
        self.assertIn("report", first_task)

    def test_performance_sources_expose_metrics_and_hash(self) -> None:
        payload = self.payload
        self.assertGreater(len(payload["performance_sources"]), 0)
        source = payload["performance_sources"][-1]
        self.assertIn("artifact_path", source)
        self.assertIn("source_hash", source)
        self.assertIn("pnl_column", source)
        self.assertIn("count", source)
        self.assertIn("symbol_count", source)
        self.assertIn("avg_net_pct", source)
        self.assertIn("win_rate", source)

    def test_write_catalog_outputs_app_json(self) -> None:
        payload = self.payload
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "catalog"
            write_catalog(payload, [out])
            written = out / "trader_terminal_catalog.json"
            self.assertTrue(written.exists())
            loaded = json.loads(written.read_text(encoding="utf-8"))
        self.assertEqual(loaded["contract_version"], "trader-terminal-v1")
        json.dumps(loaded, allow_nan=False)

    def test_selected_payload_contains_matrix_and_trade_evidence_fields(self) -> None:
        payload = self.payload
        selected = payload["selected_performance"]
        self.assertIn("matrix", selected)
        self.assertIn("composite_groups", selected)
        if selected["composite_groups"]:
            self.assertIn("market_theme_intraday", selected["composite_groups"])
        self.assertIn("trade_sample", selected)
        self.assertIn("trades", selected)
        sample = selected["trade_sample"]
        if sample.get("full_symbol_count"):
            self.assertEqual(sample["full_symbol_count"], sample["sample_symbol_count"])
        if selected["trades"]:
            trade = selected["trades"][0]
            self.assertTrue({"entry_ts", "lifecycle_id", "symbol"}.intersection(trade.keys()))
            if "chart_window" in trade:
                chart_window = trade["chart_window"]
                self.assertIn("lifecycle_bars", chart_window)
                self.assertIn("entry_bars", chart_window)
                self.assertIn("exit_bars", chart_window)
                self.assertIn("long_hold_split_flag", chart_window)
                self.assertIn("lifecycle_downsampled_flag", chart_window)

    def test_paper_ops_entry_context_prefers_runtime_market_bars(self) -> None:
        payload = build_paper_ops_runtime_catalog(Path("."))
        v2 = payload["paper_ops"]["v2"]
        self.assertIn("universe_coverage", v2)
        self.assertIn("source_diagnostics", v2)
        self.assertIn("paper_readiness_gate", v2)
        self.assertIn("readiness_registry", v2)
        self.assertEqual(v2["readiness_registry"]["strategy_acceptance"]["status"], "NOT_ACCEPTED")
        self.assertEqual(v2["readiness_registry"]["paper_operation"]["status"], "READY_FOR_CONTROLLED_PAPER_RUN")
        self.assertIn("warning_codes", v2["source_diagnostics"])
        self.assertIn("filled_trade_history_rows_count", v2["source_diagnostics"])
        self.assertIn("paper_ready_flag", v2["source_diagnostics"])
        self.assertIn("paper_readiness_status", v2["source_diagnostics"])
        self.assertIn("fill_price_unrepairable_rows", v2["source_diagnostics"])
        self.assertIn("scorecard_blocked_flag", v2["source_diagnostics"])
        gate = v2["paper_readiness_gate"]
        self.assertIn("blockers", gate)
        self.assertIn("deployment_blockers", gate)
        self.assertEqual(int(gate["paper_ready_flag"]), 0 if gate["blockers"] else 1)
        eod_report = payload["paper_ops"]["v2"]["eod_report"]
        self.assertIn("filled_trade_history", eod_report)
        self.assertIn("filled_decision_evidence", eod_report)
        self.assertIn("trade_detail_view", eod_report)
        self.assertIn("fill_price_repair_audit", eod_report)
        self.assertIn("stale_source_scoreboard", v2["signal_refresh"])
        self.assertIn("no_trade_decomposition", v2["runtime_decision"])
        if eod_report["trade_detail_view"]:
            view = eod_report["trade_detail_view"][0]
            self.assertEqual(view["view_contract"], "paper_trade_detail_view_v1")
            self.assertIn("decision_reason_ko", view)
            self.assertIn("post_entry_summary_ko", view)
            self.assertIn("risk_note_ko", view)
            self.assertIn("chart", view)
            self.assertEqual(view["chart"]["status"], "ENTRY_TO_LATEST_HOLDING_WINDOW")
            self.assertGreater(len(view["chart"]["bars"]), 0)
            self.assertEqual(view["evidence"]["position_matching_policy"], "EXACT_ORDER_OR_FILL_ID_ONLY")
            self.assertEqual(int(view["evidence"]["proximity_fallback_used_flag"]), 0)
        entry_context = payload["paper_ops"]["v2"]["eod_report"].get("entry_context", [])
        if not entry_context:
            self.skipTest("paper EOD entry context has not been generated")
        with_bars = [item for item in entry_context if item.get("chart_window", {}).get("bars")]
        self.assertGreater(len(with_bars), 0)
        chart_window = with_bars[0]["chart_window"]
        self.assertEqual(chart_window["source_type"], "trading_db_market_bars_5m")
        self.assertEqual(chart_window["status"], "ENTRY_TO_LATEST_HOLDING_WINDOW")
        self.assertIn("current_ts", chart_window)
        self.assertIn("current_price", chart_window)
        self.assertGreaterEqual(len(chart_window.get("lifecycle_bars", [])), len(chart_window.get("entry_bars", [])))
        self.assertIn("indicator_context", with_bars[0])

    def test_paper_ops_universe_coverage_uses_eod_summary_as_canonical(self) -> None:
        payload = build_paper_ops_runtime_catalog(Path("."))
        v2 = payload["paper_ops"]["v2"]
        summary_rows = v2["eod_report"]["summary"]
        if not summary_rows:
            self.skipTest("paper EOD summary has not been generated")
        summary = summary_rows[0]
        coverage = v2["universe_coverage"]
        diagnostics = v2["source_diagnostics"]
        self.assertEqual(coverage["canonical_source"], "Task589 EOD summary")
        for key in [
            "expected_universe_count",
            "evaluated_symbol_count",
            "fresh_symbol_count",
            "selected_symbol_count",
            "missing_or_stale_symbol_count",
        ]:
            self.assertEqual(int(coverage[key]), int(summary[key]))
        self.assertIn("account_truth_source", diagnostics)
        self.assertIn("session_trade_scope", diagnostics)
        self.assertIn("position_sync_status", diagnostics)
        self.assertIn("task583_freshness_audit_utc", diagnostics)
        self.assertIn("task589_eod_generated_utc", diagnostics)
        self.assertIn("eod_stale_against_refresh_flag", diagnostics)
        self.assertIn("paper_readiness_blocker_count", diagnostics)
        warning_codes = set(diagnostics["warning_codes"])
        if int(diagnostics.get("paper_readiness_blocker_count", 0)) > 0:
            self.assertIn("PAPER_READY_BLOCKED", warning_codes)
        if int(summary.get("fill_price_active_blocker_rows", 0)) > 0:
            self.assertIn("UNPRICED_FILL_BLOCKER", warning_codes)
            self.assertEqual(v2["paper_readiness_gate"]["paper_readiness_status"], "BLOCKED")

    def test_paper_ops_time_helpers_detect_stale_eod_after_refresh(self) -> None:
        import pandas as pd

        frame = pd.DataFrame(
            [
                {"audit_ts_utc": "2026-06-02T18:31:00Z", "fresh_symbol_count": 36},
                {"audit_ts_utc": "2026-06-02T18:35:00Z", "fresh_symbol_count": 40},
            ]
        )
        latest = _latest_row_by_time(frame, ["audit_ts_utc"])
        self.assertEqual(int(latest["fresh_symbol_count"]), 40)
        self.assertTrue(_timestamp_after("2026-06-02T18:35:00Z", "2026-06-02T18:31:00Z"))
        self.assertFalse(_timestamp_after("2026-06-02T18:31:00Z", "2026-06-02T18:35:00Z"))

    def test_paper_ops_write_outputs_trade_detail_view_json(self) -> None:
        payload = build_paper_ops_runtime_catalog(Path("."))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "catalog"
            write_paper_ops_runtime_catalog(payload, [out])
            runtime_catalog = out / "paper_ops_runtime_catalog.json"
            trade_view = out / "paper_trade_detail_view.json"
            readiness = out / "readiness_registry.json"
            self.assertTrue(runtime_catalog.exists())
            self.assertTrue(trade_view.exists())
            self.assertTrue(readiness.exists())
            loaded = json.loads(trade_view.read_text(encoding="utf-8"))
            readiness_loaded = json.loads(readiness.read_text(encoding="utf-8"))
        self.assertEqual(loaded["contract_version"], "paper_trade_detail_view_v1")
        self.assertIn("trade_detail_view", loaded)
        self.assertEqual(readiness_loaded["contract_version"], "readiness-registry-v1")


if __name__ == "__main__":
    unittest.main()
