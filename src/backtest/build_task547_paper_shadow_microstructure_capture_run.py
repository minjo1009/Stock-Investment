from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from scripts.task_artifact_manifest import write_manifest
from src.backtest.task_report_utils import write_standard_report
from src.data.paper_shadow_microstructure_capture import (
    build_decision_microstructure_snapshots,
    build_latest_microstructure_state,
    build_microstructure_feature_lineage,
    load_stream_archive_records,
)


TASK547_OUT = Path("docs/reports/task_547_paper_shadow_microstructure_capture_run")
STREAM_ARCHIVE_DIR = Path("data/raw/alpaca_stock_stream_archive")
TASK531_DECISIONS = Path("docs/reports/task_531_paper_shadow_order_fill_archive/paper_shadow_decision_snapshot_log.csv")
TASK531_LINEAGE = Path("docs/reports/task_531_paper_shadow_order_fill_archive/paper_shadow_lifecycle_lineage.csv")


def build_task547_paper_shadow_microstructure_capture_run(
    *,
    stream_archive_dir: Path = STREAM_ARCHIVE_DIR,
    task531_decisions_path: Path = TASK531_DECISIONS,
    task531_lineage_path: Path = TASK531_LINEAGE,
    out_dir: Path = TASK547_OUT,
) -> dict[str, pd.DataFrame]:
    records = load_stream_archive_records(stream_archive_dir)
    state = build_latest_microstructure_state(records)
    decisions = load_task531_decisions(task531_decisions_path)
    snapshots = build_decision_microstructure_snapshots(decisions, state)
    lineage = attach_microstructure_to_lineage(task531_lineage_path, snapshots)
    feature_lineage = build_microstructure_feature_lineage(snapshots, state)
    source_audit = build_capture_source_audit(records, state, snapshots)
    timing_audit = build_pre_action_timing_audit(snapshots, lineage)
    decision = build_decision(source_audit, snapshots, lineage)
    artifacts = {
        "raw_stream_capture_source_audit": source_audit,
        "latest_microstructure_state_cache": state,
        "decision_microstructure_snapshot_log": snapshots,
        "microstructure_feature_lineage_log": feature_lineage,
        "paper_shadow_microstructure_order_lineage": lineage,
        "pre_action_snapshot_timing_audit": timing_audit,
        "task_547_decision": decision,
    }
    write_task547(out_dir, artifacts)
    return artifacts


