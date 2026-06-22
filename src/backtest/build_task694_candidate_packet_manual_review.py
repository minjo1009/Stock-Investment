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


TASK690_DIR = Path("docs/reports/task_690_slot_replacement_hurdle")
TASK693_DIR = Path("docs/reports/task_693_source_packet_v2_price_packet")
TASK694_DIR = Path("docs/reports/task_694_candidate_packet_manual_review")

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


def build_task694_program(task690_dir: Path = TASK690_DIR, task693_dir: Path = TASK693_DIR) -> dict[str, pd.DataFrame]:
    TASK694_DIR.mkdir(parents=True, exist_ok=True)
    competition = pd.read_csv(task690_dir / "task690_cohort_slot_competition_panel.csv")
    leader_v2 = pd.read_csv(task693_dir / "task693_leader_source_packet_v2_review.csv")
    event_evidence = pd.read_csv(task693_dir / "task693_source_event_v2_evidence.csv")
    price_packet = pd.read_csv(task693_dir / "task693_price_absorption_review_ready_packet.csv")

    review_rulebook = build_review_rulebook()
    candidate_packets = build_candidate_packet_review(competition, leader_v2, event_evidence, price_packet)
    summary = build_packet_review_summary(candidate_packets)
    audit = build_integrity_audit(candidate_packets)
    decision = build_decision(candidate_packets, audit)
    pass_fail = audit.copy()

    write_outputs(review_rulebook, candidate_packets, summary, audit, decision, pass_fail)
    return {
        "review_rulebook": review_rulebook,
        "candidate_packets": candidate_packets,
        "summary": summary,
        "audit": audit,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_review_rulebook() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "review_rule": "direct_source_leader_pass",
                "applies_to": "source_supported_leader",
                "pass_condition": "direct economic source events exist and noise share is not dominant",
                "reject_condition": "source packet is mostly ownership/sale/policy noise",
            },
            {
                "review_rule": "price_packet_conditional",
                "applies_to": "price_absorption_packet",
                "pass_condition": "confirmed absorption with no residual extension risk",
                "reject_condition": "review-ready price packet still has extension/high-near risk",
            },
            {
                "review_rule": "cohort_context_check",
                "applies_to": "all_packets",
                "pass_condition": "same timestamp rank and slot claim are coherent",
                "reject_condition": "low absolute score or only relative win versus weak peers",
            },
            {
                "review_rule": "no_strategy_promotion",
                "applies_to": "all_packets",
                "pass_condition": "packet can be used for manual review only",
                "reject_condition": "any attempt to treat packet state as allocation approval",
            },
        ]
    )


