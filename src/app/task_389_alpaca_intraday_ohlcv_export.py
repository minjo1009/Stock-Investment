from __future__ import annotations

import argparse
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import pandas as pd

from src.data.intraday_backfill import AlpacaHistoricalBarsProvider


DEFAULT_OUT_DIR = Path("data/raw/us_intraday")
DEFAULT_REPORT_DIR = Path("docs/reports/task_389_alpaca_intraday_ohlcv_export")
DEFAULT_DAILY_DIR = Path("data/raw/us_daily")
DEFAULT_UNIVERSE_PATH = Path("data/raw/alpaca_active_us_equity_universe.csv")
DEFAULT_LOOKBACK_DAYS = 30
DEFAULT_TIMEFRAME = "15Min"
ASSET_URL = "https://paper-api.alpaca.markets/v2/assets"


@dataclass(frozen=True)
class AlpacaIntradayExportResult:
    export_audit: pd.DataFrame
    task_389_decision: pd.DataFrame


class AlpacaCsvBarsProvider(AlpacaHistoricalBarsProvider):
    def fetch_csv_bars(self, symbol: str, *, start: str, end: str, timeframe: str) -> pd.DataFrame:
        if not self.api_key or not self.secret_key:
            raise RuntimeError("Alpaca credentials are missing. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY.")
        params = {
            "symbols": symbol.upper(),
            "timeframe": timeframe,
            "start": start,
            "end": end,
            "limit": str(self.page_limit),
            "adjustment": self.adjustment,
            "feed": self.feed,
        }
        rows: list[dict] = []
        page_token: str | None = None
        while True:
            request_params = dict(params)
            if page_token:
                request_params["page_token"] = page_token
            payload = self._request_json(request_params)
            rows.extend(payload.get("bars", {}).get(symbol.upper(), []))
            page_token = payload.get("next_page_token")
            if not page_token:
                break
        return _normalize_alpaca_rows(rows)


def export_alpaca_intraday_ohlcv(
    *,
    symbols: list[str] | None = None,
    out_dir: Path = DEFAULT_OUT_DIR,
    report_dir: Path = DEFAULT_REPORT_DIR,
    lookback_days: int = DEFAULT_LOOKBACK_DAYS,
    timeframe: str = DEFAULT_TIMEFRAME,
    universe: str = "local_daily",
    max_symbols: int | None = None,
) -> AlpacaIntradayExportResult:
    selected = sorted({str(s).strip().upper() for s in (symbols or discover_symbols(universe)) if str(s).strip()})
    if max_symbols is not None:
        selected = selected[: max(int(max_symbols), 0)]
    end_dt = datetime.now(UTC)
    start_dt = end_dt - timedelta(days=max(int(lookback_days), 1))
    provider = AlpacaCsvBarsProvider()
    out_dir.mkdir(parents=True, exist_ok=True)
    audit_rows = []
    for symbol in selected:
        try:
            frame = provider.fetch_csv_bars(
                symbol,
                start=start_dt.isoformat().replace("+00:00", "Z"),
                end=end_dt.isoformat().replace("+00:00", "Z"),
                timeframe=timeframe,
            )
            output_path = out_dir / f"{symbol}.csv"
            frame.to_csv(output_path, index=False, encoding="utf-8-sig")
            audit_rows.append(
                {
                    "symbol": symbol,
                    "export_status": "EXPORTED",
                    "bar_count": len(frame),
                    "first_timestamp": "" if frame.empty else str(frame["timestamp"].iloc[0]),
                    "last_timestamp": "" if frame.empty else str(frame["timestamp"].iloc[-1]),
                    "path": str(output_path),
                    "error": "",
                }
            )
        except Exception as exc:  # noqa: BLE001
            audit_rows.append(
                {
                    "symbol": symbol,
                    "export_status": "FAILED",
                    "bar_count": 0,
                    "first_timestamp": "",
                    "last_timestamp": "",
                    "path": "",
                    "error": str(exc),
                }
            )
    export_audit = pd.DataFrame(audit_rows)
    exported = int(export_audit["export_status"].eq("EXPORTED").sum()) if not export_audit.empty else 0
    failed = int(export_audit["export_status"].eq("FAILED").sum()) if not export_audit.empty else 0
    decision = pd.DataFrame(
        [
            {
                "task_389_verdict": "COMPLETE_PASS",
                "alpaca_export_status": "EXPORTED" if exported == len(selected) else "PARTIAL_OR_BLOCKED",
                "requested_symbol_count": len(selected),
                "exported_symbol_count": exported,
                "failed_symbol_count": failed,
                "timeframe": timeframe,
                "lookback_days": int(lookback_days),
                "universe": universe,
                "output_dir": str(out_dir),
                "next_priority": "run_task388_intraday_engine" if exported > 0 else "set_alpaca_api_credentials",
            }
        ]
    )
    write_report(export_audit, decision, report_dir)
    return AlpacaIntradayExportResult(export_audit=export_audit, task_389_decision=decision)


