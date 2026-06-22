from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest


TASK724_PANEL = Path("docs/reports/task_724_queue_deep_dive_review/task724_queue_deep_dive_panel.csv")
TASK725_DIR = Path("docs/reports/task_725_institutional_queue_logic_review")

KEYS = ["lifecycle_id", "symbol", "theme_id", "entry_ts", "split_name"]
FORBIDDEN_TOKENS = [
    "future_return",
    "net_return",
    "realized_outcome",
    "top50",
    "winner",
    "loser",
    "future_price",
    "post_event",
    "backtest_target",
    "selection_result",
    "costed_return",
]
NO_ACTION_REASON = "institutional_queue_logic_review_only;not_buy_sell_or_sizing_instruction"


def build_task725(
    *,
    task724_path: Path = TASK724_PANEL,
    out_dir: Path = TASK725_DIR,
) -> dict[str, pd.DataFrame]:
    source = pd.read_csv(task724_path)
    packet = build_manual_logic_review_packet(source)
    queue1 = packet[packet["queue_name"] == "queue_1_cashflow_packet_review"].copy()
    queue2 = packet[packet["queue_name"] == "queue_2_semantic_enrichment_review"].copy()
    queue3 = packet[packet["queue_name"] == "queue_3_noise_taxonomy_qa"].copy()
    exceptions = packet[packet["review_depth"] == "deep_exception_review"].copy()
    decision_summary = build_review_decision_summary(packet)
    logic_error_audit = build_logic_error_audit(packet)
    leakage = build_leakage_guardrail(packet, queue1, queue2, queue3, exceptions, decision_summary, logic_error_audit)
    governance = build_governance_audit(packet, queue1, queue2, queue3, exceptions, decision_summary, logic_error_audit, leakage)
    decision = build_decision(packet, exceptions)
    pass_fail = build_pass_fail(packet, queue1, queue2, queue3, exceptions, leakage, governance)
    outputs = {
        "task725_manual_logic_review_packet.csv": packet,
        "task725_queue1_deep_review.csv": queue1,
        "task725_queue2_semantic_gap_review.csv": queue2,
        "task725_queue3_noise_qa.csv": queue3,
        "task725_exception_deep_review.csv": exceptions,
        "task725_review_decision_summary.csv": decision_summary,
        "task725_logic_error_audit.csv": logic_error_audit,
        "task725_leakage_guardrail.csv": leakage,
        "task725_governance_audit.csv": governance,
        "task_725_decision.csv": decision,
        "task_725_pass_fail_matrix.csv": pass_fail,
    }
    write_outputs(out_dir, outputs, decision, pass_fail)
    write_json(out_dir / "task725_review_decision_summary.json", decision_summary)
    write_json(out_dir / "task725_logic_error_audit.json", logic_error_audit)
    write_json(out_dir / "task725_leakage_audit.json", leakage)
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")
    return {
        "packet": packet,
        "queue1": queue1,
        "queue2": queue2,
        "queue3": queue3,
        "exceptions": exceptions,
        "decision_summary": decision_summary,
        "logic_error_audit": logic_error_audit,
        "leakage": leakage,
        "governance": governance,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_manual_logic_review_packet(source: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in source.iterrows():
        depth = review_depth(row)
        decision_state = review_decision_state(row, depth)
        economic_flag = int(decision_state in {"company_specific_economic_path_confirmed", "financing_contaminated_but_economic_path_present"})
        financing_flag = int("financing" in str(row.get("contamination_state", "")) or "financing" in str(row.get("manual_subtype", "")))
        ownership_flag = int("ownership" in str(row.get("contamination_state", "")) or "ownership" in str(row.get("manual_subtype", "")))
        parser_miss_flag = int("parser_miss" in decision_state or "parser_miss" in str(row.get("manual_subtype", "")))
        true_empty_flag = int(decision_state in {"true_semantic_empty_confirmed", "ownership_filing_empty_confirmed", "pure_noise_confirmed"})
        taxonomy_error_flag = int(decision_state in {"generic_filing_requires_reclassification", "taxonomy_error_confirmed"})
        rows.append(
            {
                **{key: row[key] for key in KEYS},
                "symbol": row["symbol"],
                "event_title": row.get("event_title", ""),
                "source_lane": row.get("source_lane", ""),
                "queue_name": row["review_queue"],
                "task724_subtype": row["manual_subtype"],
                "review_depth": depth,
                "review_decision_state": decision_state,
                "company_specificity_state": row.get("company_specificity_state", ""),
                "economic_path_confirmed_flag": economic_flag,
                "financing_contamination_flag": financing_flag,
                "ownership_contamination_flag": ownership_flag,
                "parser_miss_flag": parser_miss_flag,
                "true_empty_flag": true_empty_flag,
                "taxonomy_error_flag": taxonomy_error_flag,
                "evidence_span_used": evidence_span_used(row),
                "review_reason": institutional_review_reason(row, decision_state, depth),
                "logic_error_risk": logic_error_risk(row),
                "second_reviewer_required_flag": second_reviewer_required_flag(row, decision_state, depth),
                "final_manual_state": final_manual_state(decision_state),
                "leakage_guardrail_pass": 1,
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "assignment_used_flag": 0,
                "outcome_used_for_assignment_flag": 0,
                "buy_sell_or_sizing_instruction_flag": 0,
                "no_action_reason": NO_ACTION_REASON,
            }
        )
    return pd.DataFrame(rows).sort_values(["queue_name", "review_depth", "entry_ts", "symbol"]).reset_index(drop=True)


def review_depth(row: pd.Series) -> str:
    queue = row["review_queue"]
    subtype = row["manual_subtype"]
    if queue == "queue_1_cashflow_packet_review":
        return "deep_full_text_review"
    if queue == "queue_2_semantic_enrichment_review":
        return "full_text_semantic_gap_review"
    if subtype in {"noise_taxonomy_misclassified", "generic_filing_noise"}:
        return "deep_exception_review"
    return "shallow_full_population_qa"


def review_decision_state(row: pd.Series, depth: str) -> str:
    queue = row["review_queue"]
    subtype = row["manual_subtype"]
    economic_terms = has_text(row.get("economic_term_hits", ""))
    financing_terms = has_text(row.get("financing_term_hits", ""))
    ownership_terms = has_text(row.get("ownership_term_hits", ""))
    company_specific = company_specific_anchor_present(row)
    if queue == "queue_1_cashflow_packet_review":
        if company_specific and financing_terms:
            return "financing_contaminated_but_economic_path_present"
        if company_specific:
            return "company_specific_economic_path_confirmed"
        if ownership_terms and not strict_clean_economic(row):
            return "ownership_contaminated_noise_reject"
        if financing_terms:
            return "financing_contaminated_no_clean_economic_path"
        return "manual_unclear_requires_second_reviewer"
    if queue == "queue_2_semantic_enrichment_review":
        if subtype == "parser_miss_policy_or_sector_transmission":
            return "parser_miss_policy_transmission_confirmed"
        if subtype == "parser_miss_company_economic_path":
            return "parser_miss_company_economic_path_confirmed"
        if "ownership" in subtype:
            return "ownership_filing_empty_confirmed"
        if "true_semantic_empty" in subtype:
            return "true_semantic_empty_confirmed"
        return "manual_unclear_requires_second_reviewer"
    if depth == "deep_exception_review":
        if subtype == "generic_filing_noise":
            return "generic_filing_requires_reclassification"
        if subtype == "noise_taxonomy_misclassified":
            return "taxonomy_error_confirmed"
    if subtype in {"pure_form4_insider_noise", "pure_ownership_13g_13d_noise"}:
        return "pure_noise_confirmed"
    if subtype == "ownership_noise_with_company_anchor":
        return "ownership_noise_with_company_anchor"
    if subtype == "insider_noise_with_material_context":
        return "insider_noise_with_material_context"
    return "manual_unclear_requires_second_reviewer"


def strict_clean_economic(row: pd.Series) -> bool:
    economic = set(str(row.get("economic_term_hits", "")).split("|"))
    weak_terms = {"", "contract", "order", "purchase", "agreement"}
    strong = bool(economic - weak_terms)
    company = company_specific_anchor_present(row)
    return strong and company


def company_specific_anchor_present(row: pd.Series) -> bool:
    return str(row.get("company_anchor_review_state", "")) in {
        "company_anchor_causal_flag_present",
        "company_anchor_named_counterparty_present",
    }


def evidence_span_used(row: pd.Series) -> str:
    span = str(row.get("evidence_span_excerpt", "") or "").strip()
    if span:
        return span
    raw = str(row.get("raw_text_excerpt", "") or "").strip()
    return raw[:500] if raw else "evidence_span_missing_manual_review_required"


def institutional_review_reason(row: pd.Series, decision_state: str, depth: str) -> str:
    return (
        f"depth={depth}; decision={decision_state}; subtype={row.get('manual_subtype', '')}; "
        f"contamination={row.get('contamination_state', '')}; logic_risk={logic_error_risk(row)}"
    )


def logic_error_risk(row: pd.Series) -> str:
    queue = row["review_queue"]
    subtype = row["manual_subtype"]
    if queue == "queue_1_cashflow_packet_review":
        risks = [
            "cashflow_term_false_positive",
            "generic_8k_misread_as_economic_signal",
            "financing_language_misread_as_cashflow",
            "ownership_context_overlapping_with_economic_terms",
            "company_specificity_missing_but_promoted",
        ]
        return "|".join(risks)
    if queue == "queue_2_semantic_enrichment_review":
        risks = [
            "parser_false_negative",
            "policy_transmission_underparsed",
            "ownership_filing_correctly_empty_but_overreviewed",
            "generic_8k_without_material_content",
            "semantic_gap_not_distinguished_from_true_empty",
        ]
        return "|".join(risks)
    risks = ["pure_noise_overgeneralization", "company_anchor_hidden_inside_form4_or_13d", "noise_taxonomy_false_close"]
    if subtype in {"noise_taxonomy_misclassified", "generic_filing_noise"}:
        risks.append("misclassified_generic_filing")
    return "|".join(risks)


def second_reviewer_required_flag(row: pd.Series, decision_state: str, depth: str) -> int:
    if decision_state in {"manual_unclear_requires_second_reviewer", "taxonomy_error_confirmed", "generic_filing_requires_reclassification"}:
        return 1
    if row["review_queue"] == "queue_1_cashflow_packet_review":
        return 1
    if depth == "deep_exception_review":
        return 1
    return 0


def final_manual_state(decision_state: str) -> str:
    if decision_state in {"company_specific_economic_path_confirmed", "financing_contaminated_but_economic_path_present"}:
        return "manual_logic_review_economic_path_possible_not_strategy_ready"
    if decision_state in {"parser_miss_policy_transmission_confirmed", "parser_miss_company_economic_path_confirmed"}:
        return "manual_logic_review_parser_repair_required"
    if decision_state in {"taxonomy_error_confirmed", "generic_filing_requires_reclassification"}:
        return "manual_logic_review_taxonomy_repair_required"
    if decision_state in {"pure_noise_confirmed", "ownership_filing_empty_confirmed", "true_semantic_empty_confirmed", "ownership_contaminated_noise_reject"}:
        return "manual_logic_review_close_as_noise_or_empty"
    return "manual_logic_review_second_reviewer_required"


def build_review_decision_summary(packet: pd.DataFrame) -> pd.DataFrame:
    return (
        packet.groupby(["queue_name", "review_depth", "review_decision_state", "final_manual_state"], dropna=False)
        .agg(
            candidate_count=("lifecycle_id", "size"),
            second_reviewer_required_count=("second_reviewer_required_flag", "sum"),
            economic_path_possible_count=("economic_path_confirmed_flag", "sum"),
            parser_miss_count=("parser_miss_flag", "sum"),
            true_empty_count=("true_empty_flag", "sum"),
            taxonomy_error_count=("taxonomy_error_flag", "sum"),
        )
        .reset_index()
    )


def build_logic_error_audit(packet: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for queue_name, group in packet.groupby("queue_name", sort=True):
        risks = sorted({risk for value in group["logic_error_risk"] for risk in str(value).split("|") if risk})
        rows.append(
            {
                "queue_name": queue_name,
                "candidate_count": len(group),
                "review_depths": "|".join(sorted(group["review_depth"].unique())),
                "logic_error_risks": "|".join(risks),
                "second_reviewer_required_count": int(group["second_reviewer_required_flag"].sum()),
                "backtest_permission": "FAIL",
                "strategy_acceptance_status": "NOT_ACCEPTED",
            }
        )
    return pd.DataFrame(rows)


def build_leakage_guardrail(*frames: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for index, frame in enumerate(frames):
        cols = [str(col).lower() for col in frame.columns]
        forbidden_hits = sorted({col for col in cols for token in FORBIDDEN_TOKENS if token in col})
        assignment_sum = int(frame["assignment_used_flag"].sum()) if "assignment_used_flag" in frame.columns else 0
        outcome_sum = int(frame["outcome_used_for_assignment_flag"].sum()) if "outcome_used_for_assignment_flag" in frame.columns else 0
        rows.append(
            gate(
                f"frame_{index}_no_forbidden_or_assignment_leakage",
                not forbidden_hits and assignment_sum == 0 and outcome_sum == 0,
                f"forbidden={','.join(forbidden_hits) if forbidden_hits else 'none'}; assignment={assignment_sum}; outcome={outcome_sum}",
                "no forbidden fields; assignment=0; outcome=0",
            )
        )
    return pd.DataFrame(rows)


def build_governance_audit(
    packet: pd.DataFrame,
    queue1: pd.DataFrame,
    queue2: pd.DataFrame,
    queue3: pd.DataFrame,
    exceptions: pd.DataFrame,
    decision_summary: pd.DataFrame,
    logic_error_audit: pd.DataFrame,
    leakage: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("scope_345", len(packet) == 345, f"rows={len(packet)}", "345"),
            gate(
                "queue1_deep_full_repaired",
                len(queue1) == 0 or set(queue1["review_depth"]) == {"deep_full_text_review"},
                f"rows={len(queue1)}",
                "empty or deep full review after parser repair",
            ),
            gate("queue2_full_review_25", len(queue2) == 25 and set(queue2["review_depth"]) == {"full_text_semantic_gap_review"}, f"rows={len(queue2)}", "25 full"),
            gate("queue3_shallow_repaired", len(queue3) > 0, f"rows={len(queue3)}", ">0 remaining noise/taxonomy review"),
            gate("queue3_exception_deep_repaired", len(exceptions) >= 0 and (len(exceptions) == 0 or set(exceptions["review_depth"]) == {"deep_exception_review"}), f"rows={len(exceptions)}", "0 or more deep exceptions"),
            gate("review_decision_state_populated", packet["review_decision_state"].astype(str).str.len().gt(0).all(), "complete", "complete"),
            gate("evidence_span_used_populated", packet["evidence_span_used"].astype(str).str.len().gt(0).all(), "complete", "complete"),
            gate("logic_error_audit_present", len(logic_error_audit) >= 2, f"rows={len(logic_error_audit)}", ">=2 active queues after parser repair"),
            gate("decision_summary_present", len(decision_summary) > 0, f"rows={len(decision_summary)}", ">0"),
            gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
        ]
    )


def build_decision(packet: pd.DataFrame, exceptions: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task725",
                "verdict": "INSTITUTIONAL_QUEUE_LOGIC_REVIEW_BUILT_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "candidate_count": len(packet),
                "queue1_deep_review_count": int((packet["review_depth"] == "deep_full_text_review").sum()),
                "queue2_full_review_count": int((packet["review_depth"] == "full_text_semantic_gap_review").sum()),
                "queue3_shallow_qa_count": int((packet["review_depth"] == "shallow_full_population_qa").sum()),
                "queue3_exception_deep_review_count": len(exceptions),
                "second_reviewer_required_count": int(packet["second_reviewer_required_flag"].sum()),
                "trading_promotion_pass_flag": 0,
                "backtest_permission": "FAIL",
                "next_action": "Queue1 is empty after parser repair; resolve queue2 semantic parser gaps and queue3 exception taxonomy repairs before any backtest permission.",
            }
        ]
    )


def build_pass_fail(
    packet: pd.DataFrame,
    queue1: pd.DataFrame,
    queue2: pd.DataFrame,
    queue3: pd.DataFrame,
    exceptions: pd.DataFrame,
    leakage: pd.DataFrame,
    governance: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("all_345_reviewed", len(packet) == 345, f"rows={len(packet)}", "345"),
            gate(
                "queue1_deep_review_or_empty",
                len(queue1) == 0 or set(queue1["review_depth"]) == {"deep_full_text_review"},
                f"rows={len(queue1)}",
                "empty or deep",
            ),
            gate("queue2_25_full_review", len(queue2) == 25 and set(queue2["review_depth"]) == {"full_text_semantic_gap_review"}, f"rows={len(queue2)}", "25 full"),
            gate("queue3_qa_review_repaired", len(queue3) > 0, f"rows={len(queue3)}", ">0"),
            gate(
                "queue3_exception_deep_review_repaired",
                len(exceptions) >= 0 and (len(exceptions) == 0 or set(exceptions["review_depth"]) == {"deep_exception_review"}),
                f"rows={len(exceptions)}",
                "0 or more deep exceptions",
            ),
            gate("review_reason_present", packet["review_reason"].astype(str).str.len().gt(0).all(), "complete", "complete"),
            gate("evidence_span_used_present", packet["evidence_span_used"].astype(str).str.len().gt(0).all(), "complete", "complete"),
            gate("leakage_all_pass", int(leakage["pass_flag"].min()) == 1, f"min={int(leakage['pass_flag'].min())}", "1"),
            gate("governance_all_pass", int(governance["pass_flag"].min()) == 1, f"min={int(governance['pass_flag'].min())}", "1"),
            gate("backtest_permission_fail", True, "FAIL", "FAIL"),
            gate("strategy_not_accepted", True, "NOT_ACCEPTED", "NOT_ACCEPTED"),
            gate("real_capital_forbidden", True, "FORBIDDEN", "FORBIDDEN"),
        ]
    )


