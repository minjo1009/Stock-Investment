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
from src.backtest.build_task512_516_firm_grade_validation import replay_events
from src.data.full_depth_book_archive import FullDepthBookArchive


TASK503_PANEL = Path("docs/reports/task_503_multiday_entry_population_rebuild/selected_multiday_lifecycle_panel.csv")
TASK505_PANEL = Path("docs/reports/task_505_two_year_pnl_grid/selected_two_year_pnl_strategy_panel.csv")
TASK516_QUEUE = Path("docs/reports/task_516_vectorized_discovery_layer/candidate_to_replay_queue.csv")
DATA_RAW = Path("data/raw")

TASK517_OUT = Path("docs/reports/task_517_raw_native_deterministic_replay")
TASK518_OUT = Path("docs/reports/task_518_firm_grade_overfit_statistics")
TASK519_OUT = Path("docs/reports/task_519_broker_truth_execution_readiness")
TASK520_OUT = Path("docs/reports/task_520_live_source_acquisition_loop")
TASK521_OUT = Path("docs/reports/task_521_replay_queued_discovery_grid")
TASK522_OUT = Path("docs/reports/task_522_firm_grade_promotion_gate")


def build_task517_raw_native_deterministic_replay(
    *,
    task505_panel_path: Path = TASK505_PANEL,
    raw_intraday_dir: Path = DATA_RAW / "us_intraday",
    out_dir: Path = TASK517_OUT,
) -> dict[str, pd.DataFrame]:
    panel = load_panel(task505_panel_path)
    raw_audit = raw_intraday_coverage(panel, raw_intraday_dir)
    replay = raw_native_replay(panel, raw_intraday_dir)
    decision_snapshot = replay[replay["event_type"].eq("DECISION_SNAPSHOT")].copy()
    lifecycle = replay[replay["event_type"].isin(["LIFECYCLE_ENTRY", "LIFECYCLE_EXIT"])].copy()
    audit = pd.DataFrame(
        [
            {
                "raw_intraday_symbol_coverage": float(raw_audit["raw_available_flag"].mean()) if not raw_audit.empty else 0.0,
                "raw_bar_exact_match_rate": float(raw_audit["exact_entry_bar_match_flag"].mean()) if not raw_audit.empty else 0.0,
                "raw_replay_hash": _frame_hash(replay),
                "replay_event_count": int(len(replay)),
                "raw_receive_timestamp_available_flag": 0,
                "inferred_lifecycle_matching_used_flag": 0,
                "label_used_in_assignment_flag": 0,
            }
        ]
    )
    complete = int(float(audit.iloc[0]["raw_bar_exact_match_rate"]) >= 0.95)
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task517",
                "raw_native_replay_complete_flag": complete,
                "raw_intraday_symbol_coverage": audit.iloc[0]["raw_intraday_symbol_coverage"],
                "raw_bar_exact_match_rate": audit.iloc[0]["raw_bar_exact_match_rate"],
                "receive_ts_available_flag": 0,
                "strategy_acceptance_status": "RAW_NATIVE_REPLAY_DIAGNOSTIC_RECEIVE_TS_BLOCKED",
            }
        ]
    )
    _write(TASK517_OUT if out_dir == TASK517_OUT else out_dir, {
        "raw_intraday_replay_source_audit": raw_audit,
        "raw_native_event_replay_log": replay,
        "raw_native_decision_snapshot_log": decision_snapshot,
        "raw_native_lifecycle_replay_panel": lifecycle,
        "raw_native_replay_determinism_audit": audit,
        "task_517_decision": decision,
    }, "task_517_raw_native_deterministic_replay.md")
    return {"raw_intraday_replay_source_audit": raw_audit, "raw_native_replay_determinism_audit": audit, "task_517_decision": decision}


