from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.trader_brain_870_879_full_data_replay import (
    fetch_daily_and_actions,
    fetch_recent_intraday,
    normalize_daily,
    normalize_intraday,
    build_calendar,
    read_csv,
    sha256_file,
    write_csv,
)


UNIVERSE_PATH = ROOT / "data/raw/theme_universe_10x7.csv"
ADAPTER_PATH = ROOT / "docs/reports/task_836_controlled_adapter_input_builder/adapter_inputs.csv"
RAW_DIR = ROOT / "data/raw/yfinance/task_880_theme_universe_10x7"
OUT_DIR = ROOT / "data/artifacts/task_880_theme_universe_10x7_replay"


def read_theme_universe(path: Path) -> tuple[list[dict[str, str]], list[str]]:
    rows = read_csv(path)
    for row in rows:
        row["theme"] = row["theme"].strip()
        row["symbol"] = row["symbol"].strip().upper()
        row["role"] = row["role"].strip()
    symbols = sorted({row["symbol"] for row in rows})
    return rows, symbols


def universe_contract(rows: list[dict[str, str]], out_dir: Path) -> dict[str, object]:
    theme_counts = pd.DataFrame(rows).groupby("theme")["symbol"].count().to_dict()
    contract_rows = []
    for theme, count in sorted(theme_counts.items()):
        contract_rows.append(
            {
                "universe_id": "theme_universe_10x7_v1",
                "theme": theme,
                "symbol_count": int(count),
                "source_path": UNIVERSE_PATH.as_posix(),
                "universe_state": "explicit_theme_universe_for_diagnostic_replay",
                "does_not_mean": "point-in-time universe strategy acceptance deployment readiness or real-capital permission",
            }
        )
    write_csv(
        out_dir / "theme_universe_10x7_contract.csv",
        contract_rows,
        ["universe_id", "theme", "symbol_count", "source_path", "universe_state", "does_not_mean"],
    )
    return {
        "theme_count": len(theme_counts),
        "row_count": len(rows),
        "unique_symbol_count": len({row["symbol"] for row in rows}),
    }


def min_adapter_asof() -> str:
    adapter_rows = read_csv(ADAPTER_PATH)
    timestamps = [pd.Timestamp(row["bundle_asof_ts"]) for row in adapter_rows]
    return min(timestamps).isoformat()


def build_trade_specs(
    universe_rows: list[dict[str, str]],
    daily_frames: dict[str, pd.DataFrame],
    out_dir: Path,
    initial_capital: float,
) -> list[dict[str, object]]:
    source_adapter_ids = ";".join(row["adapter_input_id"] for row in read_csv(ADAPTER_PATH))
    source_bundle_ids = ";".join(row["candidate_bundle_id"] for row in read_csv(ADAPTER_PATH))
    asof = pd.Timestamp(min_adapter_asof())
    per_symbol = initial_capital / max(1, len(universe_rows))
    specs: list[dict[str, object]] = []
    for row in universe_rows:
        symbol = row["symbol"]
        frame = daily_frames.get(symbol)
        if frame is None:
            status = "blocked"
            tradable_after = ""
            reason = "missing_daily_frame"
        else:
            dates = pd.to_datetime(frame["timestamp"], utc=True)
            eligible = frame.loc[dates > asof]
            if eligible.empty:
                status = "blocked"
                tradable_after = ""
                reason = "no_daily_bar_after_theme_universe_asof"
            else:
                status = "ready_for_controlled_replay"
                tradable_after = str(eligible.iloc[0]["timestamp"])
                reason = ""
        specs.append(
            {
                "trade_spec_id": f"task880_theme_universe_10x7_{row['theme']}_{symbol}",
                "universe_id": "theme_universe_10x7_v1",
                "source_adapter_input_ids": source_adapter_ids,
                "source_candidate_bundle_ids": source_bundle_ids,
                "theme": row["theme"],
                "symbol": symbol,
                "role": row["role"],
                "side": "long",
                "theme_universe_asof_ts": asof.isoformat(),
                "tradable_after_ts": tradable_after,
                "entry_policy_id": "next_daily_adjusted_close_after_min_adapter_asof_v1",
                "exit_policy_id": "hold_until_latest_certified_daily_bar_v1",
                "position_policy_id": "equal_weight_10x7_theme_universe_v1",
                "allocated_capital": round(per_symbol, 8),
                "initial_capital": initial_capital,
                "benchmark_id": "qqq_buy_hold_reference_and_same_window",
                "trade_spec_state": status,
                "blocked_reason": reason,
                "validation_authority": "DIAGNOSTIC_THEME_UNIVERSE_REPLAY_ONLY",
            }
        )
    write_csv(
        out_dir / "controlled_trade_specs.csv",
        specs,
        [
            "trade_spec_id",
            "universe_id",
            "source_adapter_input_ids",
            "source_candidate_bundle_ids",
            "theme",
            "symbol",
            "role",
            "side",
            "theme_universe_asof_ts",
            "tradable_after_ts",
            "entry_policy_id",
            "exit_policy_id",
            "position_policy_id",
            "allocated_capital",
            "initial_capital",
            "benchmark_id",
            "trade_spec_state",
            "blocked_reason",
            "validation_authority",
        ],
    )
    return specs


