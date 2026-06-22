from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data/artifacts/task_860_869_backtest_cycle"
RAW_QQQ_DIR = ROOT / "data/raw/yfinance/task_860_qqq_benchmark"


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize_yfinance(frame: pd.DataFrame) -> pd.DataFrame:
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
    if "adj_close" not in out.columns and "adjclose" in out.columns:
        out = out.rename(columns={"adjclose": "adj_close"})
    return out


def fetch_qqq_benchmark(raw_dir: Path) -> dict[str, object]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    status = {
        "fetch_status": "not_attempted",
        "source_provider": "yfinance",
        "raw_daily_path": str((raw_dir / "QQQ_daily.csv").as_posix()),
        "raw_actions_path": str((raw_dir / "QQQ_actions.csv").as_posix()),
        "row_count": 0,
        "date_start": "",
        "date_end": "",
        "error": "",
    }
    try:
        import yfinance as yf

        ticker = yf.Ticker("QQQ")
        history = ticker.history(start="2021-01-01", auto_adjust=False, actions=True)
        frame = normalize_yfinance(history)
        if frame.empty:
            raise RuntimeError("empty QQQ history from yfinance")
        expected = ["timestamp", "open", "high", "low", "close", "volume"]
        missing = [col for col in expected if col not in frame.columns]
        if missing:
            raise RuntimeError(f"missing columns: {','.join(missing)}")
        if "adj_close" not in frame.columns:
            frame["adj_close"] = frame["close"]
        out = frame[[col for col in ["timestamp", "open", "high", "low", "close", "adj_close", "volume", "dividends", "stock_splits"] if col in frame.columns]].copy()
        out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True, errors="coerce").dt.strftime("%Y-%m-%d")
        out = out.dropna(subset=["timestamp"]).sort_values("timestamp").drop_duplicates(subset=["timestamp"], keep="last")
        out["symbol"] = "QQQ"
        daily_path = raw_dir / "QQQ_daily.csv"
        out.to_csv(daily_path, index=False)

        actions = out.loc[
            (pd.to_numeric(out.get("dividends", 0), errors="coerce").fillna(0) != 0)
            | (pd.to_numeric(out.get("stock_splits", 0), errors="coerce").fillna(0) != 0)
        ].copy()
        actions_path = raw_dir / "QQQ_actions.csv"
        if actions.empty:
            pd.DataFrame(columns=["timestamp", "symbol", "dividends", "stock_splits"]).to_csv(actions_path, index=False)
        else:
            actions[[col for col in ["timestamp", "symbol", "dividends", "stock_splits"] if col in actions.columns]].to_csv(actions_path, index=False)

        status.update(
            {
                "fetch_status": "ok",
                "row_count": int(len(out)),
                "date_start": str(out["timestamp"].iloc[0]),
                "date_end": str(out["timestamp"].iloc[-1]),
                "raw_daily_sha256": sha256_file(daily_path),
                "raw_actions_sha256": sha256_file(actions_path),
            }
        )
    except Exception as exc:  # noqa: BLE001
        status["fetch_status"] = "failed"
        status["error"] = repr(exc)
    return status


def load_qqq_frame(fetch_status: dict[str, object]) -> tuple[pd.DataFrame, str]:
    raw_path = Path(str(fetch_status.get("raw_daily_path", "")))
    if str(fetch_status.get("fetch_status")) == "ok" and raw_path.exists():
        return pd.read_csv(raw_path), "managed_yfinance_task860"
    fallback = ROOT / "data/raw/us_daily_breadth_top500/QQQ.csv"
    frame = pd.read_csv(fallback)
    frame["symbol"] = "QQQ"
    if "adj_close" not in frame.columns:
        frame["adj_close"] = frame["close"]
    return frame, "fallback_existing_us_daily_breadth_top500_reference_only"


