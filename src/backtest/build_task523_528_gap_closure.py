from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate
from src.backtest.build_task505_two_year_pnl_grid import build_cell_pool, run_grid, simulate_portfolio
from src.backtest.build_task508_511_task505_validation import assign_cells_like, load_panel
from src.backtest.build_task517_522_firm_grade_completion import raw_native_replay


TASK503_PANEL = Path("docs/reports/task_503_multiday_entry_population_rebuild/selected_multiday_lifecycle_panel.csv")
TASK505_PANEL = Path("docs/reports/task_505_two_year_pnl_grid/selected_two_year_pnl_strategy_panel.csv")
TASK516_QUEUE = Path("docs/reports/task_516_vectorized_discovery_layer/candidate_to_replay_queue.csv")
DATA_RAW = Path("data/raw")

TASK523_OUT = Path("docs/reports/task_523_receive_timestamp_replay")
TASK524_OUT = Path("docs/reports/task_524_entry_reduce_suppression_oos")
TASK525_OUT = Path("docs/reports/task_525_broker_order_fill_archive_contract")
TASK526_OUT = Path("docs/reports/task_526_depth_scope_decision")
TASK527_OUT = Path("docs/reports/task_527_replay_queue_promotion_rerun")
TASK528_OUT = Path("docs/reports/task_528_firm_grade_gate_v2")


def build_task523_receive_timestamp_replay(
    *,
    task505_panel_path: Path = TASK505_PANEL,
    raw_intraday_dir: Path = DATA_RAW / "us_intraday",
    stream_archive_dir: Path = DATA_RAW / "alpaca_stock_stream_archive",
    out_dir: Path = TASK523_OUT,
) -> dict[str, pd.DataFrame]:
    panel = load_panel(task505_panel_path)
    replay = raw_native_replay(panel, raw_intraday_dir)
    stream_records = load_stream_archive_records(stream_archive_dir)
    replay["receive_ts_status"] = "receive_ts_missing"
    replay["recv_ts_utc"] = pd.NA
    replay["stream_archive_match_flag"] = 0
    if not stream_records.empty:
        stream_symbols = set(stream_records["symbol"].astype(str).str.upper())
        symbol_mask = replay["symbol"].astype(str).str.upper().isin(stream_symbols)
        replay.loc[symbol_mask, "stream_archive_match_flag"] = 1
    source_audit = pd.DataFrame(
        [
            {
                "source_name": "historical_ohlcv_replay",
                "row_count": int(len(replay)),
                "receive_ts_available_flag": 0,
                "source_status": "historical_no_receive_ts",
            },
            {
                "source_name": "live_stream_archive_jsonl",
                "row_count": int(len(stream_records)),
                "receive_ts_available_flag": int(not stream_records.empty),
                "source_status": "available" if not stream_records.empty else "no_archive_rows_found",
            },
        ]
    )
    clock = pd.DataFrame(
        [
            {
                "event_count": int(len(replay)),
                "receive_ts_missing_count": int(replay["recv_ts_utc"].isna().sum()),
                "live_ready_event_count": int(replay["recv_ts_utc"].notna().sum()),
                "historical_and_live_separated_flag": 1,
            }
        ]
    )
    decision_snapshot = replay[replay["event_type"].eq("DECISION_SNAPSHOT")].copy()
    decision_snapshot["live_ready_flag"] = decision_snapshot["recv_ts_utc"].notna().astype(int)
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task523",
                "receive_ts_replay_ready_flag": int(decision_snapshot["live_ready_flag"].mean() == 1.0) if not decision_snapshot.empty else 0,
                "decision_snapshot_count": int(len(decision_snapshot)),
                "receive_ts_missing_decision_count": int(decision_snapshot["recv_ts_utc"].isna().sum()),
                "missing_receive_ts_treated_live_ready_flag": 0,
                "strategy_acceptance_status": "RECEIVE_TS_REPLAY_BLOCKED_FOR_HISTORICAL_ROWS",
            }
        ]
    )
    _write(out_dir, {
        "receive_timestamp_replay_source_audit": source_audit,
        "event_clock_consistency_audit": clock,
        "decision_snapshot_receive_ts_audit": decision_snapshot,
        "task_523_decision": decision,
    }, "task_523_receive_timestamp_replay.md")
    return {"task_523_decision": decision, "event_clock_consistency_audit": clock}


