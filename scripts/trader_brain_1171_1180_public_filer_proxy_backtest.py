from __future__ import annotations

import csv
import hashlib
import json
import math
import sys
import time
import zipfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import yfinance as yf


ROOT = Path(__file__).resolve().parents[1]
TASK1161 = ROOT / "data/artifacts/task_1161_1170_sec_bulk_public_filer_universe"
SEC_ZIP = ROOT / "data/raw/task_1161_1170_sec_bulk_submissions/submissions.zip"
RAW_DIR = ROOT / "data/raw/yfinance/task_1171_1180_public_filer_proxy"
OUT_DIR = ROOT / "data/artifacts/task_1171_1180_public_filer_proxy_backtest"
REPORT_DIR = ROOT / "docs/reports/task_1171_1180_public_filer_proxy_backtest"

AUTHORITY = "DIAGNOSTIC_PUBLIC_FILER_PROXY_BACKTEST_ONLY"
HIST_START = date(2021, 1, 31)
HIST_END = date(2026, 3, 31)
PRICE_START = "2020-01-01"
PRICE_END = "2026-04-15"
INITIAL_CAPITAL = 1000.0
ROUND_TRIP_COST_BPS = 20.0
MAX_PRICE_SYMBOLS = 1500
CHUNK_SIZE = 75
BENCHMARK = "QQQ"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def clean_symbol(symbol: str) -> str:
    return symbol.strip().upper()


def normal_ticker(symbol: str) -> bool:
    if not symbol or len(symbol) > 5:
        return False
    return symbol.replace("-", "").isalnum() and "." not in symbol and "/" not in symbol


def month_decision_rows() -> list[dict[str, str]]:
    rows = read_csv(TASK1161 / "task1165_decision_calendar.csv")
    return [row for row in rows if HIST_START.isoformat() <= row["decision_date"] <= HIST_END.isoformat()]


def build_symbol_candidate_pool() -> list[dict[str, object]]:
    entities = read_csv(TASK1161 / "task1163_public_filer_entity_panel.csv")
    rows: list[dict[str, object]] = []
    for row in entities:
        exchanges = set(filter(None, row["exchanges"].split(";")))
        if not ({"NYSE", "Nasdaq"} & exchanges):
            continue
        first = parse_dt(row["first_acceptance_ts"])
        if first is None or first.date() > HIST_END:
            continue
        for symbol in row["tickers"].split(";"):
            symbol = clean_symbol(symbol)
            if not normal_ticker(symbol):
                continue
            rows.append(
                {
                    "task_id": "Task1171",
                    "symbol": symbol,
                    "cik": row["cik"],
                    "entity_name": row["entity_name"],
                    "exchanges": row["exchanges"],
                    "first_acceptance_ts": row["first_acceptance_ts"],
                    "historical_filing_count_2021_2026q1": row["historical_filing_count_2021_2026q1"],
                    "pool_source": "sec_public_filer_proxy",
                    "selection_prefilter_state": "neutral_download_pool_sorted_by_symbol",
                    "authority": AUTHORITY,
                }
            )
    dedup: dict[str, dict[str, object]] = {}
    for row in sorted(rows, key=lambda item: (str(item["symbol"]), str(item["cik"]))):
        dedup.setdefault(str(row["symbol"]), row)
    selected = list(dedup.values())[:MAX_PRICE_SYMBOLS]
    selected.append(
        {
            "task_id": "Task1171",
            "symbol": BENCHMARK,
            "cik": "",
            "entity_name": "Invesco QQQ Trust",
            "exchanges": "Nasdaq",
            "first_acceptance_ts": "",
            "historical_filing_count_2021_2026q1": "",
            "pool_source": "benchmark",
            "selection_prefilter_state": "benchmark_only_not_strategy_candidate",
            "authority": AUTHORITY,
        }
    )
    return selected


