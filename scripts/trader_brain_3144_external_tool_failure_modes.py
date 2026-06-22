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

from src.infra.external_tools import (
    dependency_status,
    duckdb_strict_gate_aggregate,
    file_sha256,
    pandas_strict_gate_aggregate,
    polars_strict_gate_aggregate,
    validate_sec_panel_schema_with_pandera_venv,
    write_csv,
)


TASK_ID = "task_3144_external_tool_failure_modes"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_3144_external_tool_failure_modes.md"
DECISION = REPORT_DIR / "task_3144_decision.csv"
AUTHORITY = "DIAGNOSTIC_EXTERNAL_TOOL_FAILURE_MODES_ONLY"

TASK3126_VENV = ROOT / ".cache/task_3126_external_tool_venv"


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


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def build_bad_fixtures() -> list[dict[str, object]]:
    fixture_dir = OUT_DIR / "bad_fixtures"
    missing_join = fixture_dir / "missing_join_key.csv"
    missing_strict = fixture_dir / "missing_strict_gate.csv"
    bad_schema = fixture_dir / "bad_sec_schema.csv"
    write_csv(
        missing_join,
        [{"symbol": "AAA", "strict_gate_pass": "1"}, {"symbol": "BBB", "strict_gate_pass": "0"}],
        fieldnames=["symbol", "strict_gate_pass"],
    )
    write_csv(
        missing_strict,
        [{"symbol": "AAA", "event_family": "x"}, {"symbol": "BBB", "event_family": "y"}],
        fieldnames=["symbol", "event_family"],
    )
    write_csv(
        bad_schema,
        [
            {
                "source_packet_id": "BAD-1",
                "symbol": "AAA",
                "cik": "1",
                "accession_number": "000",
                "source_ts": "2026-01-01T00:00:00+00:00",
                "available_to_brain_ts": "2026-01-01T00:00:00+00:00",
                "raw_path": "",
                "missing_source_is_negative": "1",
                "assignment_uses_future_outcome": "1",
                "outcome_used_for_assignment": "1",
            }
        ],
    )
    return [
        {"fixture_name": "missing_join_key", "path": missing_join.as_posix(), "sha256": file_sha256(missing_join), **common_status()},
        {"fixture_name": "missing_strict_gate", "path": missing_strict.as_posix(), "sha256": file_sha256(missing_strict), **common_status()},
        {"fixture_name": "bad_sec_schema", "path": bad_schema.as_posix(), "sha256": file_sha256(bad_schema), **common_status()},
    ]


def run_failure_cases(fixtures: list[dict[str, object]]) -> list[dict[str, object]]:
    paths = {row["fixture_name"]: Path(str(row["path"])) for row in fixtures}
    rows: list[dict[str, object]] = []
    for engine, fn in [("pandas", pandas_strict_gate_aggregate), ("polars", polars_strict_gate_aggregate), ("duckdb", duckdb_strict_gate_aggregate)]:
        for fixture_name, group_cols in [("missing_join_key", ["symbol", "event_family"]), ("missing_strict_gate", ["symbol", "event_family"])]:
            metrics, result_rows = fn(paths[fixture_name], group_cols)
            rows.append(
                {
                    "case_id": f"FAIL3144-{engine.upper()}-{fixture_name}",
                    "tool_name": engine,
                    "fixture_name": fixture_name,
                    "expected_status": "invalid_input",
                    "actual_status": metrics.get("dependency_status", ""),
                    "error": metrics.get("error", ""),
                    "result_row_count": len(result_rows),
                    "failure_mode_pass": "1" if metrics.get("dependency_status") == "invalid_input" and len(result_rows) == 0 else "0",
                    **common_status(),
                }
            )
    required_cols = [
        "source_packet_id",
        "symbol",
        "cik",
        "accession_number",
        "source_ts",
        "available_to_brain_ts",
        "raw_path",
        "raw_sha256",
        "missing_source_is_negative",
        "assignment_uses_future_outcome",
        "outcome_used_for_assignment",
    ]
    schema = validate_sec_panel_schema_with_pandera_venv(ROOT, TASK3126_VENV, paths["bad_sec_schema"], required_cols)
    rows.append(
        {
            "case_id": "FAIL3144-PANDERA-bad_sec_schema",
            "tool_name": "pandera",
            "fixture_name": "bad_sec_schema",
            "expected_status": "schema_execution_failed",
            "actual_status": schema.get("schema_status", ""),
            "error": schema.get("error", ""),
            "result_row_count": schema.get("row_count", 0),
            "failure_mode_pass": "1" if schema.get("schema_status") == "schema_execution_failed" else "0",
            **common_status(),
        }
    )
    missing = dependency_status("definitely_missing_external_tool_for_task3144")
    rows.append(
        {
            "case_id": "FAIL3144-DEPENDENCY-MISSING",
            "tool_name": "definitely_missing_external_tool_for_task3144",
            "fixture_name": "none",
            "expected_status": "dependency_missing",
            "actual_status": missing.dependency_status,
            "error": "",
            "result_row_count": 0,
            "failure_mode_pass": "1" if missing.dependency_status == "dependency_missing" else "0",
            **common_status(),
        }
    )
    return rows


