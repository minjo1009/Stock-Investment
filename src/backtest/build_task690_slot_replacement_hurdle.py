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


TASK688_DIR = Path("docs/reports/task_688_context_object_contracts")
TASK689_DIR = Path("docs/reports/task_689_interpretation_edge_quality")
TASK690_DIR = Path("docs/reports/task_690_slot_replacement_hurdle")

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


def build_task690_program(task688_dir: Path = TASK688_DIR, task689_dir: Path = TASK689_DIR) -> dict[str, pd.DataFrame]:
    TASK690_DIR.mkdir(parents=True, exist_ok=True)
    bundles = pd.read_csv(task688_dir / "task688_candidate_context_bundles.csv")
    slot = pd.read_csv(task688_dir / "task688_slot_decision_explanations.csv")
    interpretation = pd.read_csv(task689_dir / "task689_interpretation_quality_panel.csv")
    edge = pd.read_csv(task689_dir / "task689_edge_quality_panel.csv")
    weak = pd.read_csv(task689_dir / "task689_candidate_weak_layer_audit.csv")

    rulebook = build_slot_replacement_rulebook()
    competition = build_cohort_slot_competition_panel(bundles, slot, interpretation, edge, weak)
    explanation = build_slot_claim_explanation_v2(competition)
    decomposition = build_slot_hurdle_decomposition(competition)
    audit = build_integrity_audit(competition, explanation, decomposition)
    decision = build_decision(competition, decomposition, audit)
    pass_fail = audit.copy()

    write_outputs(rulebook, competition, explanation, decomposition, audit, decision, pass_fail)
    return {
        "rulebook": rulebook,
        "competition": competition,
        "explanation": explanation,
        "decomposition": decomposition,
        "audit": audit,
        "decision": decision,
        "pass_fail": pass_fail,
    }


def build_slot_replacement_rulebook() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "rule_id": "same_timestamp_only",
                "purpose": "Prevent global Top5 leakage and compare only candidates competing at the same entry timestamp.",
                "required_inputs": "entry_ts|split_name|same-entry peer set",
                "decision_effect": "cohort_rank can be used only inside the same entry_ts and split.",
                "forbidden_shortcut": "No global priority rank or future outcome rank.",
            },
            {
                "rule_id": "clear_superiority_margin",
                "purpose": "New slot claimant must be meaningfully better than peers, not merely slightly higher.",
                "required_inputs": "claim_score minus cohort_median and next peer score",
                "decision_effect": "Leader becomes clear only when margin to median is >= 3 and no blocker exists.",
                "forbidden_shortcut": "Do not admit a candidate because it is rank 1 by a tiny score gap.",
            },
            {
                "rule_id": "blocker_overrides_rank",
                "purpose": "Sector blocker beats attractive headline score.",
                "required_inputs": "sector_specific_blocker_flag|weakest_layer",
                "decision_effect": "Candidate becomes blocker_limited even if cohort_rank is high.",
                "forbidden_shortcut": "Do not use a blocker candidate as a full-slot replacement.",
            },
            {
                "rule_id": "quality_before_capacity",
                "purpose": "Capacity pressure is not enough; candidate must have quality evidence.",
                "required_inputs": "interpretation quality|edge quality|bundle readiness",
                "decision_effect": "Low quality candidates stay confirmation/research even when cohort is small.",
                "forbidden_shortcut": "Do not fill empty slots with weak evidence.",
            },
            {
                "rule_id": "active_exposure_proxy_only",
                "purpose": "Existing holdings are not reconstructed here, so active exposure is a proxy, not an incumbent identity.",
                "required_inputs": "active_theme_count|active_relation_count|active_driver_count where available",
                "decision_effect": "Produces unresolved incumbent hurdle when peer comparison is insufficient.",
                "forbidden_shortcut": "No inferred incumbent symbol/date/price matching.",
            },
        ]
    )


