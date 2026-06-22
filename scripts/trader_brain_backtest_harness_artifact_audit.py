from __future__ import annotations

import argparse
import csv
from pathlib import Path


REQUIRED_PLAN_COLUMNS = {
    "run_id",
    "harness_input_id",
    "adapter_input_id",
    "candidate_bundle_id",
    "source_graph_id",
    "replay_config_id",
    "dry_run_state",
    "no_execution_assertion",
}

FORBIDDEN_COLUMNS = {
    "entry_price",
    "exit_price",
    "pnl",
    "return",
    "win_rate",
    "drawdown",
    "sharpe",
    "order_id",
    "position_size",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def audit_artifacts(run_plan: Path, summary: Path) -> tuple[list[dict[str, str]], list[str]]:
    errors: list[str] = []
    plan_rows = read_csv(run_plan)
    summary_rows = read_csv(summary)
    if not plan_rows:
        errors.append("run plan has no rows")
        plan_columns: set[str] = set()
    else:
        plan_columns = set(plan_rows[0].keys())
    missing = REQUIRED_PLAN_COLUMNS - plan_columns
    if missing:
        errors.append(f"run plan missing columns {','.join(sorted(missing))}")
    forbidden = plan_columns & FORBIDDEN_COLUMNS
    if forbidden:
        errors.append(f"run plan has forbidden execution columns {','.join(sorted(forbidden))}")
    for idx, row in enumerate(plan_rows, start=2):
        for field in REQUIRED_PLAN_COLUMNS:
            if not row.get(field):
                errors.append(f"run plan row {idx}: missing {field}")
        assertion = row.get("no_execution_assertion", "").lower()
        for phrase in ["no price lookup", "no trades", "no pnl", "no engine call"]:
            if phrase not in assertion:
                errors.append(f"run plan row {idx}: no_execution_assertion missing {phrase}")
    if not summary_rows:
        errors.append("summary has no rows")
    else:
        summary_row = summary_rows[0]
        for field in ["price_lookup_count", "trade_row_count", "pnl_metric_count", "engine_call_count"]:
            if summary_row.get(field) != "0":
                errors.append(f"summary {field} must be 0")
        if summary_row.get("strategy_acceptance") != "NOT_ACCEPTED":
            errors.append("summary strategy_acceptance must be NOT_ACCEPTED")
        if summary_row.get("deployment_status") != "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY":
            errors.append("summary deployment_status must be DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY")
        if summary_row.get("real_capital") != "FORBIDDEN":
            errors.append("summary real_capital must be FORBIDDEN")
    audit_rows = [
        {
            "audit_id": "harness_artifact_audit_v1",
            "run_plan": run_plan.as_posix(),
            "summary": summary.as_posix(),
            "plan_rows": str(len(plan_rows)),
            "summary_rows": str(len(summary_rows)),
            "error_count": str(len(errors)),
            "audit_state": "pass" if not errors else "fail",
            "validation_authority": "GOVERNANCE_HEALTH",
            "pass_does_not_mean": "strategy acceptance, deployment readiness, broker truth, backtest validity, source completeness, or real-capital permission",
        }
    ]
    return audit_rows, errors


FIELDS = [
    "audit_id",
    "run_plan",
    "summary",
    "plan_rows",
    "summary_rows",
    "error_count",
    "audit_state",
    "validation_authority",
    "pass_does_not_mean",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-plan", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    parser.add_argument("--audit-output", required=True, type=Path)
    args = parser.parse_args()
    audit_rows, errors = audit_artifacts(args.run_plan, args.summary)
    write_csv(args.audit_output, audit_rows, FIELDS)
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_HARNESS_ARTIFACT_AUDIT_ERROR] {error}")
        raise SystemExit(1)
    print(f"[TRADER_BRAIN_HARNESS_ARTIFACT_AUDIT_OK] {args.audit_output}")


if __name__ == "__main__":
    main()