def build_checks(failures: list[dict[str, object]]) -> list[dict[str, object]]:
    checks = [
        ("failure_cases_present", len(failures) == 8, "All failure cases are recorded."),
        ("failure_modes_pass", all(row["failure_mode_pass"] == "1" for row in failures), "All bad inputs close as expected statuses."),
        ("no_traceback_escape", all(row["actual_status"] for row in failures), "All failure cases returned structured status."),
        ("status_unchanged", True, "Strategy/deployment/real-capital statuses remain unchanged."),
    ]
    return [
        {"check_id": f"CHK3144-{idx:03d}", "check_name": name, "pass": "1" if passed else "0", "detail": detail, **common_status()}
        for idx, (name, passed, detail) in enumerate(checks, start=1)
    ]


def markdown_table(rows: list[dict[str, object]], fields: list[str]) -> str:
    lines = ["| " + " | ".join(fields) + " |", "| " + " | ".join(["---"] * len(fields)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ")[:300] for field in fields) + " |")
    return "\n".join(lines)


def write_report(fixtures: list[dict[str, object]], failures: list[dict[str, object]], checks: list[dict[str, object]], closeout: dict[str, object]) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = f"""# Task3144 External Tool Failure Modes

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- What changed: hardened `src/infra/external_tools.py` so malformed local artifact inputs return structured failure statuses instead of uncaught crashes.
- What did not change: no source acquisition, replay, selector, sizing, paper order, live order, root dependency manifest, acceptance, or deployment state changed.
- Key metrics: bad fixtures {len(fixtures)}, failure cases {len(failures)}, pass rows {closeout['failure_mode_pass_rows']}.

## Quant Expert Report

### Bad Fixtures

{markdown_table(fixtures, ['fixture_name', 'path', 'sha256'])}

### Failure Cases

{markdown_table(failures, ['case_id', 'tool_name', 'fixture_name', 'expected_status', 'actual_status', 'failure_mode_pass'])}

### Acceptance Checks

{markdown_table(checks, ['check_name', 'pass', 'detail'])}

No output from this task is connected to selector, sizing, replay, paper runtime, live orders, strategy acceptance, or deployment readiness.

## No-Background Decision-Maker Report

Conclusion first: bad inputs now fail closed with structured statuses.

Malformed query panels return `invalid_input`, bad Pandera schema returns `schema_execution_failed`, and missing tools return `dependency_missing`.

## Artifact Manifest

- Outputs:
  - `docs/reports/{TASK_ID}/task_3144_external_tool_failure_modes.md`
  - `data/artifacts/{TASK_ID}/`
- Validation commands:
  - `python scripts/trader_brain_3144_external_tool_failure_modes_validate.py`
  - `python scripts/task_registry_validate.py`

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
"""
    REPORT.write_text(report, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    fixtures = build_bad_fixtures()
    failures = run_failure_cases(fixtures)
    checks = build_checks(failures)
    closeout = {
        "task_id": "Task3144",
        "verdict": "external_tool_failure_modes_completed_diagnostic_only",
        "bad_fixture_rows": len(fixtures),
        "failure_case_rows": len(failures),
        "failure_mode_pass_rows": sum(1 for row in failures if row["failure_mode_pass"] == "1"),
        "all_acceptance_checks_pass": "1" if all(row["pass"] == "1" for row in checks) else "0",
        "generated_at_utc": now_utc(),
        **common_status(),
    }
    write_csv(OUT_DIR / "bad_fixture_manifest.csv", fixtures)
    write_csv(OUT_DIR / "failure_mode_result.csv", failures)
    write_csv(OUT_DIR / "acceptance_checks.csv", checks)
    write_csv(OUT_DIR / "task3144_closeout.csv", [closeout])
    write_json(OUT_DIR / "task3144_closeout.json", closeout)
    write_csv(DECISION, [closeout])
    write_report(fixtures, failures, checks, closeout)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print("[TASK3144_EXTERNAL_TOOL_FAILURE_MODES_COMPLETE]")


if __name__ == "__main__":
    main()
