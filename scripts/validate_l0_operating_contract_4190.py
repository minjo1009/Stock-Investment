from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = ROOT / "data/artifacts/l0_operating_status/current_l0_status.json"
CONTEXT_PATH = ROOT / "data/artifacts/l0_operating_status/current_l0_context.md"
MANIFEST_PATH = ROOT / "data/artifacts/l0_operating_status/l0_operating_manifest.json"
CONTRACT_PATH = ROOT / "ops/l0_operating_contract.yaml"
BUILDER = ROOT / "scripts/build_l0_operating_status_4190.py"


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return data if isinstance(data, dict) else {}


def run_builder() -> tuple[int, str]:
    proc = subprocess.run(
        [sys.executable, str(BUILDER), "--contract", str(CONTRACT_PATH)],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return proc.returncode, proc.stdout


def is_stale(path: Path, max_age_minutes: int = 60) -> bool:
    if not path.exists():
        return True
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    age = datetime.now(timezone.utc) - mtime
    return age.total_seconds() > max_age_minutes * 60


def collect_failures(status: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    if not CONTRACT_PATH.exists():
        failures.append("L0_CONTRACT_MISSING")
    else:
        passes.append("contract exists")

    for path, code in [
        (STATUS_PATH, "L0_STATUS_MISSING"),
        (CONTEXT_PATH, "L0_CONTEXT_MISSING"),
        (MANIFEST_PATH, "L0_MANIFEST_MISSING"),
    ]:
        if not path.exists():
            failures.append(code)
        else:
            passes.append(f"{path.relative_to(ROOT).as_posix()} exists")

    if is_stale(CONTEXT_PATH):
        failures.append("L0_CONTEXT_STALE")
    else:
        passes.append("current L0 context is fresh")

    blockers = status.get("blockers") or []
    warnings.extend(status.get("warnings") or [])
    pn = status.get("public_newswire") or {}
    scheduler = (status.get("scheduler") or {}).get("realtime") or {}
    config_alignment = status.get("config_alignment") or {}

    if pn.get("aggregate_status") == "RUNNING" and pn.get("launcher_pid_alive") is False:
        if "L0_AGGREGATE_RUNNING_BUT_LAUNCHER_DEAD" not in blockers:
            failures.append("L0_AGGREGATE_RUNNING_BUT_LAUNCHER_DEAD_NOT_REPORTED")
        else:
            passes.append("dead RUNNING public newswire launcher is detected")

    if (pn.get("pending_units") or 0) > 0 or (pn.get("partial_units") or 0) > 0:
        if "L0_PUBLIC_NEWSWIRE_INCOMPLETE" not in blockers:
            failures.append("L0_PUBLIC_NEWSWIRE_INCOMPLETE_NOT_REPORTED")
        else:
            passes.append("public newswire incomplete blocker is explicit")

    if not scheduler.get("exists"):
        if "L0_REALTIME_SCHEDULER_MISSING" not in blockers:
            failures.append("L0_REALTIME_SCHEDULER_MISSING_NOT_REPORTED")
    elif scheduler.get("last_result_status") == "FAILED":
        if "L0_REALTIME_SCHEDULER_LAST_RESULT_FAILED" not in blockers:
            failures.append("L0_REALTIME_SCHEDULER_LAST_RESULT_FAILED_NOT_REPORTED")
        else:
            passes.append("realtime scheduler failure is explicit")

    if not config_alignment.get("aligned"):
        if "L0_REALTIME_CONFIG_SCHEDULER_MISMATCH" not in blockers:
            failures.append("L0_REALTIME_CONFIG_SCHEDULER_MISMATCH_NOT_REPORTED")
    else:
        passes.append("realtime config scheduler aligns with contract")

    if status.get("negative_evidence_conversion") != 0:
        failures.append("L0_NEGATIVE_EVIDENCE_CONVERSION_NONZERO")
    if status.get("broker_mutation_permitted_flag") != 0:
        failures.append("L0_BROKER_MUTATION_FLAG_NONZERO")
    if status.get("live_order_permitted_flag") != 0:
        failures.append("L0_LIVE_ORDER_FLAG_NONZERO")
    if status.get("paper_promotion_permitted_flag") != 0:
        failures.append("L0_PAPER_PROMOTION_FLAG_NONZERO")
    if status.get("real_capital_permitted_flag") != 0:
        failures.append("L0_REAL_CAPITAL_FLAG_NONZERO")

    for blocker in blockers:
        if blocker not in failures:
            failures.append(blocker)

    return passes, warnings, sorted(set(failures))


def print_result(title: str, passes: list[str], warnings: list[str], failures: list[str], exit_code: int) -> int:
    print(title)
    for item in passes:
        print(f"PASS {item}")
    for item in warnings:
        print(f"WARN {item}")
    for item in failures:
        print(f"FAIL {item}")
    if exit_code:
        print("RESULT: FAIL")
    elif warnings:
        print("RESULT: PASS_WITH_WARNINGS")
    else:
        print("RESULT: PASS")
    return exit_code


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["health", "harness"], default="health")
    parser.add_argument("--expect-blocked", action="store_true")
    args = parser.parse_args()

    code, out = run_builder()
    if code != 0:
        return print_result("L0 OPERATING CONTRACT VALIDATION", [], [], [f"L0_STATUS_BUILD_FAILED: {out.strip()}"], 1)

    try:
        status = load_json(STATUS_PATH)
    except Exception as exc:
        return print_result("L0 OPERATING CONTRACT VALIDATION", [], [], [f"L0_STATUS_JSON_INVALID: {exc}"], 1)

    passes, warnings, failures = collect_failures(status)
    blockers = status.get("blockers") or []

    if args.mode == "harness" and args.expect_blocked:
        expected = {
            "L0_AGGREGATE_RUNNING_BUT_LAUNCHER_DEAD",
            "L0_PUBLIC_NEWSWIRE_INCOMPLETE",
        }
        missing = sorted(item for item in expected if item not in blockers)
        if missing:
            return print_result("L0 OPERATING CONTRACT HARNESS VALIDATION", passes, warnings, [f"EXPECTED_BLOCKER_MISSING:{item}" for item in missing], 1)
        passes.append("expected L0 blockers detected")
        harness_failures = [f for f in failures if f.endswith("_NOT_REPORTED") or f.endswith("_NONZERO") or f in {"L0_CONTRACT_MISSING", "L0_STATUS_MISSING", "L0_CONTEXT_MISSING", "L0_MANIFEST_MISSING", "L0_CONTEXT_STALE"}]
        return print_result("L0 OPERATING CONTRACT HARNESS VALIDATION", passes, warnings, harness_failures, 1 if harness_failures else 0)

    if args.mode == "harness":
        structural_failures = [f for f in failures if f.endswith("_NOT_REPORTED") or f.endswith("_NONZERO")]
        return print_result("L0 OPERATING CONTRACT HARNESS VALIDATION", passes, warnings, structural_failures, 1 if structural_failures else 0)

    return print_result("L0 OPERATING CONTRACT HEALTH VALIDATION", passes, warnings, failures, 1 if failures else 0)


if __name__ == "__main__":
    raise SystemExit(main())
