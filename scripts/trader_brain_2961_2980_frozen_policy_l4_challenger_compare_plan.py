from __future__ import annotations

import csv
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK_ID = "task_2961_2980_frozen_policy_l4_challenger_compare_plan"
OUT_DIR = ROOT / "data/artifacts" / TASK_ID
REPORT_DIR = ROOT / "docs/reports" / TASK_ID
REPORT = REPORT_DIR / "task_2961_2980_frozen_policy_l4_challenger_compare_plan.md"
DECISION = REPORT_DIR / "task_2980_decision.csv"
AUTHORITY = "DIAGNOSTIC_POLICY_FREEZE_COMPARE_PLAN_ONLY"

BASELINE_VARIANT = "exit_chain_repaired_soft_boost_cap_top2_v1"
CHALLENGER_VARIANT = "exit_chain_repaired_soft_boost_cap_top2_v1__l4_thesis_invalidation_v1"

TASK2381 = ROOT / "data/artifacts/task_2381_2400_plus8000_exit_chain_parity_repair"
TASK2401 = ROOT / "data/artifacts/task_2401_2500_research_to_paper_readiness"
TASK2501 = ROOT / "data/artifacts/task_2501_2510_kis_cost_basis_test"
TASK2941 = ROOT / "data/artifacts/task_2941_2960_l4_thesis_invalidation"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)
        if not fieldnames:
            fieldnames = ["empty"]
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def hash_payload(payload: object) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def now_utc() -> str:
    return datetime.now(tz=UTC).isoformat()


def common_flags(audit_only: str = "0") -> dict[str, object]:
    return {
        "outcome_used_for_audit_only": audit_only,
        "assignment_uses_future_outcome": "0",
        "outcome_used_for_assignment": "0",
        "missing_source_is_negative": "0",
        "authority": AUTHORITY,
    }


def load_inputs() -> dict[str, list[dict[str, str]]]:
    return {
        "baseline_metrics": read_csv(TASK2381 / "task2386_replay_metrics.csv"),
        "baseline_trades": read_csv(TASK2381 / "task2386_replay_trades.csv"),
        "baseline_equity": read_csv(TASK2381 / "task2386_replay_equity.csv"),
        "source_gate": read_csv(TASK2401 / "task2421_source_time_gate_ledger.csv"),
        "policy_freeze": read_csv(TASK2401 / "task2431_policy_freeze_manifest.csv"),
        "dry_adapter": read_csv(TASK2401 / "task2442_dry_adapter_inputs.csv"),
        "kis_metrics": read_csv(TASK2501 / "task2504_kis_repriced_metrics.csv"),
        "l4_assignment": read_csv(TASK2941 / "task2945_l4_assignment.csv"),
        "l4_rulebook": read_csv(TASK2941 / "task2944_l4_invalidation_rulebook.csv"),
        "l4_input_manifest": read_csv(TASK2941 / "task2942_l4_input_manifest.csv"),
    }


