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

from backtest.analysis_structural_breakout_lifecycle_recovery_378 import main as report_main
from backtest.build_lifecycle_recovery_378 import build_lifecycle_recovery_378, write_lifecycle_recovery_378


def _queue_row(
    trade_id: str,
    *,
    symbol: str,
    split: str = "train",
    bucket: str = "qualified_watchlist",
    gap_class: str = "watchlist_missing",
    theme_group: str = "non_theme",
    tier: str = "p1_watchlist_or_theme",
    risk_gate: str = "pass",
    breadth: str = "broad",
    forward_bucket: str = "high_quality",
    theme_prior: float = 0.3,
    score: float = 0.70,
) -> dict:
    return {
        "trade_id": trade_id,
        "symbol": symbol,
        "current_split": split,
        "persistence_universe_bucket": bucket,
        "lifecycle_coverage_flag": 0,
        "stateful_persistence_target_v1": None,
        "target_reason": "coverage_missing",
        "target_confidence": "low",
        "risk_gate_v1": risk_gate,
        "data_leadership_gate_v1": 1 if breadth == "broad" else 0,
        "market_breadth_state": breadth,
        "sector_leadership_state": "broad_led",
        "tech_led_narrow_flag": 0 if breadth == "broad" else 1,
        "theme_prior_v1": theme_prior,
        "forward_breakout_bucket": forward_bucket,
        "forward_persistence_score": score,
        "theme_group": theme_group,
        "coverage_gap_class": gap_class,
        "recovery_priority_tier": tier,
        "recovery_priority_score": 100 if tier == "p0_anchored_or_core" else 70,
    }


def _lifecycle_row(raw_trade_id: str, *, symbol: str, session_date: str) -> dict:
    return {
        "raw_trade_id": raw_trade_id,
        "symbol": symbol,
        "session_date": session_date,
        "event_count": 3,
        "persistence_depth": 1,
        "add_depth": 0,
        "scale_depth": 0,
        "source_linked_flag": 1,
        "fragile_transition_flag": 0,
        "invalidated_flag": 0,
        "add_confirmed_flag": 0,
        "scale_up_flag": 0,
        "persistence_confirmed_flag": 1,
        "lineage_quality": "source_linked",
        "identity_confidence": 0.9,
        "persistence_duration_minutes": 30,
        "realized_R": 0.5,
        "start_event_timestamp": "2025-01-02T14:30:00Z",
        "end_event_timestamp": "2025-01-02T15:00:00Z",
        "evaluation_scope": "full_period",
    }


def _fixtures() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    queue = pd.DataFrame(
        [
            _queue_row("AAPL|2025-01-02|2025-01-02|100.000000", symbol="AAPL", bucket="persistence_core", gap_class="core_missing", theme_group="platform_quality_leader", tier="p0_anchored_or_core", theme_prior=1.0),
            _queue_row("MSFT|2025-01-03|2025-01-03|200.000000", symbol="MSFT", bucket="persistence_core", gap_class="core_missing", theme_group="platform_quality_leader", tier="p0_anchored_or_core", theme_prior=1.0),
            _queue_row("META|2025-01-04|2025-01-04|300.000000", symbol="META", theme_group="platform_quality_leader", theme_prior=1.0),
            _queue_row("AMD|2025-01-05|2025-01-05|120.000000", symbol="AMD", split="anchored_oos", bucket="suppressed_crowding_risk", gap_class="anchored_oos_suppressed_missing", theme_group="semis_leader", tier="p2_standard", risk_gate="fail", breadth="narrow", forward_bucket="fragile_candidate", theme_prior=0.45),
            _queue_row("ZZZ|2025-01-06|2025-01-06|50.000000", symbol="ZZZ", bucket="suppressed_crowding_risk", gap_class="suppressed_missing_low_priority", tier="p3_low_priority", risk_gate="fail", breadth="narrow", forward_bucket="blocked_candidate", theme_prior=0.2),
        ]
    )
    lifecycle = pd.DataFrame(
        [
            _lifecycle_row("AAPL|2025-01-02|2025-01-02|100.000000", symbol="AAPL", session_date="2025-01-02"),
            _lifecycle_row("MSFT|2025-01-03|2025-01-03|198.000000", symbol="MSFT", session_date="2025-01-03"),
            _lifecycle_row("META|2025-01-04|2025-01-04|295.000000", symbol="META", session_date="2025-01-04"),
            _lifecycle_row("META|2025-01-04|2025-01-04|296.000000", symbol="META", session_date="2025-01-04"),
        ]
    )
    source_events = pd.DataFrame(
        [
            {
                "symbol": "AMD",
                "session_date": "2025-01-05",
                "event_type": "PERSISTENCE_CONFIRMED",
                "event_source": "SOURCE_CAPTURED",
                "source_event_id": "evt_amd",
                "lifecycle_id": "life_amd",
            }
        ]
    )
    anchored = queue[queue["current_split"].eq("anchored_oos")].copy()
    anchored["coverage_status"] = "coverage_missing"
    anchored["core_miss_reasons"] = "risk_gate_fail|breadth_not_broad|theme_prior_not_core"
    theme = queue[queue["theme_group"].ne("non_theme")].copy()
    theme["theme_audit_status"] = "theme_suppressed_by_risk"
    theme["core_miss_reasons"] = "theme_prior_not_core"
    return queue, lifecycle, source_events, anchored, theme


