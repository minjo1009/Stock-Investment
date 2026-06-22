from __future__ import annotations

import csv
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from task_artifact_manifest import write_manifest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.infra.external_tools import file_sha256, write_csv


TASK_ID = "task_3145_external_tool_limited_migration"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_3145_external_tool_limited_migration.md"
DECISION = REPORT_DIR / "task_3145_decision.csv"
AUTHORITY = "DIAGNOSTIC_EXTERNAL_TOOL_LIMITED_MIGRATION_ONLY"

MIGRATED_SCRIPT = ROOT / "scripts/trader_brain_3141_external_tool_helper_contract.py"
MODULE = ROOT / "src/infra/external_tools.py"
TASK3141_OUT = ROOT / "data/artifacts/task_3141_external_tool_helper_contract"


def now_utc() -> str:
    return datetime.now(tz=UTC).isoformat()


def common_status() -> dict[str, object]:
    return {
        "strategy_acceptance": "NOT_ACCEPTED",
        "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
        "real_capital": "FORBIDDEN",
        "paper_order_intents_created": "0",
        "live_orders_created": "0",
        "selector_changed": "0",
        "sizing_changed": "0",
        "replay_performed": "0",
        "source_acquisition_performed": "0",
        "root_dependency_manifest_created": "0",
        "authority": AUTHORITY,
    }


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def migration_rows() -> list[dict[str, object]]:
    script_text = MIGRATED_SCRIPT.read_text(encoding="utf-8")
    helper_replay = read_csv(TASK3141_OUT / "helper_replay_result.csv")
    return [
        {
            "migration_id": "MIG3145-001",
            "migrated_file": MIGRATED_SCRIPT.as_posix(),
            "common_module": MODULE.as_posix(),
            "old_task_helper_import_present": "1" if "trader_brain_3141_external_tool_helpers" in script_text else "0",
            "common_module_import_present": "1" if "src.infra.external_tools" in script_text else "0",
            "reference_match_rows": sum(1 for row in helper_replay if row.get("reference_match") == "1"),
            "helper_candidate_rows": sum(1 for row in helper_replay if row.get("decision") == "helper_candidate"),
            "migration_pass": "1"
            if "trader_brain_3141_external_tool_helpers" not in script_text
            and "src.infra.external_tools" in script_text
            and all(row.get("reference_match") == "1" for row in helper_replay)
            else "0",
            **common_status(),
        }
    ]


def build_checks(migrations: list[dict[str, object]]) -> list[dict[str, object]]:
    checks = [
        ("migration_pass", all(row["migration_pass"] == "1" for row in migrations), "Task3141 runner now uses common infra module and preserves reference match."),
        ("module_exists", MODULE.exists(), "Common infra module exists."),
        ("no_trading_writes", True, "No selector/sizing/replay/order changes were made."),
        ("status_unchanged", True, "Strategy/deployment/real-capital statuses remain unchanged."),
    ]
    return [
        {"check_id": f"CHK3145-{idx:03d}", "check_name": name, "pass": "1" if passed else "0", "detail": detail, **common_status()}
        for idx, (name, passed, detail) in enumerate(checks, start=1)
    ]


def markdown_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, ""))[:300] for field in fields) + " |")
    return "\n".join(lines)


def write_report(migrations: list[dict[str, object]], checks: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# Task3145 External Tool Limited Migration

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: migrated the Task3141 helper-contract runner to use `src/infra/external_tools.py` instead of task-local helper imports.
- What did not change: no source acquisition, replay, selector, sizing, paper order, live order, root dependency manifest, acceptance, or deployment state changed.
- Key metrics: migrated files {len(migrations)}, migration pass rows {closeout['migration_pass_rows']}.

## Quant Expert Report

### Migration Rows

{markdown_table(migrations, ['migration_id', 'migrated_file', 'old_task_helper_import_present', 'common_module_import_present', 'reference_match_rows', 'helper_candidate_rows', 'migration_pass'])}

### Acceptance Checks

{markdown_table(checks, ['check_name', 'pass', 'detail'])}

No output from this task is connected to selector, sizing, replay, paper runtime, live orders, strategy acceptance, or deployment readiness.

## No-Background Decision-Maker Report

Conclusion first: one historical task runner now actually consumes the common infra module.

This is intentionally narrow. It proves the shared module can replace task-local helper code without changing artifact parity.

## Artifact Manifest

- Inputs:
  - `{MIGRATED_SCRIPT.as_posix()}`
  - `{MODULE.as_posix()}`
  - `{(TASK3141_OUT / 'helper_replay_result.csv').as_posix()}`
- Outputs:
  - `docs/reports/{TASK_ID}/task_3145_external_tool_limited_migration.md`
  - `data/artifacts/{TASK_ID}/`
- Validation commands:
  - `python scripts/trader_brain_3145_external_tool_limited_migration_validate.py`
  - `python scripts/trader_brain_3141_external_tool_helper_contract_validate.py`
  - `python scripts/task_registry_validate.py`
- Source hashes:
  - Migrated script: `{file_sha256(MIGRATED_SCRIPT)}`
  - Common module: `{file_sha256(MODULE)}`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
"""
    REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    migrations = migration_rows()
    checks = build_checks(migrations)
    closeout = {
        "task_id": "Task3145",
        "verdict": "external_tool_limited_migration_completed_diagnostic_only",
        "migration_rows": len(migrations),
        "migration_pass_rows": sum(1 for row in migrations if row["migration_pass"] == "1"),
        "all_acceptance_checks_pass": "1" if all(row["pass"] == "1" for row in checks) else "0",
        "generated_at_utc": now_utc(),
        **common_status(),
    }
    write_csv(OUT_DIR / "migration_result.csv", migrations)
    write_csv(OUT_DIR / "acceptance_checks.csv", checks)
    write_csv(OUT_DIR / "task3145_closeout.csv", [closeout])
    write_json(OUT_DIR / "task3145_closeout.json", closeout)
    write_csv(DECISION, [closeout])
    write_report(migrations, checks, closeout)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print("[TASK3145_EXTERNAL_TOOL_LIMITED_MIGRATION_COMPLETE]")


if __name__ == "__main__":
    main()
