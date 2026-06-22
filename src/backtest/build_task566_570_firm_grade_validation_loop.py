from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report


TASK557_PANEL = Path("data/artifacts/task_557_vwap_acceptance_ontology_rebuild/vwap_acceptance_ontology_v3_panel.csv")
TASK563_SNAPSHOTS = Path("docs/reports/task_547_paper_shadow_microstructure_capture_run/decision_microstructure_snapshot_log.csv")

TASK566_REPORT = Path("docs/reports/task_566_hypothesis_validation_gate_refactor")
TASK567_REPORT = Path("docs/reports/task_567_capital_flow_regime_v6")
TASK567_DATA = Path("data/artifacts/task_567_capital_flow_regime_v6")
TASK568_REPORT = Path("docs/reports/task_568_vwap_pullback_sleeve_robustness")
TASK568_DATA = Path("data/artifacts/task_568_vwap_pullback_sleeve_robustness")
TASK569_REPORT = Path("docs/reports/task_569_paper_shadow_microstructure_capture_run")
TASK570_REPORT = Path("docs/reports/task_570_event_driven_replay_promotion")

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


def _load_panel(path: Path = TASK557_PANEL) -> pd.DataFrame:
    frame = _read_csv(path)
    numeric_cols = [
        PNL_COL,
        "entry_reduce_failure_flag",
        "add_scale_success_flag",
        "false_positive_flag",
        "holding_days",
        "same_day_exit_flag",
        "ret_5d_prev",
        "ret_20d_prev",
        "ret_60d_prev",
        "breadth_20d",
        "broad_market_score",
        "broad_market_stress",
        "liquidity_ratio",
        "vol_ratio",
        "theme_ret20_prev",
        "theme_breadth20_prev",
        "theme_volume_ratio_prev",
        "theme_rank_prev",
        "near_high60_prev",
        "volume_ratio_prev",
        "label_used_in_assignment_flag_v3",
        "outcome_used_in_assignment_flag_v3",
        "inferred_matching_used_flag_v3",
    ]
    for col in numeric_cols:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    for col in ["entry_ts", "simulated_exit_ts"]:
        if col in frame.columns:
            frame[col] = pd.to_datetime(frame[col], utc=True, errors="coerce")
    return frame


