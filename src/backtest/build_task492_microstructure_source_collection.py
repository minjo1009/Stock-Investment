from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

from src.backtest.build_task489_broad_regime_cell_portfolio import (
    DEFAULT_BROAD_DAILY_DIR,
    DEFAULT_BROAD_MARKET_CACHE,
    DEFAULT_TASK487_PANEL,
    load_or_build_broad_market_state,
    load_panel_with_broad_market,
)
from src.backtest.build_task490r_firm_grade_intraday_continuation_validation import (
    DEFAULT_TASK489_SELECTED_CELLS,
    build_task489_selected_panel,
)


DEFAULT_OUT_DIR = Path("docs/reports/task_492_microstructure_source_collection")
DEFAULT_RAW_QUOTE_PATH = Path("data/raw/alpaca_quote_entry_windows/task492_raw_quote_entry_windows.csv")
ALPACA_QUOTES_URL = "https://data.alpaca.markets/v2/stocks/quotes"


@dataclass(frozen=True)
class Task492Artifacts:
    raw_quote_entry_window_panel: pd.DataFrame
    microstructure_entry_feature_panel: pd.DataFrame
    microstructure_source_availability_audit: pd.DataFrame
    microstructure_collection_gap_audit: pd.DataFrame
    task_492_decision: pd.DataFrame


def build_task492_microstructure_source_collection(
    *,
    task487_panel_path: Path = DEFAULT_TASK487_PANEL,
    task489_selected_cells_path: Path = DEFAULT_TASK489_SELECTED_CELLS,
    broad_daily_dir: Path = DEFAULT_BROAD_DAILY_DIR,
    broad_market_cache: Path = DEFAULT_BROAD_MARKET_CACHE,
    raw_quote_path: Path = DEFAULT_RAW_QUOTE_PATH,
    out_dir: Path = DEFAULT_OUT_DIR,
    feed: str = "sip",
    window_seconds: int = 30,
    sleep_seconds: float = 0.05,
    max_requests: int | None = None,
    use_cache_only: bool = False,
) -> Task492Artifacts:
    _, market = load_or_build_broad_market_state(broad_daily_dir, broad_market_cache)
    panel = load_panel_with_broad_market(task487_panel_path, market)
    base = build_task489_selected_panel(panel, task489_selected_cells_path)
    raw_quotes = collect_or_load_quote_windows(
        base,
        raw_quote_path=raw_quote_path,
        feed=feed,
        window_seconds=window_seconds,
        sleep_seconds=sleep_seconds,
        max_requests=max_requests,
        use_cache_only=use_cache_only,
    )
    features = build_microstructure_entry_features(base, raw_quotes)
    source_audit = build_source_availability_audit(raw_quotes, features)
    gap_audit = build_gap_audit(features)
    decision = build_decision(base, raw_quotes, features, source_audit)
    artifacts = Task492Artifacts(raw_quotes, features, source_audit, gap_audit, decision)
    write_artifacts(artifacts, out_dir)
    return artifacts


def collect_or_load_quote_windows(
    base: pd.DataFrame,
    *,
    raw_quote_path: Path,
    feed: str,
    window_seconds: int,
    sleep_seconds: float,
    max_requests: int | None,
    use_cache_only: bool,
) -> pd.DataFrame:
    raw_quote_path.parent.mkdir(parents=True, exist_ok=True)
    existing = pd.read_csv(raw_quote_path, parse_dates=["entry_ts", "quote_ts"]) if raw_quote_path.exists() else pd.DataFrame()
    done = set(existing["lifecycle_id"].astype(str)) if not existing.empty and "lifecycle_id" in existing.columns else set()
    if use_cache_only:
        return existing
    rows: list[pd.DataFrame] = []
    if not existing.empty:
        rows.append(existing)
    requests_done = 0
    for _, row in base.sort_values("entry_ts").iterrows():
        lifecycle_id = str(row["lifecycle_id"])
        if lifecycle_id in done:
            continue
        if max_requests is not None and requests_done >= max_requests:
            break
        entry_ts = pd.to_datetime(row["entry_ts"], utc=True)
        symbol = str(row["symbol"]).upper()
        start_ts = (entry_ts - pd.Timedelta(seconds=window_seconds)).isoformat().replace("+00:00", "Z")
        end_ts = (entry_ts + pd.Timedelta(seconds=1)).isoformat().replace("+00:00", "Z")
        quote_rows = fetch_quote_window(symbol, start_ts, end_ts, feed=feed)
        normalized = normalize_quote_rows(lifecycle_id, symbol, entry_ts, quote_rows, feed)
        rows.append(normalized)
        done.add(lifecycle_id)
        requests_done += 1
        if sleep_seconds:
            time.sleep(sleep_seconds)
    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if not out.empty:
        out = out.drop_duplicates(subset=["lifecycle_id", "quote_ts", "bid_price", "ask_price", "bid_size", "ask_size"]).reset_index(drop=True)
    out.to_csv(raw_quote_path, index=False)
    return out