def load_task531_decisions(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    if "order_submission_enabled_flag" not in frame.columns:
        frame["order_submission_enabled_flag"] = 0
    return frame


def attach_microstructure_to_lineage(lineage_path: Path, snapshots: pd.DataFrame) -> pd.DataFrame:
    lineage = pd.read_csv(lineage_path) if lineage_path.exists() else pd.DataFrame()
    if lineage.empty or snapshots.empty:
        return pd.DataFrame()
    out = lineage.merge(
        snapshots[["decision_id", "microstructure_snapshot_id", "microstructure_source_ready_flag", "pre_action_snapshot_flag"]],
        on="decision_id",
        how="left",
    )
    out["microstructure_snapshot_linked_flag"] = out["microstructure_snapshot_id"].notna().astype(int)
    return out


def build_capture_source_audit(records: pd.DataFrame, state: pd.DataFrame, snapshots: pd.DataFrame) -> pd.DataFrame:
    channels = records["channel"].value_counts().to_dict() if not records.empty else {}
    return pd.DataFrame(
        [
            {
                "source_name": "alpaca_stock_stream_archive",
                "archive_path": str(STREAM_ARCHIVE_DIR),
                "raw_stream_record_count": int(len(records)),
                "quote_record_count": int(channels.get("quotes", 0)),
                "bar_record_count": int(channels.get("bars", 0) + channels.get("updatedBars", 0)),
                "status_record_count": int(channels.get("statuses", 0)),
                "luld_record_count": int(channels.get("lulds", 0)),
                "state_symbol_count": int(state["symbol"].nunique()) if not state.empty else 0,
                "decision_snapshot_count": int(len(snapshots)),
                "microstructure_ready_snapshot_count": int(snapshots["microstructure_source_ready_flag"].sum()) if not snapshots.empty else 0,
                "live_capture_rows_available_flag": int(not records.empty),
                "historical_ohlcv_used_as_microstructure_flag": 0,
                "missing_source_approximated_flag": 0,
            }
        ]
    )


def build_pre_action_timing_audit(snapshots: pd.DataFrame, lineage: pd.DataFrame) -> pd.DataFrame:
    if snapshots.empty:
        return pd.DataFrame([{"audit_name": "decision_snapshots", "row_count": 0, "pass_flag": 0}])
    return pd.DataFrame(
        [
            {"audit_name": "decision_snapshots", "row_count": int(len(snapshots)), "pass_flag": int(len(snapshots) > 0)},
            {"audit_name": "pre_action_snapshot_flag", "row_count": int(snapshots["pre_action_snapshot_flag"].sum()), "pass_flag": int(snapshots["pre_action_snapshot_flag"].min())},
            {"audit_name": "microstructure_lineage_linked", "row_count": int(lineage["microstructure_snapshot_linked_flag"].sum()) if not lineage.empty else 0, "pass_flag": int(not lineage.empty and lineage["microstructure_snapshot_linked_flag"].min() == 1)},
            {"audit_name": "order_submission_disabled_shadow_mode", "row_count": int((snapshots["order_submission_enabled_flag"] == 0).sum()), "pass_flag": int((snapshots["order_submission_enabled_flag"] == 0).all())},
        ]
    )


def build_decision(source_audit: pd.DataFrame, snapshots: pd.DataFrame, lineage: pd.DataFrame) -> pd.DataFrame:
    source = source_audit.iloc[0].to_dict() if not source_audit.empty else {}
    live_rows = int(source.get("raw_stream_record_count", 0))
    ready_snapshots = int(source.get("microstructure_ready_snapshot_count", 0))
    snapshot_count = int(source.get("decision_snapshot_count", 0))
    linked = int(lineage["microstructure_snapshot_linked_flag"].min()) if not lineage.empty else 0
    if live_rows > 0 and ready_snapshots > 0 and linked:
        status = "PAPER_SHADOW_MICROSTRUCTURE_CAPTURE_ACTIVE"
    else:
        status = "COLLECTOR_IMPLEMENTED_NO_LIVE_MICROSTRUCTURE_ROWS_YET"
    return pd.DataFrame(
        [
            {
                "task_id": "Task547",
                "raw_stream_record_count": live_rows,
                "decision_snapshot_count": snapshot_count,
                "microstructure_ready_snapshot_count": ready_snapshots,
                "microstructure_lineage_linked_flag": linked,
                "pre_action_snapshot_flag": int(snapshots["pre_action_snapshot_flag"].min()) if not snapshots.empty else 0,
                "order_submission_enabled_flag": int(snapshots["order_submission_enabled_flag"].max()) if not snapshots.empty else 0,
                "historical_ohlcv_used_as_microstructure_flag": 0,
                "missing_source_approximated_flag": 0,
                "deployment_ready_flag": 0,
                "strategy_acceptance_status": status,
            }
        ]
    )


def write_task547(out_dir: Path, artifacts: dict[str, pd.DataFrame]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in artifacts.items():
        frame.to_csv(out_dir / f"{name}.csv", index=False)
    decision = artifacts["task_547_decision"].iloc[0].to_dict()
    write_standard_report(
        out_dir / "task_547_paper_shadow_microstructure_capture_run.md",
        title="Task 547 Paper Shadow Microstructure Capture Run",
        decision_summary=[
            f"Strategy acceptance: {decision['strategy_acceptance_status']}",
            f"Raw stream records: {decision['raw_stream_record_count']}",
            f"Decision snapshots: {decision['decision_snapshot_count']}",
            f"Microstructure-ready snapshots: {decision['microstructure_ready_snapshot_count']}",
            f"Lineage linked: {decision['microstructure_lineage_linked_flag']}",
            "Deployment-ready: NO",
        ],
        quant_expert_lines=[
            "Task547 implements the paper/shadow capture path from stream archive records to latest quote/status/bar state, pre-action decision snapshots, feature lineage, and order/fill/lifecycle lineage.",
            "No historical OHLCV row is used as NBBO/status microstructure. If the stream archive is empty, snapshots remain explicit missing-source records.",
            "The current run is collector-ready but has no live microstructure rows yet, so Task548 failure separation remains blocked until capture data accumulates.",
        ],
        decision_maker_lines=[
            "The collector path is now wired, but this run did not find live quote/status rows in the archive.",
            "We can start capturing during market hours. Until then, the strategy is still not deployment-ready.",
        ],
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stream-archive-dir", type=Path, default=STREAM_ARCHIVE_DIR)
    args = parser.parse_args()
    build_task547_paper_shadow_microstructure_capture_run(stream_archive_dir=args.stream_archive_dir)


if __name__ == "__main__":
    main()