def flatten_download_frame(data: pd.DataFrame, tickers: list[str]) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    if data.empty:
        return out
    if isinstance(data.columns, pd.MultiIndex):
        for ticker in tickers:
            if ticker in data.columns.get_level_values(0):
                frame = data.xs(ticker, axis=1, level=0, drop_level=True).copy()
                if not frame.empty:
                    out[ticker] = frame
            elif ticker in data.columns.get_level_values(1):
                frame = data.xs(ticker, axis=1, level=1, drop_level=True).copy()
                if not frame.empty:
                    out[ticker] = frame
    else:
        if len(tickers) == 1:
            out[tickers[0]] = data.copy()
    return out


def download_prices(pool: list[dict[str, object]]) -> list[dict[str, object]]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    symbols = [str(row["symbol"]) for row in pool]
    rows: list[dict[str, object]] = []
    pending_symbols: list[str] = []
    for symbol in symbols:
        path = RAW_DIR / "daily" / symbol / f"{symbol}_daily.csv"
        if path.exists() and path.stat().st_size > 0:
            rows.append(
                {
                    "task_id": "Task1172",
                    "symbol": symbol,
                    "download_status": "downloaded",
                    "row_count": max(sum(1 for _ in path.open(encoding="utf-8", errors="ignore")) - 1, 0),
                    "raw_source_path": rel(path),
                    "source_hash": sha256(path),
                    "downloaded_at_utc": now_utc(),
                    "error": "",
                    "authority": AUTHORITY,
                }
            )
        else:
            pending_symbols.append(symbol)
    for start in range(0, len(pending_symbols), CHUNK_SIZE):
        chunk = pending_symbols[start:start + CHUNK_SIZE]
        chunk_id = f"{start // CHUNK_SIZE + 1:03d}"
        try:
            data = yf.download(
                tickers=" ".join(chunk),
                start=PRICE_START,
                end=PRICE_END,
                auto_adjust=True,
                group_by="ticker",
                threads=True,
                progress=False,
                timeout=30,
            )
        except Exception as exc:
            for symbol in chunk:
                rows.append(
                    {
                        "task_id": "Task1172",
                        "symbol": symbol,
                        "download_status": "failed",
                        "row_count": 0,
                        "raw_source_path": "",
                        "source_hash": "",
                        "downloaded_at_utc": now_utc(),
                        "error": str(exc)[:300],
                        "authority": AUTHORITY,
                    }
                )
            continue
        frames = flatten_download_frame(data, chunk)
        for symbol in chunk:
            frame = frames.get(symbol)
            path = RAW_DIR / "daily" / symbol / f"{symbol}_daily.csv"
            if frame is None or frame.empty or "Close" not in frame.columns:
                rows.append(
                    {
                        "task_id": "Task1172",
                        "symbol": symbol,
                        "download_status": "empty",
                        "row_count": 0,
                        "raw_source_path": "",
                        "source_hash": "",
                        "downloaded_at_utc": now_utc(),
                        "error": "no_price_rows",
                        "authority": AUTHORITY,
                    }
                )
                continue
            frame = frame.reset_index()
            path.parent.mkdir(parents=True, exist_ok=True)
            frame.to_csv(path, index=False)
            rows.append(
                {
                    "task_id": "Task1172",
                    "symbol": symbol,
                    "download_status": "downloaded",
                    "row_count": len(frame),
                    "raw_source_path": rel(path),
                    "source_hash": sha256(path),
                    "downloaded_at_utc": now_utc(),
                    "error": "",
                    "authority": AUTHORITY,
                }
            )
        print(f"[PRICE_DOWNLOAD_PROGRESS] chunk={chunk_id} symbols={len(chunk)}", flush=True)
        time.sleep(0.25)
    return sorted(rows, key=lambda row: str(row["symbol"]))


def load_price_tables(download_rows: list[dict[str, object]]) -> dict[str, pd.DataFrame]:
    prices: dict[str, pd.DataFrame] = {}
    for row in download_rows:
        if row["download_status"] != "downloaded":
            continue
        path = ROOT / str(row["raw_source_path"])
        frame = pd.read_csv(path)
        date_col = "Date" if "Date" in frame.columns else frame.columns[0]
        frame[date_col] = pd.to_datetime(frame[date_col]).dt.date
        frame = frame.rename(columns={date_col: "date"})
        if "Close" not in frame.columns or "Volume" not in frame.columns:
            continue
        frame = frame[["date", "Close", "Volume"]].dropna()
        frame = frame.sort_values("date")
        prices[str(row["symbol"])] = frame
    return prices