def fetch_quote_window(symbol: str, start_ts: str, end_ts: str, *, feed: str) -> list[dict[str, object]]:
    api_key = os.environ.get("APCA_API_KEY_ID") or os.environ.get("ALPACA_API_KEY")
    secret_key = os.environ.get("APCA_API_SECRET_KEY") or os.environ.get("ALPACA_SECRET_KEY")
    if not api_key or not secret_key:
        raise RuntimeError("Alpaca credentials are missing. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY.")
    rows: list[dict[str, object]] = []
    page_token: str | None = None
    while True:
        params = {
            "symbols": symbol,
            "start": start_ts,
            "end": end_ts,
            "limit": "10000",
            "feed": feed,
        }
        if page_token:
            params["page_token"] = page_token
        req = Request(
            f"{ALPACA_QUOTES_URL}?{urlencode(params)}",
            headers={
                "APCA-API-KEY-ID": api_key,
                "APCA-API-SECRET-KEY": secret_key,
                "Accept": "application/json",
            },
        )
        with urlopen(req, timeout=30) as response:  # noqa: S310
            payload = json.loads(response.read().decode("utf-8"))
        rows.extend(payload.get("quotes", {}).get(symbol, []))
        page_token = payload.get("next_page_token")
        if not page_token:
            break
    return rows


def normalize_quote_rows(lifecycle_id: str, symbol: str, entry_ts: pd.Timestamp, rows: list[dict[str, object]], feed: str) -> pd.DataFrame:
    normalized: list[dict[str, object]] = []
    for idx, row in enumerate(rows):
        quote_ts = pd.to_datetime(row.get("t"), utc=True, errors="coerce")
        if pd.isna(quote_ts):
            continue
        record = {
            "lifecycle_id": lifecycle_id,
            "symbol": symbol,
            "entry_ts": entry_ts,
            "quote_ts": quote_ts,
            "bid_price": pd.to_numeric(row.get("bp"), errors="coerce"),
            "ask_price": pd.to_numeric(row.get("ap"), errors="coerce"),
            "bid_size": pd.to_numeric(row.get("bs"), errors="coerce"),
            "ask_size": pd.to_numeric(row.get("as"), errors="coerce"),
            "bid_exchange": row.get("bx"),
            "ask_exchange": row.get("ax"),
            "quote_conditions_json": json.dumps(row.get("c", []), sort_keys=True),
            "tape": row.get("z"),
            "feed": feed,
            "raw_receive_timestamp_available_flag": 0,
        }
        record["raw_quote_row_hash"] = _row_hash(record)
        record["raw_quote_row_number"] = idx
        normalized.append(record)
    return pd.DataFrame(normalized)


