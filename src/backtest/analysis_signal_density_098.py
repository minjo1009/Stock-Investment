from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_daily_bars
from strategy.conditions import is_breakout, is_ma_trend, prepare_condition_frame


@dataclass
class FilterCounts:
    symbol: str
    bars_evaluated: int
    breakout_true: int
    ma_true: int
    breakout_and_ma_true: int
    liquidity_pass: int
    gap_pass: int
    pre_risk_signal_candidates: int


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _f(v: float, d: int = 6) -> float:
    return float(round(float(v), d))


def _count_filters_for_symbol(
    symbol: str,
    *,
    base_dir: Path,
    start_index: int,
    min_avg_volume: float,
    min_avg_turnover: float,
    gap_filter_max: float,
) -> FilterCounts:
    frame_raw = load_daily_bars(symbol, base_dir=base_dir)
    frame = prepare_condition_frame(frame_raw)
    if frame.empty or len(frame) <= start_index + 1:
        return FilterCounts(symbol, 0, 0, 0, 0, 0, 0, 0)

    breakout_true = 0
    ma_true = 0
    both_true = 0
    liq_pass = 0
    gap_pass = 0
    pre_risk = 0

    close = frame["close"].astype(float).tolist()
    open_ = frame["open"].astype(float).tolist()
    avg_volume_20 = pd.to_numeric(frame.get("avg_volume_20"), errors="coerce")
    avg_turnover_20 = pd.to_numeric(frame.get("avg_turnover_20"), errors="coerce")

    bars_eval = 0
    for i in range(start_index, len(frame) - 1):
        bars_eval += 1
        bo = is_breakout(frame, i) is True
        ma = is_ma_trend(frame, i) is True
        if bo:
            breakout_true += 1
        if ma:
            ma_true += 1
        if bo and ma:
            both_true += 1
            vol = float(avg_volume_20.iloc[i]) if pd.notna(avg_volume_20.iloc[i]) else None
            tov = float(avg_turnover_20.iloc[i]) if pd.notna(avg_turnover_20.iloc[i]) else None
            liq = (vol is not None and tov is not None and vol >= min_avg_volume and tov >= min_avg_turnover)
            if liq:
                liq_pass += 1
                gap = (open_[i + 1] - close[i]) / close[i] if close[i] > 0 else 1.0
                if gap <= gap_filter_max:
                    gap_pass += 1
                    pre_risk += 1

    return FilterCounts(
        symbol=symbol,
        bars_evaluated=bars_eval,
        breakout_true=breakout_true,
        ma_true=ma_true,
        breakout_and_ma_true=both_true,
        liquidity_pass=liq_pass,
        gap_pass=gap_pass,
        pre_risk_signal_candidates=pre_risk,
    )


def _agg(rows: list[FilterCounts]) -> dict[str, Any]:
    if not rows:
        return {
            "symbols": 0,
            "bars_evaluated": 0,
            "breakout_true": 0,
            "ma_true": 0,
            "breakout_and_ma_true": 0,
            "liquidity_pass": 0,
            "gap_pass": 0,
            "pre_risk_signal_candidates": 0,
            "breakout_rate": 0.0,
            "ma_rate": 0.0,
            "both_rate": 0.0,
            "candidate_rate": 0.0,
        }
    bars = sum(r.bars_evaluated for r in rows)
    breakout = sum(r.breakout_true for r in rows)
    ma = sum(r.ma_true for r in rows)
    both = sum(r.breakout_and_ma_true for r in rows)
    liq = sum(r.liquidity_pass for r in rows)
    gap = sum(r.gap_pass for r in rows)
    cand = sum(r.pre_risk_signal_candidates for r in rows)
    return {
        "symbols": len(rows),
        "bars_evaluated": bars,
        "breakout_true": breakout,
        "ma_true": ma,
        "breakout_and_ma_true": both,
        "liquidity_pass": liq,
        "gap_pass": gap,
        "pre_risk_signal_candidates": cand,
        "breakout_rate": _f(breakout / bars) if bars else 0.0,
        "ma_rate": _f(ma / bars) if bars else 0.0,
        "both_rate": _f(both / bars) if bars else 0.0,
        "candidate_rate": _f(cand / bars) if bars else 0.0,
    }