def load_stream_archive_records(root: Path) -> pd.DataFrame:
    rows = []
    for path in root.rglob("*.jsonl") if root.exists() else []:
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    try:
                        rows.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    return pd.DataFrame(rows)


def build_task524_entry_reduce_suppression_oos(
    *,
    task503_panel_path: Path = TASK503_PANEL,
    out_dir: Path = TASK524_OUT,
) -> dict[str, pd.DataFrame]:
    panel = load_panel(task503_panel_path)
    recent = panel[panel["entry_ts"].ge(panel["entry_ts"].max() - pd.Timedelta(days=730))].copy()
    families = suppression_families()
    rows = []
    folds = []
    quarters = sorted(recent["quarter"].dropna().astype(str).unique().tolist())
    baseline_count = 0
    for idx in range(2, len(quarters)):
        train = recent[recent["quarter"].isin(quarters[:idx])].copy()
        test = recent[recent["quarter"].eq(quarters[idx])].copy()
        if len(train) < 100 or len(test) < 5:
            continue
        pool = build_cell_pool(train)
        candidates, _ = run_grid(train, pool)
        if candidates.empty:
            continue
        best = candidates.iloc[0]
        cells = pool[
            pool["cell_dims"].eq(best["cell_dims"])
            & pool["avg_net_return_pct"].ge(float(best["min_avg_net_pct"]))
            & pool["win_rate"].ge(float(best["min_win_rate"]))
            & pool["entry_reduce_failure_rate"].le(float(best["max_entry_reduce_rate"]))
        ].copy()
        assigned = assign_cells_like(test, cells)
        baseline_count += len(assigned)
        for family in families:
            filtered = apply_suppression_family(assigned, family["family_name"])
            result = simulate_portfolio(filtered, max_positions=int(best["max_positions"]))
            metrics = aggregate(result.accepted_panel)
            row = dict(family)
            row.update(metrics)
            row.update(
                {
                    "test_quarter": quarters[idx],
                    "baseline_count": int(len(assigned)),
                    "retained_count": int(len(filtered)),
                    "retention_rate": float(len(filtered) / max(len(assigned), 1)),
                    "positive_fold_flag": int(float(metrics["avg_net_return_pct"]) > 0),
                    "entry_safe_assignment_flag": 1,
                    "label_used_in_assignment_flag": 0,
                }
            )
            folds.append(row)
    fold_df = pd.DataFrame(folds)
    if not fold_df.empty:
        summary = (
            fold_df.groupby("family_name", dropna=False)
            .agg(
                fold_count=("test_quarter", "nunique"),
                total_count=("lifecycle_count", "sum"),
                avg_net_mean=("avg_net_return_pct", "mean"),
                positive_fold_rate=("positive_fold_flag", "mean"),
                entry_reduce_mean=("entry_reduce_failure_rate", "mean"),
                retention_mean=("retention_rate", "mean"),
            )
            .reset_index()
        )
        summary["pass_flag"] = (
            summary["entry_reduce_mean"].le(0.30)
            & summary["positive_fold_rate"].ge(0.70)
            & summary["retention_mean"].ge(0.60)
        ).astype(int)
    else:
        summary = pd.DataFrame()
    selected = summary[summary["pass_flag"].eq(1)].sort_values(["entry_reduce_mean", "avg_net_mean"], ascending=[True, False]).head(1) if not summary.empty else pd.DataFrame()
    pass_flag = int(not selected.empty)
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task524",
                "suppression_oos_pass_flag": pass_flag,
                "selected_family": selected.iloc[0]["family_name"] if pass_flag else "none",
                "selected_entry_reduce_rate": selected.iloc[0]["entry_reduce_mean"] if pass_flag else pd.NA,
                "selected_positive_fold_rate": selected.iloc[0]["positive_fold_rate"] if pass_flag else pd.NA,
                "strategy_acceptance_status": "SUPPRESSION_PASS_DIAGNOSTIC" if pass_flag else "SUPPRESSION_FAIL_NEEDS_NEW_FEATURES",
            }
        ]
    )
    _write(out_dir, {
        "entry_reduce_suppression_candidate_pool": summary,
        "entry_reduce_suppression_walk_forward_quality": fold_df,
        "entry_reduce_suppression_selected_rules": selected,
        "task_524_decision": decision,
    }, "task_524_entry_reduce_suppression_oos.md")
    return {"entry_reduce_suppression_candidate_pool": summary, "task_524_decision": decision}


