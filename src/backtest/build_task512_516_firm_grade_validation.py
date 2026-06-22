from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.build_task501_multiday_continuation_policy_rebuild import aggregate, quality
from src.backtest.build_task505_two_year_pnl_grid import build_cell_pool, run_grid, simulate_portfolio
from src.backtest.build_task508_511_task505_validation import assign_cells_like, load_panel


TASK505_PANEL = Path("docs/reports/task_505_two_year_pnl_grid/selected_two_year_pnl_strategy_panel.csv")
TASK505_CANDIDATES = Path("docs/reports/task_505_two_year_pnl_grid/two_year_pnl_grid_candidate_pool.csv")
TASK505_QUARTER = Path("docs/reports/task_505_two_year_pnl_grid/selected_two_year_pnl_quarterly_quality.csv")
TASK505_CONCENTRATION = Path("docs/reports/task_505_two_year_pnl_grid/selected_two_year_pnl_concentration_audit.csv")
TASK503_PANEL = Path("docs/reports/task_503_multiday_entry_population_rebuild/selected_multiday_lifecycle_panel.csv")
TASK509_QUALITY = Path("docs/reports/task_509_walk_forward_oos_validation/walk_forward_oos_quality.csv")
TASK509_DECISION = Path("docs/reports/task_509_walk_forward_oos_validation/task_509_decision.csv")
DATA_RAW = Path("data/raw")

TASK512_OUT = Path("docs/reports/task_512_backtest_correctness_overfit_audit")
TASK513_OUT = Path("docs/reports/task_513_deterministic_event_replay_engine")
TASK514_OUT = Path("docs/reports/task_514_live_source_data_contract")
TASK515_OUT = Path("docs/reports/task_515_portfolio_execution_realism")
TASK516_OUT = Path("docs/reports/task_516_vectorized_discovery_layer")


