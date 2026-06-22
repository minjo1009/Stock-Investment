from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from backtest.analysis_structural_breakout_timestamp_price_namespace_repair_381 import main as report_main
from backtest.build_timestamp_price_namespace_repair_381 import (
    build_timestamp_price_namespace_repair_381,
    write_timestamp_price_namespace_repair_381,
)


def _protocol_row(
    trade_id: str,
    *,
    symbol: str,
    raw_id: str,
    lineage: str,
    price: float,
    candidate_price: float,
    tier: str = "symbol_session_single_match",
    theme_group: str = "non_theme",
) -> dict:
    return {
        "trade_id": trade_id,
        "symbol": symbol,
        "candidate_raw_trade_id": raw_id,
        "candidate_lineage_quality": lineage,
        "candidate_raw_entry_price": candidate_price,
        "entry_price": price,
        "recovery_match_tier": tier,
        "identity_confidence_score_v1": 0.9,
        "recovery_priority_score": 80,
        "theme_group": theme_group,
        "accepted_label_update_flag": 0,
        "diagnostic_only_flag": 1,
    }


def _lifecycle_row(raw_id: str, ts: str, *, lineage: str) -> dict:
    return {
        "raw_trade_id": raw_id,
        "start_event_timestamp": ts,
        "end_event_timestamp": ts,
        "lineage_quality": lineage,
        "identity_confidence": 0.9 if lineage == "source_linked" else 0.35,
    }


def _fixtures() -> tuple[pd.DataFrame, pd.DataFrame]:
    protocol = pd.DataFrame(
        [
            _protocol_row(
                "AAPL|2025-01-02|2025-01-02|100.000000",
                symbol="AAPL",
                raw_id="AAPL|2025-01-02|2025-01-02|99.500000",
                lineage="source_linked",
                price=100.0,
                candidate_price=99.5,
            ),
            _protocol_row(
                "MSFT|2025-01-06|2025-01-06|200.000000",
                symbol="MSFT",
                raw_id="MSFT|2025-01-06|2025-01-06|200.000000",
                lineage="source_linked",
                price=200.0,
                candidate_price=200.0,
                tier="exact_trade_id_match",
            ),
            _protocol_row(
                "AMD|2025-01-03|2025-01-03|120.000000",
                symbol="AMD",
                raw_id="AMD|2025-01-03|2025-01-03|119.000000",
                lineage="replay_derived",
                price=120.0,
                candidate_price=119.0,
                theme_group="semis_leader",
            ),
            _protocol_row(
                "COST|2025-01-04|2025-01-04|500.000000",
                symbol="COST",
                raw_id="COST|2025-01-04|2025-01-04|450.000000",
                lineage="source_linked",
                price=500.0,
                candidate_price=450.0,
                theme_group="platform_quality_leader",
            ),
            _protocol_row(
                "ZZZ|2025-01-05|2025-01-05|50.000000",
                symbol="ZZZ",
                raw_id="",
                lineage="",
                price=50.0,
                candidate_price=0.0,
            ),
        ]
    )
    lifecycle = pd.DataFrame(
        [
            _lifecycle_row("AAPL|2025-01-02|2025-01-02|99.500000", "2025-01-02T14:30:00Z", lineage="source_linked"),
            _lifecycle_row("MSFT|2025-01-06|2025-01-06|200.000000", "2025-01-06T14:30:00Z", lineage="source_linked"),
            _lifecycle_row("AMD|2025-01-03|2025-01-03|119.000000", "2025-01-03T14:30:00Z", lineage="replay_derived"),
            _lifecycle_row("COST|2025-01-04|2025-01-04|450.000000", "2025-01-04T14:30:00Z", lineage="source_linked"),
        ]
    )
    return protocol, lifecycle


