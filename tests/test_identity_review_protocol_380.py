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

from backtest.analysis_structural_breakout_identity_review_protocol_380 import main as report_main
from backtest.build_identity_review_protocol_380 import build_identity_review_protocol_380, write_identity_review_protocol_380


def _candidate(
    trade_id: str,
    *,
    symbol: str,
    raw_id: str,
    bucket: str,
    tier: str,
    lineage: str,
    price_rel: float,
    entry_ts: str,
    theme_group: str = "non_theme",
) -> dict:
    return {
        "trade_id": trade_id,
        "symbol": symbol,
        "candidate_raw_trade_id": raw_id,
        "recovery_match_tier": tier,
        "identity_confidence_bucket_v1": bucket,
        "identity_confidence_score_v1": 0.9 if bucket == "high_confidence_recovered_candidate" else 0.55,
        "candidate_lineage_quality": lineage,
        "price_rel_diff": price_rel,
        "price_distance_status": "price_blocked" if price_rel > 0.05 else "price_close",
        "time_distance_status": "time_close",
        "entry_component_ts": entry_ts,
        "entry_ts": entry_ts,
        "recovery_priority_tier": "p1_watchlist_or_theme",
        "recovery_priority_score": 80,
        "theme_group": theme_group,
        "accepted_label_update_flag": 0,
        "diagnostic_only_flag": 1,
    }


def _fixtures() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    candidates = pd.DataFrame(
        [
            _candidate(
                "AAPL|2025-01-02|2025-01-02T14:30:00Z|100.000000",
                symbol="AAPL",
                raw_id="AAPL|2025-01-02|2025-01-02T14:30:00Z|100.000000",
                bucket="high_confidence_recovered_candidate",
                tier="symbol_session_single_match",
                lineage="source_linked",
                price_rel=0.005,
                entry_ts="2025-01-02T14:30:00Z",
            ),
            _candidate(
                "MSFT|2025-01-03|2025-01-03|200.000000",
                symbol="MSFT",
                raw_id="MSFT|2025-01-03|2025-01-03|199.000000",
                bucket="high_confidence_recovered_candidate",
                tier="symbol_session_single_match",
                lineage="source_linked",
                price_rel=0.005,
                entry_ts="2025-01-03",
            ),
            _candidate(
                "NVDA|2025-01-04|2025-01-04T14:30:00Z|150.000000",
                symbol="NVDA",
                raw_id="NVDA|2025-01-04|2025-01-04T14:31:00Z|149.000000",
                bucket="high_confidence_recovered_candidate",
                tier="symbol_session_multi_match",
                lineage="source_linked",
                price_rel=0.005,
                entry_ts="2025-01-04T14:30:00Z",
                theme_group="semis_leader",
            ),
            _candidate(
                "AMD|2025-01-05|2025-01-05T14:30:00Z|120.000000",
                symbol="AMD",
                raw_id="AMD|2025-01-05|2025-01-05T14:32:00Z|119.000000",
                bucket="medium_confidence_review_queue",
                tier="symbol_session_single_match",
                lineage="replay_derived",
                price_rel=0.005,
                entry_ts="2025-01-05T14:30:00Z",
                theme_group="semis_leader",
            ),
            _candidate(
                "COST|2025-01-06|2025-01-06T14:30:00Z|500.000000",
                symbol="COST",
                raw_id="COST|2025-01-06|2025-01-06T14:32:00Z|450.000000",
                bucket="high_confidence_recovered_candidate",
                tier="symbol_session_single_match",
                lineage="source_linked",
                price_rel=0.10,
                entry_ts="2025-01-06T14:30:00Z",
                theme_group="platform_quality_leader",
            ),
            _candidate(
                "META|2025-01-07|2025-01-07T14:30:00Z|300.000000",
                symbol="META",
                raw_id="",
                bucket="high_confidence_recovered_candidate",
                tier="symbol_session_single_match",
                lineage="source_linked",
                price_rel=0.005,
                entry_ts="2025-01-07T14:30:00Z",
                theme_group="platform_quality_leader",
            ),
            _candidate(
                "ZZZ|2025-01-08|2025-01-08T14:30:00Z|50.000000",
                symbol="ZZZ",
                raw_id="",
                bucket="no_recovery_evidence",
                tier="no_recovery_evidence",
                lineage="",
                price_rel=0.0,
                entry_ts="2025-01-08T14:30:00Z",
            ),
        ]
    )
    task374 = pd.DataFrame(
        {
            "trade_id": candidates["trade_id"],
            "entry_ts": candidates["entry_ts"],
        }
    )
    lifecycle = pd.DataFrame(
        {
            "raw_trade_id": candidates["candidate_raw_trade_id"],
            "start_event_timestamp": candidates["entry_ts"],
        }
    )
    return candidates, task374, lifecycle