def price_on_or_before(frame: pd.DataFrame, d: date) -> tuple[date, float] | None:
    sub = frame[frame["date"] <= d]
    if sub.empty:
        return None
    last = sub.iloc[-1]
    return last["date"], float(last["Close"])


def price_on_or_after(frame: pd.DataFrame, d: date) -> tuple[date, float] | None:
    sub = frame[frame["date"] >= d]
    if sub.empty:
        return None
    first = sub.iloc[0]
    return first["date"], float(first["Close"])


def pct_change(frame: pd.DataFrame, d: date, lookback_days: int) -> float | None:
    current = price_on_or_before(frame, d)
    past = price_on_or_before(frame, d - timedelta(days=lookback_days))
    if not current or not past or past[1] <= 0:
        return None
    return current[1] / past[1] - 1.0


def realized_vol(frame: pd.DataFrame, d: date, lookback_days: int = 90) -> float | None:
    sub = frame[(frame["date"] <= d) & (frame["date"] >= d - timedelta(days=lookback_days))].copy()
    if len(sub) < 30:
        return None
    sub["ret"] = sub["Close"].pct_change()
    vol = sub["ret"].std()
    if pd.isna(vol):
        return None
    return float(vol) * math.sqrt(252)


def avg_dollar_volume(frame: pd.DataFrame, d: date, lookback_days: int = 60) -> float | None:
    sub = frame[(frame["date"] <= d) & (frame["date"] >= d - timedelta(days=lookback_days))]
    if len(sub) < 20:
        return None
    return float((sub["Close"] * sub["Volume"]).mean())


def load_asof_membership(symbols: set[str]) -> dict[str, set[str]]:
    rows = read_csv(TASK1161 / "task1166_public_filer_asof_universe_panel.csv")
    out: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        symbol = clean_symbol(row["symbol"])
        if symbol in symbols:
            out[row["decision_asof_ts"]].add(symbol)
    return out


def sec_filing_features(symbols: set[str], decision_rows: list[dict[str, str]], symbol_to_cik: dict[str, str]) -> dict[tuple[str, str], dict[str, object]]:
    decision_dates = [(row["decision_asof_ts"], datetime.fromisoformat(row["decision_asof_ts"].replace("Z", "+00:00"))) for row in decision_rows]
    features: dict[tuple[str, str], dict[str, object]] = {}
    cik_to_symbols: dict[str, list[str]] = defaultdict(list)
    for symbol, cik in symbol_to_cik.items():
        if symbol in symbols and cik:
            cik_to_symbols[cik].append(symbol)
    needed_ciks = set(cik_to_symbols)
    with zipfile.ZipFile(SEC_ZIP) as zf:
        names = {Path(name).stem.replace("CIK", "").zfill(10): name for name in zf.namelist() if name.lower().endswith(".json")}
        for idx, cik in enumerate(sorted(needed_ciks), start=1):
            name = names.get(cik)
            if not name:
                continue
            payload = json.loads(zf.read(name))
            recent = payload.get("filings", {}).get("recent", {})
            acceptance = recent.get("acceptanceDateTime", [])
            forms = recent.get("form", [])
            accepted_forms: list[tuple[datetime, str]] = []
            for accepted_value, form in zip(acceptance, forms):
                ts = parse_dt(str(accepted_value))
                if ts is not None:
                    accepted_forms.append((ts, str(form)))
            accepted_forms.sort(key=lambda item: item[0])
            for symbol in cik_to_symbols[cik]:
                for decision_ts, decision_dt in decision_dates:
                    look90 = decision_dt - timedelta(days=90)
                    look365 = decision_dt - timedelta(days=365)
                    filings90 = [form for ts, form in accepted_forms if look90 <= ts <= decision_dt]
                    filings365 = [form for ts, form in accepted_forms if look365 <= ts <= decision_dt]
                    features[(decision_ts, symbol)] = {
                        "filing_count_90d": len(filings90),
                        "filing_count_365d": len(filings365),
                        "form_diversity_365d": len(set(filings365)),
                        "latest_filing_ts": max((ts.isoformat() for ts, _form in accepted_forms if ts <= decision_dt), default=""),
                    }
            if idx % 250 == 0:
                print(f"[SEC_FEATURE_PROGRESS] ciks={idx}/{len(needed_ciks)}", flush=True)
    return features


