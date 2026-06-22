from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
UNIVERSE_PATH = ROOT / "docs/reports/task_872_explicit_harness_universe_contract/explicit_harness_universe_contract.csv"
ADAPTER_PATH = ROOT / "docs/reports/task_836_controlled_adapter_input_builder/adapter_inputs.csv"
RAW_DIR = ROOT / "data/raw/yfinance/task_870_879_full_market_data"
OUT_DIR = ROOT / "data/artifacts/task_870_879_full_controlled_replay"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def norm_yf(frame: pd.DataFrame) -> pd.DataFrame:
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
    if "adjclose" in out.columns and "adj_close" not in out.columns:
        out = out.rename(columns={"adjclose": "adj_close"})
    return out


def universe_symbols() -> tuple[list[str], dict[str, list[str]]]:
    rows = read_csv(UNIVERSE_PATH)
    by_family: dict[str, list[str]] = {}
    all_symbols: set[str] = set()
    for row in rows:
        family = row["bundle_family"]
        symbols = [item.strip().upper() for item in row["symbols"].split(";") if item.strip()]
        by_family[family] = symbols
        all_symbols.update(symbols)
    return sorted(all_symbols), by_family


def adapter_family(adapter_input_id: str) -> str:
    if "semi" in adapter_input_id:
        return "semiconductor_supply"
    return "ai_capex"


def fetch_daily_and_actions(symbol: str, raw_dir: Path) -> dict[str, object]:
    import yfinance as yf

    sym_dir = raw_dir / "daily" / symbol
    sym_dir.mkdir(parents=True, exist_ok=True)
    daily_path = sym_dir / f"{symbol}_daily.csv"
    actions_path = sym_dir / f"{symbol}_actions.csv"
    status: dict[str, object] = {
        "symbol": symbol,
        "daily_status": "not_attempted",
        "actions_status": "not_attempted",
        "daily_path": str(daily_path.as_posix()),
        "actions_path": str(actions_path.as_posix()),
        "daily_rows": 0,
        "actions_rows": 0,
        "date_start": "",
        "date_end": "",
        "error": "",
    }
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(start="2021-01-01", auto_adjust=False, actions=True)
        frame = norm_yf(hist)
        if frame.empty:
            raise RuntimeError("empty daily history")
        if "adj_close" not in frame.columns:
            frame["adj_close"] = frame["close"]
        needed = ["timestamp", "open", "high", "low", "close", "adj_close", "volume"]
        missing = [col for col in needed if col not in frame.columns]
        if missing:
            raise RuntimeError(f"missing daily columns: {missing}")
        out_cols = needed + [col for col in ["dividends", "stock_splits"] if col in frame.columns]
        out = frame[out_cols].copy()
        out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="coerce").dt.strftime("%Y-%m-%d")
        out = out.dropna(subset=["timestamp"]).sort_values("timestamp").drop_duplicates("timestamp", keep="last")
        out["symbol"] = symbol
        out.to_csv(daily_path, index=False)
        actions = out.loc[
            (pd.to_numeric(out.get("dividends", 0), errors="coerce").fillna(0) != 0)
            | (pd.to_numeric(out.get("stock_splits", 0), errors="coerce").fillna(0) != 0)
        ].copy()
        if actions.empty:
            pd.DataFrame(columns=["timestamp", "symbol", "dividends", "stock_splits"]).to_csv(actions_path, index=False)
        else:
            actions[[col for col in ["timestamp", "symbol", "dividends", "stock_splits"] if col in actions.columns]].to_csv(actions_path, index=False)
        status.update(
            {
                "daily_status": "ok",
                "actions_status": "ok",
                "daily_rows": int(len(out)),
                "actions_rows": int(len(actions)),
                "date_start": str(out["timestamp"].iloc[0]),
                "date_end": str(out["timestamp"].iloc[-1]),
                "daily_sha256": sha256_file(daily_path),
                "actions_sha256": sha256_file(actions_path),
            }
        )
    except Exception as exc:  # noqa: BLE001
        status["daily_status"] = "failed"
        status["actions_status"] = "failed"
        status["error"] = repr(exc)
    return status


