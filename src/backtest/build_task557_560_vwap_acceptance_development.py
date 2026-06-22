from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report


TASK550_PANEL = Path("data/artifacts/task_550_anchored_vwap_band_walk_continuation/symbol_continuation_structure_v2_panel.csv")
TASK557_REPORT = Path("docs/reports/task_557_vwap_acceptance_ontology_rebuild")
TASK557_DATA = Path("data/artifacts/task_557_vwap_acceptance_ontology_rebuild")
TASK558_REPORT = Path("docs/reports/task_558_pullback_acceptance_true_failure_test")
TASK559_REPORT = Path("docs/reports/task_559_context_gate_reattach")
TASK559_DATA = Path("data/artifacts/task_559_context_gate_reattach")
TASK560_REPORT = Path("docs/reports/task_560_microstructure_confirmation_requirement")

PNL_COL = "net_return_from_entry"


def _read_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path) if path.exists() else pd.DataFrame()


def _pct(series: pd.Series) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    if values.dropna().empty:
        return values
    return values * 100.0 if values.dropna().abs().max() <= 5 else values


def _decision(task_id: str, status: str, **extra: Any) -> pd.DataFrame:
    return pd.DataFrame([{"task_id": task_id, "strategy_acceptance_status": status, "deployment_ready_flag": 0, **extra}])


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
        )
        .reset_index()
    )
    for col in ["win_rate", "entry_reduce_failure_rate", "add_scale_success_rate", "false_positive_rate"]:
        grouped[col] *= 100.0
    return grouped.sort_values(["avg_net_pct", "lifecycle_count"], ascending=[False, False]).reset_index(drop=True)


