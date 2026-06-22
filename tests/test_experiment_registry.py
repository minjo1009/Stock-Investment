from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestExperimentRegistry(unittest.TestCase):
    def test_registry_schema_and_required_fields(self) -> None:
        from experiments.registry import ExperimentMetrics, ExperimentRecord

        record = ExperimentRecord(
            experiment_id="exp-001",
            strategy="US_BREAKOUT_V0",
            execution_policy="LIMITED_CHASE",
            risk_policy="BASELINE",
            fee=0.0025,
            slippage=0.001,
            universe="US12",
            dataset_version="us_daily_v1",
            metrics=ExperimentMetrics(pf=1.08, net_pnl=4582.87, mdd=9885.24, sharpe=0.38),
            decision="WARNING",
        )
        payload = record.to_dict()

        for key in (
            "experiment_id",
            "strategy",
            "execution_policy",
            "risk_policy",
            "fee",
            "slippage",
            "universe",
            "dataset_version",
            "metrics",
            "decision",
        ):
            with self.subTest(field=key):
                self.assertIn(key, payload)

        self.assertIn("pf", payload["metrics"])
        self.assertIn("net_pnl", payload["metrics"])
        self.assertIn("mdd", payload["metrics"])
        self.assertIn("sharpe", payload["metrics"])

    def test_save_records_roundtrip(self) -> None:
        from experiments.registry import ExperimentMetrics, ExperimentRecord, save_records

        record = ExperimentRecord(
            experiment_id="exp-002",
            strategy="US_BREAKOUT_V0",
            execution_policy="BASELINE",
            risk_policy="BASELINE",
            fee=0.0,
            slippage=0.0,
            universe="US12",
            dataset_version="us_daily_v1",
            metrics=ExperimentMetrics(pf=1.3, net_pnl=10000.0, mdd=5000.0, sharpe=1.2),
            decision="PASS",
        )

        with tempfile.TemporaryDirectory() as tmp_dir:
            out = save_records(Path(tmp_dir) / "registry.json", [record])
            self.assertTrue(out.exists())
            loaded = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(len(loaded), 1)
            self.assertEqual(loaded[0]["experiment_id"], "exp-002")
            self.assertEqual(loaded[0]["decision"], "PASS")


if __name__ == "__main__":
    unittest.main()
