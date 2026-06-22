from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import pandas as pd

from scripts.task_artifact_manifest import write_manifest


TASK_ID = "Task608G"
REPORT_DIR = Path("docs/reports/task_608g_live_detectable_entry_failure_path_diagnostics")
TASK509_PANEL = Path("docs/reports/task_509_walk_forward_oos_validation/walk_forward_oos_assignment_panel.csv")
INTRADAY_DIR = Path("data/raw/us_intraday")
REFERENCE_SYMBOL = "QQQ"
HORIZONS_MINUTES = [15, 30, 60, 120]


def build_task608g_live_detectable_entry_failure_path_diagnostics(
    *,
    task509_panel_path: Path = TASK509_PANEL,
    intraday_dir: Path = INTRADAY_DIR,
    out_dir: Path = REPORT_DIR,
) -> dict[str, pd.DataFrame]:
    assignments = load_assignments(task509_panel_path)
    symbols = sorted(set(assignments["symbol"].dropna().astype(str).str.upper()) | {REFERENCE_SYMBOL})
    intraday_map, source_coverage = load_intraday_sources(symbols, intraday_dir)
    path_panel = build_path_panel(assignments, intraday_map)
    cohort_summary = build_cohort_summary(path_panel)
    signal_summary = build_signal_candidate_summary(path_panel)
    interaction_summary = build_state_signal_interaction_summary(path_panel)
    quarter_summary = build_quarter_signal_summary(path_panel)
    decisions = build_decisions(source_coverage, path_panel, signal_summary, interaction_summary)

    out_dir.mkdir(parents=True, exist_ok=True)
    source_coverage.to_csv(out_dir / "intraday_source_coverage.csv", index=False)
    path_panel.to_csv(out_dir / "entry_failure_path_panel.csv", index=False)
    cohort_summary.to_csv(out_dir / "clean_vs_failed_path_summary.csv", index=False)
    signal_summary.to_csv(out_dir / "live_signal_candidate_summary.csv", index=False)
    interaction_summary.to_csv(out_dir / "state_signal_interaction_summary.csv", index=False)
    quarter_summary.to_csv(out_dir / "quarter_live_signal_summary.csv", index=False)
    decisions.to_csv(out_dir / "task_608g_decision.csv", index=False)
    (out_dir / "task_608g_live_detectable_entry_failure_path_diagnostics.md").write_text(
        render_report(source_coverage, cohort_summary, signal_summary, interaction_summary, quarter_summary, decisions),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "intraday_source_coverage": source_coverage,
        "entry_failure_path_panel": path_panel,
        "clean_vs_failed_path_summary": cohort_summary,
        "live_signal_candidate_summary": signal_summary,
        "state_signal_interaction_summary": interaction_summary,
        "quarter_live_signal_summary": quarter_summary,
        "task_608g_decision": decisions,
    }


def load_assignments(path: Path) -> pd.DataFrame:
    path = Path(path)
    frame = pd.read_csv(path)
    frame["entry_ts"] = pd.to_datetime(frame["entry_ts"], utc=True, errors="coerce")
    frame["entry_price"] = pd.to_numeric(frame["entry_price"], errors="coerce")
    frame["net_return_from_entry"] = pd.to_numeric(frame["net_return_from_entry"], errors="coerce")
    frame["entry_reduce_failure_flag"] = pd.to_numeric(
        frame["entry_reduce_failure_flag"], errors="coerce"
    ).fillna(0).astype(int)
    frame["win_flag"] = pd.to_numeric(frame["win_flag"], errors="coerce").fillna(0).astype(int)
    frame = frame.dropna(subset=["lifecycle_id", "symbol", "entry_ts", "entry_price"]).copy()
    if "quarter" not in frame.columns:
        frame["quarter"] = frame["entry_ts"].dt.to_period("Q").astype(str)
    return frame.sort_values("entry_ts").reset_index(drop=True)


