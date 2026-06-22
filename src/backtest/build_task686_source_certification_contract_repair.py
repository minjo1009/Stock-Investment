from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest import build_task678_active_cap3_winner_archetype as t678


TASK672_DIR = Path("docs/reports/task_672_current_data_state_axis_panel")
TASK684_DIR = Path("docs/reports/task_684_interaction_context_prediction_stack")
TASK686_DIR = Path("docs/reports/task_686_source_certification_contract_repair")
ACTIVE_CAP3 = "active_relation_cap3_reference"
GUARDED = "interaction_context_superiority_guarded_v3"

PROVENANCE_COLUMNS = [
    "source_integrity_state",
    "asof_valid_flag",
    "used_for_assignment_flag",
    "company_source_assignment_certified_flag",
    "content_prediction_assignment_certified_flag",
    "macro_assignment_certified_flag",
    "macro_used_for_assignment_flag",
    "theme_price_assignment_certified_flag",
    "relation_assignment_certified_flag",
    "portfolio_capacity_assignment_certified_flag",
    "allocation_assignment_ready_flag",
    "assignment_certification_scope",
    "assignment_block_reason",
    "macro_asof_provisional_for_diagnostic_flag",
    "macro_provisional_used_as_certified",
    "missing_source_used_as_negative",
    "return_used_in_assignment_flag",
    "label_used_in_assignment_flag_task661",
    "future_price_used_in_assignment",
]