def replay(
    specs: list[dict[str, object]],
    daily_frames: dict[str, pd.DataFrame],
    initial_capital: float,
    out_dir: Path,
) -> tuple[list[dict[str, object]], list[dict[str, object]], dict[str, object]]:
    trades: list[dict[str, object]] = []
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
        trades.append(
            {
                "trade_spec_id": spec["trade_spec_id"],
                "theme": spec["theme"],
                "symbol": spec["symbol"],
                "side": spec["side"],
                "entry_date": data.iloc[0]["timestamp"],
                "exit_date": data.iloc[-1]["timestamp"],
                "entry_adj_close": round(entry, 6),
                "exit_adj_close": round(exit_, 6),
                "allocated_capital": round(capital, 8),
                "final_capital": round(ending, 8),
                "return_pct": round(((ending / capital) - 1.0) * 100.0, 6),
            }
        )
    trade_frame = pd.DataFrame(trades)
    if trade_frame.empty:
        by_theme: list[dict[str, object]] = []
        final_capital = 0.0
    else:
        final_capital = float(trade_frame["final_capital"].sum())
        by_theme = []
        for theme, group in trade_frame.groupby("theme"):
            allocated = float(group["allocated_capital"].sum())
            final = float(group["final_capital"].sum())
            by_theme.append(
                {
                    "theme": theme,
                    "trade_count": int(len(group)),
                    "allocated_capital": round(allocated, 6),
                    "final_capital": round(final, 6),
                    "return_pct": round(((final / allocated) - 1.0) * 100.0, 6) if allocated else "",
                }
            )
    qqq = daily_frames["QQQ"].copy()
    asof = min(pd.Timestamp(str(spec["theme_universe_asof_ts"])) for spec in specs)
    q_same = qqq.loc[pd.to_datetime(qqq["timestamp"], utc=True) > asof].copy()
    q_same_entry = float(q_same.iloc[0]["adj_close"])
    q_same_exit = float(q_same.iloc[-1]["adj_close"])
    q_same_final = initial_capital * q_same_exit / q_same_entry
    q_long_entry = float(qqq.iloc[0]["adj_close"])
    q_long_exit = float(qqq.iloc[-1]["adj_close"])
    q_long_final = initial_capital * q_long_exit / q_long_entry
    summary = {
        "initial_capital": round(initial_capital, 2),
        "universe_id": "theme_universe_10x7_v1",
        "theme_count": len({str(spec["theme"]) for spec in specs}),
        "symbol_count": len({str(spec["symbol"]) for spec in specs}),
        "trade_count": len(trades),
        "theme_universe_final_capital": round(final_capital, 2),
        "theme_universe_total_return_pct": round(((final_capital / initial_capital) - 1.0) * 100.0, 6),
        "qqq_same_window_final_capital": round(q_same_final, 2),
        "qqq_same_window_total_return_pct": round(((q_same_final / initial_capital) - 1.0) * 100.0, 6),
        "qqq_long_term_final_capital": round(q_long_final, 2),
        "qqq_long_term_total_return_pct": round(((q_long_final / initial_capital) - 1.0) * 100.0, 6),
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "result_authority": "DIAGNOSTIC_THEME_UNIVERSE_REPLAY_ONLY",
    }
    write_csv(
        out_dir / "controlled_replay_trades.csv",
        trades,
        ["trade_spec_id", "theme", "symbol", "side", "entry_date", "exit_date", "entry_adj_close", "exit_adj_close", "allocated_capital", "final_capital", "return_pct"],
    )
    write_csv(out_dir / "controlled_replay_by_theme.csv", by_theme, ["theme", "trade_count", "allocated_capital", "final_capital", "return_pct"])
    write_csv(out_dir / "controlled_replay_summary.csv", [summary], list(summary.keys()))
    return trades, by_theme, summary


