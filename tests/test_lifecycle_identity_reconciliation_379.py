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

from backtest.analysis_structural_breakout_lifecycle_identity_reconciliation_379 import main as report_main
from backtest.build_lifecycle_identity_reconciliation_379 import (
    build_lifecycle_identity_reconciliation_379,
    write_lifecycle_identity_reconciliation_379,
)


def _match_row(
    trade_id: str,
    *,
    symbol: str,
    candidate_raw_trade_id: str,
    tier: str,
    lineage: str,
    price_abs_diff: float,
    entry_price: float,
    event_count: int,
    priority: str = "p1_watchlist_or_theme",
    theme_group: str = "non_theme",
) -> dict:
    return {
        "trade_id": trade_id,
        "symbol": symbol,
        "current_split": "train",
        "persistence_universe_bucket": "qualified_watchlist",
        "coverage_gap_class": "watchlist_missing",
        "theme_group": theme_group,
        "recovery_priority_tier": priority,
        "recovery_priority_score": 80,
        "entry_price": entry_price,
        "candidate_raw_trade_id": candidate_raw_trade_id,
        "candidate_raw_entry_price": entry_price - price_abs_diff,
        "candidate_identity_confidence": 0.9 if lineage == "source_linked" else 0.35,
        "candidate_lineage_quality": lineage,
        "candidate_event_count": event_count,
        "candidate_diagnostic_stateful_target": 1,
        "recovery_match_tier": tier,
        "price_abs_diff": price_abs_diff,
        "candidate_recovery_match_flag": int(tier != "no_recovery_evidence"),
        "accepted_label_update_flag": 0,
        "diagnostic_only_flag": 1,
    }


def _lifecycle_row(raw_trade_id: str, *, start_ts: str, source_linked: int = 1) -> dict:
    return {
        "raw_trade_id": raw_trade_id,
        "start_event_timestamp": start_ts,
        "end_event_timestamp": start_ts,
        "identity_origin": "explicit_trade_identity" if source_linked else "replay_fallback_identity",
        "source_linked_flag": source_linked,
        "replay_derived_only": 0 if source_linked else 1,
    }


def _fixtures() -> tuple[pd.DataFrame, pd.DataFrame]:
    matches = pd.DataFrame(
        [
            _match_row(
                "AAPL|2025-01-02|2025-01-02T14:30:00Z|100.000000",
                symbol="AAPL",
                candidate_raw_trade_id="AAPL|2025-01-02|2025-01-02T14:30:00Z|100.000000",
                tier="exact_trade_id_match",
                lineage="source_linked",
                price_abs_diff=0.0,
                entry_price=100.0,
                event_count=4,
                priority="p0_anchored_or_core",
            ),
            _match_row(
                "MSFT|2025-01-02|2025-01-02T14:30:00Z|200.000000",
                symbol="MSFT",
                candidate_raw_trade_id="MSFT|2025-01-02|2025-01-02T14:32:00Z|199.000000",
                tier="symbol_session_single_match",
                lineage="source_linked",
                price_abs_diff=1.0,
                entry_price=200.0,
                event_count=3,
            ),
            _match_row(
                "AMD|2025-01-02|2025-01-02T14:30:00Z|120.000000",
                symbol="AMD",
                candidate_raw_trade_id="AMD|2025-01-02|2025-01-02T14:32:00Z|119.000000",
                tier="symbol_session_single_match",
                lineage="replay_derived",
                price_abs_diff=1.0,
                entry_price=120.0,
                event_count=3,
                theme_group="semis_leader",
            ),
            _match_row(
                "COST|2025-01-02|2025-01-02T14:30:00Z|500.000000",
                symbol="COST",
                candidate_raw_trade_id="COST|2025-01-02|2025-01-02T14:32:00Z|470.000000",
                tier="symbol_session_single_match",
                lineage="source_linked",
                price_abs_diff=30.0,
                entry_price=500.0,
                event_count=3,
                theme_group="platform_quality_leader",
            ),
            _match_row(
                "META|2025-01-02|2025-01-02T14:30:00Z|300.000000",
                symbol="META",
                candidate_raw_trade_id="META|2025-01-02|2025-01-02T22:00:00Z|299.000000",
                tier="symbol_session_single_match",
                lineage="source_linked",
                price_abs_diff=1.0,
                entry_price=300.0,
                event_count=3,
                theme_group="platform_quality_leader",
            ),
            _match_row(
                "NVDA|2025-01-02|2025-01-02T14:30:00Z|150.000000",
                symbol="NVDA",
                candidate_raw_trade_id="NVDA|2025-01-02|2025-01-02T14:31:00Z|149.000000",
                tier="symbol_session_multi_match",
                lineage="source_linked",
                price_abs_diff=1.0,
                entry_price=150.0,
                event_count=3,
                theme_group="semis_leader",
            ),
            _match_row(
                "ZZZ|2025-01-02|2025-01-02T14:30:00Z|50.000000",
                symbol="ZZZ",
                candidate_raw_trade_id="",
                tier="no_recovery_evidence",
                lineage="",
                price_abs_diff=0.0,
                entry_price=50.0,
                event_count=0,
                priority="p3_low_priority",
            ),
        ]
    )
    lifecycle = pd.DataFrame(
        [
            _lifecycle_row("AAPL|2025-01-02|2025-01-02T14:30:00Z|100.000000", start_ts="2025-01-02T14:30:00Z"),
            _lifecycle_row("MSFT|2025-01-02|2025-01-02T14:32:00Z|199.000000", start_ts="2025-01-02T14:32:00Z"),
            _lifecycle_row("AMD|2025-01-02|2025-01-02T14:32:00Z|119.000000", start_ts="2025-01-02T14:32:00Z", source_linked=0),
            _lifecycle_row("COST|2025-01-02|2025-01-02T14:32:00Z|470.000000", start_ts="2025-01-02T14:32:00Z"),
            _lifecycle_row("META|2025-01-02|2025-01-02T22:00:00Z|299.000000", start_ts="2025-01-02T22:00:00Z"),
            _lifecycle_row("NVDA|2025-01-02|2025-01-02T14:31:00Z|149.000000", start_ts="2025-01-02T14:31:00Z"),
        ]
    )
    return matches, lifecycle