def load_intraday_sources(symbols: list[str], intraday_dir: Path) -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    intraday_dir = Path(intraday_dir)
    intraday_map: dict[str, pd.DataFrame] = {}
    rows = []
    for symbol in symbols:
        path = intraday_dir / f"{symbol}.csv"
        if not path.exists():
            rows.append(
                {
                    "symbol": symbol,
                    "available_flag": 0,
                    "row_count": 0,
                    "has_raw_vwap_flag": 0,
                    "derived_ohlcv_vwap_flag": 0,
                    "path": str(path),
                    "missing_reason": "intraday_ohlcv_missing",
                }
            )
            continue
        frame = pd.read_csv(path)
        frame.columns = [str(column).lower() for column in frame.columns]
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True, errors="coerce")
        for column in ["open", "high", "low", "close", "volume"]:
            frame[column] = pd.to_numeric(frame[column], errors="coerce")
        frame = frame.dropna(subset=["timestamp", "open", "high", "low", "close", "volume"]).copy()
        frame = frame.sort_values("timestamp").reset_index(drop=True)
        frame["session_date_et"] = frame["timestamp"].dt.tz_convert("America/New_York").dt.date.astype(str)
        has_raw_vwap = "vwap" in frame.columns and pd.to_numeric(frame["vwap"], errors="coerce").notna().any()
        if has_raw_vwap:
            frame["diagnostic_vwap"] = pd.to_numeric(frame["vwap"], errors="coerce")
            derived_flag = 0
        else:
            typical = (frame["high"] + frame["low"] + frame["close"]) / 3.0
            pv = typical * frame["volume"]
            cum_pv = pv.groupby(frame["session_date_et"]).cumsum()
            cum_volume = frame["volume"].groupby(frame["session_date_et"]).cumsum()
            frame["diagnostic_vwap"] = cum_pv / cum_volume.replace(0, pd.NA)
            derived_flag = 1
        intraday_map[symbol] = frame
        rows.append(
            {
                "symbol": symbol,
                "available_flag": int(not frame.empty),
                "row_count": int(len(frame)),
                "has_raw_vwap_flag": int(has_raw_vwap),
                "derived_ohlcv_vwap_flag": derived_flag,
                "path": str(path),
                "missing_reason": "" if not frame.empty else "intraday_ohlcv_empty",
            }
        )
    return intraday_map, pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)


def build_path_panel(assignments: pd.DataFrame, intraday_map: dict[str, pd.DataFrame]) -> pd.DataFrame:
    reference = intraday_map.get(REFERENCE_SYMBOL, pd.DataFrame())
    rows = []
    for item in assignments.to_dict(orient="records"):
        symbol = str(item["symbol"]).upper()
        symbol_frame = intraday_map.get(symbol, pd.DataFrame())
        row = base_path_row(item, symbol_frame)
        if not symbol_frame.empty:
            row.update(path_features(item, symbol_frame, prefix="symbol"))
        if not reference.empty:
            ref_item = dict(item)
            ref_item["symbol"] = REFERENCE_SYMBOL
            row.update(path_features(ref_item, reference, prefix="qqq"))
            for horizon in HORIZONS_MINUTES:
                symbol_ret = row.get(f"symbol_ret_{horizon}m")
                qqq_ret = row.get(f"qqq_ret_{horizon}m")
                row[f"relative_ret_vs_qqq_{horizon}m"] = _subtract(symbol_ret, qqq_ret)
        row.update(signal_flags(row))
        rows.append(row)
    return pd.DataFrame(rows)


def base_path_row(item: dict[str, Any], symbol_frame: pd.DataFrame) -> dict[str, Any]:
    return {
        "lifecycle_id": item["lifecycle_id"],
        "symbol": str(item["symbol"]).upper(),
        "theme_id": item.get("theme_id", ""),
        "quarter": item.get("quarter", ""),
        "entry_ts": item["entry_ts"],
        "entry_price": float(item["entry_price"]),
        "timing_state": item.get("timing_state", ""),
        "intraday_entry_state_v4": item.get("intraday_entry_state_v4", ""),
        "symbol_multiday_setup_state": item.get("symbol_multiday_setup_state", ""),
        "theme_regime_state_v4": item.get("theme_regime_state_v4", ""),
        "net_return_from_entry": float(item.get("net_return_from_entry", 0.0)),
        "win_flag": int(item.get("win_flag", 0)),
        "entry_reduce_failure_flag": int(item.get("entry_reduce_failure_flag", 0)),
        "symbol_intraday_available_flag": int(not symbol_frame.empty),
    }


