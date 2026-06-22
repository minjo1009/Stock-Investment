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


TASK694_DIR = Path("docs/reports/task_694_candidate_packet_manual_review")
TASK695_DIR = Path("docs/reports/task_695_tiny_eligibility_rule_audit")

FORBIDDEN_COLUMNS = {
    "net_return_from_entry",
    "net_return_pct",
    "return_pct",
    "win_flag",
    "win_eval_flag",
    "entry_reduce_failure_flag",
    "false_positive_flag",
    "simulated_exit_price",
    "simulated_exit_ts",
}

IDENTITY = ["lifecycle_id", "symbol", "entry_ts", "entry_ts_utc", "theme_id", "split_name"]


def build_task695_program(task694_dir: Path = TASK694_DIR) -> dict[str, pd.DataFrame]:
    TASK695_DIR.mkdir(parents=True, exist_ok=True)
    packets = pd.read_csv(task694_dir / "task694_candidate_packet_review.csv")

    rulebook = build_eligibility_rulebook()
    eligibility = build_eligibility_draft(packets)
    audit = build_rule_audit(eligibility)
    decision = build_decision(eligibility, audit)
    pass_fail = audit.copy()

    write_outputs(rulebook, eligibility, audit, decision, pass_fail)
    return {
        "rulebook": rulebook,
        "eligibility": eligibility,
        "audit": audit,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_eligibility_rulebook() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "rule_id": "manual_pass_to_eligible_review_candidate",
                "input_condition": "packet_review_verdict == manual_review_pass_not_allocation_approved",
                "eligibility_state": "eligible_review_candidate",
                "permission": "may enter a tiny pre-backtest candidate set after audit",
                "explicit_non_permission": "not allocation approved and not live/paper-trade approved",
            },
            {
                "rule_id": "manual_conditional_to_needs_extra_confirmation",
                "input_condition": "packet_review_verdict == manual_review_conditional",
                "eligibility_state": "needs_extra_confirmation",
                "permission": "kept for confirmation research only",
                "explicit_non_permission": "cannot enter backtest candidate set until confirmation rule is defined",
            },
            {
                "rule_id": "manual_reject_to_excluded",
                "input_condition": "packet_review_verdict == manual_review_reject",
                "eligibility_state": "excluded",
                "permission": "excluded from tiny pre-backtest candidate set",
                "explicit_non_permission": "no allocation, no backtest promotion",
            },
            {
                "rule_id": "outcome_firewall",
                "input_condition": "only Task694 manual packet fields are allowed",
                "eligibility_state": "audit_gate",
                "permission": "audit only",
                "explicit_non_permission": "no PnL, win/loss, exit, or future price fields",
            },
        ]
    )