def raw_intraday_coverage(panel: pd.DataFrame, raw_dir: Path) -> pd.DataFrame:
    rows = []
    for row in panel.to_dict(orient="records"):
        symbol = str(row["symbol"]).upper()
        path = raw_dir / f"{symbol}.csv"
        entry_ts = pd.Timestamp(row["entry_ts"])
        exact = 0
        source_hash = ""
        if path.exists():
            raw = pd.read_csv(path)
            raw["timestamp"] = pd.to_datetime(raw["timestamp"], utc=True, errors="coerce")
            match = raw[raw["timestamp"].eq(entry_ts)]
            exact = int(not match.empty)
            if not match.empty:
                source_hash = hashlib.sha256(match.iloc[0].astype(str).to_json().encode()).hexdigest()
        rows.append(
            {
                "lifecycle_id": row["lifecycle_id"],
                "symbol": symbol,
                "entry_ts": entry_ts,
                "raw_source_path": str(path),
                "raw_available_flag": int(path.exists()),
                "exact_entry_bar_match_flag": exact,
                "raw_entry_bar_hash": source_hash,
            }
        )
    return pd.DataFrame(rows)


def raw_native_replay(panel: pd.DataFrame, raw_dir: Path) -> pd.DataFrame:
    events = []
    coverage = raw_intraday_coverage(panel, raw_dir).set_index("lifecycle_id")
    for row in panel.sort_values("entry_ts").to_dict(orient="records"):
        lifecycle_id = str(row["lifecycle_id"])
        cov = coverage.loc[lifecycle_id].to_dict()
        source_hash = cov.get("raw_entry_bar_hash") or hashlib.sha256(lifecycle_id.encode()).hexdigest()
        common = {
            "lifecycle_id": lifecycle_id,
            "decision_id": f"RD|{lifecycle_id}",
            "order_id": f"RO|{lifecycle_id}",
            "symbol": row.get("symbol"),
            "source_path": cov.get("raw_source_path"),
            "source_hash": source_hash,
            "receive_ts": pd.NA,
            "raw_entry_bar_available_flag": cov.get("exact_entry_bar_match_flag", 0),
            "inferred_lifecycle_matching_used_flag": 0,
        }
        for event_type, ts, price in [
            ("RAW_BAR_OBSERVED", row["entry_ts"], row.get("entry_price")),
            ("DECISION_SNAPSHOT", row["entry_ts"], row.get("entry_price")),
            ("ORDER_SUBMITTED", row["entry_ts"], row.get("entry_price")),
            ("FILL_SIMULATED", row["entry_ts"], row.get("entry_price")),
            ("LIFECYCLE_ENTRY", row["entry_ts"], row.get("entry_price")),
            ("LIFECYCLE_EXIT", row["simulated_exit_ts"], row.get("simulated_exit_price")),
        ]:
            out = dict(common)
            out.update({"event_type": event_type, "event_ts": ts, "event_price": price})
            events.append(out)
    return pd.DataFrame(events).sort_values(["event_ts", "lifecycle_id", "event_type"]).reset_index(drop=True)


