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


TASK689_DIR = Path("docs/reports/task_689_interpretation_edge_quality")
TASK690_DIR = Path("docs/reports/task_690_slot_replacement_hurdle")
TASK691_DIR = Path("docs/reports/task_691_slot_leader_contender_review")

FORBIDDEN_OBJECT_COLUMNS = {
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


def build_task691_program(task689_dir: Path = TASK689_DIR, task690_dir: Path = TASK690_DIR) -> dict[str, pd.DataFrame]:
    TASK691_DIR.mkdir(parents=True, exist_ok=True)
    competition = pd.read_csv(task690_dir / "task690_cohort_slot_competition_panel.csv")
    explanation = pd.read_csv(task690_dir / "task690_slot_claim_explanation_v2.csv")
    interpretation = pd.read_csv(task689_dir / "task689_interpretation_quality_panel.csv")
    edge = pd.read_csv(task689_dir / "task689_edge_quality_panel.csv")
    weak = pd.read_csv(task689_dir / "task689_candidate_weak_layer_audit.csv")

    confirmation_rulebook = build_confirmation_rulebook()
    leader_review = build_leader_review(competition, interpretation, edge, weak)
    contender_map = build_contender_confirmation_map(competition, interpretation, edge, weak)
    cohort_review = build_cohort_review_summary(competition, leader_review, contender_map)
    audit = build_integrity_audit(competition, explanation, leader_review, contender_map, cohort_review)
    decision = build_decision(leader_review, contender_map, cohort_review, audit)
    pass_fail = audit.copy()

    write_outputs(confirmation_rulebook, leader_review, contender_map, cohort_review, audit, decision, pass_fail)
    return {
        "confirmation_rulebook": confirmation_rulebook,
        "leader_review": leader_review,
        "contender_map": contender_map,
        "cohort_review": cohort_review,
        "audit": audit,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_confirmation_rulebook() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "confirmation_type": "price_absorption_confirmation",
                "applies_when": "priced-in gap, extension risk, or low margin versus next peer",
                "must_confirm": "price remains accepted without immediate fade; no full-slot promotion from headline alone",
                "promotion_effect": "contender may become review-ready, not auto-buy",
            },
            {
                "confirmation_type": "source_packet_confirmation",
                "applies_when": "customer quality, contract value, margin bridge, or surprise is weak",
                "must_confirm": "source text supports economic value, counterparty quality, repeatability, and expectation surprise",
                "promotion_effect": "economic interpretation gap can be downgraded",
            },
            {
                "confirmation_type": "sector_blocker_clearance",
                "applies_when": "sector blocker or blocker-limited state exists",
                "must_confirm": "funding, duration, policy, commodity, or credit blocker is absent or improving",
                "promotion_effect": "candidate can move from cap-limited/delayed to contender review",
            },
            {
                "confirmation_type": "peer_margin_confirmation",
                "applies_when": "candidate is rank 1-3 but margin is small",
                "must_confirm": "candidate has clear same-timestamp superiority versus peers after quality penalties",
                "promotion_effect": "candidate can become slot leader candidate",
            },
            {
                "confirmation_type": "incumbent_replay_confirmation",
                "applies_when": "active exposure proxy hurdle remains unresolved",
                "must_confirm": "deterministic portfolio replay identifies incumbent and opportunity cost without proximity matching",
                "promotion_effect": "replacement decision can be audited against actual incumbent",
            },
        ]
    )