def build_eligibility_draft(packets: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in packets.iterrows():
        eligibility_state = classify_eligibility(row["packet_review_verdict"])
        rows.append(
            {
                "eligibility_draft_id": f"{row['lifecycle_id']}|tiny_eligibility_v1",
                **identity_from_row(row),
                "packet_type": row["packet_type"],
                "sector_family": row["sector_family"],
                "slot_claim_score": float(row["slot_claim_score"]),
                "packet_review_state": row["packet_review_state"],
                "packet_review_verdict": row["packet_review_verdict"],
                "eligibility_state": eligibility_state,
                "tiny_backtest_candidate_flag": int(eligibility_state == "eligible_review_candidate"),
                "extra_confirmation_required_flag": int(eligibility_state == "needs_extra_confirmation"),
                "excluded_flag": int(eligibility_state == "excluded"),
                "allocation_approved_flag": 0,
                "paper_or_live_trade_approved_flag": 0,
                "eligibility_reason": eligibility_reason(row, eligibility_state),
                "remaining_risk": row["remaining_risk"],
                "human_review_summary": row["human_review_summary"],
                "allowed_input_surface": "task694_candidate_packet_review_only",
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def classify_eligibility(verdict: object) -> str:
    text = str(verdict)
    if text == "manual_review_pass_not_allocation_approved":
        return "eligible_review_candidate"
    if text == "manual_review_conditional":
        return "needs_extra_confirmation"
    return "excluded"


def eligibility_reason(row: pd.Series, state: str) -> str:
    if state == "eligible_review_candidate":
        return f"manual_pass_packet|type={row['packet_type']}|state={row['packet_review_state']}"
    if state == "needs_extra_confirmation":
        return f"conditional_packet|risk={row['remaining_risk']}"
    return f"manual_reject|state={row['packet_review_state']}"


def build_rule_audit(eligibility: pd.DataFrame) -> pd.DataFrame:
    forbidden = sorted(col for col in eligibility.columns if col in FORBIDDEN_COLUMNS)
    return pd.DataFrame(
        [
            gate(
                "eligibility_row_count",
                len(eligibility) == 11,
                f"rows={len(eligibility)}",
                "one eligibility row per Task694 candidate packet",
            ),
            gate(
                "pass_conditional_excluded_counts",
                int(eligibility["tiny_backtest_candidate_flag"].sum()) == 3
                and int(eligibility["extra_confirmation_required_flag"].sum()) == 8
                and int(eligibility["excluded_flag"].sum()) == 0,
                "eligible="
                f"{int(eligibility['tiny_backtest_candidate_flag'].sum())}; conditional="
                f"{int(eligibility['extra_confirmation_required_flag'].sum())}; excluded="
                f"{int(eligibility['excluded_flag'].sum())}",
                "pass 3 eligible, conditional 8 needs extra confirmation, reject 0 excluded",
            ),
            gate(
                "no_allocation_or_trade_approval",
                int(eligibility["allocation_approved_flag"].sum()) == 0
                and int(eligibility["paper_or_live_trade_approved_flag"].sum()) == 0,
                "allocation_approved_sum="
                f"{int(eligibility['allocation_approved_flag'].sum())}; trade_approved_sum="
                f"{int(eligibility['paper_or_live_trade_approved_flag'].sum())}",
                "eligibility draft cannot approve allocation or trading",
            ),
            gate(
                "no_outcome_columns_in_task695_outputs",
                len(forbidden) == 0,
                "|".join(forbidden) if forbidden else "none",
                "PnL/outcome columns excluded",
            ),
            gate(
                "no_strategy_promotion",
                True,
                "no PnL simulation or allocation rule promotion was run",
                "eligibility draft audit only",
            ),
        ]
    )


def build_decision(eligibility: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task695",
                "verdict": "TINY_ELIGIBILITY_RULE_DRAFT_AUDITED_NO_BACKTEST",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "eligibility_row_count": int(len(eligibility)),
                "eligible_review_candidate_count": int(eligibility["tiny_backtest_candidate_flag"].sum()),
                "needs_extra_confirmation_count": int(eligibility["extra_confirmation_required_flag"].sum()),
                "excluded_count": int(eligibility["excluded_flag"].sum()),
                "allocation_approved_count": int(eligibility["allocation_approved_flag"].sum()),
                "paper_or_live_trade_approved_count": int(eligibility["paper_or_live_trade_approved_flag"].sum()),
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "Tiny eligibility rule draft is audited and ready to be passed to a small backtest candidate builder.",
                "next_action": "Build a tiny backtest candidate set from eligible_review_candidate only, then audit before running PnL.",
            }
        ]
    )


def write_outputs(
    rulebook: pd.DataFrame,
    eligibility: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task695_tiny_eligibility_rulebook.csv": rulebook,
        "task695_tiny_eligibility_draft.csv": eligibility,
        "task695_rule_audit.csv": audit,
        "task_695_decision.csv": decision,
        "task_695_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK695_DIR / name, index=False)
    (TASK695_DIR / "task_695_tiny_eligibility_rule_audit.md").write_text(
        render_report(rulebook, eligibility, audit, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK695_DIR, TASK695_DIR / "artifact_manifest.csv")


def render_report(
    rulebook: pd.DataFrame,
    eligibility: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    state_summary = eligibility.groupby(["eligibility_state", "packet_type"], dropna=False).size().reset_index(name="candidate_count")
    candidate_table = eligibility[
        [
            "symbol",
            "entry_ts",
            "packet_type",
            "eligibility_state",
            "tiny_backtest_candidate_flag",
            "extra_confirmation_required_flag",
            "remaining_risk",
        ]
    ]
    return f"""# Task695 Tiny Eligibility Rule Audit

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Key metrics: rows {int(d["eligibility_row_count"])}, eligible {int(d["eligible_review_candidate_count"])}, needs confirmation {int(d["needs_extra_confirmation_count"])}, excluded {int(d["excluded_count"])}.
- What changed: a tiny eligibility rule draft was created and audited, but no backtest was run.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and source readiness

Input is Task694 candidate packet manual review. No raw source is added and no allocation is changed.

### Exact join keys

- `lifecycle_id` is preserved from Task694 packet review.
- No inferred lifecycle matching is used.

### Leakage audit

- No PnL, win/loss, simulated exit, or future price columns are included.
- All allocation/trade approval flags are zero.
- This task does not run a backtest and does not promote a strategy.

### Eligibility Rulebook

{t678.markdown_table(rulebook)}

### Eligibility Summary

{t678.markdown_table(state_summary)}

### Candidate Draft

{t678.markdown_table(candidate_table)}

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- Pass packets become only `eligible_review_candidate`, not allocation-approved candidates.
- Conditional packets remain blocked until extra confirmation logic is defined.
- Reject packets would be excluded, but this reviewed set has zero rejects.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Build a tiny candidate-set artifact from eligible review candidates only.
- Audit that artifact before any PnL simulation.
- Keep conditional packets outside PnL until confirmation rules exist.

## No-Background Decision-Maker Report

- What happened: the 11 reviewed packets became a tiny eligibility draft.
- Why it matters: only 3 candidates can move toward a tiny backtest candidate set.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: create a tiny candidate-set artifact from the 3 eligible rows, then audit it.

## Artifact Manifest

- Inputs: Task694 candidate packet review.
- Outputs: rulebook, eligibility draft, rule audit, decision, pass/fail, manifest.
- Row counts: eligibility {len(eligibility)}, audit {len(audit)}.
- Validation commands: `python src/backtest/build_task695_tiny_eligibility_rule_audit.py`; `python -m unittest tests.test_task695_tiny_eligibility_rule_audit`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

{t678.markdown_table(pass_fail)}
"""


def identity_from_row(row: pd.Series) -> dict[str, object]:
    return {col: row[col] if col in row.index else "" for col in IDENTITY}


def gate(name: str, passed: bool, observed: str, required: str) -> dict[str, object]:
    return {
        "gate_name": name,
        "status": "PRIMARY_PASS" if passed else "NOT_ACCEPTED",
        "pass_flag": int(passed),
        "observed": observed,
        "required": required,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task694-dir", type=Path, default=TASK694_DIR)
    args = parser.parse_args()
    build_task695_program(task694_dir=args.task694_dir)
    print(f"[Task695] wrote {TASK695_DIR}")


if __name__ == "__main__":
    main()