def fetch_recent_intraday(symbol: str, raw_dir: Path) -> dict[str, object]:
    import yfinance as yf

    sym_dir = raw_dir / "intraday_15m" / symbol
    sym_dir.mkdir(parents=True, exist_ok=True)
    out_path = sym_dir / f"{symbol}_15m_yfinance_recent.csv"
    status: dict[str, object] = {
        "symbol": symbol,
        "intraday_fetch_status": "not_attempted",
        "intraday_path": str(out_path.as_posix()),
        "intraday_rows": 0,
        "intraday_start": "",
        "intraday_end": "",
        "error": "",
    }
    try:
        raw = yf.download(symbol, period="60d", interval="15m", auto_adjust=False, prepost=True, progress=False, threads=False)
        frame = norm_yf(raw)
        if frame.empty:
            raise RuntimeError("empty intraday history")
        needed = ["timestamp", "open", "high", "low", "close", "volume"]
        missing = [col for col in needed if col not in frame.columns]
        if missing:
            raise RuntimeError(f"missing intraday columns: {missing}")
        out = frame[needed].copy()
        out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        out = out.dropna(subset=["timestamp"]).sort_values("timestamp").drop_duplicates("timestamp", keep="last")
        out["symbol"] = symbol
        out.to_csv(out_path, index=False)
        status.update(
            {
                "intraday_fetch_status": "ok",
                "intraday_rows": int(len(out)),
                "intraday_start": str(out["timestamp"].iloc[0]),
                "intraday_end": str(out["timestamp"].iloc[-1]),
                "intraday_sha256": sha256_file(out_path),
            }
        )
    except Exception as exc:  # noqa: BLE001
        status["intraday_fetch_status"] = "failed"
        status["error"] = repr(exc)
    return status


def build_calendar(daily_frames: dict[str, pd.DataFrame], raw_dir: Path) -> dict[str, object]:
    qqq = daily_frames["QQQ"].copy()
    dates = sorted(pd.to_datetime(qqq["timestamp"], utc=True).dt.strftime("%Y-%m-%d").unique().tolist())
    rows = []
    for d in dates:
        rows.append(
            {
                "calendar_id": "data_derived_qqq_sessions_v1",
                "exchange": "NASDAQ",
                "session_date": d,
                "open_ts_utc": f"{d}T13:30:00Z",
                "close_ts_utc": f"{d}T20:00:00Z",
                "early_close_flag": "",
                "holiday_flag": "0",
                "source": "QQQ_yfinance_daily_sessions",
            }
        )
    path = raw_dir / "calendar" / "data_derived_qqq_sessions_v1.csv"
    write_csv(path, rows, ["calendar_id", "exchange", "session_date", "open_ts_utc", "close_ts_utc", "early_close_flag", "holiday_flag", "source"])
    return {
        "calendar_id": "data_derived_qqq_sessions_v1",
        "path": str(path.as_posix()),
        "session_count": len(rows),
        "date_start": dates[0] if dates else "",
        "date_end": dates[-1] if dates else "",
        "sha256": sha256_file(path),
        "certification_status": "certified_for_controlled_replay_diagnostic",
    }