def zscore(values: list[float]) -> list[float]:
    if not values:
        return []
    mean = sum(values) / len(values)
    var = sum((value - mean) ** 2 for value in values) / len(values)
    std = math.sqrt(var)
    if std == 0:
        return [0.0 for _ in values]
    return [(value - mean) / std for value in values]


def build_feature_panel(
    pool: list[dict[str, object]],
    download_rows: list[dict[str, object]],
    prices: dict[str, pd.DataFrame],
    decision_rows: list[dict[str, str]],
) -> list[dict[str, object]]:
    downloaded_symbols = {str(row["symbol"]) for row in download_rows if row["download_status"] == "downloaded"}
    strategy_symbols = {str(row["symbol"]) for row in pool if row["pool_source"] != "benchmark"} & downloaded_symbols
    symbol_to_cik = {str(row["symbol"]): str(row["cik"]) for row in pool if row["pool_source"] != "benchmark"}
    asof_membership = load_asof_membership(strategy_symbols)
    sec_features = sec_filing_features(strategy_symbols, decision_rows, symbol_to_cik)
    rows: list[dict[str, object]] = []
    for decision in decision_rows:
        decision_date = date.fromisoformat(decision["decision_date"])
        decision_ts = decision["decision_asof_ts"]
        eligible_symbols = sorted(asof_membership.get(decision_ts, set()) & strategy_symbols)
        raw_rows = []
        for symbol in eligible_symbols:
            frame = prices.get(symbol)
            if frame is None:
                continue
            close = price_on_or_before(frame, decision_date)
            entry = price_on_or_after(frame, decision_date + timedelta(days=1))
            if not close or not entry:
                continue
            mom_126 = pct_change(frame, decision_date, 182)
            mom_252 = pct_change(frame, decision_date, 365)
            vol_90 = realized_vol(frame, decision_date, 90)
            adv_60 = avg_dollar_volume(frame, decision_date, 60)
            if mom_126 is None or mom_252 is None or vol_90 is None or adv_60 is None:
                continue
            if adv_60 < 5_000_000:
                continue
            sec = sec_features.get((decision_ts, symbol), {})
            raw_rows.append(
                {
                    "decision_asof_ts": decision_ts,
                    "decision_date": decision["decision_date"],
                    "symbol": symbol,
                    "cik": symbol_to_cik.get(symbol, ""),
                    "decision_close_date": close[0].isoformat(),
                    "decision_close": close[1],
                    "entry_date": entry[0].isoformat(),
                    "entry_price": entry[1],
                    "momentum_126d": mom_126,
                    "momentum_252d": mom_252,
                    "realized_vol_90d": vol_90,
                    "avg_dollar_volume_60d": adv_60,
                    "filing_count_90d": int(sec.get("filing_count_90d", 0)),
                    "filing_count_365d": int(sec.get("filing_count_365d", 0)),
                    "form_diversity_365d": int(sec.get("form_diversity_365d", 0)),
                    "latest_filing_ts": sec.get("latest_filing_ts", ""),
                }
            )
        if not raw_rows:
            continue
        score_inputs = {
            "momentum_126d": zscore([float(row["momentum_126d"]) for row in raw_rows]),
            "momentum_252d": zscore([float(row["momentum_252d"]) for row in raw_rows]),
            "realized_vol_90d": zscore([float(row["realized_vol_90d"]) for row in raw_rows]),
            "filing_count_90d": zscore([float(row["filing_count_90d"]) for row in raw_rows]),
            "form_diversity_365d": zscore([float(row["form_diversity_365d"]) for row in raw_rows]),
            "avg_dollar_volume_60d": zscore([math.log(max(float(row["avg_dollar_volume_60d"]), 1.0)) for row in raw_rows]),
        }
        for idx, row in enumerate(raw_rows):
            score = (
                0.40 * score_inputs["momentum_126d"][idx]
                + 0.25 * score_inputs["momentum_252d"][idx]
                - 0.20 * score_inputs["realized_vol_90d"][idx]
                + 0.10 * score_inputs["filing_count_90d"][idx]
                + 0.10 * score_inputs["form_diversity_365d"][idx]
                + 0.05 * score_inputs["avg_dollar_volume_60d"][idx]
            )
            rows.append(
                {
                    "task_id": "Task1174",
                    "feature_row_id": f"PFPROXY1174-{len(rows)+1:09d}",
                    **row,
                    "proxy_brain_score": round(score, 8),
                    "source_time_pass": "1",
                    "future_price_used": "0",
                    "future_filing_used": "0",
                    "authority": AUTHORITY,
                }
            )
    return rows