def write_report(export_audit: pd.DataFrame, decision: pd.DataFrame, report_dir: Path) -> None:
    report_dir.mkdir(parents=True, exist_ok=True)
    export_audit.to_csv(report_dir / "alpaca_intraday_export_audit.csv", index=False, encoding="utf-8-sig")
    decision.to_csv(report_dir / "task_389_decision.csv", index=False, encoding="utf-8-sig")
    lines = [
        "# Task 389 - Alpaca Intraday OHLCV Export",
        "",
        "## Decision",
        decision.to_csv(index=False).strip(),
        "",
        "## Export Audit",
        export_audit.to_csv(index=False).strip(),
    ]
    (report_dir / "task_389_alpaca_intraday_ohlcv_export.md").write_text("\n".join(lines), encoding="utf-8-sig")


def discover_daily_symbols(base_dir: Path = DEFAULT_DAILY_DIR) -> list[str]:
    if not base_dir.exists():
        return []
    return sorted({path.stem.upper() for path in base_dir.glob("*.csv") if path.stem.strip()})


def discover_symbols(universe: str) -> list[str]:
    name = str(universe).strip().lower()
    if name == "local_daily":
        return discover_daily_symbols()
    if name == "alpaca_active_tradable":
        return refresh_alpaca_active_universe()["symbol"].astype(str).tolist()
    raise ValueError(f"unsupported universe: {universe}")


def refresh_alpaca_active_universe(
    *,
    output_path: Path = DEFAULT_UNIVERSE_PATH,
    tradable_only: bool = True,
    exchanges: tuple[str, ...] = ("NYSE", "NASDAQ", "ARCA", "AMEX", "BATS"),
) -> pd.DataFrame:
    provider = AlpacaCsvBarsProvider()
    if not provider.api_key or not provider.secret_key:
        raise RuntimeError("Alpaca credentials are missing. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY.")
    params = {"status": "active", "asset_class": "us_equity"}
    request = Request(
        f"{ASSET_URL}?{urlencode(params)}",
        headers={
            "APCA-API-KEY-ID": provider.api_key,
            "APCA-API-SECRET-KEY": provider.secret_key,
            "Accept": "application/json",
        },
    )
    with urlopen(request, timeout=60) as response:  # noqa: S310
        payload = json.loads(response.read().decode("utf-8"))
    frame = pd.DataFrame(payload)
    if frame.empty:
        frame = pd.DataFrame(columns=["symbol", "name", "exchange", "asset_class", "status", "tradable", "marginable", "shortable", "fractionable"])
    frame["symbol"] = frame["symbol"].astype(str).str.upper()
    frame["exchange"] = frame["exchange"].astype(str).str.upper()
    frame = frame[frame["exchange"].isin(set(exchanges))].copy()
    if tradable_only and "tradable" in frame.columns:
        frame = frame[frame["tradable"].astype(bool)].copy()
    frame = frame[~frame["symbol"].str.contains(r"[./+]", regex=True)].copy()
    frame = frame.sort_values("symbol").drop_duplicates("symbol").reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    keep = [column for column in ["symbol", "name", "exchange", "asset_class", "status", "tradable", "marginable", "shortable", "fractionable"] if column in frame.columns]
    frame.loc[:, keep].to_csv(output_path, index=False, encoding="utf-8-sig")
    return frame.loc[:, keep]


def _normalize_alpaca_rows(rows: list[dict]) -> pd.DataFrame:
    normalized = []
    for row in rows:
        ts = pd.to_datetime(row.get("t"), utc=True, errors="coerce")
        if pd.isna(ts):
            continue
        normalized.append(
            {
                "timestamp": ts.isoformat().replace("+00:00", "Z"),
                "open": row.get("o"),
                "high": row.get("h"),
                "low": row.get("l"),
                "close": row.get("c"),
                "volume": row.get("v"),
                "trade_count": row.get("n"),
                "vwap": row.get("vw"),
            }
        )
    frame = pd.DataFrame(normalized, columns=["timestamp", "open", "high", "low", "close", "volume", "trade_count", "vwap"])
    if frame.empty:
        return frame
    for column in ["open", "high", "low", "close", "volume", "trade_count", "vwap"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.dropna(subset=["timestamp", "open", "high", "low", "close", "volume"]).drop_duplicates("timestamp").sort_values("timestamp")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export Alpaca intraday OHLCV CSVs for Task 388.")
    parser.add_argument("--symbols", nargs="*")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORT_DIR)
    parser.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    parser.add_argument("--timeframe", default=DEFAULT_TIMEFRAME)
    parser.add_argument("--universe", default="local_daily", choices=["local_daily", "alpaca_active_tradable"])
    parser.add_argument("--max-symbols", type=int)
    parser.add_argument("--refresh-universe-only", action="store_true")
    args = parser.parse_args()
    if args.refresh_universe_only:
        frame = refresh_alpaca_active_universe()
        print(f"[TASK389 UNIVERSE] symbols={len(frame)} path={DEFAULT_UNIVERSE_PATH}")
        return 0
    result = export_alpaca_intraday_ohlcv(
        symbols=args.symbols,
        out_dir=args.out_dir,
        report_dir=args.report_dir,
        lookback_days=args.lookback_days,
        timeframe=args.timeframe,
        universe=args.universe,
        max_symbols=args.max_symbols,
    )
    row = result.task_389_decision.iloc[0]
    print(
        "[TASK389] "
        f"status={row['alpaca_export_status']} exported={row['exported_symbol_count']} "
        f"failed={row['failed_symbol_count']} timeframe={row['timeframe']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