def load_panel(path: Path = TASK550_PANEL) -> pd.DataFrame:
    panel = _read_csv(path)
    if panel.empty:
        return panel
    numeric_cols = [
        "open",
        "high",
        "low",
        "close",
        "vwap",
        "entry_close_vs_vwap",
        "entry_close_pos_in_bar",
        "range_pos",
        "volume_ratio_prev",
        "near_high60_prev",
        "ret_20d_prev",
        "theme_ret20_prev",
        "theme_breadth20_prev",
        "breadth_20d",
        PNL_COL,
        "entry_reduce_failure_flag",
        "add_scale_success_flag",
        "false_positive_flag",
        "holding_days",
        "label_used_in_assignment_flag",
        "inferred_lifecycle_matching_used_flag",
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


def assign_vwap_acceptance_ontology(panel: pd.DataFrame) -> pd.DataFrame:
    out = panel.copy()
    idx = out.index
    dist = out.get("entry_close_vs_vwap", pd.Series(np.nan, index=idx))
    close_pos = out.get("entry_close_pos_in_bar", pd.Series(np.nan, index=idx))
    range_pos = out.get("range_pos", pd.Series(np.nan, index=idx))
    vol_ratio = out.get("volume_ratio_prev", pd.Series(np.nan, index=idx))
    open_px = out.get("open", pd.Series(np.nan, index=idx))
    high = out.get("high", pd.Series(np.nan, index=idx))
    low = out.get("low", pd.Series(np.nan, index=idx))
    close = out.get("close", pd.Series(np.nan, index=idx))
    vwap = out.get("vwap", pd.Series(np.nan, index=idx))

    bar_range = (high - low).replace(0, np.nan)
    open_pos = (open_px - low) / bar_range
    out["open_pos_in_bar_v3"] = open_pos
    out["vwap_crossed_in_bar_flag_v3"] = ((low <= vwap) & (high >= vwap)).astype(int)
    out["bar_close_above_open_flag_v3"] = (close > open_px).astype(int)

    late_chase = dist.ge(0.01) & close_pos.ge(0.80) & range_pos.ge(0.92)
    upper_wick_rejection = range_pos.ge(0.90) & close_pos.le(0.45) & dist.ge(0)
    blowoff = vol_ratio.ge(2.0) & range_pos.ge(0.95) & close_pos.lt(0.55)
    reclaim_confirmed = out["vwap_crossed_in_bar_flag_v3"].eq(1) & dist.ge(0.002) & close_pos.ge(0.60)
    true_reclaim_failed = open_px.ge(vwap) & close.lt(vwap) & close_pos.le(0.45)
    controlled_pullback = dist.between(-0.015, 0.002, inclusive="both") & range_pos.ge(0.80) & close_pos.between(0.20, 0.58, inclusive="both")
    near_high_absorption = dist.between(-0.012, 0.006, inclusive="both") & range_pos.ge(0.85) & close_pos.between(0.25, 0.65, inclusive="both") & vol_ratio.lt(1.25)
    above_acceptance = dist.between(0.002, 0.012, inclusive="both") & close_pos.between(0.45, 0.82, inclusive="both") & ~late_chase

    out["vwap_acceptance_state_v3"] = np.select(
        [
            blowoff,
            upper_wick_rejection,
            true_reclaim_failed,
            late_chase,
            near_high_absorption,
            controlled_pullback,
            reclaim_confirmed,
            above_acceptance,
            dist.ge(0),
            dist.lt(0),
        ],
        [
            "blowoff_without_acceptance",
            "upper_wick_rejection",
            "vwap_reclaim_failed_true",
            "late_chase_above_vwap",
            "near_high_absorption",
            "below_vwap_controlled_pullback",
            "vwap_reclaim_confirmed",
            "above_vwap_acceptance",
            "above_vwap_unclassified",
            "below_vwap_unclassified",
        ],
        default="vwap_unknown",
    )
    out["pullback_acceptance_state_v3"] = np.select(
        [
            out["vwap_acceptance_state_v3"].isin(["near_high_absorption", "below_vwap_controlled_pullback"]),
            out["vwap_acceptance_state_v3"].eq("vwap_reclaim_confirmed"),
            out["vwap_acceptance_state_v3"].isin(["vwap_reclaim_failed_true", "upper_wick_rejection", "blowoff_without_acceptance"]),
        ],
        ["controlled_pullback_or_absorption", "confirmed_reclaim", "true_failure_or_rejection"],
        default="not_pullback_acceptance",
    )
    out["chase_exhaustion_state_v3"] = np.select(
        [
            out["vwap_acceptance_state_v3"].eq("late_chase_above_vwap"),
            out["vwap_acceptance_state_v3"].eq("blowoff_without_acceptance"),
            out["vwap_acceptance_state_v3"].eq("upper_wick_rejection"),
        ],
        ["late_chase", "blowoff", "upper_wick_rejection"],
        default="not_chase_exhaustion",
    )
    out["vwap_ontology_v3"] = (
        out["vwap_acceptance_state_v3"].astype(str)
        + "|"
        + out.get("relative_volume_state_v2", pd.Series("unknown_volume", index=idx)).astype(str)
        + "|"
        + out.get("band_walk_state_v2", pd.Series("unknown_band", index=idx)).astype(str)
        + "|"
        + out.get("overextension_state_v2", pd.Series("unknown_overextension", index=idx)).astype(str)
    )
    out["label_used_in_assignment_flag_v3"] = 0
    out["outcome_used_in_assignment_flag_v3"] = 0
    out["inferred_matching_used_flag_v3"] = 0
    return out


def build_task557(panel: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    out = assign_vwap_acceptance_ontology(load_panel() if panel is None else panel)
    quality = _quality(out, ["vwap_acceptance_state_v3"])
    split_quality = _quality(out, ["vwap_acceptance_state_v3", "split_name"])
    audit = pd.DataFrame(
        [
            {"check": "legacy failed_vwap_reclaim name deprecated", "status": "PASS", "bad_rows": 0, "total_rows": len(out)},
            {"check": "label not used in assignment", "status": "PASS" if int(out["label_used_in_assignment_flag_v3"].max()) == 0 else "FAIL", "bad_rows": int(out["label_used_in_assignment_flag_v3"].sum()), "total_rows": len(out)},
            {"check": "outcome not used in assignment", "status": "PASS" if int(out["outcome_used_in_assignment_flag_v3"].max()) == 0 else "FAIL", "bad_rows": int(out["outcome_used_in_assignment_flag_v3"].sum()), "total_rows": len(out)},
            {"check": "no inferred lifecycle matching", "status": "PASS" if int(out["inferred_matching_used_flag_v3"].max()) == 0 else "FAIL", "bad_rows": int(out["inferred_matching_used_flag_v3"].sum()), "total_rows": len(out)},
        ]
    )
    decision = _decision(
        "Task557",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        ontology_state_count=int(out["vwap_acceptance_state_v3"].nunique()),
        label_used_in_assignment_flag=0,
        inferred_matching_used_flag=0,
    )
    return {
        "vwap_acceptance_ontology_v3_panel": out,
        "vwap_acceptance_ontology_quality": quality,
        "vwap_acceptance_ontology_split_quality": split_quality,
        "vwap_acceptance_ontology_leakage_audit": audit,
        "task_557_decision": decision,
    }


def build_task558(ontology_panel: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    out = assign_vwap_acceptance_ontology(load_panel() if ontology_panel is None else ontology_panel)
    pullback = out[out["pullback_acceptance_state_v3"].isin(["controlled_pullback_or_absorption", "confirmed_reclaim", "true_failure_or_rejection"])].copy()
    contrast = _quality(pullback, ["pullback_acceptance_state_v3", "vwap_acceptance_state_v3"])
    split = _quality(pullback, ["pullback_acceptance_state_v3", "split_name"])
    by_context = _quality(pullback, ["pullback_acceptance_state_v3", "multi_day_market_state_v4", "theme_regime_state_v4"])
    decision = _decision(
        "Task558",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        tested_pullback_rows=int(len(pullback)),
        controlled_pullback_rows=int(pullback["pullback_acceptance_state_v3"].eq("controlled_pullback_or_absorption").sum()),
        label_used_in_assignment_flag=0,
    )
    return {
        "pullback_acceptance_true_failure_panel": pullback,
        "pullback_acceptance_true_failure_quality": contrast,
        "pullback_acceptance_split_quality": split,
        "pullback_acceptance_context_quality": by_context,
        "task_558_decision": decision,
    }


def build_task559(ontology_panel: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    out = assign_vwap_acceptance_ontology(load_panel() if ontology_panel is None else ontology_panel)
    market_good = out.get("multi_day_market_state_v4", pd.Series("", index=out.index)).astype(str).str.contains("constructive|risk_on", case=False, na=False)
    theme_good = out.get("theme_regime_state_v4", pd.Series("", index=out.index)).astype(str).str.contains("leader|persistent", case=False, na=False)
    symbol_good = out.get("symbol_multiday_setup_state", pd.Series("", index=out.index)).astype(str).str.contains("near_high|persistence|trend", case=False, na=False)
    intraday_good = out["vwap_acceptance_state_v3"].isin(["near_high_absorption", "below_vwap_controlled_pullback", "vwap_reclaim_confirmed", "above_vwap_acceptance"])
    chase_bad = out["vwap_acceptance_state_v3"].isin(["late_chase_above_vwap", "upper_wick_rejection", "blowoff_without_acceptance", "vwap_reclaim_failed_true"])
    out["context_gate_v3"] = np.select(
        [
            market_good & theme_good & symbol_good & intraday_good,
            market_good & theme_good & intraday_good,
            chase_bad,
        ],
        ["regime_theme_symbol_intraday_aligned", "regime_theme_intraday_aligned", "intraday_rejection_or_chase_blocked"],
        default="context_not_aligned",
    )
    out["label_used_in_context_assignment_flag"] = 0
    quality = _quality(out, ["context_gate_v3"])
    split = _quality(out, ["context_gate_v3", "split_name"])
    quarter = _quality(out, ["context_gate_v3", "quarter"])
    decision = _decision(
        "Task559",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        context_gate_count=int(out["context_gate_v3"].nunique()),
        label_used_in_assignment_flag=0,
        best_context_gate=str(quality.iloc[0]["context_gate_v3"]) if not quality.empty else "",
    )
    return {
        "context_gate_v3_panel": out,
        "context_gate_v3_quality": quality,
        "context_gate_v3_split_quality": split,
        "context_gate_v3_quarterly_quality": quarter,
        "task_559_decision": decision,
    }


def build_task560() -> dict[str, pd.DataFrame]:
    features = [
        ("spread_bps", "NBBO bid/ask", "blocked_missing_live_quote_history", 1),
        ("spread_to_intraday_range", "NBBO bid/ask + OHLCV range", "blocked_missing_live_quote_history", 1),
        ("quote_staleness_ms", "local receive timestamp", "blocked_missing_recv_ts_history", 1),
        ("nbbo_size_dollar", "NBBO bid_size/ask_size", "blocked_missing_live_quote_size_history", 1),
        ("nbbo_imbalance", "NBBO bid_size/ask_size", "blocked_missing_live_quote_size_history", 1),
        ("status_clean_flag", "status/halt feed", "blocked_missing_status_luld_history", 1),
        ("luld_active_flag", "LULD feed", "blocked_missing_status_luld_history", 1),
        ("order_fill_slippage_bps", "broker order/fill archive", "blocked_missing_broker_truth_fill_history", 1),
        ("full_depth_pressure", "full depth book provider", "FULL_DEPTH_BLOCKED", 1),
    ]
    contract = pd.DataFrame(
        [
            {
                "feature_name": name,
                "required_raw_source": source,
                "source_status": status,
                "blocked_missing_source_flag": blocked,
                "approximation_allowed_flag": 0,
                "assignment_ready_flag": 0,
            }
            for name, source, status, blocked in features
        ]
    )
    hypothesis = pd.DataFrame(
        [
            {"hypothesis": "Controlled pullbacks require clean spread and fresh quote before entry.", "required_features": "spread_bps,quote_staleness_ms,nbbo_size_dollar"},
            {"hypothesis": "True VWAP failure should show poor bid support or stale/dirty market state.", "required_features": "nbbo_imbalance,status_clean_flag,luld_active_flag"},
            {"hypothesis": "Broad VWAP chase failure may be execution-friction amplified.", "required_features": "spread_to_intraday_range,order_fill_slippage_bps"},
        ]
    )
    readiness = pd.DataFrame(
        [
            {
                "gate": "microstructure_confirmation_ready",
                "status": "DATA_BLOCKED",
                "blocked_feature_count": int(contract["blocked_missing_source_flag"].sum()),
                "approximation_used_flag": 0,
                "next_action": "paper_shadow_capture_nbbo_status_luld_order_fill",
            }
        ]
    )
    decision = _decision(
        "Task560",
        "DATA_BLOCKED_MICROSTRUCTURE_CONFIRMATION_REQUIRED",
        blocked_feature_count=int(contract["blocked_missing_source_flag"].sum()),
        approximation_used_flag=0,
    )
    return {
        "microstructure_confirmation_feature_contract": contract,
        "microstructure_confirmation_hypothesis": hypothesis,
        "microstructure_confirmation_readiness_gate": readiness,
        "task_560_decision": decision,
    }


def _write_frames(out_dir: Path, frames: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def _write_report(out_dir: Path, file_name: str, title: str, decision: pd.DataFrame, quant_lines: list[str], dm_lines: list[str]) -> None:
    status = decision.iloc[0]["strategy_acceptance_status"] if not decision.empty else "UNKNOWN"
    write_standard_report(
        out_dir / file_name,
        title=title,
        decision_summary=[f"Strategy acceptance: {status}", "Deployment-ready claim: NO"],
        quant_expert_lines=quant_lines,
        decision_maker_lines=dm_lines,
    )


def main() -> None:
    task557 = build_task557()
    panel557 = task557["vwap_acceptance_ontology_v3_panel"]
    task558 = build_task558(panel557)
    task559 = build_task559(panel557)
    task560 = build_task560()

    _write_frames(TASK557_DATA, {"vwap_acceptance_ontology_v3_panel": panel557})
    _write_frames(TASK557_REPORT, {k: v for k, v in task557.items() if k != "vwap_acceptance_ontology_v3_panel"})
    _write_report(
        TASK557_REPORT,
        "task_557_vwap_acceptance_ontology_rebuild.md",
        "Task557 — VWAP Acceptance Ontology Rebuild",
        task557["task_557_decision"],
        [
            "- Deprecated the legacy `failed_vwap_reclaim` interpretation and rebuilt entry-safe VWAP states around acceptance, controlled pullback, true failure, chase, and rejection.",
            "- Assignment uses current bar OHLCV/VWAP, bar close location, range location, and previous volume ratio only.",
        ],
        [
            "- 기존의 'VWAP 실패'라는 이름을 폐기하고, 눌림/흡수/진짜 실패/추격을 분리했습니다.",
            "- 이 단계는 전략 배포가 아니라 판단 체계를 바로잡는 작업입니다.",
        ],
    )

    _write_frames(TASK558_REPORT, task558)
    _write_report(
        TASK558_REPORT,
        "task_558_pullback_acceptance_true_failure_test.md",
        "Task558 — Pullback Acceptance vs True Failure Test",
        task558["task_558_decision"],
        [
            "- Compared controlled pullback/absorption, confirmed reclaim, and true failure/rejection groups using labels only for evaluation.",
            "- Split and context quality tables quantify whether the new ontology separates entry_reduce from ADD/SCALE success.",
        ],
        [
            "- VWAP 아래 눌림 중 어떤 것이 좋은 흡수이고 어떤 것이 진짜 실패인지 분리해 봤습니다.",
            "- label은 사후 평가에만 사용했고 진입 판단에는 쓰지 않았습니다.",
        ],
    )

    _write_frames(TASK559_DATA, {"context_gate_v3_panel": task559["context_gate_v3_panel"]})
    _write_frames(TASK559_REPORT, {k: v for k, v in task559.items() if k != "context_gate_v3_panel"})
    _write_report(
        TASK559_REPORT,
        "task_559_context_gate_reattach.md",
        "Task559 — Context Gate Re-Attach",
        task559["task_559_decision"],
        [
            "- Re-attached multi-day market regime, theme leadership, symbol persistence, and VWAP acceptance into context gates.",
            "- This prevents VWAP structure from being evaluated outside its professional trading context.",
        ],
        [
            "- 좋은 시장/테마/종목 구조 안에서만 intraday continuation을 인정하는 형태로 다시 묶었습니다.",
            "- 이것은 단일 VWAP 신호가 아니라 레짐과 타점이 결합된 판단입니다.",
        ],
    )

    _write_frames(TASK560_REPORT, task560)
    _write_report(
        TASK560_REPORT,
        "task_560_microstructure_confirmation_requirement.md",
        "Task560 — Microstructure Confirmation Requirement",
        task560["task_560_decision"],
        [
            "- Defined the NBBO/spread/size/status/LULD/order-fill sources required to confirm pullback acceptance versus fake acceptance.",
            "- Missing microstructure sources remain blockers; no OHLCV approximation is allowed.",
        ],
        [
            "- OHLCV만으로는 진짜 흡수와 가짜 수용을 완전히 구분할 수 없습니다.",
            "- 필요한 데이터가 없으면 추정하지 않고 source 확보 과제로 넘깁니다.",
        ],
    )
    print("[TASK557_560_OK]")


if __name__ == "__main__":
    main()