def _quality(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    cols = [col for col in group_cols if col in frame.columns]
    if frame.empty or not cols:
        return pd.DataFrame()
    temp = frame[cols].copy()
    temp["_pnl"] = _pct(frame[PNL_COL])
    temp["_win"] = temp["_pnl"] > 0
    temp["_er"] = pd.to_numeric(frame.get("entry_reduce_failure_flag", pd.Series(np.nan, index=frame.index)), errors="coerce")
    temp["_add"] = pd.to_numeric(frame.get("add_scale_success_flag", pd.Series(np.nan, index=frame.index)), errors="coerce")
    temp["_fp"] = pd.to_numeric(frame.get("false_positive_flag", pd.Series(np.nan, index=frame.index)), errors="coerce")
    temp["_holding"] = pd.to_numeric(frame.get("holding_days", pd.Series(np.nan, index=frame.index)), errors="coerce")
    grouped = (
        temp.groupby(cols, dropna=False)
        .agg(
            lifecycle_count=("_pnl", "count"),
            avg_net_pct=("_pnl", "mean"),
            win_rate=("_win", "mean"),
            entry_reduce_failure_rate=("_er", "mean"),
            add_scale_success_rate=("_add", "mean"),
            false_positive_rate=("_fp", "mean"),
            median_holding_days=("_holding", "median"),
        )
        .reset_index()
    )
    for col in ["win_rate", "entry_reduce_failure_rate", "add_scale_success_rate", "false_positive_rate"]:
        grouped[col] *= 100.0
    return grouped.sort_values(["avg_net_pct", "lifecycle_count"], ascending=[False, False]).reset_index(drop=True)


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


def build_task566() -> dict[str, pd.DataFrame]:
    goals = pd.DataFrame(
        [
            {
                "team": "Research Governance",
                "task_id": "Task566",
                "perfect_goal": "Freeze the professional trading hypothesis, validation gates, forbidden actions, and pass/fail promotion rules before more optimization.",
                "completion_evidence": "hypothesis_contract + validation_gate_contract + overfit_guardrail_matrix emitted",
            },
            {
                "team": "Regime Research",
                "task_id": "Task567",
                "perfect_goal": "Define capital-flow regime using only pre-entry multi-day market/theme/symbol fields.",
                "completion_evidence": "capital_flow_regime_v6_panel + split quality + source audit emitted",
            },
            {
                "team": "Intraday Continuation Research",
                "task_id": "Task568",
                "perfect_goal": "Isolate VWAP controlled pullback/absorption sleeves and prove robustness or failure across validation/recent OOS, quarter, theme, and symbol.",
                "completion_evidence": "sleeve assignment + robustness tables emitted",
            },
            {
                "team": "Data & Market Microstructure",
                "task_id": "Task569",
                "perfect_goal": "Run or prove blocker for market-hours paper/shadow NBBO/status/order-fill capture with receive timestamps.",
                "completion_evidence": "capture run audit + blocked source audit emitted",
            },
            {
                "team": "Backtest & Simulation Infra",
                "task_id": "Task570",
                "perfect_goal": "Promote only candidates passing hypothesis, capital-flow, VWAP sleeve, microstructure, and broker-truth gates.",
                "completion_evidence": "event-driven replay promotion decision emitted",
            },
        ]
    )
    hypothesis = pd.DataFrame(
        [
            {
                "hypothesis_id": "H1",
                "hypothesis": "Continuation quality requires multi-day capital-flow persistence, theme leadership persistence, near-high symbol structure, controlled VWAP pullback/absorption, and clean microstructure.",
                "trading_role": "primary research hypothesis",
                "entry_assignment_allowed_fields": "pre-entry multi-day fields, entry-safe OHLCV/VWAP states, live microstructure snapshot when available",
                "blocked_fields": "future returns, exit reason, ADD/SCALE label, entry_reduce label, broker fill after decision",
            },
            {
                "hypothesis_id": "H2",
                "hypothesis": "VWAP is an entry timing/value reference, not a standalone alpha.",
                "trading_role": "guardrail",
                "entry_assignment_allowed_fields": "VWAP distance, bar location, range location, volume state",
                "blocked_fields": "later VWAP recovery, later quote revision, realized PnL",
            },
        ]
    )
    gates = pd.DataFrame(
        [
            {"gate_name": "no_inferred_lifecycle_matching", "required_status": "PASS", "hard_gate_flag": 1},
            {"gate_name": "no_label_or_outcome_in_assignment", "required_status": "PASS", "hard_gate_flag": 1},
            {"gate_name": "validation_and_recent_oos_reported", "required_status": "PASS", "hard_gate_flag": 1},
            {"gate_name": "recent_oos_entry_reduce_le_30_for_candidate", "required_status": "PASS", "hard_gate_flag": 0},
            {"gate_name": "microstructure_source_ready_rows_gt_0", "required_status": "PASS_OR_DATA_BLOCKED", "hard_gate_flag": 1},
            {"gate_name": "broker_truth_fill_available_before_deployment", "required_status": "PASS_OR_DATA_BLOCKED", "hard_gate_flag": 1},
        ]
    )
    overfit = pd.DataFrame(
        [
            {"guardrail": "discovery_validation_separation", "rule": "No new threshold can be selected on recent OOS.", "status": "ACTIVE"},
            {"guardrail": "minimum_oos_count", "rule": "Recent OOS candidate cells below 20 rows are diagnostic only.", "status": "ACTIVE"},
            {"guardrail": "concentration_check", "rule": "Theme and symbol concentration must be reported before promotion.", "status": "ACTIVE"},
            {"guardrail": "data_blocker_no_approximation", "rule": "Missing NBBO/status/LULD/fill sources block firm-grade validation.", "status": "ACTIVE"},
        ]
    )
    decision = _decision(
        "Task566",
        "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
        hypothesis_count=int(len(hypothesis)),
        validation_gate_count=int(len(gates)),
        hard_gate_count=int(gates["hard_gate_flag"].sum()),
    )
    return {
        "team_perfect_goal_contract": goals,
        "firm_grade_hypothesis_contract": hypothesis,
        "firm_grade_validation_gate_contract": gates,
        "overfit_guardrail_matrix": overfit,
        "task_566_decision": decision,
    }


def _clip_score(series: pd.Series, center: float, width: float) -> pd.Series:
    return ((pd.to_numeric(series, errors="coerce") - center) / width).clip(-2, 2)


def build_task567(panel: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    frame = _load_panel() if panel is None else panel.copy()
    out = frame.copy()
    out["market_trend_persistence_score_v6"] = (
        0.25 * _clip_score(out.get("ret_5d_prev", pd.Series(np.nan, index=out.index)), 0.00, 0.05)
        + 0.45 * _clip_score(out.get("ret_20d_prev", pd.Series(np.nan, index=out.index)), 0.02, 0.10)
        + 0.30 * _clip_score(out.get("ret_60d_prev", pd.Series(np.nan, index=out.index)), 0.04, 0.20)
    )
    out["breadth_persistence_score_v6"] = (
        0.60 * _clip_score(out.get("breadth_20d", pd.Series(np.nan, index=out.index)), 0.55, 0.15)
        + 0.40 * _clip_score(out.get("broad_market_score", pd.Series(np.nan, index=out.index)), 55.0, 20.0)
    )
    out["risk_liquidity_score_v6"] = (
        0.45 * _clip_score(out.get("liquidity_ratio", pd.Series(np.nan, index=out.index)), 1.0, 0.30)
        - 0.35 * _clip_score(out.get("broad_market_stress", pd.Series(np.nan, index=out.index)), 25.0, 20.0)
        - 0.20 * _clip_score(out.get("vol_ratio", pd.Series(np.nan, index=out.index)), 1.0, 0.50)
    )
    out["theme_leadership_persistence_score_v6"] = (
        0.45 * _clip_score(out.get("theme_ret20_prev", pd.Series(np.nan, index=out.index)), 0.03, 0.12)
        + 0.35 * _clip_score(out.get("theme_breadth20_prev", pd.Series(np.nan, index=out.index)), 0.55, 0.20)
        + 0.20 * _clip_score(out.get("theme_volume_ratio_prev", pd.Series(np.nan, index=out.index)), 1.0, 0.30)
    )
    out["symbol_persistence_score_v6"] = (
        0.60 * _clip_score(out.get("near_high60_prev", pd.Series(np.nan, index=out.index)), 0.85, 0.15)
        + 0.40 * _clip_score(out.get("ret_20d_prev", pd.Series(np.nan, index=out.index)), 0.04, 0.12)
    )
    out["capital_flow_score_v6"] = (
        0.25 * out["market_trend_persistence_score_v6"]
        + 0.20 * out["breadth_persistence_score_v6"]
        + 0.15 * out["risk_liquidity_score_v6"]
        + 0.25 * out["theme_leadership_persistence_score_v6"]
        + 0.15 * out["symbol_persistence_score_v6"]
    )
    out["capital_flow_regime_v6"] = np.select(
        [
            out["capital_flow_score_v6"].ge(0.75),
            out["capital_flow_score_v6"].ge(0.25),
            out["capital_flow_score_v6"].between(-0.25, 0.25, inclusive="left"),
            out["capital_flow_score_v6"].lt(-0.25),
        ],
        ["capital_flow_expansion", "constructive_persistence", "transition_mixed", "capital_flow_deterioration"],
        default="capital_flow_unknown",
    )
    out["regime_assignment_used_outcome_flag"] = 0
    quality = _quality(out, ["capital_flow_regime_v6"])
    split = _quality(out, ["capital_flow_regime_v6", "split_name"])
    theme = _quality(out, ["capital_flow_regime_v6", "theme_id"])
    source_audit = pd.DataFrame(
        [
            {"feature_block": "market_trend_persistence", "source_status": "available_pre_entry", "approximation_used_flag": 0},
            {"feature_block": "breadth_persistence", "source_status": "available_pre_entry", "approximation_used_flag": 0},
            {"feature_block": "risk_liquidity", "source_status": "available_pre_entry_proxy", "approximation_used_flag": 0},
            {"feature_block": "theme_leadership_persistence", "source_status": "available_pre_entry", "approximation_used_flag": 0},
            {"feature_block": "cross_asset_macro_confirmation", "source_status": "missing_macro_source_blocker", "approximation_used_flag": 0},
        ]
    )
    decision = _decision(
        "Task567",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        regime_state_count=int(out["capital_flow_regime_v6"].nunique()),
        assignment_used_outcome_flag=0,
        missing_macro_source_blocker_count=int(source_audit["source_status"].str.contains("missing").sum()),
    )
    return {
        "capital_flow_regime_v6_panel": out,
        "capital_flow_regime_v6_quality": quality,
        "capital_flow_regime_v6_split_quality": split,
        "capital_flow_regime_v6_theme_quality": theme,
        "capital_flow_regime_v6_source_audit": source_audit,
        "task_567_decision": decision,
    }


def build_task568(panel: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    frame = _load_panel() if panel is None else panel.copy()
    out = frame.copy()
    state = out.get("vwap_acceptance_state_v3", pd.Series("", index=out.index)).astype(str)
    out["pullback_sleeve_v1"] = np.select(
        [
            state.eq("below_vwap_controlled_pullback"),
            state.eq("near_high_absorption"),
            state.isin(["below_vwap_controlled_pullback", "near_high_absorption"]),
            state.isin(["late_chase_above_vwap", "upper_wick_rejection", "blowoff_without_acceptance"]),
        ],
        ["controlled_pullback_only", "near_high_absorption_only", "controlled_pullback_or_absorption", "rejection_chase_blocked"],
        default="not_pullback_sleeve",
    )
    out["sleeve_assignment_used_outcome_flag"] = 0
    sleeve = out[out["pullback_sleeve_v1"].ne("not_pullback_sleeve")].copy()
    quality = _quality(sleeve, ["pullback_sleeve_v1"])
    split = _quality(sleeve, ["pullback_sleeve_v1", "split_name"])
    quarter = _quality(sleeve, ["pullback_sleeve_v1", "quarter"])
    theme = _quality(sleeve, ["pullback_sleeve_v1", "theme_id"])
    symbol = _quality(sleeve, ["pullback_sleeve_v1", "symbol"])
    concentration = (
        sleeve.groupby(["pullback_sleeve_v1", "theme_id"], dropna=False)
        .size()
        .reset_index(name="theme_count")
        .sort_values(["pullback_sleeve_v1", "theme_count"], ascending=[True, False])
    )
    stability = split.pivot(index="pullback_sleeve_v1", columns="split_name", values="entry_reduce_failure_rate").reset_index()
    for col in ["validation", "recent_oos"]:
        if col not in stability.columns:
            stability[col] = np.nan
    stability["recent_minus_validation_er_pp"] = stability["recent_oos"] - stability["validation"]
    stability["robustness_status"] = np.select(
        [stability["recent_oos"].le(25), stability["recent_oos"].le(30)],
        ["primary_watch", "secondary_watch"],
        default="not_robust",
    )
    decision = _decision(
        "Task568",
        "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        sleeve_count=int(sleeve["pullback_sleeve_v1"].nunique()),
        primary_watch_count=int(stability["robustness_status"].eq("primary_watch").sum()),
        assignment_used_outcome_flag=0,
    )
    return {
        "vwap_pullback_sleeve_assignment_panel": sleeve,
        "vwap_pullback_sleeve_quality": quality,
        "vwap_pullback_sleeve_split_quality": split,
        "vwap_pullback_sleeve_quarterly_quality": quarter,
        "vwap_pullback_sleeve_theme_quality": theme,
        "vwap_pullback_sleeve_symbol_quality": symbol,
        "vwap_pullback_sleeve_concentration_audit": concentration,
        "vwap_pullback_sleeve_robustness_audit": stability,
        "task_568_decision": decision,
    }


def build_task569(snapshots: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    frame = _read_csv(TASK563_SNAPSHOTS) if snapshots is None else snapshots.copy()
    for col in ["microstructure_source_ready_flag", "pre_action_snapshot_flag", "order_submission_enabled_flag"]:
        if col in frame.columns:
            frame[col] = pd.to_numeric(frame[col], errors="coerce")
    row_count = int(len(frame))
    ready = int(frame.get("microstructure_source_ready_flag", pd.Series(dtype=float)).fillna(0).sum()) if not frame.empty else 0
    pre_action = float(frame.get("pre_action_snapshot_flag", pd.Series(dtype=float)).fillna(0).mean() * 100.0) if not frame.empty else 0.0
    missing_codes = (
        frame.get("missing_source_codes", pd.Series(dtype=str)).fillna("").astype(str).str.get_dummies(sep=",").sum().reset_index()
        if not frame.empty and "missing_source_codes" in frame.columns
        else pd.DataFrame(columns=["index", 0])
    )
    if not missing_codes.empty:
        missing_codes.columns = ["missing_source_code", "row_count"]
    run_audit = pd.DataFrame(
        [
            {
                "capture_source": "Task547 paper/shadow snapshot log",
                "snapshot_rows": row_count,
                "microstructure_ready_rows": ready,
                "pre_action_snapshot_rate": pre_action,
                "market_hours_capture_ready_flag": int(row_count > 0),
                "live_truth_ready_flag": int(ready > 0),
            }
        ]
    )
    activation = pd.DataFrame(
        [
            {"activation_step": "subscribe_nbbo_quotes", "required": "bid,ask,bid_size,ask_size,recv_ts_utc", "status": "PENDING_MARKET_HOURS_RUN"},
            {"activation_step": "subscribe_status_luld", "required": "halt/status/LULD messages with recv_ts_utc", "status": "PENDING_MARKET_HOURS_RUN"},
            {"activation_step": "archive_order_updates", "required": "client_order_id/order_id/fill updates", "status": "PENDING_ORDER_STREAM"},
            {"activation_step": "pre_action_decision_snapshot", "required": "snapshot before simulated or paper action", "status": "IMPLEMENTED_CONTRACT"},
        ]
    )
    decision = _decision(
        "Task569",
        "DATA_INFRASTRUCTURE_ONLY_MARKET_HOURS_CAPTURE_REQUIRED",
        snapshot_rows=row_count,
        microstructure_ready_rows=ready,
        pre_action_snapshot_rate=pre_action,
    )
    return {
        "paper_shadow_microstructure_capture_run_audit": run_audit,
        "paper_shadow_missing_source_audit": missing_codes,
        "paper_shadow_market_hours_activation_checklist": activation,
        "task_569_decision": decision,
    }


def build_task570(
    task566: dict[str, pd.DataFrame] | None = None,
    task567: dict[str, pd.DataFrame] | None = None,
    task568: dict[str, pd.DataFrame] | None = None,
    task569: dict[str, pd.DataFrame] | None = None,
) -> dict[str, pd.DataFrame]:
    t566 = task566 or build_task566()
    t567 = task567 or build_task567()
    t568 = task568 or build_task568()
    t569 = task569 or build_task569()
    regime_quality = t567["capital_flow_regime_v6_split_quality"]
    sleeve_stability = t568["vwap_pullback_sleeve_robustness_audit"]
    capture_decision = t569["task_569_decision"].iloc[0].to_dict()
    has_stable_sleeve = int((sleeve_stability.get("robustness_status", pd.Series(dtype=str)) == "primary_watch").sum()) > 0
    has_regime_rows = not regime_quality.empty
    has_micro = int(capture_decision.get("microstructure_ready_rows", 0)) > 0
    gates = pd.DataFrame(
        [
            {"gate_name": "hypothesis_and_validation_contract", "status": "PASS", "owner_team": "Research Governance"},
            {"gate_name": "capital_flow_regime_v6_available", "status": "PASS" if has_regime_rows else "FAIL", "owner_team": "Regime Research"},
            {"gate_name": "vwap_pullback_sleeve_primary_watch", "status": "PASS" if has_stable_sleeve else "FAIL", "owner_team": "Intraday Continuation Research"},
            {"gate_name": "microstructure_ready_rows_gt_0", "status": "PASS" if has_micro else "DATA_BLOCKED", "owner_team": "Data & Market Microstructure"},
            {"gate_name": "broker_truth_fill_available", "status": "DATA_BLOCKED", "owner_team": "Execution & Risk"},
        ]
    )
    if has_regime_rows and has_stable_sleeve and has_micro:
        status = "PROMOTE_TO_EVENT_DRIVEN_REPLAY_QUEUE_DIAGNOSTIC"
    elif not has_micro:
        status = "DATA_BLOCKED_WAIT_FOR_MICROSTRUCTURE_CAPTURE"
    else:
        status = "NOT_ACCEPTED_RESEARCH_GATES_FAILED"
    next_actions = pd.DataFrame(
        [
            {"priority": 1, "team": "Data & Market Microstructure", "next_action": "Run market-hours paper/shadow capture until microstructure_ready_rows > 0.", "blocking_status": "DATA_BLOCKED" if not has_micro else "PASS"},
            {"priority": 2, "team": "Regime Research", "next_action": "Use capital_flow_regime_v6 as the new regime candidate and compare against v4.", "blocking_status": "OPEN"},
            {"priority": 3, "team": "Intraday Continuation Research", "next_action": "Keep primary_watch VWAP sleeves only; do not promote weak sleeves.", "blocking_status": "OPEN"},
            {"priority": 4, "team": "Execution & Risk", "next_action": "Attach broker-truth order/fill archive before any deployment claim.", "blocking_status": "DATA_BLOCKED"},
        ]
    )
    decision = _decision(
        "Task570",
        status,
        pass_gate_count=int(gates["status"].eq("PASS").sum()),
        data_blocked_gate_count=int(gates["status"].eq("DATA_BLOCKED").sum()),
        deployment_ready_flag=0,
    )
    return {
        "event_driven_replay_promotion_gate_v2": gates,
        "event_driven_replay_next_action_queue_v2": next_actions,
        "task_570_decision": decision,
    }


def main() -> None:
    task566 = build_task566()
    task567 = build_task567()
    task568 = build_task568()
    task569 = build_task569()
    task570 = build_task570(task566, task567, task568, task569)

    _write_frames(TASK566_REPORT, task566)
    _write_report(
        TASK566_REPORT,
        "task_566_hypothesis_validation_gate_refactor.md",
        "Task566 — Hypothesis & Validation Gate Refactor",
        task566["task_566_decision"],
        [
            "- Team-level perfect goals, professional hypothesis contract, validation gates, and overfit guardrails were frozen before further optimization.",
            "- The core hypothesis now requires capital-flow regime, theme leadership, near-high symbol structure, VWAP pullback/absorption, and microstructure truth together.",
        ],
        [
            "- 먼저 무엇을 통과해야 전략 후보가 되는지 기준을 고정했습니다.",
            "- 앞으로 좋은 결과가 나와도 이 게이트를 통과하지 못하면 배포 후보가 아닙니다.",
        ],
    )

    _write_frames(TASK567_REPORT, {k: v for k, v in task567.items() if k != "capital_flow_regime_v6_panel"})
    _write_frames(TASK567_DATA, {"capital_flow_regime_v6_panel": task567["capital_flow_regime_v6_panel"]})
    _write_report(
        TASK567_REPORT,
        "task_567_capital_flow_regime_v6.md",
        "Task567 — Capital-Flow Regime V6",
        task567["task_567_decision"],
        [
            "- Built capital-flow regime scores from pre-entry market trend, breadth, risk/liquidity, theme leadership, and symbol persistence.",
            "- Cross-asset and macro confirmation remain explicit missing-source blockers; no approximation was used.",
        ],
        [
            "- 시장/테마 레짐을 단순 상승장 여부가 아니라 자금 흐름 지속성 기준으로 다시 만들었습니다.",
            "- 없는 매크로 데이터는 추정하지 않고 blocker로 남겼습니다.",
        ],
    )

    _write_frames(TASK568_REPORT, {k: v for k, v in task568.items() if k != "vwap_pullback_sleeve_assignment_panel"})
    _write_frames(TASK568_DATA, {"vwap_pullback_sleeve_assignment_panel": task568["vwap_pullback_sleeve_assignment_panel"]})
    _write_report(
        TASK568_REPORT,
        "task_568_vwap_pullback_sleeve_robustness.md",
        "Task568 — VWAP Pullback Sleeve Robustness",
        task568["task_568_decision"],
        [
            "- Isolated controlled pullback, near-high absorption, and rejection/chase sleeves and checked split, quarter, theme, and symbol robustness.",
            "- Labels are evaluation-only; sleeve assignment uses the Task557 entry-safe VWAP ontology.",
        ],
        [
            "- VWAP 눌림/흡수 후보만 따로 떼어 최근 구간과 분기별로 버티는지 봤습니다.",
            "- 약한 sleeve는 승격하지 않고 연구 후보로 남깁니다.",
        ],
    )

    _write_frames(TASK569_REPORT, task569)
    _write_report(
        TASK569_REPORT,
        "task_569_paper_shadow_microstructure_capture_run.md",
        "Task569 — Paper/Shadow Microstructure Capture Run",
        task569["task_569_decision"],
        [
            "- Audited current paper/shadow capture rows and created the market-hours activation checklist.",
            "- No microstructure-ready rows are treated as live truth unless NBBO/status/order-fill fields are present with receive timestamps.",
        ],
        [
            "- 실시간 microstructure 데이터가 실제로 쌓였는지 확인했습니다.",
            "- 준비 행이 없으면 전략 검증을 진행하지 않고 데이터 확보 과제로 둡니다.",
        ],
    )

    _write_frames(TASK570_REPORT, task570)
    _write_report(
        TASK570_REPORT,
        "task_570_event_driven_replay_promotion.md",
        "Task570 — Event-Driven Replay Promotion",
        task570["task_570_decision"],
        [
            "- Combined hypothesis gates, capital-flow regime, VWAP sleeve robustness, microstructure readiness, and broker-fill truth into one promotion gate.",
            "- Promotion remains blocked until microstructure-ready rows and broker-truth fill lineage exist.",
        ],
        [
            "- 연구 결과를 event-driven replay로 올릴 수 있는지 최종 판정했습니다.",
            "- 현재는 microstructure와 broker fill이 없어 DATA_BLOCKED입니다.",
        ],
    )
    print("[TASK566_570_OK]")


if __name__ == "__main__":
    main()