def build_microstructure_entry_features(base: pd.DataFrame, raw_quotes: pd.DataFrame) -> pd.DataFrame:
    base_cols = ["lifecycle_id", "symbol", "entry_ts", "split_name", "theme_id"]
    output = base[base_cols].copy()
    if raw_quotes.empty:
        for column in microstructure_feature_columns():
            output[column] = np.nan
        output["quote_source_available_flag"] = 0
        output["microstructure_feature_available_flag"] = 0
        return output
    quotes = raw_quotes.copy()
    quotes["entry_ts"] = pd.to_datetime(quotes["entry_ts"], utc=True, errors="coerce")
    quotes["quote_ts"] = pd.to_datetime(quotes["quote_ts"], utc=True, errors="coerce")
    quotes = quotes[quotes["quote_ts"].le(quotes["entry_ts"])].copy()
    quotes["quote_age_seconds"] = (quotes["entry_ts"] - quotes["quote_ts"]).dt.total_seconds()
    quotes = quotes.sort_values(["lifecycle_id", "quote_ts"])
    latest = quotes.groupby("lifecycle_id", as_index=False).tail(1).copy()
    latest["mid_price"] = (latest["bid_price"] + latest["ask_price"]) / 2.0
    latest["spread_bps"] = (latest["ask_price"] - latest["bid_price"]) / latest["mid_price"].replace(0, np.nan) * 10000.0
    latest["nbbo_size_shares"] = latest["bid_size"].fillna(0) + latest["ask_size"].fillna(0)
    latest["nbbo_size_dollar"] = latest["nbbo_size_shares"] * latest["mid_price"] * 100.0
    latest["quote_source_available_flag"] = 1
    latest["microstructure_feature_available_flag"] = (
        latest["spread_bps"].notna() & latest["quote_age_seconds"].notna() & latest["nbbo_size_dollar"].notna()
    ).astype(int)
    feature_cols = [
        "lifecycle_id",
        "quote_ts",
        "bid_price",
        "ask_price",
        "bid_size",
        "ask_size",
        "mid_price",
        "spread_bps",
        "quote_age_seconds",
        "nbbo_size_shares",
        "nbbo_size_dollar",
        "quote_conditions_json",
        "raw_quote_row_hash",
        "quote_source_available_flag",
        "microstructure_feature_available_flag",
    ]
    out = output.merge(latest[feature_cols], on="lifecycle_id", how="left")
    out["quote_source_available_flag"] = out["quote_source_available_flag"].fillna(0).astype(int)
    out["microstructure_feature_available_flag"] = out["microstructure_feature_available_flag"].fillna(0).astype(int)
    assign_microstructure_states(out)
    return out


def assign_microstructure_states(frame: pd.DataFrame) -> None:
    valid_spread = frame.loc[frame["spread_bps"].notna() & frame["spread_bps"].ge(0), "spread_bps"]
    valid_size = frame.loc[frame["nbbo_size_dollar"].notna(), "nbbo_size_dollar"]
    p50 = valid_spread.quantile(0.50) if not valid_spread.empty else np.nan
    p80 = valid_spread.quantile(0.80) if not valid_spread.empty else np.nan
    size50 = valid_size.quantile(0.50) if not valid_size.empty else np.nan
    size25 = valid_size.quantile(0.25) if not valid_size.empty else np.nan
    frame["spread_state"] = "spread_missing"
    frame.loc[frame["spread_bps"].le(p50), "spread_state"] = "tight_spread"
    frame.loc[frame["spread_bps"].gt(p50) & frame["spread_bps"].le(p80), "spread_state"] = "normal_spread"
    frame.loc[frame["spread_bps"].gt(p80), "spread_state"] = "wide_spread"
    frame["quote_freshness_state"] = "quote_missing"
    frame.loc[frame["quote_age_seconds"].le(5), "quote_freshness_state"] = "fresh_quote"
    frame.loc[frame["quote_age_seconds"].gt(5) & frame["quote_age_seconds"].le(30), "quote_freshness_state"] = "stale_quote"
    frame.loc[frame["quote_age_seconds"].gt(30), "quote_freshness_state"] = "too_stale_quote"
    frame["nbbo_size_state"] = "size_missing"
    frame.loc[frame["nbbo_size_dollar"].ge(size50), "nbbo_size_state"] = "thick_nbbo"
    frame.loc[frame["nbbo_size_dollar"].lt(size50) & frame["nbbo_size_dollar"].ge(size25), "nbbo_size_state"] = "normal_nbbo"
    frame.loc[frame["nbbo_size_dollar"].lt(size25), "nbbo_size_state"] = "thin_nbbo"
    frame["microstructure_tradability_state"] = "microstructure_missing"
    clean = frame["spread_state"].eq("tight_spread") & frame["quote_freshness_state"].eq("fresh_quote") & frame["nbbo_size_state"].isin(["thick_nbbo", "normal_nbbo"])
    heavy = frame["spread_state"].eq("wide_spread") | frame["quote_freshness_state"].isin(["stale_quote", "too_stale_quote"]) | frame["nbbo_size_state"].eq("thin_nbbo")
    frame.loc[clean, "microstructure_tradability_state"] = "micro_clean"
    frame.loc[~clean & ~heavy & frame["microstructure_feature_available_flag"].eq(1), "microstructure_tradability_state"] = "micro_neutral"
    frame.loc[heavy & frame["microstructure_feature_available_flag"].eq(1), "microstructure_tradability_state"] = "micro_friction_heavy"