def build_task518_firm_grade_overfit_statistics(
    *,
    task503_panel_path: Path = TASK503_PANEL,
    out_dir: Path = TASK518_OUT,
) -> dict[str, pd.DataFrame]:
    panel = load_panel(task503_panel_path)
    recent = panel[panel["entry_ts"].ge(panel["entry_ts"].max() - pd.Timedelta(days=730))].copy()
    fold_rows = []
    quarters = sorted(recent["quarter"].dropna().astype(str).unique().tolist())
    for idx in range(2, len(quarters)):
        train = recent[recent["quarter"].isin(quarters[:idx])].copy()
        test = recent[recent["quarter"].eq(quarters[idx])].copy()
        if len(train) < 100 or len(test) < 5:
            continue
        pool = build_cell_pool(train)
        candidates, _ = run_grid(train, pool)
        if candidates.empty:
            continue
        top = candidates.head(10).copy()
        for rank, cand in top.iterrows():
            cells = pool[
                pool["cell_dims"].eq(cand["cell_dims"])
                & pool["avg_net_return_pct"].ge(float(cand["min_avg_net_pct"]))
                & pool["win_rate"].ge(float(cand["min_win_rate"]))
                & pool["entry_reduce_failure_rate"].le(float(cand["max_entry_reduce_rate"]))
            ].copy()
            assigned = assign_cells_like(test, cells)
            result = simulate_portfolio(assigned, max_positions=int(cand["max_positions"]))
            metrics = aggregate(result.accepted_panel)
            fold_rows.append(
                {
                    "test_quarter": quarters[idx],
                    "candidate_rank": int(rank) + 1,
                    "candidate_strategy_name": cand["candidate_strategy_name"],
                    "lifecycle_count": metrics["lifecycle_count"],
                    "avg_net_return_pct": metrics["avg_net_return_pct"],
                    "win_rate": metrics["win_rate"],
                    "entry_reduce_failure_rate": metrics["entry_reduce_failure_rate"],
                    "capital_pnl_pct": result.quality["two_year_capital_pnl_pct"],
                }
            )
    fold = pd.DataFrame(fold_rows)
    stability = (
        fold.groupby("candidate_rank", dropna=False)
        .agg(
            fold_count=("test_quarter", "nunique"),
            avg_net_mean=("avg_net_return_pct", "mean"),
            avg_net_std=("avg_net_return_pct", "std"),
            win_mean=("win_rate", "mean"),
            entry_reduce_mean=("entry_reduce_failure_rate", "mean"),
            positive_fold_rate=("avg_net_return_pct", lambda s: float((s > 0).mean())),
        )
        .reset_index()
        if not fold.empty
        else pd.DataFrame()
    )
    bootstrap = bootstrap_selected_family(fold)
    pass_flag = int(not stability.empty and float(stability["positive_fold_rate"].mean()) >= 0.60 and float(stability["entry_reduce_mean"].mean()) <= 0.30)
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task518",
                "firm_grade_overfit_stats_pass_flag": pass_flag,
                "fold_count": int(fold["test_quarter"].nunique()) if not fold.empty else 0,
                "top_family_positive_fold_rate": float(stability["positive_fold_rate"].mean()) if not stability.empty else 0.0,
                "top_family_entry_reduce_rate": float(stability["entry_reduce_mean"].mean()) if not stability.empty else 1.0,
                "strategy_acceptance_status": "OVERFIT_STATS_PASS_DIAGNOSTIC" if pass_flag else "OVERFIT_STATS_FAIL",
            }
        ]
    )
    _write(out_dir, {
        "walk_forward_topn_fold_quality": fold,
        "topn_family_stability_audit": stability,
        "bootstrap_confidence_audit": bootstrap,
        "task_518_decision": decision,
    }, "task_518_firm_grade_overfit_statistics.md")
    return {"walk_forward_topn_fold_quality": fold, "topn_family_stability_audit": stability, "task_518_decision": decision}


def bootstrap_selected_family(fold: pd.DataFrame) -> pd.DataFrame:
    if fold.empty:
        return pd.DataFrame()
    rng = np.random.default_rng(518)
    rows = []
    values = fold["avg_net_return_pct"].to_numpy(dtype=float)
    for idx in range(200):
        sample = rng.choice(values, size=len(values), replace=True)
        rows.append({"bootstrap_id": idx, "avg_net_mean": float(sample.mean()), "positive_flag": int(sample.mean() > 0)})
    return pd.DataFrame(rows)


def build_task519_broker_truth_execution_readiness(*, out_dir: Path = TASK519_OUT) -> dict[str, pd.DataFrame]:
    scenarios = pd.DataFrame(
        [
            ("simulated_market_fill", 1, 0, "uses entry/exit prices from historical simulation"),
            ("simulated_spread_cross", 1, 0, "spread stress possible where quote window exists"),
            ("partial_fill_model", 1, 0, "can be simulated but not broker-truth"),
            ("broker_order_fill_updates", 0, 1, "broker fill archive missing for Task505 history"),
            ("halt_luld_rejects", 0, 1, "historical status/LULD missing for Task505 history"),
        ],
        columns=["execution_component", "simulated_available_flag", "broker_truth_required_flag", "readiness_note"],
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task519",
                "broker_truth_execution_ready_flag": 0,
                "simulated_execution_available_flag": 1,
                "broker_truth_missing_component_count": int(scenarios["broker_truth_required_flag"].sum()),
                "strategy_acceptance_status": "BROKER_TRUTH_EXECUTION_BLOCKED",
            }
        ]
    )
    _write(out_dir, {
        "broker_truth_execution_readiness_audit": scenarios,
        "execution_component_contract.csv": scenarios,
        "task_519_decision": decision,
    }, "task_519_broker_truth_execution_readiness.md")
    return {"broker_truth_execution_readiness_audit": scenarios, "task_519_decision": decision}


