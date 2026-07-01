from __future__ import annotations

import csv
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4148"
SLUG = "task_4148_l0_backfill_worker_recovery_health_gate"
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ARTIFACT_DIR = ROOT / "data" / "artifacts" / SLUG
REPORT_DIR = ROOT / "docs" / "reports" / SLUG
CRITICAL_LANES = {"public_newswire_backfill", "public_market_macro_news_backfill"}
STALE_PROGRESS_MINUTES = 720
STALE_PROCESS_GRACE_MINUTES = 15
STALE_PID_FIXTURE_DIR = ARTIFACT_DIR / "fixtures" / "stale_pid_case"
SCHEDULER_TASK_NAME = "TraderBrainL0BackfillWorkerRecovery4148"


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


def parse_utc(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def age_minutes(value: Any) -> int:
    parsed = parse_utc(value)
    if not parsed:
        return -1
    return max(int((datetime.now(timezone.utc) - parsed).total_seconds() // 60), 0)


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            f"$p=Get-Process -Id {pid} -ErrorAction SilentlyContinue; if ($p) {{ '1' }} else {{ '0' }}",
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
    )
    return result.stdout.strip().endswith("1")


def scheduler_last_result() -> str:
    result = subprocess.run(
        ["schtasks.exe", "/Query", "/TN", SCHEDULER_TASK_NAME, "/FO", "LIST", "/V"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=15,
    )
    if result.returncode != 0:
        return "QUERY_FAILED"
    for line in result.stdout.splitlines():
        if line.strip().startswith("Last Result:"):
            return line.split(":", 1)[1].strip()
    return "MISSING"


def emit(passes: list[str], warnings: list[str], failures: list[str]) -> int:
    result = "FAIL" if failures else "PASS_WITH_WARNINGS" if warnings else "PASS"
    lines = ["TASK-4148 L0 BACKFILL WORKER RECOVERY VALIDATION"]
    lines += [f"PASS {item}" for item in passes]
    lines += [f"WARN {item}" for item in warnings]
    lines += [f"FAIL {item}" for item in failures]
    lines.append(f"RESULT: {result}")
    text = "\n".join(lines)
    print(text)
    report = {"task_id": TASK_ID, "result": result, "passes": passes, "warnings": warnings, "failures": failures}
    write_json(ARTIFACT_DIR / "validator_report.json", report)
    md = "# TASK-4148 Validation Results\n\n"
    md += f"Result: `{result}`\n\n"
    for title, items in [("Passes", passes), ("Warnings", warnings), ("Failures", failures)]:
        md += f"## {title}\n\n"
        md += "\n".join(f"- {item}" for item in items) if items else "- none"
        md += "\n\n"
    (REPORT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    (ARTIFACT_DIR / "validation_results.md").write_text(md, encoding="utf-8", newline="\n")
    return 1 if failures else 0


def main() -> int:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    required = [
        REPORT_DIR / "gpt_prompt.md",
        REPORT_DIR / "gpt_attempt_log.md",
        REPORT_DIR / "report.md",
        REPORT_DIR / "artifact_manifest.csv",
        REPORT_DIR / "summary.json",
        ARTIFACT_DIR / "windows_task_scheduler_registration.json",
        STALE_PID_FIXTURE_DIR / "background_process.json",
        STALE_PID_FIXTURE_DIR / "expected_result.json",
        ARTIFACT_DIR / "l0_worker_recovery_ledger.csv",
        ARTIFACT_DIR / "l0_worker_health_gate.csv",
        ARTIFACT_DIR / "summary.json",
    ]
    missing = [path for path in required if not path.exists()]
    if missing:
        failures.extend(f"missing required artifact: {path.relative_to(ROOT).as_posix()}" for path in missing)
        return emit(passes, warnings, failures)
    passes.append(f"required_artifacts_exist: {len(required)}")

    rows = read_csv(ARTIFACT_DIR / "l0_worker_health_gate.csv")
    by_lane = {row.get("lane", ""): row for row in rows}
    if set(by_lane) != CRITICAL_LANES:
        failures.append(f"critical lane coverage mismatch: {sorted(by_lane)}")
    else:
        passes.append("critical_lanes_have_health_gate_rows")

    for lane in sorted(CRITICAL_LANES):
        row = by_lane.get(lane, {})
        if as_int(row.get("after_complete")) == 0 and as_int(row.get("after_pid_alive")) != 1:
            failures.append(f"{lane} incomplete but worker pid is not alive")
        if as_int(row.get("after_pid_recorded")) <= 0:
            failures.append(f"{lane} has no after pid recorded")
        elif not pid_alive(as_int(row.get("after_pid_recorded"))):
            failures.append(f"{lane} after pid is stale/dead by direct OS check")
        if as_int(row.get("after_pid_alive")) == 1 and str(row.get("after_pid_owner_verified", "")) not in {"1", "True", "true"}:
            warnings.append(f"{lane} pid is alive but pid owner verification is not confirmed")
        progress_age = as_int(row.get("after_progress_age_minutes"))
        process_age = as_int(row.get("after_status_started_age_minutes"))
        if as_int(row.get("after_complete")) == 0 and progress_age >= STALE_PROGRESS_MINUTES and process_age >= STALE_PROCESS_GRACE_MINUTES:
            failures.append(f"{lane} incomplete worker alive but progress is stale: progress_age_minutes={progress_age}")
        if as_int(row.get("after_stop_file_exists")) != 0:
            failures.append(f"{lane} stop file still exists")
        if as_int(row.get("trade_authority_flag")) != 0:
            failures.append(f"{lane} trade authority opened")
        if as_int(row.get("broker_mutation_permitted_flag")) != 0:
            failures.append(f"{lane} broker mutation opened")
        if as_int(row.get("real_capital_permitted_flag")) != 0:
            failures.append(f"{lane} real capital opened")
    if not any("incomplete" in failure or "pid" in failure for failure in failures):
        passes.append("critical_incomplete_workers_have_live_pid")
    if not any("stop file" in failure for failure in failures):
        passes.append("critical_stop_files_absent")
    if not any("opened" in failure for failure in failures):
        passes.append("authority_flags_closed")

    summary = read_json(ARTIFACT_DIR / "summary.json")
    dead_lanes = summary.get("incomplete_dead_lanes", [])
    if dead_lanes:
        failures.append(f"summary reports incomplete dead lanes: {dead_lanes}")
    else:
        passes.append("summary_reports_no_incomplete_dead_lanes")
    if as_int(summary.get("authority_flags_opened")) != 0:
        failures.append("summary reports authority flags opened")
    stale_lanes = summary.get("stale_progress_lanes", [])
    if stale_lanes:
        failures.append(f"summary reports stale progress lanes: {stale_lanes}")

    scheduler = read_json(ARTIFACT_DIR / "windows_task_scheduler_registration.json")
    if as_int(scheduler.get("registered")) != 1:
        failures.append("Windows Task Scheduler guard is not registered")
    else:
        passes.append("windows_task_scheduler_guard_registered")
    last_result = scheduler_last_result()
    if last_result != "0":
        failures.append(f"Windows Task Scheduler guard last result is not 0: {last_result}")
    else:
        passes.append("windows_task_scheduler_guard_last_result_zero")

    if any(as_int(row.get("before_pid_recorded")) > 0 and as_int(row.get("before_pid_alive")) == 0 for row in rows):
        passes.append("stale_pid_condition_captured")
    else:
        passes.append("runtime_stale_pid_condition_not_present")

    fixture_status = read_json(STALE_PID_FIXTURE_DIR / "background_process.json")
    fixture_expected = read_json(STALE_PID_FIXTURE_DIR / "expected_result.json")
    fixture_pid = as_int(fixture_status.get("pid"))
    fixture_alive = pid_alive(fixture_pid)
    if fixture_expected.get("expected_gate_state") != "BLOCKED_WORKER_NOT_ALIVE":
        failures.append("stale pid fixture expected_result is not BLOCKED_WORKER_NOT_ALIVE")
    elif fixture_alive:
        failures.append(f"stale pid fixture unexpectedly alive: pid={fixture_pid}")
    else:
        passes.append("stale_pid_regression_fixture_passed")

    return emit(passes, warnings, failures)


if __name__ == "__main__":
    raise SystemExit(main())