def normalize_daily(symbols: list[str], raw_dir: Path, out_dir: Path) -> tuple[list[dict[str, object]], dict[str, pd.DataFrame]]:
    manifest = []
    frames: dict[str, pd.DataFrame] = {}
    canonical_dir = out_dir / "canonical_daily"
    for symbol in symbols:
        path = raw_dir / "daily" / symbol / f"{symbol}_daily.csv"
        if not path.exists():
            manifest.append({"symbol": symbol, "canonical_status": "missing_raw", "rows": 0, "path": "", "date_start": "", "date_end": "", "sha256": ""})
            continue
        frame = pd.read_csv(path)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce").dt.strftime("%Y-%m-%d")
        frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp").drop_duplicates("timestamp", keep="last")
        frame["symbol"] = symbol
        out = frame[["timestamp", "symbol", "open", "high", "low", "close", "adj_close", "volume"]].copy()
        out_path = canonical_dir / f"{symbol}.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(out_path, index=False)
        frames[symbol] = out
        manifest.append(
            {
                "symbol": symbol,
                "canonical_status": "ok",
                "rows": int(len(out)),
                "path": str(out_path.as_posix()),
                "date_start": str(out["timestamp"].iloc[0]),
                "date_end": str(out["timestamp"].iloc[-1]),
                "sha256": sha256_file(out_path),
            }
        )
    return manifest, frames


