from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_3221_3280_backend_acceleration_program"
OUT_DIR = ROOT / "data" / "artifacts" / TASK_ID
TASK3142_OUT = ROOT / "data" / "artifacts" / "task_3142_external_tool_infra_module_promotion"
TASK3143_OUT = ROOT / "data" / "artifacts" / "task_3143_external_tool_typed_contract"
SCRIPT3142 = ROOT / "scripts" / "trader_brain_3142_external_tool_infra_module_promotion.py"
SCRIPT3143 = ROOT / "scripts" / "trader_brain_3143_external_tool_typed_contract.py"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise AssertionError(f"missing artifact: {path}")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    if not fieldnames:
        fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    regenerate_commands = [
        [sys.executable, "scripts/trader_brain_3142_external_tool_infra_module_promotion.py"],
        [sys.executable, "scripts/trader_brain_3143_external_tool_typed_contract.py"],
    ]
    command_rows = []
    for command in regenerate_commands:
        completed = subprocess.run(command, cwd=ROOT, text=True, encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
        command_rows.append(
            {
                "command": " ".join(command),
                "returncode": completed.returncode,
                "stdout_tail": completed.stdout[-1000:],
                "stderr_tail": completed.stderr[-1000:],
            }
        )
    text3142 = SCRIPT3142.read_text(encoding="utf-8")
    text3143 = SCRIPT3143.read_text(encoding="utf-8")
    replay3142 = read_csv(TASK3142_OUT / "module_replay_result.csv")
    parity3143 = read_csv(TASK3143_OUT / "typed_parity_result.csv")

    forbidden_direct_tokens = [
        "polars_strict_gate_aggregate(",
        "duckdb_strict_gate_aggregate(",
        "pandas_strict_gate_aggregate(",
        "polars_strict_gate_aggregate_result(",
        "duckdb_strict_gate_aggregate_result(",
        "pandas_strict_gate_aggregate_result(",
    ]
    checks = [
        {"check_name": "task3142_3143_regenerated_current_artifacts", "pass": int(all(row["returncode"] == 0 for row in command_rows))},
        {"check_name": "task3142_uses_core_accelerator", "pass": int("strict_gate_aggregate_accelerated" in text3142)},
        {"check_name": "task3143_uses_core_accelerator", "pass": int("strict_gate_aggregate_accelerated" in text3143)},
        {"check_name": "task3142_direct_aggregate_calls_removed", "pass": int(not any(token in text3142 for token in forbidden_direct_tokens))},
        {"check_name": "task3143_direct_aggregate_calls_removed", "pass": int(not any(token in text3143 for token in forbidden_direct_tokens))},
        {"check_name": "task3142_reference_matches_preserved", "pass": int(all(row["reference_match"] == "1" for row in replay3142))},
        {"check_name": "task3143_parity_preserved", "pass": int(all(row["parity_pass"] == "1" for row in parity3143))},
    ]
    rows = [
        {
            "lane": "source_panel",
            "authority": "PACKAGE_HEALTH",
            "task3142_rows": len(replay3142),
            "task3143_rows": len(parity3143),
            "source_acquisition_performed": 0,
            "replay_performed": 0,
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
        }
    ]
    write_csv(OUT_DIR / "source_panel_acceleration_result.csv", rows)
    write_csv(OUT_DIR / "source_panel_regeneration_commands.csv", command_rows)
    write_csv(OUT_DIR / "source_panel_acceptance_checks.csv", checks)
    failed = [row for row in checks if row["pass"] != 1]
    if failed:
        for row in failed:
            print(f"[TASK3261_3270_ERROR] {row['check_name']}")
        return 1
    print("[TASK3261_3270_SOURCE_PANEL_ACCELERATION_OK]")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
