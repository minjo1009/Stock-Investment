from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestTask088EvidenceDecision(unittest.TestCase):
    def test_empty_evidence_folder_warning(self) -> None:
        from app.task_088_evidence_decision import evaluate_aggregate_status

        summary = {
            "trading_days_observed": 0,
            "order_attempts": 0,
            "filled_orders": 0,
            "cancelled_orders": 0,
            "eod_reviews_completed": 0,
            "reconciliation_checks": 0,
            "unknown_events": 0,
            "reconciliation_critical_count": 0,
            "unresolved_late_fill": 0,
            "market_order_path_count": 0,
            "risk_guard_breach_count": 0,
            "live_env_count": 0,
            "cancel_success_rate": 0.0,
            "slippage_drift_flag": False,
            "data_fresh_ratio": 0.0,
            "missing_bar_ratio": 1.0,
        }
        status, _, warnings = evaluate_aggregate_status(summary)
        self.assertEqual(status, "WARNING")
        self.assertIn("MINIMUM_SAMPLE_NOT_MET", warnings)

    def test_unknown_event_fail(self) -> None:
        from app.task_088_evidence_decision import evaluate_aggregate_status

        summary = {
            "trading_days_observed": 5,
            "order_attempts": 10,
            "filled_orders": 5,
            "cancelled_orders": 1,
            "eod_reviews_completed": 5,
            "reconciliation_checks": 5,
            "unknown_events": 1,
            "reconciliation_critical_count": 0,
            "unresolved_late_fill": 0,
            "market_order_path_count": 0,
            "risk_guard_breach_count": 0,
            "live_env_count": 0,
            "cancel_success_rate": 1.0,
            "slippage_drift_flag": False,
            "data_fresh_ratio": 1.0,
            "missing_bar_ratio": 0.0,
        }
        status, failures, _ = evaluate_aggregate_status(summary)
        self.assertEqual(status, "FAIL")
        self.assertIn("UNKNOWN_EVENT_DETECTED", failures)

    def test_threshold_met_pass(self) -> None:
        from app.task_088_evidence_decision import evaluate_aggregate_status

        summary = {
            "trading_days_observed": 5,
            "order_attempts": 12,
            "filled_orders": 6,
            "cancelled_orders": 2,
            "eod_reviews_completed": 5,
            "reconciliation_checks": 6,
            "unknown_events": 0,
            "reconciliation_critical_count": 0,
            "unresolved_late_fill": 0,
            "market_order_path_count": 0,
            "risk_guard_breach_count": 0,
            "live_env_count": 0,
            "cancel_success_rate": 1.0,
            "slippage_drift_flag": False,
            "data_fresh_ratio": 1.0,
            "missing_bar_ratio": 0.0,
        }
        status, failures, warnings = evaluate_aggregate_status(summary)
        self.assertEqual(status, "PASS")
        self.assertEqual(failures, [])
        self.assertEqual(warnings, [])

    def test_malformed_evidence_is_ignored_safely(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runs_dir = root / "runs"
            runs_dir.mkdir(parents=True, exist_ok=True)
            (runs_dir / "bad.json").write_text("{malformed", encoding="utf-8")
            (runs_dir / "ok.json").write_text(
                json.dumps(
                    {
                        "run_id": "r1",
                        "started_at": "2026-04-24T10:00:00Z",
                        "ended_at": "2026-04-24T10:05:00Z",
                        "status": "WARNING",
                        "order_attempts": 0,
                        "submitted_orders": 0,
                        "filled_orders": 0,
                        "cancelled_orders": 0,
                        "partial_fills": 0,
                        "late_fills": 0,
                        "timeout_events": 0,
                        "unknown_events": 0,
                        "reconciliation_checks": 0,
                        "reconciliation_critical_count": 0,
                        "average_slippage": 0.0,
                        "max_slippage": 0.0,
                        "realized_pnl": 0.0,
                        "eod_review_completed": False,
                    }
                ),
                encoding="utf-8",
            )
            out_json = root / "summary.json"
            out_md = root / "summary.md"
            env = dict(os.environ)
            env["PYTHONPATH"] = str(SRC)
            cmd = [
                sys.executable,
                "-m",
                "app.task_088_evidence_decision",
                "--runs-dir",
                str(runs_dir),
                "--json-out",
                str(out_json),
                "--md-out",
                str(out_md),
            ]
            proc = subprocess.run(cmd, check=False, capture_output=True, text=True, env=env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            payload = json.loads(out_json.read_text(encoding="utf-8"))
            self.assertEqual(payload["final_decision"]["status"], "WARNING")
            self.assertGreaterEqual(len(payload["ignored_files"]), 1)


if __name__ == "__main__":
    unittest.main()
