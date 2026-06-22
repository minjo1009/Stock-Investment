from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.task_artifact_manifest import write_manifest
from src.backtest import build_task678_active_cap3_winner_archetype as t678
from src.backtest.build_task618_1000_capital_portfolio_comparison import simulate_deterministic_portfolio
from src.backtest.build_task697_tiny_candidate_pnl_test import INITIAL_CAPITAL_USD, ROUND_TRIP_COST_BPS


TASK698_DIR = Path("docs/reports/task_698_full_candidate_packet_drilldown")
TASK699_DIR = Path("docs/reports/task_699_source_direct_catalyst_decomposition")
TASK693_DIR = Path("docs/reports/task_693_source_packet_v2_price_packet")
TASK684_PANEL = Path("docs/reports/task_684_interaction_context_prediction_stack/task684_interaction_stack_panel.csv")
TASK701_DIR = Path("docs/reports/task_701_conflict_aware_source_direct_rule")

FINANCING_PATTERN = re.compile(
    r"private offering|convertible senior notes|senior notes due|indenture and notes|"
    r"capped call|note purchase agreement|convertible notes|aggregate principal amount",
    flags=re.IGNORECASE,
)
REAFFIRM_PATTERN = re.compile(
    r"reaffirm|reaffirmed|reaffirms|previously issued|previous guidance|not rely|unauthorized",
    flags=re.IGNORECASE,
)
CONTEXT_COLUMNS = [
    "lifecycle_id",
    "symbol",
    "price_acceptance_score",
    "price_acceptance_state",
    "price_chart_acceptance_state",
    "catalyst_absorption_state",
    "catalyst_priced_in_state",
    "volume_ratio_prev",
]