class LifecycleIdentityReconciliation379Tests(unittest.TestCase):
    def _build_fixture_artifacts(self):
        matches, lifecycle = _fixtures()
        return build_lifecycle_identity_reconciliation_379(
            recovery_matches_df=matches,
            recovery_priority_df=pd.DataFrame(),
            task_378_decision_df=pd.DataFrame(),
            lifecycle_df=lifecycle,
        )

    def test_confidence_buckets_respect_lineage_price_and_time(self) -> None:
        candidates = self._build_fixture_artifacts().identity_reconciliation_candidates.set_index("symbol")
        self.assertEqual(candidates.loc["AAPL", "identity_confidence_bucket_v1"], "high_confidence_recovered_candidate")
        self.assertEqual(candidates.loc["MSFT", "identity_confidence_bucket_v1"], "high_confidence_recovered_candidate")
        self.assertNotEqual(candidates.loc["AMD", "identity_confidence_bucket_v1"], "high_confidence_recovered_candidate")
        self.assertEqual(candidates.loc["COST", "price_distance_status"], "price_blocked")
        self.assertEqual(candidates.loc["META", "time_distance_status"], "time_blocked")
        self.assertEqual(candidates.loc["ZZZ", "identity_confidence_bucket_v1"], "no_recovery_evidence")

    def test_no_labels_are_overwritten_and_theme_is_not_promoted(self) -> None:
        candidates = self._build_fixture_artifacts().identity_reconciliation_candidates
        self.assertEqual(int(candidates["accepted_label_update_flag"].sum()), 0)
        self.assertEqual(int(candidates["diagnostic_only_flag"].min()), 1)
        semis = candidates[candidates["theme_group"].astype(str).eq("semis_leader")]
        self.assertFalse(semis.empty)

    def test_namespace_audit_flags_exact_trade_id_failure(self) -> None:
        namespace = self._build_fixture_artifacts().identity_namespace_audit.iloc[0]
        self.assertEqual(namespace["namespace_status"], "exact_trade_id_reconciliation_failure")
        self.assertGreaterEqual(int(namespace["symbol_session_candidate_rows"]), 1)

    def test_decision_preserves_acceptance_and_blocks_revalidation(self) -> None:
        decision = self._build_fixture_artifacts().task_379_decision.iloc[0]
        self.assertEqual(decision["task_379_verdict"], "COMPLETE_PASS")
        self.assertEqual(decision["strategy_acceptance_status"], "UNCHANGED_EXPANDED_SAMPLE_REQUIRED")
        self.assertEqual(decision["task_376_ontology_relaxed"], "NO")
        self.assertEqual(decision["theme_promoted_by_task_379"], "NO")
        self.assertEqual(decision["labels_overwritten"], "NO")
        self.assertEqual(decision["task_381_revalidation_ready"], "NO")

    def test_report_artifacts_are_generated(self) -> None:
        artifacts = self._build_fixture_artifacts()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            write_lifecycle_identity_reconciliation_379(artifacts, out_dir)
            with patch(
                "backtest.analysis_structural_breakout_lifecycle_identity_reconciliation_379.build_lifecycle_identity_reconciliation_379",
                return_value=artifacts,
            ):
                argv = sys.argv
                try:
                    sys.argv = ["identity_reconciliation_379", "--out-dir", str(out_dir)]
                    report_main()
                finally:
                    sys.argv = argv

            for name in (
                "identity_reconciliation_candidates.csv",
                "identity_confidence_audit.csv",
                "p0_p1_identity_review_queue.csv",
                "high_confidence_recovered_candidates.csv",
                "medium_confidence_review_queue.csv",
                "low_confidence_reject_queue.csv",
                "identity_namespace_audit.csv",
                "task_379_decision.csv",
                "task_379_lifecycle_identity_reconciliation.md",
            ):
                self.assertTrue((out_dir / name).exists(), name)
            report = (out_dir / "task_379_lifecycle_identity_reconciliation.md").read_text(encoding="utf-8-sig")
            self.assertIn("Did Task 379 overwrite labels: `NO`", report)
            self.assertIn("Did Task 379 promote AMD/semis by theme: `NO`", report)
            self.assertIn("Final Task 379 verdict: `COMPLETE_PASS`", report)


if __name__ == "__main__":
    unittest.main()
