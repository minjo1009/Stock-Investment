from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report


TASK557_PANEL = Path("data/artifacts/task_557_vwap_acceptance_ontology_rebuild/vwap_acceptance_ontology_v3_panel.csv")
TASK559_PANEL = Path("data/artifacts/task_559_context_gate_reattach/context_gate_v3_panel.csv")
TASK547_SNAPSHOTS = Path("docs/reports/task_547_paper_shadow_microstructure_capture_run/decision_microstructure_snapshot_log.csv")
TASK560_CONTRACT = Path("docs/reports/task_560_microstructure_confirmation_requirement/microstructure_confirmation_feature_contract.csv")

TASK561_REPORT = Path("docs/reports/task_561_regime_theme_gate_failure_decomposition")
TASK562_REPORT = Path("docs/reports/task_562_vwap_acceptance_oos_stability_test")
TASK563_REPORT = Path("docs/reports/task_563_paper_shadow_microstructure_capture_activation")
TASK564_REPORT = Path("docs/reports/task_564_event_driven_replay_promotion_gate")
TASK565_REPORT = Path("docs/reports/task_565_regime_vwap_microstructure_retest")
TASK562_DATA = Path("data/artifacts/task_562_vwap_acceptance_oos_stability_test")
TASK563_DATA = Path("data/artifacts/task_563_paper_shadow_microstructure_capture_activation")

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


def _load_panel(path: Path) -> pd.DataFrame:
    frame = _read_csv(path)
    for col in [
        PNL_COL,
        "entry_reduce_failure_flag",
        "add_scale_success_flag",
        "false_positive_flag",
        "holding_days",
        "label_used_in_assignment_flag_v3",
        "outcome_used_in_assignment_flag_v3",
        "inferred_matching_used_flag_v3",
        "label_used_in_context_assignment_flag",
    ]:
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


