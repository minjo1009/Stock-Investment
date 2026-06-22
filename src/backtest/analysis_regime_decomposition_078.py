from __future__ import annotations

import argparse
import json
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pandas as pd

import backtest.engine_full as engine_full
import risk.policies as risk_policies
from backtest.analysis_stop_loss_structure import _trade_rows
from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_daily_bars
from backtest.engine_full import FullTradeResult, run_full_backtest_universe_with_stats
from backtest.entry_gates import EntryGateConfig, prepare_entry_gate_frame
from strategy.conditions import prepare_condition_frame


BASELINE_RISK_POLICY = "TIME_STOP_ONLY_066B"
S4_FEE = 0.0025
S4_SLIP = 0.0010


def _gate_config_from_name(name: str) -> EntryGateConfig:
    mapping = {
        "A_BASELINE": EntryGateConfig.disabled(),
        "B_KER_ONLY": EntryGateConfig(use_ker_gate=True),
        "C_VOLUME_ONLY": EntryGateConfig(use_volume_gate=True),
        "D_DAILY_BIAS_ONLY": EntryGateConfig(use_daily_bias_gate=True),
        "E_KER_VOLUME": EntryGateConfig(use_ker_gate=True, use_volume_gate=True),
        "F_KER_DAILY_BIAS": EntryGateConfig(use_ker_gate=True, use_daily_bias_gate=True),
        "G_VOLUME_DAILY_BIAS": EntryGateConfig(use_volume_gate=True, use_daily_bias_gate=True),
        "H_KER_VOLUME_DAILY_BIAS": EntryGateConfig(use_ker_gate=True, use_volume_gate=True, use_daily_bias_gate=True),
    }
    return mapping.get(name, EntryGateConfig.disabled())


@contextmanager
def patched_time_stop_only_policy() -> Any:
    old_mfe_trigger = risk_policies.RISK_MFE_TRIGGER
    old_giveback = risk_policies.RISK_GIVEBACK_FRACTION
    old_time_bars = risk_policies.RISK_TIME_STOP_BARS
    old_profit_buffer = risk_policies.RISK_TIME_STOP_MIN_RETURN
    old_engine_mfe_trigger = engine_full.RISK_MFE_TRIGGER
    had_policy = BASELINE_RISK_POLICY in risk_policies.RISK_POLICIES
    old_policy = risk_policies.RISK_POLICIES.get(BASELINE_RISK_POLICY)
    try:
        risk_policies.RISK_MFE_TRIGGER = 0.03
        risk_policies.RISK_GIVEBACK_FRACTION = 0.50
        risk_policies.RISK_TIME_STOP_BARS = 10
        risk_policies.RISK_TIME_STOP_MIN_RETURN = 0.0
        engine_full.RISK_MFE_TRIGGER = 0.03
        risk_policies.RISK_POLICIES[BASELINE_RISK_POLICY] = {"break_even": False, "giveback": False, "time_stop": True}
        yield
    finally:
        risk_policies.RISK_MFE_TRIGGER = old_mfe_trigger
        risk_policies.RISK_GIVEBACK_FRACTION = old_giveback
        risk_policies.RISK_TIME_STOP_BARS = old_time_bars
        risk_policies.RISK_TIME_STOP_MIN_RETURN = old_profit_buffer
        engine_full.RISK_MFE_TRIGGER = old_engine_mfe_trigger
        if had_policy:
            risk_policies.RISK_POLICIES[BASELINE_RISK_POLICY] = old_policy if old_policy is not None else {}
        else:
            risk_policies.RISK_POLICIES.pop(BASELINE_RISK_POLICY, None)


def _build_frames(symbols: list[str], base_dir: Path, gate_cfg: EntryGateConfig) -> dict[str, pd.DataFrame]:
    out: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        raw = load_daily_bars(symbol, base_dir=base_dir)
        frame = prepare_condition_frame(raw)
        frame = prepare_entry_gate_frame(frame, gate_cfg)
        out[symbol] = frame
    return out


def _ker_regime(frame: pd.DataFrame, idx: int, cfg: EntryGateConfig) -> str:
    if "ker" not in frame.columns or idx < 0 or idx >= len(frame):
        return "UNKNOWN"
    value = frame.iloc[idx]["ker"]
    if pd.isna(value):
        return "UNKNOWN"
    ker = float(value)
    if ker > cfg.ker_trend_threshold:
        return "TREND"
    if ker < cfg.ker_mean_rev_threshold:
        return "SIDEWAYS"
    return "MIXED"


def _classify_trade_regime(results: list[FullTradeResult], frames: dict[str, pd.DataFrame], cfg: EntryGateConfig) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for item in results:
        trade = item.trade
        meta = dict(item.metadata or {})
        symbol = str(trade.symbol)
        signal_idx = meta.get("signal_bar_index")
        frame = frames.get(symbol)
        gate_regime = "UNKNOWN"
        if isinstance(signal_idx, int) and frame is not None:
            gate_regime = _ker_regime(frame, signal_idx, cfg)
        rows.append(
            {
                "trade_id": trade.trade_id,
                "symbol": symbol,
                "net_pnl": float(item.net_pnl),
                "regime_gate": gate_regime,
                "engine_regime": str(item.regime),
                "exit_rule": str(meta.get("exit_rule", "UNKNOWN")),
                "stop_hit_flag": bool(meta.get("stop_hit_flag") is True),
            }
        )
    return pd.DataFrame(rows)