def next_decision_map(decision_rows: list[dict[str, str]]) -> dict[str, str]:
    ordered = [row["decision_asof_ts"] for row in decision_rows]
    return {ordered[i]: ordered[i + 1] for i in range(len(ordered) - 1)}


def build_selections(features: list[dict[str, object]], slot_cap: int) -> list[dict[str, object]]:
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in features:
        grouped[str(row["decision_asof_ts"])].append(row)
    rows: list[dict[str, object]] = []
    for decision_ts, items in sorted(grouped.items()):
        selected = sorted(items, key=lambda row: (-float(row["proxy_brain_score"]), str(row["symbol"])))[:slot_cap]
        for rank, item in enumerate(selected, start=1):
            rows.append(
                {
                    "task_id": "Task1175",
                    "policy_variant_id": f"public_filer_proxy_slot{slot_cap}_v1",
                    "selection_id": f"PFSEL1175-{slot_cap}-{len(rows)+1:07d}",
                    "decision_asof_ts": decision_ts,
                    "rank": rank,
                    "symbol": item["symbol"],
                    "cik": item["cik"],
                    "entry_date": item["entry_date"],
                    "entry_price": item["entry_price"],
                    "proxy_brain_score": item["proxy_brain_score"],
                    "momentum_126d": item["momentum_126d"],
                    "momentum_252d": item["momentum_252d"],
                    "filing_count_90d": item["filing_count_90d"],
                    "form_diversity_365d": item["form_diversity_365d"],
                    "authority": AUTHORITY,
                }
            )
    return rows


