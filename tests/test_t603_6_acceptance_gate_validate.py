from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path

from scripts.acceptance_gate_validate import collect_acceptance_gate_metrics, evaluate_acceptance_gate


def _write_csv(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


class AcceptanceGateValidateTest(unittest.TestCase):
    def test_acceptance_gate_passes_when_all_required_metrics_pass(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_csv(
                root
                / "docs/reports/task_603_6_acceptance_promotion_program/program_a_broker_truth/broker_fill_coverage_summary.csv",
                {"broker_truth_sell_fills": 3},
            )
            _write_csv(
                root
                / "docs/reports/task_603_6_acceptance_promotion_program/program_b_entry_risk/entry_risk_snapshot_summary.csv",
                {"snapshot_coverage": 1.0},
            )
            _write_csv(
                root
                / "docs/reports/task_603_6_acceptance_promotion_program/program_c_replay_completeness/replay_completeness_summary.csv",
                {"position_match_rate": 1.0, "replay_completeness_score": 1.0},
            )
            _write_csv(
                root / "docs/reports/task_601_4_concentration_stability/concentration_recent_window_metrics.csv",
                {"top3_share": 0.75},
            )

            metrics = collect_acceptance_gate_metrics(root, db_path=root / "missing.db")
            evaluation = evaluate_acceptance_gate(metrics)

        self.assertEqual(evaluation["status"], "PASS")
        self.assertEqual(evaluation["blockers"], [])

    def test_acceptance_gate_fails_with_exact_blocker_list(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _write_csv(
                root / "docs/reports/task_600_4_broker_truth_exit_lifecycle/broker_truth_exit_summary.csv",
                {"broker_truth_sell_fills": 0},
            )
            _write_csv(
                root / "docs/reports/task_602_4_order_replay_recovery/task_602_4_decision.csv",
                {"position_match_rate": 0.958333},
            )
            _write_csv(
                root / "docs/reports/task_601_4_concentration_stability/concentration_recent_window_metrics.csv",
                {"top3_share": 0.80},
            )

            metrics = collect_acceptance_gate_metrics(root, db_path=root / "missing.db")
            evaluation = evaluate_acceptance_gate(metrics)

        self.assertEqual(evaluation["status"], "FAIL")
        self.assertIn("broker_truth_sell_fills <= 0", evaluation["blockers"])
        self.assertIn("snapshot_coverage <= 95%", evaluation["blockers"])
        self.assertIn("position_match_rate <= 99%", evaluation["blockers"])
        self.assertIn("top3_share >= 0.80 or missing", evaluation["blockers"])


if __name__ == "__main__":
    unittest.main()