def build_task561(panel: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    frame = _load_panel(TASK559_PANEL) if panel is None else panel.copy()
    gate = _quality(frame, ["context_gate_v3"])
    gate_split = _quality(frame, ["context_gate_v3", "split_name"])
    gate_quarter = _quality(frame, ["context_gate_v3", "quarter"])
    matrix = _quality(frame, ["multi_day_market_state_v4", "theme_regime_state_v4", "symbol_multiday_setup_state", "vwap_acceptance_state_v3"])
    aligned = gate[gate["context_gate_v3"].eq("regime_theme_symbol_intraday_aligned")]
    other = gate[gate["context_gate_v3"].ne("regime_theme_symbol_intraday_aligned")]
    aligned_er = float(aligned["entry_reduce_failure_rate"].iloc[0]) if not aligned.empty else np.nan
    best_other_er = float(other["entry_reduce_failure_rate"].min()) if not other.empty else np.nan
    failure_reasons = pd.DataFrame(
        [
            {
                "failure_axis": "context_gate_not_selective",
                "evidence": "aligned_gate_entry_reduce_not_better_than_best_other_gate",
                "aligned_entry_reduce_rate": aligned_er,
                "best_other_entry_reduce_rate": best_other_er,
                "requires_next_action": "tighten_regime_theme_persistence_or_add_microstructure_confirmation",
            },
            {
                "failure_axis": "regime_label_too_broad",
                "evidence": "constructive/persistent labels cover too many intraday outcomes",
                "aligned_entry_reduce_rate": aligned_er,
                "best_other_entry_reduce_rate": best_other_er,
                "requires_next_action": "decompose_regime_transition_lag_and_theme_rotation",
            },
        ]
    )
    status = "DIAGNOSTIC_ONLY_CONTEXT_GATE_FAILED" if aligned_er >= best_other_er else "DIAGNOSTIC_ONLY_CONTEXT_GATE_IMPROVED"
    decision = _decision(
        "Task561",
        status,
        aligned_entry_reduce_rate=aligned_er,
        best_other_entry_reduce_rate=best_other_er,
        label_used_in_assignment_flag=int(frame.get("label_used_in_context_assignment_flag", pd.Series([0])).max()),
        inferred_matching_used_flag=int(frame.get("inferred_matching_used_flag_v3", pd.Series([0])).max()),
    )
    return {
        "context_gate_failure_decomposition.csv".replace(".csv", ""): failure_reasons,
        "context_gate_quality": gate,
        "context_gate_split_quality": gate_split,
        "context_gate_quarterly_quality": gate_quarter,
        "context_gate_state_matrix": matrix,
        "task_561_decision": decision,
    }


def build_task562(panel: pd.DataFrame | None = None) -> dict[str, pd.DataFrame]:
    frame = _load_panel(TASK557_PANEL) if panel is None else panel.copy()
    state_quality = _quality(frame, ["vwap_acceptance_state_v3"])
    split = _quality(frame, ["vwap_acceptance_state_v3", "split_name"])
    quarter = _quality(frame, ["vwap_acceptance_state_v3", "quarter"])
    theme = _quality(frame, ["vwap_acceptance_state_v3", "theme_id"])
    symbol = _quality(frame, ["vwap_acceptance_state_v3", "symbol"])
    pivot = split.pivot(index="vwap_acceptance_state_v3", columns="split_name", values="entry_reduce_failure_rate").reset_index()
    for col in ["train_design", "validation", "recent_oos"]:
        if col not in pivot.columns:
            pivot[col] = np.nan
    pivot["validation_recent_er_gap_pp"] = pivot["recent_oos"] - pivot["validation"]
    pivot["oos_stability_status"] = np.select(
        [
            pivot["recent_oos"].le(30) & pivot["validation_recent_er_gap_pp"].le(5),
            pivot["recent_oos"].le(35) & pivot["validation_recent_er_gap_pp"].le(10),
        ],
        ["stable_low_entry_reduce", "watch_moderate_degradation"],
        default="unstable_or_high_entry_reduce",
    )
    good = pivot[pivot["oos_stability_status"].eq("stable_low_entry_reduce")]
    decision = _decision(
        "Task562",
        "DIAGNOSTIC_ONLY_OOS_STABILITY_TESTED",
        stable_state_count=int(len(good)),
        total_state_count=int(frame["vwap_acceptance_state_v3"].nunique()) if "vwap_acceptance_state_v3" in frame.columns else 0,
        label_used_in_assignment_flag=int(frame.get("label_used_in_assignment_flag_v3", pd.Series([0])).max()),
    )
    return {
        "vwap_acceptance_state_quality": state_quality,
        "vwap_acceptance_split_quality": split,
        "vwap_acceptance_quarterly_quality": quarter,
        "vwap_acceptance_theme_quality": theme,
        "vwap_acceptance_symbol_quality": symbol,
        "vwap_acceptance_oos_stability_audit": pivot,
        "task_562_decision": decision,
    }


def build_task563() -> dict[str, pd.DataFrame]:
    snapshots = _read_csv(TASK547_SNAPSHOTS)
    numeric = ["microstructure_source_ready_flag", "pre_action_snapshot_flag", "order_submission_enabled_flag"]
    for col in numeric:
        if col in snapshots.columns:
            snapshots[col] = pd.to_numeric(snapshots[col], errors="coerce")
    required = [
        "decision_id",
        "symbol",
        "decision_ts_utc",
        "feature_cutoff_recv_ts_utc",
        "last_quote_recv_ts_utc",
        "bid",
        "ask",
        "bid_size",
        "ask_size",
        "spread_bps",
        "quote_staleness_ms",
        "status_clean_flag",
        "luld_active_flag",
        "pre_action_snapshot_flag",
    ]
    schema = pd.DataFrame(
        [
            {"field_name": field, "present_flag": int(field in snapshots.columns), "required_flag": 1}
            for field in required
        ]
    )
    row_count = int(len(snapshots))
    ready_count = int(snapshots.get("microstructure_source_ready_flag", pd.Series(dtype=float)).fillna(0).sum()) if not snapshots.empty else 0
    pre_action_rate = float(snapshots.get("pre_action_snapshot_flag", pd.Series(dtype=float)).fillna(0).mean() * 100.0) if not snapshots.empty else 0.0
    run_audit = pd.DataFrame(
        [
            {
                "capture_run": "task547_seed_snapshot",
                "snapshot_rows": row_count,
                "microstructure_ready_rows": ready_count,
                "pre_action_snapshot_rate": pre_action_rate,
                "order_submission_enabled_rows": int(snapshots.get("order_submission_enabled_flag", pd.Series(dtype=float)).fillna(0).sum()) if not snapshots.empty else 0,
                "activation_status": "READY_FOR_MARKET_HOURS_CAPTURE" if row_count > 0 else "NO_CAPTURE_ROWS",
                "live_source_truth_status": "DATA_BLOCKED_NO_READY_NBBO_ROWS" if ready_count == 0 else "PARTIAL_READY",
            }
        ]
    )
    activation_plan = pd.DataFrame(
        [
            {"step": 1, "team": "Data & Market Microstructure", "action": "Run live/paper collector during market hours with NBBO/bar/status subscriptions.", "blocking_if_missing": "NBBO quote recv_ts"},
            {"step": 2, "team": "Execution & Risk", "action": "Keep order submission disabled until lineage is validated; store simulated_action pre-order.", "blocking_if_missing": "broker order update stream"},
            {"step": 3, "team": "Research Governance", "action": "Promote capture rows only when pre_action_snapshot_flag=1 and microstructure_source_ready_flag=1.", "blocking_if_missing": "decision snapshot contract"},
        ]
    )
    decision = _decision(
        "Task563",
        "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
        snapshot_rows=row_count,
        microstructure_ready_rows=ready_count,
        pre_action_snapshot_rate=pre_action_rate,
    )
    return {
        "paper_shadow_capture_schema_audit": schema,
        "paper_shadow_capture_run_audit": run_audit,
        "paper_shadow_capture_activation_plan": activation_plan,
        "task_563_decision": decision,
    }


def build_task564(task561: dict[str, pd.DataFrame] | None = None, task562: dict[str, pd.DataFrame] | None = None, task563: dict[str, pd.DataFrame] | None = None) -> dict[str, pd.DataFrame]:
    t561 = task561 or build_task561()
    t562 = task562 or build_task562()
    t563 = task563 or build_task563()
    stable_states = t562["vwap_acceptance_oos_stability_audit"]
    capture_audit = t563["paper_shadow_capture_run_audit"].iloc[0].to_dict()
    context_decision = t561["task_561_decision"].iloc[0].to_dict()
    stable_count = int((stable_states["oos_stability_status"] == "stable_low_entry_reduce").sum()) if not stable_states.empty else 0
    source_ready = int(capture_audit.get("microstructure_ready_rows", 0)) > 0
    context_gate_ok = "IMPROVED" in str(context_decision.get("strategy_acceptance_status", ""))
    gates = pd.DataFrame(
        [
            {"gate_name": "context_gate_improves_entry_reduce", "status": "PASS" if context_gate_ok else "FAIL", "next_action_if_fail": "Task561 regime/theme gate redesign"},
            {"gate_name": "vwap_state_has_oos_stable_low_entry_reduce", "status": "PASS" if stable_count > 0 else "FAIL", "next_action_if_fail": "Task562 ontology refinement or broader sample"},
            {"gate_name": "microstructure_capture_has_ready_rows", "status": "PASS" if source_ready else "DATA_BLOCKED", "next_action_if_fail": "Task563 market-hours capture run"},
            {"gate_name": "broker_truth_fill_available", "status": "DATA_BLOCKED", "next_action_if_fail": "Task552/563 order-fill archive activation"},
        ]
    )
    if source_ready and stable_count > 0 and context_gate_ok:
        promotion = "PROMOTE_TO_EVENT_DRIVEN_REPLAY_QUEUE"
    elif stable_count > 0 and not source_ready:
        promotion = "DATA_BLOCKED_WAIT_FOR_MICROSTRUCTURE_CAPTURE"
    else:
        promotion = "REJECT_PROMOTION_NEEDS_RESEARCH_REDESIGN"
    queue = pd.DataFrame(
        [
            {"priority": 1, "next_task": "Task563 market-hours capture run", "reason": "microstructure ready rows are required before firm-grade replay"},
            {"priority": 2, "next_task": "Task561 regime/theme redesign", "reason": "context gate did not improve entry_reduce"},
            {"priority": 3, "next_task": "Task562 OOS stability refinement", "reason": "VWAP ontology states must survive recent OOS"},
        ]
    )
    decision = _decision(
        "Task564",
        promotion,
        stable_vwap_state_count=stable_count,
        microstructure_ready_rows=int(capture_audit.get("microstructure_ready_rows", 0)),
        context_gate_ok_flag=int(context_gate_ok),
    )
    return {
        "event_driven_replay_promotion_gate": gates,
        "event_driven_replay_next_action_queue": queue,
        "task_564_decision": decision,
    }


def build_task565(task564: dict[str, pd.DataFrame] | None = None) -> dict[str, pd.DataFrame]:
    t564 = task564 or build_task564()
    decision564 = t564["task_564_decision"].iloc[0].to_dict()
    micro_ready = int(decision564.get("microstructure_ready_rows", 0))
    can_retest = micro_ready > 0 and "PROMOTE" in str(decision564.get("strategy_acceptance_status", ""))
    design = pd.DataFrame(
        [
            {"grid_axis": "multi_day_market_state", "source": "Task559/561", "ready_flag": 1},
            {"grid_axis": "theme_regime_state", "source": "Task559/561", "ready_flag": 1},
            {"grid_axis": "vwap_acceptance_state_v3", "source": "Task557/562", "ready_flag": 1},
            {"grid_axis": "spread_bps_bucket", "source": "Task563 live NBBO capture", "ready_flag": int(micro_ready > 0)},
            {"grid_axis": "quote_staleness_bucket", "source": "Task563 live recv_ts capture", "ready_flag": int(micro_ready > 0)},
            {"grid_axis": "status_luld_clean", "source": "Task563 status/LULD capture", "ready_flag": int(micro_ready > 0)},
        ]
    )
    blocked = design[design["ready_flag"].eq(0)].copy()
    if can_retest:
        status = "DIAGNOSTIC_ONLY_READY_FOR_MICROSTRUCTURE_RETEST"
    else:
        status = "DATA_BLOCKED_MICROSTRUCTURE_RETEST_NOT_RUN"
    retest_plan = pd.DataFrame(
        [
            {
                "test_name": "regime_theme_vwap_microstructure_grid",
                "run_status": "NOT_RUN_DATA_BLOCKED" if not can_retest else "READY",
                "blocked_axes": ",".join(blocked["grid_axis"].astype(str).tolist()),
                "approximation_used_flag": 0,
            }
        ]
    )
    decision = _decision(
        "Task565",
        status,
        ready_grid_axis_count=int(design["ready_flag"].sum()),
        blocked_grid_axis_count=int((design["ready_flag"] == 0).sum()),
        approximation_used_flag=0,
    )
    return {
        "regime_vwap_microstructure_grid_design": design,
        "regime_vwap_microstructure_retest_plan": retest_plan,
        "task_565_decision": decision,
    }


def main() -> None:
    task561 = build_task561()
    task562 = build_task562()
    task563 = build_task563()
    task564 = build_task564(task561, task562, task563)
    task565 = build_task565(task564)

    _write_frames(TASK561_REPORT, task561)
    _write_report(
        TASK561_REPORT,
        "task_561_regime_theme_gate_failure_decomposition.md",
        "Task561 — Regime/Theme Gate Failure Decomposition",
        task561["task_561_decision"],
        [
            "- Decomposed why the current market/theme/symbol/intraday context gate failed to reduce entry_reduce.",
            "- Labels are evaluation-only; context assignment remains pre-entry and exact lifecycle based.",
        ],
        [
            "- 좋은 시장/테마라고 묶은 후보가 실제로 실패를 줄였는지 확인했습니다.",
            "- 실패했다면 조합을 더 돌리는 것이 아니라 레짐/테마 정의를 다시 고쳐야 합니다.",
        ],
    )

    _write_frames(TASK562_REPORT, task562)
    _write_frames(TASK562_DATA, {"vwap_acceptance_oos_stability_audit": task562["vwap_acceptance_oos_stability_audit"]})
    _write_report(
        TASK562_REPORT,
        "task_562_vwap_acceptance_oos_stability_test.md",
        "Task562 — VWAP Acceptance OOS Stability Test",
        task562["task_562_decision"],
        [
            "- Tested whether VWAP acceptance states survive train/validation/recent OOS rather than only looking good in-sample.",
            "- State stability is measured by recent OOS entry_reduce and validation-to-recent degradation.",
        ],
        [
            "- VWAP 눌림/흡수 구조가 최근 구간에서도 유지되는지 확인했습니다.",
            "- 최근 구간에서 무너지면 실전 후보가 아니라 연구 후보로 남깁니다.",
        ],
    )

    _write_frames(TASK563_REPORT, task563)
    _write_frames(TASK563_DATA, {"paper_shadow_capture_activation_plan": task563["paper_shadow_capture_activation_plan"]})
    _write_report(
        TASK563_REPORT,
        "task_563_paper_shadow_microstructure_capture_activation.md",
        "Task563 — Paper/Shadow Microstructure Capture Activation",
        task563["task_563_decision"],
        [
            "- Audited the current Task547 capture rows and defined the market-hours activation path.",
            "- Historical seed rows without live-ready NBBO/status are not treated as firm-grade microstructure.",
        ],
        [
            "- 실시간 quote/status/order-fill 데이터를 실제로 쌓기 위한 실행 준비 상태를 점검했습니다.",
            "- 아직 source-ready 행이 없으면 실전 검증은 막힌 상태로 둡니다.",
        ],
    )

    _write_frames(TASK564_REPORT, task564)
    _write_report(
        TASK564_REPORT,
        "task_564_event_driven_replay_promotion_gate.md",
        "Task564 — Event-Driven Replay Promotion Gate",
        task564["task_564_decision"],
        [
            "- Converted Task561/562/563 outputs into a promotion gate for event-driven replay.",
            "- Promotion is blocked unless context, OOS stability, and microstructure source truth pass together.",
        ],
        [
            "- 연구 결과를 다음 단계로 올려도 되는지 게이트로 판정했습니다.",
            "- 데이터가 부족하면 전략을 억지로 통과시키지 않고 DATA_BLOCKED로 남깁니다.",
        ],
    )

    _write_frames(TASK565_REPORT, task565)
    _write_report(
        TASK565_REPORT,
        "task_565_regime_vwap_microstructure_retest.md",
        "Task565 — Regime × VWAP × Microstructure Retest",
        task565["task_565_decision"],
        [
            "- Defined the final regime × VWAP × microstructure retest grid.",
            "- The retest is not run when NBBO/status/receive timestamp axes are unavailable.",
        ],
        [
            "- 최종 조합 테스트는 microstructure 데이터가 있어야만 실행됩니다.",
            "- 없는 데이터를 추정하지 않았고, blocked axis를 명확히 남겼습니다.",
        ],
    )
    print("[TASK561_565_OK]")


if __name__ == "__main__":
    main()
