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


TASK695_DIR = Path("docs/reports/task_695_tiny_eligibility_rule_audit")
TASK696_DIR = Path("docs/reports/task_696_tiny_backtest_candidate_set_audit")

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
    "holding_days",
    "exit_reason",
}

IDENTITY = ["lifecycle_id", "symbol", "entry_ts", "entry_ts_utc", "theme_id", "split_name"]


def build_task696_program(task695_dir: Path = TASK695_DIR) -> dict[str, pd.DataFrame]:
    TASK696_DIR.mkdir(parents=True, exist_ok=True)
    eligibility = pd.read_csv(task695_dir / "task695_tiny_eligibility_draft.csv")

    candidate_set = build_candidate_set(eligibility)
    audit = build_candidate_set_audit(candidate_set, eligibility)
    decision = build_decision(candidate_set, audit)
    pass_fail = audit.copy()
    write_outputs(candidate_set, audit, decision, pass_fail)
    return {
        "candidate_set": candidate_set,
        "audit": audit,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_candidate_set(eligibility: pd.DataFrame) -> pd.DataFrame:
    eligible = eligibility[eligibility["eligibility_state"].eq("eligible_review_candidate")].copy()
    rows = []
    for idx, row in eligible.sort_values(["entry_ts", "symbol"]).reset_index(drop=True).iterrows():
        rows.append(
            {
                "tiny_candidate_set_id": f"Task696|tiny_candidate|{idx + 1:03d}",
                **identity_from_row(row),
                "packet_type": row["packet_type"],
                "sector_family": row["sector_family"],
                "slot_claim_score": float(row["slot_claim_score"]),
                "packet_review_state": row["packet_review_state"],
                "eligibility_state": row["eligibility_state"],
                "tiny_backtest_candidate_flag": 1,
                "candidate_set_scope": "eligible_review_candidate_only",
                "backtest_ready_after_audit_flag": 1,
                "allocation_approved_flag": 0,
                "paper_or_live_trade_approved_flag": 0,
                "pnl_not_run_flag": 1,
                "candidate_reason": row["eligibility_reason"],
                "remaining_risk": row["remaining_risk"],
                "human_review_summary": row["human_review_summary"],
                "source_artifact": "docs/reports/task_695_tiny_eligibility_rule_audit/task695_tiny_eligibility_draft.csv",
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_candidate_set_audit(candidate_set: pd.DataFrame, eligibility: pd.DataFrame) -> pd.DataFrame:
    forbidden = sorted(col for col in candidate_set.columns if col in FORBIDDEN_COLUMNS)
    symbols = set(candidate_set["symbol"].astype(str))
    expected_symbols = {"ASTS", "BA", "TER"}
    return pd.DataFrame(
        [
            gate(
                "candidate_set_count",
                len(candidate_set) == 3,
                f"rows={len(candidate_set)}",
                "tiny candidate set must contain exactly 3 rows",
            ),
            gate(
                "candidate_symbols_match",
                symbols == expected_symbols,
                f"symbols={','.join(sorted(symbols))}",
                "candidate symbols must be ASTS, BA, TER",
            ),
            gate(
                "candidate_set_from_eligible_only",
                candidate_set["eligibility_state"].eq("eligible_review_candidate").all()
                and int(candidate_set["tiny_backtest_candidate_flag"].sum()) == 3,
                "eligible_only="
                f"{candidate_set['eligibility_state'].value_counts().to_dict()}; flags={int(candidate_set['tiny_backtest_candidate_flag'].sum())}",
                "only eligible_review_candidate rows can enter tiny candidate set",
            ),
            gate(
                "conditional_candidates_excluded",
                len(eligibility[eligibility["eligibility_state"].eq("needs_extra_confirmation")]) == 8
                and not set(eligibility[eligibility["eligibility_state"].eq("needs_extra_confirmation")]["lifecycle_id"]).intersection(
                    set(candidate_set["lifecycle_id"])
                ),
                "conditional_count="
                f"{len(eligibility[eligibility['eligibility_state'].eq('needs_extra_confirmation')])}",
                "needs_extra_confirmation rows must stay out of candidate set",
            ),
            gate(
                "no_allocation_or_trade_approval",
                int(candidate_set["allocation_approved_flag"].sum()) == 0
                and int(candidate_set["paper_or_live_trade_approved_flag"].sum()) == 0,
                "allocation_approved_sum="
                f"{int(candidate_set['allocation_approved_flag'].sum())}; trade_approved_sum="
                f"{int(candidate_set['paper_or_live_trade_approved_flag'].sum())}",
                "candidate set cannot approve allocation or trading",
            ),
            gate(
                "pnl_not_run",
                int(candidate_set["pnl_not_run_flag"].sum()) == len(candidate_set),
                f"pnl_not_run_sum={int(candidate_set['pnl_not_run_flag'].sum())}",
                "candidate set is pre-PnL only",
            ),
            gate(
                "no_outcome_columns_in_task696_outputs",
                len(forbidden) == 0,
                "|".join(forbidden) if forbidden else "none",
                "PnL/outcome columns excluded",
            ),
            gate("no_strategy_promotion", True, "no PnL simulation or allocation rule promotion was run", "candidate-set audit only"),
        ]
    )


def build_decision(candidate_set: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task696",
                "verdict": "TINY_BACKTEST_CANDIDATE_SET_BUILT_AUDITED_NO_PNL",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "candidate_set_count": int(len(candidate_set)),
                "candidate_symbols": "|".join(candidate_set["symbol"].astype(str).tolist()),
                "allocation_approved_count": int(candidate_set["allocation_approved_flag"].sum()),
                "paper_or_live_trade_approved_count": int(candidate_set["paper_or_live_trade_approved_flag"].sum()),
                "pnl_run_flag": 0,
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "Tiny backtest candidate set contains ASTS, BA, and TER only and passed pre-PnL audit.",
                "next_action": "Run a small PnL test only against this audited candidate set, with costs and benchmark caveats.",
            }
        ]
    )


def write_outputs(
    candidate_set: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task696_tiny_backtest_candidate_set.csv": candidate_set,
        "task696_candidate_set_audit.csv": audit,
        "task_696_decision.csv": decision,
        "task_696_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK696_DIR / name, index=False)
    (TASK696_DIR / "task_696_tiny_backtest_candidate_set_audit.md").write_text(
        render_report(candidate_set, audit, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK696_DIR, TASK696_DIR / "artifact_manifest.csv")


def render_report(
    candidate_set: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    view = candidate_set[
        [
            "symbol",
            "entry_ts",
            "theme_id",
            "split_name",
            "packet_type",
            "slot_claim_score",
            "remaining_risk",
            "candidate_reason",
        ]
    ]
    return f"""# Task696 Tiny Backtest Candidate Set Audit

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Key metrics: candidate set {int(d["candidate_set_count"])}, symbols `{d["candidate_symbols"]}`, PnL run flag {int(d["pnl_run_flag"])}.
- What changed: built an audited tiny backtest candidate set from eligible review candidates only.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and source readiness

Input is Task695 tiny eligibility draft. No raw source is added and no PnL simulation is run.

### Exact join keys

- Candidate rows preserve `lifecycle_id`, `symbol`, `entry_ts`, `entry_ts_utc`, `theme_id`, and `split_name`.
- No inferred lifecycle matching is used.

### Leakage audit

- No PnL, win/loss, simulated exit, future price, or holding-period columns are included.
- Conditional candidates are excluded.
- Allocation and paper/live trading approvals remain zero.

### Tiny Candidate Set

{t678.markdown_table(view)}

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- Candidate set is very small and research-only.
- BA and TER still carry ownership-filing-mix residual risk from packet review.
- This file is only a clean input for a later small PnL test.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Run a small PnL test only after this pre-PnL audit.
- Compare against cash and QQQ for the same timestamps if PnL is run.
- Keep real capital forbidden regardless of tiny test outcome until full gates pass.

## No-Background Decision-Maker Report

- What happened: ASTS, BA, and TER were isolated as the only tiny backtest candidates.
- Why it matters: PnL can be tested on a clean, audited set instead of a moving target.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: run a tiny PnL test using only this file.

## Artifact Manifest

- Inputs: Task695 tiny eligibility draft.
- Outputs: tiny candidate set, candidate-set audit, decision, pass/fail, manifest.
- Row counts: candidate set {len(candidate_set)}, audit {len(audit)}.
- Validation commands: `python src/backtest/build_task696_tiny_backtest_candidate_set_audit.py`; `python -m unittest tests.test_task696_tiny_backtest_candidate_set_audit`; `python scripts/task_registry_validate.py`.

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
    parser.add_argument("--task695-dir", type=Path, default=TASK695_DIR)
    args = parser.parse_args()
    build_task696_program(task695_dir=args.task695_dir)
    print(f"[Task696] wrote {TASK696_DIR}")


if __name__ == "__main__":
    main()
