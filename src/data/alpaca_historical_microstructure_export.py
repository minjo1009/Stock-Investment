from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import pandas as pd

from src.data.env_loader import load_repo_env


DEFAULT_OUT_DIR = Path("data/raw/alpaca_historical_microstructure")
DEFAULT_FEED = "sip"
DEFAULT_LIMIT = 10_000


@dataclass(frozen=True)
class HistoricalMicrostructureExportResult:
    quote_audit: pd.DataFrame
    trade_audit: pd.DataFrame


class AlpacaHistoricalMicrostructureProvider:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        secret_key: str | None = None,
        feed: str = DEFAULT_FEED,
        page_limit: int = DEFAULT_LIMIT,
    ) -> None:
        load_repo_env()
        self.api_key = api_key or os.environ.get("APCA_API_KEY_ID") or os.environ.get("ALPACA_API_KEY")
        self.secret_key = secret_key or os.environ.get("APCA_API_SECRET_KEY") or os.environ.get("ALPACA_SECRET_KEY")
        self.feed = feed
        self.page_limit = int(page_limit)

    def fetch_quotes(self, symbol: str, *, start: str, end: str) -> pd.DataFrame:
        payload_rows = self._paged_request(
            endpoint="https://data.alpaca.markets/v2/stocks/quotes",
            symbol=symbol,
            start=start,
            end=end,
        )
        return normalize_quote_rows(symbol, payload_rows)

    def fetch_trades(self, symbol: str, *, start: str, end: str) -> pd.DataFrame:
        payload_rows = self._paged_request(
            endpoint="https://data.alpaca.markets/v2/stocks/trades",
            symbol=symbol,
            start=start,
            end=end,
        )
        return normalize_trade_rows(symbol, payload_rows)

    def _paged_request(self, *, endpoint: str, symbol: str, start: str, end: str) -> list[dict[str, Any]]:
        if not self.api_key or not self.secret_key:
            raise RuntimeError("Alpaca credentials are missing. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY.")
        rows: list[dict[str, Any]] = []
        page_token: str | None = None
        upper = symbol.upper()
        while True:
            params = {
                "symbols": upper,
                "start": start,
                "end": end,
                "limit": str(self.page_limit),
                "feed": self.feed,
            }
            if page_token:
                params["page_token"] = page_token
            request = Request(
                f"{endpoint}?{urlencode(params)}",
                headers={
                    "APCA-API-KEY-ID": self.api_key or "",
                    "APCA-API-SECRET-KEY": self.secret_key or "",
                    "Accept": "application/json",
                },
            )
            with urlopen(request, timeout=60) as response:  # noqa: S310
                payload = json.loads(response.read().decode("utf-8"))
            key = "quotes" if endpoint.endswith("quotes") else "trades"
            rows.extend(payload.get(key, {}).get(upper, []))
            page_token = payload.get("next_page_token")
            if not page_token:
                break
        return rows


def normalize_quote_rows(symbol: str, rows: Iterable[dict[str, Any]]) -> pd.DataFrame:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        ts = pd.to_datetime(row.get("t"), utc=True, errors="coerce")
        if pd.isna(ts):
            continue
        bid = _num(row.get("bp"))
        ask = _num(row.get("ap"))
        bid_size = _num(row.get("bs"))
        ask_size = _num(row.get("as"))
        mid = (bid + ask) / 2 if bid > 0 and ask > 0 else pd.NA
        spread_bps = ((ask - bid) / mid * 10_000) if mid and mid > 0 else pd.NA
        normalized.append(
            {
                "symbol": symbol.upper(),
                "quote_ts": ts.isoformat().replace("+00:00", "Z"),
                "bid": bid,
                "ask": ask,
                "bid_size": bid_size,
                "ask_size": ask_size,
                "exchange_bid": row.get("bx"),
                "exchange_ask": row.get("ax"),
                "quote_conditions": "|".join(row.get("c", []) or []),
                "tape": row.get("z", ""),
                "mid": mid,
                "spread_bps": spread_bps,
                "nbbo_size_dollar": (bid_size + ask_size) * 100 * mid if mid and mid > 0 else pd.NA,
                "nbbo_imbalance": (bid_size - ask_size) / (bid_size + ask_size) if (bid_size + ask_size) > 0 else pd.NA,
                "source": "ALPACA_HISTORICAL_QUOTES",
                "recv_ts_utc": "",
                "receive_ts_available_flag": 0,
            }
        )
    frame = pd.DataFrame(normalized)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "symbol",
                "quote_ts",
                "bid",
                "ask",
                "bid_size",
                "ask_size",
                "exchange_bid",
                "exchange_ask",
                "quote_conditions",
                "tape",
                "mid",
                "spread_bps",
                "nbbo_size_dollar",
                "nbbo_imbalance",
                "source",
                "recv_ts_utc",
                "receive_ts_available_flag",
            ]
        )
    return frame.sort_values(["symbol", "quote_ts"]).drop_duplicates(["symbol", "quote_ts"], keep="last").reset_index(drop=True)


