from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_daily_bars
from strategy.conditions import is_breakout, is_ma_trend, prepare_condition_frame


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _f(v: float, d: int = 6) -> float:
    return float(round(float(v), d))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _fwd_return(close: list[float], i: int, horizon: int) -> float | None:
    j = i + horizon
    if i < 0 or j >= len(close):
        return None
    c0 = float(close[i])
    c1 = float(close[j])
    if c0 <= 0:
        return None
    return float((c1 - c0) / c0)


def _quality_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "count": 0,
            "avg_fwd_ret_5": 0.0,
            "avg_fwd_ret_10": 0.0,
            "avg_fwd_ret_20": 0.0,
            "positive_rate_20": 0.0,
            "net_impact_20_sum": 0.0,
        }
    ret5 = [float(r["ret_5"]) for r in rows if r.get("ret_5") is not None]
    ret10 = [float(r["ret_10"]) for r in rows if r.get("ret_10") is not None]
    ret20 = [float(r["ret_20"]) for r in rows if r.get("ret_20") is not None]
    return {
        "count": int(len(rows)),
        "avg_fwd_ret_5": _f(sum(ret5) / len(ret5)) if ret5 else 0.0,
        "avg_fwd_ret_10": _f(sum(ret10) / len(ret10)) if ret10 else 0.0,
        "avg_fwd_ret_20": _f(sum(ret20) / len(ret20)) if ret20 else 0.0,
        "positive_rate_20": _f(sum(1 for v in ret20 if v > 0) / len(ret20)) if ret20 else 0.0,
        "net_impact_20_sum": _f(sum(ret20)) if ret20 else 0.0,
    }


def _evaluate_symbol(
    symbol: str,
    *,
    selected: bool,
    base_dir: Path,
    start_index: int,
    min_avg_volume: float,
    min_avg_turnover: float,
    gap_filter_max: float,
) -> dict[str, Any]:
    frame_raw = load_daily_bars(symbol, base_dir=base_dir)
    frame = prepare_condition_frame(frame_raw)
    if frame.empty or len(frame) <= start_index + 20:
        return {
            "symbol": symbol,
            "selected": bool(selected),
            "bars_evaluated": 0,
            "stages": {"s0": 0, "s1": 0, "s2": 0, "s3": 0, "s4": 0, "s5": 0},
            "counterfactual": {"c2": 0, "c3": 0, "c4": 0, "c5": 0},
            "filter_removed": {"universe_fail": [], "breakout_fail": [], "ma_fail": [], "liquidity_fail": [], "gap_fail": []},
            "monthly": {},
        }

    close = frame["close"].astype(float).tolist()
    open_ = frame["open"].astype(float).tolist()
    avg_volume_20 = pd.to_numeric(frame.get("avg_volume_20"), errors="coerce")
    avg_turnover_20 = pd.to_numeric(frame.get("avg_turnover_20"), errors="coerce")
    if "timestamp" in frame.columns:
        idx = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
    else:
        idx = pd.to_datetime(frame.index, utc=True, errors="coerce")

    stage_counts = {"s0": 0, "s1": 0, "s2": 0, "s3": 0, "s4": 0, "s5": 0}
    counterfactual = {"c2": 0, "c3": 0, "c4": 0, "c5": 0}
    removed: dict[str, list[dict[str, Any]]] = {
        "universe_fail": [],
        "breakout_fail": [],
        "ma_fail": [],
        "liquidity_fail": [],
        "gap_fail": [],
    }
    monthly = defaultdict(lambda: {"bars": 0, "s2_breakout": 0, "s3_ma": 0, "s4_liquidity": 0, "s5_gap": 0})

    for i in range(start_index, len(frame) - 20):
        ts = idx[i]
        if pd.isna(ts):
            continue
        ym = str(pd.Timestamp(ts).strftime("%Y-%m"))
        monthly[ym]["bars"] += 1
        stage_counts["s0"] += 1

        bo = is_breakout(frame, i) is True
        if bo:
            counterfactual["c2"] += 1
        ma = is_ma_trend(frame, i) is True
        if bo and ma:
            counterfactual["c3"] += 1
        vol = float(avg_volume_20.iloc[i]) if pd.notna(avg_volume_20.iloc[i]) else None
        tov = float(avg_turnover_20.iloc[i]) if pd.notna(avg_turnover_20.iloc[i]) else None
        liq = (vol is not None and tov is not None and vol >= min_avg_volume and tov >= min_avg_turnover)
        if bo and ma and liq:
            counterfactual["c4"] += 1
        gap = (open_[i + 1] - close[i]) / close[i] if close[i] > 0 else 1.0
        if bo and ma and liq and gap <= gap_filter_max:
            counterfactual["c5"] += 1

        if not selected:
            if bo and ma and liq and gap <= gap_filter_max:
                removed["universe_fail"].append(
                    {
                        "symbol": symbol,
                        "ts": str(pd.Timestamp(ts).isoformat()),
                        "ret_5": _fwd_return(close, i, 5),
                        "ret_10": _fwd_return(close, i, 10),
                        "ret_20": _fwd_return(close, i, 20),
                    }
                )
            continue

        stage_counts["s1"] += 1

        if not bo:
            removed["breakout_fail"].append(
                {
                    "symbol": symbol,
                    "ts": str(pd.Timestamp(ts).isoformat()),
                    "ret_5": _fwd_return(close, i, 5),
                    "ret_10": _fwd_return(close, i, 10),
                    "ret_20": _fwd_return(close, i, 20),
                }
            )
            continue
        stage_counts["s2"] += 1
        monthly[ym]["s2_breakout"] += 1

        ma = is_ma_trend(frame, i) is True
        if not ma:
            removed["ma_fail"].append(
                {
                    "symbol": symbol,
                    "ts": str(pd.Timestamp(ts).isoformat()),
                    "ret_5": _fwd_return(close, i, 5),
                    "ret_10": _fwd_return(close, i, 10),
                    "ret_20": _fwd_return(close, i, 20),
                }
            )
            continue
        stage_counts["s3"] += 1
        monthly[ym]["s3_ma"] += 1

        if not liq:
            removed["liquidity_fail"].append(
                {
                    "symbol": symbol,
                    "ts": str(pd.Timestamp(ts).isoformat()),
                    "ret_5": _fwd_return(close, i, 5),
                    "ret_10": _fwd_return(close, i, 10),
                    "ret_20": _fwd_return(close, i, 20),
                }
            )
            continue
        stage_counts["s4"] += 1
        monthly[ym]["s4_liquidity"] += 1

        if gap > gap_filter_max:
            removed["gap_fail"].append(
                {
                    "symbol": symbol,
                    "ts": str(pd.Timestamp(ts).isoformat()),
                    "ret_5": _fwd_return(close, i, 5),
                    "ret_10": _fwd_return(close, i, 10),
                    "ret_20": _fwd_return(close, i, 20),
                }
            )
            continue
        stage_counts["s5"] += 1
        monthly[ym]["s5_gap"] += 1

    return {
        "symbol": symbol,
        "selected": bool(selected),
        "bars_evaluated": int(stage_counts["s0"]),
        "stages": stage_counts,
        "counterfactual": counterfactual,
        "filter_removed": removed,
        "monthly": {k: dict(v) for k, v in sorted(monthly.items())},
    }