def suppression_families() -> list[dict[str, object]]:
    return [
        {"family_name": "drop_theme_participation", "description": "Remove weaker theme participation regimes."},
        {"family_name": "drop_opening_drive", "description": "Remove opening drive timing failures."},
        {"family_name": "drop_volume_confirmed_reclaim", "description": "Remove high entry-reduce volume reclaim setup."},
        {"family_name": "drop_early_acceleration", "description": "Remove early acceleration failures."},
        {"family_name": "strict_late_midday_only", "description": "Keep late-day and midday only."},
        {"family_name": "trend_persistence_only", "description": "Keep trend persistence near high only."},
    ]


def apply_suppression_family(frame: pd.DataFrame, name: str) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()
    out = frame.copy()
    if name == "drop_theme_participation" and "theme_regime_state_v4" in out.columns:
        out = out[~out["theme_regime_state_v4"].astype(str).eq("theme_participation")]
    elif name == "drop_opening_drive" and "timing_state" in out.columns:
        out = out[~out["timing_state"].astype(str).eq("opening_drive")]
    elif name == "drop_volume_confirmed_reclaim" and "symbol_multiday_setup_state" in out.columns:
        out = out[~out["symbol_multiday_setup_state"].astype(str).eq("volume_confirmed_reclaim")]
    elif name == "drop_early_acceleration" and "symbol_multiday_setup_state" in out.columns:
        out = out[~out["symbol_multiday_setup_state"].astype(str).eq("early_acceleration")]
    elif name == "strict_late_midday_only" and "timing_state" in out.columns:
        out = out[out["timing_state"].astype(str).isin(["late_day_confirmation", "midday_continuation"])]
    elif name == "trend_persistence_only" and "symbol_multiday_setup_state" in out.columns:
        out = out[out["symbol_multiday_setup_state"].astype(str).eq("trend_persistence_near_high")]
    return out.reset_index(drop=True)


def build_task525_broker_order_fill_archive_contract(*, out_dir: Path = TASK525_OUT) -> dict[str, pd.DataFrame]:
    required = [
        "client_order_id",
        "decision_id",
        "order_id",
        "order_status",
        "submitted_ts",
        "filled_ts",
        "filled_qty",
        "filled_avg_price",
        "reject_reason",
        "raw_message_hash",
    ]
    contract = pd.DataFrame(
        [{"field_name": field, "required_flag": 1, "nullable_allowed_flag": int(field in {"filled_ts", "filled_qty", "filled_avg_price", "reject_reason"})} for field in required]
    )
    lineage = pd.DataFrame(
        [
            {"lineage_edge": "decision_id_to_client_order_id", "required_flag": 1},
            {"lineage_edge": "client_order_id_to_order_id", "required_flag": 1},
            {"lineage_edge": "order_id_to_lifecycle_id", "required_flag": 1},
        ]
    )
    gap = pd.DataFrame(
        [
            {"gap_name": "historical_task505_broker_truth_missing", "blocked_flag": 1},
            {"gap_name": "live_order_update_collector_not_implemented", "blocked_flag": 1},
        ]
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task525",
                "contract_defined_flag": 1,
                "historical_task505_broker_truth_available_flag": 0,
                "collector_implemented_flag": 0,
                "strategy_acceptance_status": "CONTRACT_READY_COLLECTION_BLOCKED",
            }
        ]
    )
    _write(out_dir, {
        "broker_order_fill_archive_contract": contract,
        "order_fill_lineage_contract": lineage,
        "broker_truth_gap_audit": gap,
        "task_525_decision": decision,
    }, "task_525_broker_order_fill_archive_contract.md")
    return {"task_525_decision": decision}