class TimestampPriceNamespaceRepair381Tests(unittest.TestCase):
    def _build_fixture_artifacts(self):
        protocol, lifecycle = _fixtures()
        return build_timestamp_price_namespace_repair_381(
            protocol_candidates_df=protocol,
            namespace_fix_df=pd.DataFrame(),
            manual_review_df=pd.DataFrame(),
            task374_candidates_df=pd.DataFrame(),
            lifecycle_df=lifecycle,
        )

    def test_repair_decisions_are_conservative(self) -> None:
        repair = self._build_fixture_artifacts().timestamp_price_repair_candidates.set_index("symbol")
        self.assertEqual(repair.loc["AAPL", "timestamp_repair_status"], "repair_candidate_source_linked_intraday_ts")
        self.assertEqual(repair.loc["AAPL", "price_anchor_repair_class"], "price_anchor_minor_mismatch")
        self.assertEqual(repair.loc["AAPL", "namespace_repair_decision_v1"], "manual_namespace_review_required")
        self.assertEqual(repair.loc["MSFT", "namespace_repair_decision_v1"], "namespace_repair_ready_candidate")
        self.assertEqual(repair.loc["AMD", "timestamp_repair_status"], "repair_candidate_replay_derived_ts")
        self.assertEqual(repair.loc["AMD", "namespace_repair_decision_v1"], "manual_namespace_review_required")
        self.assertEqual(repair.loc["COST", "price_anchor_repair_class"], "price_anchor_material_mismatch")
        self.assertEqual(repair.loc["COST", "namespace_repair_decision_v1"], "manual_namespace_review_required")
        self.assertEqual(repair.loc["ZZZ", "namespace_repair_decision_v1"], "insufficient_repair_evidence")

    def test_repair_layer_keeps_diagnostic_boundary(self) -> None:
        repair = self._build_fixture_artifacts().timestamp_price_repair_candidates
        self.assertEqual(int(repair["accepted_label_update_flag"].sum()), 0)
        self.assertEqual(int(repair["diagnostic_only_flag"].min()), 1)
        semis = repair[repair["theme_group"].astype(str).eq("semis_leader")]
        self.assertFalse(semis.empty)
        self.assertFalse(semis["namespace_repair_decision_v1"].astype(str).eq("namespace_repair_ready_candidate").any())

    def test_decision_reports_diagnostic_revalidation_readiness(self) -> None:
        decision = self._build_fixture_artifacts().namespace_repair_decision.iloc[0]
        self.assertEqual(decision["task_381_verdict"], "COMPLETE_PASS")
        self.assertEqual(decision["persistence_revalidation_ready"], "YES_DIAGNOSTIC_LAYER_ONLY")
        self.assertEqual(decision["labels_overwritten"], "NO")
        self.assertEqual(decision["task_376_ontology_relaxed"], "NO")
        self.assertEqual(decision["theme_promoted_by_task_381"], "NO")

    def test_report_artifacts_are_generated(self) -> None:
        artifacts = self._build_fixture_artifacts()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            write_timestamp_price_namespace_repair_381(artifacts, out_dir)
            with patch(
                "backtest.analysis_structural_breakout_timestamp_price_namespace_repair_381.build_timestamp_price_namespace_repair_381",
                return_value=artifacts,
            ):
                argv = sys.argv
                try:
                    sys.argv = ["timestamp_price_namespace_repair_381", "--out-dir", str(out_dir)]
                    report_main()
                finally:
                    sys.argv = argv

            for name in (
                "timestamp_price_repair_candidates.csv",
                "namespace_repair_ready_layer.csv",
                "manual_namespace_review_queue.csv",
                "namespace_repair_rejected.csv",
                "timestamp_repair_audit.csv",
                "price_anchor_repair_audit.csv",
                "namespace_repair_decision.csv",
                "task_381_timestamp_price_namespace_repair.md",
            ):
                self.assertTrue((out_dir / name).exists(), name)
            report = (out_dir / "task_381_timestamp_price_namespace_repair.md").read_text(encoding="utf-8-sig")
            self.assertIn("Did Task 381 overwrite labels: `NO`", report)
            self.assertIn("Did Task 381 promote AMD/semis by theme: `NO`", report)
            self.assertIn("Final Task 381 verdict: `COMPLETE_PASS`", report)


if __name__ == "__main__":
    unittest.main()