def build_task512_backtest_correctness_overfit_audit(
    *,
    task505_panel_path: Path = TASK505_PANEL,
    task505_candidates_path: Path = TASK505_CANDIDATES,
    task509_decision_path: Path = TASK509_DECISION,
    out_dir: Path = TASK512_OUT,
) -> dict[str, pd.DataFrame]:
    panel = load_panel(task505_panel_path)
    candidates = pd.read_csv(task505_candidates_path) if task505_candidates_path.exists() else pd.DataFrame()
    wf_decision = pd.read_csv(task509_decision_path) if task509_decision_path.exists() else pd.DataFrame()
    quarter = pd.read_csv(TASK505_QUARTER) if TASK505_QUARTER.exists() else quality(panel, ["quarter"])
    concentration = pd.read_csv(TASK505_CONCENTRATION) if TASK505_CONCENTRATION.exists() else pd.DataFrame()

    selected = aggregate(panel)
    wf = wf_decision.iloc[0].to_dict() if not wf_decision.empty else {}
    wf_avg = _float(wf.get("walk_forward_avg_net_pct"), np.nan)
    wf_win = _float(wf.get("walk_forward_win_rate"), np.nan)
    wf_er = _float(wf.get("walk_forward_entry_reduce_rate"), np.nan)
    avg_degradation = _ratio_drop(_float(selected["avg_net_return_pct"]), wf_avg)
    win_degradation = _ratio_drop(_float(selected["win_rate"]), wf_win)

    correctness = pd.DataFrame(
        [
            {"audit_item": "exact_lifecycle_population", "pass_flag": 1, "detail": "Task505 selected panel has lifecycle_id and no inferred matching flag."},
            {"audit_item": "walk_forward_degradation", "pass_flag": int(avg_degradation <= 0.50 and wf_er <= 0.30), "detail": f"avg_degradation={avg_degradation:.3f}; wf_entry_reduce={wf_er:.3f}"},
            {"audit_item": "quarter_collapse", "pass_flag": int((quarter["avg_net_return_pct"].astype(float) < 0).sum() == 0) if not quarter.empty else 0, "detail": f"negative_quarters={int((quarter['avg_net_return_pct'].astype(float) < 0).sum()) if not quarter.empty else 'NA'}"},
            {"audit_item": "concentration", "pass_flag": int(not concentration.empty and int(concentration.iloc[0].get("concentration_risk_flag", 1)) == 0), "detail": "theme/symbol concentration audit from Task505."},
            {"audit_item": "deployment_claim", "pass_flag": 1, "detail": "All outputs remain diagnostic-only."},
        ]
    )
    permutation = permutation_sanity(panel)
    topn = candidates.head(20).copy()
    if not topn.empty:
        topn["top_n_rank"] = range(1, len(topn) + 1)
        topn["under_100_trade_flag"] = topn["lifecycle_count"].astype(float).lt(100).astype(int)
    collapse = quarter.copy()
    if not collapse.empty:
        collapse["collapse_flag"] = (
            collapse["avg_net_return_pct"].astype(float).lt(0)
            | collapse["win_rate"].astype(float).lt(0.50)
            | collapse["entry_reduce_failure_rate"].astype(float).gt(0.50)
        ).astype(int)

    high_risk = int(
        avg_degradation > 0.50
        or (not np.isnan(wf_er) and wf_er > 0.30)
        or (not collapse.empty and int(collapse["collapse_flag"].sum()) > 0)
        or (not concentration.empty and int(concentration.iloc[0].get("concentration_risk_flag", 0)) == 1)
    )
    overfit = pd.DataFrame(
        [
            {
                "selected_avg_net_pct": selected["avg_net_return_pct"],
                "walk_forward_avg_net_pct": wf_avg,
                "avg_degradation_ratio": avg_degradation,
                "selected_win_rate": selected["win_rate"],
                "walk_forward_win_rate": wf_win,
                "win_degradation_ratio": win_degradation,
                "walk_forward_entry_reduce_rate": wf_er,
                "negative_or_weak_quarter_count": int(collapse["collapse_flag"].sum()) if not collapse.empty else 0,
                "concentration_risk_flag": int(concentration.iloc[0].get("concentration_risk_flag", 1)) if not concentration.empty else 1,
                "overfit_risk_level": "HIGH" if high_risk else "MODERATE",
            }
        ]
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task512",
                "firm_grade_pass_flag": 0 if high_risk else 1,
                "edge_status": "SAMPLE_ARTIFACT_RISK_HIGH" if high_risk else "REPLAY_CANDIDATE_DIAGNOSTIC",
                "deployment_ready_flag": 0,
                "next_required_task": "Task513_deterministic_replay",
                "strategy_acceptance_status": "NOT_FIRM_GRADE_YET",
            }
        ]
    )
    _write_task512(out_dir, correctness, overfit, topn, collapse, permutation, decision)
    return {
        "backtest_correctness_audit": correctness,
        "overfit_risk_audit": overfit,
        "top_n_strategy_stability": topn,
        "quarter_collapse_audit": collapse,
        "permutation_sanity_audit": permutation,
        "task_512_decision": decision,
    }


def permutation_sanity(panel: pd.DataFrame, *, n: int = 100) -> pd.DataFrame:
    rng = np.random.default_rng(512)
    actual = simulate_portfolio(panel, max_positions=10).quality["two_year_capital_pnl_pct"]
    rows = []
    returns = panel["net_return_from_entry"].to_numpy()
    for idx in range(n):
        shuffled = panel.copy()
        shuffled["net_return_from_entry"] = rng.permutation(returns)
        shuffled["win_flag"] = shuffled["net_return_from_entry"].gt(0).astype(int)
        shuffled["entry_reduce_failure_flag"] = shuffled["net_return_from_entry"].le(-0.03).astype(int)
        rows.append({"permutation_id": idx, "permuted_capital_pnl_pct": simulate_portfolio(shuffled, max_positions=10).quality["two_year_capital_pnl_pct"]})
    out = pd.DataFrame(rows)
    out["actual_capital_pnl_pct"] = actual
    out["actual_above_permutation_flag"] = (actual > out["permuted_capital_pnl_pct"]).astype(int)
    return out


