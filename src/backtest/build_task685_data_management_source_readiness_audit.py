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


TASK684_DIR = Path("docs/reports/task_684_interaction_context_prediction_stack")
TASK685_DIR = Path("docs/reports/task_685_data_management_source_readiness_audit")
ACTIVE_CAP3 = "active_relation_cap3_reference"
GUARDED = "interaction_context_superiority_guarded_v3"


def build_task685_program(task684_dir: Path = TASK684_DIR) -> dict[str, pd.DataFrame]:
    TASK685_DIR.mkdir(parents=True, exist_ok=True)
    stack = pd.read_csv(task684_dir / "task684_interaction_stack_panel.csv")
    accepted = pd.read_csv(task684_dir / "task684_accepted_trades.csv")
    allocation = pd.read_csv(task684_dir / "task684_cohort_slot_qualification.csv")
    grid = pd.read_csv(task684_dir / "task684_simulation_result.csv")

    active = accepted[
        accepted["candidate_name"].eq(ACTIVE_CAP3) & accepted["split_scope"].eq("all")
    ].copy()

    summary = build_source_readiness_summary(stack, active, allocation)
    flags = build_flag_distribution(stack, active, allocation)
    active_audit = build_active_cap3_source_audit(active)
    root_cause = build_pipeline_root_cause()
    guarded_identity = build_guarded_identity_audit(allocation, grid)
    split_readiness = build_engine_input_readiness_by_split(stack)
    decision = build_decision(summary, guarded_identity)
    pass_fail = build_pass_fail(summary, guarded_identity)

    write_outputs(
        summary,
        flags,
        active_audit,
        root_cause,
        guarded_identity,
        split_readiness,
        decision,
        pass_fail,
    )
    return {
        "summary": summary,
        "flags": flags,
        "active_audit": active_audit,
        "root_cause": root_cause,
        "guarded_identity": guarded_identity,
        "split_readiness": split_readiness,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_source_readiness_summary(
    stack: pd.DataFrame, active: pd.DataFrame, allocation: pd.DataFrame
) -> pd.DataFrame:
    rows = []
    for scope, frame in [
        ("universe_stack", stack),
        ("active_cap3_accepted", active),
        ("all_allocation_rows", allocation),
    ]:
        total = len(frame)
        rows.append(
            {
                "scope": scope,
                "row_count": total,
                "source_integrity_field_present_flag": int("source_integrity_state" in frame.columns),
                "assignment_flag_fields_present_flag": int(
                    "asof_valid_flag" in frame.columns and "used_for_assignment_flag" in frame.columns
                ),
                "source_gap_research_only_count": count_eq(frame, "source_integrity_state", "source_gap_research_only"),
                "asof_valid_count": sum_int(frame, "asof_valid_flag"),
                "used_for_assignment_count": sum_int(frame, "used_for_assignment_flag"),
                "assignment_ready_count": assignment_ready_count(frame),
                "macro_series_available_median": median_num(frame, "macro_series_available_count"),
                "macro_release_timestamp_repaired_count": sum_int(frame, "macro_release_timestamp_repaired_flag"),
                "macro_asof_provisional_count": sum_int(frame, "macro_asof_provisional_for_diagnostic_flag"),
                "macro_asof_certified_count": sum_int(frame, "macro_asof_certified_for_assignment_flag"),
                "linked_event_nonzero_count": count_gt(frame, "linked_event_count", 0),
                "source_text_certified_nonzero_count": count_gt(frame, "source_text_certified_event_count", 0),
                "content_prediction_certified_nonzero_count": count_gt(frame, "content_prediction_certified_event_count", 0),
            }
        )
    return pd.DataFrame(rows)


def build_flag_distribution(stack: pd.DataFrame, active: pd.DataFrame, allocation: pd.DataFrame) -> pd.DataFrame:
    rows = []
    fields = [
        "source_integrity_state",
        "asof_valid_flag",
        "used_for_assignment_flag",
        "macro_release_timestamp_repaired_flag",
        "macro_asof_provisional_for_diagnostic_flag",
        "macro_asof_certified_for_assignment_flag",
        "source_action_block_flag",
        "sparse_action_block_flag",
        "microstructure_state",
        "microstructure_used_in_assignment",
    ]
    for scope, frame in [
        ("universe_stack", stack),
        ("active_cap3_accepted", active),
        ("guarded_allocation_all", allocation[
            allocation["candidate_name"].eq(GUARDED) & allocation["split_scope"].eq("all")
        ]),
    ]:
        total = max(len(frame), 1)
        for field in fields:
            if field not in frame.columns:
                rows.append(
                    {
                        "scope": scope,
                        "field_name": field,
                        "field_value": "__MISSING_COLUMN__",
                        "row_count": 0,
                        "share_pct": 0.0,
                    }
                )
                continue
            counts = frame[field].fillna("__NA__").value_counts(dropna=False)
            for value, count in counts.items():
                rows.append(
                    {
                        "scope": scope,
                        "field_name": field,
                        "field_value": value,
                        "row_count": int(count),
                        "share_pct": float(count / total * 100.0),
                    }
                )
    return pd.DataFrame(rows)


def build_active_cap3_source_audit(active: pd.DataFrame) -> pd.DataFrame:
    keep = [
        "lifecycle_id",
        "symbol",
        "entry_ts",
        "split_name",
        "theme_id",
        "source_integrity_state",
        "asof_valid_flag",
        "used_for_assignment_flag",
        "macro_series_available_count",
        "macro_release_timestamp_repaired_flag",
        "macro_asof_provisional_for_diagnostic_flag",
        "linked_event_count",
        "source_text_certified_event_count",
        "content_prediction_certified_event_count",
        "sparse_action_block_flag",
        "microstructure_state",
        "net_return_costed",
    ]
    present = [col for col in keep if col in active.columns]
    out = active[present].copy()
    out["assignment_ready_flag"] = (
        pd.to_numeric(out.get("asof_valid_flag", 0), errors="coerce").fillna(0).eq(1)
        & pd.to_numeric(out.get("used_for_assignment_flag", 0), errors="coerce").fillna(0).eq(1)
    ).astype(int)
    return out


def build_pipeline_root_cause() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "issue_id": "used_for_assignment_flag_hardcoded_zero",
                "file_path": "src/backtest/build_task661_mechanism_relation_engine.py",
                "line_reference": "213-214",
                "observed_code_contract": "asof_valid_flag is copied from macro_asof_provisional_for_diagnostic_flag; used_for_assignment_flag is hard-coded to 0.",
                "observed_effect": "Every downstream relation/context row becomes diagnostic-only for assignment readiness.",
                "required_fix_direction": "Create a row-level source certification contract before setting used_for_assignment_flag=1.",
                "trading_status": "FORBIDDEN_UNTIL_FIXED_AND_VALIDATED",
            },
            {
                "issue_id": "macro_asof_provisional_all_available_rows",
                "file_path": "src/backtest/build_task655_macro_asof_release_repair.py",
                "line_reference": "251-257",
                "observed_code_contract": "macro_release_timestamp_repaired_flag and macro_asof_provisional_for_diagnostic_flag are set from macro_series_available_count > 0.",
                "observed_effect": "Macro context exists, but it is repaired/provisional rather than raw release-asof certified.",
                "required_fix_direction": "Separate raw release timestamp, vintage timestamp, repair provenance, and assignment certification.",
                "trading_status": "FORBIDDEN_UNTIL_FIXED_AND_VALIDATED",
            },
            {
                "issue_id": "source_integrity_requires_assignment_flag",
                "file_path": "src/backtest/build_task672_current_data_state_axis_panel.py",
                "line_reference": "135-139",
                "observed_code_contract": "source_integrity_state becomes source_gap_research_only unless both asof_valid_flag and used_for_assignment_flag are 1.",
                "observed_effect": "Rows with data still get demoted when assignment certification is missing.",
                "required_fix_direction": "Keep this gate strict, but fix upstream certification instead of bypassing it.",
                "trading_status": "GATE_IS_CORRECT_UPSTREAM_IS_NOT_READY",
            },
            {
                "issue_id": "guarded_candidate_preserves_baseline_by_construction",
                "file_path": "src/backtest/build_task684_interaction_context_prediction_stack.py",
                "line_reference": "565-654",
                "observed_code_contract": "Guarded selection preserves active baseline first and admits challengers only after strict superiority checks.",
                "observed_effect": "With source readiness weak, challengers cannot earn replacement rights, so guarded result can equal active cap3.",
                "required_fix_direction": "After source readiness is fixed, retest challenger admission and replacement reasons by same entry_ts cohort.",
                "trading_status": "RESEARCH_ONLY",
            },
        ]
    )