def build_cohort_slot_competition_panel(
    bundles: pd.DataFrame,
    slot: pd.DataFrame,
    interpretation: pd.DataFrame,
    edge: pd.DataFrame,
    weak: pd.DataFrame,
) -> pd.DataFrame:
    interp = summarize_interpretation(interpretation)
    edge_summary = summarize_edges(edge)
    base = (
        bundles.merge(slot, on="lifecycle_id", suffixes=("", "_slot"))
        .merge(weak, on="lifecycle_id", suffixes=("", "_weak"))
        .merge(interp, on="lifecycle_id")
        .merge(edge_summary, on="lifecycle_id")
    )
    normalize_duplicate_metric_columns(
        base,
        [
            "interpretation_weak_count",
            "interpretation_strong_count",
            "edge_weak_count",
            "edge_strong_count",
            "blocker_edge_count",
            "confirmation_edge_count",
            "sizing_modifier_count",
        ],
    )
    base["cohort_id"] = base["split_name"].astype(str) + "|" + base["entry_ts"].astype(str)
    base["slot_claim_score"] = base.apply(score_slot_claim, axis=1)
    base["quality_score_component"] = base["interpretation_claim_score"] + base["edge_claim_score"]
    base["risk_penalty_component"] = (
        base["blocker_edge_count"] * 4
        + base["edge_weak_count"] * 2
        + base["interpretation_weak_count"] * 1.5
        + base["slot_replacement_hurdle_required_flag"] * 1
    )
    grouped = base.groupby("cohort_id", dropna=False)
    base["cohort_size"] = grouped["lifecycle_id"].transform("count")
    base["cohort_rank"] = grouped["slot_claim_score"].rank(method="first", ascending=False).astype(int)
    base["cohort_score_median"] = grouped["slot_claim_score"].transform("median")
    base["cohort_score_max"] = grouped["slot_claim_score"].transform("max")
    base["cohort_score_second"] = grouped["slot_claim_score"].transform(second_highest)
    base["margin_vs_cohort_median"] = base["slot_claim_score"] - base["cohort_score_median"]
    base["margin_vs_next_peer"] = base.apply(margin_vs_next_peer, axis=1)
    base["same_timestamp_rank_scope"] = "same_entry_ts_split_only"
    base["replacement_hurdle_state"] = base.apply(classify_replacement_hurdle_state, axis=1)
    base["slot_claim_tier"] = base.apply(classify_slot_claim_tier, axis=1)
    base["peer_comparison_reason_codes"] = base.apply(build_peer_reason_codes, axis=1)
    columns = [
        "lifecycle_id",
        "symbol",
        "entry_ts",
        "entry_ts_utc",
        "theme_id",
        "split_name",
        "sector_family",
        "cohort_id",
        "cohort_size",
        "same_timestamp_rank_scope",
        "cohort_rank",
        "slot_claim_score",
        "quality_score_component",
        "risk_penalty_component",
        "cohort_score_median",
        "cohort_score_max",
        "cohort_score_second",
        "margin_vs_cohort_median",
        "margin_vs_next_peer",
        "candidate_role",
        "slot_candidate_role",
        "weakest_layer",
        "replacement_hurdle_state",
        "slot_claim_tier",
        "bundle_assignment_ready_flag",
        "slot_replacement_hurdle_required_flag",
        "interpretation_claim_score",
        "edge_claim_score",
        "interpretation_weak_count",
        "interpretation_strong_count",
        "edge_weak_count",
        "edge_strong_count",
        "blocker_edge_count",
        "confirmation_edge_count",
        "sizing_modifier_count",
        "peer_comparison_reason_codes",
    ]
    out = base[columns].copy()
    out["outcome_used_flag"] = 0
    out["future_price_used_flag"] = 0
    out["label_used_flag"] = 0
    return out


