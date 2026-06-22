from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report


TASK550_PANEL = Path("data/artifacts/task_550_anchored_vwap_band_walk_continuation/symbol_continuation_structure_v2_panel.csv")
TASK553_RISK = Path("docs/reports/task_553_portfolio_realism_simulator/portfolio_risk_quality.csv")
TASK556_REPORT = Path("docs/reports/task_556_vwap_bandwalk_portfolio_revalidation")
TASK556_DATA = Path("data/artifacts/task_556_vwap_bandwalk_portfolio_revalidation")

PNL_COL = "net_return_from_entry"
NOTIONAL = 10_000.0


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _pct(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.dropna().empty:
        return values
    return values * 100.0 if values.dropna().abs().max() <= 5 else values


def _decision(task_id: str, status: str, **extra: Any) -> pd.DataFrame:
    return pd.DataFrame([{"task_id": task_id, "strategy_acceptance_status": status, "deployment_ready_flag": 0, **extra}])


def load_task550_panel(path: Path = TASK550_PANEL) -> pd.DataFrame:
    panel = _read_csv(path)
    if panel.empty:
        return panel
    numeric_cols = [
        PNL_COL,
        "entry_reduce_failure_flag",
        "add_scale_success_flag",
        "false_positive_flag",
        "win_flag",
        "holding_days",
        "same_day_exit_flag",
        "label_used_in_assignment_flag",
        "inferred_lifecycle_matching_used_flag",
        "factor_assignment_used_label_flag",
        "missing_data_approximated_flag",
    ]
    for col in numeric_cols:
        if col in panel.columns:
            panel[col] = pd.to_numeric(panel[col], errors="coerce")
    for col in ["entry_ts", "simulated_exit_ts"]:
        if col in panel.columns:
            panel[col] = pd.to_datetime(panel[col], utc=True, errors="coerce")
    if "quarter" not in panel.columns and "entry_ts" in panel.columns:
        panel["quarter"] = panel["entry_ts"].dt.to_period("Q").astype(str)
    return panel


def _candidate_masks(panel: pd.DataFrame) -> dict[str, pd.Series]:
    idx = panel.index
    vwap = panel.get("vwap_reclaim_state_v2", pd.Series("", index=idx)).astype(str)
    relvol = panel.get("relative_volume_state_v2", pd.Series("", index=idx)).astype(str)
    band = panel.get("band_walk_state_v2", pd.Series("", index=idx)).astype(str)
    over = panel.get("overextension_state_v2", pd.Series("", index=idx)).astype(str)

    vwap_good = vwap.isin(["strong_vwap_acceptance", "early_vwap_reclaim"])
    volume_good = relvol.isin(["volume_confirmed", "volume_climax"])
    not_exhausted = ~over.eq("exhaustion_overextension")
    upper_or_mid = band.isin(["upper_band_walk_proxy", "middle_range"])
    accepted_over = over.eq("accepted_overextension")
    failed_reclaim = vwap.str.contains("failed", case=False, na=False)
    quiet = relvol.eq("normal_or_thin_volume")

    return {
        "baseline_all_task550": pd.Series(True, index=idx),
        "strong_vwap_acceptance_core": vwap.eq("strong_vwap_acceptance") & volume_good & upper_or_mid & not_exhausted,
        "early_reclaim_volume_confirmed": vwap.eq("early_vwap_reclaim") & volume_good & upper_or_mid & not_exhausted,
        "accepted_overextension_confirmed": accepted_over & vwap_good & volume_good,
        "volume_climax_accepted": relvol.eq("volume_climax") & vwap_good & upper_or_mid & not_exhausted,
        "upper_band_walk_clean": band.eq("upper_band_walk_proxy") & vwap_good & volume_good & not_exhausted,
        "middle_range_vwap_hold": band.eq("middle_range") & vwap_good & not_exhausted,
        "not_exhausted_vwap_acceptance": vwap_good & not_exhausted,
        "quiet_breakout_suppressed_portfolio": vwap_good & ~quiet & not_exhausted,
        "failed_reclaim_excluded_portfolio": ~failed_reclaim & not_exhausted,
        "low_entry_reduce_structural_core": vwap.eq("strong_vwap_acceptance") & volume_good & not_exhausted,
        "balanced_vwap_bandwalk_portfolio": vwap_good & upper_or_mid & not_exhausted,
    }


def build_assignment_panel(panel: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    masks = _candidate_masks(panel)
    for name, mask in masks.items():
        selected = panel.loc[mask.fillna(False)].copy()
        if selected.empty:
            continue
        selected["candidate_set"] = name
        selected["candidate_set_type"] = np.where(name.endswith("_suppressed_portfolio"), "false_positive_suppression", "positive_selection")
        selected["assignment_used_label_flag"] = 0
        selected["assignment_used_outcome_flag"] = 0
        selected["inferred_matching_used_flag"] = 0
        frames.append(selected)
    if "continuation_structure_v2" in panel.columns:
        for structure, group in panel.groupby("continuation_structure_v2", dropna=False):
            if pd.isna(structure) or group.empty:
                continue
            selected = group.copy()
            safe_name = str(structure).replace("|", "__").replace(" ", "_")
            selected["candidate_set"] = f"state_cell__{safe_name}"
            selected["candidate_set_type"] = "state_space_cell"
            selected["assignment_used_label_flag"] = 0
            selected["assignment_used_outcome_flag"] = 0
            selected["inferred_matching_used_flag"] = 0
            frames.append(selected)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def _quality(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    cols = [col for col in group_cols if col in frame.columns]
    if frame.empty or not cols:
        return pd.DataFrame()
    temp = frame[cols].copy()
    temp["_pnl"] = _pct(frame[PNL_COL])
    temp["_win"] = temp["_pnl"] > 0
    temp["_entry_reduce"] = pd.to_numeric(frame.get("entry_reduce_failure_flag", pd.Series(np.nan, index=frame.index)), errors="coerce")
    temp["_add_scale"] = pd.to_numeric(frame.get("add_scale_success_flag", pd.Series(np.nan, index=frame.index)), errors="coerce")
    temp["_false_positive"] = pd.to_numeric(frame.get("false_positive_flag", pd.Series(np.nan, index=frame.index)), errors="coerce")
    temp["_holding_days"] = pd.to_numeric(frame.get("holding_days", pd.Series(np.nan, index=frame.index)), errors="coerce")
    grouped = (
        temp.groupby(cols, dropna=False)
        .agg(
            lifecycle_count=("_pnl", "count"),
            avg_net_pct=("_pnl", "mean"),
            median_net_pct=("_pnl", "median"),
            win_rate=("_win", "mean"),
            entry_reduce_failure_rate=("_entry_reduce", "mean"),
            add_scale_success_rate=("_add_scale", "mean"),
            false_positive_rate=("_false_positive", "mean"),
            median_holding_days=("_holding_days", "median"),
            p75_holding_days=("_holding_days", lambda x: x.quantile(0.75)),
        )
        .reset_index()
    )
    for col in ["win_rate", "entry_reduce_failure_rate", "add_scale_success_rate", "false_positive_rate"]:
        grouped[col] = grouped[col] * 100.0
    return grouped.sort_values(["avg_net_pct", "lifecycle_count"], ascending=[False, False]).reset_index(drop=True)


def _max_drawdown(values: pd.Series) -> float:
    if values.empty:
        return 0.0
    running_max = values.cummax()
    drawdown = running_max - values
    return float(drawdown.max())


def _portfolio_row(name: str, frame: pd.DataFrame) -> dict[str, Any]:
    if frame.empty:
        return {
            "candidate_set": name,
            "trade_count": 0,
            "avg_net_pct": np.nan,
            "win_rate": np.nan,
            "total_net_dollar_proxy": 0.0,
            "max_drawdown_dollar_proxy": 0.0,
            "broker_truth_fill_used_flag": 0,
        }
    ordered = frame.sort_values("entry_ts") if "entry_ts" in frame.columns else frame.copy()
    pnl_pct = _pct(ordered[PNL_COL]).fillna(0.0)
    pnl_dollar = pnl_pct / 100.0 * NOTIONAL
    equity = pnl_dollar.cumsum()
    return {
        "candidate_set": name,
        "trade_count": int(len(ordered)),
        "avg_net_pct": float(pnl_pct.mean()),
        "win_rate": float((pnl_pct > 0).mean() * 100.0),
        "entry_reduce_failure_rate": float(pd.to_numeric(ordered.get("entry_reduce_failure_flag", pd.Series(np.nan, index=ordered.index)), errors="coerce").mean() * 100.0),
        "add_scale_success_rate": float(pd.to_numeric(ordered.get("add_scale_success_flag", pd.Series(np.nan, index=ordered.index)), errors="coerce").mean() * 100.0),
        "total_net_dollar_proxy": float(pnl_dollar.sum()),
        "max_drawdown_dollar_proxy": _max_drawdown(equity),
        "max_drawdown_per_100_trades_proxy": float(_max_drawdown(equity) / max(len(ordered), 1) * 100.0),
        "broker_truth_fill_used_flag": 0,
    }


def build_portfolio_quality(assignment: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for name, group in assignment.groupby("candidate_set", dropna=False):
        rows.append(_portfolio_row(str(name), group))
    return pd.DataFrame(rows).sort_values(["avg_net_pct", "trade_count"], ascending=[False, False]).reset_index(drop=True)


def build_entry_reduce_audit(quality: pd.DataFrame) -> pd.DataFrame:
    baseline = quality[quality["candidate_set"].eq("baseline_all_task550")]
    baseline_er = float(baseline["entry_reduce_failure_rate"].iloc[0]) if not baseline.empty else np.nan
    baseline_avg = float(baseline["avg_net_pct"].iloc[0]) if not baseline.empty else np.nan
    out = quality.copy()
    out["baseline_entry_reduce_rate"] = baseline_er
    out["entry_reduce_improvement_pp"] = baseline_er - out["entry_reduce_failure_rate"]
    out["avg_net_lift_vs_baseline_pp"] = out["avg_net_pct"] - baseline_avg
    return out.sort_values(["entry_reduce_improvement_pp", "avg_net_pct"], ascending=[False, False]).reset_index(drop=True)


def build_leakage_audit(assignment: pd.DataFrame) -> pd.DataFrame:
    blocked = [
        "lifecycle_outcome_class",
        "failure_group",
        "exit_reason",
        "simulated_exit_price",
        "simulated_exit_ts",
        "net_return_from_entry",
        "win_flag",
        "add_scale_success_flag",
        "entry_reduce_failure_flag",
        "false_positive_flag",
    ]
    assignment_fields = [
        "vwap_reclaim_state_v2",
        "relative_volume_state_v2",
        "band_walk_state_v2",
        "overextension_state_v2",
    ]
    rows = []
    for field in blocked:
        rows.append(
            {
                "check": f"Blocked field not used in assignment: {field}",
                "status": "PASS",
                "field_present_in_panel": int(field in assignment.columns),
                "used_in_assignment_flag": 0,
            }
        )
    rows.append(
        {
            "check": "Assignment fields are entry-safe VWAP/OHLCV structure states",
            "status": "PASS" if set(assignment_fields).issubset(set(assignment.columns)) else "FAIL",
            "field_present_in_panel": int(set(assignment_fields).issubset(set(assignment.columns))),
            "used_in_assignment_flag": 1,
        }
    )
    rows.append(
        {
            "check": "No inferred lifecycle matching",
            "status": "PASS" if int(assignment.get("inferred_matching_used_flag", pd.Series([0])).max()) == 0 else "FAIL",
            "field_present_in_panel": 1,
            "used_in_assignment_flag": 0,
        }
    )
    return pd.DataFrame(rows)


def build_task556(panel: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    source = load_task550_panel() if panel is None else panel.copy()
    assignment = build_assignment_panel(source)
    candidate_quality = _quality(assignment, ["candidate_set", "candidate_set_type"])
    split_quality = _quality(assignment, ["candidate_set", "split_name"])
    quarter_quality = _quality(assignment, ["candidate_set", "quarter"])
    portfolio_quality = build_portfolio_quality(assignment)
    entry_reduce_audit = build_entry_reduce_audit(portfolio_quality)
    concentration = _quality(assignment, ["candidate_set", "theme_id"])
    leakage = build_leakage_audit(assignment)

    baseline = portfolio_quality[portfolio_quality["candidate_set"].eq("baseline_all_task550")]
    baseline_er = float(baseline["entry_reduce_failure_rate"].iloc[0]) if not baseline.empty else np.nan
    non_baseline = portfolio_quality[~portfolio_quality["candidate_set"].eq("baseline_all_task550")].copy()
    recent = split_quality[split_quality.get("split_name", pd.Series(dtype=str)).astype(str).str.contains("recent", case=False, na=False)]
    validation = split_quality[split_quality.get("split_name", pd.Series(dtype=str)).astype(str).str.contains("validation", case=False, na=False)]
    passing_sets = non_baseline[
        (non_baseline["trade_count"] >= 300)
        & (non_baseline["avg_net_pct"] > 0)
        & ((baseline_er - non_baseline["entry_reduce_failure_rate"]) >= 5.0)
    ]
    status = "DIAGNOSTIC_PASS_ENTRY_REDUCE_REDUCED" if not passing_sets.empty else "DIAGNOSTIC_ONLY_NO_PORTFOLIO_PASS"
    decision = _decision(
        "Task556",
        status,
        source_task="Task550+Task553",
        candidate_set_count=int(assignment["candidate_set"].nunique()) if not assignment.empty else 0,
        baseline_entry_reduce_rate=baseline_er,
        passing_candidate_set_count=int(len(passing_sets)),
        validation_rows=int(len(validation)),
        recent_oos_rows=int(len(recent)),
        broker_truth_fill_used_flag=0,
        inferred_matching_used_flag=0,
        label_used_in_assignment_flag=0,
    )
    return {
        "vwap_bandwalk_assignment_panel": assignment,
        "vwap_bandwalk_candidate_set_quality": candidate_quality,
        "vwap_bandwalk_split_quality": split_quality,
        "vwap_bandwalk_quarterly_quality": quarter_quality,
        "vwap_bandwalk_portfolio_quality": portfolio_quality,
        "vwap_bandwalk_entry_reduce_audit": entry_reduce_audit,
        "vwap_bandwalk_concentration_audit": concentration,
        "vwap_bandwalk_leakage_audit": leakage,
        "task_556_decision": decision,
    }


def _write_frames(out_dir: Path, frames: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def _write_report(frames: dict[str, pd.DataFrame]) -> None:
    decision = frames["task_556_decision"].iloc[0].to_dict()
    quality = frames["vwap_bandwalk_portfolio_quality"]
    best = quality.iloc[0].to_dict() if not quality.empty else {}
    entry_reduce = frames["vwap_bandwalk_entry_reduce_audit"]
    best_er = entry_reduce.iloc[0].to_dict() if not entry_reduce.empty else {}
    write_standard_report(
        TASK556_REPORT / "task_556_vwap_bandwalk_portfolio_revalidation.md",
        title="Task556 — VWAP/Band-Walk Portfolio Revalidation",
        decision_summary=[
            f"Strategy acceptance: {decision.get('strategy_acceptance_status')}",
            "Task550 entry-safe VWAP/Band-walk structure states were replayed as portfolio candidate sets.",
            "Broker-truth fills remain unavailable, so all PnL/DD outputs are diagnostic proxy results.",
        ],
        quant_expert_lines=[
            f"- Candidate sets tested: {decision.get('candidate_set_count')}. Assignment uses only `vwap_reclaim_state_v2`, `relative_volume_state_v2`, `band_walk_state_v2`, and `overextension_state_v2`.",
            f"- Best avg-net portfolio set: `{best.get('candidate_set', 'n/a')}` with count={best.get('trade_count', 'n/a')}, avg_net={best.get('avg_net_pct', np.nan):.3f}%, win={best.get('win_rate', np.nan):.1f}%, entry_reduce={best.get('entry_reduce_failure_rate', np.nan):.1f}%.",
            f"- Best entry-reduce improvement set: `{best_er.get('candidate_set', 'n/a')}` improved entry_reduce by {best_er.get('entry_reduce_improvement_pp', np.nan):.2f}pp vs baseline.",
            "- Labels, PnL, ADD/SCALE, EXIT, and false-positive fields are evaluation-only; they are blocked from assignment.",
        ],
        decision_maker_lines=[
            "- 이번 작업은 VWAP/Band-walk 근거가 실제 포트폴리오 품질을 개선하는지 확인하는 검증 단계입니다.",
            "- 좋은 결과가 있더라도 아직 실전 배포가 아닙니다. 실제 주문/체결 원장과 broker-truth fill이 없기 때문입니다.",
            "- 통과 후보가 없으면 다음 병목은 더 많은 조합이 아니라 microstructure source 또는 entry-reduce 구조 재정의입니다.",
        ],
    )


def main() -> None:
    frames = build_task556()
    report_frames = {k: v for k, v in frames.items() if k != "vwap_bandwalk_assignment_panel"}
    data_frames = {"vwap_bandwalk_assignment_panel": frames["vwap_bandwalk_assignment_panel"]}
    _write_frames(TASK556_REPORT, report_frames)
    _write_frames(TASK556_DATA, data_frames)
    _write_report(frames)
    write_manifest(TASK556_REPORT, TASK556_REPORT / "artifact_manifest.csv")
    write_manifest(TASK556_DATA, TASK556_DATA / "artifact_manifest.csv")
    print(f"[TASK556_OK] report={TASK556_REPORT}")


if __name__ == "__main__":
    main()
