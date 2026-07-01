from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TASK_ID = "TASK-4135"
SLUG = "task_4135_l1_final_hardening_l2_gpt_consult"
DATA_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG
GPT_CAPTURE_STATUSES = {
    "PENDING_CAPTURE",
    "PENDING_USER_CHROME_PERMISSION",
    "CAPTURED",
    "BLOCKED_AUTOMATION_NO_GPT_CAPTURE",
    "BLOCKED_CHROME_EXTENSION_COMMUNICATION",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    print("L1 FINAL HARDENING L2 CONSULT VALIDATION")
    for item in passes:
        print(f"PASS {item}")
    for item in warnings:
        print(f"WARN {item}")
    for item in failures:
        print(f"FAIL {item}")
    print(f"RESULT: {result}")
    report = {"task_id": TASK_ID, "result": result, "passes": passes, "warnings": warnings, "failures": failures}
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "validator_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8", newline="\n")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    markdown = f"# TASK-4135 Validation Results\n\nResult: `{result}`\n\n"
    for label, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        markdown += f"## {label}\n\n"
        markdown += "\n".join(f"- {item}" for item in items) if items else "- none"
        markdown += "\n\n"
    (REPORT_DIR / "validation_results.md").write_text(markdown, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    from scripts.run_l1_final_hardening_l2_consult_prep import main as run_main

    run_main()
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []
    required = [
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "l2_gpt_local_context_packet.md",
        REPORT_DIR / "l2_gpt_prompt.md",
        REPORT_DIR / "l2_gpt_response.md",
        REPORT_DIR / "l1_final_hardening_l2_consult_summary.json",
        DATA_DIR / "l1_l2_handoff_contract.csv",
        DATA_DIR / "l1_coverage_audit.csv",
        DATA_DIR / "l1_remaining_risk_register.csv",
        DATA_DIR / "gpt_consult_ledger.csv",
    ]
    for path in required:
        if not path.exists():
            failures.append(f"missing artifact: {path.relative_to(ROOT).as_posix()}")
    if failures:
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")
    handoff = read_csv(DATA_DIR / "l1_l2_handoff_contract.csv")
    coverage = read_csv(DATA_DIR / "l1_coverage_audit.csv")
    ledger = read_csv(DATA_DIR / "gpt_consult_ledger.csv")
    prompt = (REPORT_DIR / "l2_gpt_prompt.md").read_text(encoding="utf-8")
    if "Do not use GitHub" not in prompt or "not committed" not in prompt:
        failures.append("GPT prompt does not explicitly forbid GitHub and explain local uncommitted state")
    else:
        passes.append("gpt_prompt_forbids_github")
    if not handoff:
        failures.append("handoff contract has no rows")
    if any(row.get("trading_authority") != "0" or row.get("l2_write_allowed_by_task") != "0" for row in handoff):
        failures.append("handoff contract opens trading authority or L2 writes")
    else:
        passes.append(f"handoff_rows_diagnostic_only: {len(handoff)}")
    strict_families = {row["source_family"] for row in handoff if row.get("l1_classification") == "STRICT_SOURCE_TIME_CERTIFIED"}
    if not {"daily_bars", "market_bars_5m"}.issubset(strict_families):
        failures.append("strict handoff missing daily_bars or market_bars_5m")
    else:
        passes.append("strict_market_families_present")
    if not all(row.get("known_gap_count") == "0" for row in coverage):
        failures.append("coverage audit reports unexpected known gaps")
    else:
        passes.append(f"coverage_rows_no_known_gaps: {len(coverage)}")
    if not ledger or ledger[0].get("capture_status") not in GPT_CAPTURE_STATUSES:
        failures.append("GPT consult ledger has invalid capture status")
    else:
        passes.append(f"gpt_capture_status_recorded: {ledger[0].get('capture_status')}")
    return emit(passes, warnings, failures)


if __name__ == "__main__":
    raise SystemExit(main())
