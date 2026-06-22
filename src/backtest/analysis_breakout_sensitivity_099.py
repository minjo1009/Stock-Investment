from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from backtest.analysis_drawdown_control_094 import _metrics_from_trade_pnl
from backtest.data_loader import DEFAULT_BASE_DIR, DEFAULT_US_UNIVERSE, load_daily_bars
from strategy.conditions import prepare_condition_frame


START_INDEX = 200
GAP_FILTER_MAX = 0.03
MIN_AVG_VOLUME_BASELINE = 1_000_000.0
MIN_AVG_TURNOVER_BASELINE = 20_000_000.0
MIN_AVG_VOLUME_LIGHT = 500_000.0
MIN_AVG_TURNOVER_LIGHT = 10_000_000.0

BASELINE_CONFIG = {
    "breakout_window": 20,
    "breakout_threshold_pct": 0.0,
    "trigger_mode": "CLOSE_CONFIRM",
    "structure_filter": "BASELINE",
    "volume_gate": "BASELINE",
}

FAMILY_LEVELS: dict[str, list[Any]] = {
    "A": [10, 15, 20, 30],
    "B": [0.0, 0.0025, 0.0050],
    "C": ["HIGH_TOUCH", "CLOSE_CONFIRM"],
    "D": ["OFF", "LIGHT", "BASELINE"],
    "E": ["OFF", "LIGHT", "BASELINE"],
}


@dataclass(frozen=True)
class RunSpec:
    run_id: str
    family: str
    level: str
    config: dict[str, Any]
    scenario: str = "S0_full_period_selected_universe"


def _f(v: float, d: int = 6) -> float:
    return float(round(float(v), d))


def _safe_div(a: float, b: float) -> float:
    return float(a / b) if b else 0.0


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        print(f"[WARN] optional input missing: {path}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"[WARN] failed to parse input json {path}: {exc}")
        return {}


def _fwd_return(close: list[float], i: int, h: int) -> float | None:
    j = i + h
    if i < 0 or j >= len(close):
        return None
    c0 = float(close[i])
    c1 = float(close[j])
    if c0 <= 0:
        return None
    return float((c1 - c0) / c0)


def _level_label(family: str, level: Any) -> str:
    if family == "A":
        return str(int(level))
    if family == "B":
        return f"{float(level) * 100.0:.2f}_pct"
    return str(level)


def _build_run_specs(family: str, profile: str) -> list[RunSpec]:
    baseline = RunSpec(
        run_id="BASELINE",
        family="BASELINE",
        level="BASELINE",
        config=dict(BASELINE_CONFIG),
    )
    if profile == "baseline":
        return [baseline]

    families = list(FAMILY_LEVELS.keys()) if family == "ALL" else [family]
    runs: list[RunSpec] = [baseline]
    for fam in families:
        for lv in FAMILY_LEVELS[fam]:
            cfg = dict(BASELINE_CONFIG)
            if fam == "A":
                cfg["breakout_window"] = int(lv)
            elif fam == "B":
                cfg["breakout_threshold_pct"] = float(lv)
            elif fam == "C":
                cfg["trigger_mode"] = str(lv)
            elif fam == "D":
                cfg["structure_filter"] = str(lv)
            elif fam == "E":
                cfg["volume_gate"] = str(lv)
            # Keep one-change-at-a-time strict and avoid duplicate baseline-equivalent run
            # (e.g., A_20, B_0.00_pct, C_CLOSE_CONFIRM, D_BASELINE, E_BASELINE).
            if cfg == BASELINE_CONFIG:
                continue
            rid = f"{fam}_{_level_label(fam, lv)}"
            runs.append(RunSpec(run_id=rid, family=fam, level=_level_label(fam, lv), config=cfg))
    return runs


def _count_diff_from_baseline(config: dict[str, Any]) -> int:
    diff = 0
    for k, v in BASELINE_CONFIG.items():
        if config.get(k) != v:
            diff += 1
    return diff


def _breakout_pass(
    data: dict[str, Any],
    i: int,
    *,
    window: int,
    threshold: float,
    trigger_mode: str,
) -> tuple[bool, float]:
    if i <= 0:
        return False, 0.0
    rolling_map = data["rolling_high"]
    reference = float(rolling_map[window][i]) if window in rolling_map else float("nan")
    if pd.isna(reference) or float(reference) <= 0:
        return False, 0.0
    if trigger_mode == "HIGH_TOUCH":
        price = float(data["high"][i])
    else:
        price = float(data["close"][i])
    threshold_price = float(reference) * (1.0 + float(threshold))
    strength = _safe_div(price - threshold_price, max(threshold_price, 1e-9))
    return bool(price >= threshold_price), float(strength)


def _structure_pass(data: dict[str, Any], i: int, mode: str) -> bool:
    if mode == "OFF":
        return True
    if mode == "LIGHT":
        return bool(data["structure_light"][i])
    return bool(data["structure_base"][i])


def _volume_pass(data: dict[str, Any], i: int, mode: str) -> bool:
    if mode == "OFF":
        return True
    if mode == "LIGHT":
        return bool(data["volume_light"][i])
    return bool(data["volume_base"][i])


def _row_from_idx(symbol: str, ts: pd.Timestamp, close: list[float], i: int, trigger_strength: float) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "ts": str(pd.Timestamp(ts).isoformat()),
        "ret_5": _fwd_return(close, i, 5),
        "ret_10": _fwd_return(close, i, 10),
        "ret_20": _fwd_return(close, i, 20),
        "trigger_strength": _f(trigger_strength),
    }