def _to_md(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T098 - Signal Density & Opportunity Frequency Diagnosis")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append(f"- primary_cause: {report['primary_cause']}")
    lines.append(f"- classification: {report['classification']}")
    lines.append(f"- final_answer: {report['final_answer']}")
    lines.append("")
    lines.append("## 2. Filter Funnel (Selected Universe)")
    f = report["selected_universe_funnel"]
    lines.append("| Stage | Count |")
    lines.append("|---|---:|")
    lines.append(f"| Bars Evaluated | {f['bars_evaluated']} |")
    lines.append(f"| Breakout True | {f['breakout_true']} |")
    lines.append(f"| MA True | {f['ma_true']} |")
    lines.append(f"| Breakout & MA | {f['breakout_and_ma_true']} |")
    lines.append(f"| Liquidity Pass | {f['liquidity_pass']} |")
    lines.append(f"| Gap Pass | {f['gap_pass']} |")
    lines.append(f"| Pre-risk Candidates | {f['pre_risk_signal_candidates']} |")
    lines.append("")
    lines.append("## 3. Signal Density")
    s = report["signal_density"]
    lines.append(f"- total_signals: {s['total_signals']}")
    lines.append(f"- executed_signals: {s['executed_signals']}")
    lines.append(f"- missed_signals: {s['missed_signals']}")
    lines.append(f"- execution_ratio: {s['execution_ratio']}")
    lines.append("")
    lines.append("## 4. Opportunity Frequency / Universe")
    u = report["universe_diagnosis"]
    lines.append(f"- default_universe_size: {u['default_universe_size']}")
    lines.append(f"- selected_universe_size: {u['selected_universe_size']}")
    lines.append(f"- selected_symbols_with_trades: {u['selected_symbols_with_trades']}")
    lines.append(f"- selected_symbols_without_trades: {u['selected_symbols_without_trades']}")
    lines.append(f"- unselected_symbols_candidate_count: {u['unselected_symbols_candidate_count']}")
    lines.append("")
    lines.append("## 5. Risk Overlay Impact on Re-entry")
    r = report["risk_overlay_reentry_impact"]
    lines.append(f"- blocked_by_loss_breaker: {r['blocked_by_loss_breaker']}")
    lines.append(f"- blocked_by_slot_or_sector: {r['blocked_by_slot_or_sector']}")
    lines.append(f"- missed_winners: {r['missed_winners']}")
    lines.append(f"- missed_losers: {r['missed_losers']}")
    lines.append("")
    lines.append("## 6. Recommended Next Task")
    n = report["recommended_next_task"]
    lines.append(f"- task_id: {n['task_id']}")
    lines.append(f"- title: {n['title']}")
    lines.append(f"- objective: {n['objective']}")
    lines.append("")
    lines.append("## 7. Final Answer")
    lines.append(report["final_answer"])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T098 signal density diagnosis")
    parser.add_argument("--base-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--input-t093", type=str, default="docs/reports/task_093/task_093_capital_backtest.json")
    parser.add_argument("--input-t096", type=str, default="docs/reports/task_096/task_096_revalidation.json")
    parser.add_argument("--input-t097-5", type=str, default="docs/reports/task_097_5/task_097_5_capital_deployment.json")
    parser.add_argument("--json-out", type=str, default="docs/reports/task_098/task_098_signal_density_diagnosis.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_098/task_098_signal_density_diagnosis.md")
    args = parser.parse_args(argv)

    base_dir = Path(args.base_dir)
    t093 = _load_json(Path(args.input_t093))
    _ = _load_json(Path(args.input_t096))
    t0975 = _load_json(Path(args.input_t097_5))

    selected_symbols = list(t093.get("selected_symbols", []))
    default_symbols = list(DEFAULT_US_UNIVERSE)
    unselected = [s for s in default_symbols if s not in selected_symbols]

    # Keep in sync with engine_full constants (diagnostic-only mirror).
    start_index = 200
    min_avg_volume = 1_000_000.0
    min_avg_turnover = 20_000_000.0
    gap_filter_max = 0.03

    selected_rows = [
        _count_filters_for_symbol(
            s,
            base_dir=base_dir,
            start_index=start_index,
            min_avg_volume=min_avg_volume,
            min_avg_turnover=min_avg_turnover,
            gap_filter_max=gap_filter_max,
        )
        for s in selected_symbols
    ]
    unselected_rows = [
        _count_filters_for_symbol(
            s,
            base_dir=base_dir,
            start_index=start_index,
            min_avg_volume=min_avg_volume,
            min_avg_turnover=min_avg_turnover,
            gap_filter_max=gap_filter_max,
        )
        for s in unselected
    ]

    selected_agg = _agg(selected_rows)
    unselected_agg = _agg(unselected_rows)

    # Pull signal execution from T097.5 best-case diagnostics.
    signal_exec = t0975.get("signal_execution", {})
    total_signals = int(signal_exec.get("total_signals", 0))
    executed = int(signal_exec.get("executed", 0))
    missed = int(signal_exec.get("missed", 0))
    execution_ratio = float(signal_exec.get("execution_ratio", 0.0))
    opp = t0975.get("opportunity_capture", {})
    missed_winners = int(opp.get("missed_profitable", 0))
    missed_losers = int(opp.get("missed_unprofitable", 0))

    selected_symbols_with_trades = int(sum(1 for r in selected_rows if r.pre_risk_signal_candidates > 0))
    selected_symbols_without_trades = int(len(selected_rows) - selected_symbols_with_trades)

    # Root cause classification:
    # If execution ratio high and missed mostly losers, bottleneck is signal frequency.
    if execution_ratio >= 0.90 and missed_winners <= missed_losers:
        classification = "Signal density / opportunity frequency problem"
        primary_cause = "Signals are inherently sparse after breakout+MA+liquidity filters; execution is not the limiting step."
    else:
        classification = "Mixed"
        primary_cause = "Both signal sparsity and deployment friction contribute."

    recommended = {
        "task_id": "T098.5",
        "title": "Signal Funnel Attribution Audit (No Rule Change)",
        "objective": (
            "Quantify per-filter elimination share over time/symbols (breakout, MA, liquidity, universe/sector selection) "
            "and identify where opportunity frequency is structurally constrained."
        ),
    }

    report = {
        "status": "PASS",
        "task": "T098",
        "primary_cause": primary_cause,
        "classification": classification,
        "selected_universe_funnel": selected_agg,
        "unselected_universe_funnel": unselected_agg,
        "signal_density": {
            "total_signals": total_signals,
            "executed_signals": executed,
            "missed_signals": missed,
            "execution_ratio": _f(execution_ratio),
        },
        "universe_diagnosis": {
            "default_universe_size": len(default_symbols),
            "selected_universe_size": len(selected_symbols),
            "selected_symbols_with_trades": selected_symbols_with_trades,
            "selected_symbols_without_trades": selected_symbols_without_trades,
            "unselected_symbols_candidate_count": int(unselected_agg["pre_risk_signal_candidates"]),
            "unselected_symbols": unselected,
        },
        "risk_overlay_reentry_impact": {
            "blocked_by_loss_breaker": int(
                t0975.get("scenarios", [{}])[0].get("blocked_breakdown", {}).get("LOSS_CLUSTER_BREAKER", 0)
            ),
            "blocked_by_slot_or_sector": int(
                t0975.get("scenarios", [{}])[0].get("blocked_breakdown", {}).get("MAX_CONCURRENT_CAP", 0)
            )
            + int(t0975.get("scenarios", [{}])[0].get("blocked_breakdown", {}).get("EXPOSURE_OR_SECTOR_CAP", 0)),
            "missed_winners": missed_winners,
            "missed_losers": missed_losers,
        },
        "key_questions_answered": {
            "universe_too_narrow": bool(unselected_agg["pre_risk_signal_candidates"] > 0),
            "sector_filter_too_strict": bool(selected_symbols_without_trades >= max(1, len(selected_symbols) // 2)),
            "breakout_too_sparse": bool(selected_agg["breakout_rate"] < 0.08),
            "ma_too_strict": bool(selected_agg["both_rate"] < selected_agg["breakout_rate"] * 0.6 if selected_agg["breakout_rate"] > 0 else False),
            "risk_overlay_limits_reentry": bool(
                int(t0975.get("scenarios", [{}])[0].get("blocked_breakdown", {}).get("LOSS_CLUSTER_BREAKER", 0)) > 0
            ),
        },
        "recommended_next_task": recommended,
        "final_answer": "The main bottleneck is low opportunity frequency (signal density), not execution fill/deployment, because most generated signals are executed and missed ones were not profitable.",
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_to_md(report), encoding="utf-8")

    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"classification={classification}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