def _drawdown_top3(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    work = frame.copy().reset_index(drop=True)
    work["equity"] = work["net_pnl"].cumsum()
    work["peak"] = work["equity"].cummax()
    work["drawdown"] = work["peak"] - work["equity"]
    top = work.sort_values("drawdown", ascending=False).head(3)
    out: list[dict[str, Any]] = []
    for row in top.itertuples(index=False):
        out.append({"drawdown": float(row.drawdown), "equity": float(row.equity), "peak": float(row.peak)})
    return out


def _to_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task 078 - Regime Decomposition Report")
    lines.append("")
    lines.append(f"- policy lock: `{payload['policy_lock']}`")
    lines.append(f"- scenario: `{payload['scenario']}`")
    lines.append("")
    lines.append("## Regime Performance")
    lines.append("| Regime | Trades | NetPnL | WinRate | PF |")
    lines.append("|---|---:|---:|---:|---:|")
    for row in payload["regime_breakdown"]:
        lines.append(
            f"| {row['regime_gate']} | {row['trades']} | {row['net_pnl']:.2f} | {row['win_rate']:.2f}% | {row['profit_factor']:.4f} |"
        )
    lines.append("")
    lines.append("## Symbol Contribution")
    lines.append("| Symbol | NetPnL | Trades | StopRate |")
    lines.append("|---|---:|---:|---:|")
    for row in payload["symbol_contribution"]:
        lines.append(f"| {row['symbol']} | {row['net_pnl']:.2f} | {row['trades']} | {row['stop_rate_pct']:.2f}% |")
    lines.append("")
    lines.append("## Drawdown Top 3")
    for idx, row in enumerate(payload["drawdown_top3"], start=1):
        lines.append(f"- #{idx}: drawdown={row['drawdown']:.2f}, equity={row['equity']:.2f}, peak={row['peak']:.2f}")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Task 078: Regime decomposition using gate-locked policy")
    parser.add_argument("--task077-json", type=str, default="docs/reports/task_077/task_077_gate_revalidation.json")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--initial-equity", type=float, default=100_000.0)
    parser.add_argument("--json-out", type=str, default="docs/reports/task_078/task_078_regime_decomposition.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_078/task_078_regime_decomposition.md")
    args = parser.parse_args()

    task077 = json.loads(Path(args.task077_json).read_text(encoding="utf-8"))
    policy_lock = str(task077.get("policy_lock", "A_BASELINE"))
    gate_cfg = _gate_config_from_name(policy_lock)
    symbols = sorted({str(sym).strip().upper() for sym in args.symbols if str(sym).strip()})
    base_dir = Path(args.data_dir)

    with patched_time_stop_only_policy():
        results, _stats = run_full_backtest_universe_with_stats(
            symbols=symbols,
            base_dir=base_dir,
            initial_equity=args.initial_equity,
            fee_rate=S4_FEE,
            slippage_rate=S4_SLIP,
            entry_policy="LIMITED_CHASE",
            risk_policy=BASELINE_RISK_POLICY,
            entry_gate_config=gate_cfg,
        )

    frames = _build_frames(symbols, base_dir, gate_cfg)
    trades = _classify_trade_regime(results, frames, gate_cfg)
    if trades.empty:
        payload = {
            "policy_lock": policy_lock,
            "scenario": "S4_KIS_REALISTIC",
            "regime_breakdown": [],
            "symbol_contribution": [],
            "drawdown_top3": [],
        }
    else:
        trades["win"] = trades["net_pnl"] > 0
        grouped = trades.groupby("regime_gate", as_index=False).agg(
            trades=("trade_id", "count"),
            net_pnl=("net_pnl", "sum"),
            wins=("win", "sum"),
            gross_win=("net_pnl", lambda s: float(s[s > 0].sum())),
            gross_loss=("net_pnl", lambda s: float(-s[s < 0].sum())),
        )
        grouped["win_rate"] = grouped["wins"] / grouped["trades"] * 100.0
        grouped["profit_factor"] = grouped.apply(
            lambda r: (float(r["gross_win"]) / float(r["gross_loss"])) if float(r["gross_loss"]) > 0 else float("inf"),
            axis=1,
        )
        regime_breakdown = grouped[["regime_gate", "trades", "net_pnl", "win_rate", "profit_factor"]].sort_values(
            "net_pnl",
            ascending=False,
        ).to_dict(orient="records")

        sym = trades.groupby("symbol", as_index=False).agg(
            net_pnl=("net_pnl", "sum"),
            trades=("trade_id", "count"),
            stop_count=("stop_hit_flag", "sum"),
        )
        sym["stop_rate_pct"] = sym["stop_count"] / sym["trades"] * 100.0
        symbol_contribution = sym.sort_values("net_pnl", ascending=False).to_dict(orient="records")
        drawdown_top3 = _drawdown_top3(trades[["net_pnl"]])

        payload = {
            "policy_lock": policy_lock,
            "scenario": "S4_KIS_REALISTIC",
            "regime_breakdown": regime_breakdown,
            "symbol_contribution": symbol_contribution,
            "drawdown_top3": drawdown_top3,
        }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_to_markdown(payload), encoding="utf-8")
    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"policy_lock={payload['policy_lock']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