def build_task526_depth_scope_decision(*, out_dir: Path = TASK526_OUT) -> dict[str, pd.DataFrame]:
    matrix = pd.DataFrame(
        [
            {"scope_mode": "FULL_DEPTH_REQUIRED", "deployment_grade_allowed_flag": 0, "paper_shadow_allowed_flag": 0, "reason": "provider_missing"},
            {"scope_mode": "NBBO_ONLY_SCOPE_LIMITED", "deployment_grade_allowed_flag": 0, "paper_shadow_allowed_flag": 1, "reason": "allowed only for NBBO/spread-size limited paper or shadow testing"},
        ]
    )
    nbbo = pd.DataFrame(
        [
            {"feature_name": "spread_bps", "allowed_flag": 1},
            {"feature_name": "nbbo_bid_ask_size", "allowed_flag": 1},
            {"feature_name": "depth_imbalance", "allowed_flag": 0},
            {"feature_name": "order_book_sweep_pressure", "allowed_flag": 0},
        ]
    )
    blocker = pd.DataFrame([{"provider_name": "UNCONFIGURED_FULL_DEPTH_PROVIDER", "blocked_flag": 1, "not_approximated_flag": 1}])
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task526",
                "selected_scope_mode": "NBBO_ONLY_SCOPE_LIMITED",
                "deployment_grade_allowed_flag": 0,
                "paper_shadow_allowed_flag": 1,
                "full_depth_approximated_flag": 0,
                "strategy_acceptance_status": "NBBO_ONLY_PAPER_SHADOW_SCOPE_LIMITED",
            }
        ]
    )
    _write(out_dir, {
        "depth_scope_decision_matrix": matrix,
        "nbbo_only_allowed_feature_contract": nbbo,
        "full_depth_provider_blocker_audit": blocker,
        "task_526_decision": decision,
    }, "task_526_depth_scope_decision.md")
    return {"task_526_decision": decision}


def build_task527_replay_queue_promotion_rerun(
    *,
    queue_quality_path: Path = Path("docs/reports/task_521_replay_queued_discovery_grid/queued_candidate_replay_quality.csv"),
    suppression_decision_path: Path = TASK524_OUT / "task_524_decision.csv",
    out_dir: Path = TASK527_OUT,
) -> dict[str, pd.DataFrame]:
    quality = pd.read_csv(queue_quality_path) if queue_quality_path.exists() else pd.DataFrame()
    suppression = pd.read_csv(suppression_decision_path).iloc[0].to_dict() if suppression_decision_path.exists() else {}
    rows = []
    for row in quality.to_dict(orient="records"):
        er = float(row.get("entry_reduce_failure_rate", 1.0))
        count = int(row.get("lifecycle_count", 0))
        pnl = float(row.get("capital_pnl_pct", 0.0))
        if suppression.get("suppression_oos_pass_flag", 0) != 1:
            decision = "NEEDS_SUPPRESSION_RERUN"
            reason = "entry_reduce_suppression_not_passed"
        elif count >= 50 and pnl > 0 and er <= 0.30:
            decision = "PROMOTE_TO_PAPER_SHADOW_CANDIDATE"
            reason = "diagnostic_metrics_pass_nbbo_scope_limited"
        else:
            decision = "REJECT_DIAGNOSTIC"
            reason = "count_pnl_or_entry_reduce_failed"
        out = dict(row)
        out.update({"promotion_decision": decision, "promotion_reason": reason})
        rows.append(out)
    panel = pd.DataFrame(rows)
    promoted = panel[panel["promotion_decision"].eq("PROMOTE_TO_PAPER_SHADOW_CANDIDATE")].copy() if not panel.empty else pd.DataFrame()
    rejected = panel[~panel["promotion_decision"].eq("PROMOTE_TO_PAPER_SHADOW_CANDIDATE")].copy() if not panel.empty else pd.DataFrame()
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task527",
                "candidate_count": int(len(panel)),
                "promoted_candidate_count": int(len(promoted)),
                "has_clear_terminal_decision_flag": int(len(panel) > 0),
                "strategy_acceptance_status": "PROMOTION_RERUN_NEEDS_SUPPRESSION" if promoted.empty else "PAPER_SHADOW_CANDIDATE_FOUND",
            }
        ]
    )
    _write(out_dir, {
        "replay_queue_post_suppression_quality": panel,
        "replay_queue_promotion_candidates": promoted,
        "replay_queue_reject_reasons": rejected,
        "task_527_decision": decision,
    }, "task_527_replay_queue_promotion_rerun.md")
    return {"task_527_decision": decision}