def build_task701_program(
    *,
    task698_dir: Path = TASK698_DIR,
    task699_dir: Path = TASK699_DIR,
    task693_dir: Path = TASK693_DIR,
    task684_panel_path: Path = TASK684_PANEL,
    out_dir: Path = TASK701_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    freeze_435 = pd.read_csv(task698_dir / "task698_full_candidate_freeze_panel.csv")
    eval_435 = pd.read_csv(task698_dir / "task698_full_candidate_eval_panel.csv")
    source_direct_features = pd.read_csv(task699_dir / "task699_source_direct_feature_freeze.csv")
    events = pd.read_csv(task693_dir / "task693_source_event_v2_evidence.csv")
    context = pd.read_csv(task684_panel_path, usecols=CONTEXT_COLUMNS)

    rule_freeze = build_rule_freeze(freeze_435, source_direct_features, events, context)
    rule_eval = build_rule_eval(rule_freeze, eval_435)
    action_summary = build_action_summary(rule_eval)
    portfolio_comparison = build_portfolio_comparison(rule_eval)
    audit = build_audit(rule_freeze, rule_eval, action_summary, portfolio_comparison)
    pass_fail = audit.copy()
    decision = build_decision(rule_freeze, rule_eval, action_summary, portfolio_comparison, audit)
    write_outputs(out_dir, rule_freeze, rule_eval, action_summary, portfolio_comparison, audit, pass_fail, decision)
    return {
        "task701_rule_freeze_panel": rule_freeze,
        "task701_rule_eval_panel": rule_eval,
        "task701_action_summary": action_summary,
        "task701_portfolio_comparison": portfolio_comparison,
        "task701_integrity_audit": audit,
        "task_701_pass_fail_matrix": pass_fail,
        "task_701_decision": decision,
    }


def build_rule_freeze(
    freeze_435: pd.DataFrame,
    source_direct_features: pd.DataFrame,
    events: pd.DataFrame,
    context: pd.DataFrame,
) -> pd.DataFrame:
    source_cols = [
        "lifecycle_id",
        "symbol",
        "direct_event_count",
        "noise_ratio",
        "direct_signal_family_count",
        "direct_economic_signature",
        "catalyst_structure_bucket",
        "quality_risk_bucket",
    ]
    out = freeze_435.merge(source_direct_features[source_cols], on=["lifecycle_id", "symbol"], how="left")
    out = out.merge(build_text_flags(events), on=["lifecycle_id", "symbol"], how="left")
    out = out.drop(columns=[col for col in CONTEXT_COLUMNS if col not in {"lifecycle_id", "symbol"} and col in out.columns])
    out = out.merge(context, on=["lifecycle_id", "symbol"], how="left")
    for col in ["financing_overhang_flag", "guidance_reaffirm_flag", "direct_event_count", "noise_ratio", "price_acceptance_score", "volume_ratio_prev"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    out["high_noise_thin_signal_flag"] = (
        out["packet_bucket"].eq("source_direct_supported")
        & out["noise_ratio"].ge(0.75)
        & out["direct_event_count"].le(1)
    ).astype(int)
    out["price_absorption_confirmation_flag"] = (
        out["packet_bucket"].eq("source_direct_supported")
        & out["price_acceptance_score"].ge(6)
        & out["volume_ratio_prev"].ge(1.0)
        & out["price_chart_acceptance_state"].astype(str).str.contains("price_confirmed", na=False)
    ).astype(int)
    out["conflict_aware_action"] = out.apply(classify_action, axis=1)
    out["conflict_aware_eligible_flag"] = out["conflict_aware_action"].eq("ELIGIBLE_RULE_CANDIDATE").astype(int)
    out["outcome_used_for_selection_flag"] = 0
    out["future_price_used_for_selection_flag"] = 0
    out["allocation_approved_flag"] = 0
    out["paper_or_live_trade_approved_flag"] = 0
    columns = [
        "lifecycle_id",
        "symbol",
        "entry_ts",
        "entry_ts_utc",
        "theme_id",
        "split_name",
        "packet_bucket",
        "source_packet_v2_state",
        "direct_economic_signature",
        "catalyst_structure_bucket",
        "quality_risk_bucket",
        "direct_event_count",
        "noise_ratio",
        "financing_overhang_flag",
        "guidance_reaffirm_flag",
        "high_noise_thin_signal_flag",
        "price_acceptance_score",
        "price_chart_acceptance_state",
        "volume_ratio_prev",
        "price_absorption_confirmation_flag",
        "conflict_aware_action",
        "conflict_aware_eligible_flag",
        "outcome_used_for_selection_flag",
        "future_price_used_for_selection_flag",
        "allocation_approved_flag",
        "paper_or_live_trade_approved_flag",
    ]
    return out[columns].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def build_text_flags(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (lifecycle_id, symbol), group in events.groupby(["lifecycle_id", "symbol"], dropna=False):
        text = " ".join(group[["event_title", "evidence_snippet"]].fillna("").astype(str).to_numpy().ravel().tolist())
        for path_value in group["raw_text_path"].dropna().unique():
            path = Path(str(path_value))
            if not path.is_absolute():
                path = ROOT / path
            try:
                text += " " + path.read_text(encoding="utf-8", errors="ignore")[:50000]
            except OSError:
                pass
        rows.append(
            {
                "lifecycle_id": lifecycle_id,
                "symbol": symbol,
                "financing_overhang_flag": int(FINANCING_PATTERN.search(text) is not None),
                "guidance_reaffirm_flag": int(REAFFIRM_PATTERN.search(text) is not None),
            }
        )
    return pd.DataFrame(rows)


def classify_action(row: pd.Series) -> str:
    if row["packet_bucket"] != "source_direct_supported":
        return "RESEARCH_ONLY_NOT_SOURCE_DIRECT"
    if int(row["financing_overhang_flag"]) == 1:
        return "CONFIRMATION_REQUIRED_FINANCING"
    if int(row["guidance_reaffirm_flag"]) == 1:
        return "CONFIRMATION_REQUIRED_REAFFIRM"
    if int(row["high_noise_thin_signal_flag"]) == 1 and int(row["price_absorption_confirmation_flag"]) == 0:
        return "CONFIRMATION_REQUIRED_HIGH_NOISE"
    if int(row["price_absorption_confirmation_flag"]) == 0:
        return "CONFIRMATION_REQUIRED_PRICE"
    return "ELIGIBLE_RULE_CANDIDATE"


def build_rule_eval(rule_freeze: pd.DataFrame, eval_435: pd.DataFrame) -> pd.DataFrame:
    eval_cols = [
        "lifecycle_id",
        "symbol",
        "entry_price",
        "simulated_exit_ts",
        "simulated_exit_price",
        "exit_reason",
        "holding_days",
        "costed_return_pct",
        "qqq_costed_return_pct",
        "excess_vs_qqq_costed_pct",
        "beats_qqq_same_window_flag",
        "win_flag",
        "add_scale_success_flag",
        "entry_reduce_failure_flag",
        "false_positive_flag",
        "same_day_exit_flag",
    ]
    joined = rule_freeze.merge(eval_435[eval_cols], on=["lifecycle_id", "symbol"], how="left", indicator=True)
    if not joined["_merge"].eq("both").all():
        raise ValueError("Task701 all frozen rows must join to Task698 eval rows.")
    joined = joined.drop(columns=["_merge"])
    joined["outcome_used_for_evaluation_flag"] = 1
    return joined


def build_action_summary(rule_eval: pd.DataFrame) -> pd.DataFrame:
    rows = []
    source = rule_eval[rule_eval["packet_bucket"].eq("source_direct_supported")]
    for action, group in source.groupby("conflict_aware_action", dropna=False):
        costed = group["costed_return_pct"].astype(float)
        rows.append(
            {
                "conflict_aware_action": action,
                "candidate_count": int(len(group)),
                "symbols": "|".join(group["symbol"].astype(str).tolist()),
                "avg_costed_return_pct": float(costed.mean()),
                "median_costed_return_pct": float(costed.median()),
                "win_rate": float((costed > 0).mean()),
                "avg_excess_vs_qqq_costed_pct": float(group["excess_vs_qqq_costed_pct"].astype(float).mean()),
                "outcome_used_for_selection_flag": 0,
                "outcome_used_for_evaluation_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values("avg_costed_return_pct", ascending=False).reset_index(drop=True)


def build_portfolio_comparison(rule_eval: pd.DataFrame) -> pd.DataFrame:
    source = rule_eval[rule_eval["packet_bucket"].eq("source_direct_supported")].copy()
    eligible = rule_eval[rule_eval["conflict_aware_eligible_flag"].eq(1)].copy()
    rows = []
    for cohort_name, panel in [
        ("source_direct_original_9", source),
        ("conflict_aware_eligible_4", eligible),
    ]:
        sim = panel.copy()
        sim["net_return_from_entry"] = sim["costed_return_pct"].astype(float) / 100.0
        for max_positions in [1, 3, 5, 10]:
            quality, accepted, _curve = simulate_deterministic_portfolio(sim, max_positions=max_positions)
            rows.append(
                {
                    "portfolio_cohort": cohort_name,
                    "max_positions": int(max_positions),
                    "source_candidate_count": int(len(sim)),
                    "accepted_trade_count": int(len(accepted)),
                    "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
                    "initial_capital_usd": INITIAL_CAPITAL_USD,
                    "final_capital_usd": INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0),
                    "capital_return_pct": float(quality["capital_pnl_pct"]),
                    "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                    "strategy_acceptance_status": "NOT_ACCEPTED",
                    "real_capital_status": "FORBIDDEN",
                }
            )
    return pd.DataFrame(rows)


def build_audit(
    rule_freeze: pd.DataFrame,
    rule_eval: pd.DataFrame,
    action_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate(
                "freeze_scope_435",
                len(rule_freeze) == 435,
                f"rows={len(rule_freeze)}",
                "Task701 rule is applied to the full Task698 frozen 435 rows",
            ),
            gate(
                "source_direct_action_scope_9",
                int(rule_freeze["packet_bucket"].eq("source_direct_supported").sum()) == 9,
                f"source_direct={int(rule_freeze['packet_bucket'].eq('source_direct_supported').sum())}",
                "Source-direct action scope remains 9",
            ),
            gate(
                "eligible_count_4",
                int(rule_freeze["conflict_aware_eligible_flag"].sum()) == 4,
                f"eligible={int(rule_freeze['conflict_aware_eligible_flag'].sum())}",
                "Conflict-aware eligible rows should be CEG, CEG, DDOG, TER",
            ),
            gate(
                "asts_snow_blocked",
                rule_freeze[rule_freeze["symbol"].isin(["ASTS", "SNOW"])]["conflict_aware_eligible_flag"].sum() == 0,
                "ASTS/SNOW eligible count=0",
                "ASTS and SNOW should require confirmation, not immediate eligibility",
            ),
            gate(
                "eval_rows_complete",
                len(rule_eval) == len(rule_freeze) and int(rule_eval["outcome_used_for_evaluation_flag"].sum()) == len(rule_freeze),
                f"eval_rows={len(rule_eval)}",
                "All frozen rows must be evaluation-joined after selection",
            ),
            gate(
                "portfolio_comparison_present",
                set(portfolio_comparison["portfolio_cohort"]) == {"source_direct_original_9", "conflict_aware_eligible_4"},
                "|".join(sorted(set(portfolio_comparison["portfolio_cohort"]))),
                "Portfolio comparison must include original source-direct and conflict-aware eligible cohorts",
            ),
            gate(
                "no_strategy_or_trade_promotion",
                int(rule_freeze["allocation_approved_flag"].sum()) == 0
                and int(rule_freeze["paper_or_live_trade_approved_flag"].sum()) == 0,
                "allocation_approved=0; paper_or_live_trade_approved=0",
                "Task701 is still research-only",
            ),
        ]
    )


def build_decision(
    rule_freeze: pd.DataFrame,
    rule_eval: pd.DataFrame,
    action_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
    audit: pd.DataFrame,
) -> pd.DataFrame:
    eligible_summary = action_summary[action_summary["conflict_aware_action"].eq("ELIGIBLE_RULE_CANDIDATE")].iloc[0]
    eligible_max5 = portfolio_row(portfolio_comparison, "conflict_aware_eligible_4", 5)
    original_max5 = portfolio_row(portfolio_comparison, "source_direct_original_9", 5)
    return pd.DataFrame(
        [
            {
                "task_id": "Task701",
                "verdict": "CONFLICT_AWARE_SOURCE_DIRECT_RULE_TEST_COMPLETE_RESEARCH_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "full_freeze_count": int(len(rule_freeze)),
                "source_direct_count": int(rule_freeze["packet_bucket"].eq("source_direct_supported").sum()),
                "eligible_count": int(rule_freeze["conflict_aware_eligible_flag"].sum()),
                "eligible_symbols": "|".join(rule_freeze[rule_freeze["conflict_aware_eligible_flag"].eq(1)]["symbol"].astype(str).tolist()),
                "eligible_avg_costed_return_pct": float(eligible_summary["avg_costed_return_pct"]),
                "eligible_win_rate": float(eligible_summary["win_rate"]),
                "original_source_direct_max5_final_capital_usd": float(original_max5["final_capital_usd"]),
                "eligible_max5_final_capital_usd": float(eligible_max5["final_capital_usd"]),
                "eligible_max5_return_pct": float(eligible_max5["capital_return_pct"]),
                "eligible_max5_mdd_pct": float(eligible_max5["max_drawdown_pct"]),
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "Conflict-aware source-direct rule blocks ASTS/SNOW and keeps CEG, CEG, DDOG, TER in this diagnostic replay.",
                "research_caveat": "This is a post-diagnosis research rule on a 9-row source-direct subset, not a deployable strategy.",
                "next_action": "Run the same axes across all source packets, not just current source-direct rows, before any broader allocation test.",
            }
        ]
    )


def portfolio_row(portfolio_comparison: pd.DataFrame, cohort: str, max_positions: int) -> pd.Series:
    return portfolio_comparison[
        portfolio_comparison["portfolio_cohort"].eq(cohort) & portfolio_comparison["max_positions"].eq(max_positions)
    ].iloc[0]


def write_outputs(
    out_dir: Path,
    rule_freeze: pd.DataFrame,
    rule_eval: pd.DataFrame,
    action_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
    audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> None:
    outputs = {
        "task701_rule_freeze_panel.csv": rule_freeze,
        "task701_rule_eval_panel.csv": rule_eval,
        "task701_action_summary.csv": action_summary,
        "task701_portfolio_comparison.csv": portfolio_comparison,
        "task701_integrity_audit.csv": audit,
        "task_701_pass_fail_matrix.csv": pass_fail,
        "task_701_decision.csv": decision,
    }
    for name, frame in outputs.items():
        frame.to_csv(out_dir / name, index=False)
    (out_dir / "task_701_conflict_aware_source_direct_rule.md").write_text(
        render_report(rule_freeze, rule_eval, action_summary, portfolio_comparison, audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def render_report(
    rule_freeze: pd.DataFrame,
    rule_eval: pd.DataFrame,
    action_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
    audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    source_view = rule_eval[rule_eval["packet_bucket"].eq("source_direct_supported")][
        [
            "symbol",
            "split_name",
            "financing_overhang_flag",
            "guidance_reaffirm_flag",
            "high_noise_thin_signal_flag",
            "price_absorption_confirmation_flag",
            "conflict_aware_action",
            "costed_return_pct",
            "qqq_costed_return_pct",
        ]
    ]
    portfolio_view = portfolio_comparison[
        [
            "portfolio_cohort",
            "max_positions",
            "source_candidate_count",
            "accepted_trade_count",
            "final_capital_usd",
            "capital_return_pct",
            "max_drawdown_pct",
        ]
    ]
    return f"""# Task701 Conflict-Aware Source Direct Rule

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Scope: full Task698 freeze {int(d["full_freeze_count"])} rows, source-direct {int(d["source_direct_count"])} rows.
- Eligible symbols: {d["eligible_symbols"]}.
- Key $1,000 max5: original source-direct ${float(d["original_source_direct_max5_final_capital_usd"]):,.2f}; conflict-aware eligible ${float(d["eligible_max5_final_capital_usd"]):,.2f}.
- Main finding: {d["primary_result"]}
- Next action: {d["next_action"]}

## Quant Expert Report

### Rule Design

- Block immediate eligibility when `financing_overhang_flag=1`.
- Block immediate eligibility when `guidance_reaffirm_flag=1`.
- High-noise thin signals require price absorption confirmation.
- Every eligible source-direct row must have price acceptance score >= 6, volume ratio >= 1, and a confirmed price chart state.

### Source Direct Action Table

{t678.markdown_table(source_view)}

### Action Summary

{t678.markdown_table(action_summary)}

### Portfolio Comparison

{t678.markdown_table(portfolio_view)}

### Interpretation

- The rule blocks the exact two failure types found in Task700: ASTS financing overhang and SNOW reaffirm/high-noise thin signal.
- It keeps CEG, CEG, DDOG, and TER.
- This improves the diagnostic source-direct subset, but it is still too small and too post-diagnosis to promote.

## No-Background Decision-Maker Report

- What happened: source-direct no longer means automatic eligible.
- ASTS is blocked by financing overhang.
- SNOW is blocked by reaffirm/high-noise logic.
- CEG/DDOG/TER remain eligible in this small replay.
- Capital status: still FORBIDDEN.

## Artifact Manifest

- Inputs: Task698 freeze/eval, Task699 source-direct features, Task693 source evidence, Task684 context.
- Outputs: rule freeze, rule eval, action summary, portfolio comparison, audit, decision, pass/fail, manifest.
- Row counts: freeze {len(rule_freeze)}, eval {len(rule_eval)}, action summary {len(action_summary)}.
- Validation commands: `python src/backtest/build_task701_conflict_aware_source_direct_rule.py`; `python -m unittest tests.test_task701_conflict_aware_source_direct_rule`; `python scripts/task_registry_validate.py`.

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
    parser.add_argument("--task698-dir", type=Path, default=TASK698_DIR)
    parser.add_argument("--task699-dir", type=Path, default=TASK699_DIR)
    parser.add_argument("--task693-dir", type=Path, default=TASK693_DIR)
    parser.add_argument("--task684-panel", type=Path, default=TASK684_PANEL)
    parser.add_argument("--out-dir", type=Path, default=TASK701_DIR)
    args = parser.parse_args()
    build_task701_program(
        task698_dir=args.task698_dir,
        task699_dir=args.task699_dir,
        task693_dir=args.task693_dir,
        task684_panel_path=args.task684_panel,
        out_dir=args.out_dir,
    )
    print(f"[Task701] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