def build_guarded_identity_audit(allocation: pd.DataFrame, grid: pd.DataFrame) -> pd.DataFrame:
    guarded = allocation[
        allocation["candidate_name"].eq(GUARDED) & allocation["split_scope"].eq("all")
    ].copy()
    active = grid[grid["candidate_name"].eq(ACTIVE_CAP3) & grid["split_name"].eq("all")].iloc[0]
    guarded_grid = grid[grid["candidate_name"].eq(GUARDED) & grid["split_name"].eq("all")].iloc[0]

    reason_counts = guarded["allocation_reason"].fillna("__NA__").value_counts().to_dict()
    accepted = guarded[pd.to_numeric(guarded["accepted_flag"], errors="coerce").fillna(0).eq(1)]
    baseline_accepted = int(
        (
            accepted["allocation_reason"].eq("accepted_baseline_context_preserved")
            & pd.to_numeric(accepted.get("active_cap3_baseline_flag", 0), errors="coerce").fillna(0).eq(1)
        ).sum()
    )
    challenger_accepted = int(accepted["allocation_reason"].eq("accepted_context_superiority").sum())

    rows = [
        {
            "audit_item": "final_capital_identity_check",
            "metric_value": float(guarded_grid["final_capital_usd"] - active["final_capital_usd"]),
            "detail": f"guarded={float(guarded_grid['final_capital_usd']):.2f}; active={float(active['final_capital_usd']):.2f}",
        },
        {
            "audit_item": "mdd_identity_check",
            "metric_value": float(guarded_grid["max_drawdown_pct"] - active["max_drawdown_pct"]),
            "detail": f"guarded={float(guarded_grid['max_drawdown_pct']):.2f}; active={float(active['max_drawdown_pct']):.2f}",
        },
        {
            "audit_item": "accepted_baseline_context_preserved",
            "metric_value": baseline_accepted,
            "detail": "Accepted guarded trades that are preserved active cap3 baseline rows.",
        },
        {
            "audit_item": "accepted_context_superiority_challenger",
            "metric_value": challenger_accepted,
            "detail": "Challenger rows admitted by superiority logic.",
        },
    ]
    for reason, count in reason_counts.items():
        rows.append(
            {
                "audit_item": f"allocation_reason::{reason}",
                "metric_value": int(count),
                "detail": "Guarded all-scope allocation reason count.",
            }
        )
    return pd.DataFrame(rows)