def run(raw_dir: Path, out_dir: Path, initial_capital: float) -> dict[str, object]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(parents=True, exist_ok=True)
    universe_rows, universe_symbols = read_theme_universe(UNIVERSE_PATH)
    symbols = sorted(set(universe_symbols) | {"QQQ"})
    contract = universe_contract(universe_rows, out_dir)
    daily_status = [fetch_daily_and_actions(symbol, raw_dir) for symbol in symbols]
    intraday_status = [fetch_recent_intraday(symbol, raw_dir) for symbol in symbols]
    daily_manifest, daily_frames = normalize_daily(symbols, raw_dir, out_dir)
    calendar = build_calendar(daily_frames, out_dir)
    intraday_manifest = normalize_intraday(symbols, raw_dir, out_dir)
    specs = build_trade_specs(universe_rows, daily_frames, out_dir, initial_capital)
    trades, by_theme, summary = replay(specs, daily_frames, initial_capital, out_dir)
    write_csv(out_dir / "full_data_acquisition_audit.csv", daily_status, sorted({k for row in daily_status for k in row.keys()}))
    write_csv(out_dir / "intraday_acquisition_audit.csv", intraday_status, sorted({k for row in intraday_status for k in row.keys()}))
    write_csv(out_dir / "daily_canonical_manifest.csv", daily_manifest, ["symbol", "canonical_status", "rows", "path", "date_start", "date_end", "sha256"])
    write_csv(out_dir / "intraday_15m_canonical_manifest.csv", intraday_manifest, ["symbol", "canonical_status", "rows", "path", "date_start", "date_end", "sha256"])
    write_csv(out_dir / "calendar_certification_manifest.csv", [calendar], list(calendar.keys()))
    corp_rows = [
        {
            "symbol": row["symbol"],
            "actions_status": row["actions_status"],
            "actions_rows": row["actions_rows"],
            "actions_path": row["actions_path"],
            "actions_sha256": row.get("actions_sha256", ""),
        }
        for row in daily_status
    ]
    write_csv(out_dir / "corporate_action_adjustment_manifest.csv", corp_rows, ["symbol", "actions_status", "actions_rows", "actions_path", "actions_sha256"])
    promotion = {
        "market_data_gate_status": "READY_FOR_THEME_UNIVERSE_CONTROLLED_REPLAY_PLAN",
        "theme_count": contract["theme_count"],
        "explicit_universe_rows": contract["row_count"],
        "explicit_universe_symbols": contract["unique_symbol_count"],
        "data_symbols_including_benchmark": len(symbols),
        "daily_symbols_ok": sum(1 for row in daily_manifest if row["canonical_status"] == "ok"),
        "intraday_symbols_ok": sum(1 for row in intraday_manifest if row["canonical_status"] == "ok"),
        "calendar_status": calendar["certification_status"],
        "corporate_actions_symbols_ok": sum(1 for row in corp_rows if row["actions_status"] == "ok"),
        "does_not_mean": "strategy acceptance deployment readiness or real-capital permission",
    }
    write_csv(out_dir / "market_data_gate_promotion_result.csv", [promotion], list(promotion.keys()))
    cycle = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "universe_id": "theme_universe_10x7_v1",
        "theme_count": contract["theme_count"],
        "row_count": contract["row_count"],
        "symbol_count": contract["unique_symbol_count"],
        "data_symbol_count_including_benchmark": len(symbols),
        "symbols": symbols,
        "trade_spec_count": len(specs),
        "trade_count": len(trades),
        "theme_result_count": len(by_theme),
        "market_data_gate_status": promotion["market_data_gate_status"],
        "universe_source_sha256": sha256_file(UNIVERSE_PATH),
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
        "[TRADER_BRAIN_880_THEME_10X7_REPLAY_OK] "
        f"themes={result['theme_count']} symbols={result['symbol_count']} trades={result['trade_count']} "
        f"theme_final={summary['theme_universe_final_capital']} qqq_same_window={summary['qqq_same_window_final_capital']} "
        f"qqq_long_term={summary['qqq_long_term_final_capital']}"
    )


if __name__ == "__main__":
    main()