def summarize_interpretation(interpretation: pd.DataFrame) -> pd.DataFrame:
    weights = {"strong": 4, "medium": 2, "proxy_only": -1, "weak": -3}
    frame = interpretation.copy()
    frame["tier_weight"] = frame["interpretation_quality_tier"].map(weights).fillna(0)
    frame["specificity_weight"] = pd.to_numeric(frame["economic_specificity_score"], errors="coerce").fillna(0) / 3.0
    return frame.groupby("lifecycle_id").agg(
        interpretation_claim_score=("tier_weight", "sum"),
        interpretation_specificity_score=("specificity_weight", "sum"),
        interpretation_weak_count=("interpretation_quality_tier", lambda values: int(values.isin(["weak", "proxy_only"]).sum())),
        interpretation_strong_count=("interpretation_quality_tier", lambda values: int(values.eq("strong").sum())),
    ).reset_index()


def summarize_edges(edge: pd.DataFrame) -> pd.DataFrame:
    weights = {"strong": 4, "medium": 2, "proxy_only": -1, "weak": -3}
    frame = edge.copy()
    frame["tier_weight"] = frame["edge_quality_tier"].map(weights).fillna(0)
    frame["blocker_penalty"] = pd.to_numeric(frame["sector_specific_blocker_flag"], errors="coerce").fillna(0) * -4
    frame["confirmation_penalty"] = pd.to_numeric(frame["sector_specific_confirmation_required_flag"], errors="coerce").fillna(0) * -1
    return frame.groupby("lifecycle_id").agg(
        edge_claim_score=("tier_weight", "sum"),
        edge_blocker_penalty=("blocker_penalty", "sum"),
        edge_confirmation_penalty=("confirmation_penalty", "sum"),
        edge_weak_count=("edge_quality_tier", lambda values: int(values.isin(["weak", "proxy_only"]).sum())),
        edge_strong_count=("edge_quality_tier", lambda values: int(values.eq("strong").sum())),
        blocker_edge_count=("sector_specific_blocker_flag", "sum"),
        confirmation_edge_count=("sector_specific_confirmation_required_flag", "sum"),
        sizing_modifier_count=("sizing_modifier_flag", "sum"),
    ).reset_index()


def score_slot_claim(row: pd.Series) -> float:
    score = float(row["interpretation_claim_score"]) + float(row["edge_claim_score"])
    score += 4 if int(row["bundle_assignment_ready_flag"]) == 1 else -8
    if str(row["candidate_role"]) == "priority_candidate":
        score += 3
    elif str(row["candidate_role"]) == "confirmation_required_candidate":
        score += 1
    elif str(row["candidate_role"]) == "research_only":
        score -= 6
    score -= float(row["blocker_edge_count"]) * 4
    score -= float(row["edge_weak_count"]) * 1.5
    score -= float(row["interpretation_weak_count"]) * 1.0
    score -= float(row["slot_replacement_hurdle_required_flag"]) * 1.0
    return round(score, 4)


def normalize_duplicate_metric_columns(frame: pd.DataFrame, columns: list[str]) -> None:
    for col in columns:
        if col in frame.columns:
            continue
        for candidate in [f"{col}_y", f"{col}_x", f"{col}_weak", f"{col}_slot"]:
            if candidate in frame.columns:
                frame[col] = frame[candidate]
                break
        if col not in frame.columns:
            frame[col] = 0


def second_highest(values: pd.Series) -> float:
    sorted_values = sorted([float(v) for v in values], reverse=True)
    if len(sorted_values) < 2:
        return sorted_values[0] if sorted_values else 0.0
    return sorted_values[1]


def margin_vs_next_peer(row: pd.Series) -> float:
    if int(row["cohort_size"]) <= 1:
        return 0.0
    if int(row["cohort_rank"]) == 1:
        return round(float(row["slot_claim_score"]) - float(row["cohort_score_second"]), 4)
    return round(float(row["slot_claim_score"]) - float(row["cohort_score_max"]), 4)