def run_monthly_backtest(
    selections: list[dict[str, object]],
    prices: dict[str, pd.DataFrame],
    decision_rows: list[dict[str, str]],
    slot_cap: int,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    next_map = next_decision_map(decision_rows)
    grouped: dict[str, list[dict[str, object]]] = defaultdict(list)
    for row in selections:
        grouped[str(row["decision_asof_ts"])].append(row)
    capital = INITIAL_CAPITAL
    equity_rows: list[dict[str, object]] = []
    trade_rows: list[dict[str, object]] = []
    for decision in decision_rows[:-1]:
        decision_ts = decision["decision_asof_ts"]
        next_ts = next_map[decision_ts]
        exit_decision_date = date.fromisoformat(next(row["decision_date"] for row in decision_rows if row["decision_asof_ts"] == next_ts))
        items = grouped.get(decision_ts, [])
        if not items:
            equity_rows.append(
                {
                    "task_id": "Task1176",
                    "policy_variant_id": f"public_filer_proxy_slot{slot_cap}_v1",
                    "decision_asof_ts": decision_ts,
                    "equity": round(capital, 4),
                    "period_return": 0.0,
                    "selected_count": 0,
                    "authority": AUTHORITY,
                }
            )
            continue
        per_position = capital / len(items)
        new_capital = 0.0
        for item in items:
            symbol = str(item["symbol"])
            frame = prices.get(symbol)
            if frame is None:
                continue
            entry_date = date.fromisoformat(str(item["entry_date"]))
            entry_price = float(item["entry_price"])
            exit_price_row = price_on_or_before(frame, exit_decision_date)
            if exit_price_row is None:
                continue
            exit_date, exit_price = exit_price_row
            gross_return = exit_price / entry_price - 1.0
            net_return = gross_return - ROUND_TRIP_COST_BPS / 10000.0
            pnl = per_position * net_return
            new_capital += per_position + pnl
            trade_rows.append(
                {
                    "task_id": "Task1176",
                    "policy_variant_id": f"public_filer_proxy_slot{slot_cap}_v1",
                    "trade_id": f"PFTRADE1176-{slot_cap}-{len(trade_rows)+1:07d}",
                    "decision_asof_ts": decision_ts,
                    "symbol": symbol,
                    "entry_date": entry_date.isoformat(),
                    "entry_price": round(entry_price, 6),
                    "exit_date": exit_date.isoformat(),
                    "exit_price": round(exit_price, 6),
                    "gross_return": round(gross_return, 8),
                    "net_return": round(net_return, 8),
                    "capital_allocated": round(per_position, 4),
                    "pnl": round(pnl, 4),
                    "authority": AUTHORITY,
                }
            )
        if new_capital > 0:
            period_return = new_capital / capital - 1.0
            capital = new_capital
        else:
            period_return = 0.0
        equity_rows.append(
            {
                "task_id": "Task1176",
                "policy_variant_id": f"public_filer_proxy_slot{slot_cap}_v1",
                "decision_asof_ts": decision_ts,
                "equity": round(capital, 4),
                "period_return": round(period_return, 8),
                "selected_count": len(items),
                "authority": AUTHORITY,
            }
        )
    summary = {
        "policy_variant_id": f"public_filer_proxy_slot{slot_cap}_v1",
        "final_equity": capital,
        "trade_count": len(trade_rows),
        "periods": len(equity_rows),
    }
    return trade_rows, equity_rows, summary


def max_drawdown(equity_values: list[float]) -> float:
    peak = -float("inf")
    worst = 0.0
    for value in equity_values:
        peak = max(peak, value)
        if peak > 0:
            worst = min(worst, value / peak - 1.0)
    return worst


def cagr(start_value: float, end_value: float, start_date: date, end_date: date) -> float:
    years = (end_date - start_date).days / 365.25
    if start_value <= 0 or end_value <= 0 or years <= 0:
        return 0.0
    return (end_value / start_value) ** (1.0 / years) - 1.0


def benchmark_summary(prices: dict[str, pd.DataFrame], decision_rows: list[dict[str, str]]) -> dict[str, object]:
    frame = prices[BENCHMARK]
    start = date.fromisoformat(decision_rows[0]["decision_date"]) + timedelta(days=1)
    end = date.fromisoformat(decision_rows[-1]["decision_date"])
    entry = price_on_or_after(frame, start)
    exit_ = price_on_or_before(frame, end)
    if not entry or not exit_:
        return {"benchmark_symbol": BENCHMARK, "benchmark_final_equity": 0.0}
    final = INITIAL_CAPITAL * (exit_[1] / entry[1])
    return {
        "benchmark_symbol": BENCHMARK,
        "benchmark_entry_date": entry[0].isoformat(),
        "benchmark_exit_date": exit_[0].isoformat(),
        "benchmark_final_equity": round(final, 4),
        "benchmark_cagr": round(cagr(INITIAL_CAPITAL, final, entry[0], exit_[0]), 6),
    }


def build_metric_rows(summaries: list[dict[str, object]], equity_by_variant: dict[str, list[dict[str, object]]], benchmark: dict[str, object], decision_rows: list[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    start = date.fromisoformat(decision_rows[0]["decision_date"])
    end = date.fromisoformat(decision_rows[-1]["decision_date"])
    benchmark_final = float(benchmark["benchmark_final_equity"])
    for summary in summaries:
        variant = str(summary["policy_variant_id"])
        equities = [INITIAL_CAPITAL] + [float(row["equity"]) for row in equity_by_variant[variant]]
        final = float(summary["final_equity"])
        rows.append(
            {
                "task_id": "Task1177",
                "policy_variant_id": variant,
                "initial_capital": INITIAL_CAPITAL,
                "final_equity": round(final, 4),
                "total_return": round(final / INITIAL_CAPITAL - 1.0, 6),
                "cagr": round(cagr(INITIAL_CAPITAL, final, start, end), 6),
                "max_drawdown": round(max_drawdown(equities), 6),
                "trade_count": summary["trade_count"],
                "benchmark_symbol": benchmark["benchmark_symbol"],
                "benchmark_final_equity": benchmark["benchmark_final_equity"],
                "benchmark_cagr": benchmark["benchmark_cagr"],
                "beats_benchmark": "1" if final > benchmark_final else "0",
                "strategy_acceptance": "NOT_ACCEPTED",
                "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "real_capital": "FORBIDDEN",
                "authority": AUTHORITY,
            }
        )
    return rows


def write_report(decision: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md = REPORT_DIR / "task_1171_1180_public_filer_proxy_backtest.md"
    lines = [
        "# Task1171-1180 Public-Filer Proxy Backtest",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{decision['verdict']}`.",
        f"- Price pool symbols: {decision['price_pool_symbols']}.",
        f"- Price downloaded symbols: {decision['price_downloaded_symbols']}.",
        f"- Feature rows: {decision['feature_rows']}.",
        f"- Best variant: `{decision['best_variant']}`.",
        f"- Best final equity: {decision['best_final_equity']}.",
        f"- Best CAGR: {decision['best_cagr']}.",
        f"- Best MDD: {decision['best_max_drawdown']}.",
        f"- QQQ final equity: {decision['benchmark_final_equity']}.",
        "- Strategy acceptance: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "This is the first broad public-filer proxy replay after removing the custom 10x7 winner basket as the selection universe.",
        "",
        "The replay uses:",
        "",
        "- SEC public-filer as-of proxy membership.",
        "- yfinance daily adjusted prices for a bounded 1,500-symbol download pool plus QQQ.",
        "- Monthly decisions from 2021-01-31 through 2026-03-31.",
        "- Trailing price momentum, trailing volatility, dollar-volume, and SEC filing-activity features.",
        "- Slot caps 3, 5, and 10.",
        "",
        "Limitations:",
        "",
        "- This is not true exchange-listed PIT.",
        "- The price universe is a bounded download pool, not all 8,129 public filers.",
        "- Current ticker metadata remains a proxy limitation.",
        "- No acceptance or deployment status changes.",
        "",
        "## No-Background Decision-Maker Report",
        "",
        "We finally moved away from the 70-name handpicked basket.",
        "",
        "The model now chooses from a broad SEC public-filer universe proxy.",
        "",
        "This is a real diagnostic backtest, but still not a final institution-grade acceptance test.",
        "",
        "## Artifact Manifest",
        "",
        "- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1171_price_download_pool.csv`",
        "- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1172_yfinance_price_download_ledger.csv`",
        "- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1173_price_coverage_gate.csv`",
        "- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1174_public_filer_proxy_feature_panel.csv`",
        "- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1175_policy_selections.csv`",
        "- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1176_proxy_backtest_trades.csv`",
        "- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1176_proxy_backtest_equity.csv`",
        "- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1177_proxy_backtest_metrics.csv`",
        "- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1180_public_filer_proxy_backtest_closeout.csv`",
        "- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1180_public_filer_proxy_backtest_closeout.json`",
    ]
    md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    write_csv(REPORT_DIR / "task_1171_1180_decision.csv", [decision])


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    pool = build_symbol_candidate_pool()
    write_csv(OUT_DIR / "task1171_price_download_pool.csv", pool)
    download_rows = download_prices(pool)
    write_csv(OUT_DIR / "task1172_yfinance_price_download_ledger.csv", download_rows)
    prices = load_price_tables(download_rows)
    decision_rows = month_decision_rows()
    coverage = [
        {
            "task_id": "Task1173",
            "price_pool_symbols": len(pool),
            "strategy_price_pool_symbols": len(pool) - 1,
            "price_downloaded_symbols": len(prices),
            "benchmark_downloaded": "1" if BENCHMARK in prices else "0",
            "price_coverage_pass": "1" if len(prices) >= 500 and BENCHMARK in prices else "0",
            "authority": AUTHORITY,
        }
    ]
    write_csv(OUT_DIR / "task1173_price_coverage_gate.csv", coverage)
    features = build_feature_panel(pool, download_rows, prices, decision_rows)
    write_csv(OUT_DIR / "task1174_public_filer_proxy_feature_panel.csv", features)
    all_selections: list[dict[str, object]] = []
    all_trades: list[dict[str, object]] = []
    all_equity: list[dict[str, object]] = []
    summaries: list[dict[str, object]] = []
    equity_by_variant: dict[str, list[dict[str, object]]] = {}
    for slot_cap in [3, 5, 10]:
        selections = build_selections(features, slot_cap)
        trades, equity, summary = run_monthly_backtest(selections, prices, decision_rows, slot_cap)
        all_selections.extend(selections)
        all_trades.extend(trades)
        all_equity.extend(equity)
        summaries.append(summary)
        equity_by_variant[str(summary["policy_variant_id"])] = equity
    write_csv(OUT_DIR / "task1175_policy_selections.csv", all_selections)
    write_csv(OUT_DIR / "task1176_proxy_backtest_trades.csv", all_trades)
    write_csv(OUT_DIR / "task1176_proxy_backtest_equity.csv", all_equity)
    benchmark = benchmark_summary(prices, decision_rows)
    metrics = build_metric_rows(summaries, equity_by_variant, benchmark, decision_rows)
    write_csv(OUT_DIR / "task1177_proxy_backtest_metrics.csv", metrics)
    best = max(metrics, key=lambda row: float(row["final_equity"])) if metrics else {}
    decision = {
        "task_id": "Task1171-1180",
        "verdict": "diagnostic_public_filer_proxy_backtest_executed_not_accepted",
        "price_pool_symbols": len(pool),
        "price_downloaded_symbols": len(prices),
        "feature_rows": len(features),
        "selection_rows": len(all_selections),
        "trade_rows": len(all_trades),
        "best_variant": best.get("policy_variant_id", ""),
        "best_final_equity": best.get("final_equity", 0),
        "best_cagr": best.get("cagr", 0),
        "best_max_drawdown": best.get("max_drawdown", 0),
        "benchmark_symbol": benchmark.get("benchmark_symbol", BENCHMARK),
        "benchmark_final_equity": benchmark.get("benchmark_final_equity", 0),
        "benchmark_cagr": benchmark.get("benchmark_cagr", 0),
        "diagnostic_replay_executed": "1",
        "selection_promoted": "0",
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "next_action": "diagnose_public_filer_proxy_result_and_decide_true_exchange_listing_feed_or_policy_iteration",
        "authority": AUTHORITY,
    }
    write_csv(OUT_DIR / "task1180_public_filer_proxy_backtest_closeout.csv", [decision])
    write_json(OUT_DIR / "task1180_public_filer_proxy_backtest_closeout.json", decision)
    write_report(decision)
    print(
        "[TRADER_BRAIN_1171_1180_PUBLIC_FILER_PROXY_BACKTEST_OK] "
        f"prices={decision['price_downloaded_symbols']}/{decision['price_pool_symbols']} "
        f"features={decision['feature_rows']} "
        f"best={decision['best_variant']} "
        f"final={decision['best_final_equity']} "
        f"cagr={decision['best_cagr']} "
        f"mdd={decision['best_max_drawdown']} "
        f"qqq={decision['benchmark_final_equity']}"
    )


if __name__ == "__main__":
    main()
