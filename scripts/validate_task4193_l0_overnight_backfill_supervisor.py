from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


TASK_ID = "TASK-4193"
ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_DIR = ROOT / "data" / "artifacts" / "task_4193_l0_overnight_backfill_completion_run"
REPORT_DIR = ROOT / "docs" / "reports" / "task_4193_l0_overnight_backfill_completion_run"
STATUS_PATH = ARTIFACT_DIR / "supervisor_status.json"
BACKGROUND_PATH = ARTIFACT_DIR / "background_process.json"


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return default


def as_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def as_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


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


def print_result(title: str, passes: list[str], warnings: list[str], failures: list[str]) -> int:
    print(f"# {title}")
    for row in passes:
        print(f"PASS: {row}")
    for row in warnings:
        print(f"WARN: {row}")
    for row in failures:
        print(f"FAIL: {row}")
    if failures:
        print("VERDICT: FAIL")
        return 1
    if warnings:
        print("VERDICT: PASS_WITH_WARNINGS")
    else:
        print("VERDICT: PASS")
    return 0


def main() -> int:
    passes: list[str] = []
    warnings: list[str] = []
    failures: list[str] = []

    if not BACKGROUND_PATH.exists():
        failures.append(f"missing background process file: {BACKGROUND_PATH}")
    if not STATUS_PATH.exists():
        failures.append(f"missing supervisor status file: {STATUS_PATH}")
    if failures:
        return print_result("TASK-4193 L0 OVERNIGHT SUPERVISOR", passes, warnings, failures)

    background = read_json(BACKGROUND_PATH, {})
    status = read_json(STATUS_PATH, {})
    supervisor_pid = as_int(background.get("pid")) if isinstance(background, dict) else 0
    if not pid_alive(supervisor_pid):
        failures.append(f"supervisor pid is not alive: {supervisor_pid}")
    else:
        passes.append(f"supervisor_pid_alive:{supervisor_pid}")

    safety = status.get("safety", {}) if isinstance(status, dict) else {}
    for key in [
        "trade_authority_flag",
        "broker_mutation_permitted_flag",
        "live_order_permitted_flag",
        "paper_promotion_permitted_flag",
        "real_capital_permitted_flag",
    ]:
        if as_int(safety.get(key)) != 0:
            failures.append(f"safety flag opened: {key}={safety.get(key)}")
    passes.append("trading_safety_flags_closed")

    newswire = status.get("public_newswire", {}) if isinstance(status, dict) else {}
    newswire_pending = as_int(newswire.get("pending_units"))
    if newswire_pending > 0:
        if as_int(newswire.get("pid_alive")) != 1:
            failures.append("public newswire pending but launcher pid is not alive")
        elif as_int(newswire.get("pid_owner_verified")) != 1:
            failures.append("public newswire pending but launcher pid owner not verified")
        else:
            passes.append(f"public_newswire_running_with_pending:{newswire_pending}")
    else:
        passes.append("public_newswire_no_pending_units")

    market = status.get("public_market_macro_news", {}) if isinstance(status, dict) else {}
    market_pending = as_int(market.get("pending_units"))
    if market_pending > 0:
        if as_int(market.get("pid_alive")) != 1:
            failures.append("market/macro pending but collector pid is not alive")
        elif as_int(market.get("pid_owner_verified")) != 1:
            failures.append("market/macro pending but collector pid owner not verified")
        else:
            passes.append(f"market_macro_running_with_pending:{market_pending}")
    else:
        passes.append("market_macro_no_pending_units")

    bars = status.get("bars", {}) if isinstance(status, dict) else {}
    daily_pct = as_float(bars.get("daily_progress_pct"))
    if daily_pct < 99.0:
        warnings.append(f"daily bars are below 99pct: {daily_pct}")
    else:
        passes.append(f"daily_bars_effectively_complete:{daily_pct}")

    five_pct = as_float(bars.get("five_min_progress_pct"))
    if five_pct < 100.0:
        if as_int(bars.get("five_min_pid_alive")) != 1:
            failures.append("5m bars incomplete but collector pid is not alive")
        else:
            passes.append(f"five_min_running_with_progress_pct:{five_pct}")
    else:
        passes.append("five_min_no_pending_progress")

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    validation_text = ["# Validation Results - TASK-4193", ""]
    validation_text.extend(f"- PASS: {row}" for row in passes)
    validation_text.extend(f"- WARN: {row}" for row in warnings)
    validation_text.extend(f"- FAIL: {row}" for row in failures)
    validation_text.append("")
    validation_text.append(f"VERDICT: {'FAIL' if failures else ('PASS_WITH_WARNINGS' if warnings else 'PASS')}")
    (REPORT_DIR / "validation_results.md").write_text("\n".join(validation_text) + "\n", encoding="utf-8", newline="\n")

    return print_result("TASK-4193 L0 OVERNIGHT SUPERVISOR", passes, warnings, failures)


if __name__ == "__main__":
    raise SystemExit(main())