def classify_replacement_hurdle_state(row: pd.Series) -> str:
    if int(row["bundle_assignment_ready_flag"]) == 0:
        return "research_only_not_assignment_ready"
    if int(row["blocker_edge_count"]) > 0:
        return "sector_blocker_limited"
    if int(row["cohort_size"]) == 1 and int(row["slot_replacement_hurdle_required_flag"]) == 1:
        return "active_exposure_proxy_hurdle_unresolved"
    if int(row["cohort_rank"]) == 1 and float(row["margin_vs_cohort_median"]) >= 3 and float(row["margin_vs_next_peer"]) >= 1:
        return "clear_same_timestamp_superiority"
    if int(row["cohort_rank"]) <= 3 and float(row["margin_vs_cohort_median"]) >= 0:
        return "cohort_contender_needs_confirmation"
    if int(row["edge_weak_count"]) >= 2 or int(row["interpretation_weak_count"]) >= 3:
        return "quality_gap_no_slot_claim"
    return "crowded_or_low_margin_no_edge"


def classify_slot_claim_tier(row: pd.Series) -> str:
    state = str(row["replacement_hurdle_state"])
    if state == "clear_same_timestamp_superiority":
        return "slot_leader"
    if state == "cohort_contender_needs_confirmation":
        return "slot_contender"
    if state in {"sector_blocker_limited", "active_exposure_proxy_hurdle_unresolved"}:
        return "cap_limited_or_delayed"
    return "research_only_or_no_claim"


def build_peer_reason_codes(row: pd.Series) -> str:
    return "|".join(
        [
            f"rank_scope={row['same_timestamp_rank_scope']}",
            f"cohort_size={int(row['cohort_size'])}",
            f"rank={int(row['cohort_rank'])}",
            f"margin_median={float(row['margin_vs_cohort_median']):.2f}",
            f"margin_next={float(row['margin_vs_next_peer']):.2f}",
            f"weakest={row['weakest_layer']}",
            f"blockers={int(row['blocker_edge_count'])}",
        ]
    )


