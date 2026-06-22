from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


class TestTask089MarketSignalRefresh(unittest.TestCase):
    def test_runtime_appended_price_is_fresh_and_has_source_metadata(self) -> None:
        from app.task_089_market_data_signal_refresh import _build_indicator_input, _compute_row
        from backtest.data_loader import DEFAULT_BASE_DIR

        frame = _build_indicator_input(
            symbol="AAPL",
            bars_5m=__import__("pandas").DataFrame(),
            base_dir=DEFAULT_BASE_DIR,
            latest_price=999999.0,
            now=datetime.now(UTC),
        )
        row = _compute_row("AAPL", frame, datetime.now(UTC))
        self.assertEqual(row["source_type"], "KIS_CURRENT_PRICE_APPENDED")
        self.assertEqual(int(bool(row["data_fresh"])), 1)
        self.assertIn("freshness_age_sec", row)

    def test_raw_intraday_history_is_used_when_daily_source_is_missing(self) -> None:
        import pandas as pd
        from app.task_089_market_data_signal_refresh import _build_canonical_runtime_rows, _init_tables

        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db_path = root / "trading.db"
            raw_dir = root / "intraday"
            raw_dir.mkdir()
            timestamps = pd.date_range("2026-05-01T13:30:00Z", periods=80, freq="15min")
            pd.DataFrame(
                {
                    "timestamp": timestamps.astype(str),
                    "open": range(80, 160),
                    "high": range(81, 161),
                    "low": range(79, 159),
                    "close": range(80, 160),
                    "volume": [1000] * 80,
                }
            ).to_csv(raw_dir / "AFRM.csv", index=False)
            _init_tables(str(db_path))
            with patch("app.task_089_market_data_signal_refresh.RAW_INTRADAY_ROOT", raw_dir):
                rows, _, _ = _build_canonical_runtime_rows(
                    symbols=["AFRM"],
                    base_dir=root / "missing_daily",
                    db_path=str(db_path),
                    now=datetime.fromisoformat("2026-06-02T12:00:00+00:00"),
                )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["symbol"], "AFRM")
        self.assertEqual(rows[0]["source_type"], "RAW_INTRADAY_HISTORY")
        self.assertNotEqual(rows[0]["reason"], "MISSING_SOURCE")

    def test_kis_rate_limit_error_is_retried(self) -> None:
        from app.task_089_market_data_signal_refresh import _get_current_price_with_retry

        class FakeKis:
            def __init__(self) -> None:
                self.calls = 0
                self.exchange_code = "NASD"

            def get_current_price(self, symbol: str) -> float:
                self.calls += 1
                if self.calls == 1:
                    raise RuntimeError("KIS HTTP 500: EGW00201: 초당 거래건수를 초과하였습니다.")
                return 123.45

        fake = FakeKis()
        with patch("app.task_089_market_data_signal_refresh.time.sleep") as sleep:
            price = _get_current_price_with_retry(fake, "AMD", max_attempts=2, base_sleep_sec=0.01)
        self.assertEqual(price, 123.45)
        self.assertEqual(fake.calls, 2)
        sleep.assert_called_once()

    def test_kis_empty_quote_tries_symbol_exchange_hint(self) -> None:
        from app.task_089_market_data_signal_refresh import _get_current_price_with_retry

        class FakeKis:
            def __init__(self) -> None:
                self.exchange_code = "NASD"
                self.exchanges: list[str] = []

            def get_current_price(self, symbol: str) -> float:
                self.exchanges.append(self.exchange_code)
                if self.exchange_code != "NYSE":
                    raise RuntimeError(f"Could not parse current price for {symbol}: empty output")
                return 222.22

        fake = FakeKis()
        price = _get_current_price_with_retry(fake, "CRM", max_attempts=1, base_sleep_sec=0.0)
        self.assertEqual(price, 222.22)
        self.assertEqual(fake.exchange_code, "NASD")
        self.assertIn("NYSE", fake.exchanges)

    def test_kis_init_failure_writes_diagnostic_report(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            db_path = root / "trading.db"
            json_out = root / "task_089.json"
            md_out = root / "task_089.md"
            missing_env_file = root / "missing.env"

            env = dict(os.environ)
            env["PYTHONPATH"] = str(SRC)
            env["KIS_ENVIRONMENT"] = "paper"
            env.pop("KIS_APP_KEY", None)
            env.pop("KIS_APP_SECRET", None)
            env.pop("KIS_ACCOUNT_NUMBER", None)
            env.pop("KIS_PRODUCT_CODE", None)

            cmd = [
                sys.executable,
                "-m",
                "app.task_089_market_data_signal_refresh",
                "--db-path",
                str(db_path),
                "--env-file",
                str(missing_env_file),
                "--json-out",
                str(json_out),
                "--md-out",
                str(md_out),
                "--symbols",
                "ZZZZ",
                "--base-dir",
                str(root / "empty_daily"),
            ]
            proc = subprocess.run(cmd, check=False, capture_output=True, text=True, env=env)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertTrue(json_out.exists())
            self.assertTrue(md_out.exists())

            payload = json.loads(json_out.read_text(encoding="utf-8"))
            warnings = payload.get("warnings", [])
            self.assertTrue(any(str(w).startswith("KIS_CLIENT_INIT_FAILED:") for w in warnings))
            self.assertEqual(int(payload.get("evaluated_count", -1)), 1)
            self.assertEqual(int(payload.get("enter_candidates", -1)), 0)
            self.assertEqual(payload["top_candidates"][0]["symbol"], "ZZZZ")
            self.assertEqual(payload["top_candidates"][0]["source_type"], "MISSING_SOURCE")


if __name__ == "__main__":
    unittest.main()