def qqq_benchmark(frame: pd.DataFrame, *, initial_capital: float) -> dict[str, object]:
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    data = data.dropna(subset=["timestamp"]).sort_values("timestamp")
    price_col = "adj_close" if "adj_close" in data.columns else "close"
    data[price_col] = pd.to_numeric(data[price_col], errors="coerce")
    data = data.dropna(subset=[price_col])
    if len(data) < 2:
        raise RuntimeError("insufficient QQQ rows")
    entry_price = float(data.iloc[0][price_col])
    exit_price = float(data.iloc[-1][price_col])
    shares = float(initial_capital) / entry_price
    final_capital = shares * exit_price
    equity = data[price_col].astype(float) * shares
    run_max = equity.cummax()
    drawdown = ((equity - run_max) / run_max.replace(0, pd.NA)).fillna(0)
    returns = equity.pct_change().dropna()
    years = max(1.0 / 252.0, len(data) / 252.0)
    sharpe = 0.0
    if not returns.empty and float(returns.std(ddof=0)) > 0:
        sharpe = float((returns.mean() / returns.std(ddof=0)) * (252.0**0.5))
    return {
        "benchmark_id": "qqq_buy_hold_reference",
        "symbol": "QQQ",
        "initial_capital": round(float(initial_capital), 2),
        "benchmark_method": "fractional_buy_hold_adjusted_close_no_fee",
        "price_column": price_col,
        "entry_date": data.iloc[0]["timestamp"].strftime("%Y-%m-%d"),
        "exit_date": data.iloc[-1]["timestamp"].strftime("%Y-%m-%d"),
        "entry_price": round(entry_price, 6),
        "exit_price": round(exit_price, 6),
        "shares": round(shares, 10),
        "final_capital": round(final_capital, 2),
        "total_return_pct": round(((final_capital / float(initial_capital)) - 1.0) * 100.0, 6),
        "cagr_pct": round(((final_capital / float(initial_capital)) ** (1.0 / years) - 1.0) * 100.0, 6),
        "max_drawdown_pct": round(abs(float(drawdown.min()) * 100.0), 6),
        "sharpe": round(sharpe, 6),
        "row_count": int(len(data)),
        "validation_authority": "DATA_HEALTH_REFERENCE_ONLY",
        "does_not_mean": "strategy acceptance, controlled replay pass, deployment readiness, or real-capital permission",
    }


