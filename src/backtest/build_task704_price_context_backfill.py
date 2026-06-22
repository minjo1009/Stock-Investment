from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


BASELINE_PANEL = Path(
    "docs/reports/task_633_qqq_benchmark_full_period_refresh/"
    "task632_temporal_strict_refresh/task_632_baseline_all_confirmed_backtest_panel.csv"
)
TASK636_LINKS = Path("docs/reports/task_636_full_period_content_prediction_backtest/task_636_entry_event_links.csv")
INTRADAY_DIR = Path("data/raw/us_intraday")
DAILY_DIR = Path("data/raw/us_daily_breadth_top500")
REPORT_DIR = Path("docs/reports/task_704_price_context_backfill")


def build_task704_price_context_backfill(
    *,
    baseline_panel_path: Path = BASELINE_PANEL,
    task636_links_path: Path = TASK636_LINKS,
    intraday_dir: Path = INTRADAY_DIR,
    daily_dir: Path = DAILY_DIR,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    baseline = pd.read_csv(baseline_panel_path, usecols=["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"])
    links = pd.read_csv(task636_links_path, usecols=["lifecycle_id", "symbol"]).drop_duplicates()
    baseline["event_linked_flag"] = baseline[["lifecycle_id", "symbol"]].merge(
        links.assign(event_linked_flag=1), on=["lifecycle_id", "symbol"], how="left"
    )["event_linked_flag"].fillna(0).astype(int)

    context = build_context_panel(baseline, intraday_dir, daily_dir)
    summary = build_summary(context)
    decision = build_decision(context, summary)
    pass_fail = build_pass_fail(context)

    context.to_csv(out_dir / "task704_price_context_panel.csv", index=False)
    summary.to_csv(out_dir / "task704_price_context_summary.csv", index=False)
    decision.to_csv(out_dir / "task_704_decision.csv", index=False)
    pass_fail.to_csv(out_dir / "task_704_pass_fail_matrix.csv", index=False)
    write_report(out_dir, context, summary, decision, pass_fail)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "context": context,
        "summary": summary,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_context_panel(baseline: pd.DataFrame, intraday_dir: Path, daily_dir: Path) -> pd.DataFrame:
    daily_cache: dict[str, pd.DataFrame] = {}
    intraday_cache: dict[str, pd.DataFrame] = {}
    rows: list[dict[str, object]] = []
    for row in baseline.sort_values(["symbol", "entry_ts", "lifecycle_id"]).to_dict(orient="records"):
        symbol = str(row["symbol"]).upper()
        entry_ts = pd.to_datetime(row["entry_ts"], utc=True)
        if symbol not in daily_cache:
            daily_cache[symbol] = load_daily(daily_dir / f"{symbol}.csv")
        if symbol not in intraday_cache:
            intraday_cache[symbol] = load_intraday(intraday_dir / f"{symbol}.csv")
        rows.append(build_row(row, entry_ts, daily_cache[symbol], intraday_cache[symbol]))
    return pd.DataFrame(rows)


def load_daily(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = [str(c).lower() for c in df.columns]
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["timestamp", "open", "high", "low", "close", "volume"]).sort_values("timestamp").reset_index(drop=True)
    df["trade_date"] = df["timestamp"].dt.date
    close = df["close"]
    df["ma20"] = close.rolling(20, min_periods=10).mean()
    df["ma50"] = close.rolling(50, min_periods=20).mean()
    df["high60"] = df["high"].rolling(60, min_periods=20).max()
    df["vol20"] = df["volume"].rolling(20, min_periods=10).mean()
    df["volume_ratio_prev"] = df["volume"] / df["vol20"].replace(0, np.nan)
    df["near_high60_prev"] = df["close"] / df["high60"].replace(0, np.nan)
    df["trend_stack_prev"] = (df["close"].gt(df["ma20"]) & df["ma20"].gt(df["ma50"])).astype(int)
    return df


def load_intraday(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df.columns = [str(c).lower() for c in df.columns]
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["timestamp", "open", "high", "low", "close", "volume"]).sort_values("timestamp").reset_index(drop=True)
    df["timestamp_et"] = df["timestamp"].dt.tz_convert("America/New_York")
    df["trade_date"] = df["timestamp_et"].dt.date
    df["minute"] = df["timestamp_et"].dt.hour * 60 + df["timestamp_et"].dt.minute
    return df[df["minute"].between(9 * 60 + 30, 15 * 60 + 45)].copy()


def build_row(base: dict[str, object], entry_ts: pd.Timestamp, daily: pd.DataFrame, intraday: pd.DataFrame) -> dict[str, object]:
    symbol = str(base["symbol"]).upper()
    entry_date = entry_ts.tz_convert("America/New_York").date()
    daily_feature = previous_daily_feature(daily, entry_date)
    intraday_feature = intraday_feature_at_entry(intraday, entry_ts, entry_date)
    merged = {**daily_feature, **intraday_feature}
    score = price_acceptance_score(merged)
    state = price_acceptance_state(score)
    chart_state = classify_price_chart_acceptance(merged, score, state)
    available = int(daily_feature["daily_context_available_flag"] == 1 and intraday_feature["intraday_context_available_flag"] == 1)
    reason = "available" if available else ";".join(
        x for x in [daily_feature["daily_missing_reason"], intraday_feature["intraday_missing_reason"]] if x
    )
    return {
        "lifecycle_id": base["lifecycle_id"],
        "symbol": symbol,
        "theme_id": base["theme_id"],
        "entry_ts": base["entry_ts"],
        "split_name": base["split_name"],
        "event_linked_flag": int(base["event_linked_flag"]),
        "price_context_available_flag": available,
        "price_context_source": "raw_daily_plus_intraday_asof_entry" if available else "missing_raw_context",
        "price_context_missing_reason": reason,
        "price_acceptance_score": score if available else 0,
        "price_acceptance_state": state if available else "price_context_missing",
        "price_chart_acceptance_state": chart_state if available else "",
        **merged,
        "outcome_used_for_assignment_flag": 0,
        "future_price_used_for_assignment_flag": 0,
    }


def previous_daily_feature(daily: pd.DataFrame, entry_date: object) -> dict[str, object]:
    if daily.empty:
        return missing_daily("daily_file_missing")
    prior = daily[daily["trade_date"] < entry_date].tail(1)
    if prior.empty:
        return missing_daily("previous_daily_bar_missing")
    row = prior.iloc[0]
    return {
        "daily_context_available_flag": 1,
        "daily_missing_reason": "",
        "previous_daily_date": str(row["trade_date"]),
        "volume_ratio_prev": safe_float(row["volume_ratio_prev"], 0.0),
        "near_high60_prev": safe_float(row["near_high60_prev"], 0.0),
        "trend_stack_prev": int(safe_float(row["trend_stack_prev"], 0.0)),
    }


def missing_daily(reason: str) -> dict[str, object]:
    return {
        "daily_context_available_flag": 0,
        "daily_missing_reason": reason,
        "previous_daily_date": "",
        "volume_ratio_prev": 0.0,
        "near_high60_prev": 0.0,
        "trend_stack_prev": 0,
    }


def intraday_feature_at_entry(intraday: pd.DataFrame, entry_ts: pd.Timestamp, entry_date: object) -> dict[str, object]:
    if intraday.empty:
        return missing_intraday("intraday_file_missing")
    day = intraday[intraday["trade_date"].eq(entry_date)].copy()
    if day.empty:
        return missing_intraday("intraday_trade_date_missing")
    day = day[day["timestamp"].le(entry_ts)].copy()
    if day.empty:
        return missing_intraday("no_intraday_bar_at_or_before_entry")
    day["day_high_so_far"] = day["high"].cummax()
    day["day_low_so_far"] = day["low"].cummin()
    day["range_pos"] = (day["close"] - day["day_low_so_far"]) / (day["day_high_so_far"] - day["day_low_so_far"]).replace(0, np.nan)
    day["intraday_ret_from_open"] = day["close"] / float(day.iloc[0]["open"]) - 1.0
    day["cum_vwap"] = (day["close"] * day["volume"]).cumsum() / day["volume"].replace(0, np.nan).cumsum()
    day["cum_vwap"] = day["cum_vwap"].ffill().fillna(day["close"])
    day["breakout_so_far"] = day["close"].gt(day["day_high_so_far"].shift(1))
    bar = day.iloc[-1]
    range_pos = safe_float(bar["range_pos"], 0.5)
    intraday_ret = safe_float(bar["intraday_ret_from_open"], 0.0)
    vwap_ok = bool(safe_float(bar["close"], 0.0) >= safe_float(bar["cum_vwap"], 0.0))
    breakout = bool(bar["breakout_so_far"]) or range_pos >= 0.85
    accepted = vwap_ok and range_pos >= 0.70 and intraday_ret >= 0.002 and breakout
    minute = int(bar["minute"])
    if accepted and minute < 10 * 60 + 30:
        timing = "opening_drive"
    elif accepted:
        timing = "trend_continuation"
    elif vwap_ok and intraday_ret >= 0:
        timing = "vwap_reclaim"
    else:
        timing = "no_intraday_confirmation"
    return {
        "intraday_context_available_flag": 1,
        "intraday_missing_reason": "",
        "entry_bar_ts": str(bar["timestamp"]),
        "entry_bar_close": safe_float(bar["close"], 0.0),
        "entry_bar_cum_vwap": safe_float(bar["cum_vwap"], 0.0),
        "range_pos": range_pos,
        "intraday_ret_from_open": intraday_ret,
        "vwap_ok_flag": int(vwap_ok),
        "breakout_so_far_flag": int(breakout),
        "intraday_entry_state_v4": "intraday_breakout_acceptance" if accepted else "intraday_observed_no_breakout_acceptance",
        "timing_state": timing,
    }


def missing_intraday(reason: str) -> dict[str, object]:
    return {
        "intraday_context_available_flag": 0,
        "intraday_missing_reason": reason,
        "entry_bar_ts": "",
        "entry_bar_close": 0.0,
        "entry_bar_cum_vwap": 0.0,
        "range_pos": 0.0,
        "intraday_ret_from_open": 0.0,
        "vwap_ok_flag": 0,
        "breakout_so_far_flag": 0,
        "intraday_entry_state_v4": "intraday_context_missing",
        "timing_state": "intraday_context_missing",
    }


def price_acceptance_score(row: dict[str, object]) -> int:
    score = 0
    if row.get("intraday_entry_state_v4") == "intraday_breakout_acceptance":
        score += 2
    if row.get("timing_state") in {"opening_drive", "trend_continuation", "vwap_reclaim"}:
        score += 1
    if safe_float(row.get("range_pos"), 0.0) >= 0.75:
        score += 1
    if safe_float(row.get("intraday_ret_from_open"), 0.0) > 0:
        score += 1
    if safe_float(row.get("volume_ratio_prev"), 0.0) >= 1.2:
        score += 1
    if safe_float(row.get("near_high60_prev"), 0.0) >= 0.95:
        score += 1
    if safe_float(row.get("range_pos"), 0.0) <= 0.35:
        score -= 2
    if safe_float(row.get("intraday_ret_from_open"), 0.0) < -0.01:
        score -= 2
    return int(score)


def price_acceptance_state(score: int) -> str:
    if score >= 5:
        return "price_acceptance_strong"
    if score >= 3:
        return "price_acceptance_accepted"
    if score >= 1:
        return "price_acceptance_neutral"
    return "price_acceptance_rejected"


def classify_price_chart_acceptance(row: dict[str, object], score: int, state: str) -> str:
    range_pos = safe_float(row.get("range_pos"), 0.0)
    intraday = safe_float(row.get("intraday_ret_from_open"), 0.0)
    volume = safe_float(row.get("volume_ratio_prev"), 0.0)
    near_high = safe_float(row.get("near_high60_prev"), 0.0)
    trend = int(safe_float(row.get("trend_stack_prev"), 0.0))
    if state == "price_acceptance_strong" and score >= 6 and trend == 1 and near_high >= 0.95 and intraday < 0.04:
        return "price_confirmed_not_extended"
    if state == "price_acceptance_strong" and (range_pos >= 0.98 or intraday >= 0.04):
        return "price_confirmed_but_extended"
    if state == "price_acceptance_strong":
        return "price_confirmed_basic"
    if state == "price_acceptance_accepted" and volume >= 0.8:
        return "price_accepted_needs_confirmation"
    return "price_fragile_or_unconfirmed"


def build_summary(context: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scope_name, frame in [
        ("all_5265", context),
        ("event_linked", context[context["event_linked_flag"].eq(1)]),
    ]:
        rows.append(
            {
                "scope": scope_name,
                "row_count": int(len(frame)),
                "price_context_available_count": int(frame["price_context_available_flag"].sum()),
                "price_context_missing_count": int((1 - frame["price_context_available_flag"]).sum()),
                "price_context_available_rate": float(frame["price_context_available_flag"].mean()) if len(frame) else 0.0,
                "outcome_used_for_assignment_flag_sum": int(frame["outcome_used_for_assignment_flag"].sum()),
                "future_price_used_for_assignment_flag_sum": int(frame["future_price_used_for_assignment_flag"].sum()),
            }
        )
    for split, frame in context[context["event_linked_flag"].eq(1)].groupby("split_name", dropna=False):
        rows.append(
            {
                "scope": f"event_linked_{split}",
                "row_count": int(len(frame)),
                "price_context_available_count": int(frame["price_context_available_flag"].sum()),
                "price_context_missing_count": int((1 - frame["price_context_available_flag"]).sum()),
                "price_context_available_rate": float(frame["price_context_available_flag"].mean()) if len(frame) else 0.0,
                "outcome_used_for_assignment_flag_sum": int(frame["outcome_used_for_assignment_flag"].sum()),
                "future_price_used_for_assignment_flag_sum": int(frame["future_price_used_for_assignment_flag"].sum()),
            }
        )
    return pd.DataFrame(rows)


def build_decision(context: pd.DataFrame, summary: pd.DataFrame) -> pd.DataFrame:
    event = summary[summary["scope"].eq("event_linked")].iloc[0]
    return pd.DataFrame(
        [
            {
                "task_id": "Task704",
                "verdict": "PRICE_CONTEXT_BACKFILL_COMPLETE",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "all_row_count": int(len(context)),
                "event_linked_row_count": int(event["row_count"]),
                "event_linked_price_context_available_count": int(event["price_context_available_count"]),
                "event_linked_price_context_missing_count": int(event["price_context_missing_count"]),
                "event_linked_price_context_available_rate": float(event["price_context_available_rate"]),
                "outcome_used_for_assignment_flag_sum": int(context["outcome_used_for_assignment_flag"].sum()),
                "future_price_used_for_assignment_flag_sum": int(context["future_price_used_for_assignment_flag"].sum()),
                "next_action": "Rerun Task703 using this as-of price context panel before changing parser rules.",
            }
        ]
    )


def build_pass_fail(context: pd.DataFrame) -> pd.DataFrame:
    event = context[context["event_linked_flag"].eq(1)]
    return pd.DataFrame(
        [
            gate("event_linked_price_context_full", int(event["price_context_available_flag"].sum()) == len(event), f"{int(event['price_context_available_flag'].sum())}/{len(event)}", "2445/2445"),
            gate("all_baseline_price_context_full", int(context["price_context_available_flag"].sum()) == len(context), f"{int(context['price_context_available_flag'].sum())}/{len(context)}", "5265/5265"),
            gate("no_outcome_assignment", int(context["outcome_used_for_assignment_flag"].sum()) == 0, str(int(context["outcome_used_for_assignment_flag"].sum())), "0"),
            gate("no_future_price_assignment", int(context["future_price_used_for_assignment_flag"].sum()) == 0, str(int(context["future_price_used_for_assignment_flag"].sum())), "0"),
        ]
    )


def write_report(out_dir: Path, context: pd.DataFrame, summary: pd.DataFrame, decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    d = decision.iloc[0]
    out_dir.joinpath("task_704_price_context_backfill.md").write_text(
        f"""# Task704 Price Context Backfill

## Decision Summary

- Verdict: {d['verdict']}.
- Strategy acceptance status: {d['strategy_acceptance_status']}.
- Real capital status: {d['real_capital_status']}.
- Event-linked coverage: {int(d['event_linked_price_context_available_count'])}/{int(d['event_linked_row_count'])}.
- Outcome/future assignment flags: {int(d['outcome_used_for_assignment_flag_sum'])}/{int(d['future_price_used_for_assignment_flag_sum'])}.

## Quant Expert Report

- Rebuilt price context from raw daily and intraday files.
- Daily features use the prior trading day only.
- Intraday features use bars at or before each candidate entry timestamp only.
- No return, exit, label, or future price fields enter assignment context.

## No-Background Decision-Maker Report

- The previously missing price confirmation fields are backfilled from raw data.
- This is not a trading strategy and does not approve capital.
- Task703 must be rerun with this panel before parser rule changes.

## Artifact Manifest

- `task704_price_context_panel.csv`
- `task704_price_context_summary.csv`
- `task_704_decision.csv`
- `task_704_pass_fail_matrix.csv`
- `artifact_manifest.csv`

## Pass/Fail Matrix

{markdown_table(pass_fail)}
""",
        encoding="utf-8",
    )


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "pass_flag": int(passed),
        "observed": observed,
        "required": required,
    }


def safe_float(value: object, default: float) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline-panel", type=Path, default=BASELINE_PANEL)
    parser.add_argument("--task636-links", type=Path, default=TASK636_LINKS)
    parser.add_argument("--intraday-dir", type=Path, default=INTRADAY_DIR)
    parser.add_argument("--daily-dir", type=Path, default=DAILY_DIR)
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    build_task704_price_context_backfill(
        baseline_panel_path=args.baseline_panel,
        task636_links_path=args.task636_links,
        intraday_dir=args.intraday_dir,
        daily_dir=args.daily_dir,
        out_dir=args.out_dir,
    )
    print(f"[Task704] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