def microstructure_feature_columns() -> list[str]:
    return [
        "quote_ts",
        "bid_price",
        "ask_price",
        "bid_size",
        "ask_size",
        "mid_price",
        "spread_bps",
        "quote_age_seconds",
        "nbbo_size_shares",
        "nbbo_size_dollar",
        "quote_conditions_json",
        "raw_quote_row_hash",
        "spread_state",
        "quote_freshness_state",
        "nbbo_size_state",
        "microstructure_tradability_state",
    ]


def build_source_availability_audit(raw_quotes: pd.DataFrame, features: pd.DataFrame) -> pd.DataFrame:
    available = int(features["microstructure_feature_available_flag"].sum()) if not features.empty else 0
    total = int(len(features))
    rows = [
        {"source_name": "historical_nbbo_quote", "source_status": "available_exact_from_alpaca_quotes" if len(raw_quotes) else "missing", "usable_feature_count": available, "candidate_count": total},
        {"source_name": "spread_bps", "source_status": "available_exact_from_bid_ask", "usable_feature_count": available, "candidate_count": total},
        {"source_name": "nbbo_bid_ask_size", "source_status": "available_exact_from_quotes_not_depth_book", "usable_feature_count": available, "candidate_count": total},
        {"source_name": "raw_receive_timestamp", "source_status": "not_available_in_historical_api_live_archive_required", "usable_feature_count": 0, "candidate_count": total},
        {"source_name": "status_luld", "source_status": "not_available_in_current_historical_quote_source", "usable_feature_count": 0, "candidate_count": total},
        {"source_name": "depth_book", "source_status": "not_available_current_source_nbbo_size_only", "usable_feature_count": 0, "candidate_count": total},
    ]
    return pd.DataFrame(rows)


def build_gap_audit(features: pd.DataFrame) -> pd.DataFrame:
    if features.empty:
        return pd.DataFrame()
    return (
        features.assign(feature_missing_flag=1 - features["microstructure_feature_available_flag"])
        .groupby(["split_name"], dropna=False)
        .agg(
            candidate_count=("lifecycle_id", "count"),
            quote_available_count=("quote_source_available_flag", "sum"),
            microstructure_feature_available_count=("microstructure_feature_available_flag", "sum"),
            missing_count=("feature_missing_flag", "sum"),
        )
        .reset_index()
    )


