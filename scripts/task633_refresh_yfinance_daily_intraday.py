from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.backtest.build_task503_multiday_entry_population_rebuild import (
    DEFAULT_DAILY_DIR,
    DEFAULT_INTRADAY_DIR,
    DEFAULT_THEME_MAP,
)


def normalize_download(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    out = frame.copy()
    if isinstance(out.columns, pd.MultiIndex):
        out.columns = [str(col[0]).strip().lower().replace(" ", "_") for col in out.columns]
    else:
        out.columns = [str(col).strip().lower().replace(" ", "_") for col in out.columns]
    out = out.reset_index()
    out.columns = [str(col).strip().lower().replace(" ", "_") for col in out.columns]
    if "date" in out.columns:
        out = out.rename(columns={"date": "timestamp"})
    if "datetime" in out.columns:
        out = out.rename(columns={"datetime": "timestamp"})
    if "adj_close" not in out.columns and "adj close" in out.columns:
        out = out.rename(columns={"adj close": "adj_close"})
    return out


def format_timestamp(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, utc=True, errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch_daily(symbol: str, out_dir: Path, period: str) -> dict[str, object]:
    import yfinance as yf

    raw = yf.download(symbol, period=period, interval="1d", auto_adjust=False, progress=False, threads=False)
    frame = normalize_download(raw)
    if frame.empty or "timestamp" not in frame.columns:
        return {"symbol": symbol, "daily_status": "empty", "daily_rows": 0, "daily_max": ""}
    columns = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [col for col in columns if col not in frame.columns]
    if missing:
        return {"symbol": symbol, "daily_status": f"missing:{'|'.join(missing)}", "daily_rows": 0, "daily_max": ""}
    out = frame[columns].copy()
    out["timestamp"] = format_timestamp(out["timestamp"])
    out = out.dropna(subset=["timestamp"]).copy()
    out["trade_count"] = 0
    out["vwap"] = (pd.to_numeric(out["high"], errors="coerce") + pd.to_numeric(out["low"], errors="coerce") + pd.to_numeric(out["close"], errors="coerce")) / 3.0
    out = out.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")
    out_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_dir / f"{symbol}.csv", index=False)
    return {
        "symbol": symbol,
        "daily_status": "ok",
        "daily_rows": int(len(out)),
        "daily_max": str(pd.to_datetime(out["timestamp"], utc=True).max().date()) if not out.empty else "",
    }


def fetch_intraday(symbol: str, out_dir: Path, period: str) -> dict[str, object]:
    import yfinance as yf

    raw = yf.download(symbol, period=period, interval="15m", auto_adjust=False, prepost=True, progress=False, threads=False)
    frame = normalize_download(raw)
    if frame.empty or "timestamp" not in frame.columns:
        return {"symbol": symbol, "intraday_status": "empty", "intraday_rows": 0, "intraday_max": ""}
    columns = ["timestamp", "open", "high", "low", "close", "volume"]
    missing = [col for col in columns if col not in frame.columns]
    if missing:
        return {"symbol": symbol, "intraday_status": f"missing:{'|'.join(missing)}", "intraday_rows": 0, "intraday_max": ""}
    out = frame[columns].copy()
    out["timestamp"] = format_timestamp(out["timestamp"])
    out = out.dropna(subset=["timestamp"]).copy()
    old_path = out_dir / f"{symbol}.csv"
    if old_path.exists():
        old = pd.read_csv(old_path)
        old.columns = [str(col).strip().lower() for col in old.columns]
        old = old[[col for col in columns if col in old.columns]].copy()
        out = pd.concat([old, out], ignore_index=True)
    out = out.sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")
    out_dir.mkdir(parents=True, exist_ok=True)
    out.to_csv(old_path, index=False)
    return {
        "symbol": symbol,
        "intraday_status": "ok",
        "intraday_rows": int(len(out)),
        "intraday_max": str(pd.to_datetime(out["timestamp"], utc=True).max().date()) if not out.empty else "",
    }


def load_symbols(theme_map_path: Path, extra_symbols: list[str]) -> list[str]:
    theme = pd.read_csv(theme_map_path)
    symbols = theme["symbol"].astype(str).str.upper().tolist()
    symbols.extend(str(symbol).upper() for symbol in extra_symbols)
    return sorted(set(symbols))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--theme-map", type=Path, default=DEFAULT_THEME_MAP)
    parser.add_argument("--daily-dir", type=Path, default=DEFAULT_DAILY_DIR)
    parser.add_argument("--intraday-dir", type=Path, default=DEFAULT_INTRADAY_DIR)
    parser.add_argument("--daily-period", default="5y")
    parser.add_argument("--intraday-period", default="60d")
    parser.add_argument("--extra-symbol", action="append", default=["QQQ"])
    parser.add_argument("--audit-path", type=Path, default=Path("docs/reports/task_633_market_data_refresh/task_633_yfinance_refresh_audit.csv"))
    args = parser.parse_args()

    rows: list[dict[str, object]] = []
    for symbol in load_symbols(args.theme_map, args.extra_symbol):
        row: dict[str, object] = {"symbol": symbol}
        row.update(fetch_daily(symbol, args.daily_dir, args.daily_period))
        row.update(fetch_intraday(symbol, args.intraday_dir, args.intraday_period))
        rows.append(row)
        print(
            f"[{symbol}] daily={row.get('daily_status')} {row.get('daily_max')} "
            f"intraday={row.get('intraday_status')} {row.get('intraday_max')}"
        )
    audit = pd.DataFrame(rows)
    args.audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit.to_csv(args.audit_path, index=False)
    print(f"[AUDIT] {args.audit_path}")


if __name__ == "__main__":
    main()
