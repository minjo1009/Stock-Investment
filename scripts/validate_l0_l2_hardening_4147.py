from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4147"
SLUG = "task_4147_l0_l2_hardening_gpt_review_and_implementation"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG
CONFIG_PATH = ROOT / "configs" / "l0_realtime_operational_safe_config_4147.json"
SCHEDULER_TASK_NAME = "TraderBrainL0L2Hardening4147"
CRITICAL_BACKFILL_LANES = {"public_newswire_backfill", "public_market_macro_news_backfill"}

FORBIDDEN_FEATURE_COLUMNS = {
    "score",
    "alpha_score",
    "rank",
    "ranking",
    "forward_return",
    "realized_return",
    "order_intent",
    "signal",
    "position_size",
    "broker_order_id",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8", newline="\n")


def as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def scheduler_exists() -> bool:
    try:
        result = subprocess.run(
            ["schtasks.exe", "/Query", "/TN", SCHEDULER_TASK_NAME],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
        )
    except Exception:
        return False
    return result.returncode == 0


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    lines = ["TASK-4147 L0-L2 HARDENING VALIDATION"]
    lines += [f"PASS {item}" for item in passes]
    lines += [f"WARN {item}" for item in warnings]
    lines += [f"FAIL {item}" for item in failures]
    lines.append(f"RESULT: {result}")
    text = "\n".join(lines)
    print(text)
    report = {"task_id": TASK_ID, "result": result, "passes": passes, "warnings": warnings, "failures": failures}
    write_json(ARTIFACT_DIR / "validator_report.json", report)
    md = "# TASK-4147 Validation Results\n\n"
    md += f"Result: `{result}`\n\n"
    for title, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        md += f"## {title}\n\n"
        md += "\n".join(f"- {item}" for item in items) if items else "- none"
        md += "\n\n"
    (REPORT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    (ARTIFACT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    from scripts.run_l0_l2_hardening_4147 import build_and_write

    summary = build_and_write()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    required = [
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "gpt_prompt.md",
        REPORT_DIR / "gpt_response.md",
        REPORT_DIR / "gpt_review_digest_ko.md",
        REPORT_DIR / "l0_l2_hardening_summary.json",
        ARTIFACT_DIR / "l1_article_packets.csv",
        ARTIFACT_DIR / "raw_article_packet_blockers.csv",
        ARTIFACT_DIR / "newswire_mapping_review_queue.csv",
        ARTIFACT_DIR / "newswire_ticker_entity_mapping_rules.json",
        ARTIFACT_DIR / "l2_diagnostic_feature_schema.json",
        ARTIFACT_DIR / "l2_diagnostic_feature_rows.csv",
        ARTIFACT_DIR / "backfill_completion_proof.csv",
        ARTIFACT_DIR / "windows_task_scheduler_registration.json",
        CONFIG_PATH,
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        failures.extend(f"missing required artifact: {path.relative_to(ROOT).as_posix()}" for path in missing)
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    packets = read_csv(ARTIFACT_DIR / "l1_article_packets.csv")
    features = read_csv(ARTIFACT_DIR / "l2_diagnostic_feature_rows.csv")
    mapping = read_csv(ARTIFACT_DIR / "newswire_mapping_review_queue.csv")
    backfill = read_csv(ARTIFACT_DIR / "backfill_completion_proof.csv")
    config = read_json(CONFIG_PATH)
    schema = read_json(ARTIFACT_DIR / "l2_diagnostic_feature_schema.json")

    if len(packets) <= summary.get("l1_article_ready_packets", 0) - 1 and not packets:
        failures.append("article-level L1 packets are empty")
    elif len(packets) <= 30:
        warnings.append(f"article-level packet count is low: {len(packets)}")
    else:
        passes.append(f"l1_article_packets: {len(packets)}")
    ready = [row for row in packets if row.get("l1_status") == "READY"]
    if not ready:
        failures.append("no READY article-level L1 packets")
    else:
        passes.append(f"l1_article_ready_packets: {len(ready)}")
    if len({row.get("l1_article_packet_id") for row in packets}) != len(packets):
        failures.append("duplicate l1_article_packet_id found")
    else:
        passes.append("l1_article_packet_ids_unique")

    if not mapping:
        failures.append("newswire mapping review queue is empty")
    else:
        mapped = sum(as_int(row.get("l0_mapped_rows")) for row in mapping)
        if mapped <= 0:
            warnings.append("newswire queue exists but no L0 mapped rows reported")
        else:
            passes.append(f"newswire_l0_mapped_rows: {mapped}")

    if not features:
        failures.append("L2 diagnostic feature rows are empty")
    else:
        passes.append(f"l2_diagnostic_feature_rows: {len(features)}")
    feature_fields = set(features[0].keys()) if features else set(schema.get("columns", []))
    forbidden = sorted(feature_fields & FORBIDDEN_FEATURE_COLUMNS)
    if forbidden:
        failures.append(f"forbidden feature columns present: {forbidden}")
    else:
        passes.append("feature_schema_has_no_score_signal_order_columns")
    unsafe_rows = [
        row for row in features
        if row.get("diagnostic_only") != "1"
        or row.get("trading_eligible") != "0"
        or row.get("signal_order_export_allowed") != "0"
        or row.get("broker_mutation_permitted") != "0"
    ]
    if unsafe_rows:
        failures.append(f"unsafe diagnostic feature rows: {len(unsafe_rows)}")
    else:
        passes.append("diagnostic_feature_authority_flags_closed")

    permissions = config.get("permissions", {})
    if not config.get("jobs"):
        failures.append("safe realtime config has no jobs")
    elif any(not job.get("enabled") for job in config.get("jobs", [])):
        failures.append("safe realtime config contains disabled job")
    elif not all(job.get("diagnostic_only") for job in config.get("jobs", [])):
        failures.append("safe realtime config contains non-diagnostic job")
    else:
        passes.append(f"safe_realtime_config_jobs_enabled: {len(config.get('jobs', []))}")
    for key in ["execution_permitted", "broker_mutation_permitted", "paper_promotion_permitted", "real_capital_permitted", "live_order_enabled", "buy_sell_signal_generation_permitted"]:
        if permissions.get(key) != 0:
            failures.append(f"unsafe permission opened in config: {key}")
    if not any("permission" in failure for failure in failures):
        passes.append("safe_realtime_config_authority_closed")

    if not backfill:
        failures.append("backfill proof is empty")
    else:
        passes.append(f"backfill_proof_rows: {len(backfill)}")
    if any(row.get("unknown_is_blocker") != "1" for row in backfill):
        failures.append("backfill proof has row where UNKNOWN is not blocker")
    else:
        passes.append("backfill_unknown_is_blocker")
    if any(row.get("trade_authority_flag") != "0" or row.get("broker_mutation_permitted_flag") != "0" or row.get("real_capital_permitted_flag") != "0" for row in backfill):
        failures.append("backfill proof opens forbidden authority")
    else:
        passes.append("backfill_authority_flags_closed")
    blocked_workers = [
        row.get("lane", "")
        for row in backfill
        if row.get("lane") in CRITICAL_BACKFILL_LANES
        and row.get("complete") != "1"
        and row.get("pid_alive") != "1"
    ]
    if blocked_workers:
        failures.append(f"critical incomplete L0 workers are not alive: {blocked_workers}")
    else:
        passes.append("critical_incomplete_backfill_workers_alive_or_complete")
    if any(row.get("proof_status") == "BLOCKED_WORKER_NOT_ALIVE" for row in backfill):
        failures.append("backfill proof contains BLOCKED_WORKER_NOT_ALIVE")

    scheduler_proof = read_json(ARTIFACT_DIR / "windows_task_scheduler_registration.json")
    if scheduler_proof.get("status") == "REGISTERED" or scheduler_exists():
        passes.append(f"windows_task_scheduler_registered: {SCHEDULER_TASK_NAME}")
    else:
        failures.append("Windows Task Scheduler task is not registered")

    if summary.get("trading_eligible_rows") != 0:
        failures.append("summary reports trading eligible rows")
    if summary.get("signal_order_export_allowed_rows") != 0:
        failures.append("summary reports signal/order export rows")
    if summary.get("broker_mutation_permitted_rows") != 0:
        failures.append("summary reports broker mutation rows")
    if summary.get("critical_incomplete_dead_backfill_lanes"):
        failures.append(f"summary reports critical incomplete dead backfill lanes: {summary.get('critical_incomplete_dead_backfill_lanes')}")
    if not any("summary reports" in failure for failure in failures):
        passes.append("summary_authority_counts_zero")

    return emit(passes, warnings, failures)


if __name__ == "__main__":
    sys.exit(main())