def build_engine_input_readiness_by_split(stack: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for split, group in stack.groupby("split_name", dropna=False):
        rows.append(
            {
                "split_name": split,
                "row_count": int(len(group)),
                "source_gap_research_only_count": count_eq(group, "source_integrity_state", "source_gap_research_only"),
                "assignment_ready_count": assignment_ready_count(group),
                "asof_valid_count": sum_int(group, "asof_valid_flag"),
                "used_for_assignment_count": sum_int(group, "used_for_assignment_flag"),
                "macro_series_available_median": median_num(group, "macro_series_available_count"),
                "macro_provisional_count": sum_int(group, "macro_asof_provisional_for_diagnostic_flag"),
                "macro_repaired_count": sum_int(group, "macro_release_timestamp_repaired_flag"),
                "linked_event_nonzero_count": count_gt(group, "linked_event_count", 0),
                "source_text_certified_nonzero_count": count_gt(group, "source_text_certified_event_count", 0),
                "content_prediction_certified_nonzero_count": count_gt(group, "content_prediction_certified_event_count", 0),
            }
        )
    return pd.DataFrame(rows).sort_values("split_name").reset_index(drop=True)


def build_decision(summary: pd.DataFrame, guarded_identity: pd.DataFrame) -> pd.DataFrame:
    universe = summary[summary["scope"].eq("universe_stack")].iloc[0]
    active = summary[summary["scope"].eq("active_cap3_accepted")].iloc[0]
    challenger = metric(guarded_identity, "accepted_context_superiority_challenger")
    return pd.DataFrame(
        [
            {
                "task_id": "Task685",
                "verdict": "DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "universe_rows": int(universe["row_count"]),
                "universe_source_gap_rows": int(universe["source_gap_research_only_count"]),
                "universe_assignment_ready_rows": int(universe["assignment_ready_count"]),
                "active_cap3_rows": int(active["row_count"]),
                "active_cap3_assignment_ready_rows": int(active["assignment_ready_count"]),
                "guarded_challenger_accepted_rows": int(challenger),
                "primary_blocker": "Source readiness certification is zero; guarded challenger admission is zero.",
                "next_action": "Fix data/source certification contract before further relation-engine trading-rule promotion.",
            }
        ]
    )


def build_pass_fail(summary: pd.DataFrame, guarded_identity: pd.DataFrame) -> pd.DataFrame:
    universe = summary[summary["scope"].eq("universe_stack")].iloc[0]
    active = summary[summary["scope"].eq("active_cap3_accepted")].iloc[0]
    source_gap_all = int(universe["source_gap_research_only_count"]) == int(universe["row_count"])
    assignment_zero = int(universe["assignment_ready_count"]) == 0
    active_assignment_zero = int(active["assignment_ready_count"]) == 0
    challenger_zero = int(metric(guarded_identity, "accepted_context_superiority_challenger")) == 0
    return pd.DataFrame(
        [
            gate("source_gap_audit_complete", source_gap_all, f"source_gap={int(universe['source_gap_research_only_count'])}/{int(universe['row_count'])}", "identify source gap scope"),
            gate("assignment_ready_zero_detected", assignment_zero, f"assignment_ready={int(universe['assignment_ready_count'])}", "0 ready rows"),
            gate("active_cap3_not_assignment_ready", active_assignment_zero, f"active_ready={int(active['assignment_ready_count'])}", "active cap3 also not ready"),
            gate("guarded_identity_explained", challenger_zero, "accepted_context_superiority_challenger=0", "no challenger admitted"),
            gate("no_strategy_promotion", True, "Task685 audit only", "NOT_ACCEPTED/FORBIDDEN"),
        ]
    )


def write_outputs(
    summary: pd.DataFrame,
    flags: pd.DataFrame,
    active_audit: pd.DataFrame,
    root_cause: pd.DataFrame,
    guarded_identity: pd.DataFrame,
    split_readiness: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task685_source_readiness_summary.csv": summary,
        "task685_flag_distribution.csv": flags,
        "task685_active_cap3_source_audit.csv": active_audit,
        "task685_pipeline_root_cause.csv": root_cause,
        "task685_guarded_identity_audit.csv": guarded_identity,
        "task685_engine_input_readiness_by_split.csv": split_readiness,
        "task_685_decision.csv": decision,
        "task_685_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK685_DIR / name, index=False)
    (TASK685_DIR / "task_685_data_management_source_readiness_audit.md").write_text(
        render_report(summary, root_cause, guarded_identity, split_readiness, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK685_DIR, TASK685_DIR / "artifact_manifest.csv")


def render_report(
    summary: pd.DataFrame,
    root_cause: pd.DataFrame,
    guarded_identity: pd.DataFrame,
    split_readiness: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    return f"""# Task685 Data Management Source Readiness Audit

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Key metrics: universe source-gap rows {int(d["universe_source_gap_rows"])}/{int(d["universe_rows"])}, universe assignment-ready rows {int(d["universe_assignment_ready_rows"])}, active cap3 assignment-ready rows {int(d["active_cap3_assignment_ready_rows"])}/{int(d["active_cap3_rows"])}, guarded challenger accepted rows {int(d["guarded_challenger_accepted_rows"])}.
- What changed: no trading logic changed; this task audits why Task682/Task684 engine changes could fail to change final guarded results.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and source readiness

Task685 reads Task684 stack, accepted trades, allocation, and simulation artifacts. The audit finds that source data is present in many rows, but assignment certification is absent. This means source-aware engines are still research-only.

{t678.markdown_table(summary)}

### Exact join keys

- Upstream panels preserve `lifecycle_id`, `symbol`, `entry_ts`, `theme_id`, and `split_name`.
- This audit does not create new joins for trading assignment.
- Guarded identity is checked by `candidate_name`, `split_scope`, `allocation_reason`, and `accepted_flag`.

### Leakage audit

- Task685 does not create assignment ranks.
- Return fields are only reported as evaluation-only in active trade audit.
- No label, future price, symbol blacklist, or theme blacklist is introduced.

### Root cause

{t678.markdown_table(root_cause)}

### Guarded identity audit

{t678.markdown_table(guarded_identity)}

### Split/OOS source readiness

{t678.markdown_table(split_readiness)}

### Failure decomposition

- The five engines can describe context, but they cannot prove assignment-ready source status.
- `source_integrity_state` is `source_gap_research_only` when `used_for_assignment_flag=0`.
- Guarded candidate preserves active cap3 first. With no certified challenger path, final result can equal active cap3.

### Cost/slippage stress where PnL changed

Not applicable. Task685 changes no PnL simulation and creates no new candidate.

### Remaining blockers

- Row-level source certification contract is missing.
- Macro as-of data is repaired/provisional, not raw release-asof certified.
- Microstructure remains pending for these assignment decisions.
- Challenger admission must be retested only after source certification is fixed.

## No-Background Decision-Maker Report

- What happened: the five engines did not change guarded results because the data layer still says the rows are research-only.
- Why it matters: better labels cannot safely control trades until the source readiness gate says the input was actually usable at that time.
- Whether this changes capital/deployment readiness: no. Status remains NOT_ACCEPTED and FORBIDDEN.
- Plain-language next step: fix the source certification pipe first, then rerun the five engines.

## Artifact Manifest

- Inputs: Task684 stack, accepted trades, allocation, simulation result.
- Outputs: source readiness summary, flag distribution, active cap3 audit, root cause table, guarded identity audit, split readiness table, decision, pass/fail, manifest.
- Row counts: summary {len(summary)}, root cause {len(root_cause)}, guarded identity {len(guarded_identity)}, split readiness {len(split_readiness)}.
- Validation commands: `python src/backtest/build_task685_data_management_source_readiness_audit.py`; `python -m unittest tests.test_task685_data_management_source_readiness_audit`; `python scripts/task_registry_validate.py`.

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


def count_gt(frame: pd.DataFrame, col: str, threshold: float) -> int:
    if col not in frame.columns:
        return 0
    return int(pd.to_numeric(frame[col], errors="coerce").fillna(0).gt(threshold).sum())


def assignment_ready_count(frame: pd.DataFrame) -> int:
    if "asof_valid_flag" not in frame.columns or "used_for_assignment_flag" not in frame.columns:
        return 0
    return int(
        (
            pd.to_numeric(frame["asof_valid_flag"], errors="coerce").fillna(0).eq(1)
            & pd.to_numeric(frame["used_for_assignment_flag"], errors="coerce").fillna(0).eq(1)
        ).sum()
    )


def median_num(frame: pd.DataFrame, col: str) -> float:
    if col not in frame.columns or frame.empty:
        return 0.0
    values = pd.to_numeric(frame[col], errors="coerce").dropna()
    return float(values.median()) if len(values) else 0.0


def metric(frame: pd.DataFrame, audit_item: str) -> float:
    row = frame[frame["audit_item"].eq(audit_item)]
    if row.empty:
        return 0.0
    return float(row.iloc[0]["metric_value"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task684-dir", type=Path, default=TASK684_DIR)
    args = parser.parse_args()
    outputs = build_task685_program(args.task684_dir)
    print(f"[Task685] wrote {TASK685_DIR} artifacts={len(outputs)}")


if __name__ == "__main__":
    main()