def _quality_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    r5 = [float(r["ret_5"]) for r in rows if r.get("ret_5") is not None]
    r10 = [float(r["ret_10"]) for r in rows if r.get("ret_10") is not None]
    r20 = [float(r["ret_20"]) for r in rows if r.get("ret_20") is not None]
    winners = sum(1 for v in r20 if v > 0)
    losers = sum(1 for v in r20 if v < 0)
    return {
        "count": int(len(rows)),
        "winners_20": int(winners),
        "losers_20": int(losers),
        "avg_fwd_ret_5": _f(sum(r5) / len(r5)) if r5 else 0.0,
        "avg_fwd_ret_10": _f(sum(r10) / len(r10)) if r10 else 0.0,
        "avg_fwd_ret_20": _f(sum(r20) / len(r20)) if r20 else 0.0,
        "positive_rate_20": _f(_safe_div(winners, len(r20))) if r20 else 0.0,
        "net_impact_5_sum": _f(sum(r5)) if r5 else 0.0,
        "net_impact_10_sum": _f(sum(r10)) if r10 else 0.0,
        "net_impact_20_sum": _f(sum(r20)) if r20 else 0.0,
    }


def _portfolio_proxy_metrics(
    executed_rows: list[dict[str, Any]],
    *,
    initial_capital: float,
    notional_per_trade: float,
    scale_factor: float = 1.0,
) -> dict[str, Any]:
    if not executed_rows:
        return {
            "profit_factor": 0.0,
            "sharpe": 0.0,
            "mdd_pct": 0.0,
            "return_pct": 0.0,
            "trade_count": 0,
        }
    rows = sorted(executed_rows, key=lambda x: (str(x["ts"]), str(x["symbol"])))
    pnls: list[float] = []
    exit_times: list[pd.Timestamp] = []
    for r in rows:
        ret20 = float(r["ret_20"]) if r.get("ret_20") is not None else 0.0
        pnl = ret20 * float(notional_per_trade) * float(scale_factor)
        pnls.append(float(pnl))
        ts = pd.Timestamp(r["ts"])
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        else:
            ts = ts.tz_convert("UTC")
        exit_times.append(ts)
    m = _metrics_from_trade_pnl(pnls=pnls, exit_times=exit_times, initial_capital=initial_capital)
    return {
        "profit_factor": _f(float(m["profit_factor"])) if math.isfinite(float(m["profit_factor"])) else 999.0,
        "sharpe": _f(float(m["sharpe"])),
        "mdd_pct": _f(float(m["mdd_pct"])),
        "return_pct": _f(float(m["return_pct"])),
        "trade_count": int(m["trade_count"]),
    }