def normalize_trade_rows(symbol: str, rows: Iterable[dict[str, Any]]) -> pd.DataFrame:
    normalized: list[dict[str, Any]] = []
    for row in rows:
        ts = pd.to_datetime(row.get("t"), utc=True, errors="coerce")
        if pd.isna(ts):
            continue
        normalized.append(
            {
                "symbol": symbol.upper(),
                "trade_ts": ts.isoformat().replace("+00:00", "Z"),
                "price": _num(row.get("p")),
                "size": _num(row.get("s")),
                "exchange": row.get("x", ""),
                "trade_id": row.get("i", ""),
                "trade_conditions": "|".join(row.get("c", []) or []),
                "tape": row.get("z", ""),
                "source": "ALPACA_HISTORICAL_TRADES",
                "recv_ts_utc": "",
                "receive_ts_available_flag": 0,
            }
        )
    frame = pd.DataFrame(normalized)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "symbol",
                "trade_ts",
                "price",
                "size",
                "exchange",
                "trade_id",
                "trade_conditions",
                "tape",
                "source",
                "recv_ts_utc",
                "receive_ts_available_flag",
            ]
        )
    return frame.sort_values(["symbol", "trade_ts"]).drop_duplicates(["symbol", "trade_ts", "trade_id"], keep="last").reset_index(drop=True)


def export_historical_microstructure(
    *,
    symbols: list[str],
    start: str,
    end: str,
    feed: str = DEFAULT_FEED,
    out_dir: Path = DEFAULT_OUT_DIR,
    include_trades: bool = True,
    include_quotes: bool = True,
) -> HistoricalMicrostructureExportResult:
    provider = AlpacaHistoricalMicrostructureProvider(feed=feed)
    quote_rows: list[dict[str, object]] = []
    trade_rows: list[dict[str, object]] = []
    for symbol in sorted({s.strip().upper() for s in symbols if s.strip()}):
        if include_quotes:
            quote_rows.append(_export_one(provider.fetch_quotes, symbol, start, end, feed, out_dir, "quotes", "quote_ts"))
        if include_trades:
            trade_rows.append(_export_one(provider.fetch_trades, symbol, start, end, feed, out_dir, "trades", "trade_ts"))
    return HistoricalMicrostructureExportResult(quote_audit=pd.DataFrame(quote_rows), trade_audit=pd.DataFrame(trade_rows))


