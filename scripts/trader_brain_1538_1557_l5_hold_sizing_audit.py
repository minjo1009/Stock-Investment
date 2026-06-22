from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

import trader_brain_1518_1537_l5_position_operating_brain as l5
from task_artifact_manifest import write_manifest


ROOT = Path(__file__).resolve().parents[1]
TASK1518 = ROOT / "data/artifacts/task_1518_1537_l5_position_operating_brain"
OUT_DIR = ROOT / "data/artifacts/task_1538_1557_l5_hold_sizing_audit"
REPORT_DIR = ROOT / "docs/reports/task_1538_1557_l5_hold_sizing_audit"
REPORT = REPORT_DIR / "task_1538_1557_l5_hold_sizing_audit.md"
DECISION = REPORT_DIR / "task_1538_1557_decision.csv"

AUTHORITY = "DIAGNOSTIC_L5_HOLD_SIZING_AUDIT_ONLY"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else ["empty"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def to_float(value: object, default: float = 0.0) -> float:
    try:
        if value in ("", None):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def expert_audit_rows() -> list[dict[str, object]]:
    rows = [
        ("quant_pm", "hold_extension_must_be_counterfactual_tested", "A hold rule is only useful if actual replay beats a no-hold replay, not merely scheduled-only."),
        ("event_driven_trader", "hold_quality_must_be_trade_level", "Extended trades must be audited one by one because a few winners can hide weak thesis tracking."),
        ("risk_manager", "cap_sizing_is_risk_control_not_alpha", "Cap-only sizing should be judged by return cost versus drawdown improvement."),
        ("portfolio_construction", "no_leverage_until_repeatable_delta", "Full sizing and leverage remain blocked unless L5 delta is robust after audit."),
        ("backend_engineer", "audit_artifacts_must_not_feed_assignment", "Scenario PnL is audit-only and cannot enter entry, exit, replacement, or sizing assignment."),
        ("governance", "acceptance_unchanged", "A positive audit can open the next design task but cannot accept the strategy."),
    ]
    return [
        {
            "task_id": "Task1538",
            "audit_id": f"L5HOLDSIZE1538-{idx:03d}",
            "expert_role": role,
            "audit_instruction": instruction,
            "feedback": feedback,
            "review_authority": "GPT_EXPERT_REVIEW_ONLY_NOT_SOURCE_OF_TRUTH",
            "authority": AUTHORITY,
        }
        for idx, (role, instruction, feedback) in enumerate(rows, 1)
    ]


def scenario_rows() -> list[dict[str, object]]:
    rows = [
        ("actual_l5_operating", "Original Task1518 L5 operating brain: hold extension on and cap-only sizing on."),
        ("no_hold_extension", "Hold extension removed; all original hold_extend actions close at scheduled exit."),
        ("full_size_no_cap", "Cap-only sizing removed; all selected rows use 1.0 allocation while original exits remain."),
        ("no_hold_full_size", "Both hold extension and cap-only sizing removed."),
        ("scheduled_only_counterfactual", "No L5 exit action; scheduled-only exit with original cap-only sizing."),
    ]
    return [
        {
            "task_id": "Task1539",
            "scenario_id": scenario_id,
            "scenario_definition": definition,
            "outcome_used_for_assignment": "0",
            "outcome_used_for_audit_only": "1",
            "authority": AUTHORITY,
        }
        for scenario_id, definition in rows
    ]


def load_specs_by_id() -> dict[str, dict[str, str]]:
    return {row["trade_spec_id"]: row for row in read_csv(l5.TASK1201 / "task1203_l5_trade_specs.csv")}


def clone_rows(rows: list[dict[str, str | object]]) -> list[dict[str, object]]:
    return [dict(row) for row in rows]


def remove_hold_extension(exit_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = clone_rows(exit_rows)
    for row in rows:
        if row.get("exit_action") == "hold_extend":
            row["exit_action"] = "scheduled_exit"
            row["exit_reason"] = "hold_extension_removed_scheduled_exit"
            row["exit_date_override"] = ""
    return rows


def remove_cap_sizing(policy_specs: list[dict[str, object]]) -> list[dict[str, object]]:
    rows = clone_rows(policy_specs)
    for row in rows:
        row["position_size_cap_multiplier"] = 1.0
    return rows


def retag_rows(rows: list[dict[str, object]], task_id: str, scenario_id: str) -> list[dict[str, object]]:
    tagged = []
    for row in rows:
        item = dict(row)
        item["task_id"] = task_id
        item["scenario_id"] = scenario_id
        item["outcome_used_for_assignment"] = "0"
        item["outcome_used_for_audit_only"] = "1"
        item["authority"] = AUTHORITY
        tagged.append(item)
    return tagged


def retag_metrics(rows: list[dict[str, object]], scenario_id: str) -> list[dict[str, object]]:
    tagged = []
    for row in rows:
        item = dict(row)
        item["task_id"] = "Task1540"
        item["scenario_id"] = scenario_id
        item["outcome_used_for_assignment"] = "0"
        item["outcome_used_for_audit_only"] = "1"
        item["strategy_acceptance"] = "NOT_ACCEPTED"
        item["deployment_readiness"] = "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY"
        item["real_capital"] = "FORBIDDEN"
        item["authority"] = AUTHORITY
        tagged.append(item)
    return tagged


def run_scenarios() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    specs_by_id = load_specs_by_id()
    final_specs = clone_rows(read_csv(TASK1518 / "task1524_policy_specs_final.csv"))
    exit_rows = clone_rows(read_csv(TASK1518 / "task1523_exit_decision_panel.csv"))
    scenarios = {
        "actual_l5_operating": (final_specs, exit_rows, False),
        "no_hold_extension": (final_specs, remove_hold_extension(exit_rows), False),
        "full_size_no_cap": (remove_cap_sizing(final_specs), exit_rows, False),
        "no_hold_full_size": (remove_cap_sizing(final_specs), remove_hold_extension(exit_rows), False),
        "scheduled_only_counterfactual": (final_specs, exit_rows, True),
    }
    all_trades: list[dict[str, object]] = []
    all_equity: list[dict[str, object]] = []
    all_metrics: list[dict[str, object]] = []
    for scenario_id, (policy_specs, scenario_exits, scheduled_only) in scenarios.items():
        trades, equity = l5.run_operating_replay(policy_specs, specs_by_id, scenario_exits, scheduled_only=scheduled_only)
        metrics = l5.build_metrics(trades, equity)
        all_trades.extend(retag_rows(trades, "Task1540", scenario_id))
        all_equity.extend(retag_rows(equity, "Task1540", scenario_id))
        all_metrics.extend(retag_metrics(metrics, scenario_id))
    return all_trades, all_equity, all_metrics


def metric_lookup(metrics: list[dict[str, object]]) -> dict[tuple[str, str], dict[str, object]]:
    return {(str(row["scenario_id"]), str(row["policy_variant_id"])): row for row in metrics}


def build_scenario_comparison(metrics: list[dict[str, object]]) -> list[dict[str, object]]:
    lookup = metric_lookup(metrics)
    pairs = [
        ("hold_extension_effect", "actual_l5_operating", "no_hold_extension"),
        ("cap_only_sizing_effect", "actual_l5_operating", "full_size_no_cap"),
        ("combined_l5_effect", "actual_l5_operating", "no_hold_full_size"),
        ("actual_vs_scheduled_only", "actual_l5_operating", "scheduled_only_counterfactual"),
    ]
    rows: list[dict[str, object]] = []
    idx = 1
    for policy_id in l5.POLICIES:
        for comparison_id, test_scenario, base_scenario in pairs:
            test = lookup[(test_scenario, policy_id)]
            base = lookup[(base_scenario, policy_id)]
            final_delta = to_float(test["final_equity"]) - to_float(base["final_equity"])
            cagr_delta = to_float(test["cagr"]) - to_float(base["cagr"])
            mdd_delta = to_float(test["max_drawdown"]) - to_float(base["max_drawdown"])
            rows.append(
                {
                    "task_id": "Task1541",
                    "comparison_row_id": f"L5HOLDSIZE1541-{idx:04d}",
                    "comparison_id": comparison_id,
                    "policy_variant_id": policy_id,
                    "test_scenario_id": test_scenario,
                    "base_scenario_id": base_scenario,
                    "test_final_equity": test["final_equity"],
                    "base_final_equity": base["final_equity"],
                    "final_equity_delta": round(final_delta, 4),
                    "test_cagr": test["cagr"],
                    "base_cagr": base["cagr"],
                    "cagr_delta": round(cagr_delta, 6),
                    "test_max_drawdown": test["max_drawdown"],
                    "base_max_drawdown": base["max_drawdown"],
                    "mdd_delta_positive_is_better": round(mdd_delta, 6),
                    "test_better_final": "1" if final_delta > 0 else "0",
                    "test_better_mdd": "1" if mdd_delta > 0 else "0",
                    "outcome_used_for_assignment": "0",
                    "outcome_used_for_audit_only": "1",
                    "authority": AUTHORITY,
                }
            )
            idx += 1
    return rows


def build_hold_trade_audit(trades: list[dict[str, object]]) -> list[dict[str, object]]:
    actual = {
        (row["policy_variant_id"], row["trade_spec_id"]): row
        for row in trades
        if row["scenario_id"] == "actual_l5_operating" and row.get("hold_extension_used") == "1"
    }
    no_hold = {
        (row["policy_variant_id"], row["trade_spec_id"]): row
        for row in trades
        if row["scenario_id"] == "no_hold_extension"
    }
    rows: list[dict[str, object]] = []
    for idx, key in enumerate(sorted(actual), 1):
        actual_row = actual[key]
        base_row = no_hold.get(key, {})
        delta = to_float(actual_row.get("net_return")) - to_float(base_row.get("net_return"))
        rows.append(
            {
                "task_id": "Task1542",
                "hold_audit_id": f"L5HOLD1542-{idx:05d}",
                "policy_variant_id": actual_row["policy_variant_id"],
                "trade_spec_id": actual_row["trade_spec_id"],
                "candidate_source_id": actual_row["candidate_source_id"],
                "symbol": actual_row["symbol"],
                "decision_asof_ts": actual_row["decision_asof_ts"],
                "actual_exit_date": actual_row["actual_exit_date"],
                "no_hold_exit_date": base_row.get("actual_exit_date", ""),
                "actual_net_return": actual_row["net_return"],
                "no_hold_net_return": base_row.get("net_return", ""),
                "hold_net_return_delta": round(delta, 8),
                "hold_helped_trade": "1" if delta > 0 else "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_cap_trade_audit(trades: list[dict[str, object]]) -> list[dict[str, object]]:
    actual = {
        (row["policy_variant_id"], row["trade_spec_id"]): row
        for row in trades
        if row["scenario_id"] == "actual_l5_operating"
    }
    full = {
        (row["policy_variant_id"], row["trade_spec_id"]): row
        for row in trades
        if row["scenario_id"] == "full_size_no_cap"
    }
    rows: list[dict[str, object]] = []
    idx = 1
    for key, actual_row in sorted(actual.items()):
        if to_float(actual_row.get("position_size_cap_multiplier"), 1.0) >= 1.0:
            continue
        full_row = full.get(key, {})
        rows.append(
            {
                "task_id": "Task1543",
                "cap_audit_id": f"L5CAP1543-{idx:05d}",
                "policy_variant_id": actual_row["policy_variant_id"],
                "trade_spec_id": actual_row["trade_spec_id"],
                "candidate_source_id": actual_row["candidate_source_id"],
                "symbol": actual_row["symbol"],
                "decision_asof_ts": actual_row["decision_asof_ts"],
                "thesis_state": actual_row["thesis_state"],
                "actual_size_cap_multiplier": actual_row["position_size_cap_multiplier"],
                "actual_pnl": actual_row["pnl"],
                "full_size_pnl": full_row.get("pnl", ""),
                "pnl_given_up_by_cap": round(to_float(full_row.get("pnl")) - to_float(actual_row.get("pnl")), 4),
                "cap_reduced_loss": "1" if to_float(full_row.get("pnl")) < to_float(actual_row.get("pnl")) else "0",
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
        idx += 1
    return rows


def build_exit_reason_summary(trades: list[dict[str, object]]) -> list[dict[str, object]]:
    grouped: dict[tuple[str, str, str], list[dict[str, object]]] = defaultdict(list)
    for row in trades:
        grouped[(str(row["scenario_id"]), str(row["policy_variant_id"]), str(row["exit_reason"]))].append(row)
    rows: list[dict[str, object]] = []
    for idx, ((scenario_id, policy_id, exit_reason), group) in enumerate(sorted(grouped.items()), 1):
        rows.append(
            {
                "task_id": "Task1544",
                "exit_summary_id": f"L5EXIT1544-{idx:04d}",
                "scenario_id": scenario_id,
                "policy_variant_id": policy_id,
                "exit_reason": exit_reason,
                "trade_count": len(group),
                "avg_net_return": round(mean([to_float(row["net_return"]) for row in group]), 8),
                "total_pnl": round(sum(to_float(row["pnl"]) for row in group), 4),
                "outcome_used_for_assignment": "0",
                "outcome_used_for_audit_only": "1",
                "authority": AUTHORITY,
            }
        )
    return rows


def build_diagnosis(
    metrics: list[dict[str, object]],
    comparisons: list[dict[str, object]],
    hold_audit: list[dict[str, object]],
    cap_audit: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    lookup = metric_lookup(metrics)
    hold_rows = [row for row in comparisons if row["comparison_id"] == "hold_extension_effect"]
    cap_rows = [row for row in comparisons if row["comparison_id"] == "cap_only_sizing_effect"]
    actual_best = max(
        [row for row in metrics if row["scenario_id"] == "actual_l5_operating"],
        key=lambda row: to_float(row["final_equity"]),
    )
    hold_help_rate_by_policy: dict[str, float] = {}
    for policy_id in l5.POLICIES:
        rows = [row for row in hold_audit if row["policy_variant_id"] == policy_id]
        hold_help_rate_by_policy[policy_id] = mean([1.0 if row["hold_helped_trade"] == "1" else 0.0 for row in rows])
    cap_loss_rows = [row for row in cap_audit if row["cap_reduced_loss"] == "1"]
    diagnosis = [
        {
            "task_id": "Task1545",
            "diagnosis_id": "L5DIAG1545-001",
            "finding": "hold_extension_is_primary_positive_driver",
            "evidence": "; ".join(
                f"{row['policy_variant_id']} final_delta={row['final_equity_delta']} cagr_delta={row['cagr_delta']} hold_help_rate={round(hold_help_rate_by_policy[row['policy_variant_id']], 4)}"
                for row in hold_rows
            ),
            "decision": "keep_hold_extension_but_audit_trade_level_quality_before_more_leverage",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1545",
            "diagnosis_id": "L5DIAG1545-002",
            "finding": "cap_only_sizing_costs_return_and_may_reduce_or_increase_drawdown_by_policy",
            "evidence": "; ".join(
                f"{row['policy_variant_id']} final_delta={row['final_equity_delta']} mdd_delta={row['mdd_delta_positive_is_better']}"
                for row in cap_rows
            ),
            "decision": "do_not_promote_full_sizing_until_cap_benefit_is_state_specific_not_blanket",
            "authority": AUTHORITY,
        },
        {
            "task_id": "Task1545",
            "diagnosis_id": "L5DIAG1545-003",
            "finding": "strategy_still_not_accepted",
            "evidence": f"best_actual={actual_best['policy_variant_id']} final={actual_best['final_equity']} cagr={actual_best['cagr']} mdd={actual_best['max_drawdown']}",
            "decision": "next_design_should_target_selective_hold_extension_and_state_specific_cap_release",
            "authority": AUTHORITY,
        },
    ]
    gate = [
        {
            "task_id": "Task1556",
            "best_actual_policy_variant_id": actual_best["policy_variant_id"],
            "best_actual_final_equity": actual_best["final_equity"],
            "best_actual_cagr": actual_best["cagr"],
            "best_actual_max_drawdown": actual_best["max_drawdown"],
            "target_cagr_30pct_met": actual_best["target_cagr_30pct_met"],
            "target_mdd_minus30pct_met": actual_best["target_mdd_minus30pct_met"],
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "decision": "audit_supports_l5_driver_diagnosis_not_strategy_acceptance",
            "authority": AUTHORITY,
        }
    ]
    closeout = [
        {
            "task_id": "Task1557",
            "verdict": "l5_hold_sizing_audit_complete_not_accepted",
            "hold_extension_primary_driver": "1" if all(row["test_better_final"] == "1" for row in hold_rows) else "0",
            "cap_only_blanket_release_approved": "0",
            "next_action": "build selective hold-extension quality gate and state-specific cap-release shadow policy",
            "strategy_acceptance": "NOT_ACCEPTED",
            "deployment_readiness": "DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "real_capital": "FORBIDDEN",
            "authority": AUTHORITY,
        }
    ]
    return diagnosis, gate, closeout


def write_report(
    metrics: list[dict[str, object]],
    comparisons: list[dict[str, object]],
    hold_audit: list[dict[str, object]],
    cap_audit: list[dict[str, object]],
    diagnosis: list[dict[str, object]],
    closeout: dict[str, object],
) -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    actual = [row for row in metrics if row["scenario_id"] == "actual_l5_operating"]
    no_hold = [row for row in comparisons if row["comparison_id"] == "hold_extension_effect"]
    cap = [row for row in comparisons if row["comparison_id"] == "cap_only_sizing_effect"]
    lines = [
        "# Task1538-1557 L5 Hold Extension and Sizing Audit",
        "",
        "## Decision Summary",
        "",
        f"- Verdict: `{closeout['verdict']}`.",
        "- Conclusion: hold extension is the main positive L5 driver; blanket cap release is not approved.",
        "- Strategy acceptance status: `NOT_ACCEPTED`.",
        "- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.",
        "- Real capital: `FORBIDDEN`.",
        "",
        "## Quant Expert Report",
        "",
        "Actual L5 operating metrics:",
        "",
        "| Policy | Final | CAGR | MDD | Trades | Hold Ext | Source Exit | Price Exit |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for row in actual:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['final_equity']} | {row['cagr']} | {row['max_drawdown']} | {row['trade_count']} | {row['hold_extension_count']} | {row['source_receipt_exit_count']} | {row['price_path_exit_count']} |"
        )
    lines.extend(
        [
            "",
            "Hold extension counterfactual:",
            "",
            "| Policy | Actual Final | No-Hold Final | Delta | CAGR Delta | MDD Delta |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in no_hold:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['test_final_equity']} | {row['base_final_equity']} | {row['final_equity_delta']} | {row['cagr_delta']} | {row['mdd_delta_positive_is_better']} |"
        )
    lines.extend(
        [
            "",
            "Cap-only sizing counterfactual:",
            "",
            "| Policy | Cap Final | Full-Size Final | Delta | CAGR Delta | MDD Delta |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in cap:
        lines.append(
            f"| `{row['policy_variant_id']}` | {row['test_final_equity']} | {row['base_final_equity']} | {row['final_equity_delta']} | {row['cagr_delta']} | {row['mdd_delta_positive_is_better']} |"
        )
    hold_help_rate = mean([1.0 if row["hold_helped_trade"] == "1" else 0.0 for row in hold_audit])
    cap_reduced_loss_rate = mean([1.0 if row["cap_reduced_loss"] == "1" else 0.0 for row in cap_audit])
    lines.extend(
        [
            "",
            "## No-Background Decision-Maker Report",
            "",
            "1. L5가 좋아진 제일 큰 이유는 보유 연장입니다.",
            f"2. 보유 연장 trade 중 이긴 비율은 {round(hold_help_rate, 4)}입니다.",
            "3. cap-only sizing은 알파 엔진이 아니라 안전장치입니다.",
            f"4. cap이 손실을 줄인 cap 대상 trade 비율은 {round(cap_reduced_loss_rate, 4)}입니다.",
            "5. 그래서 다음은 전체 cap 해제가 아니라, 상태별 cap 해제 shadow policy입니다.",
            "6. 전략 승인 상태는 그대로 아닙니다.",
            "",
            "## Diagnosis",
            "",
        ]
    )
    for row in diagnosis:
        lines.append(f"- `{row['finding']}`: {row['decision']}. Evidence: {row['evidence']}")
    lines.extend(
        [
            "",
            "## Artifact Manifest",
            "",
            "- `task1538_expert_audit.csv`",
            "- `task1539_scenario_definitions.csv`",
            "- `task1540_scenario_replay_trades.csv`",
            "- `task1540_scenario_replay_equity.csv`",
            "- `task1540_scenario_replay_metrics.csv`",
            "- `task1541_scenario_comparison.csv`",
            "- `task1542_hold_extension_trade_audit.csv`",
            "- `task1543_cap_sizing_trade_audit.csv`",
            "- `task1544_exit_reason_summary.csv`",
            "- `task1545_audit_diagnosis.csv`",
            "- `task1556_acceptance_gate.csv`",
            "- `task1557_closeout.csv/json`",
            "",
            "Validation commands:",
            "",
            "- `python scripts/trader_brain_1538_1557_l5_hold_sizing_audit_validate.py`",
            "",
            "```text",
            "Test results do not modify strategy acceptance status.",
            "Strategy: NOT_ACCEPTED",
            "Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
            "Real Capital: FORBIDDEN",
            "```",
        ]
    )
    REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_decision(gate: list[dict[str, object]]) -> None:
    write_csv(DECISION, gate)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    expert = expert_audit_rows()
    scenarios = scenario_rows()
    trades, equity, metrics = run_scenarios()
    comparisons = build_scenario_comparison(metrics)
    hold_audit = build_hold_trade_audit(trades)
    cap_audit = build_cap_trade_audit(trades)
    exit_summary = build_exit_reason_summary(trades)
    diagnosis, gate, closeout = build_diagnosis(metrics, comparisons, hold_audit, cap_audit)

    write_csv(OUT_DIR / "task1538_expert_audit.csv", expert)
    write_csv(OUT_DIR / "task1539_scenario_definitions.csv", scenarios)
    write_csv(OUT_DIR / "task1540_scenario_replay_trades.csv", trades)
    write_csv(OUT_DIR / "task1540_scenario_replay_equity.csv", equity)
    write_csv(OUT_DIR / "task1540_scenario_replay_metrics.csv", metrics)
    write_csv(OUT_DIR / "task1541_scenario_comparison.csv", comparisons)
    write_csv(OUT_DIR / "task1542_hold_extension_trade_audit.csv", hold_audit)
    write_csv(OUT_DIR / "task1543_cap_sizing_trade_audit.csv", cap_audit)
    write_csv(OUT_DIR / "task1544_exit_reason_summary.csv", exit_summary)
    write_csv(OUT_DIR / "task1545_audit_diagnosis.csv", diagnosis)
    write_csv(OUT_DIR / "task1556_acceptance_gate.csv", gate)
    write_csv(OUT_DIR / "task1557_closeout.csv", closeout)
    write_json(OUT_DIR / "task1557_closeout.json", closeout[0])
    write_decision(gate)
    write_report(metrics, comparisons, hold_audit, cap_audit, diagnosis, closeout[0])
    write_manifest(OUT_DIR, OUT_DIR / "artifact_manifest.csv")
    print(f"[TASK1538_1557] wrote {OUT_DIR}")


if __name__ == "__main__":
    main()