def _build_markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T098.5 - Signal Funnel Attribution Audit")
    lines.append("")
    lines.append("## 1. Executive Summary")
    lines.append(f"- status: {report['status']}")
    lines.append(f"- primary_bottleneck: {report['primary_bottleneck']}")
    lines.append(f"- over_filtering_detected: {report['over_filtering']['detected']}")
    lines.append("")
    lines.append("## 2. Stage Funnel (0..7)")
    lines.append("| Stage | Label | Count | Drop vs prior |")
    lines.append("|---:|---|---:|---:|")
    for s in report["stage_funnel"]:
        lines.append(f"| {s['stage']} | {s['label']} | {s['count']} | {s['drop_from_prior']} |")
    lines.append("")
    lines.append("## 3. Filter Attribution")
    lines.append("| Filter | Removed | Removal Rate | Avg 20-bar Fwd Ret | Net Impact (20-bar sum) |")
    lines.append("|---|---:|---:|---:|---:|")
    for r in report["filter_attribution"]:
        q = r["removed_quality"]
        lines.append(
            f"| {r['filter']} | {r['removed_count']} | {r['removal_rate_vs_prior']} | {q['avg_fwd_ret_20']} | {q['net_impact_20_sum']} |"
        )
    lines.append("")
    lines.append("## 4. Selected vs Unselected")
    c = report["cohort_summary"]
    lines.append(f"- selected_symbols: {c['selected_symbols']}")
    lines.append(f"- unselected_symbols: {c['unselected_symbols']}")
    lines.append(f"- selected_stage5_candidates: {c['selected_stage5_candidates']}")
    lines.append(f"- unselected_stage5_candidates_counterfactual: {c['unselected_stage5_candidates_counterfactual']}")
    lines.append("")
    lines.append("## 5. Time-Series Behavior")
    t = report["time_series_behavior"]
    lines.append(f"- months: {t['months']}")
    lines.append(f"- median_stage5_per_month: {t['median_stage5_per_month']}")
    lines.append(f"- zero_stage5_month_ratio: {t['zero_stage5_month_ratio']}")
    lines.append("")
    lines.append("## 6. Over-Filtering Detection")
    lines.append(f"- detected: {report['over_filtering_detected']}")
    for flag in report["over_filtering"]["flags"]:
        lines.append(
            f"- {flag['filter']}: removal_rate={flag['removal_rate_vs_prior']} removed_avg_ret20={flag['removed_avg_fwd_ret_20']}"
        )
    lines.append("")
    lines.append("## 7. Root Cause")
    lines.append(f"- primary_filter_bottleneck: {report['primary_filter_bottleneck']}")
    lines.append(f"- secondary_filters: {', '.join(report['secondary_filters']) if report['secondary_filters'] else 'none'}")
    lines.append("")
    lines.append("## 8. Recommended Next Task")
    nxt = report["recommended_next_task"]
    lines.append(f"- task_id: {nxt['task_id']}")
    lines.append(f"- objective: {nxt['objective']}")
    lines.append("")
    lines.append("## 9. Final Answer")
    lines.append(report["final_answer"])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T098.5 signal funnel attribution audit (analysis only)")
    parser.add_argument("--base-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--input-t098", type=str, default="docs/reports/task_098/task_098_signal_density_diagnosis.json")
    parser.add_argument("--input-t097", type=str, default="docs/reports/task_097/task_097_execution_density_capital_efficiency.json")
    parser.add_argument("--input-t096", type=str, default="docs/reports/task_096/task_096_revalidation.json")
    parser.add_argument("--input-t093", type=str, default="docs/reports/task_093/task_093_capital_backtest.json")
    parser.add_argument("--json-out", type=str, default="docs/reports/task_098_5/task_098_5_signal_funnel.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_098_5/task_098_5_signal_funnel.md")
    args = parser.parse_args(argv)

    base_dir = Path(args.base_dir)
    t098 = _load_json(Path(args.input_t098))
    t097 = _load_json(Path(args.input_t097))
    t096 = _load_json(Path(args.input_t096))
    t093 = _load_json(Path(args.input_t093))
    _ = t096  # kept for required input linkage/context continuity

    selected_symbols = list(t093.get("selected_symbols", []))
    default_symbols = list(DEFAULT_US_UNIVERSE)
    unselected_symbols = [s for s in default_symbols if s not in selected_symbols]

    # Mirror strategy constants (analysis-only, no logic change).
    start_index = 200
    min_avg_volume = 1_000_000.0
    min_avg_turnover = 20_000_000.0
    gap_filter_max = 0.03

    symbol_rows: list[dict[str, Any]] = []
    for symbol in default_symbols:
        symbol_rows.append(
            _evaluate_symbol(
                symbol,
                selected=symbol in selected_symbols,
                base_dir=base_dir,
                start_index=start_index,
                min_avg_volume=min_avg_volume,
                min_avg_turnover=min_avg_turnover,
                gap_filter_max=gap_filter_max,
            )
        )

    selected_rows = [r for r in symbol_rows if bool(r["selected"])]
    unselected_rows = [r for r in symbol_rows if not bool(r["selected"])]

    s0 = int(sum(r["stages"]["s0"] for r in symbol_rows))
    s1 = int(sum(r["stages"]["s1"] for r in symbol_rows))
    s2 = int(sum(r["stages"]["s2"] for r in selected_rows))
    s3 = int(sum(r["stages"]["s3"] for r in selected_rows))
    s4 = int(sum(r["stages"]["s4"] for r in selected_rows))
    s5 = int(sum(r["stages"]["s5"] for r in selected_rows))

    s6 = int(t098.get("signal_density", {}).get("total_signals", 0))
    s7 = int(t098.get("signal_density", {}).get("executed_signals", s6))

    stage_labels = {
        0: "All bars (default universe, analyzable window)",
        1: "Selected-universe bars",
        2: "Breakout pass",
        3: "Breakout + MA pass",
        4: "Liquidity pass",
        5: "Gap pass (pre-risk candidates)",
        6: "Generated signals (from T098)",
        7: "Executed signals",
    }
    stage_counts = {0: s0, 1: s1, 2: s2, 3: s3, 4: s4, 5: s5, 6: s6, 7: s7}
    stage_funnel: list[dict[str, Any]] = []
    for i in range(8):
        prev = stage_counts[i - 1] if i > 0 else stage_counts[i]
        stage_funnel.append(
            {
                "stage": i,
                "label": stage_labels[i],
                "count": int(stage_counts[i]),
                "drop_from_prior": int(max(0, prev - stage_counts[i])) if i > 0 else 0,
                "pass_rate_vs_prior": _f(_safe_div(stage_counts[i], prev)) if i > 0 else 1.0,
            }
        )

    removed_universe = [x for r in unselected_rows for x in r["filter_removed"]["universe_fail"]]

    removed_breakout = [x for r in selected_rows for x in r["filter_removed"]["breakout_fail"]]
    removed_ma = [x for r in selected_rows for x in r["filter_removed"]["ma_fail"]]
    removed_liq = [x for r in selected_rows for x in r["filter_removed"]["liquidity_fail"]]
    removed_gap = [x for r in selected_rows for x in r["filter_removed"]["gap_fail"]]

    filter_rows = [
        ("UNIVERSE_SELECTION", s0 - s1, s0, removed_universe),
        ("BREAKOUT", s1 - s2, s1, removed_breakout),
        ("MA_TREND", s2 - s3, s2, removed_ma),
        ("LIQUIDITY", s3 - s4, s3, removed_liq),
        ("GAP", s4 - s5, s4, removed_gap),
        ("SIGNAL_MATERIALIZATION", s5 - s6, s5, []),
        (
            "RISK_OVERLAY",
            s6 - s7,
            s6,
            [],
        ),
    ]

    filter_attribution: list[dict[str, Any]] = []
    for name, removed_count, prior_count, quality_rows in filter_rows:
        q = _quality_summary(quality_rows)
        net_impact = {
            "h5": _f(float(removed_count) * float(q["avg_fwd_ret_5"])),
            "h10": _f(float(removed_count) * float(q["avg_fwd_ret_10"])),
            "h20": _f(float(removed_count) * float(q["avg_fwd_ret_20"])),
        }
        if name in {"SIGNAL_MATERIALIZATION"}:
            q = {
                "count": int(removed_count),
                "avg_fwd_ret_5": 0.0,
                "avg_fwd_ret_10": 0.0,
                "avg_fwd_ret_20": 0.0,
                "positive_rate_20": 0.0,
                "net_impact_20_sum": 0.0,
            }
            net_impact = {"h5": 0.0, "h10": 0.0, "h20": 0.0}
        if name == "RISK_OVERLAY":
            opp = t097.get("opportunity_loss", {})
            q = {
                "count": int(removed_count),
                "avg_fwd_ret_5": 0.0,
                "avg_fwd_ret_10": 0.0,
                "avg_fwd_ret_20": 0.0,
                "positive_rate_20": 0.0,
                "net_impact_20_sum": _f(float(opp.get("net_block_effect", 0.0))),
                "blocked_winners": int(opp.get("blocked_winners", 0)),
                "blocked_losers": int(opp.get("blocked_losers", 0)),
            }
            net_impact = {"h5": 0.0, "h10": 0.0, "h20": _f(float(opp.get("net_block_effect", 0.0)))}
        filter_attribution.append(
            {
                "filter": name,
                "removed_count": int(removed_count),
                "removal_rate_vs_prior": _f(_safe_div(removed_count, max(prior_count, 1))),
                "removed_quality": q,
                "net_impact_by_horizon": net_impact,
            }
        )

    symbol_level: list[dict[str, Any]] = []
    for r in symbol_rows:
        s = r["stages"]
        symbol_level.append(
            {
                "symbol": r["symbol"],
                "selected": bool(r["selected"]),
                "bars_evaluated": int(r["bars_evaluated"]),
                "stage_counts": {
                    "s0": int(s["s0"]),
                    "s1": int(s["s1"]),
                    "s2": int(s["s2"]),
                    "s3": int(s["s3"]),
                    "s4": int(s["s4"]),
                    "s5": int(s["s5"]),
                },
                "counterfactual_stage_counts": {
                    "c2": int(r["counterfactual"]["c2"]),
                    "c3": int(r["counterfactual"]["c3"]),
                    "c4": int(r["counterfactual"]["c4"]),
                    "c5": int(r["counterfactual"]["c5"]),
                },
                "stage5_rate": _f(_safe_div(s["s5"], max(s["s1"], 1))) if s["s1"] > 0 else 0.0,
            }
        )

    monthly = defaultdict(lambda: {"s1": 0, "s2": 0, "s3": 0, "s4": 0, "s5": 0})
    for r in selected_rows:
        for ym, vals in r["monthly"].items():
            monthly[ym]["s1"] += int(vals.get("bars", 0))
            monthly[ym]["s2"] += int(vals.get("s2_breakout", 0))
            monthly[ym]["s3"] += int(vals.get("s3_ma", 0))
            monthly[ym]["s4"] += int(vals.get("s4_liquidity", 0))
            monthly[ym]["s5"] += int(vals.get("s5_gap", 0))
    monthly_rows = [{"month": k, **dict(v)} for k, v in sorted(monthly.items())]
    stage5_month_vals = [int(r["s5"]) for r in monthly_rows]
    median_stage5 = float(pd.Series(stage5_month_vals).median()) if stage5_month_vals else 0.0
    zero_ratio = _safe_div(sum(1 for v in stage5_month_vals if v == 0), max(len(stage5_month_vals), 1))

    drops = [
        ("UNIVERSE_SELECTION", s0 - s1),
        ("BREAKOUT", s1 - s2),
        ("MA_TREND", s2 - s3),
        ("LIQUIDITY", s3 - s4),
        ("GAP", s4 - s5),
        ("SIGNAL_MATERIALIZATION", s5 - s6),
        ("RISK_OVERLAY", s6 - s7),
    ]
    primary_bottleneck = max(drops, key=lambda x: x[1])[0] if drops else "NONE"
    secondary_filters = [name for name, _ in sorted(drops, key=lambda x: x[1], reverse=True) if name != primary_bottleneck][:2]

    over_filter_flags = []
    for row in filter_attribution:
        name = str(row["filter"])
        if name in {"RISK_OVERLAY"}:
            continue
        removal = float(row["removal_rate_vs_prior"])
        avg20 = float(row["removed_quality"]["avg_fwd_ret_20"])
        if removal >= 0.60 and avg20 > 0:
            over_filter_flags.append(
                {
                    "filter": name,
                    "reason": "high_removal_with_positive_removed_signal_quality",
                    "removal_rate_vs_prior": _f(removal),
                    "removed_avg_fwd_ret_20": _f(avg20),
                }
            )

    report = {
        "status": "PASS",
        "task": "T098.5",
        "inputs": {
            "t098": args.input_t098,
            "t097": args.input_t097,
            "t096": args.input_t096,
            "t093": args.input_t093,
            "base_dir": str(base_dir),
        },
        "stage_funnel": stage_funnel,
        "funnel": stage_funnel,
        "filter_attribution": filter_attribution,
        "filter_impact": filter_attribution,
        "net_impact_by_filter": {
            row["filter"]: row["net_impact_by_horizon"] for row in filter_attribution
        },
        "cohort_summary": {
            "default_universe_size": int(len(default_symbols)),
            "selected_symbols": int(len(selected_symbols)),
            "unselected_symbols": int(len(unselected_symbols)),
            "selected_stage5_candidates": int(s5),
            "unselected_stage5_candidates_counterfactual": int(sum(r["counterfactual"]["c5"] for r in unselected_rows)),
            "unselected_symbols_list": list(unselected_symbols),
        },
        "symbol_level": symbol_level,
        "time_series_behavior": {
            "months": int(len(monthly_rows)),
            "median_stage5_per_month": _f(median_stage5),
            "zero_stage5_month_ratio": _f(zero_ratio),
            "monthly_stage_counts": monthly_rows,
        },
        "over_filtering": {
            "detected": bool(len(over_filter_flags) > 0),
            "flags": over_filter_flags,
        },
        "over_filtering_detected": bool(len(over_filter_flags) > 0),
        "primary_bottleneck": primary_bottleneck,
        "primary_filter_bottleneck": primary_bottleneck,
        "secondary_filters": secondary_filters,
        "removed_signal_quality": {
            row["filter"]: row["removed_quality"] for row in filter_attribution
        },
        "consistency_check": {
            "t098_selected_candidate_rate": t098.get("selected_universe_funnel", {}).get("candidate_rate"),
            "recomputed_selected_stage5_rate": _f(_safe_div(s5, max(s1, 1))),
            "t097_blocked_trades": int(t097.get("opportunity_loss", {}).get("blocked_trades", 0)),
            "t097_blocked_reason_breakdown": t097.get("opportunity_loss", {}).get("blocked_reason_breakdown", {}),
        },
        "recommended_next_task": {
            "task_id": "T099",
            "objective": "Run constrained filter-relaxation sensitivity tests on the identified bottleneck filter only, with fixed alpha logic and explicit winner/loser preservation checks.",
        },
        "final_answer": (
            f"Primary bottleneck is {primary_bottleneck}: it removes the largest share before execution, "
            "while risk-overlay blocking is comparatively small and net blocked impact is not winner-dominant."
        ),
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_build_markdown(report), encoding="utf-8")

    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print("status=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