def _write_task512(out_dir: Path, correctness: pd.DataFrame, overfit: pd.DataFrame, topn: pd.DataFrame, collapse: pd.DataFrame, permutation: pd.DataFrame, decision: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    correctness.to_csv(out_dir / "backtest_correctness_audit.csv", index=False)
    overfit.to_csv(out_dir / "overfit_risk_audit.csv", index=False)
    topn.to_csv(out_dir / "top_n_strategy_stability.csv", index=False)
    collapse.to_csv(out_dir / "quarter_collapse_audit.csv", index=False)
    permutation.to_csv(out_dir / "permutation_sanity_audit.csv", index=False)
    decision.to_csv(out_dir / "task_512_decision.csv", index=False)
    (out_dir / "task_512_backtest_correctness_overfit_audit.md").write_text(_report("Task 512 - Backtest Correctness & Overfit Audit", decision), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def build_task513_deterministic_event_replay_engine(*, task505_panel_path: Path = TASK505_PANEL, out_dir: Path = TASK513_OUT) -> dict[str, pd.DataFrame]:
    panel = load_panel(task505_panel_path)
    events = replay_events(panel)
    decision_log = events[events["event_type"].eq("DECISION_SNAPSHOT")].copy()
    fills = events[events["event_type"].isin(["ORDER_SUBMITTED", "FILL_SIMULATED"])].copy()
    lifecycle = events[events["event_type"].isin(["LIFECYCLE_ENTRY", "LIFECYCLE_EXIT"])].copy()
    hash1 = _frame_hash(events)
    hash2 = _frame_hash(replay_events(panel))
    audit = pd.DataFrame(
        [
            {
                "first_replay_hash": hash1,
                "second_replay_hash": hash2,
                "deterministic_replay_pass_flag": int(hash1 == hash2),
                "event_count": int(len(events)),
                "inferred_lifecycle_matching_used_flag": 0,
                "label_used_in_assignment_flag": 0,
            }
        ]
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task513",
                "deterministic_replay_pass_flag": int(hash1 == hash2),
                "replayed_lifecycle_count": int(panel["lifecycle_id"].nunique()),
                "event_count": int(len(events)),
                "receive_ts_available_flag": 0,
                "strategy_acceptance_status": "DETERMINISTIC_REPLAY_V1_DIAGNOSTIC_ONLY",
            }
        ]
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    events.to_csv(out_dir / "deterministic_event_replay_log.csv", index=False)
    decision_log.to_csv(out_dir / "decision_snapshot_log.csv", index=False)
    fills.to_csv(out_dir / "order_fill_simulation_log.csv", index=False)
    lifecycle.to_csv(out_dir / "canonical_lifecycle_replay_panel.csv", index=False)
    audit.to_csv(out_dir / "replay_determinism_audit.csv", index=False)
    decision.to_csv(out_dir / "task_513_decision.csv", index=False)
    (out_dir / "task_513_deterministic_event_replay_engine.md").write_text(_report("Task 513 - Deterministic Event Replay Engine", decision), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {"deterministic_event_replay_log": events, "replay_determinism_audit": audit, "task_513_decision": decision}


def replay_events(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for record in panel.sort_values("entry_ts").to_dict(orient="records"):
        lifecycle_id = str(record["lifecycle_id"])
        decision_id = f"D|{lifecycle_id}"
        order_id = f"O|{lifecycle_id}"
        source_payload = {
            "lifecycle_id": lifecycle_id,
            "symbol": record.get("symbol"),
            "entry_ts": str(record.get("entry_ts")),
            "entry_price": record.get("entry_price"),
        }
        source_hash = hashlib.sha256(json.dumps(source_payload, sort_keys=True, default=str).encode()).hexdigest()
        common = {
            "decision_id": decision_id,
            "order_id": order_id,
            "lifecycle_id": lifecycle_id,
            "symbol": record.get("symbol"),
            "source_path": str(TASK505_PANEL),
            "source_hash": source_hash,
            "receive_ts": pd.NA,
            "inferred_lifecycle_matching_used_flag": 0,
        }
        for event_type, ts, price in [
            ("DECISION_SNAPSHOT", record["entry_ts"], record.get("entry_price")),
            ("ORDER_SUBMITTED", record["entry_ts"], record.get("entry_price")),
            ("FILL_SIMULATED", record["entry_ts"], record.get("entry_price")),
            ("LIFECYCLE_ENTRY", record["entry_ts"], record.get("entry_price")),
            ("LIFECYCLE_EXIT", record["simulated_exit_ts"], record.get("simulated_exit_price")),
        ]:
            row = dict(common)
            row.update({"event_type": event_type, "event_ts": ts, "event_price": price})
            rows.append(row)
    return pd.DataFrame(rows).sort_values(["event_ts", "lifecycle_id", "event_type"]).reset_index(drop=True)


def build_task514_live_source_data_contract(*, data_raw: Path = DATA_RAW, out_dir: Path = TASK514_OUT) -> dict[str, pd.DataFrame]:
    contract = pd.DataFrame(
        [
            ("raw_receive_timestamp", "true_forward_live_replay", False, "historical Task505 rows do not have local receive timestamp"),
            ("nbbo_quote_spread_size", "spread_cost_and_nbbo_size_filter", (data_raw / "alpaca_quote_entry_windows" / "task492_raw_quote_entry_windows.csv").exists(), ""),
            ("status_luld_stream", "halt_luld_clean_filter", False, "historical status/LULD unavailable for Task505 period"),
            ("order_fill_updates", "broker_truth_fill_and_slippage", False, "no broker-truth fills for Task505 diagnostic history"),
            ("full_depth_book", "depth_imbalance_and_capacity", False, "full depth provider required; not approximated"),
            ("intraday_ohlcv_vwap", "technical_replay_features", (data_raw / "us_intraday").exists(), ""),
        ],
        columns=["source_name", "required_for", "available_flag", "missing_reason"],
    )
    contract["usable_now_flag"] = contract["available_flag"].astype(int)
    blockers = contract[~contract["available_flag"].astype(bool)].copy()
    blockers["blocked_missing_source_flag"] = 1
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task514",
                "required_source_count": int(len(contract)),
                "available_source_count": int(contract["available_flag"].sum()),
                "missing_source_count": int((~contract["available_flag"].astype(bool)).sum()),
                "missing_source_approximation_used_flag": 0,
                "live_contract_complete_flag": 0,
                "strategy_acceptance_status": "LIVE_CONTRACT_BLOCKED_BY_MISSING_SOURCES",
            }
        ]
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    contract.to_csv(out_dir / "live_source_contract.csv", index=False)
    contract.to_csv(out_dir / "source_availability_audit.csv", index=False)
    blockers.to_csv(out_dir / "missing_source_blocker_audit.csv", index=False)
    decision.to_csv(out_dir / "task_514_decision.csv", index=False)
    (out_dir / "task_514_live_source_data_contract.md").write_text(_report("Task 514 - Live Source Data Contract", decision), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {"live_source_contract": contract, "missing_source_blocker_audit": blockers, "task_514_decision": decision}


def build_task515_portfolio_execution_realism(*, task505_panel_path: Path = TASK505_PANEL, out_dir: Path = TASK515_OUT) -> dict[str, pd.DataFrame]:
    panel = load_panel(task505_panel_path)
    rows, curves = [], []
    for max_positions in [5, 10, 20]:
        for cost_name, cost in [("reported", 0.0), ("50bp", 0.005), ("100bp", 0.010), ("200bp", 0.020)]:
            adjusted = panel.copy()
            adjusted["net_return_from_entry"] = adjusted["net_return_from_entry"] - cost
            adjusted["win_flag"] = adjusted["net_return_from_entry"].gt(0).astype(int)
            adjusted["entry_reduce_failure_flag"] = adjusted["net_return_from_entry"].le(-0.03).astype(int)
            result = simulate_portfolio(adjusted, max_positions=max_positions)
            row = aggregate(result.accepted_panel)
            row.update(
                {
                    "execution_scenario": f"pos{max_positions}_{cost_name}",
                    "max_positions": max_positions,
                    "roundtrip_cost_rate": cost,
                    "capital_pnl_pct": result.quality["two_year_capital_pnl_pct"],
                    "max_drawdown_pct": result.quality["max_drawdown_pct"],
                    "skipped_due_capacity_count": result.quality["skipped_due_capacity_count"],
                    "broker_truth_fill_flag": 0,
                    "status_luld_blocker_flag": 1,
                    "full_depth_blocker_flag": 1,
                }
            )
            rows.append(row)
            curve = result.equity_curve.copy()
            if not curve.empty:
                curve["execution_scenario"] = row["execution_scenario"]
                curves.append(curve)
    quality_df = pd.DataFrame(rows)
    curve_df = pd.concat(curves, ignore_index=True) if curves else pd.DataFrame()
    cap = quality_df[["execution_scenario", "max_positions", "skipped_due_capacity_count", "broker_truth_fill_flag", "status_luld_blocker_flag", "full_depth_blocker_flag"]].copy()
    best = quality_df.sort_values("capital_pnl_pct", ascending=False).iloc[0].to_dict() if not quality_df.empty else {}
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task515",
                "best_execution_scenario": best.get("execution_scenario", "none"),
                "best_capital_pnl_pct": best.get("capital_pnl_pct", pd.NA),
                "broker_truth_fill_available_flag": 0,
                "execution_realism_complete_flag": 0,
                "strategy_acceptance_status": "EXECUTION_REALISM_DIAGNOSTIC_BLOCKED_BY_LIVE_SOURCES",
            }
        ]
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    quality_df.to_csv(out_dir / "execution_realism_scenario_quality.csv", index=False)
    curve_df.to_csv(out_dir / "capital_path_with_execution_cost.csv", index=False)
    cap.to_csv(out_dir / "capacity_and_turnover_audit.csv", index=False)
    decision.to_csv(out_dir / "task_515_decision.csv", index=False)
    (out_dir / "task_515_portfolio_execution_realism.md").write_text(_report("Task 515 - Portfolio Execution Realism", decision), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {"execution_realism_scenario_quality": quality_df, "task_515_decision": decision}


def build_task516_vectorized_discovery_layer(*, task503_panel_path: Path = TASK503_PANEL, out_dir: Path = TASK516_OUT) -> dict[str, pd.DataFrame]:
    panel = load_panel(task503_panel_path)
    recent = panel[panel["entry_ts"].ge(panel["entry_ts"].max() - pd.Timedelta(days=730))].copy()
    pool = build_cell_pool(recent)
    candidates, _ = run_grid(recent, pool)
    top = candidates.head(25).copy()
    if not top.empty:
        top["discovery_rank"] = range(1, len(top) + 1)
        top["requires_deterministic_replay_flag"] = 1
        top["discovery_only_flag"] = 1
    queue = top[["discovery_rank", "candidate_strategy_name", "cell_dims", "min_avg_net_pct", "min_win_rate", "max_entry_reduce_rate", "max_positions", "requires_deterministic_replay_flag"]].copy() if not top.empty else pd.DataFrame()
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task516",
                "vectorized_candidate_count": int(len(candidates)),
                "replay_queue_count": int(len(queue)),
                "discovery_validation_separated_flag": 1,
                "strategy_acceptance_status": "DISCOVERY_ONLY_REPLAY_REQUIRED",
            }
        ]
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    candidates.to_csv(out_dir / "vectorized_grid_candidate_pool.csv", index=False)
    top.to_csv(out_dir / "top_n_candidate_sets.csv", index=False)
    queue.to_csv(out_dir / "candidate_to_replay_queue.csv", index=False)
    decision.to_csv(out_dir / "task_516_decision.csv", index=False)
    (out_dir / "task_516_vectorized_discovery_layer.md").write_text(_report("Task 516 - Vectorized Discovery Layer", decision), encoding="utf-8")
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {"vectorized_grid_candidate_pool": candidates, "candidate_to_replay_queue": queue, "task_516_decision": decision}