class LifecycleRecovery378Tests(unittest.TestCase):
    def _build_fixture_artifacts(self):
        queue, lifecycle, source_events, anchored, theme = _fixtures()
        return build_lifecycle_recovery_378(
            recovery_queue_df=queue,
            lifecycle_df=lifecycle,
            source_event_df=source_events,
            anchored_audit_df=anchored,
            theme_audit_df=theme,
            evaluation_panel_df=pd.DataFrame(),
        )

    def test_matching_tiers_are_detected_without_label_updates(self) -> None:
        matches = self._build_fixture_artifacts().lifecycle_recovery_candidate_matches.set_index("trade_id")
        self.assertEqual(matches.loc["AAPL|2025-01-02|2025-01-02|100.000000", "recovery_match_tier"], "exact_trade_id_match")
        self.assertEqual(matches.loc["MSFT|2025-01-03|2025-01-03|200.000000", "recovery_match_tier"], "symbol_session_single_match")
        self.assertEqual(matches.loc["META|2025-01-04|2025-01-04|300.000000", "recovery_match_tier"], "symbol_session_multi_match")
        self.assertEqual(matches.loc["AMD|2025-01-05|2025-01-05|120.000000", "recovery_match_tier"], "source_event_candidate_match")
        self.assertEqual(matches.loc["ZZZ|2025-01-06|2025-01-06|50.000000", "recovery_match_tier"], "no_recovery_evidence")
        self.assertEqual(int(matches["accepted_label_update_flag"].sum()), 0)

    def test_root_cause_and_theme_rows_remain_diagnostic(self) -> None:
        artifacts = self._build_fixture_artifacts()
        status = artifacts.recovery_priority_status.set_index("trade_id")
        self.assertIn("coverage_identity_gap", str(status.loc["MSFT|2025-01-03|2025-01-03|200.000000", "root_cause_class"]))
        self.assertIn("risk_or_breadth_suppression", str(status.loc["AMD|2025-01-05|2025-01-05|120.000000", "root_cause_class"]))
        theme = artifacts.theme_leader_root_cause_audit
        self.assertEqual(int(theme["theme_promoted_by_task_378_flag"].sum()), 0)
        self.assertEqual(int(theme["accepted_label_update_flag"].fillna(0).sum()), 0)

    def test_anchored_oos_remains_diagnostic_only(self) -> None:
        anchored = self._build_fixture_artifacts().anchored_oos_recovery_audit
        self.assertIn("diagnostic_only_undercovered", set(anchored["anchored_oos_interpretability_status"].astype(str)))
        self.assertEqual(int(anchored["accepted_label_update_flag"].fillna(0).sum()), 0)

    def test_decision_preserves_strategy_acceptance(self) -> None:
        decision = self._build_fixture_artifacts().task_378_decision.iloc[0]
        self.assertEqual(decision["task_378_verdict"], "COMPLETE_PASS")
        self.assertEqual(decision["strategy_acceptance_status"], "UNCHANGED_EXPANDED_SAMPLE_REQUIRED")
        self.assertEqual(decision["task_376_ontology_relaxed"], "NO")
        self.assertEqual(decision["theme_promoted_by_task_378"], "NO")
        self.assertEqual(decision["anchored_oos_core_absence_interpretable"], "NO")
        self.assertEqual(decision["next_priority"], "manual_identity_review_for_p0_p1")

    def test_report_artifacts_are_generated(self) -> None:
        artifacts = self._build_fixture_artifacts()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            write_lifecycle_recovery_378(artifacts, out_dir)
            with patch(
                "backtest.analysis_structural_breakout_lifecycle_recovery_378.build_lifecycle_recovery_378",
                return_value=artifacts,
            ):
                argv = sys.argv
                try:
                    sys.argv = ["lifecycle_recovery_378", "--out-dir", str(out_dir)]
                    report_main()
                finally:
                    sys.argv = argv

            for name in (
                "lifecycle_recovery_candidate_matches.csv",
                "recovery_priority_status.csv",
                "anchored_oos_recovery_audit.csv",
                "core_miss_root_cause_audit.csv",
                "theme_leader_root_cause_audit.csv",
                "lifecycle_recovery_sample_adequacy.csv",
                "task_378_decision.csv",
                "task_378_lifecycle_recovery.md",
            ):
                self.assertTrue((out_dir / name).exists(), name)
            report = (out_dir / "task_378_lifecycle_recovery.md").read_text(encoding="utf-8-sig")
            self.assertIn("Did Task 378 relax Task 376 ontology: `NO`", report)
            self.assertIn("Did Task 378 promote AMD/semis by theme: `NO`", report)
            self.assertIn("Final Task 378 verdict: `COMPLETE_PASS`", report)


if __name__ == "__main__":
    unittest.main()