def build_slot_claim_explanation_v2(competition: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in competition.iterrows():
        rows.append(
            {
                "slot_claim_explanation_v2_id": f"{row['lifecycle_id']}|slot_claim_v2",
                **identity_from_row(row),
                "cohort_id": row["cohort_id"],
                "same_timestamp_rank_scope": row["same_timestamp_rank_scope"],
                "cohort_rank": int(row["cohort_rank"]),
                "cohort_size": int(row["cohort_size"]),
                "replacement_hurdle_state": row["replacement_hurdle_state"],
                "slot_claim_tier": row["slot_claim_tier"],
                "slot_claim_score": float(row["slot_claim_score"]),
                "margin_vs_cohort_median": float(row["margin_vs_cohort_median"]),
                "margin_vs_next_peer": float(row["margin_vs_next_peer"]),
                "claim_explanation": explain_claim(row),
                "incumbent_identity_status": "not_reconstructed_active_exposure_proxy_only",
                "allowed_inputs_only_flag": 1,
                "outcome_used_flag": 0,
                "future_price_used_flag": 0,
                "label_used_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def explain_claim(row: pd.Series) -> str:
    state = str(row["replacement_hurdle_state"])
    if state == "clear_same_timestamp_superiority":
        return "Candidate leads same-timestamp cohort with enough margin and no blocker."
    if state == "cohort_contender_needs_confirmation":
        return "Candidate is competitive in same-timestamp cohort but margin or quality is not decisive."
    if state == "sector_blocker_limited":
        return "Sector-specific blocker prevents full slot claim despite score."
    if state == "active_exposure_proxy_hurdle_unresolved":
        return "Same-timestamp peer set is insufficient; active exposure proxy says replacement hurdle remains unresolved."
    if state == "quality_gap_no_slot_claim":
        return "Candidate has too many interpretation or relation edge quality gaps for slot claim."
    if state == "research_only_not_assignment_ready":
        return "Candidate is not assignment-ready."
    return "Candidate lacks enough peer-relative margin for a finite slot."


def build_slot_hurdle_decomposition(competition: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for scope, frame in [("all_candidates", competition), ("slot_hurdle_required", competition[competition["slot_replacement_hurdle_required_flag"].eq(1)])]:
        for state, group in frame.groupby("replacement_hurdle_state", dropna=False):
            rows.append(
                {
                    "scope": scope,
                    "replacement_hurdle_state": state,
                    "candidate_count": int(len(group)),
                    "avg_cohort_size": round(float(group["cohort_size"].mean()), 4) if len(group) else 0.0,
                    "avg_slot_claim_score": round(float(group["slot_claim_score"].mean()), 4) if len(group) else 0.0,
                    "leader_count": int(group["slot_claim_tier"].eq("slot_leader").sum()),
                    "contender_count": int(group["slot_claim_tier"].eq("slot_contender").sum()),
                    "research_or_no_claim_count": int(group["slot_claim_tier"].eq("research_only_or_no_claim").sum()),
                }
            )
    return pd.DataFrame(rows)


def build_integrity_audit(
    competition: pd.DataFrame,
    explanation: pd.DataFrame,
    decomposition: pd.DataFrame,
) -> pd.DataFrame:
    outputs = {
        "competition": competition,
        "explanation": explanation,
        "decomposition": decomposition,
    }
    forbidden = sorted(
        f"{name}:{col}" for name, frame in outputs.items() for col in frame.columns if col in FORBIDDEN_OBJECT_COLUMNS
    )
    hurdle = competition[competition["slot_replacement_hurdle_required_flag"].eq(1)]
    rows = [
        gate(
            "competition_panel_present",
            len(competition) > 0 and len(explanation) == len(competition),
            f"competition={len(competition)}; explanations={len(explanation)}",
            "one explanation per competition row",
        ),
        gate(
            "same_timestamp_rank_scope_only",
            competition["same_timestamp_rank_scope"].eq("same_entry_ts_split_only").all(),
            competition["same_timestamp_rank_scope"].value_counts().to_dict().__repr__(),
            "no global ranking scope",
        ),
        gate(
            "slot_hurdle_decomposed",
            hurdle["replacement_hurdle_state"].nunique() >= 3,
            f"hurdle_states={hurdle['replacement_hurdle_state'].nunique()}",
            "slot hurdle candidates should split into multiple states",
        ),
        gate(
            "no_outcome_columns_in_slot_outputs",
            len(forbidden) == 0,
            "|".join(forbidden) if forbidden else "none",
            "PnL/outcome columns excluded",
        ),
        gate(
            "no_strategy_promotion",
            True,
            "no PnL simulation or allocation rule promotion was run",
            "slot hurdle explanation only",
        ),
    ]
    return pd.DataFrame(rows)


def build_decision(competition: pd.DataFrame, decomposition: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    hurdle = competition[competition["slot_replacement_hurdle_required_flag"].eq(1)]
    return pd.DataFrame(
        [
            {
                "task_id": "Task690",
                "verdict": "SAME_TIMESTAMP_SLOT_REPLACEMENT_HURDLE_BUILT_NO_TRADING_PROMOTION",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "candidate_count": int(len(competition)),
                "slot_hurdle_required_count": int(len(hurdle)),
                "cohort_count": int(competition["cohort_id"].nunique()),
                "replacement_hurdle_state_count": int(competition["replacement_hurdle_state"].nunique()),
                "slot_leader_count": int(competition["slot_claim_tier"].eq("slot_leader").sum()),
                "slot_contender_count": int(competition["slot_claim_tier"].eq("slot_contender").sum()),
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "Slot replacement hurdle now compares candidates only within same timestamp cohorts.",
                "next_action": "Review slot leaders and contenders by cohort before any allocation backtest.",
            }
        ]
    )


def write_outputs(
    rulebook: pd.DataFrame,
    competition: pd.DataFrame,
    explanation: pd.DataFrame,
    decomposition: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> None:
    files = {
        "task690_slot_replacement_rulebook.csv": rulebook,
        "task690_cohort_slot_competition_panel.csv": competition,
        "task690_slot_claim_explanation_v2.csv": explanation,
        "task690_slot_hurdle_decomposition.csv": decomposition,
        "task690_integrity_audit.csv": audit,
        "task_690_decision.csv": decision,
        "task_690_pass_fail_matrix.csv": pass_fail,
    }
    for name, frame in files.items():
        frame.to_csv(TASK690_DIR / name, index=False)
    (TASK690_DIR / "task_690_slot_replacement_hurdle.md").write_text(
        render_report(rulebook, competition, explanation, decomposition, audit, decision, pass_fail),
        encoding="utf-8",
    )
    write_manifest(TASK690_DIR, TASK690_DIR / "artifact_manifest.csv")


def render_report(
    rulebook: pd.DataFrame,
    competition: pd.DataFrame,
    explanation: pd.DataFrame,
    decomposition: pd.DataFrame,
    audit: pd.DataFrame,
    decision: pd.DataFrame,
    pass_fail: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    state_summary = (
        competition.groupby(["replacement_hurdle_state", "slot_claim_tier"], dropna=False)
        .size()
        .reset_index(name="candidate_count")
    )
    tier_summary = competition.groupby(["slot_claim_tier"], dropna=False).size().reset_index(name="candidate_count")
    return f"""# Task690 Same-Timestamp Slot Replacement Hurdle

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Key metrics: candidates {int(d["candidate_count"])}, slot-hurdle candidates {int(d["slot_hurdle_required_count"])}, cohorts {int(d["cohort_count"])}, hurdle states {int(d["replacement_hurdle_state_count"])}.
- What changed: slot claim is now explained inside same-timestamp cohorts only.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and source readiness

Inputs are Task688 bundle/slot explanations and Task689 interpretation/edge/weak-layer panels. No new raw source is added.

### Exact join keys

- `lifecycle_id` joins all candidate-level panels.
- `cohort_id = split_name + entry_ts`.
- `cohort_rank` is valid only inside `cohort_id`.

### Leakage audit

- No PnL, win/loss, simulated exit, or future price columns are included.
- This task does not run a backtest and does not promote a trading rule.
- Existing holdings are not inferred; active exposure is marked as proxy only.

### Slot replacement rulebook

{t678.markdown_table(rulebook)}

### Hurdle state summary

{t678.markdown_table(state_summary)}

### Slot claim tier summary

{t678.markdown_table(tier_summary)}

### Hurdle decomposition

{t678.markdown_table(decomposition)}

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- Many candidates still require slot replacement proof rather than automatic entry.
- High rank inside a cohort is not enough when sector blockers or quality gaps exist.
- Single-candidate cohorts with active exposure pressure remain unresolved because incumbent identities are not reconstructed here.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Review slot leaders/contenders with source packets.
- Add actual active holding identity only through deterministic portfolio replay, not proximity matching.
- Then convert only reviewed slot states into a backtest candidate.

## No-Background Decision-Maker Report

- What happened: slot competition is now peer-relative, not global.
- Why it matters: a candidate must prove it deserves a scarce slot at that timestamp.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: inspect leaders and contenders before changing allocation.

## Artifact Manifest

- Inputs: Task688 bundle/slot objects, Task689 interpretation/edge/weak-layer panels.
- Outputs: slot replacement rulebook, cohort competition panel, slot claim explanation v2, hurdle decomposition, integrity audit, decision, pass/fail, manifest.
- Row counts: competition {len(competition)}, explanation {len(explanation)}, decomposition {len(decomposition)}.
- Validation commands: `python src/backtest/build_task690_slot_replacement_hurdle.py`; `python -m unittest tests.test_task690_slot_replacement_hurdle`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

{t678.markdown_table(pass_fail)}
"""


def identity_from_row(row: pd.Series) -> dict[str, object]:
    out = {}
    for col in IDENTITY:
        if col in row.index:
            out[col] = row[col]
        elif f"{col}_slot" in row.index:
            out[col] = row[f"{col}_slot"]
        elif f"{col}_weak" in row.index:
            out[col] = row[f"{col}_weak"]
        else:
            out[col] = ""
    return out


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
    parser.add_argument("--task688-dir", type=Path, default=TASK688_DIR)
    parser.add_argument("--task689-dir", type=Path, default=TASK689_DIR)
    args = parser.parse_args()
    build_task690_program(task688_dir=args.task688_dir, task689_dir=args.task689_dir)
    print(f"[Task690] wrote {TASK690_DIR}")


if __name__ == "__main__":
    main()