def export_entry_window_microstructure(
    *,
    entry_panel: Path,
    feed: str = DEFAULT_FEED,
    out_dir: Path = DEFAULT_OUT_DIR,
    symbols: list[str] | None = None,
    symbol_column: str = "symbol",
    entry_ts_column: str = "entry_ts",
    window_before_minutes: int = 10,
    window_after_minutes: int = 1,
    max_windows: int | None = None,
    include_trades: bool = True,
    include_quotes: bool = True,
) -> HistoricalMicrostructureExportResult:
    panel = pd.read_csv(entry_panel, usecols=lambda col: col in {symbol_column, entry_ts_column})
    if panel.empty:
        return HistoricalMicrostructureExportResult(quote_audit=pd.DataFrame(), trade_audit=pd.DataFrame())
    panel[symbol_column] = panel[symbol_column].astype(str).str.upper()
    panel[entry_ts_column] = pd.to_datetime(panel[entry_ts_column], utc=True, errors="coerce")
    panel = panel.dropna(subset=[symbol_column, entry_ts_column]).copy()
    if symbols:
        allowed = {s.strip().upper() for s in symbols if s.strip()}
        panel = panel[panel[symbol_column].isin(allowed)].copy()
    windows = _entry_windows(
        panel,
        symbol_column=symbol_column,
        entry_ts_column=entry_ts_column,
        before_minutes=window_before_minutes,
        after_minutes=window_after_minutes,
    )
    if max_windows is not None:
        windows = windows[: max(int(max_windows), 0)]
    provider = AlpacaHistoricalMicrostructureProvider(feed=feed)
    quote_audit = _export_windows(provider.fetch_quotes, windows, feed, out_dir, "quotes", "quote_ts") if include_quotes else pd.DataFrame()
    trade_audit = _export_windows(provider.fetch_trades, windows, feed, out_dir, "trades", "trade_ts") if include_trades else pd.DataFrame()
    return HistoricalMicrostructureExportResult(quote_audit=quote_audit, trade_audit=trade_audit)


def _entry_windows(
    panel: pd.DataFrame,
    *,
    symbol_column: str,
    entry_ts_column: str,
    before_minutes: int,
    after_minutes: int,
) -> list[dict[str, str]]:
    panel = panel.copy()
    panel["window_start"] = panel[entry_ts_column] - pd.Timedelta(minutes=int(before_minutes))
    panel["window_end"] = panel[entry_ts_column] + pd.Timedelta(minutes=int(after_minutes))
    rows: list[dict[str, str]] = []
    for symbol, group in panel.groupby(symbol_column, sort=True):
        ordered = group.sort_values("window_start")
        current_start = None
        current_end = None
        entry_count = 0
        for row in ordered.itertuples(index=False):
            start = getattr(row, "window_start")
            end = getattr(row, "window_end")
            if current_start is None:
                current_start = start
                current_end = end
                entry_count = 1
                continue
            if start <= current_end:
                current_end = max(current_end, end)
                entry_count += 1
                continue
            rows.append(_window_record(str(symbol), current_start, current_end, entry_count))
            current_start = start
            current_end = end
            entry_count = 1
        if current_start is not None and current_end is not None:
            rows.append(_window_record(str(symbol), current_start, current_end, entry_count))
    return rows


def _window_record(symbol: str, start: pd.Timestamp, end: pd.Timestamp, entry_count: int) -> dict[str, str]:
    return {
        "symbol": symbol.upper(),
        "window_date": str(start.date()),
        "start": start.isoformat().replace("+00:00", "Z"),
        "end": end.isoformat().replace("+00:00", "Z"),
        "entry_count": str(entry_count),
    }


def _export_windows(fetcher, windows: list[dict[str, str]], feed: str, out_dir: Path, kind: str, ts_col: str) -> pd.DataFrame:
    audits: list[dict[str, object]] = []
    for symbol in sorted({window["symbol"] for window in windows}):
        frames: list[pd.DataFrame] = []
        for idx, window in [(idx, w) for idx, w in enumerate(windows, start=1) if w["symbol"] == symbol]:
            try:
                frame = fetcher(symbol, start=window["start"], end=window["end"])
                frame["window_id"] = idx
                frame["window_start"] = window["start"]
                frame["window_end"] = window["end"]
                frame["window_entry_count"] = int(window["entry_count"])
                frames.append(frame)
                audits.append(
                    {
                        "symbol": symbol,
                        "source_kind": kind,
                        "feed": feed,
                        "window_id": idx,
                        "window_start": window["start"],
                        "window_end": window["end"],
                        "entry_count": int(window["entry_count"]),
                        "export_status": "EXPORTED",
                        "row_count": int(len(frame)),
                        "error": "",
                        "secret_value_logged_flag": 0,
                    }
                )
            except Exception as exc:  # noqa: BLE001
                audits.append(
                    {
                        "symbol": symbol,
                        "source_kind": kind,
                        "feed": feed,
                        "window_id": idx,
                        "window_start": window["start"],
                        "window_end": window["end"],
                        "entry_count": int(window["entry_count"]),
                        "export_status": "FAILED",
                        "row_count": 0,
                        "error": str(exc),
                        "secret_value_logged_flag": 0,
                    }
                )
        output = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
        if not output.empty:
            output = output.drop_duplicates([col for col in [ts_col, "symbol"] if col in output.columns], keep="last").sort_values(ts_col)
        path = out_dir / f"feed={feed}" / kind / f"{symbol}.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        output.to_csv(path, index=False, encoding="utf-8-sig")
    return pd.DataFrame(audits)