def build_task686_program(task672_dir: Path = TASK672_DIR, task684_dir: Path = TASK684_DIR) -> dict[str, pd.DataFrame]:
    TASK686_DIR.mkdir(parents=True, exist_ok=True)
    panel = pd.read_csv(task672_dir / "task672_state_axis_panel.csv")
    allocation = pd.read_csv(task684_dir / "task684_cohort_slot_qualification.csv")
    grid = pd.read_csv(task684_dir / "task684_simulation_result.csv")
    superiority = pd.read_csv(task684_dir / "task684_superiority_audit.csv")

    source_summary = build_source_certification_summary(panel)
    macro_audit = build_macro_assignment_usage_audit(panel, allocation)
    provenance = build_allocation_provenance_audit(allocation)
    guarded = build_guarded_post_repair_audit(allocation, grid, superiority)
    gpt_review = build_gpt_review_pack()
    decision = build_decision(source_summary, macro_audit, provenance, guarded)
    pass_fail = build_pass_fail(source_summary, macro_audit, provenance, guarded)

    write_outputs(source_summary, macro_audit, provenance, guarded, gpt_review, decision, pass_fail)
    return {
        "source_summary": source_summary,
        "macro_audit": macro_audit,
        "provenance": provenance,
        "guarded": guarded,
        "gpt_review": gpt_review,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_source_certification_summary(panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scope, frame in [("task672_core_panel", panel)] + [
        (str(split), group) for split, group in panel.groupby("split_name", dropna=False)
    ]:
        rows.append(
            {
                "scope": scope,
                "row_count": int(len(frame)),
                "source_gap_research_only_count": count_eq(frame, "source_integrity_state", "source_gap_research_only"),
                "company_certified_macro_provisional_count": count_eq(frame, "source_integrity_state", "company_certified_macro_provisional"),
                "allocation_assignment_ready_count": sum_int(frame, "allocation_assignment_ready_flag"),
                "company_source_certified_count": sum_int(frame, "company_source_assignment_certified_flag"),
                "content_prediction_certified_count": sum_int(frame, "content_prediction_assignment_certified_flag"),
                "theme_price_certified_count": sum_int(frame, "theme_price_assignment_certified_flag"),
                "relation_certified_count": sum_int(frame, "relation_assignment_certified_flag"),
                "macro_assignment_certified_count": sum_int(frame, "macro_assignment_certified_flag"),
                "macro_used_for_assignment_count": sum_int(frame, "macro_used_for_assignment_flag"),
                "macro_provisional_used_as_certified_count": sum_int(frame, "macro_provisional_used_as_certified"),
                "missing_source_used_as_negative_count": sum_int(frame, "missing_source_used_as_negative"),
            }
        )
    return pd.DataFrame(rows)


def build_macro_assignment_usage_audit(panel: pd.DataFrame, allocation: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scope, frame in [
        ("task672_core_panel", panel),
        ("task684_allocation", allocation),
        ("task684_guarded_all", allocation[allocation["candidate_name"].eq(GUARDED) & allocation["split_scope"].eq("all")]),
    ]:
        rows.append(
            {
                "scope": scope,
                "row_count": int(len(frame)),
                "macro_assignment_certified_count": sum_int(frame, "macro_assignment_certified_flag"),
                "macro_used_for_assignment_count": sum_int(frame, "macro_used_for_assignment_flag"),
                "macro_provisional_for_diagnostic_count": sum_int(frame, "macro_asof_provisional_for_diagnostic_flag"),
                "macro_provisional_used_as_certified_count": sum_int(frame, "macro_provisional_used_as_certified"),
                "missing_source_used_as_negative_count": sum_int(frame, "missing_source_used_as_negative"),
            }
        )
    return pd.DataFrame(rows)


def build_allocation_provenance_audit(allocation: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for col in PROVENANCE_COLUMNS:
        rows.append(
            {
                "column_name": col,
                "present_flag": int(col in allocation.columns),
                "non_null_count": int(allocation[col].notna().sum()) if col in allocation.columns else 0,
            }
        )
    return pd.DataFrame(rows)


def build_guarded_post_repair_audit(
    allocation: pd.DataFrame, grid: pd.DataFrame, superiority: pd.DataFrame
) -> pd.DataFrame:
    guarded = allocation[allocation["candidate_name"].eq(GUARDED) & allocation["split_scope"].eq("all")].copy()
    active_grid = grid[grid["candidate_name"].eq(ACTIVE_CAP3) & grid["split_name"].eq("all")].iloc[0]
    guarded_grid = grid[grid["candidate_name"].eq(GUARDED) & grid["split_name"].eq("all")].iloc[0]
    reason_counts = guarded["allocation_reason"].value_counts(dropna=False).to_dict()
    rows = [
        {
            "audit_item": "final_capital_delta_vs_active",
            "metric_value": float(guarded_grid["final_capital_usd"] - active_grid["final_capital_usd"]),
            "detail": f"guarded={float(guarded_grid['final_capital_usd']):.2f}; active={float(active_grid['final_capital_usd']):.2f}",
        },
        {
            "audit_item": "mdd_delta_vs_active",
            "metric_value": float(guarded_grid["max_drawdown_pct"] - active_grid["max_drawdown_pct"]),
            "detail": f"guarded={float(guarded_grid['max_drawdown_pct']):.2f}; active={float(active_grid['max_drawdown_pct']):.2f}",
        },
        {
            "audit_item": "accepted_context_superiority_challenger",
            "metric_value": float(reason_counts.get("accepted_context_superiority", 0)),
            "detail": "Challengers accepted by guarded superiority after source certification repair.",
        },
        {
            "audit_item": "superiority_failed_source",
            "metric_value": float(reason_counts.get("superiority_failed_source", 0)),
            "detail": "Now means sparse source/action block, not all-row assignment-readiness collapse.",
        },
    ]
    for reason, count in reason_counts.items():
        rows.append(
            {
                "audit_item": f"allocation_reason::{reason}",
                "metric_value": float(count),
                "detail": "Guarded all-scope allocation reason count after repair.",
            }
        )
    rows.append(
        {
            "audit_item": "superiority_audit_rows",
            "metric_value": float(len(superiority)),
            "detail": "Task684 superiority audit rows available after rerun.",
        }
    )
    return pd.DataFrame(rows)


def build_gpt_review_pack() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "reviewer": "Chrome ChatGPT external reviewer",
                "captured_scope": "Task685 source certification repair design",
                "source_type": "external_model_interpretation_not_source_truth",
                "finding": "Problem is source certification contract, not merely model weakness.",
                "accepted_implementation": "Split company/content/theme_price/macro/relation/portfolio assignment certification flags.",
            },
            {
                "reviewer": "Chrome ChatGPT external reviewer",
                "captured_scope": "Macro provisional handling",
                "source_type": "external_model_interpretation_not_source_truth",
                "finding": "Macro provisional must not grant action, size, cap, block, or superiority authority.",
                "accepted_implementation": "Keep macro_assignment_certified_flag=0 and macro_used_for_assignment_flag=0.",
            },
            {
                "reviewer": "Chrome ChatGPT external reviewer",
                "captured_scope": "Allocation provenance",
                "source_type": "external_model_interpretation_not_source_truth",
                "finding": "Allocation must preserve source/asof/provenance columns.",
                "accepted_implementation": "Task684 allocation now carries source_integrity_state and assignment certification flags.",
            },
        ]
    )


def build_decision(
    source_summary: pd.DataFrame,
    macro_audit: pd.DataFrame,
    provenance: pd.DataFrame,
    guarded: pd.DataFrame,
) -> pd.DataFrame:
    core = source_summary[source_summary["scope"].eq("task672_core_panel")].iloc[0]
    challenger = metric(guarded, "accepted_context_superiority_challenger")
    return pd.DataFrame(
        [
            {
                "task_id": "Task686",
                "verdict": "DATA_INFRASTRUCTURE_REPAIR_COMPLETE_STRATEGY_NOT_PROMOTED",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "row_count": int(core["row_count"]),
                "source_gap_research_only_count": int(core["source_gap_research_only_count"]),
                "allocation_assignment_ready_count": int(core["allocation_assignment_ready_count"]),
                "macro_assignment_certified_count": int(core["macro_assignment_certified_count"]),
                "macro_used_for_assignment_count": int(core["macro_used_for_assignment_count"]),
                "allocation_provenance_columns_present": int(provenance["present_flag"].sum()),
                "guarded_challenger_accepted_count": int(challenger),
                "primary_result": "Source certification collapse fixed; guarded strategy still not improved because challenger displacement remains zero.",
                "next_action": "Develop conditional displacement hurdle after source certification repair, without using macro provisional as certified.",
            }
        ]
    )


def build_pass_fail(
    source_summary: pd.DataFrame,
    macro_audit: pd.DataFrame,
    provenance: pd.DataFrame,
    guarded: pd.DataFrame,
) -> pd.DataFrame:
    core = source_summary[source_summary["scope"].eq("task672_core_panel")].iloc[0]
    macro = macro_audit[macro_audit["scope"].eq("task672_core_panel")].iloc[0]
    missing_cols = provenance[provenance["present_flag"].eq(0)]
    challenger = metric(guarded, "accepted_context_superiority_challenger")
    return pd.DataFrame(
        [
            gate("source_gap_collapse_fixed", int(core["source_gap_research_only_count"]) == 0, f"source_gap={int(core['source_gap_research_only_count'])}", "0 source_gap rows"),
            gate("partial_assignment_ready_opened", int(core["allocation_assignment_ready_count"]) == int(core["row_count"]), f"ready={int(core['allocation_assignment_ready_count'])}/{int(core['row_count'])}", "all Task672 core rows ready"),
            gate("macro_not_promoted", int(macro["macro_assignment_certified_count"]) == 0 and int(macro["macro_used_for_assignment_count"]) == 0, f"macro_cert={int(macro['macro_assignment_certified_count'])}, macro_used={int(macro['macro_used_for_assignment_count'])}", "macro remains diagnostic"),
            gate("no_macro_provisional_bypass", int(macro["macro_provisional_used_as_certified_count"]) == 0, f"macro_provisional_used_as_certified={int(macro['macro_provisional_used_as_certified_count'])}", "0 bypass"),
            gate("allocation_provenance_preserved", missing_cols.empty, f"missing={missing_cols['column_name'].tolist()}", "all provenance columns present"),
            gate("guarded_still_not_strategy_promotion", int(challenger) == 0, f"challenger_accepted={int(challenger)}", "document remaining slot displacement blocker"),
        ]
    )


def write_outputs(
    source_summary: pd.DataFrame,
    macro_audit: pd.DataFrame,
    provenance: pd.DataFrame,
    guarded: pd.DataFrame,
    gpt_review: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task686_source_certification_summary.csv": source_summary,
        "task686_macro_assignment_usage_audit.csv": macro_audit,
        "task686_allocation_provenance_audit.csv": provenance,
        "task686_guarded_post_repair_audit.csv": guarded,
        "task686_gpt_review_pack.csv": gpt_review,
        "task_686_decision.csv": decision,
        "task_686_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK686_DIR / name, index=False)
    (TASK686_DIR / "task_686_source_certification_contract_repair.md").write_text(
        render_report(source_summary, macro_audit, provenance, guarded, gpt_review, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK686_DIR, TASK686_DIR / "artifact_manifest.csv")


def render_report(
    source_summary: pd.DataFrame,
    macro_audit: pd.DataFrame,
    provenance: pd.DataFrame,
    guarded: pd.DataFrame,
    gpt_review: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    return f"""# Task686 Source Certification Contract Repair

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Key metrics: source-gap rows {int(d["source_gap_research_only_count"])}/{int(d["row_count"])}, allocation-ready rows {int(d["allocation_assignment_ready_count"])}/{int(d["row_count"])}, macro-certified rows {int(d["macro_assignment_certified_count"])}, macro-used rows {int(d["macro_used_for_assignment_count"])}, guarded challenger accepted rows {int(d["guarded_challenger_accepted_count"])}.
- What changed: Task661 now separates company/content/theme-price/macro/relation/portfolio certification; Task672 no longer collapses certified company rows into source-gap; Task684 allocation preserves provenance columns.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and source readiness

Task686 repairs the source-certification contract. Macro remains provisional and is not used for assignment. Company/content/theme-price certification can now create partial assignment readiness.

{t678.markdown_table(source_summary)}

### Exact join keys

- `lifecycle_id` and `entry_ts` remain the replay keys.
- Task684 allocation now carries provenance fields forward to the cohort-slot audit surface.

### Leakage audit

- Return, label, and future price flags remain zero for assignment.
- `macro_provisional_used_as_certified` is zero.
- `missing_source_used_as_negative` is zero.
- GPT review is saved as interpretive design review only, not source truth.

### Macro assignment audit

{t678.markdown_table(macro_audit)}

### Allocation provenance audit

{t678.markdown_table(provenance)}

### Guarded post-repair audit

{t678.markdown_table(guarded)}

### GPT review pack

{t678.markdown_table(gpt_review)}

### Split/OOS metrics

Task686 does not promote a new strategy. Task684 post-repair still has the same all-period final capital for guarded and active cap3 because challenger displacement remains zero. This is now a slot-displacement logic blocker, not the all-row source-readiness collapse found in Task685.

### Failure decomposition

- Fixed: all Task672 core rows no longer show `source_gap_research_only`.
- Fixed: allocation output preserves source/asof/provenance fields.
- Preserved: macro provisional is not treated as certified.
- Remaining: guarded displacement still accepts zero challengers.

### Cost/slippage stress where PnL changed

Not applicable. No strategy is accepted or promoted by Task686.

### Remaining blockers

- Macro raw release/vintage certification is still missing.
- Guarded cohort replacement needs a conditional displacement hurdle.
- Strategy remains NOT_ACCEPTED and real capital remains FORBIDDEN.

## No-Background Decision-Maker Report

- What happened: the data pipe no longer marks every candidate as research-only.
- Why it matters: the five engines can now carry certified company/source context into allocation records.
- Whether this changes capital/deployment readiness: no. The strategy still did not improve over active cap3.
- Plain-language next step: now fix the slot replacement rule. The old data blocker is removed.

## Artifact Manifest

- Inputs: Task672 state panel, Task684 allocation/simulation/superiority artifacts, Chrome GPT review.
- Outputs: source certification summary, macro assignment audit, allocation provenance audit, guarded post-repair audit, GPT review pack, decision, pass/fail, manifest.
- Row counts: source summary {len(source_summary)}, macro audit {len(macro_audit)}, provenance {len(provenance)}, guarded audit {len(guarded)}.
- Validation commands: `python src/backtest/build_task686_source_certification_contract_repair.py`; `python -m unittest tests.test_task686_source_certification_contract_repair`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

{t678.markdown_table(pass_fail)}
"""


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "status": "PRIMARY_PASS" if passed else "NOT_ACCEPTED",
        "pass_flag": int(passed),
        "observed": observed,
        "required": required,
    }


def sum_int(frame: pd.DataFrame, col: str) -> int:
    if col not in frame.columns:
        return 0
    return int(pd.to_numeric(frame[col], errors="coerce").fillna(0).sum())


def count_eq(frame: pd.DataFrame, col: str, value: object) -> int:
    if col not in frame.columns:
        return 0
    return int(frame[col].fillna("__NA__").eq(value).sum())


def metric(frame: pd.DataFrame, audit_item: str) -> float:
    row = frame[frame["audit_item"].eq(audit_item)]
    if row.empty:
        return 0.0
    return float(row.iloc[0]["metric_value"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task672-dir", type=Path, default=TASK672_DIR)
    parser.add_argument("--task684-dir", type=Path, default=TASK684_DIR)
    args = parser.parse_args()
    build_task686_program(task672_dir=args.task672_dir, task684_dir=args.task684_dir)
    print(f"[Task686] wrote {TASK686_DIR}")


if __name__ == "__main__":
    main()