def path_features(item: dict[str, Any], frame: pd.DataFrame, *, prefix: str) -> dict[str, Any]:
    entry_ts = pd.Timestamp(item["entry_ts"])
    session_date = entry_ts.tz_convert("America/New_York").date().isoformat()
    session = frame[frame["session_date_et"].eq(session_date)].copy()
    if session.empty:
        return {f"{prefix}_session_available_flag": 0}
    entry_bar = session[session["timestamp"].ge(entry_ts)].head(1)
    if entry_bar.empty:
        return {f"{prefix}_session_available_flag": 1, f"{prefix}_entry_bar_available_flag": 0}
    entry_price = float(entry_bar.iloc[0]["close"]) if prefix == "qqq" else float(item["entry_price"])

    features: dict[str, Any] = {
        f"{prefix}_session_available_flag": 1,
        f"{prefix}_entry_bar_available_flag": 1,
    }
    opening_window = session[
        session["timestamp"].between(pd.Timestamp(session_date).tz_localize("America/New_York").tz_convert("UTC") + pd.Timedelta(hours=9, minutes=30), entry_ts)
    ]
    if opening_window.empty:
        opening_window = entry_bar
    opening_high = float(opening_window["high"].max())
    opening_low = float(opening_window["low"].min())
    post_120 = session[session["timestamp"].between(entry_ts, entry_ts + pd.Timedelta(minutes=120), inclusive="both")]
    if not post_120.empty:
        features[f"{prefix}_mfe_120m"] = float(post_120["high"].max() / entry_price - 1.0)
        features[f"{prefix}_mae_120m"] = float(post_120["low"].min() / entry_price - 1.0)
        features[f"{prefix}_opening_range_high_reclaim_120m_flag"] = int(post_120["close"].max() >= opening_high)
        features[f"{prefix}_opening_range_rejection_120m_flag"] = int(post_120["close"].iloc[-1] < opening_high)
        features[f"{prefix}_volume_decay_120m"] = _volume_decay(post_120)
    for horizon in HORIZONS_MINUTES:
        horizon_ts = entry_ts + pd.Timedelta(minutes=horizon)
        bars = session[session["timestamp"].between(entry_ts, horizon_ts, inclusive="both")]
        if bars.empty:
            features[f"{prefix}_ret_{horizon}m"] = pd.NA
            features[f"{prefix}_mae_{horizon}m"] = pd.NA
            features[f"{prefix}_mfe_{horizon}m"] = pd.NA
            features[f"{prefix}_vwap_fail_{horizon}m_flag"] = pd.NA
            continue
        last = bars.iloc[-1]
        features[f"{prefix}_ret_{horizon}m"] = float(last["close"] / entry_price - 1.0)
        features[f"{prefix}_mae_{horizon}m"] = float(bars["low"].min() / entry_price - 1.0)
        features[f"{prefix}_mfe_{horizon}m"] = float(bars["high"].max() / entry_price - 1.0)
        vwap = last.get("diagnostic_vwap")
        features[f"{prefix}_vwap_fail_{horizon}m_flag"] = int(pd.notna(vwap) and float(last["close"]) < float(vwap))
    return features


def signal_flags(row: dict[str, Any]) -> dict[str, int]:
    return {
        "early_adverse_60m_flag": int(_le(row.get("symbol_mae_60m"), -0.03)),
        "early_adverse_120m_flag": int(_le(row.get("symbol_mae_120m"), -0.03)),
        "vwap_fail_60m_flag": int(row.get("symbol_vwap_fail_60m_flag") == 1),
        "opening_rejection_120m_flag": int(row.get("symbol_opening_range_rejection_120m_flag") == 1),
        "relative_strength_fail_60m_flag": int(_le(row.get("relative_ret_vs_qqq_60m"), -0.01)),
        "volume_decay_120m_flag": int(_ge(row.get("symbol_volume_decay_120m"), 0.50)),
    }