def _export_one(fetcher, symbol: str, start: str, end: str, feed: str, out_dir: Path, kind: str, ts_col: str) -> dict[str, object]:
    try:
        frame = fetcher(symbol, start=start, end=end)
        path = out_dir / f"feed={feed}" / kind / f"{symbol}.csv"
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False, encoding="utf-8-sig")
        return {
            "symbol": symbol,
            "source_kind": kind,
            "feed": feed,
            "export_status": "EXPORTED",
            "row_count": int(len(frame)),
            "first_timestamp": "" if frame.empty else str(frame[ts_col].iloc[0]),
            "last_timestamp": "" if frame.empty else str(frame[ts_col].iloc[-1]),
            "path": str(path),
            "error": "",
            "secret_value_logged_flag": 0,
        }
    except Exception as exc:  # noqa: BLE001
        return {
            "symbol": symbol,
            "source_kind": kind,
            "feed": feed,
            "export_status": "FAILED",
            "row_count": 0,
            "first_timestamp": "",
            "last_timestamp": "",
            "path": "",
            "error": str(exc),
            "secret_value_logged_flag": 0,
        }


def _num(value: object) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def default_window(days: int = 5) -> tuple[str, str]:
    end_dt = datetime.now(UTC) - timedelta(minutes=20)
    start_dt = end_dt - timedelta(days=max(int(days), 1))
    return start_dt.isoformat().replace("+00:00", "Z"), end_dt.isoformat().replace("+00:00", "Z")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Alpaca historical quotes/trades for microstructure diagnostics.")
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--lookback-days", type=int, default=5)
    parser.add_argument("--feed", default=DEFAULT_FEED, choices=["sip", "iex"])
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--entry-panel", type=Path)
    parser.add_argument("--entry-ts-column", default="entry_ts")
    parser.add_argument("--symbol-column", default="symbol")
    parser.add_argument("--window-before-minutes", type=int, default=10)
    parser.add_argument("--window-after-minutes", type=int, default=1)
    parser.add_argument("--max-windows", type=int)
    parser.add_argument("--no-quotes", action="store_true")
    parser.add_argument("--no-trades", action="store_true")
    args = parser.parse_args()
    if args.entry_panel:
        result = export_entry_window_microstructure(
            entry_panel=args.entry_panel,
            symbols=args.symbols,
            feed=args.feed,
            out_dir=args.out_dir,
            symbol_column=args.symbol_column,
            entry_ts_column=args.entry_ts_column,
            window_before_minutes=args.window_before_minutes,
            window_after_minutes=args.window_after_minutes,
            max_windows=args.max_windows,
            include_quotes=not args.no_quotes,
            include_trades=not args.no_trades,
        )
    else:
        start, end = (args.start, args.end) if args.start and args.end else default_window(args.lookback_days)
        result = export_historical_microstructure(
            symbols=args.symbols,
            start=start,
            end=end,
            feed=args.feed,
            out_dir=args.out_dir,
            include_quotes=not args.no_quotes,
            include_trades=not args.no_trades,
        )
    quote_exported = int(result.quote_audit.get("export_status", pd.Series(dtype=str)).eq("EXPORTED").sum()) if not result.quote_audit.empty else 0
    trade_exported = int(result.trade_audit.get("export_status", pd.Series(dtype=str)).eq("EXPORTED").sum()) if not result.trade_audit.empty else 0
    print(f"[HISTORICAL_MICROSTRUCTURE_EXPORT] quotes={quote_exported} trades={trade_exported} feed={args.feed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
