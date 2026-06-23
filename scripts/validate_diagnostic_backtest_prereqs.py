from __future__ import annotations

import json

from news_ops_to_backtest_common import ARTIFACT_DIR, ROOT, ensure_dirs, fail_if_errors, safety_payload, write_csv, write_json
from trader_brain_backtest_dry_replay_harness import build_run_plan, write_csv as write_harness_csv, PLAN_FIELDS, SUMMARY_FIELDS
from trader_brain_backtest_harness_artifact_audit import audit_artifacts, FIELDS as AUDIT_FIELDS


REQUIRED_SCOPE_ARTIFACTS = {
    "scope_a_b_scheduler_reconciliation": ARTIFACT_DIR / "scope_a_b_scheduler_reconciliation.json",
    "scope_c_l0_l1_storage_validation": ARTIFACT_DIR / "scope_c_l0_l1_storage_validation.json",
    "scope_d_l1_l6_consumption_validation": ARTIFACT_DIR / "scope_d_l1_l6_consumption_validation.json",
    "scope_e_source_time_audit": ARTIFACT_DIR / "scope_e_source_time_audit.json",
}


def _load(path):
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _repo_rel(path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def main() -> None:
    ensure_dirs()
    errors: list[str] = []
    blockers: list[dict[str, object]] = []
    manifest_rows: list[dict[str, object]] = []
    for name, path in REQUIRED_SCOPE_ARTIFACTS.items():
        payload = _load(path)
        status = "MISSING" if payload is None else str(payload.get("status", "UNKNOWN"))
        manifest_rows.append({"artifact_name": name, "artifact_path": _repo_rel(path), "status": status})
        if payload is None:
            errors.append(f"missing_prereq_artifact:{name}")
            blockers.append({"blocker_code": "MISSING_PREREQ_ARTIFACT", "artifact_name": name, "status": status})
        elif name == "scope_e_source_time_audit" and status in {"PASS_WITH_BLOCKERS"}:
            blockers.append({"blocker_code": "SOURCE_TIME_AUDIT_HAS_BLOCKERS", "artifact_name": name, "status": status})
        elif status not in {"PASS"}:
            errors.append(f"prereq_not_pass:{name}:{status}")
            blockers.append({"blocker_code": "PREREQ_NOT_PASS", "artifact_name": name, "status": status})

    harness_input_manifest = ARTIFACT_DIR / "scope_f_harness_input_manifest.csv"
    market_data_gate = ARTIFACT_DIR / "scope_f_market_data_gate_report.csv"
    split_oos_cost_slippage = ARTIFACT_DIR / "scope_f_split_oos_cost_slippage_plan.csv"
    run_plan = ARTIFACT_DIR / "scope_f_dry_harness_run_plan.csv"
    run_summary = ARTIFACT_DIR / "scope_f_dry_harness_run_summary.csv"
    artifact_audit = ARTIFACT_DIR / "scope_f_harness_artifact_audit.csv"
    go_no_go = ARTIFACT_DIR / "scope_g_controlled_replay_go_no_go_matrix.csv"

    harness_input_rows = [
        {
            "harness_input_id": "scope-f-input-1",
            "adapter_input_id": "dry-adapter-input-news-ops-1",
            "candidate_bundle_id": "dry-candidate-bundle-placeholder",
            "source_graph_id": "source-graph-diagnostic-news-ops",
            "bundle_asof_ts": "2026-06-24T00:00:00Z",
            "market_data_gate_id": "market-data-gate-scope-f",
            "replay_config_id": "replay-config-scope-f",
            "adapter_input_state": "dry_adapter_input",
            "harness_input_state": "planned_only",
            "blocked_reason": "CONTROLLED_REPLAY_NOT_AUTHORIZED_SCOPE_G_NO_GO",
        }
    ]
    market_gate_rows = [
        {
            "market_data_gate_id": "market-data-gate-scope-f",
            "current_state": "blocked",
            "blocked_reason": "MARKET_DATA_MANIFEST_NOT_CERTIFIED_FOR_CONTROLLED_REPLAY",
            "validation_authority": "GOVERNANCE_HEALTH",
        }
    ]
    replay_config_rows = [
        {
            "replay_config_id": "replay-config-scope-f",
            "current_state": "dry_plan_only",
            "split_oos_plan_state": "draft_not_owner_approved",
            "cost_slippage_config_state": "draft_not_owner_approved",
            "validation_authority": "GOVERNANCE_HEALTH",
        }
    ]
    write_csv(harness_input_manifest, harness_input_rows)
    write_csv(market_data_gate, market_gate_rows)
    write_csv(split_oos_cost_slippage, replay_config_rows)

    plan_rows, summary_rows, harness_errors = build_run_plan(
        harness_input_manifest,
        market_data_gate,
        split_oos_cost_slippage,
        "task3883_scope_f_no_execution",
    )
    write_harness_csv(run_plan, plan_rows, PLAN_FIELDS)
    write_harness_csv(run_summary, summary_rows, SUMMARY_FIELDS)
    audit_rows, audit_errors = audit_artifacts(run_plan, run_summary)
    write_harness_csv(artifact_audit, audit_rows, AUDIT_FIELDS)
    errors.extend(f"harness_error:{error}" for error in harness_errors)
    errors.extend(f"artifact_audit_error:{error}" for error in audit_errors)

    ready_count = int(summary_rows[0]["ready_for_future_controlled_replay_count"]) if summary_rows else -1
    if ready_count != 0:
        errors.append(f"controlled_replay_ready_count_must_be_zero:{ready_count}")
    go_no_go_rows = [
        {
            "decision_area": "controlled_diagnostic_replay",
            "status": "NO_GO",
            "reason": "Scope G keeps replay blocked until source-time, market-data, split/OOS, and cost/slippage blockers are explicitly cleared by a later owner-approved task.",
            "price_lookup_count": "0",
            "trade_row_count": "0",
            "pnl_metric_count": "0",
            "engine_call_count": "0",
            "validation_authority": "GOVERNANCE_HEALTH",
        }
    ]
    write_csv(go_no_go, go_no_go_rows)

    harness_manifest = {
        "harness_mode": "NO_EXECUTION_DIAGNOSTIC_ONLY",
        "allowed_outputs": [
            "input_manifest",
            "source_time_blocker_report",
            "market_data_gate_report",
            "split_oos_plan",
            "cost_slippage_config_draft",
            "no_execution_dry_harness",
        ],
        "forbidden_until_blockers_clear": [
            "pnl_replay",
            "trade_generation",
            "strategy_acceptance_comparison",
            "paper_promotion",
            "live_readiness",
            "buy_sell_position_size_recommendation",
        ],
        "controlled_replay_allowed": False,
        "controlled_replay_blocker": "NO_EXECUTION_HARNESS_ONLY_FOR_SCOPE_F",
        "generated_artifacts": [
            _repo_rel(harness_input_manifest),
            _repo_rel(market_data_gate),
            _repo_rel(split_oos_cost_slippage),
            _repo_rel(run_plan),
            _repo_rel(run_summary),
            _repo_rel(artifact_audit),
            _repo_rel(go_no_go),
        ],
        "status": "PASS" if not errors else "BLOCKED",
        "errors": errors,
        **safety_payload(),
    }

    write_csv(ARTIFACT_DIR / "scope_f_diagnostic_backtest_prereq_manifest.csv", manifest_rows)
    write_csv(
        ARTIFACT_DIR / "scope_f_diagnostic_backtest_blockers.csv",
        blockers,
        fieldnames=["blocker_code", "artifact_name", "status"],
    )
    write_json(ARTIFACT_DIR / "scope_f_no_execution_harness_manifest.json", harness_manifest)
    fail_if_errors(errors)
    print("[TASK3883_SCOPE_F_G_OK] no_execution_harness=PASS controlled_replay_blocked_until_explicit_scope=1")


if __name__ == "__main__":
    main()