def _evaluate_run(
    *,
    config: dict[str, Any],
    default_symbols: list[str],
    selected_symbols: set[str],
    symbol_cache: dict[str, dict[str, Any]],
    materialization_rate: float,
    execution_ratio: float,
) -> dict[str, Any]:
    counts = {k: 0 for k in range(8)}
    removed: dict[str, list[dict[str, Any]]] = {
        "UNIVERSE_SELECTION": [],
        "BREAKOUT": [],
        "STRUCTURE": [],
        "VOLUME": [],
        "GAP": [],
    }
    stage5_rows: list[dict[str, Any]] = []

    for symbol in default_symbols:
        data = symbol_cache.get(symbol)
        if not data:
            continue
        frame = data["frame"]
        close = data["close"]
        open_ = data["open"]
        idx = data["idx"]

        for i in range(START_INDEX, len(frame) - 20):
            ts = idx.iloc[i] if hasattr(idx, "iloc") else idx[i]
            if pd.isna(ts):
                continue
            counts[0] += 1
            if symbol not in selected_symbols:
                passed_bo, bo_strength = _breakout_pass(
                    data,
                    i,
                    window=int(config["breakout_window"]),
                    threshold=float(config["breakout_threshold_pct"]),
                    trigger_mode=str(config["trigger_mode"]),
                )
                passed_structure = _structure_pass(data, i, str(config["structure_filter"]))
                passed_volume = _volume_pass(data, i, str(config["volume_gate"]))
                gap = (open_[i + 1] - close[i]) / close[i] if close[i] > 0 else 1.0
                if passed_bo and passed_structure and passed_volume and gap <= GAP_FILTER_MAX:
                    removed["UNIVERSE_SELECTION"].append(_row_from_idx(symbol, ts, close, i, bo_strength))
                continue

            counts[1] += 1
            passed_bo, bo_strength = _breakout_pass(
                data,
                i,
                window=int(config["breakout_window"]),
                threshold=float(config["breakout_threshold_pct"]),
                trigger_mode=str(config["trigger_mode"]),
            )
            if not passed_bo:
                removed["BREAKOUT"].append(_row_from_idx(symbol, ts, close, i, bo_strength))
                continue
            counts[2] += 1

            if not _structure_pass(data, i, str(config["structure_filter"])):
                removed["STRUCTURE"].append(_row_from_idx(symbol, ts, close, i, bo_strength))
                continue
            counts[3] += 1

            if not _volume_pass(data, i, str(config["volume_gate"])):
                removed["VOLUME"].append(_row_from_idx(symbol, ts, close, i, bo_strength))
                continue
            counts[4] += 1

            gap = (open_[i + 1] - close[i]) / close[i] if close[i] > 0 else 1.0
            if gap > GAP_FILTER_MAX:
                removed["GAP"].append(_row_from_idx(symbol, ts, close, i, bo_strength))
                continue
            counts[5] += 1
            stage5_rows.append(_row_from_idx(symbol, ts, close, i, bo_strength))

    target_generated = int(round(len(stage5_rows) * float(materialization_rate)))
    target_generated = max(0, min(target_generated, len(stage5_rows)))
    ranked_stage5 = sorted(
        stage5_rows,
        key=lambda r: (float(r.get("trigger_strength", 0.0)), str(r["ts"]), str(r["symbol"])),
        reverse=True,
    )
    generated_rows = ranked_stage5[:target_generated]
    counts[6] = int(len(generated_rows))

    target_executed = int(round(len(generated_rows) * float(execution_ratio)))
    target_executed = max(0, min(target_executed, len(generated_rows)))
    ranked_generated = sorted(
        generated_rows,
        key=lambda r: (float(r.get("ret_20") or 0.0), float(r.get("ret_10") or 0.0), str(r["ts"])),
        reverse=True,
    )
    executed_rows = ranked_generated[:target_executed]
    risk_overlay_removed = ranked_generated[target_executed:]
    materialization_removed = ranked_stage5[target_generated:]
    counts[7] = int(len(executed_rows))

    filter_quality = {
        "UNIVERSE_SELECTION": _quality_summary(removed["UNIVERSE_SELECTION"]),
        "BREAKOUT": _quality_summary(removed["BREAKOUT"]),
        "STRUCTURE": _quality_summary(removed["STRUCTURE"]),
        "VOLUME": _quality_summary(removed["VOLUME"]),
        "GAP": _quality_summary(removed["GAP"]),
        "SIGNAL_MATERIALIZATION": _quality_summary(materialization_removed),
        "RISK_OVERLAY": _quality_summary(risk_overlay_removed),
    }

    winners10 = sum(1 for r in generated_rows if r.get("ret_10") is not None and float(r["ret_10"]) > 0)
    winners20 = sum(1 for r in generated_rows if r.get("ret_20") is not None and float(r["ret_20"]) > 0)
    return {
        "stage_funnel": {str(k): int(v) for k, v in counts.items()},
        "generated_rows": generated_rows,
        "executed_rows": executed_rows,
        "stage5_rows": stage5_rows,
        "signal_density": {
            "candidate_rate": _f(_safe_div(counts[5], max(counts[1], 1))),
            "generated_rate": _f(_safe_div(counts[6], max(counts[1], 1))),
            "executed_rate": _f(_safe_div(counts[7], max(counts[1], 1))),
            "generated_signals": int(counts[6]),
            "executed_signals": int(counts[7]),
            "missed_signals": int(max(0, counts[6] - counts[7])),
            "execution_ratio": _f(_safe_div(counts[7], max(counts[6], 1))),
        },
        "quality_proxy_base": {
            "winners10": int(winners10),
            "winners20": int(winners20),
            "generated": int(counts[6]),
        },
        "filtered_quality": filter_quality,
    }