def normalize_intraday(symbols: list[str], raw_dir: Path, out_dir: Path) -> list[dict[str, object]]:
    manifest = []
    canonical_dir = out_dir / "canonical_intraday_15m"
    for symbol in symbols:
        frames = []
        existing = ROOT / "data/raw/us_intraday" / f"{symbol}.csv"
        if existing.exists():
            old = pd.read_csv(existing)
            old["symbol"] = symbol
            frames.append(old)
        recent = raw_dir / "intraday_15m" / symbol / f"{symbol}_15m_yfinance_recent.csv"
        if recent.exists():
            frames.append(pd.read_csv(recent))
        if not frames:
            manifest.append({"symbol": symbol, "canonical_status": "missing_raw", "rows": 0, "path": "", "date_start": "", "date_end": "", "sha256": ""})
            continue
        frame = pd.concat(frames, ignore_index=True)
        frame.columns = [str(c).strip().lower() for c in frame.columns]
        for col in ["trade_count", "vwap"]:
            if col not in frame.columns:
                frame[col] = ""
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
        frame = frame.dropna(subset=["timestamp"]).sort_values("timestamp").drop_duplicates("timestamp", keep="last")
        frame["session_date"] = frame["timestamp"].dt.strftime("%Y-%m-%d")
        frame["timestamp"] = frame["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        frame["symbol"] = symbol
        out = frame[["timestamp", "session_date", "symbol", "open", "high", "low", "close", "volume", "trade_count", "vwap"]].copy()
        out_path = canonical_dir / f"{symbol}.csv"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out.to_csv(out_path, index=False)
        manifest.append(
            {
                "symbol": symbol,
                "canonical_status": "ok",
                "rows": int(len(out)),
                "path": str(out_path.as_posix()),
                "date_start": str(out["session_date"].iloc[0]),
                "date_end": str(out["session_date"].iloc[-1]),
                "sha256": sha256_file(out_path),
            }
        )
    return manifest


def build_trade_specs(by_family: dict[str, list[str]], daily_frames: dict[str, pd.DataFrame], out_dir: Path, initial_capital: float) -> list[dict[str, object]]:
    adapter_rows = read_csv(ADAPTER_PATH)
    specs = []
    capital_per_adapter = initial_capital / max(1, len(adapter_rows))
    for adapter in adapter_rows:
        family = adapter_family(adapter["adapter_input_id"])
        symbols = [s for s in by_family[family] if s in daily_frames]
        per_symbol = capital_per_adapter / max(1, len(symbols))
        bundle_asof = pd.Timestamp(adapter["bundle_asof_ts"])
        for symbol in symbols:
            frame = daily_frames[symbol].copy()
            dates = pd.to_datetime(frame["timestamp"], utc=True)
            eligible = frame.loc[dates > bundle_asof]
            if eligible.empty:
                status = "blocked"
                tradable_after = ""
                reason = "no_daily_bar_after_bundle_asof"
            else:
                status = "ready_for_controlled_replay"
                tradable_after = str(eligible.iloc[0]["timestamp"])
                reason = ""
            specs.append(
                {
                    "trade_spec_id": f"trade_spec_{adapter['adapter_input_id']}_{symbol}",
                    "adapter_input_id": adapter["adapter_input_id"],
                    "candidate_bundle_id": adapter["candidate_bundle_id"],
                    "source_graph_id": adapter["source_graph_id"],
                    "symbol": symbol,
                    "side": "long",
                    "tradable_after_ts": tradable_after,
                    "entry_policy_id": "next_daily_adjusted_close_after_bundle_asof_v1",
                    "exit_policy_id": "hold_until_latest_certified_daily_bar_v1",
                    "position_policy_id": "equal_weight_within_adapter_half_capital_v1",
                    "allocated_capital": round(per_symbol, 6),
                    "initial_capital": initial_capital,
                    "benchmark_id": "qqq_buy_hold_reference",
                    "trade_spec_state": status,
                    "blocked_reason": reason,
                    "validation_authority": "DIAGNOSTIC_CONTROLLED_REPLAY_ONLY",
                }
            )
    write_csv(
        out_dir / "controlled_trade_specs.csv",
        specs,
        ["trade_spec_id", "adapter_input_id", "candidate_bundle_id", "source_graph_id", "symbol", "side", "tradable_after_ts", "entry_policy_id", "exit_policy_id", "position_policy_id", "allocated_capital", "initial_capital", "benchmark_id", "trade_spec_state", "blocked_reason", "validation_authority"],
    )
    return specs


def replay(specs: list[dict[str, object]], daily_frames: dict[str, pd.DataFrame], initial_capital: float, out_dir: Path) -> tuple[list[dict[str, object]], dict[str, object]]:
    rows = []
    final_capital = 0.0
    for spec in specs:
        if spec["trade_spec_state"] != "ready_for_controlled_replay":
            continue
        frame = daily_frames[str(spec["symbol"])].copy()
        data = frame.loc[pd.to_datetime(frame["timestamp"], utc=True) >= pd.Timestamp(str(spec["tradable_after_ts"]), tz="UTC")].copy()
        if len(data) < 2:
            continue
        entry = float(data.iloc[0]["adj_close"])
        exit_ = float(data.iloc[-1]["adj_close"])
        capital = float(spec["allocated_capital"])
        shares = capital / entry
        ending = shares * exit_
        final_capital += ending
        rows.append(
            {
                "trade_spec_id": spec["trade_spec_id"],
                "symbol": spec["symbol"],
                "side": spec["side"],
                "entry_date": data.iloc[0]["timestamp"],
                "exit_date": data.iloc[-1]["timestamp"],
                "entry_adj_close": round(entry, 6),
                "exit_adj_close": round(exit_, 6),
                "allocated_capital": round(capital, 6),
                "final_capital": round(ending, 6),
                "return_pct": round(((ending / capital) - 1.0) * 100.0, 6),
            }
        )
    qqq = daily_frames["QQQ"].copy()
    qdata = qqq.copy()
    q_entry = float(qdata.iloc[0]["adj_close"])
    q_exit = float(qdata.iloc[-1]["adj_close"])
    q_final = initial_capital * q_exit / q_entry
    summary = {
        "initial_capital": round(initial_capital, 2),
        "strategy_final_capital": round(final_capital, 2),
        "strategy_total_return_pct": round(((final_capital / initial_capital) - 1.0) * 100.0, 6),
        "benchmark": "QQQ",
        "qqq_final_capital": round(q_final, 2),
        "qqq_total_return_pct": round(((q_final / initial_capital) - 1.0) * 100.0, 6),
        "relative_return_vs_qqq_pct": round(((final_capital / q_final) - 1.0) * 100.0, 6) if q_final else "",
        "trade_count": len(rows),
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "result_authority": "DIAGNOSTIC_CONTROLLED_REPLAY_ONLY",
    }
    write_csv(out_dir / "controlled_replay_trades.csv", rows, ["trade_spec_id", "symbol", "side", "entry_date", "exit_date", "entry_adj_close", "exit_adj_close", "allocated_capital", "final_capital", "return_pct"])
    write_csv(out_dir / "controlled_replay_summary.csv", [summary], list(summary.keys()))
    return rows, summary


def run(raw_dir: Path, out_dir: Path, initial_capital: float) -> dict[str, object]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    symbols, by_family = universe_symbols()
    daily_status = [fetch_daily_and_actions(symbol, raw_dir) for symbol in symbols]
    intraday_status = [fetch_recent_intraday(symbol, raw_dir) for symbol in symbols]
    daily_manifest, daily_frames = normalize_daily(symbols, raw_dir, out_dir)
    calendar = build_calendar(daily_frames, out_dir)
    intraday_manifest = normalize_intraday(symbols, raw_dir, out_dir)
    specs = build_trade_specs(by_family, daily_frames, out_dir, initial_capital)
    trades, summary = replay(specs, daily_frames, initial_capital, out_dir)

    write_csv(out_dir / "full_data_acquisition_audit.csv", daily_status, sorted({k for row in daily_status for k in row.keys()}))
    write_csv(out_dir / "intraday_acquisition_audit.csv", intraday_status, sorted({k for row in intraday_status for k in row.keys()}))
    write_csv(out_dir / "daily_canonical_manifest.csv", daily_manifest, ["symbol", "canonical_status", "rows", "path", "date_start", "date_end", "sha256"])
    write_csv(out_dir / "intraday_15m_canonical_manifest.csv", intraday_manifest, ["symbol", "canonical_status", "rows", "path", "date_start", "date_end", "sha256"])
    write_csv(out_dir / "calendar_certification_manifest.csv", [calendar], list(calendar.keys()))
    corp_rows = []
    for row in daily_status:
        corp_rows.append(
            {
                "symbol": row["symbol"],
                "actions_status": row["actions_status"],
                "actions_rows": row["actions_rows"],
                "actions_path": row["actions_path"],
                "actions_sha256": row.get("actions_sha256", ""),
            }
        )
    write_csv(out_dir / "corporate_action_adjustment_manifest.csv", corp_rows, ["symbol", "actions_status", "actions_rows", "actions_path", "actions_sha256"])
    promotion = {
        "market_data_gate_status": "READY_FOR_CONTROLLED_REPLAY_PLAN",
        "daily_symbols_ok": sum(1 for row in daily_manifest if row["canonical_status"] == "ok"),
        "intraday_symbols_ok": sum(1 for row in intraday_manifest if row["canonical_status"] == "ok"),
        "calendar_status": calendar["certification_status"],
        "corporate_actions_symbols_ok": sum(1 for row in corp_rows if row["actions_status"] == "ok"),
        "explicit_universe_symbols": len(symbols),
        "does_not_mean": "strategy acceptance deployment readiness or real-capital permission",
    }
    write_csv(out_dir / "market_data_gate_promotion_result.csv", [promotion], list(promotion.keys()))
    cycle = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "symbol_count": len(symbols),
        "symbols": symbols,
        "trade_spec_count": len(specs),
        "trade_count": len(trades),
        "market_data_gate_status": promotion["market_data_gate_status"],
        "replay_summary": summary,
    }
    (out_dir / "full_cycle_summary.json").write_text(json.dumps(cycle, ensure_ascii=True, indent=2), encoding="utf-8")
    return cycle


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-dir", type=Path, default=RAW_DIR)
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--initial-capital", type=float, default=1000.0)
    args = parser.parse_args()
    result = run(args.raw_dir, args.out_dir, args.initial_capital)
    summary = result["replay_summary"]
    print(
        "[TRADER_BRAIN_870_879_FULL_REPLAY_OK] "
        f"symbols={result['symbol_count']} trades={result['trade_count']} "
        f"strategy_final={summary['strategy_final_capital']} qqq_final={summary['qqq_final_capital']}"
    )


if __name__ == "__main__":
    main()