def build_task528_firm_grade_gate_v2(*, out_dir: Path = TASK528_OUT) -> dict[str, pd.DataFrame]:
    d523 = _read_decision(TASK523_OUT / "task_523_decision.csv")
    d524 = _read_decision(TASK524_OUT / "task_524_decision.csv")
    d525 = _read_decision(TASK525_OUT / "task_525_decision.csv")
    d526 = _read_decision(TASK526_OUT / "task_526_decision.csv")
    d527 = _read_decision(TASK527_OUT / "task_527_decision.csv")
    gate = pd.DataFrame(
        [
            {"gate": "receive_ts_replay", "pass_flag": int(d523.get("receive_ts_replay_ready_flag", 0)), "next_action": "collect_live_stream_archive_with_recv_ts"},
            {"gate": "entry_reduce_suppression", "pass_flag": int(d524.get("suppression_oos_pass_flag", 0)), "next_action": "design_new_entry_safe_features"},
            {"gate": "broker_order_fill_contract", "pass_flag": int(d525.get("collector_implemented_flag", 0)), "next_action": "implement_order_fill_update_collector"},
            {"gate": "depth_scope", "pass_flag": int(d526.get("paper_shadow_allowed_flag", 0)), "next_action": "paper_shadow_nbbo_only_or_acquire_depth"},
            {"gate": "replay_queue_promotion", "pass_flag": int(d527.get("promoted_candidate_count", 0) > 0), "next_action": "rerun_after_suppression_pass"},
        ]
    )
    if int(gate["pass_flag"].sum()) == len(gate):
        promotion = "PROMOTE_TO_PAPER_SHADOW"
    elif int(d526.get("paper_shadow_allowed_flag", 0)) == 1 and int(d527.get("has_clear_terminal_decision_flag", 0)) == 1:
        promotion = "NEEDS_SUPPRESSION_RERUN"
    else:
        promotion = "DATA_BLOCKED"
    next_actions = gate[gate["pass_flag"].eq(0)].copy().reset_index(drop=True)
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task528",
                "promotion_decision_v2": promotion,
                "passed_gate_count": int(gate["pass_flag"].sum()),
                "required_gate_count": int(len(gate)),
                "deployment_ready_flag": 0,
                "strategy_acceptance_status": "NOT_DEPLOYMENT_READY",
            }
        ]
    )
    _write(out_dir, {
        "firm_grade_gate_v2": gate,
        "promotion_decision_v2": decision,
        "next_action_queue": next_actions,
        "task_528_decision": decision,
    }, "task_528_firm_grade_gate_v2.md")
    return {"firm_grade_gate_v2": gate, "task_528_decision": decision}


def _read_decision(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    return frame.iloc[0].to_dict() if not frame.empty else {}


def _write(out_dir: Path, artifacts: dict[str, pd.DataFrame], report_name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    decision = next((frame for name, frame in artifacts.items() if name.startswith("task_")), pd.DataFrame())
    (out_dir / report_name).write_text(_report(report_name.replace(".md", "").replace("_", " ").title(), decision), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def _report(title: str, decision: pd.DataFrame) -> str:
    status = decision.iloc[0].get("strategy_acceptance_status", "UNKNOWN") if not decision.empty else "UNKNOWN"
    return "\n".join(
        [
            f"# {title}",
            "",
            "## Decision Summary",
            "",
            f"- Strategy acceptance: {status}",
            "- Deployment-ready: NO",
            "",
            "## Quant Expert Report",
            "",
            "This task closes one firm-grade validation gap and converts remaining blockers into explicit next actions. Missing data is not approximated.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "This report says what passed, what is still blocked, and what must happen next before paper/shadow or live trading.",
            "",
            "## Artifact Manifest",
            "",
            "See `artifact_manifest.csv`.",
        ]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task505-panel", type=Path, default=TASK505_PANEL)
    parser.add_argument("--task503-panel", type=Path, default=TASK503_PANEL)
    args = parser.parse_args()
    build_task523_receive_timestamp_replay(task505_panel_path=args.task505_panel)
    build_task524_entry_reduce_suppression_oos(task503_panel_path=args.task503_panel)
    build_task525_broker_order_fill_archive_contract()
    build_task526_depth_scope_decision()
    build_task527_replay_queue_promotion_rerun()
    build_task528_firm_grade_gate_v2()


if __name__ == "__main__":
    main()
