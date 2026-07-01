from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASK_ID = "TASK-4146"
SLUG = "task_4146_l0_l2_wide_packetization_handoff"
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG

FORBIDDEN_COLUMNS = {
    "score",
    "alpha_score",
    "rank",
    "ranking",
    "realized_return",
    "forward_return",
    "order_intent",
    "signal",
    "position_size",
    "broker_order_id",
}
CRITICAL_BACKFILL_LANES = {"public_newswire_backfill", "public_market_macro_news_backfill"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    print("TASK-4146 L0-L2 WIDE HANDOFF VALIDATION")
    for item in passes:
        print(f"PASS {item}")
    for item in warnings:
        print(f"WARN {item}")
    for item in failures:
        print(f"FAIL {item}")
    print(f"RESULT: {result}")
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = {"task_id": TASK_ID, "result": result, "passes": passes, "warnings": warnings, "failures": failures}
    (ARTIFACT_DIR / "validator_report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")
    md = "# TASK-4146 Validation Results\n\n"
    md += f"Result: `{result}`\n\n"
    for title, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        md += f"## {title}\n\n"
        md += "\n".join(f"- {item}" for item in items) if items else "- none"
        md += "\n\n"
    (REPORT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    (ARTIFACT_DIR / "l0_l2_wide_handoff_validation_report.md").write_text(md, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def as_int(value: object) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def main() -> int:
    from scripts.run_l0_l2_wide_handoff_4146 import build_and_write

    summary = build_and_write()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    required = [
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "l0_l2_wide_handoff_summary.json",
        ARTIFACT_DIR / "l0_wide_source_ledger.csv",
        ARTIFACT_DIR / "l1_wide_normalized_source_packets.csv",
        ARTIFACT_DIR / "l2_wide_admission_view.csv",
        ARTIFACT_DIR / "l2_feature_materialization_candidates.csv",
        ARTIFACT_DIR / "l0_stopped_lane_recovery.csv",
        ARTIFACT_DIR / "continuous_handoff_plan.csv",
        ARTIFACT_DIR / "continuous_handoff_loop_status.json",
        ARTIFACT_DIR / "source_family_rollup.csv",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        failures.extend(f"missing artifact: {path.relative_to(ROOT).as_posix()}" for path in missing)
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    l0_rows = read_csv(ARTIFACT_DIR / "l0_wide_source_ledger.csv")
    l1_rows = read_csv(ARTIFACT_DIR / "l1_wide_normalized_source_packets.csv")
    l2_rows = read_csv(ARTIFACT_DIR / "l2_wide_admission_view.csv")
    feature_rows = read_csv(ARTIFACT_DIR / "l2_feature_materialization_candidates.csv")
    lane_rows = read_csv(ARTIFACT_DIR / "l0_stopped_lane_recovery.csv")
    continuous_rows = read_csv(ARTIFACT_DIR / "continuous_handoff_plan.csv")
    rollup_rows = read_csv(ARTIFACT_DIR / "source_family_rollup.csv")
    loop_status = json.loads((ARTIFACT_DIR / "continuous_handoff_loop_status.json").read_text(encoding="utf-8-sig"))

    if len(l0_rows) <= 30:
        failures.append(f"L0 wide ledger is not wider than prior TASK-4144 audit sample: {len(l0_rows)}")
    else:
        passes.append(f"l0_wide_rows: {len(l0_rows)}")
    if len(l1_rows) != len(l0_rows):
        failures.append("L1 packet count does not match L0 source ledger count")
    else:
        passes.append(f"l1_packet_rows: {len(l1_rows)}")
    if len(l2_rows) != len(l1_rows):
        failures.append("L2 admission rows do not match L1 packet count")
    else:
        passes.append(f"l2_rows: {len(l2_rows)}")
    if not feature_rows:
        failures.append("diagnostic feature materialization candidates are empty")
    else:
        passes.append(f"feature_candidate_materialization_rows: {len(feature_rows)}")

    family_set = {row.get("source_family") for row in rollup_rows}
    expected = {"public_context_news_feeds", "public_market_macro_news_feeds", "public_newswire_feeds"}
    if family_set != expected:
        failures.append(f"source family rollup mismatch: {sorted(family_set)}")
    else:
        passes.append("source_family_rollup_covers_target_families")

    ready_packets = [row for row in l1_rows if not str(row.get("l1_gate_classification", "")).startswith("BLOCKED")]
    if len(ready_packets) <= 3:
        failures.append("wide L1 did not improve beyond prior 3-row sample")
    else:
        passes.append(f"wide_l1_ready_packet_rows: {len(ready_packets)}")
    l2_open = [row for row in l2_rows if str(row.get("admission_status", "")).startswith("L2_")]
    if len(l2_open) <= 3:
        failures.append("wide L2 did not improve beyond prior 3-row admission")
    else:
        passes.append(f"wide_l2_admitted_or_review_rows: {len(l2_open)}")

    for row in l1_rows:
        row_id = row.get("source_packet_id", "")
        if row.get("missing_source_is_negative") != "0":
            failures.append(f"missing source treated as negative: {row_id}")
        if row.get("assignment_uses_future_outcome") != "0" or row.get("outcome_used_for_assignment") != "0":
            failures.append(f"future/outcome assignment flag opened: {row_id}")
        if row.get("source_time_certified") == "1" and (not row.get("raw_path") or not row.get("raw_sha256")):
            failures.append(f"source-time certified packet missing raw lineage: {row_id}")
    if not any("negative" in failure or "future" in failure or "lineage" in failure for failure in failures):
        passes.append("l1_safety_flags_and_lineage_valid")

    l2_fields = set(l2_rows[0].keys()) if l2_rows else set()
    forbidden = sorted(l2_fields & FORBIDDEN_COLUMNS)
    if forbidden:
        failures.append(f"L2 wide view exposes forbidden trading/scoring columns: {forbidden}")
    else:
        passes.append("l2_wide_view_has_no_score_signal_order_columns")
    if any(row.get("trading_authority_opened") != "0" for row in l2_rows):
        failures.append("trading authority opened in L2 wide view")
    if any(row.get("paper_live_broker_order_opened") != "0" for row in l2_rows):
        failures.append("paper/live/broker/order opened in L2 wide view")
    if not any("opened" in failure for failure in failures):
        passes.append("trading_paper_live_broker_order_gates_closed")

    feature_count = sum(as_int(row.get("feature_candidate_count")) for row in feature_rows)
    if feature_count <= 3:
        failures.append(f"feature candidate count did not materially expand: {feature_count}")
    else:
        passes.append(f"feature_candidate_count: {feature_count}")
    if any(row.get("feature_materialization_scope") != "diagnostic_batch_candidate_only_no_signal" for row in feature_rows):
        failures.append("feature materialization row has unsafe scope")
    else:
        passes.append("feature_materialization_scope_is_diagnostic_only")

    if len(continuous_rows) < 3:
        failures.append("continuous handoff plan is missing required steps")
    else:
        passes.append(f"continuous_handoff_steps: {len(continuous_rows)}")
    if as_int(loop_status.get("pid")) <= 0:
        failures.append("continuous handoff loop has no recorded pid")
    elif loop_status.get("diagnostic_only_flag") != 1 or loop_status.get("trade_authority_flag") != 0:
        failures.append("continuous handoff loop safety flags are invalid")
    else:
        passes.append(f"continuous_handoff_loop_pid_recorded: {loop_status.get('pid')}")
    restart_rows = [row for row in lane_rows if as_int(row.get("background_pid_recorded_after_supervisor")) > 0]
    if not restart_rows:
        warnings.append("no background PID recorded in stopped lane recovery rows")
    else:
        passes.append(f"background_pid_rows_recorded: {len(restart_rows)}")
    live_restart_rows = [row for row in lane_rows if as_int(row.get("background_pid_alive_after_supervisor")) > 0]
    if live_restart_rows:
        passes.append(f"background_pid_rows_alive: {len(live_restart_rows)}")
    for row in lane_rows:
        lane = row.get("lane", "")
        if lane in CRITICAL_BACKFILL_LANES and as_int(row.get("complete_at_audit")) == 0 and as_int(row.get("background_pid_alive_after_supervisor")) != 1:
            failures.append(f"critical incomplete L0 worker is not alive: {lane}")

    if summary.get("l0_batch_rows") != len(l0_rows):
        failures.append("summary l0_batch_rows mismatch")
    if summary.get("l1_packet_rows") != len(l1_rows):
        failures.append("summary l1_packet_rows mismatch")
    if summary.get("l2_rows") != len(l2_rows):
        failures.append("summary l2_rows mismatch")
    if summary.get("trading_authority_opened_rows") != 0 or summary.get("paper_live_broker_order_opened_rows") != 0:
        failures.append("summary reports forbidden authority opened")
    if not any("summary" in failure for failure in failures):
        passes.append("summary_counts_match_artifacts")

    return emit(passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