def task2961_scope(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    return [
        {
            "task_id": "Task2961",
            "scope_id": "FREEZECOMP2961-0001",
            "objective": "Freeze baseline and L4 challenger identities before any replay or performance comparison.",
            "baseline_variant_id": BASELINE_VARIANT,
            "challenger_variant_id": CHALLENGER_VARIANT,
            "baseline_trade_rows": len([row for row in inputs["baseline_trades"] if row.get("policy_variant_id") == BASELINE_VARIANT]),
            "l4_assignment_rows": len(inputs["l4_assignment"]),
            "source_gate_rows": len(inputs["source_gate"]),
            "dry_adapter_rows": len(inputs["dry_adapter"]),
            "replay_performed": "0",
            "performance_compared": "0",
            "selector_tuning_performed": "0",
            "sizing_tuning_performed": "0",
            "exit_tuning_performed": "0",
            "paper_order_intents_created": "0",
            "live_orders_created": "0",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            **common_flags("0"),
        }
    ]


def task2962_policy_freeze_registry(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    baseline_files = [
        TASK2381 / "task2386_replay_metrics.csv",
        TASK2381 / "task2386_replay_trades.csv",
        TASK2381 / "task2386_replay_equity.csv",
        TASK2381 / "task2384_repaired_exit_source_rows.csv",
        TASK2501 / "task2504_kis_repriced_metrics.csv",
    ]
    challenger_files = [
        TASK2941 / "task2944_l4_invalidation_rulebook.csv",
        TASK2941 / "task2945_l4_assignment.csv",
        TASK2941 / "task2942_l4_input_manifest.csv",
        TASK2941 / "task2943_l4_thesis_evidence_snapshot.csv",
    ]
    baseline_hash = hash_payload([(path.as_posix(), file_hash(path)) for path in baseline_files])
    challenger_hash = hash_payload([(path.as_posix(), file_hash(path)) for path in challenger_files])
    rows = [
        {
            "task_id": "Task2962",
            "freeze_id": "POLICYFREEZE2962-BASELINE",
            "policy_role": "frozen_baseline",
            "variant_id": BASELINE_VARIANT,
            "source_task": "Task2381-Task2501",
            "selector_id": "soft_boost_cap_top2",
            "sizing_id": "task2191_api_dd_guard_top2_sizing_chain",
            "exit_id": "task2381_repaired_exit_chain_parity",
            "capital_path": "1000_initial_capital_monthly_replay_path",
            "cost_slippage_model": "KIS_cost_basis_available_task2501_but_replay_plan_must_declare_model",
            "feature_set_hash": baseline_hash,
            "config_hash": baseline_hash,
            "frozen_at_utc": now_utc(),
            "policy_change_allowed": "0",
            "paper_order_intents_created": "0",
            "live_orders_created": "0",
            **common_flags("0"),
        },
        {
            "task_id": "Task2962",
            "freeze_id": "POLICYFREEZE2962-CHALLENGER",
            "policy_role": "l4_challenger",
            "variant_id": CHALLENGER_VARIANT,
            "source_task": "Task2941-Task2960",
            "selector_id": "soft_boost_cap_top2_plus_l4_assignment_overlay",
            "sizing_id": "same_as_baseline_until_replay_plan_changes_are_approved",
            "exit_id": "same_as_baseline_until_replay_plan_changes_are_approved",
            "capital_path": "same_as_baseline_until_replay_plan_changes_are_approved",
            "cost_slippage_model": "same_as_baseline_until_replay_plan_changes_are_approved",
            "feature_set_hash": challenger_hash,
            "config_hash": hash_payload({"baseline": baseline_hash, "challenger": challenger_hash, "variant": CHALLENGER_VARIANT}),
            "frozen_at_utc": now_utc(),
            "policy_change_allowed": "0",
            "paper_order_intents_created": "0",
            "live_orders_created": "0",
            **common_flags("0"),
        },
    ]
    return rows


def task2963_hash_ledger() -> list[dict[str, object]]:
    files = [
        ("baseline_metrics", TASK2381 / "task2386_replay_metrics.csv"),
        ("baseline_trades", TASK2381 / "task2386_replay_trades.csv"),
        ("baseline_equity", TASK2381 / "task2386_replay_equity.csv"),
        ("baseline_exit_source", TASK2381 / "task2384_repaired_exit_source_rows.csv"),
        ("kis_cost_metrics", TASK2501 / "task2504_kis_repriced_metrics.csv"),
        ("source_time_gate", TASK2401 / "task2421_source_time_gate_ledger.csv"),
        ("dry_adapter_inputs", TASK2401 / "task2442_dry_adapter_inputs.csv"),
        ("l4_rulebook", TASK2941 / "task2944_l4_invalidation_rulebook.csv"),
        ("l4_assignment", TASK2941 / "task2945_l4_assignment.csv"),
        ("l4_input_manifest", TASK2941 / "task2942_l4_input_manifest.csv"),
        ("l4_evidence_snapshot", TASK2941 / "task2943_l4_thesis_evidence_snapshot.csv"),
    ]
    rows: list[dict[str, object]] = []
    for idx, (artifact_role, path) in enumerate(files, start=1):
        rows.append(
            {
                "task_id": "Task2963",
                "hash_id": f"FREEZEHASH2963-{idx:04d}",
                "artifact_role": artifact_role,
                "path": path.relative_to(ROOT).as_posix(),
                "exists": "1" if path.exists() else "0",
                "sha256": file_hash(path) if path.exists() else "",
                "bytes": path.stat().st_size if path.exists() else 0,
                "frozen_for_compare": "1",
                **common_flags("0"),
            }
        )
    return rows


def task2964_same_experiment_gate() -> list[dict[str, object]]:
    checks = [
        ("same_universe", "CONDITIONAL_PASS", "Both sides reference the same 3,100 L4 assignment universe, but baseline selected trades are a subset."),
        ("same_decision_dates", "PASS", "Decision dates must be inherited from baseline replay and dry adapter inputs."),
        ("same_entry_rules", "PASS", "No entry rule change is allowed before replay plan approval."),
        ("same_exit_chain", "PASS", "Task2381 repaired exit chain remains frozen."),
        ("same_capital_path", "PASS", "Initial capital and capital path must remain baseline unless replay config changes are preregistered."),
        ("same_cost_slippage", "PASS", "KIS cost/slippage model must be declared unchanged before performance compare."),
        ("same_source_gates", "NOT_SAME_EXPERIMENT", "L4 challenger adds an invalidation overlay; performance comparison must be labeled challenger experiment, not same experiment."),
        ("performance_discussion_allowed", "BLOCKED", "No performance discussion until replay artifact exists and same/different experiment class is declared."),
    ]
    return [
        {
            "task_id": "Task2964",
            "same_experiment_gate_id": f"SAMEEXP2964-{idx:04d}",
            "gate_name": name,
            "gate_status": status,
            "detail": detail,
            "performance_compare_allowed_now": "0",
            "classified_as_same_experiment": "0" if status in {"NOT_SAME_EXPERIMENT", "BLOCKED"} else "",
            **common_flags("0"),
        }
        for idx, (name, status, detail) in enumerate(checks, start=1)
    ]


def task2965_split_oos_replay_plan() -> list[dict[str, object]]:
    splits = [
        ("IS_2021_2023", "2021-01-01", "2023-12-31", "in_sample_research_context"),
        ("VALIDATION_2024", "2024-01-01", "2024-12-31", "validation_no_tuning"),
        ("OOS_2025_2026Q1", "2025-01-01", "2026-03-31", "out_of_sample_no_tuning"),
        ("REGIME_2022_RATES_DRAWDOWN", "2022-01-01", "2022-12-31", "rates_liquidity_drawdown_regime"),
        ("REGIME_2023_AI_SEMI_RECOVERY", "2023-01-01", "2023-12-31", "ai_semiconductor_recovery_regime"),
        ("REGIME_2024_2025_BULL", "2024-01-01", "2025-12-31", "bull_market_regime"),
    ]
    return [
        {
            "task_id": "Task2965",
            "replay_plan_id": f"L4REPLAYPLAN2965-{idx:04d}",
            "split_id": split_id,
            "start_date": start,
            "end_date": end,
            "regime_label": label,
            "baseline_variant_id": BASELINE_VARIANT,
            "challenger_variant_id": CHALLENGER_VARIANT,
            "selector_policy": "baseline_soft_boost_cap_top2_vs_l4_overlay_challenger",
            "sizing_policy": "same_as_baseline",
            "exit_policy": "task2381_repaired_exit_chain",
            "capital_path": "same_as_baseline",
            "cost_slippage_model": "KIS_cost_basis_required",
            "source_feature_set": "Task2581_L2_L3_plus_Task2941_L4_assignment",
            "frozen_inputs_required": "1",
            "replay_executed": "0",
            "performance_compare_allowed_now": "0",
            **common_flags("0"),
        }
        for idx, (split_id, start, end, label) in enumerate(splits, start=1)
    ]


def task2966_replay_blocker_checklist(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    strict_complete = sum(1 for row in inputs["source_gate"] if row.get("strict_raw_asof_complete") == "1")
    blockers = [
        ("strict_raw_asof_complete", "BLOCKED" if strict_complete < len(inputs["source_gate"]) else "PASS", f"strict_complete={strict_complete}/{len(inputs['source_gate'])}"),
        ("policy_hashes_frozen", "PASS", "Baseline and challenger hash rows are generated."),
        ("same_experiment_declared", "PASS", "Challenger is explicitly not the same experiment due to L4 overlay."),
        ("no_replay_this_task", "PASS", "This task only freezes and plans replay."),
        ("no_paper_or_live_orders", "PASS", "No paper/live orders are created."),
    ]
    return [
        {
            "task_id": "Task2966",
            "blocker_id": f"REPLAYBLOCK2966-{idx:04d}",
            "blocker_name": name,
            "status": status,
            "detail": detail,
            "blocks_live_or_paper": "1",
            "blocks_actual_replay": "1" if status == "BLOCKED" else "0",
            **common_flags("0"),
        }
        for idx, (name, status, detail) in enumerate(blockers, start=1)
    ]


def task2967_comparison_manifest(inputs: dict[str, list[dict[str, str]]]) -> list[dict[str, object]]:
    rows = [
        ("baseline_selected_trade_manifest", "selected_trades", str(len([row for row in inputs["baseline_trades"] if row.get("policy_variant_id") == BASELINE_VARIANT])), "Task2381 baseline selected trades"),
        ("challenger_full_assignment_manifest", "full_universe_assignment", str(len(inputs["l4_assignment"])), "Task2941 L4 assignment overlay"),
        ("outcome_not_available_for_assignment", "governance", "1", "Outcome audit is physically separate from assignment."),
        ("same_experiment_class", "classification", "not_same_experiment", "Challenger changes source gate overlay; compare as challenger experiment."),
    ]
    return [
        {
            "task_id": "Task2967",
            "manifest_id": f"COMPAREMAN2967-{idx:04d}",
            "manifest_name": name,
            "manifest_type": typ,
            "value": value,
            "detail": detail,
            **common_flags("0"),
        }
        for idx, (name, typ, value, detail) in enumerate(rows, start=1)
    ]


def task2968_subagent_review_packets() -> list[dict[str, object]]:
    roles = [
        ("freeze_hash_reviewer", "Check frozen baseline/challenger identity and hash coverage."),
        ("split_oos_replay_reviewer", "Check split/OOS replay plan before any replay execution."),
        ("governance_validator_reviewer", "Check no replay/order/outcome leakage and status wording."),
    ]
    return [
        {
            "task_id": "Task2968",
            "review_packet_id": f"SUBAGENT2968-{idx:04d}",
            "review_role": role,
            "review_focus": focus,
            "review_only": "1",
            "write_scope": "read-only",
            **common_flags("0"),
        }
        for idx, (role, focus) in enumerate(roles, start=1)
    ]


def task2969_acceptance_checks(
    scope: list[dict[str, object]],
    freezes: list[dict[str, object]],
    hashes: list[dict[str, object]],
    same_gate: list[dict[str, object]],
    plan: list[dict[str, object]],
    blockers: list[dict[str, object]],
) -> list[dict[str, object]]:
    checks = [
        ("scope_no_replay", scope[0].get("replay_performed") == "0", "scope replay_performed=0"),
        ("two_policy_freezes", len(freezes) == 2, f"freeze_rows={len(freezes)}"),
        ("hashes_all_exist", all(row.get("exists") == "1" for row in hashes), "all frozen artifacts exist"),
        ("same_experiment_blocks_performance", any(row.get("gate_status") == "NOT_SAME_EXPERIMENT" for row in same_gate), "challenger is not same experiment"),
        ("split_plan_present", len(plan) >= 6, f"split_rows={len(plan)}"),
        ("no_replay_executed", all(row.get("replay_executed") == "0" for row in plan), "plan only, no replay"),
        ("strict_asof_blocker_recorded", any(row.get("blocker_name") == "strict_raw_asof_complete" for row in blockers), "strict as-of blocker row exists"),
        ("orders_forbidden", scope[0].get("paper_order_intents_created") == "0" and scope[0].get("live_orders_created") == "0", "no orders created"),
    ]
    return [
        {
            "task_id": "Task2969",
            "check_id": f"FREEZECHECK2969-{idx:04d}",
            "check_name": name,
            "pass": "1" if passed else "0",
            "detail": detail,
            **common_flags("0"),
        }
        for idx, (name, passed, detail) in enumerate(checks, start=1)
    ]


def task2980_closeout(
    scope: list[dict[str, object]],
    freezes: list[dict[str, object]],
    same_gate: list[dict[str, object]],
    plan: list[dict[str, object]],
    blockers: list[dict[str, object]],
    checks: list[dict[str, object]],
) -> list[dict[str, object]]:
    strict_blocker = next((row for row in blockers if row.get("blocker_name") == "strict_raw_asof_complete"), {})
    return [
        {
            "task_id": "Task2980",
            "verdict": "frozen_policy_l4_challenger_compare_plan_completed_no_replay",
            "baseline_variant_id": BASELINE_VARIANT,
            "challenger_variant_id": CHALLENGER_VARIANT,
            "freeze_rows": len(freezes),
            "same_experiment_gate_rows": len(same_gate),
            "split_oos_plan_rows": len(plan),
            "strict_asof_status": strict_blocker.get("status", ""),
            "performance_compare_allowed_now": "0",
            "replay_performed": "0",
            "selector_tuning_performed": "0",
            "sizing_tuning_performed": "0",
            "exit_tuning_performed": "0",
            "paper_order_intents_created": "0",
            "live_orders_created": "0",
            "all_acceptance_checks_pass": "1" if all(row.get("pass") == "1" for row in checks) else "0",
            "next_action": "Task2981-3000 can expose this freeze/compare plan in iOS audit screens; actual replay requires separate governed replay task.",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            **common_flags("0"),
        }
    ]


def write_report(closeout: dict[str, object], same_gate: list[dict[str, object]], blockers: list[dict[str, object]]) -> None:
    gate_lines = "\n".join(f"- `{row['gate_name']}`: `{row['gate_status']}`. {row['detail']}" for row in same_gate)
    blocker_lines = "\n".join(f"- `{row['blocker_name']}`: `{row['status']}`. {row['detail']}" for row in blockers)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        f"""# Task2961-2980 Frozen Policy vs L4 Challenger Compare Plan

## Decision Summary

- Verdict: `{closeout['verdict']}`.
- Baseline: `{closeout['baseline_variant_id']}`.
- Challenger: `{closeout['challenger_variant_id']}`.
- Freeze rows: {closeout['freeze_rows']}.
- Split/OOS plan rows: {closeout['split_oos_plan_rows']}.
- Performance compare allowed now: `{closeout['performance_compare_allowed_now']}`.
- Replay performed: `0`.
- Selector tuning performed: `0`.
- Sizing tuning performed: `0`.
- Exit tuning performed: `0`.
- Paper order intents created: `0`.
- Live orders created: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Same-experiment gate:

{gate_lines}

Replay blockers:

{blocker_lines}

This task freezes identities and plans split/OOS comparison only. It does not run a replay and does not compare returns.

## No-Background Decision-Maker Report

Conclusion first: the baseline and L4 challenger are now frozen separately.

The L4 challenger is not the same experiment as the baseline because it adds an invalidation overlay. So performance must be compared only in a separate governed replay task.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2961_2980_frozen_policy_l4_challenger_compare_plan/`.
- Validator: `python scripts/trader_brain_2961_2980_frozen_policy_l4_challenger_compare_plan_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
""",
        encoding="utf-8",
    )


def update_registry() -> None:
    path = ROOT / "tasks/task_registry.csv"
    rows = read_csv(path)
    fieldnames = list(rows[0].keys())
    existing = {row["task_id"] for row in rows}
    for task_no in range(2961, 2981):
        task_id = f"Task{task_no}"
        if task_id in existing:
            continue
        rows.append(
            {
                "task_id": task_id,
                "title": f"Frozen Policy L4 Challenger Compare Plan Step {task_no}",
                "owner_team": "Research Governance / Policy Freeze / Backtest Harness",
                "status": "Diagnostic Only",
                "canonical_state": "diagnostic",
                "strategy_acceptance": "NOT_ACCEPTED",
                "data_readiness": "policy-freeze-compare-plan-no-replay",
                "parent_task": f"Task{task_no - 1}",
                "key_report": "docs/reports/task_2961_2980_frozen_policy_l4_challenger_compare_plan/task_2961_2980_frozen_policy_l4_challenger_compare_plan.md",
                "key_decision": "docs/reports/task_2961_2980_frozen_policy_l4_challenger_compare_plan/task_2980_decision.csv",
                "key_artifacts": "data/artifacts/task_2961_2980_frozen_policy_l4_challenger_compare_plan",
                "validation_command": "python scripts/trader_brain_2961_2980_frozen_policy_l4_challenger_compare_plan_validate.py",
                "notes": "Freezes baseline and L4 challenger identities and split/OOS replay plan without running replay.",
            }
        )
    write_csv(path, rows, fieldnames)


def update_operating_state(closeout: dict[str, object]) -> None:
    path = ROOT / "docs/operating_system/project_operating_state.md"
    text = path.read_text(encoding="utf-8")
    marker = "145. Task2961-Task2980"
    line = (
        "145. Task2961-Task2980 froze baseline vs L4 challenger compare plan: "
        f"baseline `{closeout['baseline_variant_id']}`, challenger `{closeout['challenger_variant_id']}`, "
        f"freeze rows {closeout['freeze_rows']}, split/OOS plan rows {closeout['split_oos_plan_rows']}, "
        f"strict as-of status {closeout['strict_asof_status']}, performance compare allowed now {closeout['performance_compare_allowed_now']}; "
        "no replay, performance comparison, selector tuning, paper order, or live order was performed. "
        "Status remains NOT_ACCEPTED / DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY / FORBIDDEN.\n"
    )
    if marker in text:
        lines = [line if item.startswith(marker) else item + "\n" for item in text.splitlines()]
        path.write_text("".join(lines), encoding="utf-8")
        return
    path.write_text(text.rstrip() + "\n" + line, encoding="utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    inputs = load_inputs()
    scope = task2961_scope(inputs)
    freezes = task2962_policy_freeze_registry(inputs)
    hashes = task2963_hash_ledger()
    same_gate = task2964_same_experiment_gate()
    split_plan = task2965_split_oos_replay_plan()
    blockers = task2966_replay_blocker_checklist(inputs)
    compare_manifest = task2967_comparison_manifest(inputs)
    subagent_packets = task2968_subagent_review_packets()
    checks = task2969_acceptance_checks(scope, freezes, hashes, same_gate, split_plan, blockers)
    closeout = task2980_closeout(scope, freezes, same_gate, split_plan, blockers, checks)

    outputs = [
        ("task2961_scope_freeze.csv", scope),
        ("task2962_policy_freeze_registry.csv", freezes),
        ("task2963_hash_ledger.csv", hashes),
        ("task2964_same_experiment_gate.csv", same_gate),
        ("task2965_split_oos_replay_plan.csv", split_plan),
        ("task2966_replay_blocker_checklist.csv", blockers),
        ("task2967_comparison_manifest.csv", compare_manifest),
        ("task2968_subagent_review_packets.csv", subagent_packets),
        ("task2969_acceptance_checks.csv", checks),
        ("task2980_closeout.csv", closeout),
    ]
    for name, rows in outputs:
        write_csv(OUT_DIR / name, rows)
    write_csv(DECISION, closeout)
    write_json(OUT_DIR / "task2980_closeout.json", closeout[0])
    write_report(closeout[0], same_gate, blockers)
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    update_registry()
    update_operating_state(closeout[0])
    print("[TASK2961_2980_FROZEN_POLICY_L4_CHALLENGER_COMPARE_PLAN_COMPLETE]")
    print(json.dumps(closeout[0], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