class IdentityReviewProtocol380Tests(unittest.TestCase):
    def _build_fixture_artifacts(self):
        candidates, task374, lifecycle = _fixtures()
        return build_identity_review_protocol_380(
            identity_candidates_df=candidates,
            p0_p1_review_df=pd.DataFrame(),
            identity_namespace_df=pd.DataFrame(),
            task374_candidates_df=task374,
            lifecycle_df=lifecycle,
        )

    def test_review_protocol_decisions_are_conservative(self) -> None:
        protocol = self._build_fixture_artifacts().identity_review_protocol_candidates.set_index("symbol")
        self.assertEqual(protocol.loc["AAPL", "review_protocol_decision_v1"], "approved_recovery_candidate")
        self.assertEqual(protocol.loc["MSFT", "review_protocol_decision_v1"], "namespace_fix_required")
        self.assertEqual(protocol.loc["NVDA", "review_protocol_decision_v1"], "manual_review_required")
        self.assertEqual(protocol.loc["AMD", "review_protocol_decision_v1"], "manual_review_required")
        self.assertEqual(protocol.loc["COST", "review_protocol_decision_v1"], "rejected_recovery_candidate")
        self.assertEqual(protocol.loc["META", "review_protocol_decision_v1"], "namespace_fix_required")
        self.assertEqual(protocol.loc["ZZZ", "review_protocol_decision_v1"], "rejected_recovery_candidate")

    def test_reviewed_layer_never_mutates_labels_or_promotes_theme(self) -> None:
        artifacts = self._build_fixture_artifacts()
        protocol = artifacts.identity_review_protocol_candidates
        self.assertEqual(int(protocol["accepted_label_update_flag"].sum()), 0)
        self.assertEqual(int(protocol["diagnostic_only_flag"].min()), 1)
        semis = protocol[protocol["theme_group"].astype(str).eq("semis_leader")]
        self.assertFalse(semis.empty)
        self.assertFalse(semis["review_protocol_decision_v1"].astype(str).eq("approved_recovery_candidate").any())

    def test_namespace_and_timestamp_audits_are_generated(self) -> None:
        artifacts = self._build_fixture_artifacts()
        namespace = artifacts.trade_id_namespace_mismatch_audit.set_index("audit_scope")
        timestamp = artifacts.timestamp_precision_audit.set_index("scope")
        self.assertGreater(int(namespace.loc["task380_protocol_candidates", "price_component_mismatch_count"]), 0)
        self.assertGreater(int(namespace.loc["task380_protocol_candidates", "date_only_timestamp_count"]), 0)
        self.assertGreater(int(timestamp.loc["all_protocol_candidates", "entry_timestamp_precision_missing_count"]), 0)

    def test_decision_allows_diagnostic_layer_only_when_approved_exists(self) -> None:
        decision = self._build_fixture_artifacts().task_380_decision.iloc[0]
        self.assertEqual(decision["task_380_verdict"], "COMPLETE_PASS")
        self.assertEqual(decision["labels_overwritten"], "NO")
        self.assertEqual(decision["task_376_ontology_relaxed"], "NO")
        self.assertEqual(decision["theme_promoted_by_task_380"], "NO")
        self.assertEqual(decision["task_381_revalidation_ready"], "YES_DIAGNOSTIC_LAYER_ONLY")

    def test_report_artifacts_are_generated(self) -> None:
        artifacts = self._build_fixture_artifacts()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            write_identity_review_protocol_380(artifacts, out_dir)
            with patch(
                "backtest.analysis_structural_breakout_identity_review_protocol_380.build_identity_review_protocol_380",
                return_value=artifacts,
            ):
                argv = sys.argv
                try:
                    sys.argv = ["identity_review_protocol_380", "--out-dir", str(out_dir)]
                    report_main()
                finally:
                    sys.argv = argv

            for name in (
                "identity_review_protocol_candidates.csv",
                "reviewed_recovery_layer.csv",
                "manual_review_required_queue.csv",
                "rejected_recovery_candidates.csv",
                "namespace_fix_required_queue.csv",
                "trade_id_namespace_mismatch_audit.csv",
                "timestamp_precision_audit.csv",
                "task_380_decision.csv",
                "task_380_identity_review_protocol.md",
            ):
                self.assertTrue((out_dir / name).exists(), name)
            report = (out_dir / "task_380_identity_review_protocol.md").read_text(encoding="utf-8-sig")
            self.assertIn("Did Task 380 overwrite labels: `NO`", report)
            self.assertIn("Did Task 380 promote AMD/semis by theme: `NO`", report)
            self.assertIn("Final Task 380 verdict: `COMPLETE_PASS`", report)


if __name__ == "__main__":
    unittest.main()