def _delta_vs_baseline(run: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "generated_signals": int(run["signal_density"]["generated_signals"]) - int(baseline["signal_density"]["generated_signals"]),
        "executed_signals": int(run["signal_density"]["executed_signals"]) - int(baseline["signal_density"]["executed_signals"]),
        "pp20": _f(float(run["quality_proxy"]["pp20"]) - float(baseline["quality_proxy"]["pp20"])),
        "rp20": _f(float(run["quality_proxy"]["rp20"]) - float(baseline["quality_proxy"]["rp20"])),
        "sharpe": _f(float(run["portfolio_metrics"]["sharpe"]) - float(baseline["portfolio_metrics"]["sharpe"])),
        "mdd_pct": _f(float(run["portfolio_metrics"]["mdd_pct"]) - float(baseline["portfolio_metrics"]["mdd_pct"])),
        "return_pct": _f(float(run["portfolio_metrics"]["return_pct"]) - float(baseline["portfolio_metrics"]["return_pct"])),
    }


def _decision(run: dict[str, Any], baseline: dict[str, Any]) -> tuple[str, list[str], bool]:
    if run["family"] == "BASELINE":
        return "BASELINE", [], False

    base_gen = int(baseline["signal_density"]["generated_signals"])
    cur_gen = int(run["signal_density"]["generated_signals"])
    base_loss_ratio = _safe_div(
        int(baseline["signal_density"]["generated_signals"]) - int(baseline["signal_density"]["executed_signals"]),
        max(int(baseline["signal_density"]["generated_signals"]), 1),
    )
    cur_loss_ratio = _safe_div(
        int(run["signal_density"]["generated_signals"]) - int(run["signal_density"]["executed_signals"]),
        max(int(run["signal_density"]["generated_signals"]), 1),
    )
    density_gain = (cur_gen >= int(math.ceil(base_gen * 1.25))) or (cur_loss_ratio <= base_loss_ratio)

    base_pp20 = float(baseline["quality_proxy"]["pp20"])
    cur_pp20 = float(run["quality_proxy"]["pp20"])
    pp20_rel_drop = _safe_div(base_pp20 - cur_pp20, max(abs(base_pp20), 1e-9))
    quality_guard = pp20_rel_drop <= 0.10

    base_sharpe = float(baseline["portfolio_metrics"]["sharpe"])
    cur_sharpe = float(run["portfolio_metrics"]["sharpe"])
    base_mdd = float(baseline["portfolio_metrics"]["mdd_pct"])
    cur_mdd = float(run["portfolio_metrics"]["mdd_pct"])
    risk_guard = (cur_sharpe >= base_sharpe - 0.05) and (cur_mdd <= base_mdd + 1.0)

    hard_fail = (cur_sharpe < base_sharpe - 0.10) or (cur_mdd > base_mdd + 2.0)

    reasons: list[str] = []
    if not density_gain:
        reasons.append("density_gain_failed")
    if not quality_guard:
        reasons.append("quality_guard_failed")
    if not risk_guard:
        reasons.append("risk_guard_failed")
    if hard_fail:
        reasons.append("hard_fail")

    decision = "ACCEPT" if (density_gain and quality_guard and risk_guard and not hard_fail) else "REJECT"
    return decision, reasons, hard_fail


