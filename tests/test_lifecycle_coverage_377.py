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

from backtest.analysis_structural_breakout_lifecycle_coverage_377 import main as report_main
from backtest.build_lifecycle_coverage_expansion_377 import (
    build_lifecycle_coverage_expansion_377,
    write_lifecycle_coverage_expansion_377,
)


def _row(
    trade_id: str,
    *,
    symbol: str,
    split: str,
    bucket: str,
    covered: int,
    target: float | None,
    risk_gate: str,
    breadth: str,
    forward_bucket: str,
    score: float,
    theme_prior: float,
) -> dict:
    return {
        "trade_id": trade_id,
        "symbol": symbol,
        "current_split": split,
        "persistence_universe_bucket": bucket,
        "lifecycle_coverage_flag": covered,
        "stateful_persistence_target_v1": target,
        "target_reason": "coverage_missing" if not covered else "no_stateful_persistence",
        "target_confidence": "low" if not covered else "high",
        "risk_gate_v1": risk_gate,
        "data_leadership_gate_v1": 1 if breadth == "broad" else 0,
        "market_breadth_state": breadth,
        "sector_leadership_state": "broad_led",
        "tech_led_narrow_flag": 0 if breadth == "broad" else 1,
        "theme_prior_v1": theme_prior,
        "forward_breakout_bucket": forward_bucket,
        "forward_persistence_score": score,
    }


def _evaluation_fixture() -> pd.DataFrame:
    return pd.DataFrame(
        [
            _row(
                "anchored_watch_missing",
                symbol="AMD",
                split="anchored_oos",
                bucket="qualified_watchlist",
                covered=0,
                target=None,
                risk_gate="pass",
                breadth="broad",
                forward_bucket="high_quality",
                score=0.72,
                theme_prior=0.45,
            ),
            _row(
                "anchored_core_covered",
                symbol="AAPL",
                split="anchored_oos",
                bucket="persistence_core",
                covered=1,
                target=1.0,
                risk_gate="pass",
                breadth="broad",
                forward_bucket="high_quality",
                score=0.82,
                theme_prior=1.0,
            ),
            _row(
                "anchored_suppressed_missing",
                symbol="NVDA",
                split="anchored_oos",
                bucket="suppressed_crowding_risk",
                covered=0,
                target=None,
                risk_gate="fail",
                breadth="narrow",
                forward_bucket="fragile_candidate",
                score=0.50,
                theme_prior=0.45,
            ),
            _row(
                "train_core_missing",
                symbol="MSFT",
                split="train",
                bucket="persistence_core",
                covered=0,
                target=None,
                risk_gate="pass",
                breadth="broad",
                forward_bucket="high_quality",
                score=0.80,
                theme_prior=1.0,
            ),
            _row(
                "train_suppressed_missing",
                symbol="ZZZ",
                split="train",
                bucket="suppressed_crowding_risk",
                covered=0,
                target=None,
                risk_gate="fail",
                breadth="narrow",
                forward_bucket="blocked_candidate",
                score=0.40,
                theme_prior=0.2,
            ),
            _row(
                "train_core_covered",
                symbol="AAPL",
                split="train",
                bucket="persistence_core",
                covered=1,
                target=1.0,
                risk_gate="pass",
                breadth="broad",
                forward_bucket="high_quality",
                score=0.82,
                theme_prior=1.0,
            ),
        ]
    )


class LifecycleCoverage377Tests(unittest.TestCase):
    def _build_fixture_artifacts(self):
        return build_lifecycle_coverage_expansion_377(evaluation_panel_df=_evaluation_fixture())

    def test_missing_lifecycle_is_classified_without_negative_target(self) -> None:
        audit = self._build_fixture_artifacts().coverage_gap_audit.set_index("trade_id")
        self.assertIn("train_core_missing", audit.index)
        self.assertTrue(pd.isna(audit.loc["train_core_missing", "stateful_persistence_target_v1"]))
        self.assertEqual(str(audit.loc["train_core_missing", "coverage_gap_class"]), "core_missing")
        self.assertEqual(str(audit.loc["anchored_watch_missing", "coverage_gap_class"]), "anchored_oos_core_or_watchlist_missing")
        self.assertEqual(str(audit.loc["anchored_suppressed_missing", "coverage_gap_class"]), "anchored_oos_suppressed_missing")

    def test_anchored_oos_core_miss_reasons_are_generated(self) -> None:
        anchored = self._build_fixture_artifacts().anchored_oos_core_miss_audit.set_index("trade_id")
        self.assertIn("anchored_watch_missing", anchored.index)
        self.assertEqual(str(anchored.loc["anchored_core_covered", "core_miss_reasons"]), "already_core")
        self.assertIn("theme_prior_not_core", str(anchored.loc["anchored_watch_missing", "core_miss_reasons"]))
        self.assertEqual(str(anchored.loc["anchored_watch_missing", "coverage_status"]), "coverage_missing")
        self.assertNotIn("coverage_missing", str(anchored.loc["anchored_watch_missing", "core_miss_reasons"]))
        self.assertIn("risk_gate_fail", str(anchored.loc["anchored_suppressed_missing", "core_miss_reasons"]))

    def test_theme_leader_audit_includes_semis_and_platform(self) -> None:
        theme = self._build_fixture_artifacts().theme_leader_miss_audit
        groups = set(theme["theme_group"].astype(str))
        self.assertIn("semis_leader", groups)
        self.assertIn("platform_quality_leader", groups)
        status = theme.set_index("trade_id")
        self.assertEqual(str(status.loc["anchored_suppressed_missing", "theme_audit_status"]), "theme_suppressed_by_risk")
        self.assertEqual(str(status.loc["anchored_core_covered", "theme_audit_status"]), "theme_core_covered")

    def test_recovery_priority_ranks_anchored_and_core_above_suppressed_low_priority(self) -> None:
        queue = self._build_fixture_artifacts().recovery_priority_queue.set_index("trade_id")
        self.assertGreater(
            int(queue.loc["anchored_watch_missing", "recovery_priority_score"]),
            int(queue.loc["train_suppressed_missing", "recovery_priority_score"]),
        )
        self.assertGreater(
            int(queue.loc["train_core_missing", "recovery_priority_score"]),
            int(queue.loc["train_suppressed_missing", "recovery_priority_score"]),
        )

    def test_report_artifacts_are_generated(self) -> None:
        artifacts = self._build_fixture_artifacts()
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir)
            write_lifecycle_coverage_expansion_377(artifacts, out_dir)
            with patch(
                "backtest.analysis_structural_breakout_lifecycle_coverage_377.build_lifecycle_coverage_expansion_377",
                return_value=artifacts,
            ):
                argv = sys.argv
                try:
                    sys.argv = ["lifecycle_coverage_377", "--out-dir", str(out_dir)]
                    report_main()
                finally:
                    sys.argv = argv

            for name in (
                "task_377_coverage_gap_audit.csv",
                "task_377_anchored_oos_core_miss_audit.csv",
                "task_377_theme_leader_miss_audit.csv",
                "task_377_recovery_priority_queue.csv",
                "task_377_summary_decision.csv",
                "task_377_lifecycle_coverage_expansion.md",
            ):
                self.assertTrue((out_dir / name).exists(), name)

            report_text = (out_dir / "task_377_lifecycle_coverage_expansion.md").read_text(encoding="utf-8-sig")
            self.assertIn("Complete-Pass Checklist", report_text)
            self.assertIn("Final Task 377 verdict: `COMPLETE_PASS`", report_text)
            self.assertIn("lifecycle coverage", report_text.lower())


if __name__ == "__main__":
    unittest.main()