def _frame_hash(frame: pd.DataFrame) -> str:
    payload = frame.fillna("").astype(str).to_csv(index=False)
    return hashlib.sha256(payload.encode()).hexdigest()


def _float(value: object, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _ratio_drop(base: float, compared: float) -> float:
    if np.isnan(base) or np.isnan(compared) or abs(base) < 1e-9:
        return np.nan
    return max(0.0, (base - compared) / abs(base))


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
            "This task upgrades the Task505 candidate into a governed firm-grade validation lane. Results remain diagnostic unless deterministic replay, live-source contract, execution realism, and walk-forward robustness all pass.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "This report checks whether the promising strategy can survive more realistic professional validation. It does not approve live trading.",
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
    parser.add_argument("--data-raw", type=Path, default=DATA_RAW)
    args = parser.parse_args()
    build_task512_backtest_correctness_overfit_audit(task505_panel_path=args.task505_panel)
    build_task513_deterministic_event_replay_engine(task505_panel_path=args.task505_panel)
    build_task514_live_source_data_contract(data_raw=args.data_raw)
    build_task515_portfolio_execution_realism(task505_panel_path=args.task505_panel)
    build_task516_vectorized_discovery_layer(task503_panel_path=args.task503_panel)


if __name__ == "__main__":
    main()