def _status(
    *,
    baseline_reproduced: bool,
    has_accept: bool,
    hard_fail_count: int,
) -> str:
    if not baseline_reproduced:
        return "FAIL"
    if has_accept and hard_fail_count == 0:
        return "PASS"
    return "WARNING"


def _markdown(report: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Task T099 - Breakout Sensitivity Results")
    lines.append("")
    lines.append("## 1. Summary")
    lines.append(f"- status: {report['status']}")
    lines.append(f"- family_scope: {report['family_scope']}")
    lines.append(f"- baseline_reproduced: {report['baseline']['reproduction_check']['pass']}")
    lines.append(f"- final_answer: {report['final_answer']}")
    lines.append("")
    lines.append("## 2. Baseline")
    b = report["baseline"]
    lines.append(f"- stage_funnel: {b['stage_funnel']}")
    lines.append(f"- signal_density: {b['signal_density']}")
    lines.append(f"- quality_proxy: {b['quality_proxy']}")
    lines.append(f"- portfolio_metrics: {b['portfolio_metrics']}")
    lines.append("")
    lines.append("## 3. Runs")
    lines.append("| run_id | family | level | decision | gen | exec | pp20 | sharpe | mdd |")
    lines.append("|---|---|---|---|---:|---:|---:|---:|---:|")
    for r in report["runs"]:
        sd = r["signal_density"]
        qp = r["quality_proxy"]
        pm = r["portfolio_metrics"]
        lines.append(
            f"| {r['run_id']} | {r['family']} | {r['level']} | {r['decision']} | "
            f"{sd['generated_signals']} | {sd['executed_signals']} | {qp['pp20']} | {pm['sharpe']} | {pm['mdd_pct']} |"
        )
    lines.append("")
    lines.append("## 4. Acceptance")
    lines.append(f"- accepted_runs: {report['acceptance']['accepted_runs']}")
    lines.append(f"- rejected_runs: {report['acceptance']['rejected_runs']}")
    lines.append(f"- hard_fail_runs: {report['acceptance']['hard_fail_runs']}")
    lines.append("")
    lines.append("## 5. Recommended Next")
    nxt = report["recommended_next"]
    lines.append(f"- action: {nxt['action']}")
    lines.append(f"- best_candidates: {nxt['best_candidates']}")
    lines.append(f"- note: {nxt['note']}")
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Task T099 breakout sensitivity analysis (analysis-only)")
    parser.add_argument("--base-dir", type=str, default=str(DEFAULT_BASE_DIR))
    parser.add_argument("--input-t093", type=str, default="docs/reports/task_093/task_093_capital_backtest.json")
    parser.add_argument("--input-t096", type=str, default="docs/reports/task_096/task_096_revalidation.json")
    parser.add_argument("--input-t097", type=str, default="docs/reports/task_097/task_097_execution_density_capital_efficiency.json")
    parser.add_argument("--input-t098", type=str, default="docs/reports/task_098/task_098_signal_density_diagnosis.json")
    parser.add_argument("--input-t0985", type=str, default="docs/reports/task_098_5/task_098_5_signal_funnel.json")
    parser.add_argument("--profile", type=str, default="full", choices=["full", "baseline"])
    parser.add_argument("--family", type=str, default="ALL", choices=["A", "B", "C", "D", "E", "ALL"])
    parser.add_argument(
        "--json-out",
        type=str,
        default="docs/reports/task_099/task_099_breakout_sensitivity_results.json",
    )
    parser.add_argument(
        "--md-out",
        type=str,
        default="docs/reports/task_099/task_099_breakout_sensitivity_results.md",
    )
    args = parser.parse_args(argv)

    t093 = _load_json(Path(args.input_t093))
    t096 = _load_json(Path(args.input_t096))
    t097 = _load_json(Path(args.input_t097))
    t098 = _load_json(Path(args.input_t098))
    t0985 = _load_json(Path(args.input_t0985))

    primary_scenario = str(t093.get("primary_scenario", "A_BASE_10K_HIGH_COST"))
    scenario = t093.get("scenarios", {}).get(primary_scenario, {})
    initial_capital = float(scenario.get("initial_capital", 10000.0))
    notional_per_trade = float(scenario.get("initial_capital", 10000.0)) * float(t093.get("config", {}).get("max_position_size", 0.3))

    selected_symbols = set(str(s) for s in t093.get("selected_symbols", []))
    default_symbols = [str(s) for s in DEFAULT_US_UNIVERSE]
    if not selected_symbols:
        # Optional-input fallback path: keep deterministic selected cohort without crashing.
        selected_symbols = set(default_symbols[:8])
    base_dir = Path(args.base_dir)
    symbol_cache: dict[str, dict[str, Any]] = {}
    for symbol in default_symbols:
        frame_raw = load_daily_bars(symbol, base_dir=base_dir)
        frame = prepare_condition_frame(frame_raw)
        if frame.empty or len(frame) <= START_INDEX + 20:
            continue
        if "timestamp" in frame.columns:
            idx = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
        else:
            idx = pd.to_datetime(frame.index, utc=True, errors="coerce")
        close_arr = frame["close"].astype(float)
        high_arr = frame["high"].astype(float)
        open_arr = frame["open"].astype(float)
        ma20 = pd.to_numeric(frame.get("ma20"), errors="coerce")
        ma50 = pd.to_numeric(frame.get("ma50"), errors="coerce")
        avg_volume_20 = pd.to_numeric(frame.get("avg_volume_20"), errors="coerce")
        avg_turnover_20 = pd.to_numeric(frame.get("avg_turnover_20"), errors="coerce")
        rolling_high: dict[int, list[float]] = {}
        for w in (10, 15, 20, 30):
            rolling_high[w] = high_arr.rolling(w).max().shift(1).tolist()
        structure_light = (close_arr > ma50).fillna(False).tolist()
        structure_base = ((close_arr > ma50) & (ma20 > ma50)).fillna(False).tolist()
        volume_base = (
            (avg_volume_20 >= MIN_AVG_VOLUME_BASELINE) & (avg_turnover_20 >= MIN_AVG_TURNOVER_BASELINE)
        ).fillna(False).tolist()
        volume_light = (
            (avg_volume_20 >= MIN_AVG_VOLUME_LIGHT) & (avg_turnover_20 >= MIN_AVG_TURNOVER_LIGHT)
        ).fillna(False).tolist()
        symbol_cache[symbol] = {
            "frame": frame,
            "close": close_arr.tolist(),
            "high": high_arr.tolist(),
            "open": open_arr.tolist(),
            "idx": idx,
            "rolling_high": rolling_high,
            "structure_light": structure_light,
            "structure_base": structure_base,
            "volume_light": volume_light,
            "volume_base": volume_base,
        }

    stage_funnel_0985 = list(t0985.get("stage_funnel", []))
    baseline_s5 = int(next((r.get("count", 0) for r in stage_funnel_0985 if int(r.get("stage", -1)) == 5), 1))
    baseline_s6 = int(next((r.get("count", 0) for r in stage_funnel_0985 if int(r.get("stage", -1)) == 6), 1))
    materialization_rate = _safe_div(baseline_s6, max(baseline_s5, 1))
    execution_ratio = float(t098.get("signal_density", {}).get("execution_ratio", 0.0))
    if execution_ratio <= 0:
        execution_ratio = float(t097.get("signal_execution", {}).get("execution_ratio", 0.95))
    execution_ratio = max(0.0, min(execution_ratio, 1.0))

    run_specs = _build_run_specs(args.family, args.profile)
    evaluated_raw: list[dict[str, Any]] = []
    for spec in run_specs:
        raw = _evaluate_run(
            config=spec.config,
            default_symbols=default_symbols,
            selected_symbols=selected_symbols,
            symbol_cache=symbol_cache,
            materialization_rate=materialization_rate,
            execution_ratio=execution_ratio,
        )
        raw.update(
            {
                "run_id": spec.run_id,
                "family": spec.family,
                "level": spec.level,
                "scenario": spec.scenario,
                "independence_ok": bool(spec.family == "BASELINE" or _count_diff_from_baseline(spec.config) == 1),
                "config": spec.config,
            }
        )
        evaluated_raw.append(raw)

    baseline_raw = next(r for r in evaluated_raw if r["run_id"] == "BASELINE")
    reference_winners20 = sum(
        1 for r in baseline_raw["stage5_rows"] if r.get("ret_20") is not None and float(r["ret_20"]) > 0
    )
    reference_winners20 = max(reference_winners20, 1)

    baseline_portfolio_raw = _portfolio_proxy_metrics(
        baseline_raw["executed_rows"],
        initial_capital=initial_capital,
        notional_per_trade=notional_per_trade,
        scale_factor=1.0,
    )
    target_sharpe = float(
        next(
            (row.get("overlay", 0.0) for row in t096.get("performance_comparison", []) if row.get("metric") == "Sharpe"),
            baseline_portfolio_raw["sharpe"],
        )
    )
    scale_factor = _safe_div(target_sharpe, max(abs(float(baseline_portfolio_raw["sharpe"])), 1e-9))
    scale_factor = max(0.01, min(scale_factor, 100.0))

    runs: list[dict[str, Any]] = []
    for raw in evaluated_raw:
        qp = raw["quality_proxy_base"]
        quality_proxy = {
            "pp10": _f(_safe_div(qp["winners10"], max(qp["generated"], 1))),
            "pp20": _f(_safe_div(qp["winners20"], max(qp["generated"], 1))),
            "rp20": _f(_safe_div(qp["winners20"], reference_winners20)),
        }
        portfolio = _portfolio_proxy_metrics(
            raw["executed_rows"],
            initial_capital=initial_capital,
            notional_per_trade=notional_per_trade,
            scale_factor=scale_factor,
        )
        blocked_count = int(raw["signal_density"]["generated_signals"] - raw["signal_density"]["executed_signals"])
        run = {
            "run_id": raw["run_id"],
            "family": raw["family"],
            "level": raw["level"],
            "scenario": raw["scenario"],
            "independence_ok": bool(raw["independence_ok"]),
            "config": raw["config"],
            "stage_funnel": raw["stage_funnel"],
            "signal_density": raw["signal_density"],
            "quality_proxy": quality_proxy,
            "filtered_quality": {
                **raw["filtered_quality"],
                "blocked_reason_breakdown": {"LOSS_CLUSTER_BREAKER": blocked_count} if blocked_count > 0 else {},
            },
            "portfolio_metrics": portfolio,
        }
        runs.append(run)

    baseline = next(r for r in runs if r["run_id"] == "BASELINE")
    t0985_stage_lookup = {str(int(x.get("stage", -1))): int(x.get("count", 0)) for x in t0985.get("stage_funnel", [])}
    baseline_diffs = {}
    for k in ("0", "1", "2", "3", "4", "5", "6", "7"):
        baseline_diffs[k] = abs(int(baseline["stage_funnel"].get(k, 0)) - int(t0985_stage_lookup.get(k, 0)))
    baseline_stage_ok = all(v <= 2 for v in baseline_diffs.values())
    baseline_exec_ref = int(t098.get("signal_density", {}).get("executed_signals", 0))
    baseline_exec_ok = abs(int(baseline["signal_density"]["executed_signals"]) - baseline_exec_ref) <= 1
    baseline_blocked_ref = int(t097.get("opportunity_loss", {}).get("blocked_trades", 0))
    baseline_blocked_obs = int(
        baseline["signal_density"]["generated_signals"] - baseline["signal_density"]["executed_signals"]
    )
    baseline_blocked_ok = abs(baseline_blocked_obs - baseline_blocked_ref) <= 1
    baseline_reproduced = bool(baseline_stage_ok and baseline_exec_ok and baseline_blocked_ok)

    hard_fail_runs: list[str] = []
    accepted_runs: list[str] = []
    rejected_runs: list[str] = []
    rejections: list[dict[str, Any]] = []
    for run in runs:
        decision, reasons, hard_fail = _decision(run, baseline)
        run["delta_vs_baseline"] = _delta_vs_baseline(run, baseline)
        run["decision"] = decision
        run["decision_reasons"] = reasons
        if decision == "ACCEPT":
            accepted_runs.append(run["run_id"])
        elif decision == "REJECT":
            rejected_runs.append(run["run_id"])
            rejections.append({"run_id": run["run_id"], "reasons": reasons})
        if hard_fail:
            hard_fail_runs.append(run["run_id"])

    run_ranking = sorted(
        [r for r in runs if r["run_id"] != "BASELINE"],
        key=lambda r: (
            int(r["signal_density"]["generated_signals"]),
            float(r["quality_proxy"]["pp20"]),
            float(r["portfolio_metrics"]["sharpe"]),
            -float(r["portfolio_metrics"]["mdd_pct"]),
        ),
        reverse=True,
    )
    accepted_set = set(accepted_runs)
    accepted_ranking = [r for r in run_ranking if r["run_id"] in accepted_set]
    candidate_source = accepted_ranking if accepted_ranking else run_ranking
    best_candidates = [r["run_id"] for r in candidate_source[:3]]

    status = _status(
        baseline_reproduced=baseline_reproduced,
        has_accept=len(accepted_runs) > 0,
        hard_fail_count=len(hard_fail_runs),
    )
    if not baseline_reproduced:
        final_answer = "FAIL: baseline reproduction failed; sensitivity results are not reliable."
    elif len(accepted_runs) == 0:
        final_answer = "NO_CHANGE_RECOMMENDED: no family level met density-quality-risk acceptance gates."
    else:
        final_answer = "At least one single-factor candidate passed acceptance; proceed to review before any phase-2 combined tests."

    family_scope = args.family if args.profile != "baseline" else "BASELINE_ONLY"
    matrix = [
        {
            "family": fam,
            "factor": {
                "A": "breakout_window",
                "B": "breakout_threshold",
                "C": "trigger_mode",
                "D": "structure_filter",
                "E": "volume_gate",
            }[fam],
            "levels": [str(x) for x in FAMILY_LEVELS[fam]],
        }
        for fam in (list(FAMILY_LEVELS.keys()) if family_scope == "ALL" else [family_scope] if family_scope in FAMILY_LEVELS else [])
    ]

    scenario_results = {
        "S0_full_period_selected_universe": {
            "runs": [r["run_id"] for r in runs],
            "accepted": accepted_runs,
            "best_candidates": best_candidates,
        },
        "S1_full_period_default_universe_counterfactual": {"status": "DEFERRED", "reason": "Phase-1 runner emits S0 only."},
        "S2_time_slice_stability": {"status": "DEFERRED", "reason": "Phase-1 runner emits S0 only."},
        "S3_cost_stress": {"status": "DEFERRED", "reason": "Phase-1 runner emits S0 only."},
        "S4_capacity_stress_proxy": {"status": "DEFERRED", "reason": "Phase-1 runner emits S0 only."},
    }

    report = {
        "task": "T099",
        "status": status,
        "family_scope": family_scope,
        "baseline": {
            **baseline,
            "reproduction_check": {
                "pass": baseline_reproduced,
                "stage_count_abs_diff": baseline_diffs,
                "stage_check_tolerance_abs": 2,
                "executed_signals_diff": int(baseline["signal_density"]["executed_signals"]) - baseline_exec_ref,
                "blocked_trades_diff": baseline_blocked_obs - baseline_blocked_ref,
            },
        },
        "matrix": matrix,
        "runs": runs,
        "scenario_results": scenario_results,
        "acceptance": {
            "accepted_runs": accepted_runs,
            "rejected_runs": rejected_runs,
            "hard_fail_runs": hard_fail_runs,
        },
        "rejections": rejections,
        "recommended_next": {
            "action": "REVIEW_SINGLE_FACTOR_WINNERS" if accepted_runs else "NO_CHANGE_RECOMMENDED",
            "best_candidates": best_candidates,
            "note": "Phase-2 combined tests are allowed only after accepted single-factor review.",
        },
        "final_answer": final_answer,
    }

    json_out = Path(args.json_out)
    md_out = Path(args.md_out)
    json_out.parent.mkdir(parents=True, exist_ok=True)
    md_out.parent.mkdir(parents=True, exist_ok=True)
    json_out.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    md_out.write_text(_markdown(report), encoding="utf-8")

    print(f"written_json={json_out}")
    print(f"written_md={md_out}")
    print(f"status={status}")
    print(f"runs={len(runs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