def build_decision(base: pd.DataFrame, raw_quotes: pd.DataFrame, features: pd.DataFrame, source_audit: pd.DataFrame) -> pd.DataFrame:
    coverage = float(features["microstructure_feature_available_flag"].mean()) if not features.empty else 0.0
    return pd.DataFrame(
        [
            {
                "task_id": "Task492",
                "task_name": "Microstructure Source Collection",
                "task489_base_count": int(len(base)),
                "raw_quote_row_count": int(len(raw_quotes)),
                "microstructure_feature_coverage": coverage,
                "feature_available_count": int(features["microstructure_feature_available_flag"].sum()) if not features.empty else 0,
                "raw_receive_timestamp_available_flag": 0,
                "status_luld_available_flag": 0,
                "depth_book_available_flag": 0,
                "historical_quote_spread_available_flag": int((source_audit["source_name"].eq("spread_bps")).any()),
                "task_492_status": "MICROSTRUCTURE_QUOTES_READY_STATUS_LULD_DEPTH_STILL_MISSING" if coverage > 0 else "MICROSTRUCTURE_COLLECTION_FAILED",
                "strategy_acceptance_status": "DATA_LAYER_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )


def write_artifacts(artifacts: Task492Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.raw_quote_entry_window_panel.to_csv(out_dir / "raw_quote_entry_window_panel.csv", index=False)
    artifacts.microstructure_entry_feature_panel.to_csv(out_dir / "microstructure_entry_feature_panel.csv", index=False)
    artifacts.microstructure_source_availability_audit.to_csv(out_dir / "microstructure_source_availability_audit.csv", index=False)
    artifacts.microstructure_collection_gap_audit.to_csv(out_dir / "microstructure_collection_gap_audit.csv", index=False)
    artifacts.task_492_decision.to_csv(out_dir / "task_492_decision.csv", index=False)
    (out_dir / "task_492_microstructure_source_collection.md").write_text(build_report(artifacts), encoding="utf-8")


def build_report(artifacts: Task492Artifacts) -> str:
    d = artifacts.task_492_decision.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task 492 - Microstructure Source Collection",
            "",
            "## Quant Expert Report",
            "",
            f"- Task489 base count: {d['task489_base_count']}",
            f"- Raw quote rows collected: {d['raw_quote_row_count']}",
            f"- Microstructure feature coverage: {float(d['microstructure_feature_coverage']):.1%}",
            "- Spread/quote-size source: historical Alpaca NBBO quotes",
            "- Raw receive timestamp: NOT available in historical API; live archive required",
            "- Status/LULD/depth-book: NOT available in current quote source; separate stream/source required",
            "",
            "## Source Availability",
            "",
            _csv_block(artifacts.microstructure_source_availability_audit),
            "",
            "## No-Background Decision-Maker Report",
            "",
            "이번 단계는 전략 성능이 아니라 데이터 확보 단계다. 실제 quote 기반 spread와 NBBO size는 확보했지만, 체결 리스크를 완전히 보려면 raw receive timestamp, status/LULD, depth book이 추가로 필요하다.",
        ]
    )


def _row_hash(record: dict[str, object]) -> str:
    payload = json.dumps({k: str(v) for k, v in sorted(record.items()) if k != "raw_quote_row_hash"}, sort_keys=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _csv_block(df: pd.DataFrame) -> str:
    if df.empty:
        return "_empty_"
    return "```csv\n" + df.to_csv(index=False) + "```"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task487-panel-path", type=Path, default=DEFAULT_TASK487_PANEL)
    parser.add_argument("--task489-selected-cells-path", type=Path, default=DEFAULT_TASK489_SELECTED_CELLS)
    parser.add_argument("--broad-daily-dir", type=Path, default=DEFAULT_BROAD_DAILY_DIR)
    parser.add_argument("--broad-market-cache", type=Path, default=DEFAULT_BROAD_MARKET_CACHE)
    parser.add_argument("--raw-quote-path", type=Path, default=DEFAULT_RAW_QUOTE_PATH)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    parser.add_argument("--feed", default="sip")
    parser.add_argument("--window-seconds", type=int, default=30)
    parser.add_argument("--sleep-seconds", type=float, default=0.05)
    parser.add_argument("--max-requests", type=int, default=None)
    parser.add_argument("--use-cache-only", action="store_true")
    args = parser.parse_args()
    artifacts = build_task492_microstructure_source_collection(
        task487_panel_path=args.task487_panel_path,
        task489_selected_cells_path=args.task489_selected_cells_path,
        broad_daily_dir=args.broad_daily_dir,
        broad_market_cache=args.broad_market_cache,
        raw_quote_path=args.raw_quote_path,
        out_dir=args.out_dir,
        feed=args.feed,
        window_seconds=args.window_seconds,
        sleep_seconds=args.sleep_seconds,
        max_requests=args.max_requests,
        use_cache_only=args.use_cache_only,
    )
    row = artifacts.task_492_decision.iloc[0]
    print(
        "[TASK492] "
        f"status={row['task_492_status']} coverage={float(row['microstructure_feature_coverage']):.1%} "
        f"quotes={row['raw_quote_row_count']}"
    )


if __name__ == "__main__":
    main()