def attempt_rows(stage: str, adapter_rows: list[dict[str, str]], certification_decisions: list[dict[str, str]]) -> list[dict[str, object]]:
    market_gate = next((row for row in certification_decisions if row.get("decision_area") == "market_data_gate_handoff"), {})
    market_status = market_gate.get("status", "unknown")
    has_trade_spec = all(
        {"symbol", "side", "entry_policy", "exit_policy", "position_size"}.issubset(set(row.keys()))
        for row in adapter_rows
    )
    blockers = []
    if market_status != "ready_for_controlled_replay_plan":
        blockers.append(f"market_data_gate={market_status}")
    if not has_trade_spec:
        blockers.append("adapter_missing_symbol_side_entry_exit_position_size")
    if not adapter_rows:
        blockers.append("no_adapter_inputs")
    decision = "not_executed"
    if not blockers:
        decision = "ready_for_future_controlled_replay_plan"
    return [
        {
            "attempt_stage": stage,
            "initial_capital": 1000.0,
            "benchmark": "QQQ_buy_hold",
            "adapter_input_count": len(adapter_rows),
            "market_data_gate_status": market_status,
            "trade_spec_present": str(has_trade_spec).lower(),
            "strategy_replay_decision": decision,
            "blocked_reason": ";".join(blockers),
            "price_lookup_count": 0,
            "trade_row_count": 0,
            "pnl_metric_count": 0,
            "engine_call_count": 0,
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
    ]


def run(out_dir: Path, raw_dir: Path, initial_capital: float) -> dict[str, object]:
    out_dir.mkdir(parents=True, exist_ok=True)
    adapter_rows = read_csv(ROOT / "docs/reports/task_836_controlled_adapter_input_builder/adapter_inputs.csv")
    certification_decisions = read_csv(ROOT / "data/artifacts/task_850_859_data_certification/certification_decision.csv")
    fetch_status = fetch_qqq_benchmark(raw_dir)
    qqq_frame, qqq_source = load_qqq_frame(fetch_status)
    qqq = qqq_benchmark(qqq_frame, initial_capital=initial_capital)
    qqq["source_status"] = qqq_source
    qqq["source_fetch_status"] = fetch_status.get("fetch_status", "")

    attempt1 = attempt_rows("attempt1_before_managed_gap_acquisition", adapter_rows, certification_decisions)
    attempt2 = attempt_rows("attempt2_after_managed_gap_acquisition", adapter_rows, certification_decisions)

    post_attempt_gaps = [
        {
            "gap_id": "gap_adapter_trade_spec",
            "gap_type": "trade_contract",
            "required_before_strategy_backtest": "yes",
            "reason": "dry adapter inputs intentionally exclude symbol side entry_policy exit_policy and position_size",
            "managed_action": "create controlled trade-spec contract from candidate bundles without score/rank/leakage",
            "download_required": "no",
        },
        {
            "gap_id": "gap_market_data_certification",
            "gap_type": "data_certification",
            "required_before_strategy_backtest": "yes",
            "reason": "Task859 remains MARKET_DATA_CERTIFICATION_PARTIAL_NO_REPLAY",
            "managed_action": "complete calendar corporate actions PIT universe and intraday schema normalization gates",
            "download_required": "partial",
        },
    ]

    write_csv(
        out_dir / "controlled_replay_attempts.csv",
        attempt1 + attempt2,
        [
            "attempt_stage",
            "initial_capital",
            "benchmark",
            "adapter_input_count",
            "market_data_gate_status",
            "trade_spec_present",
            "strategy_replay_decision",
            "blocked_reason",
            "price_lookup_count",
            "trade_row_count",
            "pnl_metric_count",
            "engine_call_count",
            "strategy_acceptance",
            "deployment_readiness",
            "real_capital",
        ],
    )
    write_csv(
        out_dir / "qqq_benchmark_reference.csv",
        [qqq],
        [
            "benchmark_id",
            "symbol",
            "initial_capital",
            "benchmark_method",
            "price_column",
            "entry_date",
            "exit_date",
            "entry_price",
            "exit_price",
            "shares",
            "final_capital",
            "total_return_pct",
            "cagr_pct",
            "max_drawdown_pct",
            "sharpe",
            "row_count",
            "source_status",
            "source_fetch_status",
            "validation_authority",
            "does_not_mean",
        ],
    )
    write_csv(
        out_dir / "managed_acquisition_audit.csv",
        [fetch_status],
        sorted(fetch_status.keys()),
    )
    write_csv(
        out_dir / "post_attempt_gap_diagnosis.csv",
        post_attempt_gaps,
        ["gap_id", "gap_type", "required_before_strategy_backtest", "reason", "managed_action", "download_required"],
    )
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "initial_capital": initial_capital,
        "benchmark": "QQQ",
        "strategy_replay_decision": attempt2[0]["strategy_replay_decision"],
        "blocked_reason": attempt2[0]["blocked_reason"],
        "qqq_reference": qqq,
        "managed_acquisition": fetch_status,
        "no_strategy_backtest_executed": True,
        "qqq_reference_only_executed": True,
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
    }
    (out_dir / "cycle_summary.json").write_text(json.dumps(summary, ensure_ascii=True, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--raw-qqq-dir", type=Path, default=RAW_QQQ_DIR)
    parser.add_argument("--initial-capital", type=float, default=1000.0)
    args = parser.parse_args()
    summary = run(args.out_dir, args.raw_qqq_dir, args.initial_capital)
    print(
        "[TRADER_BRAIN_860_869_CYCLE_OK] "
        f"strategy_replay_decision={summary['strategy_replay_decision']} "
        f"qqq_final={summary['qqq_reference']['final_capital']}"
    )


if __name__ == "__main__":
    main()
