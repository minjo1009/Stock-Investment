from __future__ import annotations

import csv
from pathlib import Path
import tempfile
import unittest

from scripts.trader_brain_840_849_program_validate import validate as validate_program
from scripts.trader_brain_backtest_dry_replay_harness import build_run_plan
from scripts.trader_brain_backtest_harness_artifact_audit import audit_artifacts


ROOT = Path(__file__).resolve().parents[1]
INPUT_MANIFEST = ROOT / "docs/reports/task_841_backtest_input_manifest_schema/backtest_input_manifest.csv"
MARKET_DATA_GATE = ROOT / "docs/reports/task_843_market_data_source_gate/market_data_source_gate.csv"
REPLAY_CONFIG = ROOT / "docs/reports/task_844_replay_config_contract/replay_config_contract.csv"
RUN_PLAN = ROOT / "docs/reports/task_845_no_execution_dry_replay_harness/harness_run_plan.csv"
RUN_SUMMARY = ROOT / "docs/reports/task_845_no_execution_dry_replay_harness/harness_run_summary.csv"
GO_NO_GO = ROOT / "docs/reports/task_849_first_controlled_backtest_go_no_go/go_no_go_matrix.csv"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


class TraderBrain840849BacktestHarnessTest(unittest.TestCase):
    def test_dry_harness_blocks_before_replay(self) -> None:
        plan_rows, summary_rows, errors = build_run_plan(INPUT_MANIFEST, MARKET_DATA_GATE, REPLAY_CONFIG, "unit_test_run")
        self.assertEqual([], errors)
        self.assertEqual(2, len(plan_rows))
        self.assertTrue(all(row["dry_run_state"] == "blocked_before_replay" for row in plan_rows))
        self.assertEqual("0", summary_rows[0]["trade_row_count"])
        self.assertEqual("0", summary_rows[0]["pnl_metric_count"])
        self.assertEqual("0", summary_rows[0]["engine_call_count"])

    def test_artifact_audit_passes_current_outputs(self) -> None:
        audit_rows, errors = audit_artifacts(RUN_PLAN, RUN_SUMMARY)
        self.assertEqual([], errors)
        self.assertEqual("pass", audit_rows[0]["audit_state"])

    def test_artifact_audit_rejects_trade_like_columns(self) -> None:
        rows = read_csv(RUN_PLAN)
        rows[0]["pnl"] = "1.0"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad_run_plan.csv"
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
                writer.writeheader()
                writer.writerows(rows)
            _audit_rows, errors = audit_artifacts(path, RUN_SUMMARY)
        self.assertTrue(any("forbidden execution columns" in error for error in errors))

    def test_first_controlled_backtest_run_is_no_go(self) -> None:
        rows = read_csv(GO_NO_GO)
        self.assertTrue(any(row["decision_area"] == "first_controlled_backtest_run" and row["status"] == "no_go" for row in rows))

    def test_program_validator_passes(self) -> None:
        self.assertEqual([], validate_program())


if __name__ == "__main__":
    unittest.main()
