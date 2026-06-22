from __future__ import annotations

import csv
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestBackendAccelerators(unittest.TestCase):
    def _fixture(self) -> Path:
        temp_dir = Path(tempfile.mkdtemp(prefix="backend-accelerator-"))
        path = temp_dir / "strict_gate_fixture.csv"
        rows = [
            {"symbol": "A", "event_family": "SEC", "strict_gate_pass": "1"},
            {"symbol": "A", "event_family": "SEC", "strict_gate_pass": "0"},
            {"symbol": "B", "event_family": "RATES", "strict_gate_pass": "1"},
            {"symbol": "B", "event_family": "RATES", "strict_gate_pass": ""},
        ]
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["symbol", "event_family", "strict_gate_pass"])
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_auto_prefers_polars_when_available_and_matches_pandas(self) -> None:
        from src.infra.accelerators import BackendAccelerationEngine, strict_gate_aggregate_accelerated

        result = strict_gate_aggregate_accelerated(
            self._fixture(),
            ["symbol", "event_family"],
            engine=BackendAccelerationEngine.AUTO,
        )

        self.assertIn(result.decision.selected_engine, {BackendAccelerationEngine.POLARS, BackendAccelerationEngine.DUCKDB, BackendAccelerationEngine.PANDAS})
        self.assertTrue(result.decision.parity_pass)
        self.assertEqual(result.result.metrics.source_row_count, 4)
        self.assertEqual(result.result.metrics.strict_gate_pass_total, 2)

    def test_polars_path_matches_pandas_baseline(self) -> None:
        from src.infra.accelerators import BackendAccelerationEngine, strict_gate_aggregate_accelerated

        result = strict_gate_aggregate_accelerated(
            self._fixture(),
            ["symbol", "event_family"],
            engine=BackendAccelerationEngine.POLARS,
        )

        self.assertTrue(result.decision.parity_checked)
        self.assertTrue(result.decision.parity_pass)
        self.assertEqual(result.decision.selected_engine, BackendAccelerationEngine.POLARS)

    def test_duckdb_path_matches_pandas_baseline(self) -> None:
        from src.infra.accelerators import BackendAccelerationEngine, strict_gate_aggregate_accelerated

        result = strict_gate_aggregate_accelerated(
            self._fixture(),
            ["symbol", "event_family"],
            engine=BackendAccelerationEngine.DUCKDB,
        )

        self.assertTrue(result.decision.parity_checked)
        self.assertTrue(result.decision.parity_pass)
        self.assertEqual(result.decision.selected_engine, BackendAccelerationEngine.DUCKDB)

    def test_invalid_engine_is_rejected(self) -> None:
        from src.infra.accelerators import strict_gate_aggregate_accelerated

        with self.assertRaises(ValueError):
            strict_gate_aggregate_accelerated(self._fixture(), ["symbol"], engine="openbb")

    def test_can_reuse_pandas_baseline_for_repeated_engine_checks(self) -> None:
        from src.infra.accelerators import BackendAccelerationEngine, strict_gate_aggregate_accelerated

        fixture = self._fixture()
        first = strict_gate_aggregate_accelerated(
            fixture,
            ["symbol", "event_family"],
            engine=BackendAccelerationEngine.POLARS,
        )
        second = strict_gate_aggregate_accelerated(
            fixture,
            ["symbol", "event_family"],
            engine=BackendAccelerationEngine.DUCKDB,
            pandas_baseline=first.pandas_baseline,
        )

        self.assertIsNotNone(first.pandas_baseline)
        self.assertIs(second.pandas_baseline, first.pandas_baseline)
        self.assertTrue(second.decision.parity_pass)

    def test_grouped_numeric_auto_matches_pandas_with_null_keys_and_non_null_count(self) -> None:
        from src.infra.accelerators import (
            GroupedAggregationMeasure,
            GroupedAggregationOp,
            grouped_numeric_aggregate_accelerated,
        )

        frame = pd.DataFrame(
            [
                {"bucket": "A", "regime": "up", "lifecycle_id": "L1", "net": 0.10, "win": 1.0},
                {"bucket": "A", "regime": "up", "lifecycle_id": None, "net": None, "win": 0.0},
                {"bucket": "B", "regime": None, "lifecycle_id": "L3", "net": -0.20, "win": 0.0},
                {"bucket": None, "regime": "down", "lifecycle_id": "L4", "net": 0.30, "win": 1.0},
            ]
        )

        result = grouped_numeric_aggregate_accelerated(
            frame,
            ["bucket", "regime"],
            [
                GroupedAggregationMeasure("lifecycle_id", "lifecycle_count", GroupedAggregationOp.COUNT_NON_NULL),
                GroupedAggregationMeasure("net", "avg_net_pct", GroupedAggregationOp.MEAN, scale=100.0),
                GroupedAggregationMeasure("net", "total_net", GroupedAggregationOp.SUM),
                GroupedAggregationMeasure("win", "win_rate", GroupedAggregationOp.MEAN),
            ],
            dropna=False,
        )

        self.assertTrue(result.decision.parity_pass)
        self.assertEqual(list(result.result.frame.columns), ["bucket", "regime", "lifecycle_count", "avg_net_pct", "total_net", "win_rate"])
        self.assertEqual(len(result.result.frame), 3)
        group_a = result.result.frame[(result.result.frame["bucket"] == "A") & (result.result.frame["regime"] == "up")].iloc[0]
        self.assertEqual(int(group_a["lifecycle_count"]), 1)
        self.assertAlmostEqual(float(group_a["avg_net_pct"]), 10.0)
        self.assertAlmostEqual(float(group_a["win_rate"]), 0.5)

    def test_grouped_numeric_can_reuse_pandas_baseline(self) -> None:
        from src.infra.accelerators import BackendAccelerationEngine, GroupedAggregationMeasure, grouped_numeric_aggregate_accelerated

        frame = pd.DataFrame(
            [
                {"bucket": "A", "value": 1.0},
                {"bucket": "A", "value": 2.0},
                {"bucket": "B", "value": 3.0},
            ]
        )
        measures = [GroupedAggregationMeasure("value", "value_sum", "sum")]
        first = grouped_numeric_aggregate_accelerated(frame, ["bucket"], measures, engine=BackendAccelerationEngine.POLARS)
        second = grouped_numeric_aggregate_accelerated(
            frame,
            ["bucket"],
            measures,
            engine=BackendAccelerationEngine.DUCKDB,
            pandas_baseline=first.pandas_baseline,
        )

        self.assertIsNotNone(first.pandas_baseline)
        self.assertIs(second.pandas_baseline, first.pandas_baseline)
        self.assertTrue(second.decision.parity_pass)


if __name__ == "__main__":
    unittest.main()
