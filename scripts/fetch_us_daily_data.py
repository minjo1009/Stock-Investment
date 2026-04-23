from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from backtest.data_loader import DEFAULT_US_UNIVERSE


def _fetch_one_symbol(symbol: str, *, period: str) -> pd.DataFrame:
    try:
        import yfinance as yf
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "yfinance is required. Install with: pip install yfinance"
        ) from exc

    ticker = yf.Ticker(symbol)
    history = ticker.history(period=period, interval="1d", auto_adjust=False)
    if history.empty:
        return pd.DataFrame()

    history = history.reset_index()
    history.columns = [str(col).strip().lower().replace(" ", "_") for col in history.columns]

    # Typical columns from yfinance: date, open, high, low, close, volume, dividends, stock_splits
    rename_map = {"date": "timestamp"}
    if "adj_close" not in history.columns and "adj_close" not in rename_map and "adjclose" in history.columns:
        rename_map["adjclose"] = "adj_close"
    history = history.rename(columns=rename_map)

    expected = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [col for col in expected if col not in history.columns]
    if missing:
        raise ValueError(f"{symbol}: missing columns from source: {', '.join(missing)}")

    out_cols = ["timestamp", "open", "high", "low", "close", "volume"]
    if "adj_close" in history.columns:
        out_cols.append("adj_close")

    out = history[out_cols].copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="coerce").dt.strftime("%Y-%m-%d")
    out = out.dropna(subset=["timestamp"])
    out["symbol"] = symbol

    out = out.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")
    out = out.reset_index(drop=True)
    return out


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch US daily OHLCV data into local CSV files.")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE), help="Ticker symbols")
    parser.add_argument("--period", default="5y", help="Yahoo period (default: 5y)")
    parser.add_argument("--out-dir", default="data/raw/us_daily", help="Output directory")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    symbols = [str(sym).strip().upper() for sym in args.symbols if str(sym).strip()]
    if not symbols:
        raise ValueError("at least one symbol is required")

    print(f"[FETCH START] symbols={len(symbols)} period={args.period} out_dir={out_dir}")
    success = 0
    failed = 0

    for symbol in symbols:
        try:
            df = _fetch_one_symbol(symbol, period=args.period)
            if df.empty:
                print(f"[SKIP] {symbol}: no data")
                failed += 1
                continue

            csv_path = out_dir / f"{symbol}.csv"
            df.to_csv(csv_path, index=False)
            print(f"[OK] {symbol}: rows={len(df)} -> {csv_path}")
            success += 1
        except Exception as exc:  # noqa: BLE001
            print(f"[ERROR] {symbol}: {exc}")
            failed += 1

    print(f"[FETCH DONE] success={success} failed={failed}")
    return 0 if success > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
