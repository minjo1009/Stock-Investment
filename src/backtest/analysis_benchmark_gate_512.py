from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.analysis_regime_rebuild_511 import (
    INITIAL_CAPITAL,
    _load_frames,
    _simulate,
)
from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE


ALL_MODES = {"compare_bench"}
ALL_CANDIDATES = {"momentum_only_hybrid", "trend_strength_weighted", "time_stop_profiled"}
ALL_BENCHMARKS = {"QLD", "TQQQ"}


def _extract_summary(sim_result: dict[str, Any]) -> dict[str, Any]:
    s = sim_result["summary"]
    return {
        "initial_capital": float(s["initial_capital"]),
        "final_capital": float(s["final_capital"]),
        "total_return_pct": float(s["total_return_pct"]),
        "cagr_pct": float(s["cagr_pct"]),
        "mdd_pct": float(s["mdd_pct"]),
        "worst_year_pct": float(s["worst_year_pct"]),
        "tuw_months": int(s["tuw_months"]),
        "sharpe": float(s["sharpe"]),
        "trade_count": int(s["trade_count"]),
    }


def _buy_hold_summary(frames: dict[str, pd.DataFrame], symbol: str) -> dict[str, Any]:
    frame = frames.get(symbol)
    if frame is None or len(frame) < 2:
        raise ValueError(f"insufficient bars for benchmark: {symbol}")
    entry_px = float(frame.iloc[1]["open"]) * 1.001
    exit_px = float(frame.iloc[-1]["close"]) * 0.999
    if entry_px <= 0:
        raise ValueError(f"invalid entry price for benchmark: {symbol}")
    shares = int(INITIAL_CAPITAL // entry_px)
    if shares <= 0:
        raise ValueError(f"benchmark {symbol} cannot buy >=1 share with initial capital")
    entry_cost = entry_px * shares
    entry_fee = entry_cost * 0.001
    cash = INITIAL_CAPITAL - entry_cost - entry_fee
    proceeds = exit_px * shares
    exit_fee = proceeds * 0.001
    final_capital = cash + proceeds - exit_fee
    total_return_pct = ((final_capital / INITIAL_CAPITAL) - 1.0) * 100.0
    years = max(1.0 / 252.0, len(frame) / 252.0)
    cagr = ((final_capital / INITIAL_CAPITAL) ** (1.0 / years) - 1.0) * 100.0 if final_capital > 0 else -100.0
    equity = (frame["close"].astype(float) * shares + cash).astype(float)
    run_max = equity.cummax()
    dd = ((equity - run_max) / run_max.replace(0.0, pd.NA)).fillna(0.0)
    mdd_pct = abs(float(dd.min()) * 100.0)
    daily_ret = equity.pct_change().dropna()
    sharpe = 0.0
    if not daily_ret.empty and float(daily_ret.std(ddof=0)) > 0:
        sharpe = float((daily_ret.mean() / daily_ret.std(ddof=0)) * (252.0 ** 0.5))
    years_idx = pd.to_datetime(frame.index).year
    yr = pd.DataFrame({"year": years_idx, "ret": daily_ret.reindex(frame.index).fillna(0.0).values})
    by_year = (1.0 + yr.groupby("year", as_index=False)["ret"].sum()["ret"]) - 1.0
    worst_year = float(by_year.min() * 100.0) if not by_year.empty else 0.0
    underwater = equity < run_max
    tuw_months = int((underwater.astype(int).sum() / 21.0))
    return {
        "initial_capital": float(INITIAL_CAPITAL),
        "final_capital": float(round(final_capital, 2)),
        "total_return_pct": float(round(total_return_pct, 6)),
        "cagr_pct": float(round(cagr, 6)),
        "mdd_pct": float(round(mdd_pct, 6)),
        "worst_year_pct": float(round(worst_year, 6)),
        "tuw_months": int(tuw_months),
        "sharpe": float(round(sharpe, 6)),
        "trade_count": int(1 if shares > 0 else 0),
    }


def _candidate_mode_to_sim(candidate_mode: str) -> tuple[str, str]:
    if candidate_mode == "momentum_only_hybrid":
        return "regime_switch_v2", "on"
    if candidate_mode == "trend_strength_weighted":
        return "regime_switch_v2", "off"
    if candidate_mode == "time_stop_profiled":
        return "regime_switch_v1", "off"
    raise ValueError(f"unsupported candidate_mode: {candidate_mode}")


def build_benchmark_comparison(candidate_summary: dict[str, Any], qld_summary: dict[str, Any], tqqq_summary: dict[str, Any], mdd_limit_pct: float = 60.0) -> dict[str, Any]:
    qld_final = float(qld_summary["final_capital"])
    tqqq_final = float(tqqq_summary["final_capital"])
    cand_final = float(candidate_summary["final_capital"])
    best_bench = max(qld_final, tqqq_final)
    rel_qld = ((cand_final / qld_final) - 1.0) * 100.0 if qld_final else 0.0
    rel_tqqq = ((cand_final / tqqq_final) - 1.0) * 100.0 if tqqq_final else 0.0
    win_qld = cand_final > qld_final
    win_tqqq = cand_final > tqqq_final
    win_both = bool(win_qld and win_tqqq)
    mdd_ok = float(candidate_summary["mdd_pct"]) <= float(mdd_limit_pct)
    gate_pass = bool(win_both and mdd_ok)
    elimination_reason = ""
    if not gate_pass:
        if not win_both:
            elimination_reason = "benchmark_underperformance"
        elif not mdd_ok:
            elimination_reason = "mdd_limit_breach"
        else:
            elimination_reason = "gate_failed"
    return {
        "relative_return_vs_qld": float(round(rel_qld, 6)),
        "relative_return_vs_tqqq": float(round(rel_tqqq, 6)),
        "win_vs_qld": bool(win_qld),
        "win_vs_tqqq": bool(win_tqqq),
        "win_both_benchmarks": bool(win_both),
        "mdd_limit_pct": float(mdd_limit_pct),
        "mdd_pass": bool(mdd_ok),
        "gate_pass": bool(gate_pass),
        "best_benchmark_final_capital": float(best_bench),
        "elimination_reason": elimination_reason,
    }


def _md(report: dict[str, Any]) -> str:
    c = report["candidate"]["summary"]
    q = report["benchmarks"]["QLD"]["summary"]
    t = report["benchmarks"]["TQQQ"]["summary"]
    bc = report["benchmark_comparison"]
    verdict = "PASS" if bc["gate_pass"] else "REJECT"
    elim = bc["elimination_reason"] or "n/a"
    lines = [
        "# Task T512 - Benchmark-Gated Candidate Evaluation",
        "",
        "## Metrics",
        "| Strategy | Initial | Final(5Y) | Return | CAGR | MDD | Worst Year | TUW | Sharpe | Trade Count |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| candidate_strategy | ${c['initial_capital']:,.2f} | ${c['final_capital']:,.2f} | {c['total_return_pct']:+.2f}% | {c['cagr_pct']:+.2f}% | -{abs(c['mdd_pct']):.2f}% | {c['worst_year_pct']:+.2f}% | {c['tuw_months']}m | {c['sharpe']:.4f} | {c['trade_count']} |",
        f"| buy_hold_QLD | ${q['initial_capital']:,.2f} | ${q['final_capital']:,.2f} | {q['total_return_pct']:+.2f}% | {q['cagr_pct']:+.2f}% | -{abs(q['mdd_pct']):.2f}% | {q['worst_year_pct']:+.2f}% | {q['tuw_months']}m | {q['sharpe']:.4f} | {q['trade_count']} |",
        f"| buy_hold_TQQQ | ${t['initial_capital']:,.2f} | ${t['final_capital']:,.2f} | {t['total_return_pct']:+.2f}% | {t['cagr_pct']:+.2f}% | -{abs(t['mdd_pct']):.2f}% | {t['worst_year_pct']:+.2f}% | {t['tuw_months']}m | {t['sharpe']:.4f} | {t['trade_count']} |",
        "",
        "## Benchmark Verdict",
        f"- vs QLD: {'WIN' if bc['win_vs_qld'] else 'LOSE'} ({bc['relative_return_vs_qld']:+.2f}% relative)",
        f"- vs TQQQ: {'WIN' if bc['win_vs_tqqq'] else 'LOSE'} ({bc['relative_return_vs_tqqq']:+.2f}% relative)",
        f"- win_both_benchmarks: {bc['win_both_benchmarks']}",
        f"- mdd_pass(<= {bc['mdd_limit_pct']:.1f}%): {bc['mdd_pass']}",
        "",
        "## Elimination Reason",
        f"- {elim}",
        "",
        f"## Final Decision: {verdict}",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="T512 benchmark-gated strategy exploration")
    parser.add_argument("--strategy-mode", type=str, default="compare_bench", help="compare_bench")
    parser.add_argument("--candidate-mode", type=str, default="momentum_only_hybrid", help="momentum_only_hybrid|trend_strength_weighted|time_stop_profiled")
    parser.add_argument("--benchmarks", type=str, default="qld,tqqq")
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_512/task_512_benchmark_gate.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_512/task_512_benchmark_gate.md")
    parser.add_argument("--regime-confirm-bars", type=int, default=2)
    parser.add_argument("--family-risk-cap-momentum-r", type=float, default=1.0)
    parser.add_argument("--family-risk-cap-reversion-r", type=float, default=0.5)
    parser.add_argument("--symbol-bucket-profile", type=str, default="hybrid_v1")
    parser.add_argument("--mdd-limit-pct", type=float, default=60.0)
    args = parser.parse_args(argv)

    mode = str(args.strategy_mode).strip().lower()
    if mode not in ALL_MODES:
        raise SystemExit(f"invalid --strategy-mode: {mode}")
    candidate_mode = str(args.candidate_mode).strip().lower()
    if candidate_mode not in ALL_CANDIDATES:
        raise SystemExit(f"invalid --candidate-mode: {candidate_mode}")
    benchmarks = [b.strip().upper() for b in str(args.benchmarks).split(",") if b.strip()]
    if set(benchmarks) != ALL_BENCHMARKS:
        raise SystemExit("--benchmarks must be exactly qld,tqqq")

    symbols = sorted({str(s).strip().upper() for s in args.symbols if str(s).strip()} | ALL_BENCHMARKS)
    frames = _load_frames(symbols, Path(args.data_dir), confirm_bars=max(1, int(args.regime_confirm_bars)))
    sim_mode, rev_guard = _candidate_mode_to_sim(candidate_mode)

    candidate_result = _simulate(
        frames,
        sim_mode,
        float(args.mdd_limit_pct),
        max(1, int(args.regime_confirm_bars)),
        float(args.family_risk_cap_momentum_r),
        float(args.family_risk_cap_reversion_r),
        str(args.symbol_bucket_profile),
        rev_guard,
    )
    candidate_summary = _extract_summary(candidate_result)
    qld_summary = _buy_hold_summary(frames, "QLD")
    tqqq_summary = _buy_hold_summary(frames, "TQQQ")
    comparison = build_benchmark_comparison(candidate_summary, qld_summary, tqqq_summary, mdd_limit_pct=float(args.mdd_limit_pct))
    decision = "PASS" if comparison["gate_pass"] else "REJECT"

    report = {
        "task": "T512",
        "strategy_mode": mode,
        "candidate_mode": candidate_mode,
        "candidate": {
            "sim_mode": sim_mode,
            "summary": candidate_summary,
        },
        "benchmarks": {
            "QLD": {"summary": qld_summary},
            "TQQQ": {"summary": tqqq_summary},
        },
        "benchmark_comparison": comparison,
        "final_decision": decision,
    }

    jout = Path(args.json_out)
    mout = Path(args.md_out)
    jout.parent.mkdir(parents=True, exist_ok=True)
    mout.parent.mkdir(parents=True, exist_ok=True)
    jout.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    mout.write_text(_md(report), encoding="utf-8")
    print(f"written_json={jout}")
    print(f"written_md={mout}")
    print(f"final_decision={decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

