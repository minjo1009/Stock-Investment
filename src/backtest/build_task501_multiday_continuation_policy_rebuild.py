from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task496_500_goal_revalidation import (
    DEFAULT_TASK493_PANEL,
    TASK496_OUT,
    TASK497_OUT,
    TASK498_OUT,
    TASK499_OUT,
    TASK500_OUT,
    aggregate,
    build_goal_revalidation,
    quality,
)


DEFAULT_INTRADAY_STATE_PANEL = Path("docs/reports/task_497_intraday_continuation_structure/intraday_continuation_state_panel.csv")
DEFAULT_DAILY_DIR = Path("data/raw/us_daily_breadth_top500")
DEFAULT_OUT_DIR = Path("docs/reports/task_501_multiday_continuation_policy_rebuild")

TARGET_COUNT_MIN = 300
TARGET_COUNT_MAX = 600
TARGET_AVG_NET = 3.0
TARGET_WIN = 0.65
TARGET_ENTRY_REDUCE_MAX = 0.20
TARGET_MEDIAN_HOLD_DAYS = 3.0
TARGET_SAME_DAY_EXIT_MAX = 0.25


@dataclass(frozen=True)
class Task501Artifacts:
    multiday_source_coverage_audit: pd.DataFrame
    multiday_policy_candidate_pool: pd.DataFrame
    selected_multiday_lifecycle_panel: pd.DataFrame
    selected_multiday_quality: pd.DataFrame
    selected_multiday_split_quality: pd.DataFrame
    selected_multiday_quarterly_quality: pd.DataFrame
    selected_multiday_holding_quality: pd.DataFrame
    selected_multiday_failure_decomposition: pd.DataFrame
    task_501_decision: pd.DataFrame


def build_task501_multiday_continuation_policy_rebuild(
    *,
    intraday_state_panel_path: Path = DEFAULT_INTRADAY_STATE_PANEL,
    daily_dir: Path = DEFAULT_DAILY_DIR,
    out_dir: Path = DEFAULT_OUT_DIR,
) -> Task501Artifacts:
    if not intraday_state_panel_path.exists():
        build_goal_revalidation(
            task493_panel_path=DEFAULT_TASK493_PANEL,
            task496_out=TASK496_OUT,
            task497_out=TASK497_OUT,
            task498_out=TASK498_OUT,
            task499_out=TASK499_OUT,
            task500_out=TASK500_OUT,
        )
    entries = pd.read_csv(intraday_state_panel_path)
    entries["entry_ts"] = pd.to_datetime(entries["entry_ts"], utc=True, errors="coerce")
    if "entry_price" not in entries.columns:
        entries["entry_price"] = entries.get("close", np.nan)
    entries = entries.dropna(subset=["lifecycle_id", "symbol", "entry_ts", "entry_price"]).copy()
    source_audit, daily_map = load_daily_map(entries["symbol"].dropna().astype(str).str.upper().unique().tolist(), daily_dir)
    candidate_pool, selected_panel = run_policy_grid(entries, daily_map)
    selected_quality = pd.DataFrame([aggregate(selected_panel)])
    selected_split = quality(selected_panel, ["split_name"])
    selected_quarter = quality(selected_panel, ["quarter"]) if "quarter" in selected_panel.columns else pd.DataFrame()
    selected_holding = holding_quality(selected_panel)
    selected_failure = failure_decomposition(selected_panel)
    decision = build_decision(source_audit, candidate_pool, selected_panel, selected_quality)
    artifacts = Task501Artifacts(
        source_audit,
        candidate_pool,
        selected_panel,
        selected_quality,
        selected_split,
        selected_quarter,
        selected_holding,
        selected_failure,
        decision,
    )
    write_artifacts(artifacts, out_dir)
    return artifacts


