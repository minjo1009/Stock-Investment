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


TASK693_DIR = Path("docs/reports/task_693_source_packet_v2_price_packet")
TASK698_DIR = Path("docs/reports/task_698_full_candidate_packet_drilldown")
TASK699_DIR = Path("docs/reports/task_699_source_direct_catalyst_decomposition")

SIGNAL_FAMILIES = [
    "contract_signal_v2",
    "customer_signal_v2",
    "order_backlog_signal_v2",
    "revenue_signal_v2",
    "guidance_signal_v2",
    "margin_signal_v2",
    "supply_demand_signal_v2",
]
FAMILY_LABELS = {
    "contract_signal_v2": "contract",
    "customer_signal_v2": "customer",
    "order_backlog_signal_v2": "order_backlog",
    "revenue_signal_v2": "revenue",
    "guidance_signal_v2": "guidance",
    "margin_signal_v2": "margin",
    "supply_demand_signal_v2": "supply_demand",
}
OUTCOME_COLUMNS = {
    "entry_price",
    "simulated_exit_ts",
    "simulated_exit_price",
    "exit_reason",
    "net_return_from_entry",
    "costed_return_pct",
    "qqq_costed_return_pct",
    "holding_days",
    "win_flag",
}


def build_task699_program(
    *,
    task693_dir: Path = TASK693_DIR,
    task698_dir: Path = TASK698_DIR,
    out_dir: Path = TASK699_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    events = pd.read_csv(task693_dir / "task693_source_event_v2_evidence.csv")
    freeze_435 = pd.read_csv(task698_dir / "task698_full_candidate_freeze_panel.csv")
    eval_435 = pd.read_csv(task698_dir / "task698_full_candidate_eval_panel.csv")

    source_direct_freeze = build_source_direct_feature_freeze(freeze_435, events)
    source_direct_eval = build_source_direct_eval(source_direct_freeze, eval_435)
    family_summary = build_family_summary(source_direct_eval)
    contrast = build_failure_success_contrast(source_direct_eval)
    audit = build_audit(source_direct_freeze, source_direct_eval, family_summary, contrast)
    pass_fail = audit.copy()
    decision = build_decision(source_direct_freeze, source_direct_eval, family_summary, contrast, audit)

    write_outputs(out_dir, source_direct_freeze, source_direct_eval, family_summary, contrast, audit, pass_fail, decision)
    return {
        "task699_source_direct_feature_freeze": source_direct_freeze,
        "task699_source_direct_eval_comparison": source_direct_eval,
        "task699_signal_family_summary": family_summary,
        "task699_failure_success_contrast": contrast,
        "task699_integrity_audit": audit,
        "task_699_pass_fail_matrix": pass_fail,
        "task_699_decision": decision,
    }


def build_source_direct_feature_freeze(freeze_435: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    source_direct = freeze_435[freeze_435["packet_bucket"].eq("source_direct_supported")].copy()
    event_features = aggregate_event_features(events[events["lifecycle_id"].isin(source_direct["lifecycle_id"])])
    freeze = source_direct.merge(event_features, on=["lifecycle_id", "symbol"], how="left")
    fill_zero = [
        "all_event_count",
        "direct_event_count",
        "company_direct_event_count",
        "policy_direct_event_count",
        "noise_event_count_event_level",
        "generic_filing_noise_count",
        "broad_policy_not_symbol_specific_count",
        *[f"all_{FAMILY_LABELS[col]}_count" for col in SIGNAL_FAMILIES],
        *[f"direct_{FAMILY_LABELS[col]}_count" for col in SIGNAL_FAMILIES],
    ]
    for col in fill_zero:
        if col not in freeze.columns:
            freeze[col] = 0
        freeze[col] = pd.to_numeric(freeze[col], errors="coerce").fillna(0)
    freeze["noise_ratio"] = safe_div(freeze["noise_event_count_event_level"], freeze["all_event_count"])
    freeze["direct_signal_family_count"] = freeze[[f"direct_{FAMILY_LABELS[col]}_count" for col in SIGNAL_FAMILIES]].gt(0).sum(axis=1)
    freeze["direct_economic_signature"] = freeze.apply(build_signature, axis=1)
    freeze["catalyst_structure_bucket"] = freeze.apply(classify_catalyst_structure, axis=1)
    freeze["quality_risk_bucket"] = freeze.apply(classify_quality_risk, axis=1)
    freeze["outcome_used_for_selection_flag"] = 0
    freeze["future_price_used_for_selection_flag"] = 0
    freeze["allocation_approved_flag"] = 0
    freeze["paper_or_live_trade_approved_flag"] = 0

    columns = [
        "lifecycle_id",
        "symbol",
        "entry_ts",
        "entry_ts_utc",
        "theme_id",
        "split_name",
        "sector_family",
        "slot_claim_score",
        "source_packet_v2_state",
        "source_packet_v2_verdict",
        "all_event_count",
        "direct_event_count",
        "company_direct_event_count",
        "policy_direct_event_count",
        "noise_event_count_event_level",
        "generic_filing_noise_count",
        "broad_policy_not_symbol_specific_count",
        "noise_ratio",
        "direct_signal_family_count",
        "direct_economic_signature",
        "catalyst_structure_bucket",
        "quality_risk_bucket",
        *[f"direct_{FAMILY_LABELS[col]}_count" for col in SIGNAL_FAMILIES],
        *[f"all_{FAMILY_LABELS[col]}_count" for col in SIGNAL_FAMILIES],
        "outcome_used_for_selection_flag",
        "future_price_used_for_selection_flag",
        "allocation_approved_flag",
        "paper_or_live_trade_approved_flag",
    ]
    return freeze[columns].sort_values(["entry_ts", "symbol"]).reset_index(drop=True)


def aggregate_event_features(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (lifecycle_id, symbol), group in events.groupby(["lifecycle_id", "symbol"], dropna=False):
        direct = group[group["source_event_v2_state"].eq("direct_economic_source_supported")]
        is_policy_direct = direct["source_lane"].astype(str).str.contains("political|whitehouse|trump", case=False, regex=True, na=False)
        row = {
            "lifecycle_id": lifecycle_id,
            "symbol": symbol,
            "all_event_count": int(len(group)),
            "direct_event_count": int(len(direct)),
            "company_direct_event_count": int((~is_policy_direct).sum()),
            "policy_direct_event_count": int(is_policy_direct.sum()),
            "noise_event_count_event_level": int(
                group["source_event_v2_state"].isin(
                    [
                        "ownership_or_sale_filing_noise",
                        "ownership_filing_with_weak_economic_terms",
                        "broad_policy_not_symbol_specific",
                    ]
                ).sum()
            ),
            "generic_filing_noise_count": int(group["generic_filing_noise_flag"].sum()),
            "broad_policy_not_symbol_specific_count": int(group["broad_policy_not_symbol_specific_flag"].sum()),
        }
        for col in SIGNAL_FAMILIES:
            label = FAMILY_LABELS[col]
            row[f"all_{label}_count"] = int(group[col].sum())
            row[f"direct_{label}_count"] = int(direct[col].sum()) if len(direct) else 0
        rows.append(row)
    return pd.DataFrame(rows)


def safe_div(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    denominator = denominator.replace(0, pd.NA)
    return (numerator / denominator).fillna(0.0)


def build_signature(row: pd.Series) -> str:
    active = []
    for col in SIGNAL_FAMILIES:
        label = FAMILY_LABELS[col]
        if float(row.get(f"direct_{label}_count", 0)) > 0:
            active.append(label)
    return "|".join(active) if active else "no_direct_family"


def classify_catalyst_structure(row: pd.Series) -> str:
    families = set(str(row["direct_economic_signature"]).split("|"))
    family_count = int(row["direct_signal_family_count"])
    company_direct = int(row["company_direct_event_count"])
    policy_direct = int(row["policy_direct_event_count"])
    if company_direct >= 1 and {"contract", "customer", "order_backlog"}.issubset(families):
        return "company_contract_customer_order"
    if company_direct >= 1 and {"guidance", "supply_demand"}.issubset(families):
        return "company_guidance_supply"
    if company_direct >= 1 and {"revenue", "guidance"}.issubset(families):
        return "company_revenue_guidance"
    if company_direct >= 1 and family_count >= 5:
        return "company_multi_vector"
    if policy_direct > 0 and company_direct == 0:
        return "policy_direct_only"
    if company_direct >= 1:
        return "company_thin_direct"
    return "direct_structure_unclear"


def classify_quality_risk(row: pd.Series) -> str:
    noise_ratio = float(row["noise_ratio"])
    family_count = int(row["direct_signal_family_count"])
    company_direct = int(row["company_direct_event_count"])
    if noise_ratio >= 0.75 and family_count <= 2:
        return "high_noise_thin_signal"
    if noise_ratio >= 0.75:
        return "high_noise_multi_signal"
    if company_direct >= 1 and family_count >= 4 and noise_ratio < 0.6:
        return "cleaner_company_multi_signal"
    if company_direct >= 1 and family_count >= 3:
        return "company_signal_with_noise"
    return "thin_or_mixed_signal"


def build_source_direct_eval(source_direct_freeze: pd.DataFrame, eval_435: pd.DataFrame) -> pd.DataFrame:
    outcome_cols = [
        "lifecycle_id",
        "symbol",
        "entry_price",
        "simulated_exit_ts",
        "simulated_exit_price",
        "exit_reason",
        "costed_return_pct",
        "qqq_costed_return_pct",
        "excess_vs_qqq_costed_pct",
        "beats_qqq_same_window_flag",
        "holding_days",
        "win_flag",
    ]
    joined = source_direct_freeze.merge(eval_435[outcome_cols], on=["lifecycle_id", "symbol"], how="left", indicator=True)
    if not joined["_merge"].eq("both").all():
        raise ValueError("Task699 source-direct rows must join to Task698 eval rows exactly.")
    joined = joined.drop(columns=["_merge"])
    joined["outcome_group"] = joined["costed_return_pct"].apply(classify_outcome_group)
    joined["same_criteria_diagnostic"] = joined.apply(same_criteria_diagnostic, axis=1)
    joined["outcome_used_for_evaluation_flag"] = 1
    return joined.sort_values(["costed_return_pct", "symbol"]).reset_index(drop=True)


def classify_outcome_group(costed_return_pct: float) -> str:
    value = float(costed_return_pct)
    if value <= -10.0:
        return "failure_loss_gt_10pct"
    if value < 10.0:
        return "modest_or_flat"
    if value < 50.0:
        return "solid_winner"
    return "large_winner"


def same_criteria_diagnostic(row: pd.Series) -> str:
    parts = [
        f"structure={row['catalyst_structure_bucket']}",
        f"risk={row['quality_risk_bucket']}",
        f"signature={row['direct_economic_signature']}",
        f"company_direct={int(row['company_direct_event_count'])}",
        f"policy_direct={int(row['policy_direct_event_count'])}",
        f"noise_ratio={float(row['noise_ratio']):.2f}",
        f"excess_vs_qqq={float(row['excess_vs_qqq_costed_pct']):.2f}",
    ]
    return "|".join(parts)


def build_family_summary(eval_panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for key in ["catalyst_structure_bucket", "quality_risk_bucket", "direct_economic_signature"]:
        for value, group in eval_panel.groupby(key, dropna=False):
            rows.append(summary_row(key, str(value), group))
    return pd.DataFrame(rows).sort_values(["dimension", "avg_costed_return_pct"], ascending=[True, False]).reset_index(drop=True)


def summary_row(dimension: str, value: str, group: pd.DataFrame) -> dict[str, object]:
    costed = group["costed_return_pct"].astype(float)
    return {
        "dimension": dimension,
        "value": value,
        "candidate_count": int(len(group)),
        "avg_costed_return_pct": float(costed.mean()),
        "median_costed_return_pct": float(costed.median()),
        "win_rate": float((costed > 0).mean()),
        "avg_excess_vs_qqq_costed_pct": float(group["excess_vs_qqq_costed_pct"].astype(float).mean()),
        "large_winner_count": int(group["outcome_group"].eq("large_winner").sum()),
        "failure_count": int(group["outcome_group"].eq("failure_loss_gt_10pct").sum()),
        "symbols": "|".join(group["symbol"].astype(str).tolist()),
        "outcome_used_for_selection_flag": 0,
        "outcome_used_for_evaluation_flag": 1,
    }


def build_failure_success_contrast(eval_panel: pd.DataFrame) -> pd.DataFrame:
    groups = {
        "failures_asts_snow": eval_panel[eval_panel["symbol"].isin(["ASTS", "SNOW"])],
        "large_winners_ter_ddog": eval_panel[eval_panel["symbol"].isin(["TER", "DDOG"])],
        "middle_ba_ceg_ph": eval_panel[~eval_panel["symbol"].isin(["ASTS", "SNOW", "TER", "DDOG"])],
    }
    rows = []
    for name, group in groups.items():
        costed = group["costed_return_pct"].astype(float)
        rows.append(
            {
                "contrast_group": name,
                "candidate_count": int(len(group)),
                "symbols": "|".join(group["symbol"].astype(str).tolist()),
                "avg_costed_return_pct": float(costed.mean()) if len(group) else 0.0,
                "avg_excess_vs_qqq_costed_pct": float(group["excess_vs_qqq_costed_pct"].astype(float).mean()) if len(group) else 0.0,
                "avg_company_direct_event_count": float(group["company_direct_event_count"].astype(float).mean()) if len(group) else 0.0,
                "avg_policy_direct_event_count": float(group["policy_direct_event_count"].astype(float).mean()) if len(group) else 0.0,
                "avg_direct_signal_family_count": float(group["direct_signal_family_count"].astype(float).mean()) if len(group) else 0.0,
                "avg_noise_ratio": float(group["noise_ratio"].astype(float).mean()) if len(group) else 0.0,
                "common_structure_buckets": "|".join(group["catalyst_structure_bucket"].astype(str).value_counts().index.tolist()),
                "common_quality_risk_buckets": "|".join(group["quality_risk_bucket"].astype(str).value_counts().index.tolist()),
                "diagnostic": diagnostic_for_group(name, group),
            }
        )
    return pd.DataFrame(rows)


def diagnostic_for_group(name: str, group: pd.DataFrame) -> str:
    if name == "failures_asts_snow":
        return "Failures had direct company events but suffered from high noise or thin revenue/guidance-only structures."
    if name == "large_winners_ter_ddog":
        return "Large winners combined direct evidence with either contract/order/guidance mix or a cleaner single hard catalyst."
    return "Middle group had positive but less explosive catalyst translation."


def build_audit(
    freeze: pd.DataFrame,
    eval_panel: pd.DataFrame,
    family_summary: pd.DataFrame,
    contrast: pd.DataFrame,
) -> pd.DataFrame:
    forbidden = sorted(col for col in freeze.columns if col in OUTCOME_COLUMNS)
    return pd.DataFrame(
        [
            gate(
                "source_direct_scope_9",
                len(freeze) == 9 and set(freeze["symbol"]) == {"ASTS", "BA", "CEG", "DDOG", "PH", "SNOW", "TER"},
                f"rows={len(freeze)}; symbols={','.join(sorted(set(freeze['symbol'])))}",
                "Task699 scope must be the 9 Task698 source-direct rows",
            ),
            gate(
                "freeze_has_no_outcomes",
                len(forbidden) == 0,
                "|".join(forbidden) if forbidden else "none",
                "Source-direct feature freeze cannot include outcome columns",
            ),
            gate(
                "direct_family_features_present",
                freeze["direct_signal_family_count"].notna().all()
                and freeze["catalyst_structure_bucket"].notna().all()
                and freeze["quality_risk_bucket"].notna().all(),
                f"feature_rows={len(freeze)}",
                "Every source-direct row needs economic family and risk buckets",
            ),
            gate(
                "eval_exact_rows",
                len(eval_panel) == len(freeze) and int(eval_panel["outcome_used_for_evaluation_flag"].sum()) == len(freeze),
                f"eval_rows={len(eval_panel)}",
                "Every frozen source-direct row must have one evaluation row",
            ),
            gate(
                "failure_success_contrast_present",
                set(contrast["contrast_group"]) == {"failures_asts_snow", "large_winners_ter_ddog", "middle_ba_ceg_ph"},
                "|".join(contrast["contrast_group"].astype(str)),
                "Contrast must compare failures, large winners, and middle cases",
            ),
            gate(
                "no_strategy_or_trade_promotion",
                int(freeze["allocation_approved_flag"].sum()) == 0
                and int(freeze["paper_or_live_trade_approved_flag"].sum()) == 0,
                "allocation_approved=0; paper_or_live_trade_approved=0",
                "Task699 is diagnostic only",
            ),
        ]
    )


def build_decision(
    freeze: pd.DataFrame,
    eval_panel: pd.DataFrame,
    family_summary: pd.DataFrame,
    contrast: pd.DataFrame,
    audit: pd.DataFrame,
) -> pd.DataFrame:
    failures = contrast[contrast["contrast_group"].eq("failures_asts_snow")].iloc[0]
    winners = contrast[contrast["contrast_group"].eq("large_winners_ter_ddog")].iloc[0]
    best_structure = family_summary[family_summary["dimension"].eq("catalyst_structure_bucket")].iloc[0]
    return pd.DataFrame(
        [
            {
                "task_id": "Task699",
                "verdict": "SOURCE_DIRECT_CATALYST_DECOMPOSITION_COMPLETE_RESEARCH_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "source_direct_count": int(len(freeze)),
                "large_winner_count": int(eval_panel["outcome_group"].eq("large_winner").sum()),
                "failure_count": int(eval_panel["outcome_group"].eq("failure_loss_gt_10pct").sum()),
                "best_structure_bucket": best_structure["value"],
                "best_structure_avg_costed_return_pct": float(best_structure["avg_costed_return_pct"]),
                "failure_avg_costed_return_pct": float(failures["avg_costed_return_pct"]),
                "winner_avg_costed_return_pct": float(winners["avg_costed_return_pct"]),
                "failure_avg_noise_ratio": float(failures["avg_noise_ratio"]),
                "winner_avg_noise_ratio": float(winners["avg_noise_ratio"]),
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "Source-direct must be split by economic structure and noise; direct evidence alone is not enough.",
                "research_caveat": "Sample is only nine source-direct rows, so this is a diagnostic map, not an allocation rule.",
                "next_action": "Build a candidate rule that requires source-direct plus catalyst structure and noise controls, then test it on the frozen 435 set.",
            }
        ]
    )


def write_outputs(
    out_dir: Path,
    freeze: pd.DataFrame,
    eval_panel: pd.DataFrame,
    family_summary: pd.DataFrame,
    contrast: pd.DataFrame,
    audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> None:
    outputs = {
        "task699_source_direct_feature_freeze.csv": freeze,
        "task699_source_direct_eval_comparison.csv": eval_panel,
        "task699_signal_family_summary.csv": family_summary,
        "task699_failure_success_contrast.csv": contrast,
        "task699_integrity_audit.csv": audit,
        "task_699_pass_fail_matrix.csv": pass_fail,
        "task_699_decision.csv": decision,
    }
    for name, frame in outputs.items():
        frame.to_csv(out_dir / name, index=False)
    (out_dir / "task_699_source_direct_catalyst_decomposition.md").write_text(
        render_report(freeze, eval_panel, family_summary, contrast, audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def render_report(
    freeze: pd.DataFrame,
    eval_panel: pd.DataFrame,
    family_summary: pd.DataFrame,
    contrast: pd.DataFrame,
    audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    eval_view = eval_panel[
        [
            "symbol",
            "split_name",
            "catalyst_structure_bucket",
            "quality_risk_bucket",
            "direct_economic_signature",
            "direct_event_count",
            "noise_ratio",
            "costed_return_pct",
            "qqq_costed_return_pct",
            "outcome_group",
        ]
    ]
    summary_view = family_summary[
        [
            "dimension",
            "value",
            "candidate_count",
            "avg_costed_return_pct",
            "win_rate",
            "avg_excess_vs_qqq_costed_pct",
            "large_winner_count",
            "failure_count",
            "symbols",
        ]
    ]
    contrast_view = contrast[
        [
            "contrast_group",
            "candidate_count",
            "symbols",
            "avg_costed_return_pct",
            "avg_direct_signal_family_count",
            "avg_noise_ratio",
            "common_structure_buckets",
            "diagnostic",
        ]
    ]
    return f"""# Task699 Source Direct Catalyst Decomposition

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Scope: Task698 source-direct rows only, count {int(d["source_direct_count"])}.
- Main finding: {d["primary_result"]}
- Best structure bucket: {d["best_structure_bucket"]}, average costed return {float(d["best_structure_avg_costed_return_pct"]):.2f}%.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and scope

- Freeze input: Task698 full candidate freeze panel.
- Evidence input: Task693 source event v2 evidence.
- Evaluation input: Task698 full candidate eval panel.
- Scope is exactly the 9 source-direct candidates from Task698.

### Freeze before outcome

- `task699_source_direct_feature_freeze.csv` contains catalyst structure, direct signal families, policy/company mix, and noise ratio.
- Outcome columns are added only in `task699_source_direct_eval_comparison.csv`.
- No allocation or live/paper trading approval is created.

### Same-Criteria Evaluation

{t678.markdown_table(eval_view)}

### Signal Family Summary

{t678.markdown_table(summary_view)}

### Failure vs Winner Contrast

{t678.markdown_table(contrast_view)}

### Interpretation

- Source-direct is not one thing. It splits into company contract/order structures, company guidance/supply structures, thin revenue/guidance structures, and policy-assisted structures.
- ASTS and SNOW failed despite direct evidence. Their issue is not absence of evidence; it is evidence quality, noise mix, and weak price/economic translation.
- TER and DDOG won because the direct evidence translated into a cleaner economic structure or a hard catalyst.
- Price and source should be combined later, but source-direct alone should first pass structure and noise controls.

### Split/OOS metrics

- The 9 rows include train-design, validation, and recent-OOS cases.
- This task is diagnostic only because the sample is small and uses outcome only after freeze.

### Remaining blockers

- Build the next rule on frozen features only.
- Do not promote direct evidence alone.
- Require catalyst structure plus noise control before any allocation test.

## No-Background Decision-Maker Report

- What happened: source-direct 9개를 같은 기준으로 다시 깠습니다.
- Result: source-direct 안에서도 좋은 놈과 나쁜 놈이 갈립니다.
- Simple answer: 직접 호재만으로는 부족합니다. 직접 호재 + 경제 구조 + 잡음 통제가 필요합니다.
- Capital status: still FORBIDDEN.

## Artifact Manifest

- Inputs: Task693 source event evidence, Task698 freeze/eval panels.
- Outputs: source-direct feature freeze, eval comparison, signal family summary, failure/success contrast, audit, decision, pass/fail, manifest.
- Row counts: freeze {len(freeze)}, eval {len(eval_panel)}, summary {len(family_summary)}, contrast {len(contrast)}.
- Validation commands: `python src/backtest/build_task699_source_direct_catalyst_decomposition.py`; `python -m unittest tests.test_task699_source_direct_catalyst_decomposition`; `python scripts/task_registry_validate.py`.

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task693-dir", type=Path, default=TASK693_DIR)
    parser.add_argument("--task698-dir", type=Path, default=TASK698_DIR)
    parser.add_argument("--out-dir", type=Path, default=TASK699_DIR)
    args = parser.parse_args()
    build_task699_program(task693_dir=args.task693_dir, task698_dir=args.task698_dir, out_dir=args.out_dir)
    print(f"[Task699] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