def build_cohort_summary(path_panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for flag, group in path_panel.groupby("entry_reduce_failure_flag", sort=True):
        row = {
            "entry_reduce_failure_flag": int(flag),
            "cohort": "entry_reduce_failed" if int(flag) else "clean_entry",
            "lifecycle_count": int(len(group)),
            "avg_net_return_pct": float(group["net_return_from_entry"].mean() * 100.0),
            "win_rate": float(group["win_flag"].mean()),
        }
        for column in path_metric_columns(path_panel):
            row[f"{column}_mean"] = _mean(group, column)
            row[f"{column}_median"] = _median(group, column)
        rows.append(row)
    return pd.DataFrame(rows)


def build_signal_candidate_summary(path_panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    failed = path_panel[path_panel["entry_reduce_failure_flag"].eq(1)]
    clean = path_panel[path_panel["entry_reduce_failure_flag"].eq(0)]
    for signal in signal_columns():
        failed_rate = _mean(failed, signal)
        clean_rate = _mean(clean, signal)
        rows.append(
            {
                "signal_name": signal,
                "failed_trigger_rate": failed_rate,
                "clean_trigger_rate": clean_rate,
                "separation_rate": failed_rate - clean_rate,
                "failed_captured_count": int(pd.to_numeric(failed[signal], errors="coerce").fillna(0).sum()) if signal in failed else 0,
                "clean_false_alarm_count": int(pd.to_numeric(clean[signal], errors="coerce").fillna(0).sum()) if signal in clean else 0,
                "diagnostic_pass_flag": int(failed_rate >= 0.50 and failed_rate - clean_rate >= 0.20),
            }
        )
    return pd.DataFrame(rows).sort_values(["diagnostic_pass_flag", "separation_rate"], ascending=[False, False])


def build_state_signal_interaction_summary(path_panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    base_failure_rate = _mean(path_panel, "entry_reduce_failure_flag")
    state_columns = [
        "timing_state",
        "symbol_multiday_setup_state",
        "theme_regime_state_v4",
        "theme_id",
        "symbol",
    ]
    for left_idx, left_signal in enumerate(signal_columns()):
        for right_signal in signal_columns()[left_idx + 1 :]:
            triggered = path_panel[left_signal].fillna(0).astype(int).eq(1) & path_panel[right_signal].fillna(0).astype(int).eq(1)
            rows.append(_candidate_row("signal_combo", f"{left_signal}&{right_signal}", triggered, path_panel, base_failure_rate))
    for state_column in state_columns:
        for value, count in path_panel[state_column].astype(str).value_counts().items():
            if int(count) < 5:
                continue
            for signal in signal_columns():
                triggered = path_panel[state_column].astype(str).eq(str(value)) & path_panel[signal].fillna(0).astype(int).eq(1)
                rows.append(
                    _candidate_row(
                        "state_signal",
                        f"{state_column}={value}&{signal}",
                        triggered,
                        path_panel,
                        base_failure_rate,
                    )
                )
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame = frame[frame["trigger_count"].ge(5)].copy()
    frame["diagnostic_pass_flag"] = (
        frame["failure_rate"].ge(0.60) & frame["lift_vs_base"].ge(0.20) & frame["failed_capture_rate"].ge(0.08)
    ).astype(int)
    return frame.sort_values(
        ["diagnostic_pass_flag", "failure_rate", "failed_capture_rate", "trigger_count"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)


def build_quarter_signal_summary(path_panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for quarter, group in path_panel.groupby("quarter", sort=True):
        row = {
            "quarter": quarter,
            "lifecycle_count": int(len(group)),
            "avg_net_return_pct": float(group["net_return_from_entry"].mean() * 100.0),
            "entry_reduce_failure_rate": float(group["entry_reduce_failure_flag"].mean()),
        }
        for signal in signal_columns():
            row[f"{signal}_rate"] = _mean(group, signal)
        rows.append(row)
    return pd.DataFrame(rows)


def build_decisions(
    source_coverage: pd.DataFrame,
    path_panel: pd.DataFrame,
    signal_summary: pd.DataFrame,
    interaction_summary: pd.DataFrame,
) -> pd.DataFrame:
    assignment_symbols = source_coverage[source_coverage["symbol"].ne(REFERENCE_SYMBOL)].copy()
    coverage_pass = int(
        not assignment_symbols.empty and assignment_symbols["available_flag"].astype(int).eq(1).all()
    )
    path_pass = int(
        not path_panel.empty
        and path_panel["symbol_session_available_flag"].fillna(0).astype(int).mean() >= 0.90
        and path_panel["qqq_session_available_flag"].fillna(0).astype(int).mean() >= 0.90
    )
    simple_candidate_count = int(signal_summary["diagnostic_pass_flag"].sum()) if not signal_summary.empty else 0
    interaction_candidate_count = (
        int(interaction_summary["diagnostic_pass_flag"].sum()) if not interaction_summary.empty else 0
    )
    candidate_count = simple_candidate_count + interaction_candidate_count
    live_detectability_pass = int(path_pass and candidate_count >= 1)
    return pd.DataFrame(
        [
            {
                "task_id": TASK_ID,
                "decision": (
                    "PASS_LIVE_DETECTABLE_FAILURE_CANDIDATES_FOUND_NEEDS_OOS_RULE_TEST"
                    if live_detectability_pass
                    else "FAIL_LIVE_DETECTABLE_FAILURE_CANDIDATES_NOT_PROVEN"
                ),
                "pass_flag": live_detectability_pass,
                "source_coverage_pass_flag": coverage_pass,
                "path_coverage_pass_flag": path_pass,
                "simple_signal_candidate_count": simple_candidate_count,
                "interaction_signal_candidate_count": interaction_candidate_count,
                "diagnostic_signal_candidate_count": candidate_count,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "next_action": "Promote only diagnostic candidates into a no-label walk-forward reduce/exit simulation with cost stress.",
            }
        ]
    )


def render_report(
    source_coverage: pd.DataFrame,
    cohort_summary: pd.DataFrame,
    signal_summary: pd.DataFrame,
    interaction_summary: pd.DataFrame,
    quarter_summary: pd.DataFrame,
    decisions: pd.DataFrame,
) -> str:
    decision = decisions.iloc[0].to_dict()
    failed = cohort_summary[cohort_summary["entry_reduce_failure_flag"].eq(1)].iloc[0].to_dict()
    clean = cohort_summary[cohort_summary["entry_reduce_failure_flag"].eq(0)].iloc[0].to_dict()
    top_signals = signal_summary.head(5)
    top_interactions = interaction_summary.head(5)
    signal_lines = [
        (
            f"- {row['signal_name']}: failed {float(row['failed_trigger_rate']):.2%}, "
            f"clean {float(row['clean_trigger_rate']):.2%}, separation {float(row['separation_rate']):.2%}"
        )
        for _, row in top_signals.iterrows()
    ]
    interaction_lines = [
        (
            f"- {row['candidate_name']}: trigger {int(row['trigger_count'])}, "
            f"failure {float(row['failure_rate']):.2%}, lift {float(row['lift_vs_base']):.2%}, "
            f"capture {float(row['failed_capture_rate']):.2%}"
        )
        for _, row in top_interactions.iterrows()
    ]
    weak_quarters = quarter_summary.sort_values("avg_net_return_pct").head(4)
    quarter_lines = [
        (
            f"- {row['quarter']}: avg {float(row['avg_net_return_pct']):.2f}%, "
            f"entry-reduce {float(row['entry_reduce_failure_rate']):.2%}"
        )
        for _, row in weak_quarters.iterrows()
    ]
    source_available = int(source_coverage["available_flag"].sum())
    return "\n".join(
        [
            "# Task608G Live-Detectable Entry Failure Path Diagnostics",
            "",
            "## Decision Summary",
            "",
            f"- Verdict: {decision['decision']}",
            "- Strategy acceptance status: NOT_ACCEPTED",
            "- Deployment status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            f"- Source coverage: {source_available}/{len(source_coverage)} intraday symbols available.",
            f"- Clean entries: count {int(clean['lifecycle_count'])}, avg {float(clean['avg_net_return_pct']):.2f}%, win {float(clean['win_rate']):.2%}.",
            f"- Entry-reduce failed entries: count {int(failed['lifecycle_count'])}, avg {float(failed['avg_net_return_pct']):.2f}%, win {float(failed['win_rate']):.2%}.",
            f"- Diagnostic live signal candidates: {int(decision['diagnostic_signal_candidate_count'])}.",
            "- What changed: the loser label is now paired with pre/post-entry path evidence instead of only final PnL.",
            f"- Next action: {decision['next_action']}",
            "",
            "## Quant Expert Report",
            "",
            "- Data source and source readiness: Task509 OOS assignment panel plus `data/raw/us_intraday` OHLCV. QQQ is used only as a relative-strength reference.",
            "- Exact join keys: lifecycle rows are not re-matched. Intraday bars are selected by exact symbol and timestamp windows around the existing `entry_ts`.",
            "- Leakage audit: `entry_reduce_failure_flag` is used only as an evaluation cohort. It is not used to create entries or calculate signal candidates.",
            "- Split/OOS metrics: the input rows are Task509 walk-forward OOS assignments.",
            "- Failure decomposition: `entry_failure_path_panel.csv`, `clean_vs_failed_path_summary.csv`, `live_signal_candidate_summary.csv`, `state_signal_interaction_summary.csv`, and `quarter_live_signal_summary.csv`.",
            "- Cost/slippage stress where PnL changed: not applied here; this is path detectability only. Any future reduce rule must rerun cost stress.",
            "- Remaining blockers: diagnostic candidates are not accepted rules until no-label walk-forward reduce/exit simulation passes.",
            "",
            "Top diagnostic candidates:",
            *signal_lines,
            "",
            "Top state/path interaction candidates:",
            *interaction_lines,
            "",
            "Weak quarters:",
            *quarter_lines,
            "",
            "## No-Background Decision-Maker Report",
            "",
            "- What happened: we checked whether bad entries show warning signs soon after entry.",
            "- Why it matters: if the warning sign exists early, we can test a real reduce/exit engine. If not, entry-reduce remains only a hindsight label.",
            "- Whether this changes capital/deployment readiness: no. This is research evidence only.",
            "- Plain-language next step: take only the best warning signs and test them as live reduce rules out-of-sample.",
            "",
            "## Artifact Manifest",
            "",
            "- See `artifact_manifest.csv`.",
        ]
    ).rstrip() + "\n"


def path_metric_columns(frame: pd.DataFrame) -> list[str]:
    return [
        column
        for column in frame.columns
        if column.startswith(("symbol_ret_", "symbol_mae_", "symbol_mfe_", "relative_ret_vs_qqq_"))
    ] + signal_columns()


def signal_columns() -> list[str]:
    return [
        "early_adverse_60m_flag",
        "early_adverse_120m_flag",
        "vwap_fail_60m_flag",
        "opening_rejection_120m_flag",
        "relative_strength_fail_60m_flag",
        "volume_decay_120m_flag",
    ]


def _candidate_row(
    candidate_type: str,
    candidate_name: str,
    triggered: pd.Series,
    path_panel: pd.DataFrame,
    base_failure_rate: float,
) -> dict[str, Any]:
    trigger_count = int(triggered.sum())
    failed_mask = path_panel["entry_reduce_failure_flag"].eq(1)
    clean_mask = path_panel["entry_reduce_failure_flag"].eq(0)
    failure_rate = _mean(path_panel[triggered], "entry_reduce_failure_flag") if trigger_count else 0.0
    return {
        "candidate_type": candidate_type,
        "candidate_name": candidate_name,
        "trigger_count": trigger_count,
        "failure_rate": failure_rate,
        "lift_vs_base": failure_rate - base_failure_rate,
        "failed_capture_rate": _safe_div(int((triggered & failed_mask).sum()), int(failed_mask.sum())),
        "clean_false_alarm_count": int((triggered & clean_mask).sum()),
        "clean_false_alarm_rate": _safe_div(int((triggered & clean_mask).sum()), int(clean_mask.sum())),
    }


def _volume_decay(frame: pd.DataFrame) -> float:
    if len(frame) < 2:
        return 0.0
    midpoint = max(1, len(frame) // 2)
    first = float(frame.iloc[:midpoint]["volume"].mean())
    second = float(frame.iloc[midpoint:]["volume"].mean())
    if first <= 0:
        return 0.0
    return max(0.0, 1.0 - second / first)


def _mean(frame: pd.DataFrame, column: str) -> float:
    if frame.empty or column not in frame:
        return 0.0
    value = pd.to_numeric(frame[column], errors="coerce").mean()
    return 0.0 if pd.isna(value) else float(value)


def _median(frame: pd.DataFrame, column: str) -> float:
    if frame.empty or column not in frame:
        return 0.0
    value = pd.to_numeric(frame[column], errors="coerce").median()
    return 0.0 if pd.isna(value) else float(value)


def _le(value: object, threshold: float) -> bool:
    try:
        return pd.notna(value) and float(value) <= threshold
    except Exception:
        return False


def _ge(value: object, threshold: float) -> bool:
    try:
        return pd.notna(value) and float(value) >= threshold
    except Exception:
        return False


def _subtract(left: object, right: object) -> float | Any:
    try:
        if pd.isna(left) or pd.isna(right):
            return pd.NA
        return float(left) - float(right)
    except Exception:
        return pd.NA


def _safe_div(numerator: float, denominator: float) -> float:
    return float(numerator / denominator) if denominator else 0.0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task509-panel", type=Path, default=TASK509_PANEL)
    parser.add_argument("--intraday-dir", type=Path, default=INTRADAY_DIR)
    parser.add_argument("--out-dir", type=Path, default=REPORT_DIR)
    args = parser.parse_args()
    artifacts = build_task608g_live_detectable_entry_failure_path_diagnostics(
        task509_panel_path=args.task509_panel,
        intraday_dir=args.intraday_dir,
        out_dir=args.out_dir,
    )
    row = artifacts["task_608g_decision"].iloc[0]
    print(f"[TASK608G] decision={row['decision']} pass={int(row['pass_flag'])}")


if __name__ == "__main__":
    main()