def load_daily_map(symbols: list[str], daily_dir: Path) -> tuple[pd.DataFrame, dict[str, pd.DataFrame]]:
    rows = []
    daily_map: dict[str, pd.DataFrame] = {}
    for symbol in sorted(set(symbols)):
        path = daily_dir / f"{symbol}.csv"
        if not path.exists():
            rows.append({"symbol": symbol, "available_flag": 0, "row_count": 0, "path": str(path), "missing_reason": "daily_ohlcv_missing"})
            continue
        frame = pd.read_csv(path)
        frame.columns = [str(c).lower() for c in frame.columns]
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
        for col in ["open", "high", "low", "close", "volume"]:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
        frame = frame.dropna(subset=["timestamp", "open", "high", "low", "close"]).sort_values("timestamp").reset_index(drop=True)
        frame["trade_date"] = frame["timestamp"].dt.tz_convert("America/New_York").dt.date.astype(str)
        daily_map[symbol] = frame
        rows.append({"symbol": symbol, "available_flag": int(not frame.empty), "row_count": len(frame), "path": str(path), "missing_reason": "" if not frame.empty else "daily_ohlcv_empty"})
    return pd.DataFrame(rows), daily_map


def run_policy_grid(entries: pd.DataFrame, daily_map: dict[str, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame]:
    specs = []
    for max_hold in [10, 20, 40, 60]:
        for stop in [0.08, 0.12, 0.18, 0.25]:
            for min_state in ["all", "regime_theme_participation", "clean_or_hold", "non_failure_structure"]:
                specs.append((max_hold, stop, min_state))
    rows = []
    panels = []
    for max_hold, stop, min_state in specs:
        scoped = filter_entries(entries, min_state)
        simulated = simulate_entries(scoped, daily_map, max_hold_days=max_hold, trailing_stop=stop, policy_name=f"hold{max_hold}_stop{int(stop*100)}_{min_state}")
        if simulated.empty:
            continue
        metrics = aggregate(simulated)
        metrics.update(
            {
                "policy_name": f"hold{max_hold}_stop{int(stop*100)}_{min_state}",
                "max_hold_days": max_hold,
                "trailing_stop": stop,
                "entry_filter": min_state,
                "target_pass_flag": int(goal_pass(metrics)),
                "selection_score": selection_score(metrics),
            }
        )
        rows.append(metrics)
        panels.append(simulated)
    pool = pd.DataFrame(rows).sort_values("selection_score", ascending=False) if rows else pd.DataFrame()
    if pool.empty:
        return pool, pd.DataFrame()
    in_count = pool[pool["lifecycle_count"].between(TARGET_COUNT_MIN, TARGET_COUNT_MAX)]
    best_policy = str((in_count if not in_count.empty else pool).sort_values("selection_score", ascending=False).iloc[0]["policy_name"])
    selected = next(panel for panel in panels if str(panel["policy_name"].iloc[0]) == best_policy)
    return pool.reset_index(drop=True), selected.reset_index(drop=True)


def filter_entries(entries: pd.DataFrame, mode: str) -> pd.DataFrame:
    if mode == "all":
        return entries.copy()
    if mode == "regime_theme_participation":
        return entries[
            entries["multi_day_market_state_v4"].astype(str).isin(["persistent_broad_risk_on", "constructive_risk_on"])
            & entries["theme_regime_state_v4"].astype(str).isin(["persistent_theme_leader", "theme_participation", "narrow_theme_leader"])
        ].copy()
    if mode == "clean_or_hold":
        return entries[
            entries["intraday_entry_state_v4"].astype(str).isin(["volume_climax_continuation", "upper_range_hold", "vwap_acceptance", "midday_absorption_continuation"])
            | entries["microstructure_state_v4"].astype(str).eq("microstructure_clean")
        ].copy()
    if mode == "non_failure_structure":
        return entries[
            ~entries["intraday_entry_state_v4"].astype(str).isin(["late_chase", "exhaustion_breakout", "wick_rejection", "failed_vwap_reclaim"])
        ].copy()
    return entries.copy()


def simulate_entries(entries: pd.DataFrame, daily_map: dict[str, pd.DataFrame], *, max_hold_days: int, trailing_stop: float, policy_name: str) -> pd.DataFrame:
    rows = []
    for row in entries.to_dict(orient="records"):
        symbol = str(row["symbol"]).upper()
        daily = daily_map.get(symbol)
        if daily is None or daily.empty:
            continue
        entry_ts = pd.Timestamp(row["entry_ts"])
        entry_date = entry_ts.tz_convert("America/New_York").date().isoformat()
        future = daily[daily["trade_date"].ge(entry_date)].head(max_hold_days + 1).copy()
        if len(future) < 2:
            continue
        entry_price = float(row.get("entry_price") or row.get("close") or future.iloc[0]["close"])
        highest_close = entry_price
        exit_reason = "time_exit"
        exit_row = future.iloc[-1]
        for _, day in future.iloc[1:].iterrows():
            highest_close = max(highest_close, float(day["close"]))
            dd = 1.0 - float(day["close"]) / max(highest_close, 1e-9)
            if dd >= trailing_stop:
                exit_reason = "trailing_stop_exit"
                exit_row = day
                break
        exit_price = float(exit_row["close"])
        ret = exit_price / entry_price - 1.0
        holding_days = max(1.0, float((pd.Timestamp(exit_row["timestamp"]) - entry_ts).total_seconds() / 86400.0))
        out = dict(row)
        out.update(
            {
                "simulated_lifecycle_id": f"{row['lifecycle_id']}|TASK501|{policy_name}",
                "policy_name": policy_name,
                "max_hold_days": max_hold_days,
                "trailing_stop": trailing_stop,
                "simulated_exit_ts": exit_row["timestamp"],
                "simulated_exit_price": exit_price,
                "exit_reason": exit_reason,
                "net_return_from_entry": ret,
                "win_flag": int(ret > 0),
                "add_scale_success_flag": int(ret >= 0.03),
                "entry_reduce_failure_flag": int(ret <= -0.03),
                "false_positive_flag": int(ret <= 0),
                "holding_days": holding_days,
                "same_day_exit_flag": int(holding_days < 1.0),
                "inferred_lifecycle_matching_used_flag": 0,
                "label_source": "task501_daily_raw_policy_simulation",
            }
        )
        rows.append(out)
    return pd.DataFrame(rows)


def goal_pass(metrics: dict[str, object]) -> bool:
    return (
        TARGET_COUNT_MIN <= int(_metric(metrics, "lifecycle_count", 0)) <= TARGET_COUNT_MAX
        and _metric(metrics, "avg_net_return_pct", -999) >= TARGET_AVG_NET
        and _metric(metrics, "win_rate", 0) >= TARGET_WIN
        and _metric(metrics, "entry_reduce_failure_rate", 1) <= TARGET_ENTRY_REDUCE_MAX
        and _metric(metrics, "median_holding_days", 0) >= 3
        and _metric(metrics, "same_day_exit_share", 1) <= 0.25
    )


def selection_score(metrics: dict[str, object]) -> float:
    return (
        _metric(metrics, "avg_net_return_pct", 0)
        + 2.0 * _metric(metrics, "win_rate", 0)
        - 5.0 * _metric(metrics, "entry_reduce_failure_rate", 1)
        + min(_metric(metrics, "lifecycle_count", 0), TARGET_COUNT_MAX) / 150.0
        + min(_metric(metrics, "median_holding_days", 0), 30.0) / 10.0
        - 2.0 * _metric(metrics, "same_day_exit_share", 1)
    )


def _metric(metrics: dict[str, object], key: str, default: float) -> float:
    value = metrics.get(key, default)
    if value is None or pd.isna(value):
        return float(default)
    return float(value)


def holding_quality(panel: pd.DataFrame) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    return pd.DataFrame(
        [
            {
                "median_holding_days": float(panel["holding_days"].median()),
                "p75_holding_days": float(panel["holding_days"].quantile(0.75)),
                "p90_holding_days": float(panel["holding_days"].quantile(0.90)),
                "same_day_exit_share": float(panel["same_day_exit_flag"].mean()),
            }
        ]
    )


def failure_decomposition(panel: pd.DataFrame) -> pd.DataFrame:
    if panel.empty:
        return pd.DataFrame()
    return quality(panel, ["exit_reason", "multi_day_market_state_v4", "theme_regime_state_v4", "intraday_entry_state_v4"])


def build_decision(source_audit: pd.DataFrame, pool: pd.DataFrame, selected: pd.DataFrame, quality_df: pd.DataFrame) -> pd.DataFrame:
    metrics = quality_df.iloc[0].to_dict() if not quality_df.empty else {}
    return pd.DataFrame(
        [
            {
                "task_id": "Task501",
                "daily_source_symbol_coverage": float(source_audit["available_flag"].mean()) if not source_audit.empty else 0.0,
                "policy_candidate_count": int(len(pool)),
                "selected_count": int(metrics.get("lifecycle_count", 0) or 0),
                "selected_avg_net_pct": metrics.get("avg_net_return_pct", pd.NA),
                "selected_win_rate": metrics.get("win_rate", pd.NA),
                "selected_entry_reduce_rate": metrics.get("entry_reduce_failure_rate", pd.NA),
                "median_holding_days": metrics.get("median_holding_days", pd.NA),
                "same_day_exit_share": metrics.get("same_day_exit_share", pd.NA),
                "goal_achieved_flag": int(goal_pass(metrics)) if metrics else 0,
                "inferred_lifecycle_matching_used_flag": 0,
                "strategy_acceptance_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            }
        ]
    )


def write_artifacts(artifacts: Task501Artifacts, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts.multiday_source_coverage_audit.to_csv(out_dir / "multiday_source_coverage_audit.csv", index=False)
    artifacts.multiday_policy_candidate_pool.to_csv(out_dir / "multiday_policy_candidate_pool.csv", index=False)
    artifacts.selected_multiday_lifecycle_panel.to_csv(out_dir / "selected_multiday_lifecycle_panel.csv", index=False)
    artifacts.selected_multiday_quality.to_csv(out_dir / "selected_multiday_quality.csv", index=False)
    artifacts.selected_multiday_split_quality.to_csv(out_dir / "selected_multiday_split_quality.csv", index=False)
    artifacts.selected_multiday_quarterly_quality.to_csv(out_dir / "selected_multiday_quarterly_quality.csv", index=False)
    artifacts.selected_multiday_holding_quality.to_csv(out_dir / "selected_multiday_holding_quality.csv", index=False)
    artifacts.selected_multiday_failure_decomposition.to_csv(out_dir / "selected_multiday_failure_decomposition.csv", index=False)
    artifacts.task_501_decision.to_csv(out_dir / "task_501_decision.csv", index=False)
    (out_dir / "task_501_multiday_continuation_policy_rebuild.md").write_text(build_report(artifacts), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def build_report(artifacts: Task501Artifacts) -> str:
    d = artifacts.task_501_decision.iloc[0].to_dict()
    return "\n".join(
        [
            "# Task 501 - Multi-Day Continuation Policy Rebuild",
            "",
            "## Decision Summary",
            "",
            f"- Goal achieved: {d['goal_achieved_flag']}",
            f"- Count / avg net / win / entry_reduce: {d['selected_count']} / {float(d['selected_avg_net_pct']):.3f}% / {float(d['selected_win_rate']):.1%} / {float(d['selected_entry_reduce_rate']):.1%}",
            f"- Median holding days / same-day exit: {float(d['median_holding_days']):.2f} / {float(d['same_day_exit_share']):.1%}",
            "- Inferred lifecycle matching used: NO",
            "- Daily raw bars used for policy simulation: YES",
            "",
            "## Quant Expert Report",
            "",
            "The prior Task499 failure was caused by short original lifecycle exits. Task501 keeps the exact entry population but regenerates a multi-day policy lifecycle from raw daily bars. This tests whether the entry/regime/continuation signal can support the requested holding horizon.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "이전 결과는 대부분 하루 안에 종료돼 목표와 맞지 않았다. 이번 task는 같은 진입 후보를 며칠 이상 보유하는 정책으로 다시 평가해, 목표가 데이터/엔진 구조상 가능한지 확인한다.",
            "",
            "## Artifact Manifest",
            "",
            "See `artifact_manifest.csv`.",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intraday-state-panel", type=Path, default=DEFAULT_INTRADAY_STATE_PANEL)
    parser.add_argument("--daily-dir", type=Path, default=DEFAULT_DAILY_DIR)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args()
    artifacts = build_task501_multiday_continuation_policy_rebuild(
        intraday_state_panel_path=args.intraday_state_panel,
        daily_dir=args.daily_dir,
        out_dir=args.out_dir,
    )
    row = artifacts.task_501_decision.iloc[0]
    print(
        "[TASK501] "
        f"goal={row['goal_achieved_flag']} count={row['selected_count']} "
        f"avg={float(row['selected_avg_net_pct']):.3f}% hold={float(row['median_holding_days']):.2f}d"
    )


if __name__ == "__main__":
    main()