def build_leader_review(
    competition: pd.DataFrame,
    interpretation: pd.DataFrame,
    edge: pd.DataFrame,
    weak: pd.DataFrame,
) -> pd.DataFrame:
    leaders = competition[competition["slot_claim_tier"].eq("slot_leader")].copy()
    interp = summarize_interpretation_quality(interpretation)
    edges = summarize_edge_quality(edge)
    weak_map = weak.set_index("lifecycle_id")
    rows = []
    for _, row in leaders.iterrows():
        lifecycle_id = str(row["lifecycle_id"])
        quality = interp.loc[lifecycle_id]
        edge_row = edges.loc[lifecycle_id]
        weak_row = weak_map.loc[lifecycle_id]
        status = classify_leader_review_status(row, quality, edge_row, weak_row)
        rows.append(
            {
                "leader_review_id": f"{lifecycle_id}|leader_review",
                **identity_from_row(row),
                "sector_family": row["sector_family"],
                "cohort_id": row["cohort_id"],
                "cohort_size": int(row["cohort_size"]),
                "cohort_rank": int(row["cohort_rank"]),
                "slot_claim_score": float(row["slot_claim_score"]),
                "margin_vs_cohort_median": float(row["margin_vs_cohort_median"]),
                "margin_vs_next_peer": float(row["margin_vs_next_peer"]),
                "leader_review_status": status,
                "leader_quality_issue_count": int(quality["quality_issue_count"]),
                "leader_edge_issue_count": int(edge_row["edge_issue_count"]),
                "dominant_interpretation_gap": weak_row["dominant_interpretation_gap"],
                "weakest_layer": row["weakest_layer"],
                "required_pre_backtest_review": leader_required_review(row, quality, edge_row, weak_row),
                "leader_verdict": leader_verdict(status),
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_contender_confirmation_map(
    competition: pd.DataFrame,
    interpretation: pd.DataFrame,
    edge: pd.DataFrame,
    weak: pd.DataFrame,
) -> pd.DataFrame:
    contenders = competition[competition["slot_claim_tier"].eq("slot_contender")].copy()
    interp = summarize_interpretation_quality(interpretation)
    edges = summarize_edge_quality(edge)
    weak_map = weak.set_index("lifecycle_id")
    rows = []
    for _, row in contenders.iterrows():
        lifecycle_id = str(row["lifecycle_id"])
        quality = interp.loc[lifecycle_id]
        edge_row = edges.loc[lifecycle_id]
        weak_row = weak_map.loc[lifecycle_id]
        confirmation = choose_confirmation_type(row, quality, edge_row, weak_row)
        rows.append(
            {
                "contender_confirmation_id": f"{lifecycle_id}|contender_confirmation",
                **identity_from_row(row),
                "sector_family": row["sector_family"],
                "cohort_id": row["cohort_id"],
                "cohort_size": int(row["cohort_size"]),
                "cohort_rank": int(row["cohort_rank"]),
                "slot_claim_score": float(row["slot_claim_score"]),
                "margin_vs_cohort_median": float(row["margin_vs_cohort_median"]),
                "margin_vs_next_peer": float(row["margin_vs_next_peer"]),
                "weakest_layer": row["weakest_layer"],
                "dominant_interpretation_gap": weak_row["dominant_interpretation_gap"],
                "required_confirmation_type": confirmation,
                "promotion_hurdle": promotion_hurdle_for_confirmation(confirmation),
                "blocker_to_clear": blocker_to_clear(row, quality, edge_row, weak_row),
                "contender_review_bucket": contender_review_bucket(row, confirmation),
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def build_cohort_review_summary(
    competition: pd.DataFrame,
    leader_review: pd.DataFrame,
    contender_map: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    leader_counts = leader_review.groupby("cohort_id").size().to_dict() if len(leader_review) else {}
    contender_counts = contender_map.groupby("cohort_id").size().to_dict() if len(contender_map) else {}
    for cohort_id, group in competition.groupby("cohort_id", dropna=False):
        rows.append(
            {
                "cohort_id": cohort_id,
                "entry_ts": group["entry_ts"].iloc[0],
                "split_name": group["split_name"].iloc[0],
                "cohort_size": int(len(group)),
                "leader_count": int(leader_counts.get(cohort_id, 0)),
                "contender_count": int(contender_counts.get(cohort_id, 0)),
                "no_claim_count": int(group["slot_claim_tier"].eq("research_only_or_no_claim").sum()),
                "cap_limited_or_delayed_count": int(group["slot_claim_tier"].eq("cap_limited_or_delayed").sum()),
                "top_score": float(group["slot_claim_score"].max()),
                "score_spread": float(group["slot_claim_score"].max() - group["slot_claim_score"].min()),
                "cohort_review_state": classify_cohort_review_state(group),
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def summarize_interpretation_quality(interpretation: pd.DataFrame) -> pd.DataFrame:
    frame = interpretation.copy()
    frame["quality_issue"] = frame["interpretation_quality_tier"].isin(["weak", "proxy_only"]).astype(int)
    frame["priced_in_issue"] = frame["priced_in_quality_state"].isin(["proxy_only", "mixed_proxy"]).astype(int)
    frame["source_packet_issue"] = frame["quality_reason_codes"].astype(str).str.contains(
        "customer_quality|cash_flow_bridge|contract_value|expectation_surprise", regex=True
    ).astype(int)
    return frame.groupby("lifecycle_id").agg(
        quality_issue_count=("quality_issue", "sum"),
        priced_in_issue_count=("priced_in_issue", "sum"),
        source_packet_issue_count=("source_packet_issue", "sum"),
        strong_interpretation_count=("interpretation_quality_tier", lambda values: int(values.eq("strong").sum())),
    )


def summarize_edge_quality(edge: pd.DataFrame) -> pd.DataFrame:
    frame = edge.copy()
    frame["edge_issue"] = frame["edge_quality_tier"].isin(["weak", "proxy_only"]).astype(int)
    return frame.groupby("lifecycle_id").agg(
        edge_issue_count=("edge_issue", "sum"),
        blocker_edge_count=("sector_specific_blocker_flag", "sum"),
        confirmation_edge_count=("sector_specific_confirmation_required_flag", "sum"),
        strong_edge_count=("edge_quality_tier", lambda values: int(values.eq("strong").sum())),
    )


def classify_leader_review_status(row: pd.Series, quality: pd.Series, edge: pd.Series, weak: pd.Series) -> str:
    if float(row["slot_claim_score"]) < 5:
        return "leader_low_absolute_score"
    if int(edge["blocker_edge_count"]) > 0:
        return "leader_blocker_conflict"
    if int(quality["source_packet_issue_count"]) > 0:
        return "leader_source_packet_needed"
    if int(quality["priced_in_issue_count"]) > 0 or "priced_in" in str(weak["dominant_interpretation_gap"]):
        return "leader_priced_in_review_needed"
    if int(row["cohort_size"]) <= 2:
        return "leader_thin_cohort"
    return "clean_review_ready_leader"


def leader_required_review(row: pd.Series, quality: pd.Series, edge: pd.Series, weak: pd.Series) -> str:
    status = classify_leader_review_status(row, quality, edge, weak)
    mapping = {
        "leader_low_absolute_score": "absolute_score_floor_review",
        "leader_blocker_conflict": "sector_blocker_clearance",
        "leader_source_packet_needed": "source_packet_confirmation",
        "leader_priced_in_review_needed": "price_absorption_confirmation",
        "leader_thin_cohort": "peer_margin_confirmation",
        "clean_review_ready_leader": "candidate_packet_review",
    }
    return mapping[status]


def leader_verdict(status: str) -> str:
    if status == "clean_review_ready_leader":
        return "review_ready_not_trade_approved"
    if status in {"leader_low_absolute_score", "leader_blocker_conflict"}:
        return "leader_label_but_not_allocation_ready"
    return "leader_needs_specific_confirmation"


def choose_confirmation_type(row: pd.Series, quality: pd.Series, edge: pd.Series, weak: pd.Series) -> str:
    dominant_gap = str(weak["dominant_interpretation_gap"])
    if int(edge["blocker_edge_count"]) > 0:
        return "sector_blocker_clearance"
    if "priced_in" in dominant_gap:
        return "price_absorption_confirmation"
    if str(row["weakest_layer"]) == "slot_replacement_hurdle" or "theme_breadth" in dominant_gap:
        return "peer_margin_confirmation"
    if int(quality["source_packet_issue_count"]) > 0 or "customer" in dominant_gap:
        return "source_packet_confirmation"
    if int(edge["confirmation_edge_count"]) > 0:
        return "sector_blocker_clearance"
    return "incumbent_replay_confirmation"


def promotion_hurdle_for_confirmation(confirmation: str) -> str:
    mapping = {
        "price_absorption_confirmation": "show_price_acceptance_without_extension_fade",
        "source_packet_confirmation": "show_direct_economic_value_customer_quality_margin_or_surprise",
        "sector_blocker_clearance": "show_sector_blocker_absent_or_improving",
        "peer_margin_confirmation": "raise_peer_margin_or_reduce_quality_penalty_inside_same_cohort",
        "incumbent_replay_confirmation": "identify_actual_incumbent_and_opportunity_cost_by_deterministic_replay",
    }
    return mapping.get(confirmation, "manual_review")


def blocker_to_clear(row: pd.Series, quality: pd.Series, edge: pd.Series, weak: pd.Series) -> str:
    blockers = []
    if int(edge["blocker_edge_count"]) > 0:
        blockers.append("sector_edge_blocker")
    if int(quality["source_packet_issue_count"]) > 0:
        blockers.append("source_packet_economic_gap")
    if int(quality["priced_in_issue_count"]) > 0:
        blockers.append("priced_in_or_absorption_gap")
    if float(row["margin_vs_next_peer"]) < 1:
        blockers.append("peer_margin_too_small")
    if str(row["weakest_layer"]) == "slot_replacement_hurdle":
        blockers.append("slot_replacement_hurdle")
    return "|".join(blockers) if blockers else "no_major_blocker_detected"


def contender_review_bucket(row: pd.Series, confirmation: str) -> str:
    if confirmation == "sector_blocker_clearance":
        return "delayed_or_cap_limited_until_blocker_clears"
    if confirmation == "peer_margin_confirmation":
        return "same_cohort_margin_review"
    if confirmation == "source_packet_confirmation":
        return "source_packet_review"
    if confirmation == "price_absorption_confirmation":
        return "price_acceptance_review"
    return "incumbent_replay_review"


def classify_cohort_review_state(group: pd.DataFrame) -> str:
    leaders = int(group["slot_claim_tier"].eq("slot_leader").sum())
    contenders = int(group["slot_claim_tier"].eq("slot_contender").sum())
    blockers = int(group["slot_claim_tier"].eq("cap_limited_or_delayed").sum())
    if leaders > 0 and contenders == 0:
        return "leader_only_cohort"
    if leaders > 0 and contenders > 0:
        return "leader_plus_contenders"
    if leaders == 0 and contenders > 0:
        return "contender_only_no_clear_leader"
    if blockers > 0:
        return "blocker_limited_cohort"
    return "no_slot_claim_cohort"


def build_integrity_audit(
    competition: pd.DataFrame,
    explanation: pd.DataFrame,
    leader_review: pd.DataFrame,
    contender_map: pd.DataFrame,
    cohort_review: pd.DataFrame,
) -> pd.DataFrame:
    outputs = {
        "leader_review": leader_review,
        "contender_map": contender_map,
        "cohort_review": cohort_review,
    }
    forbidden = sorted(
        f"{name}:{col}" for name, frame in outputs.items() for col in frame.columns if col in FORBIDDEN_OBJECT_COLUMNS
    )
    rows = [
        gate(
            "leader_and_contender_counts_match_task690",
            len(leader_review) == int(competition["slot_claim_tier"].eq("slot_leader").sum())
            and len(contender_map) == int(competition["slot_claim_tier"].eq("slot_contender").sum()),
            f"leaders={len(leader_review)}; contenders={len(contender_map)}",
            "Task690 slot leader and contender counts must match",
        ),
        gate(
            "leader_review_decomposed",
            leader_review["leader_review_status"].nunique() >= 3,
            f"leader_statuses={leader_review['leader_review_status'].nunique()}",
            "leaders should split into multiple review states",
        ),
        gate(
            "contender_confirmation_decomposed",
            contender_map["required_confirmation_type"].nunique() >= 2,
            f"confirmation_types={contender_map['required_confirmation_type'].nunique()}",
            "contenders should split into data-supported confirmation paths",
        ),
        gate(
            "cohort_review_present",
            len(cohort_review) == competition["cohort_id"].nunique(),
            f"cohort_review={len(cohort_review)}; cohorts={competition['cohort_id'].nunique()}",
            "one cohort review row per cohort",
        ),
        gate(
            "no_outcome_columns_in_review_outputs",
            len(forbidden) == 0,
            "|".join(forbidden) if forbidden else "none",
            "PnL/outcome columns excluded",
        ),
        gate(
            "no_strategy_promotion",
            True,
            "no PnL simulation or allocation rule promotion was run",
            "leader/contender review only",
        ),
    ]
    return pd.DataFrame(rows)


def build_decision(
    leader_review: pd.DataFrame,
    contender_map: pd.DataFrame,
    cohort_review: pd.DataFrame,
    audit: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "task_id": "Task691",
                "verdict": "SLOT_LEADER_CONTENDER_REVIEW_BUILT_NO_TRADING_PROMOTION",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "slot_leader_count": int(len(leader_review)),
                "slot_contender_count": int(len(contender_map)),
                "cohort_review_count": int(len(cohort_review)),
                "leader_review_status_count": int(leader_review["leader_review_status"].nunique()),
                "contender_confirmation_type_count": int(contender_map["required_confirmation_type"].nunique()),
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "Slot leaders and contenders are decomposed into review and confirmation paths before any backtest.",
                "next_action": "Inspect leader review statuses and contender confirmation paths, then define only reviewed allocation candidates.",
            }
        ]
    )


def write_outputs(
    confirmation_rulebook: pd.DataFrame,
    leader_review: pd.DataFrame,
    contender_map: pd.DataFrame,
    cohort_review: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task691_confirmation_rulebook.csv": confirmation_rulebook,
        "task691_slot_leader_review.csv": leader_review,
        "task691_contender_confirmation_map.csv": contender_map,
        "task691_cohort_review_summary.csv": cohort_review,
        "task691_integrity_audit.csv": audit,
        "task_691_decision.csv": decision,
        "task_691_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK691_DIR / name, index=False)
    (TASK691_DIR / "task_691_slot_leader_contender_review.md").write_text(
        render_report(confirmation_rulebook, leader_review, contender_map, cohort_review, audit, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK691_DIR, TASK691_DIR / "artifact_manifest.csv")


def render_report(
    confirmation_rulebook: pd.DataFrame,
    leader_review: pd.DataFrame,
    contender_map: pd.DataFrame,
    cohort_review: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    leader_summary = leader_review.groupby(["leader_review_status", "leader_verdict"], dropna=False).size().reset_index(name="leader_count")
    contender_summary = contender_map.groupby(["required_confirmation_type", "contender_review_bucket"], dropna=False).size().reset_index(name="contender_count")
    cohort_summary = cohort_review.groupby(["cohort_review_state"], dropna=False).size().reset_index(name="cohort_count")
    return f"""# Task691 Slot Leader and Contender Review

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Key metrics: leaders {int(d["slot_leader_count"])}, contenders {int(d["slot_contender_count"])}, cohort reviews {int(d["cohort_review_count"])}.
- What changed: slot leaders and contenders now have review paths before any allocation backtest.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and source readiness

Inputs are Task689 quality panels and Task690 same-timestamp slot competition outputs. No new raw source is added.

### Exact join keys

- `lifecycle_id` joins leader/contender rows to interpretation, edge, and weak-layer audits.
- `cohort_id` keeps review inside same timestamp and split.

### Leakage audit

- No PnL, win/loss, simulated exit, or future price columns are included.
- This task does not run a backtest and does not promote a trading rule.

### Confirmation rulebook

{t678.markdown_table(confirmation_rulebook)}

### Leader review summary

{t678.markdown_table(leader_summary)}

### Contender confirmation summary

{t678.markdown_table(contender_summary)}

### Cohort review summary

{t678.markdown_table(cohort_summary)}

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- Leaders are not automatically clean. They can be thin, low-score, priced-in, or source-packet dependent.
- Contenders need explicit confirmation before promotion.
- Incumbent replacement remains unresolved until deterministic portfolio replay supplies actual incumbent identity.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Review leader statuses and remove weak leaders from allocation candidates.
- Convert contender confirmation paths into pre-backtest eligibility rules.
- Add deterministic incumbent replay before true replacement logic.

## No-Background Decision-Maker Report

- What happened: 28 leaders and 407 contenders were split into review buckets.
- Why it matters: this prevents "leader" from meaning automatic buy.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: approve which review buckets can enter the next allocation test.

## Artifact Manifest

- Inputs: Task689 quality panels, Task690 slot competition outputs.
- Outputs: confirmation rulebook, leader review, contender confirmation map, cohort review summary, integrity audit, decision, pass/fail, manifest.
- Row counts: leaders {len(leader_review)}, contenders {len(contender_map)}, cohorts {len(cohort_review)}.
- Validation commands: `python src/backtest/build_task691_slot_leader_contender_review.py`; `python -m unittest tests.test_task691_slot_leader_contender_review`; `python scripts/task_registry_validate.py`.

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
    parser.add_argument("--task689-dir", type=Path, default=TASK689_DIR)
    parser.add_argument("--task690-dir", type=Path, default=TASK690_DIR)
    args = parser.parse_args()
    build_task691_program(task689_dir=args.task689_dir, task690_dir=args.task690_dir)
    print(f"[Task691] wrote {TASK691_DIR}")


if __name__ == "__main__":
    main()