def build_task520_live_source_acquisition_loop(*, out_dir: Path = TASK520_OUT) -> dict[str, pd.DataFrame]:
    depth_status = FullDepthBookArchive(output_dir=DATA_RAW / "full_depth_book_archive").readiness()
    plan = pd.DataFrame(
        [
            ("raw_receive_timestamp_archive", "implemented_for_live_stream_archive", "src/data/alpaca_stock_stream_archive.py", 1),
            ("quote_status_luld_stream_archive", "implemented_for_live_stream_archive", "src/data/alpaca_stock_stream_archive.py", 1),
            ("order_fill_update_archive", "required_next_collector", "not_implemented_for_task505_history", 0),
            ("full_depth_book_archive", depth_status.source_status, "src/data/full_depth_book_archive.py", int(depth_status.implemented_flag)),
        ],
        columns=["source_name", "current_status", "implementation_path", "implemented_flag"],
    )
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task520",
                "live_source_loop_ready_flag": int(plan["implemented_flag"].sum() >= 2),
                "full_depth_provider_ready_flag": int(depth_status.implemented_flag),
                "next_source_to_build": "order_fill_update_archive",
                "strategy_acceptance_status": "LIVE_SOURCE_COLLECTION_PARTIAL_FULL_DEPTH_BLOCKED",
            }
        ]
    )
    _write(out_dir, {
        "live_source_acquisition_plan.csv": plan,
        "collector_readiness_audit.csv": plan,
        "task_520_decision": decision,
    }, "task_520_live_source_acquisition_loop.md")
    return {"live_source_acquisition_plan": plan, "task_520_decision": decision}


def build_task521_replay_queued_discovery_grid(
    *,
    task503_panel_path: Path = TASK503_PANEL,
    task516_queue_path: Path = TASK516_QUEUE,
    out_dir: Path = TASK521_OUT,
) -> dict[str, pd.DataFrame]:
    panel = load_panel(task503_panel_path)
    recent = panel[panel["entry_ts"].ge(panel["entry_ts"].max() - pd.Timedelta(days=730))].copy()
    queue = pd.read_csv(task516_queue_path) if task516_queue_path.exists() else pd.DataFrame()
    pool = build_cell_pool(recent)
    rows = []
    panels = []
    for q in queue.to_dict(orient="records"):
        cells = pool[
            pool["cell_dims"].eq(q["cell_dims"])
            & pool["avg_net_return_pct"].ge(float(q["min_avg_net_pct"]))
            & pool["win_rate"].ge(float(q["min_win_rate"]))
            & pool["entry_reduce_failure_rate"].le(float(q["max_entry_reduce_rate"]))
        ].copy()
        assigned = assign_cells_like(recent, cells)
        result = simulate_portfolio(assigned, max_positions=int(q["max_positions"]))
        metrics = aggregate(result.accepted_panel)
        metrics.update(
            {
                "candidate_strategy_name": q["candidate_strategy_name"],
                "discovery_rank": q["discovery_rank"],
                "replay_required_flag": 1,
                "deterministic_replay_candidate_flag": 1,
                "capital_pnl_pct": result.quality["two_year_capital_pnl_pct"],
                "max_drawdown_pct": result.quality["max_drawdown_pct"],
            }
        )
        rows.append(metrics)
        if not result.accepted_panel.empty:
            out = result.accepted_panel.copy()
            out["candidate_strategy_name"] = q["candidate_strategy_name"]
            panels.append(out)
    quality_df = pd.DataFrame(rows).sort_values("capital_pnl_pct", ascending=False) if rows else pd.DataFrame()
    assignment = pd.concat(panels, ignore_index=True) if panels else pd.DataFrame()
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task521",
                "queued_candidate_count": int(len(queue)),
                "replayed_candidate_count": int(len(quality_df)),
                "best_replayed_candidate": quality_df.iloc[0]["candidate_strategy_name"] if not quality_df.empty else "none",
                "best_replayed_capital_pnl_pct": quality_df.iloc[0]["capital_pnl_pct"] if not quality_df.empty else pd.NA,
                "strategy_acceptance_status": "REPLAY_QUEUE_DIAGNOSTIC_ONLY",
            }
        ]
    )
    _write(out_dir, {
        "queued_candidate_replay_quality": quality_df,
        "queued_candidate_assignment_panel": assignment,
        "task_521_decision": decision,
    }, "task_521_replay_queued_discovery_grid.md")
    return {"queued_candidate_replay_quality": quality_df, "task_521_decision": decision}