def build_candidate_packet_review(
    competition: pd.DataFrame,
    leader_v2: pd.DataFrame,
    event_evidence: pd.DataFrame,
    price_packet: pd.DataFrame,
) -> pd.DataFrame:
    comp = competition.set_index("lifecycle_id")
    event_summary = summarize_event_evidence(event_evidence)
    rows = []

    supported_leaders = leader_v2[leader_v2["source_packet_v2_state"].eq("source_packet_direct_economic_supported")]
    for _, row in supported_leaders.iterrows():
        lifecycle_id = row["lifecycle_id"]
        comp_row = comp.loc[lifecycle_id]
        event_row = event_summary.loc[lifecycle_id]
        review = classify_source_candidate(row, comp_row, event_row)
        rows.append(
            {
                "candidate_packet_review_id": f"{lifecycle_id}|source_supported_packet_review",
                "packet_type": "source_supported_leader",
                **identity_from_row(row),
                "sector_family": row["sector_family"],
                "slot_claim_score": float(comp_row["slot_claim_score"]),
                "cohort_id": comp_row["cohort_id"],
                "cohort_size": int(comp_row["cohort_size"]),
                "cohort_rank": int(comp_row["cohort_rank"]),
                "source_packet_v2_state": row["source_packet_v2_state"],
                "direct_economic_source_event_count": int(row["direct_economic_source_event_count"]),
                "noise_event_count": int(row["noise_event_count"]),
                "event_with_economic_terms_count": int(row["event_with_economic_terms_count"]),
                "top_event_title_sample": row["top_event_title_sample"],
                "packet_review_state": review["packet_review_state"],
                "packet_review_verdict": review["packet_review_verdict"],
                "human_review_summary": review["human_review_summary"],
                "remaining_risk": review["remaining_risk"],
                "source_event_state_mix": event_row["source_event_state_mix"],
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )

    for _, row in price_packet.iterrows():
        lifecycle_id = row["lifecycle_id"]
        comp_row = comp.loc[lifecycle_id]
        review = classify_price_candidate(row, comp_row)
        rows.append(
            {
                "candidate_packet_review_id": f"{lifecycle_id}|price_absorption_packet_review",
                "packet_type": "price_absorption_packet",
                **identity_from_row(row),
                "sector_family": row["sector_family"],
                "slot_claim_score": float(row["slot_claim_score"]),
                "cohort_id": row["cohort_id"],
                "cohort_size": int(comp_row["cohort_size"]),
                "cohort_rank": int(comp_row["cohort_rank"]),
                "source_packet_v2_state": "",
                "direct_economic_source_event_count": 0,
                "noise_event_count": 0,
                "event_with_economic_terms_count": 0,
                "top_event_title_sample": "",
                "packet_review_state": review["packet_review_state"],
                "packet_review_verdict": review["packet_review_verdict"],
                "human_review_summary": review["human_review_summary"],
                "remaining_risk": review["remaining_risk"],
                "source_event_state_mix": "",
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def summarize_event_evidence(event_evidence: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for lifecycle_id, group in event_evidence.groupby("lifecycle_id"):
        state_counts = group["source_event_v2_state"].value_counts().to_dict()
        rows.append(
            {
                "lifecycle_id": lifecycle_id,
                "source_event_state_mix": "|".join(f"{key}:{value}" for key, value in sorted(state_counts.items())),
                "direct_event_count": int(group["source_event_v2_state"].eq("direct_economic_source_supported").sum()),
                "noise_event_count": int(
                    group["source_event_v2_state"].isin(
                        ["ownership_or_sale_filing_noise", "ownership_filing_with_weak_economic_terms", "broad_policy_not_symbol_specific"]
                    ).sum()
                ),
            }
        )
    return pd.DataFrame(rows).set_index("lifecycle_id")


def classify_source_candidate(row: pd.Series, comp_row: pd.Series, event_row: pd.Series) -> dict[str, str]:
    direct = int(row["direct_economic_source_event_count"])
    noise = int(row["noise_event_count"])
    total = int(row["linked_event_count"])
    score = float(comp_row["slot_claim_score"])
    noise_share = noise / total if total else 1.0
    if direct >= 2 and score >= 5 and noise_share < 0.75:
        state = "source_packet_review_pass"
        verdict = "manual_review_pass_not_allocation_approved"
    elif direct >= 1 and score >= 5:
        state = "source_packet_conditional_noise_heavy"
        verdict = "manual_review_conditional"
    else:
        state = "source_packet_review_reject"
        verdict = "manual_review_reject"
    summary = (
        f"direct_events={direct}|noise_events={noise}|linked_events={total}|"
        f"slot_score={score:.1f}|titles={row['top_event_title_sample']}"
    )
    risk = []
    if noise_share >= 0.5:
        risk.append("noise_heavy_packet")
    if "ownership" in str(event_row["source_event_state_mix"]):
        risk.append("ownership_filing_mix")
    if score < 5:
        risk.append("low_slot_score")
    return {
        "packet_review_state": state,
        "packet_review_verdict": verdict,
        "human_review_summary": summary,
        "remaining_risk": "|".join(risk) if risk else "no_major_packet_risk",
    }


def classify_price_candidate(row: pd.Series, comp_row: pd.Series) -> dict[str, str]:
    risk = str(row["residual_review_risk"])
    score = float(row["slot_claim_score"])
    if risk == "no_major_price_absorption_risk" and score >= 10:
        state = "price_packet_review_pass"
        verdict = "manual_review_pass_not_allocation_approved"
    elif score >= 10:
        state = "price_packet_conditional_extension_risk"
        verdict = "manual_review_conditional"
    else:
        state = "price_packet_review_reject"
        verdict = "manual_review_reject"
    summary = f"{row['human_packet_summary']}|cohort_rank={int(comp_row['cohort_rank'])}|cohort_size={int(comp_row['cohort_size'])}"
    return {
        "packet_review_state": state,
        "packet_review_verdict": verdict,
        "human_review_summary": summary,
        "remaining_risk": risk,
    }


def build_packet_review_summary(candidate_packets: pd.DataFrame) -> pd.DataFrame:
    return (
        candidate_packets.groupby(["packet_type", "packet_review_state", "packet_review_verdict"], dropna=False)
        .size()
        .reset_index(name="candidate_count")
    )


def build_integrity_audit(candidate_packets: pd.DataFrame) -> pd.DataFrame:
    forbidden = sorted(col for col in candidate_packets.columns if col in FORBIDDEN_COLUMNS)
    return pd.DataFrame(
        [
            gate(
                "candidate_packet_count",
                len(candidate_packets) == 11,
                f"candidate_packets={len(candidate_packets)}",
                "9 source-supported leaders plus 2 price absorption packets",
            ),
            gate(
                "packet_review_states_decomposed",
                candidate_packets["packet_review_state"].nunique() >= 2,
                f"states={candidate_packets['packet_review_state'].nunique()}",
                "manual packet review should split pass/conditional/reject where data supports it",
            ),
            gate(
                "no_outcome_columns_in_task694_outputs",
                len(forbidden) == 0,
                "|".join(forbidden) if forbidden else "none",
                "PnL/outcome columns excluded",
            ),
            gate("no_strategy_promotion", True, "no PnL simulation or allocation rule promotion was run", "manual packet review only"),
        ]
    )


def build_decision(candidate_packets: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task694",
                "verdict": "CANDIDATE_PACKET_MANUAL_REVIEW_BUILT_NO_TRADING_PROMOTION",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "candidate_packet_count": int(len(candidate_packets)),
                "manual_review_pass_count": int(candidate_packets["packet_review_verdict"].eq("manual_review_pass_not_allocation_approved").sum()),
                "manual_review_conditional_count": int(candidate_packets["packet_review_verdict"].eq("manual_review_conditional").sum()),
                "manual_review_reject_count": int(candidate_packets["packet_review_verdict"].eq("manual_review_reject").sum()),
                "source_packet_candidate_count": int(candidate_packets["packet_type"].eq("source_supported_leader").sum()),
                "price_packet_candidate_count": int(candidate_packets["packet_type"].eq("price_absorption_packet").sum()),
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "Eleven review candidates were converted into human-readable manual review packets before allocation logic.",
                "next_action": "Use only manual-review pass or conditional packets to draft a tiny eligibility rule, then audit before backtest.",
            }
        ]
    )


def write_outputs(
    review_rulebook: pd.DataFrame,
    candidate_packets: pd.DataFrame,
    summary: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task694_packet_review_rulebook.csv": review_rulebook,
        "task694_candidate_packet_review.csv": candidate_packets,
        "task694_packet_review_summary.csv": summary,
        "task694_integrity_audit.csv": audit,
        "task_694_decision.csv": decision,
        "task_694_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK694_DIR / name, index=False)
    (TASK694_DIR / "task_694_candidate_packet_manual_review.md").write_text(
        render_report(review_rulebook, candidate_packets, summary, audit, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK694_DIR, TASK694_DIR / "artifact_manifest.csv")


def render_report(
    review_rulebook: pd.DataFrame,
    candidate_packets: pd.DataFrame,
    summary: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    packet_table = candidate_packets[
        [
            "packet_type",
            "symbol",
            "entry_ts",
            "packet_review_state",
            "packet_review_verdict",
            "remaining_risk",
            "human_review_summary",
        ]
    ]
    return f"""# Task694 Candidate Packet Manual Review

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Key metrics: packets {int(d["candidate_packet_count"])}, pass {int(d["manual_review_pass_count"])}, conditional {int(d["manual_review_conditional_count"])}, reject {int(d["manual_review_reject_count"])}.
- What changed: eleven candidates became human-readable review packets, not allocation rules.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and source readiness

Inputs are Task690 cohort slot competition and Task693 source/price packet outputs.

### Exact join keys

- Source packet candidates: Task693 `lifecycle_id` to Task690 competition context.
- Price packet candidates: Task693 price packet `lifecycle_id` to Task690 competition context.

### Leakage audit

- No PnL, win/loss, simulated exit, or future price columns are included.
- This task does not run a backtest and does not promote a trading rule.

### Review Rulebook

{t678.markdown_table(review_rulebook)}

### Packet Review Summary

{t678.markdown_table(summary)}

### Candidate Packets

{t678.markdown_table(packet_table)}

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- Direct source support can still be noise-heavy when ownership filings dominate the packet.
- Price absorption packets remain conditional if residual extension risk exists.
- Manual review pass is not allocation approval.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Decide whether conditional packets are allowed into an eligibility draft.
- Define a tiny eligibility rule only after packet review.
- Audit the draft rule before any backtest.

## No-Background Decision-Maker Report

- What happened: 11 candidates were translated into readable review packets.
- Why it matters: we can judge whether the candidate makes sense before coding a trading rule.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: draft a tiny eligibility rule only from reviewed packets.

## Artifact Manifest

- Inputs: Task690 competition panel, Task693 leader source packet v2 and price packets.
- Outputs: review rulebook, candidate packet review, summary, integrity audit, decision, pass/fail, manifest.
- Row counts: candidate packets {len(candidate_packets)}, summary {len(summary)}.
- Validation commands: `python src/backtest/build_task694_candidate_packet_manual_review.py`; `python -m unittest tests.test_task694_candidate_packet_manual_review`; `python scripts/task_registry_validate.py`.

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
    parser.add_argument("--task690-dir", type=Path, default=TASK690_DIR)
    parser.add_argument("--task693-dir", type=Path, default=TASK693_DIR)
    args = parser.parse_args()
    build_task694_program(task690_dir=args.task690_dir, task693_dir=args.task693_dir)
    print(f"[Task694] wrote {TASK694_DIR}")


if __name__ == "__main__":
    main()