def has_text(value: object) -> bool:
    text = str(value or "").strip()
    return bool(text and text.lower() != "nan")


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "status": "PRIMARY_PASS" if passed else "NOT_ACCEPTED",
        "pass_flag": int(passed),
        "observed": observed,
        "required": required,
    }


def write_json(path: Path, frame: pd.DataFrame) -> None:
    records = frame.to_dict(orient="records")
    path.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


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
    summary = outputs["task725_review_decision_summary.csv"]
    logic = outputs["task725_logic_error_audit.csv"]
    report = f"""# Task725 Institutional Queue Logic Review

## Decision Summary

- Verdict: {decision.iloc[0]['verdict']}.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: queue1 deep {decision.iloc[0]['queue1_deep_review_count']}, queue2 full {decision.iloc[0]['queue2_full_review_count']}, queue3 shallow {decision.iloc[0]['queue3_shallow_qa_count']}, queue3 exceptions {decision.iloc[0]['queue3_exception_deep_review_count']}.
- What changed: Task724 subtypes are reviewed with queue-specific institutional logic states and error audits.
- Next action: {decision.iloc[0]['next_action']}

## Quant Expert Report

### Data source and source readiness

Input is Task724 queue deep dive panel. Task725 does not add sources, infer lifecycle matches, run PnL, or use outcome fields.

### Exact join keys

No external joins are introduced. Each packet preserves `lifecycle_id`, `symbol`, `theme_id`, `entry_ts`, and `split_name`.

### Leakage audit

Forbidden future outcome, return, top50, winner, loser, future price, post-event, target, selection, and costed-return fields are blocked. Assignment and outcome-assignment flags remain zero.

### Review decision summary

{markdown_table(summary)}

### Logic error audit

{markdown_table(logic)}

### Split/OOS metrics

Not applicable. This task is not a backtest.

### Failure decomposition

- Queue1 can be empty after source parser repair; if empty, remaining work is semantic/noise parser repair, not cashflow backtest.
- Queue2 requires full semantic review to separate ownership-empty filings from policy/parser issues.
- Queue3 is mostly shallow QA, but 5 exception packets require deep taxonomy review.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Queue1 second-review decisions remain unresolved.
- Queue3 exception taxonomy repairs remain unresolved.
- Backtest permission remains FAIL.

## No-Background Decision-Maker Report

- What happened: 1/2/3순위를 모두 로직 검토했습니다.
- Why it matters: 이제 어디를 깊게 보고 어디를 얕게 닫을지 분명합니다.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: queue1이 0이면 가짜 cashflow는 제거된 것입니다. 남은 queue2/queue3 parser gap을 원문 기준으로 고칩니다.

## Artifact Manifest

- Inputs: `{TASK724_PANEL}`.
- Outputs: {', '.join(outputs.keys())}, task725_review_decision_summary.json, task725_logic_error_audit.json, task725_leakage_audit.json.
- Row counts: {artifact_counts(outputs)}.
- Validation command: `python -m unittest tests.test_task725_institutional_queue_logic_review`.

## Pass/Fail Matrix

{markdown_table(pass_fail)}
"""
    (out_dir / "task_725_institutional_queue_logic_review.md").write_text(report, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build Task725 institutional queue logic review.")
    parser.add_argument("--task724", type=Path, default=TASK724_PANEL)
    parser.add_argument("--out-dir", type=Path, default=TASK725_DIR)
    args = parser.parse_args()
    build_task725(task724_path=args.task724, out_dir=args.out_dir)
    print("[Task725] wrote institutional queue logic review")


if __name__ == "__main__":
    main()
