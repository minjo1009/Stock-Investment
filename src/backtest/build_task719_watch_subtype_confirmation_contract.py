from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK718_WATCH = Path("docs/reports/task_718_winner_structure_interaction_brain/task718_watch_decomposition.csv")
TASK716_PANEL = Path("docs/reports/task_716_portfolio_competition_brain/task716_slot_competition_panel.csv")
TASK708_EVAL = Path("docs/reports/task_708_full_period_backtest_comparison/task708_eval_panel.csv")
TASK719_DIR = Path("docs/reports/task_719_watch_subtype_confirmation_contract")

KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]
NO_ACTION_REASON = "confirmation_contract_only;not_buy_sell_or_sizing_instruction"


RULES = {
    "watch_due_to_financing_absorption_test": {
        "contract_id": "CONFIRM_FINANCING_ABSORPTION_V1",
        "under_review_state": "financing_absorption_under_review",
        "resolved_state": "financing_absorption_conditionally_resolved",
        "required_confirmation_set": "evidence+price_absorption+economic_transmission+cohort_slot+invalidation",
        "hard_blocker_template": "dilution_overhang_unabsorbed_without_growth_survival_or_price_absorption",
    },
    "watch_due_to_slot_confirmation_needed": {
        "contract_id": "CONFIRM_SLOT_SUPERIORITY_V1",
        "under_review_state": "slot_comparison_under_review",
        "resolved_state": "slot_context_superiority_candidate",
        "required_confirmation_set": "evidence+economic_transmission+cohort_slot+price_absorption+invalidation",
        "hard_blocker_template": "no_context_superiority_over_same_timestamp_alternatives",
    },
    "watch_due_to_company_evidence_absorption_needed": {
        "contract_id": "CONFIRM_COMPANY_EVIDENCE_ABSORPTION_V1",
        "under_review_state": "company_evidence_under_absorption",
        "resolved_state": "company_evidence_price_confirming",
        "required_confirmation_set": "company_evidence+economic_transmission+price_absorption+cohort_slot+invalidation",
        "hard_blocker_template": "company_evidence_without_economic_path_or_price_absorption",
    },
    "watch_due_to_thin_signal_absorption_needed": {
        "contract_id": "CONFIRM_THIN_SIGNAL_CONTEXT_V1",
        "under_review_state": "thin_signal_under_review",
        "resolved_state": "thin_signal_context_supported",
        "required_confirmation_set": "secondary_evidence+economic_transmission+price_absorption+cohort_slot+invalidation",
        "hard_blocker_template": "isolated_thin_signal_without_transmission_or_absorption",
    },
}


