from __future__ import annotations

import argparse
import csv
from pathlib import Path


PASS_DOES_NOT_MEAN = (
    "strategy acceptance, deployment readiness, broker truth, backtest validity, "
    "source completeness, or real-capital permission"
)

FORBIDDEN_OUTPUT_COLUMNS = {
    "symbol",
    "side",
    "entry_price",
    "exit_price",
    "pnl",
    "return",
    "win_rate",
    "drawdown",
    "sharpe",
    "position_size",
    "order_id",
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


def gate_index(path: Path) -> dict[str, dict[str, str]]:
    return {row["market_data_gate_id"]: row for row in read_csv(path)}


def config_index(path: Path) -> dict[str, dict[str, str]]:
    return {row["replay_config_id"]: row for row in read_csv(path)}


def validate_no_execution_schema(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    if not rows:
        return ["input manifest has no rows"]
    columns = set(rows[0].keys())
    forbidden = columns & FORBIDDEN_OUTPUT_COLUMNS
    if forbidden:
        errors.append(f"forbidden execution-like columns in input manifest: {','.join(sorted(forbidden))}")
    return errors


def build_run_plan(
    input_manifest: Path,
    market_data_gate: Path,
    replay_config: Path,
    run_id: str,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[str]]:
    input_rows = read_csv(input_manifest)
    errors = validate_no_execution_schema(input_rows)
    gates = gate_index(market_data_gate)
    configs = config_index(replay_config)
    plan_rows: list[dict[str, str]] = []
    for row in input_rows:
        gate = gates.get(row.get("market_data_gate_id", ""))
        config = configs.get(row.get("replay_config_id", ""))
        blocked_reasons: list[str] = []
        if row.get("adapter_input_state") != "dry_adapter_input":
            blocked_reasons.append("adapter_input_not_dry")
        if gate is None:
            blocked_reasons.append("unknown_market_data_gate")
        elif gate.get("current_state") != "ready":
            blocked_reasons.append(gate.get("blocked_reason") or "market_data_gate_not_ready")
        if config is None:
            blocked_reasons.append("unknown_replay_config")
        elif config.get("current_state") != "dry_plan_only":
            blocked_reasons.append("replay_config_not_dry_plan")
        if row.get("harness_input_state") != "planned_only":
            blocked_reasons.append(row.get("blocked_reason") or "harness_input_not_planned")

        plan_rows.append(
            {
                "run_id": run_id,
                "harness_input_id": row.get("harness_input_id", ""),
                "adapter_input_id": row.get("adapter_input_id", ""),
                "candidate_bundle_id": row.get("candidate_bundle_id", ""),
                "source_graph_id": row.get("source_graph_id", ""),
                "bundle_asof_ts": row.get("bundle_asof_ts", ""),
                "market_data_gate_id": row.get("market_data_gate_id", ""),
                "replay_config_id": row.get("replay_config_id", ""),
                "dry_run_state": "blocked_before_replay" if blocked_reasons else "ready_for_future_controlled_replay",
                "blocked_reason": "|".join(blocked_reasons),
                "no_execution_assertion": "no price lookup no trades no pnl no engine call",
                "validation_authority": "GOVERNANCE_HEALTH",
                "pass_does_not_mean": PASS_DOES_NOT_MEAN,
            }
        )
    blocked = sum(1 for row in plan_rows if row["dry_run_state"] == "blocked_before_replay")
    ready = len(plan_rows) - blocked
    summary = [
        {
            "run_id": run_id,
            "input_count": str(len(plan_rows)),
            "ready_for_future_controlled_replay_count": str(ready),
            "blocked_before_replay_count": str(blocked),
            "price_lookup_count": "0",
            "trade_row_count": "0",
            "pnl_metric_count": "0",
            "engine_call_count": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_status": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "validation_authority": "GOVERNANCE_HEALTH",
            "pass_does_not_mean": PASS_DOES_NOT_MEAN,
        }
    ]
    return plan_rows, summary, errors


PLAN_FIELDS = [
    "run_id",
    "harness_input_id",
    "adapter_input_id",
    "candidate_bundle_id",
    "source_graph_id",
    "bundle_asof_ts",
    "market_data_gate_id",
    "replay_config_id",
    "dry_run_state",
    "blocked_reason",
    "no_execution_assertion",
    "validation_authority",
    "pass_does_not_mean",
]

SUMMARY_FIELDS = [
    "run_id",
    "input_count",
    "ready_for_future_controlled_replay_count",
    "blocked_before_replay_count",
    "price_lookup_count",
    "trade_row_count",
    "pnl_metric_count",
    "engine_call_count",
    "strategy_acceptance",
    "deployment_status",
    "real_capital",
    "validation_authority",
    "pass_does_not_mean",
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-manifest", required=True, type=Path)
    parser.add_argument("--market-data-gate", required=True, type=Path)
    parser.add_argument("--replay-config", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--run-plan-output", required=True, type=Path)
    parser.add_argument("--summary-output", required=True, type=Path)
    args = parser.parse_args()
    plan_rows, summary_rows, errors = build_run_plan(
        args.input_manifest,
        args.market_data_gate,
        args.replay_config,
        args.run_id,
    )
    write_csv(args.run_plan_output, plan_rows, PLAN_FIELDS)
    write_csv(args.summary_output, summary_rows, SUMMARY_FIELDS)
    if errors:
        for error in errors:
            print(f"[TRADER_BRAIN_BACKTEST_DRY_HARNESS_ERROR] {error}")
        raise SystemExit(1)
    print(
        f"[TRADER_BRAIN_BACKTEST_DRY_HARNESS_OK] inputs={summary_rows[0]['input_count']} "
        f"blocked={summary_rows[0]['blocked_before_replay_count']} run_id={args.run_id}"
    )


if __name__ == "__main__":
    main()
