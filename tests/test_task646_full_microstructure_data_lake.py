from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pandas as pd

from src.data.alpaca_full_microstructure_backfill import export_full_microstructure_partitioned


REPORT_DIR = Path("docs/reports/task_646_full_microstructure_data_lake")


class Task646FullMicrostructureDataLakeTest(unittest.TestCase):
    def test_task646_outputs_block_feature_builder(self) -> None:
        decision = pd.read_csv(REPORT_DIR / "task_646_decision.csv").iloc[0]
        pass_fail = pd.read_csv(REPORT_DIR / "task_646_pass_fail_matrix.csv")
        coverage = pd.read_csv(REPORT_DIR / "task_646_coverage_audit.csv")
        query_contract = pd.read_csv(REPORT_DIR / "task_646_catalog_query_contract.csv")

        self.assertEqual(decision["strategy_acceptance_status"], "NOT_ACCEPTED")
        self.assertEqual(decision["real_capital_status"], "FORBIDDEN")
        self.assertEqual(int(decision["feature_builder_allowed_flag"]), 0)
        self.assertEqual(str(decision["lake_start_date"]), "2024-01-02")
        self.assertEqual(str(decision["lake_end_date"]), "2026-06-03")

        gates = {row["gate"]: int(row["pass_flag"]) for _, row in pass_fail.iterrows()}
        self.assertEqual(gates["universe_scope_defined"], 1)
        self.assertEqual(gates["no_feature_builder_in_task646c"], 1)
        self.assertEqual(gates["coverage_sufficient_for_feature_builder"], 0)
        self.assertEqual(gates["trading_promotion"], 0)

        self.assertEqual(set(coverage["source_type"]), {"quotes", "trades"})
        self.assertTrue((coverage["missing_treated_as_negative_flag"] == 0).all())
        self.assertTrue(query_contract["forbidden_operation"].astype(str).str.contains("feature|entry|sizing|fragile", case=False).any())

    def test_full_backfill_dry_run_contract(self) -> None:
        with TemporaryDirectory() as tmp:
            result = export_full_microstructure_partitioned(
                symbols=["NVDA", "AMD"],
                start_date="2024-01-02",
                end_date="2024-01-03",
                dry_run=True,
                out_dir=Path(tmp),
            )
        self.assertEqual(len(result.audit), 56)
        self.assertTrue(result.audit["export_status"].eq("DRY_RUN").all())
        self.assertEqual(int(result.audit["secret_value_logged_flag"].sum()), 0)
        self.assertEqual(set(result.audit["source_type"]), {"quotes", "trades"})
        self.assertIn("chunk_id", result.audit.columns)

    def test_parallel_backfill_uses_bounded_worker_contract(self) -> None:
        class FakeProvider:
            def __init__(self, **_: object) -> None:
                pass

            def fetch_quotes(self, symbol: str, *, start: str, end: str) -> pd.DataFrame:
                return pd.DataFrame(
                    [
                        {
                            "symbol": symbol,
                            "quote_ts": start,
                            "bid": 10.0,
                            "ask": 10.1,
                        }
                    ]
                )

            def fetch_trades(self, symbol: str, *, start: str, end: str) -> pd.DataFrame:
                return pd.DataFrame(
                    [
                        {
                            "symbol": symbol,
                            "trade_ts": start,
                            "price": 10.05,
                            "size": 100,
                            "trade_id": f"{symbol}-{start}",
                        }
                    ]
                )

        with TemporaryDirectory() as tmp:
            audit_out = Path(tmp) / "audit.csv"
            with patch("src.data.alpaca_full_microstructure_backfill.AlpacaHistoricalMicrostructureProvider", FakeProvider):
                result = export_full_microstructure_partitioned(
                    symbols=["AMD", "NVDA"],
                    start_date="2024-01-02",
                    end_date="2024-01-02",
                    out_dir=Path(tmp) / "raw",
                    audit_out=audit_out,
                    workers=3,
                    requests_per_minute=10_000,
                    max_chunks_per_day=1,
                )
            self.assertEqual(len(result.audit), 4)
            self.assertTrue(result.audit["export_status"].eq("EXPORTED").all())
            self.assertTrue(audit_out.exists())
            self.assertEqual(len(pd.read_csv(audit_out)), 4)


if __name__ == "__main__":
    unittest.main()