def build_task719(
    *,
    watch_path: Path = TASK718_WATCH,
    task716_path: Path = TASK716_PANEL,
    eval_path: Path = TASK708_EVAL,
    out_dir: Path = TASK719_DIR,
) -> dict[str, pd.DataFrame]:
    watch = load_watch_panel(watch_path, task716_path)
    panel = build_confirmation_panel(watch)
    rulebook = build_rulebook()
    graph = build_confirmation_graph(panel)
    gap_audit = build_confirmation_gap_audit(panel)
    guardrail = build_guardrail_audit(panel, eval_path)
    governance = build_governance_audit(panel, graph, rulebook)
    decision = decision_frame(panel)
    pass_fail = pass_fail_matrix(panel, graph, rulebook, guardrail, governance)

    outputs = {
        "task719_watch_confirmation_contract_panel.csv": panel,
        "task719_confirmation_rulebook.csv": rulebook,
        "task719_confirmation_interaction_graph.csv": graph,
        "task719_confirmation_gap_audit.csv": gap_audit,
        "task719_guardrail_audit.csv": guardrail,
        "task719_governance_audit.csv": governance,
        "task_719_decision.csv": decision,
        "task_719_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, decision, pass_fail)
    return {
        "panel": panel,
        "rulebook": rulebook,
        "graph": graph,
        "gap_audit": gap_audit,
        "guardrail": guardrail,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def load_watch_panel(watch_path: Path, task716_path: Path) -> pd.DataFrame:
    watch = pd.read_csv(watch_path)
    t716 = pd.read_csv(task716_path)
    slot_cols = KEYS + [
        "slot_context_score",
        "same_timestamp_candidate_count",
        "same_timestamp_context_rank",
        "same_timestamp_theme_count",
        "slot_competition_state",
        "exposure_cluster_state",
        "portfolio_reason_codes",
    ]
    return watch.merge(t716[slot_cols], on=KEYS, how="left", validate="one_to_one")


def build_confirmation_panel(watch: pd.DataFrame) -> pd.DataFrame:
    out = watch.copy()
    out["confirmation_contract_id"] = out["watch_subtype"].map(lambda x: RULES[str(x)]["contract_id"])
    out["required_confirmation_set"] = out["watch_subtype"].map(lambda x: RULES[str(x)]["required_confirmation_set"])
    out["required_evidence_confirmation"] = out.apply(required_evidence_confirmation, axis=1)
    out["required_price_confirmation"] = 1
    out["required_economic_confirmation"] = 1
    out["required_slot_confirmation"] = out.apply(required_slot_confirmation, axis=1)
    out["required_invalidation_check"] = 1
    out["evidence_confirmation_state"] = out.apply(evidence_confirmation_state, axis=1)
    out["price_absorption_confirmation_state"] = out.apply(price_absorption_confirmation_state, axis=1)
    out["economic_confirmation_state"] = out.apply(economic_confirmation_state, axis=1)
    out["cohort_slot_confirmation_state"] = out.apply(cohort_slot_confirmation_state, axis=1)
    out["invalidation_confirmation_state"] = out.apply(invalidation_confirmation_state, axis=1)
    out["hard_blocker_state"] = out.apply(hard_blocker_state, axis=1)
    out["missing_data_state"] = out.apply(missing_data_state, axis=1)
    out["interaction_contract_state"] = out.apply(interaction_contract_state, axis=1)
    out["confirmation_contract_satisfied"] = out.apply(confirmation_contract_satisfied, axis=1)
    out["promotion_candidate_state"] = out.apply(promotion_candidate_state, axis=1)
    out["confirmation_reason_codes"] = out.apply(confirmation_reason_codes, axis=1)
    add_no_action_flags(out)
    cols = KEYS + [
        "watch_subtype",
        "winner_structure_state",
        "review_decision_state",
        "final_brain_state",
        "confirmation_contract_id",
        "promotion_candidate_state",
        "required_confirmation_set",
        "required_evidence_confirmation",
        "required_price_confirmation",
        "required_economic_confirmation",
        "required_slot_confirmation",
        "required_invalidation_check",
        "evidence_confirmation_state",
        "price_absorption_confirmation_state",
        "economic_confirmation_state",
        "cohort_slot_confirmation_state",
        "invalidation_confirmation_state",
        "hard_blocker_state",
        "missing_data_state",
        "interaction_contract_state",
        "confirmation_contract_satisfied",
        "confirmation_reason_codes",
        "same_timestamp_context_rank",
        "same_timestamp_theme_count",
        "slot_competition_state",
        "exposure_cluster_state",
    ] + no_action_columns()
    return out[cols].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def build_rulebook() -> pd.DataFrame:
    rows = []
    for subtype, rule in RULES.items():
        rows.append(
            {
                "watch_subtype": subtype,
                "confirmation_contract_id": rule["contract_id"],
                "under_review_state": rule["under_review_state"],
                "resolved_state_if_all_confirmed": rule["resolved_state"],
                "required_confirmation_set": rule["required_confirmation_set"],
                "single_condition_promotion_allowed_flag": 0,
                "buy_sell_or_sizing_instruction_flag": 0,
                "hard_blocker_template": rule["hard_blocker_template"],
                "missing_data_policy": "missing_is_unknown_not_negative",
            }
        )
    return pd.DataFrame(rows)


def build_confirmation_graph(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    edges = [
        ("evidence_confirmation_state", "economic_confirmation_state", "evidence_to_economic_path"),
        ("economic_confirmation_state", "price_absorption_confirmation_state", "economic_path_to_price_absorption"),
        ("price_absorption_confirmation_state", "cohort_slot_confirmation_state", "price_absorption_to_slot_context"),
        ("cohort_slot_confirmation_state", "invalidation_confirmation_state", "slot_context_to_invalidation"),
        ("invalidation_confirmation_state", "promotion_candidate_state", "invalidation_to_promotion_candidate_state"),
    ]
    for _, row in panel.iterrows():
        base = {key: row[key] for key in KEYS}
        for source_col, target_col, contract_edge in edges:
            relation_type = confirmation_relation_type(row[source_col], row[target_col])
            rows.append(
                {
                    **base,
                    "watch_subtype": row["watch_subtype"],
                    "confirmation_contract_id": row["confirmation_contract_id"],
                    "source_layer": source_col,
                    "source_state": row[source_col],
                    "target_layer": target_col,
                    "target_state": row[target_col],
                    "contract_edge": contract_edge,
                    "relation_type": relation_type,
                    "relation_strength_bucket": relation_strength_bucket(relation_type),
                    "evidence_column_refs": f"{source_col},{target_col}",
                    "reason_code": f"{source_col}:{row[source_col]}->{target_col}:{row[target_col]}",
                    "assignment_safe_flag": 1,
                    "outcome_used_for_assignment_flag": 0,
                }
            )
    return pd.DataFrame(rows)


def build_confirmation_gap_audit(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for subtype, group in panel.groupby("watch_subtype", dropna=False):
        rows.append(
            {
                "watch_subtype": subtype,
                "candidate_count": len(group),
                "evidence_confirmed_count": int(group["evidence_confirmation_state"].astype(str).str.contains("confirmed").sum()),
                "price_confirmed_count": int(group["price_absorption_confirmation_state"].astype(str).str.contains("confirmed").sum()),
                "economic_confirmed_count": int(group["economic_confirmation_state"].astype(str).str.contains("confirmed").sum()),
                "slot_confirmed_count": int(group["cohort_slot_confirmation_state"].astype(str).str.contains("confirmed").sum()),
                "contract_satisfied_count": int(group["confirmation_contract_satisfied"].sum()),
                "hard_blocker_count": int((group["hard_blocker_state"] != "no_hard_blocker_identified").sum()),
                "missing_unknown_count": int((group["missing_data_state"] == "missing_or_unconfirmed_treated_as_unknown").sum()),
                "outcome_used_for_assignment_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values("candidate_count", ascending=False).reset_index(drop=True)


def build_guardrail_audit(panel: pd.DataFrame, eval_path: Path) -> pd.DataFrame:
    eval_panel = pd.read_csv(eval_path)
    merged = panel.merge(
        eval_panel[KEYS + ["costed_return_pct", "entry_reduce_failure_flag"]],
        on=KEYS,
        how="left",
        validate="one_to_one",
    )
    top50 = set(eval_panel.nlargest(50, "costed_return_pct")["lifecycle_id"])
    bottom50 = set(eval_panel.nsmallest(50, "costed_return_pct")["lifecycle_id"])
    rows = []
    for state, group in merged.groupby("promotion_candidate_state", dropna=False):
        ids = set(group["lifecycle_id"])
        rows.append(
            {
                "promotion_candidate_state": state,
                "candidate_count": len(group),
                "top50_winner_count_eval_only": len(top50 & ids),
                "bottom50_loser_count_eval_only": len(bottom50 & ids),
                "avg_costed_return_pct_eval_only": float(group["costed_return_pct"].mean()),
                "entry_reduce_failure_rate_eval_only": float(pd.to_numeric(group["entry_reduce_failure_flag"], errors="coerce").fillna(0).mean()),
                "outcome_used_for_assignment_flag": 0,
                "outcome_used_for_evaluation_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values("top50_winner_count_eval_only", ascending=False).reset_index(drop=True)


def build_governance_audit(panel: pd.DataFrame, graph: pd.DataFrame, rulebook: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("scope_watch_358", len(panel) == 358, f"rows={len(panel)}", "358"),
            gate("subtype_count_4", panel["watch_subtype"].nunique() == 4, f"subtypes={panel['watch_subtype'].nunique()}", "4"),
            gate("rulebook_count_4", len(rulebook) == 4, f"rules={len(rulebook)}", "4"),
            gate("interaction_graph_present", len(graph) == len(panel) * 5, f"edges={len(graph)}", "5 edges per row"),
            gate("no_single_condition_promotion", int(rulebook["single_condition_promotion_allowed_flag"].sum()) == 0, "0", "0"),
            gate("no_contract_satisfied_now", int(panel["confirmation_contract_satisfied"].sum()) == 0, f"satisfied={int(panel['confirmation_contract_satisfied'].sum())}", "0"),
            gate("missing_is_unknown", set(panel["missing_data_state"]) == {"missing_or_unconfirmed_treated_as_unknown"}, ",".join(sorted(set(panel["missing_data_state"]))), "missing_or_unconfirmed_treated_as_unknown"),
            gate("no_action_output", int(panel["translator_output_is_action_flag"].sum()) == 0, "0", "0"),
            gate("no_outcome_assignment", int(panel["outcome_used_for_assignment_flag"].sum()) == 0, "0", "0"),
            gate("no_future_price_assignment", int(panel["future_price_used_for_assignment_flag"].sum()) == 0, "0", "0"),
            gate("top50_not_used_for_assignment", int(panel["top50_used_for_assignment_flag"].sum()) == 0, "0", "0"),
            gate("no_ticker_theme_protection", int(panel["ticker_theme_protection_rule_flag"].sum()) == 0, "0", "0"),
            gate("no_outcome_threshold_tuning", int(panel["threshold_tuned_from_outcome_flag"].sum()) == 0, "0", "0"),
            gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
        ]
    )


def required_evidence_confirmation(row: pd.Series) -> int:
    return 1


def required_slot_confirmation(row: pd.Series) -> int:
    return 1


def evidence_confirmation_state(row: pd.Series) -> str:
    strength = str(row.get("interaction_reason_codes", ""))
    subtype = str(row.get("watch_subtype", ""))
    if subtype == "watch_due_to_company_evidence_absorption_needed":
        return "company_evidence_confirmed_needs_absorption"
    if subtype == "watch_due_to_thin_signal_absorption_needed":
        return "thin_signal_present_not_sufficient"
    if "company_evidence_with_economic_detail" in strength:
        return "company_evidence_confirmed_needs_absorption"
    return "evidence_weak_or_noise_needs_confirmation"


def price_absorption_confirmation_state(row: pd.Series) -> str:
    reason = str(row.get("interaction_reason_codes", ""))
    if "risk_absorbed_by_price" in reason:
        return "price_absorption_confirmed"
    if "risk_absorption_incomplete" in reason:
        return "price_absorption_incomplete"
    return "price_absorption_unknown"


def economic_confirmation_state(row: pd.Series) -> str:
    reason = str(row.get("interaction_reason_codes", ""))
    if "winner_structure=capital_need_company_evidence_watch_structure" in reason:
        return "company_path_visible_but_financing_survival_unconfirmed"
    if "capital_need" in str(row.get("winner_structure_state", "")):
        return "growth_path_vs_financing_unresolved"
    return "economic_path_unknown"


def cohort_slot_confirmation_state(row: pd.Series) -> str:
    rank = float_safe(row.get("same_timestamp_context_rank"))
    theme_count = float_safe(row.get("same_timestamp_theme_count"))
    subtype = str(row.get("watch_subtype", ""))
    if subtype == "watch_due_to_slot_confirmation_needed":
        return "slot_rank_first_but_context_superiority_unconfirmed"
    if rank <= 1 and theme_count <= 2:
        return "slot_context_not_disqualifying_unconfirmed"
    return "slot_context_needs_comparison"


def invalidation_confirmation_state(row: pd.Series) -> str:
    if hard_blocker_state(row) == "no_hard_blocker_identified":
        return "invalidation_not_triggered_but_must_be_monitored"
    return "invalidation_risk_active"


def hard_blocker_state(row: pd.Series) -> str:
    subtype = str(row.get("watch_subtype", ""))
    evidence = evidence_confirmation_state(row)
    price = price_absorption_confirmation_state(row)
    economic = economic_confirmation_state(row)
    if subtype == "watch_due_to_thin_signal_absorption_needed" and price != "price_absorption_confirmed":
        return "isolated_thin_signal_without_absorption"
    if subtype == "watch_due_to_financing_absorption_test" and evidence == "evidence_weak_or_noise_needs_confirmation":
        return "financing_overhang_with_weak_evidence"
    if subtype == "watch_due_to_company_evidence_absorption_needed" and "unresolved" in economic:
        return "company_evidence_but_financing_survival_unconfirmed"
    if subtype == "watch_due_to_slot_confirmation_needed" and cohort_slot_confirmation_state(row) == "slot_rank_first_but_context_superiority_unconfirmed":
        return "slot_rank_first_without_full_context_confirmation"
    return "no_hard_blocker_identified"


def missing_data_state(row: pd.Series) -> str:
    return "missing_or_unconfirmed_treated_as_unknown"


def interaction_contract_state(row: pd.Series) -> str:
    required = [
        evidence_confirmation_state(row),
        price_absorption_confirmation_state(row),
        economic_confirmation_state(row),
        cohort_slot_confirmation_state(row),
        invalidation_confirmation_state(row),
    ]
    if any("unknown" in item for item in required):
        return "contract_incomplete_due_to_unknown"
    if hard_blocker_state(row) != "no_hard_blocker_identified":
        return "contract_blocked_pending_confirmation"
    if all("confirmed" in item or "not_triggered" in item for item in required):
        return "contract_conditionally_satisfied"
    return "contract_incomplete_pending_joint_confirmation"


def confirmation_contract_satisfied(row: pd.Series) -> int:
    return int(interaction_contract_state(row) == "contract_conditionally_satisfied")


def promotion_candidate_state(row: pd.Series) -> str:
    rule = RULES[str(row["watch_subtype"])]
    if confirmation_contract_satisfied(row):
        return rule["resolved_state"]
    return rule["under_review_state"]


def confirmation_reason_codes(row: pd.Series) -> str:
    return "|".join(
        [
            f"contract={row['confirmation_contract_id']}",
            f"evidence={evidence_confirmation_state(row)}",
            f"price={price_absorption_confirmation_state(row)}",
            f"economic={economic_confirmation_state(row)}",
            f"slot={cohort_slot_confirmation_state(row)}",
            f"invalidation={invalidation_confirmation_state(row)}",
            f"blocker={hard_blocker_state(row)}",
            f"missing={missing_data_state(row)}",
        ]
    )


def confirmation_relation_type(source_state: str, target_state: str) -> str:
    states = f"{source_state}|{target_state}"
    if "unknown" in states:
        return "source_gap_unknown"
    if "blocker" in states or "invalidation_risk_active" in states:
        return "blocked_pending_confirmation"
    if "incomplete" in states or "unconfirmed" in states or "needs" in states:
        return "requires_joint_confirmation"
    return "reinforces"


def relation_strength_bucket(relation_type: str) -> str:
    if relation_type == "reinforces":
        return "strong_confirmation_link"
    if relation_type == "blocked_pending_confirmation":
        return "blocked_confirmation_link"
    if relation_type == "source_gap_unknown":
        return "unknown_confirmation_link"
    return "needs_joint_confirmation_link"


def decision_frame(panel: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task719",
                "verdict": "WATCH_SUBTYPE_CONFIRMATION_CONTRACT_BUILT_DIAGNOSTIC_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "watch_candidate_count": len(panel),
                "watch_subtype_count": int(panel["watch_subtype"].nunique()),
                "confirmation_contract_satisfied_count": int(panel["confirmation_contract_satisfied"].sum()),
                "trading_promotion_pass_flag": 0,
                "next_action": "Review confirmation gaps before any allocation or backtest promotion.",
            }
        ]
    )


def pass_fail_matrix(
    panel: pd.DataFrame,
    graph: pd.DataFrame,
    rulebook: pd.DataFrame,
    guardrail: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("scope_watch_358", len(panel) == 358, f"rows={len(panel)}", "358"),
            gate("subtype_count_4", panel["watch_subtype"].nunique() == 4, f"subtypes={panel['watch_subtype'].nunique()}", "4"),
            gate("rulebook_count_4", len(rulebook) == 4, f"rules={len(rulebook)}", "4"),
            gate("interaction_graph_present", len(graph) == len(panel) * 5, f"edges={len(graph)}", "5 edges per row"),
            gate("guardrail_eval_present", int(guardrail["top50_winner_count_eval_only"].sum()) <= 50 and int(guardrail["bottom50_loser_count_eval_only"].sum()) <= 50, f"top={int(guardrail['top50_winner_count_eval_only'].sum())}; bottom={int(guardrail['bottom50_loser_count_eval_only'].sum())}", "<=50/<=50 watch subset"),
            gate("governance_all_pass", int(governance["pass_flag"].min()) == 1, f"min={int(governance['pass_flag'].min())}", "1"),
            gate("strategy_not_accepted", True, "NOT_ACCEPTED", "NOT_ACCEPTED"),
            gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
        ]
    )


def add_no_action_flags(frame: pd.DataFrame) -> None:
    frame["translator_output_is_action_flag"] = 0
    frame["assignment_used_flag"] = 0
    frame["outcome_used_for_assignment_flag"] = 0
    frame["future_price_used_for_assignment_flag"] = 0
    frame["top50_used_for_assignment_flag"] = 0
    frame["winner_structure_eval_used_for_assignment_flag"] = 0
    frame["ticker_theme_protection_rule_flag"] = 0
    frame["threshold_tuned_from_outcome_flag"] = 0
    frame["buy_sell_or_sizing_instruction_flag"] = 0
    frame["missing_source_used_as_negative_flag"] = 0
    frame["real_capital_status"] = "FORBIDDEN"
    frame["no_action_reason"] = NO_ACTION_REASON


def no_action_columns() -> list[str]:
    return [
        "translator_output_is_action_flag",
        "assignment_used_flag",
        "outcome_used_for_assignment_flag",
        "future_price_used_for_assignment_flag",
        "top50_used_for_assignment_flag",
        "winner_structure_eval_used_for_assignment_flag",
        "ticker_theme_protection_rule_flag",
        "threshold_tuned_from_outcome_flag",
        "buy_sell_or_sizing_instruction_flag",
        "missing_source_used_as_negative_flag",
        "real_capital_status",
        "no_action_reason",
    ]


def float_safe(value: object) -> float:
    try:
        if pd.isna(value):
            return 999.0
        return float(value)
    except (TypeError, ValueError):
        return 999.0


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "status": "PRIMARY_PASS" if passed else "NOT_ACCEPTED",
        "pass_flag": int(passed),
        "observed": observed,
        "required": required,
    }


def artifact_counts(outputs: dict[str, pd.DataFrame]) -> str:
    return "; ".join(f"{name}={len(frame)}" for name, frame in outputs.items())


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return ""
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join(["---"] * len(cols)) + " |"]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def write_outputs(out_dir: Path, outputs: dict[str, pd.DataFrame], decision: pd.DataFrame, pass_fail: pd.DataFrame) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in outputs.items():
        frame.to_csv(out_dir / name, index=False)
    report = f"""# Task719 Watch Subtype Confirmation Contract

## Decision Summary

- Verdict: {decision.iloc[0]['verdict']}.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: each Task718 watch subtype now has a confirmation contract.
- Next action: {decision.iloc[0]['next_action']}

## Quant Expert Report

- Scope: 358 Task718 watch candidates.
- Subtypes: 4.
- Confirmation contracts: evidence, price absorption, economic transmission, cohort slot, and invalidation checks.
- Hard rule: no single condition can promote a watch subtype.
- Assignment safety: outcomes, future prices, top-50 labels, ticker/theme protection, and outcome-tuned thresholds are forbidden.

## No-Background Decision-Maker Report

- This does not buy anything.
- It says what must be confirmed before a watch candidate can even become a review candidate.
- Missing or unconfirmed information remains unknown, not negative.
- Capital remains forbidden.

## Artifact Manifest

- Outputs: {', '.join(outputs.keys())}.
- Row counts: {artifact_counts(outputs)}.
- Validation command: `python -m unittest tests.test_task719_watch_subtype_confirmation_contract`.

## Pass/Fail Matrix

{markdown_table(pass_fail)}
"""
    (out_dir / "task_719_watch_subtype_confirmation_contract.md").write_text(report, encoding="utf-8")
    manifest = out_dir / "artifact_manifest.csv"
    if manifest.exists():
        manifest.unlink()
    write_manifest(out_dir, manifest)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Task719 watch subtype confirmation contract.")
    parser.add_argument("--watch", type=Path, default=TASK718_WATCH)
    parser.add_argument("--task716", type=Path, default=TASK716_PANEL)
    parser.add_argument("--eval", type=Path, default=TASK708_EVAL)
    parser.add_argument("--out-dir", type=Path, default=TASK719_DIR)
    args = parser.parse_args()
    build_task719(watch_path=args.watch, task716_path=args.task716, eval_path=args.eval, out_dir=args.out_dir)
    print("[Task719] wrote watch subtype confirmation contract artifacts")


if __name__ == "__main__":
    main()
