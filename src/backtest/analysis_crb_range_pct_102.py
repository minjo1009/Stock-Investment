from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_daily_bars
from strategy.conditions import prepare_condition_frame


START_INDEX = 200
FWD_HORIZON = 20


def _f(v: float, d: int = 6) -> float:
    return float(round(float(v), d))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _fwd_ret(close_vals: list[float], i: int, h: int = FWD_HORIZON) -> float | None:
    j = i + h
    if i < 0 or j >= len(close_vals):
        return None
    c0 = float(close_vals[i])
    c1 = float(close_vals[j])
    if c0 <= 0:
        return None
    return float((c1 - c0) / c0)


def _quality(rows: list[dict[str, Any]]) -> dict[str, float | int]:
    vals = [float(r["ret_20"]) for r in rows if r.get("ret_20") is not None]
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


def _run_case(*, symbols: list[str], data_dir: Path, max_range_pct: float) -> dict[str, Any]:
    stage0 = 0
    rows: list[dict[str, Any]] = []
    for symbol in symbols:
        frame_raw = load_daily_bars(symbol, base_dir=data_dir)
        frame = prepare_condition_frame(frame_raw)
        if frame.empty:
            continue
        close_vals = frame["close"].astype(float).tolist()
        for i in range(START_INDEX, len(frame) - FWD_HORIZON):
            row = frame.iloc[i]
            close_now = row.get("close")
            rh = row.get("rolling_high_20")
            range_pct = row.get("crb_range_pct")
            rv = row.get("crb_recent_vol")
            pv = row.get("crb_past_vol")
            touch = row.get("crb_touch_count_5")
            if pd.isna(close_now) or pd.isna(rh) or pd.isna(range_pct) or pd.isna(rv) or pd.isna(pv) or pd.isna(touch):
                continue
            if float(pv) <= 0:
                continue
            breakout = float(close_now) > float(rh)
            if not breakout:
                continue
            stage0 += 1
            range_ok = float(range_pct) <= max_range_pct
            comp_ok = (float(rv) / float(pv)) <= 0.65
            touch_ok = float(touch) >= 2.0
            if range_ok and comp_ok and touch_ok:
                rows.append({"symbol": symbol, "i": i, "ret_20": _fwd_ret(close_vals, i)})
    return {
        "max_range_pct": max_range_pct,
        "stage0_breakout_count": int(stage0),
        "final_signal_count": int(len(rows)),
        "signal_pass_rate_vs_breakout": _f(_safe_div(len(rows), stage0)),
        "quality": _quality(rows),
    }


def _markdown(report: dict[str, Any]) -> str:
    b = report["case_0_10"]
    c = report["case_0_12"]
    d = report["delta_0_12_minus_0_10"]
    lines = [
        "# Task T102 - CRB range_pct Validation",
        "",
        "## Objective",
        "- Validate max_range_pct 0.12 vs 0.10 while keeping N=20, compression=0.65, touch=2.",
        "",
        "## Comparison",
        "| Metric | 0.10 | 0.12 | Delta |",
        "|---|---:|---:|---:|",
        f"| final_signal_count | {b['final_signal_count']} | {c['final_signal_count']} | {d['final_signal_count']} |",
        f"| pass_rate_vs_breakout | {b['signal_pass_rate_vs_breakout']} | {c['signal_pass_rate_vs_breakout']} | {d['signal_pass_rate_vs_breakout']} |",
        f"| win_rate_20 | {b['quality']['win_rate']} | {c['quality']['win_rate']} | {d['win_rate_20']} |",
        f"| avg_return_20 | {b['quality']['avg_return']} | {c['quality']['avg_return']} | {d['avg_return_20']} |",
        f"| net_return_sum_20 | {b['quality']['net_return_sum']} | {c['quality']['net_return_sum']} | {d['net_return_sum_20']} |",
        "",
        "## Decision",
        f"- status: {report['status']}",
        f"- answer: {report['answer']}",
        f"- note: {report['note']}",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T102: max_range_pct single-parameter validation")
    parser.add_argument("--data-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--symbols", nargs="*", default=list(DEFAULT_US_UNIVERSE))
    parser.add_argument("--json-out", type=str, default="docs/reports/task_102/task_102_range_pct_validation.json")
    parser.add_argument("--md-out", type=str, default="docs/reports/task_102/task_102_range_pct_validation.md")
    args = parser.parse_args(argv)

    symbols = sorted({str(s).strip().upper() for s in args.symbols if str(s).strip()})
    data_dir = Path(args.data_dir)
    case_010 = _run_case(symbols=symbols, data_dir=data_dir, max_range_pct=0.10)
    case_012 = _run_case(symbols=symbols, data_dir=data_dir, max_range_pct=0.12)

    delta = {
        "final_signal_count": int(case_012["final_signal_count"] - case_010["final_signal_count"]),
        "signal_pass_rate_vs_breakout": _f(case_012["signal_pass_rate_vs_breakout"] - case_010["signal_pass_rate_vs_breakout"]),
        "win_rate_20": _f(case_012["quality"]["win_rate"] - case_010["quality"]["win_rate"]),
        "avg_return_20": _f(case_012["quality"]["avg_return"] - case_010["quality"]["avg_return"]),
        "net_return_sum_20": _f(case_012["quality"]["net_return_sum"] - case_010["quality"]["net_return_sum"]),
    }

    density_up = delta["final_signal_count"] > 0
    quality_not_destroyed = case_012["quality"]["avg_return"] >= (case_010["quality"]["avg_return"] - 0.003)
    status = "PASS" if density_up and quality_not_destroyed else "WARNING"
    answer = "YES" if status == "PASS" else "NO"

    report = {
        "task": "T102",
        "constraints": {
            "N": 20,
            "compression_ratio": 0.65,
            "touch_count": 2,
            "changed_only": "max_range_pct",
        },
        "case_0_10": case_010,
        "case_0_12": case_012,
        "delta_0_12_minus_0_10": delta,
        "status": status,
        "answer": answer,
        "note": "Single-parameter validation only; no multi-parameter tuning applied.",
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_out.write_text(_markdown(report), encoding="utf-8")
    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"status={status}")
    print(f"answer={answer}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