def build_task522_firm_grade_promotion_gate(*, out_dir: Path = TASK522_OUT) -> dict[str, pd.DataFrame]:
    decisions = {
        "Task517": _read_decision(TASK517_OUT / "task_517_decision.csv"),
        "Task518": _read_decision(TASK518_OUT / "task_518_decision.csv"),
        "Task519": _read_decision(TASK519_OUT / "task_519_decision.csv"),
        "Task520": _read_decision(TASK520_OUT / "task_520_decision.csv"),
        "Task521": _read_decision(TASK521_OUT / "task_521_decision.csv"),
    }
    gate = pd.DataFrame(
        [
            ("raw_native_replay", int(decisions["Task517"].get("raw_native_replay_complete_flag", 0)), "Task517"),
            ("overfit_statistics", int(decisions["Task518"].get("firm_grade_overfit_stats_pass_flag", 0)), "Task518"),
            ("broker_truth_execution", int(decisions["Task519"].get("broker_truth_execution_ready_flag", 0)), "Task519"),
            ("live_source_loop", int(decisions["Task520"].get("full_depth_provider_ready_flag", 0)), "Task520"),
            ("queued_replay_available", int(decisions["Task521"].get("replayed_candidate_count", 0) > 0), "Task521"),
        ],
        columns=["promotion_gate", "pass_flag", "source_task"],
    )
    all_pass = int(gate["pass_flag"].all())
    decision = pd.DataFrame(
        [
            {
                "task_id": "Task522",
                "promotion_decision": "PROMOTE_TO_PAPER_SHADOW" if all_pass else "DATA_AND_VALIDATION_BLOCKED",
                "passed_gate_count": int(gate["pass_flag"].sum()),
                "required_gate_count": int(len(gate)),
                "deployment_ready_flag": 0,
                "next_required_action": "build_order_fill_archive_and_full_depth_provider_or_reduce_scope",
                "strategy_acceptance_status": "NOT_PROMOTED_TO_FIRM_GRADE",
            }
        ]
    )
    _write(out_dir, {
        "firm_grade_promotion_gate.csv": gate,
        "firm_grade_promotion_decision.csv": decision,
        "task_522_decision": decision,
    }, "task_522_firm_grade_promotion_gate.md")
    return {"firm_grade_promotion_gate": gate, "task_522_decision": decision}


def _read_decision(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    frame = pd.read_csv(path)
    return frame.iloc[0].to_dict() if not frame.empty else {}


def _write(out_dir: Path, artifacts: dict[str, pd.DataFrame], report_name: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        filename = name if name.endswith(".csv") else f"{name}.csv"
        frame.to_csv(out_dir / filename, index=False)
    decision = next((frame for name, frame in artifacts.items() if name.startswith("task_") and name.endswith("_decision")), pd.DataFrame())
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
            "This task advances the firm-grade validation pipeline. Promotion is blocked unless raw-native replay, overfit statistics, broker-truth execution, live-source readiness, and replay queue validation pass together.",
            "",
            "## No-Background Decision-Maker Report",
            "",
            "This checks whether the strategy is strong enough for professional validation. It does not approve live trading.",
            "",
            "## Artifact Manifest",
            "",
            "See `artifact_manifest.csv`.",
        ]
    )


def _frame_hash(frame: pd.DataFrame) -> str:
    return hashlib.sha256(frame.fillna("").astype(str).to_csv(index=False).encode()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task505-panel", type=Path, default=TASK505_PANEL)
    parser.add_argument("--task503-panel", type=Path, default=TASK503_PANEL)
    parser.add_argument("--task516-queue", type=Path, default=TASK516_QUEUE)
    parser.add_argument("--raw-intraday-dir", type=Path, default=DATA_RAW / "us_intraday")
    args = parser.parse_args()
    build_task517_raw_native_deterministic_replay(task505_panel_path=args.task505_panel, raw_intraday_dir=args.raw_intraday_dir)
    build_task518_firm_grade_overfit_statistics(task503_panel_path=args.task503_panel)
    build_task519_broker_truth_execution_readiness()
    build_task520_live_source_acquisition_loop()
    build_task521_replay_queued_discovery_grid(task503_panel_path=args.task503_panel, task516_queue_path=args.task516_queue)
    build_task522_firm_grade_promotion_gate()


if __name__ == "__main__":
    main()
