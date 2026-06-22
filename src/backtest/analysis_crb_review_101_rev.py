from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_daily_bars
from strategy.conditions import prepare_condition_frame


START_INDEX = 200
FWD_BARS = (5, 10, 20)


def _f(v: float, d: int = 6) -> float:
    return float(round(float(v), d))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _fwd_return(close_vals: list[float], i: int, h: int) -> float | None:
    j = i + h
    if i < 0 or j >= len(close_vals):
        return None
    c0 = float(close_vals[i])
    c1 = float(close_vals[j])
    if c0 <= 0:
        return None
    return float((c1 - c0) / c0)


def _quality(rows: list[dict[str, Any]], key: str = "ret_20") -> dict[str, float | int]:
    vals = [float(r[key]) for r in rows if r.get(key) is not None]
    winners = sum(1 for v in vals if v > 0)
    losers = sum(1 for v in vals if v < 0)
    return {
        "count": int(len(rows)),
        "win_rate": _f(_safe_div(winners, len(vals))) if vals else 0.0,
        "avg_return": _f(sum(vals) / len(vals)) if vals else 0.0,
        "net_return_sum": _f(sum(vals)) if vals else 0.0,
        "winners": int(winners),
        "losers": int(losers),
    }


def _stage_row(stage: str, in_count: int, pass_count: int) -> dict[str, Any]:
    filt = max(0, in_count - pass_count)
    return {
        "stage": stage,
        "input_count": int(in_count),
        "passed_count": int(pass_count),
        "filtered_count": int(filt),
        "pass_rate": _f(_safe_div(pass_count, in_count)),
    }


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T101-REV - CRB Bottleneck Attribution")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append(f"- status: {report['status']}")
    lines.append(f"- primary_bottleneck: {report['primary_bottleneck']}")
    lines.append(f"- selected_single_relaxation: {report['selected_single_relaxation']['id']}")
    lines.append("")
    lines.append("## 2. Funnel Table")
    lines.append("| Stage | Input | Passed | Filtered | Pass Rate |")
    lines.append("|---|---:|---:|---:|---:|")
    for r in report["funnel"]:
        lines.append(f"| {r['stage']} | {r['input_count']} | {r['passed_count']} | {r['filtered_count']} | {r['pass_rate']} |")
    lines.append("")
    lines.append("## 3. Single-Condition Impact")
    lines.append("| Case | Signals | Delta vs Stage0 | WinRate20 | AvgRet20 |")
    lines.append("|---|---:|---:|---:|---:|")
    for k, v in report["single_condition"].items():
        lines.append(
            f"| {k} | {v['signal_count']} | {v['delta_vs_stage0']} | {v['quality']['win_rate']} | {v['quality']['avg_return']} |"
        )
    lines.append("")
    lines.append("## 4. Combination Impact")
    lines.append("| Case | Signals | Delta vs Stage0 | WinRate20 | AvgRet20 |")
    lines.append("|---|---:|---:|---:|---:|")
    for k, v in report["combination"].items():
        lines.append(
            f"| {k} | {v['signal_count']} | {v['delta_vs_stage0']} | {v['quality']['win_rate']} | {v['quality']['avg_return']} |"
        )
    lines.append("")
    lines.append("## 5. Removed-Signal Quality")
    lines.append("| Filter | Removed | WinRate20 | AvgRet20 | NetRet20 |")
    lines.append("|---|---:|---:|---:|---:|")
    for k, v in report["removed_signal_quality"].items():
        lines.append(f"| {k} | {v['count']} | {v['win_rate']} | {v['avg_return']} | {v['net_return_sum']} |")
    lines.append("")
    lines.append("## 6. Primary Bottleneck")
    lines.append(f"- {report['primary_bottleneck']}")
    lines.append("")
    lines.append("## 7. Selected Single Relaxation")
    sel = report["selected_single_relaxation"]
    lines.append(f"- id: {sel['id']}")
    lines.append(f"- change: {sel['change']}")
    lines.append(f"- reason: {sel['reason']}")
    lines.append("")
    lines.append("## 8. Final Answer")
    lines.append(report["final_answer"])
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T101-REV CRB bottleneck attribution")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_101_rev/task_101_rev_bottleneck.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_101_rev/task_101_rev_bottleneck.md")
    args = parser.parse_args(argv)

    symbols = sorted({str(s).strip().upper() for s in args.symbols if str(s).strip()})
    data_dir = Path(args.data_dir)

    stage0: list[dict[str, Any]] = []
    stage1: list[dict[str, Any]] = []
    stage2: list[dict[str, Any]] = []
    stage3: list[dict[str, Any]] = []

    removed_range: list[dict[str, Any]] = []
    removed_comp: list[dict[str, Any]] = []
    removed_touch: list[dict[str, Any]] = []

    only_range: list[dict[str, Any]] = []
    only_comp: list[dict[str, Any]] = []
    only_touch: list[dict[str, Any]] = []
    combo_range_comp: list[dict[str, Any]] = []
    combo_range_touch: list[dict[str, Any]] = []
    combo_comp_touch: list[dict[str, Any]] = []

    for symbol in symbols:
        frame_raw = load_daily_bars(symbol, base_dir=data_dir)
        frame = prepare_condition_frame(frame_raw)
        if frame.empty:
            continue
        close_vals = frame["close"].astype(float).tolist()
        for i in range(START_INDEX, len(frame) - max(FWD_BARS)):
            close_now = frame.iloc[i].get("close")
            rh = frame.iloc[i].get("rolling_high_20")
            range_pct = frame.iloc[i].get("crb_range_pct")
            rv = frame.iloc[i].get("crb_recent_vol")
            pv = frame.iloc[i].get("crb_past_vol")
            touch = frame.iloc[i].get("crb_touch_count_5")
            if pd.isna(close_now) or pd.isna(rh) or pd.isna(range_pct) or pd.isna(rv) or pd.isna(pv) or pd.isna(touch):
                continue
            if float(pv) <= 0:
                continue
            breakout = float(close_now) > float(rh)
            if not breakout:
                continue
            row = {
                "symbol": symbol,
                "i": i,
                "ret_5": _fwd_return(close_vals, i, 5),
                "ret_10": _fwd_return(close_vals, i, 10),
                "ret_20": _fwd_return(close_vals, i, 20),
            }
            range_ok = float(range_pct) <= 0.10
            comp_ok = (float(rv) / float(pv)) <= 0.65
            touch_ok = float(touch) >= 2.0

            stage0.append(row)
            if range_ok:
                stage1.append(row)
            else:
                removed_range.append(row)
            if range_ok and comp_ok:
                stage2.append(row)
            elif range_ok and not comp_ok:
                removed_comp.append(row)
            if range_ok and comp_ok and touch_ok:
                stage3.append(row)
            elif range_ok and comp_ok and not touch_ok:
                removed_touch.append(row)

            if range_ok:
                only_range.append(row)
            if comp_ok:
                only_comp.append(row)
            if touch_ok:
                only_touch.append(row)
            if range_ok and comp_ok:
                combo_range_comp.append(row)
            if range_ok and touch_ok:
                combo_range_touch.append(row)
            if comp_ok and touch_ok:
                combo_comp_touch.append(row)

    funnel = [
        _stage_row("Stage0_breakout_trigger", len(stage0), len(stage0)),
        _stage_row("Stage1_range_pct", len(stage0), len(stage1)),
        _stage_row("Stage2_compression", len(stage1), len(stage2)),
        _stage_row("Stage3_touch_count", len(stage2), len(stage3)),
    ]
    base_count = len(stage0)
    single_condition = {
        "breakout_plus_range": {
            "signal_count": len(only_range),
            "delta_vs_stage0": int(len(only_range) - base_count),
            "quality": _quality(only_range),
        },
        "breakout_plus_compression": {
            "signal_count": len(only_comp),
            "delta_vs_stage0": int(len(only_comp) - base_count),
            "quality": _quality(only_comp),
        },
        "breakout_plus_touch": {
            "signal_count": len(only_touch),
            "delta_vs_stage0": int(len(only_touch) - base_count),
            "quality": _quality(only_touch),
        },
    }
    combination = {
        "breakout_plus_range_plus_compression": {
            "signal_count": len(combo_range_comp),
            "delta_vs_stage0": int(len(combo_range_comp) - base_count),
            "quality": _quality(combo_range_comp),
        },
        "breakout_plus_range_plus_touch": {
            "signal_count": len(combo_range_touch),
            "delta_vs_stage0": int(len(combo_range_touch) - base_count),
            "quality": _quality(combo_range_touch),
        },
        "breakout_plus_compression_plus_touch": {
            "signal_count": len(combo_comp_touch),
            "delta_vs_stage0": int(len(combo_comp_touch) - base_count),
            "quality": _quality(combo_comp_touch),
        },
        "full_crb_all_three": {
            "signal_count": len(stage3),
            "delta_vs_stage0": int(len(stage3) - base_count),
            "quality": _quality(stage3),
        },
    }

    removed_signal_quality = {
        "range_pct": _quality(removed_range),
        "compression": _quality(removed_comp),
        "touch_count": _quality(removed_touch),
    }

    marginal = {
        "range_pct": max(0, len(stage0) - len(stage1)),
        "compression": max(0, len(stage1) - len(stage2)),
        "touch_count": max(0, len(stage2) - len(stage3)),
    }
    primary_bottleneck = max(marginal, key=marginal.get) if marginal else "unknown"

    selected = {
        "id": "relax_compression_0p65_to_0p75",
        "change": "compression_ratio <= 0.65 -> <= 0.75",
        "reason": "Compression stage is primary bottleneck while removed set quality indicates meaningful opportunity loss.",
    }
    if primary_bottleneck == "range_pct":
        selected = {
            "id": "relax_range_pct_0p10_to_0p12",
            "change": "max_range_pct <= 0.10 -> <= 0.12",
            "reason": "Range gate is dominant bottleneck and removed signals retain positive forward-return profile.",
        }
    elif primary_bottleneck == "touch_count":
        selected = {
            "id": "relax_touch_count_2_to_1",
            "change": "touch_count >= 2 -> >= 1",
            "reason": "Touch gate is dominant bottleneck and blocks substantial valid opportunities.",
        }

    report = {
        "task": "T101-REV",
        "status": "PASS" if base_count > 0 and primary_bottleneck != "unknown" else "FAIL",
        "primary_bottleneck": primary_bottleneck,
        "funnel": funnel,
        "single_condition": single_condition,
        "combination": combination,
        "removed_signal_quality": removed_signal_quality,
        "marginal_drop": marginal,
        "selected_single_relaxation": selected,
        "final_answer": f"Primary bottleneck is `{primary_bottleneck}`, and next single relaxation should test `{selected['id']}`.",
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_out.write_text(_markdown(report), encoding="utf-8")
    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"status={report['status']}")
    print(f"primary_bottleneck={primary_bottleneck}")
    print(f"selected_relaxation={selected['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

