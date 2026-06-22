from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.backtest.build_task523_528_gap_closure import build_task525_broker_order_fill_archive_contract


class Task525BrokerOrderFillArchiveContractTest(unittest.TestCase):
    def test_contract_contains_lineage_fields_and_keeps_task505_gap(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifacts = build_task525_broker_order_fill_archive_contract(out_dir=root / "out")
            contract = artifacts["task_525_decision"]
            self.assertEqual(int(contract.iloc[0]["contract_defined_flag"]), 1)
            self.assertEqual(int(contract.iloc[0]["historical_task505_broker_truth_available_flag"]), 0)


if __name__ == "__main__":
    unittest.main()
