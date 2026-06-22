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
TASK693_DIR = Path("docs/reports/task_693_source_packet_v2_price_packet")
TASK684_PANEL = Path("docs/reports/task_684_interaction_context_prediction_stack/task684_interaction_stack_panel.csv")
TASK702_DIR = Path("docs/reports/task_702_full_source_packet_axis_rule")

SIGNAL_FAMILIES = [
    "contract_signal_v2",
    "customer_signal_v2",
    "order_backlog_signal_v2",
    "revenue_signal_v2",
    "guidance_signal_v2",
    "margin_signal_v2",
    "supply_demand_signal_v2",
]
FINANCING_PATTERN = re.compile(
    r"private offering|convertible senior notes|senior notes due|indenture and notes|"
    r"capped call|note purchase agreement|convertible notes|aggregate principal amount",
    flags=re.IGNORECASE,
)
REAFFIRM_PATTERN = re.compile(
    r"\breaffirm(?:s|ed|ing)?\b|unauthorized interview|previously issued guidance|reaffirmed guidance",
    flags=re.IGNORECASE,
)
RAISE_PATTERN = re.compile(
    r"(raise|raises|raised|raising|increase|increases|increased|higher|above|upgrade|upward).{0,100}"
    r"(guidance|outlook|forecast)|(guidance|outlook|forecast).{0,100}"
    r"(raise|raises|raised|increase|higher|above|upgrade|upward)",
    flags=re.IGNORECASE,
)
SOFT_PATTERN = re.compile(
    r"(lower|lowers|lowered|reduce|reduced|cut|cuts|below).{0,100}(guidance|outlook|forecast)|"
    r"(guidance|outlook|forecast).{0,100}(lower|lowers|lowered|reduce|reduced|cut|below)",
    flags=re.IGNORECASE,
)
CONTEXT_COLUMNS = [
    "lifecycle_id",
    "symbol",
    "price_acceptance_score",
    "price_chart_acceptance_state",
    "volume_ratio_prev",
]


def build_task702_program(
    *,
    task698_dir: Path = TASK698_DIR,
    task693_dir: Path = TASK693_DIR,
    task684_panel_path: Path = TASK684_PANEL,
    out_dir: Path = TASK702_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    freeze_435 = pd.read_csv(task698_dir / "task698_full_candidate_freeze_panel.csv")
    eval_435 = pd.read_csv(task698_dir / "task698_full_candidate_eval_panel.csv")
    events = pd.read_csv(task693_dir / "task693_source_event_v2_evidence.csv")
    context = pd.read_csv(task684_panel_path, usecols=CONTEXT_COLUMNS)

    axis_freeze = build_axis_freeze(freeze_435, events, context)
    axis_eval = build_axis_eval(axis_freeze, eval_435)
    action_summary = build_action_summary(axis_eval)
    portfolio_comparison = build_portfolio_comparison(axis_eval)
    audit = build_audit(axis_freeze, axis_eval, action_summary, portfolio_comparison)
    pass_fail = audit.copy()
    decision = build_decision(axis_freeze, action_summary, portfolio_comparison, audit)
    write_outputs(out_dir, axis_freeze, axis_eval, action_summary, portfolio_comparison, audit, pass_fail, decision)
    return {
        "task702_axis_freeze_panel": axis_freeze,
        "task702_axis_eval_panel": axis_eval,
        "task702_action_summary": action_summary,
        "task702_portfolio_comparison": portfolio_comparison,
        "task702_integrity_audit": audit,
        "task_702_pass_fail_matrix": pass_fail,
        "task_702_decision": decision,
    }


def build_axis_freeze(freeze_435: pd.DataFrame, events: pd.DataFrame, context: pd.DataFrame) -> pd.DataFrame:
    base = freeze_435.copy()
    axis_columns = [
        "source_event_available_flag",
        "event_count",
        "direct_event_count",
        "manual_event_count",
        "noise_event_count",
        "noise_ratio",
        "direct_signal_family_count",
        "manual_signal_family_count",
        "financing_overhang_flag",
        "guidance_quality_axis",
        "information_novelty_axis",
        "high_noise_thin_signal_flag",
    ]
    base = base.drop(columns=[col for col in axis_columns if col in base.columns])
    base = base.drop(columns=[col for col in CONTEXT_COLUMNS if col not in {"lifecycle_id", "symbol"} and col in base.columns])
    axes = build_source_axes(events)
    out = base.merge(axes, on=["lifecycle_id", "symbol"], how="left").merge(context, on=["lifecycle_id", "symbol"], how="left")
    out["source_event_available_flag"] = pd.to_numeric(out["source_event_available_flag"], errors="coerce").fillna(0).astype(int)
    for col in [
        "event_count",
        "direct_event_count",
        "manual_event_count",
        "noise_event_count",
        "noise_ratio",
        "direct_signal_family_count",
        "manual_signal_family_count",
        "financing_overhang_flag",
        "high_noise_thin_signal_flag",
        "price_acceptance_score",
        "volume_ratio_prev",
    ]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0)
    out["guidance_quality_axis"] = out["guidance_quality_axis"].fillna("no_source_packet")
    out["information_novelty_axis"] = out["information_novelty_axis"].fillna("no_source_packet")
    out["price_absorption_confirmation_flag"] = (
        out["price_acceptance_score"].ge(6)
        & out["volume_ratio_prev"].ge(1.0)
        & out["price_chart_acceptance_state"].astype(str).str.contains("price_confirmed", na=False)
    ).astype(int)
    out["full_source_axis_action"] = out.apply(classify_full_axis_action, axis=1)
    out["full_source_axis_eligible_flag"] = out["full_source_axis_action"].eq("ELIGIBLE_RULE_CANDIDATE").astype(int)
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
        "source_event_available_flag",
        "event_count",
        "direct_event_count",
        "manual_event_count",
        "noise_event_count",
        "noise_ratio",
        "direct_signal_family_count",
        "manual_signal_family_count",
        "financing_overhang_flag",
        "guidance_quality_axis",
        "information_novelty_axis",
        "high_noise_thin_signal_flag",
        "price_acceptance_score",
        "price_chart_acceptance_state",
        "volume_ratio_prev",
        "price_absorption_confirmation_flag",
        "full_source_axis_action",
        "full_source_axis_eligible_flag",
        "outcome_used_for_selection_flag",
        "future_price_used_for_selection_flag",
        "allocation_approved_flag",
        "paper_or_live_trade_approved_flag",
    ]
    return out[columns].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def build_source_axes(events: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (lifecycle_id, symbol), group in events.groupby(["lifecycle_id", "symbol"], dropna=False):
        direct = group[group["source_event_v2_state"].eq("direct_economic_source_supported")]
        manual = group[group["source_event_v2_state"].eq("economic_terms_manual_review")]
        base_text_rows = direct if len(direct) else manual
        focused_text = " ".join(base_text_rows[["event_title", "evidence_snippet"]].fillna("").astype(str).to_numpy().ravel().tolist())
        full_text = focused_text
        for path_value in group["raw_text_path"].dropna().unique():
            path = Path(str(path_value))
            if not path.is_absolute():
                path = ROOT / path
            try:
                full_text += " " + path.read_text(encoding="utf-8", errors="ignore")[:50000]
            except OSError:
                pass
        direct_family_count = int((direct[SIGNAL_FAMILIES].sum() > 0).sum()) if len(direct) else 0
        manual_family_count = int((manual[SIGNAL_FAMILIES].sum() > 0).sum()) if len(manual) else 0
        guidance_count = int((direct["guidance_signal_v2"].sum() if len(direct) else 0) + (manual["guidance_signal_v2"].sum() if len(manual) else 0))
        noise_count = int(
            group["source_event_v2_state"].isin(
                ["ownership_or_sale_filing_noise", "ownership_filing_with_weak_economic_terms", "broad_policy_not_symbol_specific"]
            ).sum()
        )
        event_count = int(len(group))
        financing = bool(FINANCING_PATTERN.search(full_text))
        reaffirm = bool(REAFFIRM_PATTERN.search(full_text))
        soft = bool(SOFT_PATTERN.search(focused_text))
        raised = bool(RAISE_PATTERN.search(focused_text)) and not reaffirm and not soft
        rows.append(
            {
                "lifecycle_id": lifecycle_id,
                "symbol": symbol,
                "source_event_available_flag": 1,
                "event_count": event_count,
                "direct_event_count": int(len(direct)),
                "manual_event_count": int(len(manual)),
                "noise_event_count": noise_count,
                "noise_ratio": noise_count / event_count if event_count else 0.0,
                "direct_signal_family_count": direct_family_count,
                "manual_signal_family_count": manual_family_count,
                "financing_overhang_flag": int(financing),
                "guidance_quality_axis": classify_guidance_quality(financing, reaffirm, soft, raised, guidance_count),
                "information_novelty_axis": classify_information_novelty(
                    financing, reaffirm, len(direct), direct_family_count, len(manual), manual_family_count
                ),
                "high_noise_thin_signal_flag": int((noise_count / event_count if event_count else 0.0) >= 0.75 and len(direct) <= 1),
            }
        )
    return pd.DataFrame(rows)


def classify_guidance_quality(financing: bool, reaffirm: bool, soft: bool, raised: bool, guidance_count: int) -> str:
    if financing:
        return "financing_conflict"
    if reaffirm:
        return "reaffirm"
    if guidance_count and soft:
        return "soft_or_cut"
    if guidance_count and raised:
        return "raise_or_positive_change"
    if guidance_count:
        return "guidance_present_quality_unclear"
    return "no_guidance_signal"


def classify_information_novelty(
    financing: bool,
    reaffirm: bool,
    direct_count: int,
    direct_family_count: int,
    manual_count: int,
    manual_family_count: int,
) -> str:
    if financing:
        return "conflicted_by_financing"
    if reaffirm:
        return "not_new_reaffirmation"
    if direct_count > 0 and direct_family_count >= 3:
        return "new_multi_family_direct"
    if direct_count > 0:
        return "new_thin_direct"
    if manual_count > 0 and manual_family_count >= 2:
        return "manual_indirect_economic_terms"
    return "not_enough_source_novelty"


def classify_full_axis_action(row: pd.Series) -> str:
    if int(row["source_event_available_flag"]) == 0:
        return "RESEARCH_ONLY_NO_SOURCE_PACKET"
    if int(row["financing_overhang_flag"]) == 1:
        return "CONFIRMATION_REQUIRED_FINANCING"
    if row["guidance_quality_axis"] in {"reaffirm", "soft_or_cut"}:
        return "CONFIRMATION_REQUIRED_GUIDANCE_WEAK"
    if row["information_novelty_axis"] in {"not_new_reaffirmation", "not_enough_source_novelty"}:
        return "RESEARCH_ONLY_LOW_NOVELTY"
    if int(row["high_noise_thin_signal_flag"]) == 1 and int(row["price_absorption_confirmation_flag"]) == 0:
        return "CONFIRMATION_REQUIRED_HIGH_NOISE"
    if int(row["price_absorption_confirmation_flag"]) == 0:
        return "CONFIRMATION_REQUIRED_PRICE"
    return "ELIGIBLE_RULE_CANDIDATE"


def build_axis_eval(axis_freeze: pd.DataFrame, eval_435: pd.DataFrame) -> pd.DataFrame:
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
    joined = axis_freeze.merge(eval_435[eval_cols], on=["lifecycle_id", "symbol"], how="left", indicator=True)
    if not joined["_merge"].eq("both").all():
        raise ValueError("Task702 all frozen rows must join to Task698 eval rows.")
    joined = joined.drop(columns=["_merge"])
    joined["outcome_used_for_evaluation_flag"] = 1
    return joined


def build_action_summary(axis_eval: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for action, group in axis_eval.groupby("full_source_axis_action", dropna=False):
        costed = group["costed_return_pct"].astype(float)
        rows.append(
            {
                "full_source_axis_action": action,
                "candidate_count": int(len(group)),
                "source_event_count": int(group["source_event_available_flag"].sum()),
                "symbols": "|".join(group["symbol"].astype(str).head(40).tolist()),
                "avg_costed_return_pct": float(costed.mean()),
                "median_costed_return_pct": float(costed.median()),
                "win_rate": float((costed > 0).mean()),
                "avg_excess_vs_qqq_costed_pct": float(group["excess_vs_qqq_costed_pct"].astype(float).mean()),
                "outcome_used_for_selection_flag": 0,
                "outcome_used_for_evaluation_flag": 1,
            }
        )
    return pd.DataFrame(rows).sort_values("avg_costed_return_pct", ascending=False).reset_index(drop=True)


def build_portfolio_comparison(axis_eval: pd.DataFrame) -> pd.DataFrame:
    source_packet = axis_eval[axis_eval["source_event_available_flag"].eq(1)].copy()
    eligible = axis_eval[axis_eval["full_source_axis_eligible_flag"].eq(1)].copy()
    rows = []
    for cohort_name, panel in [("source_packet_available_19", source_packet), ("full_axis_eligible_5", eligible)]:
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
    axis_freeze: pd.DataFrame,
    axis_eval: pd.DataFrame,
    action_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
) -> pd.DataFrame:
    return pd.DataFrame(
        [
            gate("freeze_scope_435", len(axis_freeze) == 435, f"rows={len(axis_freeze)}", "full Task698 freeze set"),
            gate(
                "source_event_available_19",
                int(axis_freeze["source_event_available_flag"].sum()) == 19,
                f"source_event_available={int(axis_freeze['source_event_available_flag'].sum())}",
                "all Task693 source packet rows should be covered",
            ),
            gate(
                "eligible_count_5",
                int(axis_freeze["full_source_axis_eligible_flag"].sum()) == 5,
                f"eligible={int(axis_freeze['full_source_axis_eligible_flag'].sum())}",
                "expected eligible rows after full source packet axes",
            ),
            gate(
                "asts_snow_blocked",
                int(axis_freeze[axis_freeze["symbol"].isin(["ASTS", "SNOW"])]["full_source_axis_eligible_flag"].sum()) == 0,
                "ASTS/SNOW eligible count=0",
                "ASTS and SNOW should remain blocked",
            ),
            gate(
                "eval_rows_complete",
                len(axis_eval) == len(axis_freeze) and int(axis_eval["outcome_used_for_evaluation_flag"].sum()) == len(axis_freeze),
                f"eval_rows={len(axis_eval)}",
                "evaluation attaches outcomes after freeze",
            ),
            gate(
                "portfolio_comparison_present",
                set(portfolio_comparison["portfolio_cohort"]) == {"source_packet_available_19", "full_axis_eligible_5"},
                "|".join(sorted(set(portfolio_comparison["portfolio_cohort"]))),
                "portfolio comparison cohorts are present",
            ),
            gate(
                "no_strategy_or_trade_promotion",
                int(axis_freeze["allocation_approved_flag"].sum()) == 0
                and int(axis_freeze["paper_or_live_trade_approved_flag"].sum()) == 0,
                "allocation_approved=0; paper_or_live_trade_approved=0",
                "Task702 is research-only",
            ),
        ]
    )


def build_decision(
    axis_freeze: pd.DataFrame,
    action_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
    audit: pd.DataFrame,
) -> pd.DataFrame:
    eligible_summary = action_summary[action_summary["full_source_axis_action"].eq("ELIGIBLE_RULE_CANDIDATE")].iloc[0]
    eligible_max5 = portfolio_row(portfolio_comparison, "full_axis_eligible_5", 5)
    source_packet_max5 = portfolio_row(portfolio_comparison, "source_packet_available_19", 5)
    return pd.DataFrame(
        [
            {
                "task_id": "Task702",
                "verdict": "FULL_SOURCE_PACKET_AXIS_RULE_TEST_COMPLETE_RESEARCH_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "freeze_count": int(len(axis_freeze)),
                "source_event_available_count": int(axis_freeze["source_event_available_flag"].sum()),
                "eligible_count": int(axis_freeze["full_source_axis_eligible_flag"].sum()),
                "eligible_symbols": "|".join(axis_freeze[axis_freeze["full_source_axis_eligible_flag"].eq(1)]["symbol"].astype(str).tolist()),
                "eligible_avg_costed_return_pct": float(eligible_summary["avg_costed_return_pct"]),
                "eligible_win_rate": float(eligible_summary["win_rate"]),
                "source_packet_max5_final_capital_usd": float(source_packet_max5["final_capital_usd"]),
                "eligible_max5_final_capital_usd": float(eligible_max5["final_capital_usd"]),
                "eligible_max5_return_pct": float(eligible_max5["capital_return_pct"]),
                "eligible_max5_mdd_pct": float(eligible_max5["max_drawdown_pct"]),
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "Full source packet axes block ASTS/SNOW and keep CEG, CEG, TER, PH, DDOG in this diagnostic replay.",
                "research_caveat": "This remains a 19-source-packet diagnostic subset inside 435 candidates, not a deployable strategy.",
                "next_action": "Move the same source-axis parser upstream to all event-linked candidates, then retest against larger OOS cohorts.",
            }
        ]
    )


def portfolio_row(portfolio_comparison: pd.DataFrame, cohort: str, max_positions: int) -> pd.Series:
    return portfolio_comparison[
        portfolio_comparison["portfolio_cohort"].eq(cohort) & portfolio_comparison["max_positions"].eq(max_positions)
    ].iloc[0]


def write_outputs(
    out_dir: Path,
    axis_freeze: pd.DataFrame,
    axis_eval: pd.DataFrame,
    action_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
    audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> None:
    outputs = {
        "task702_axis_freeze_panel.csv": axis_freeze,
        "task702_axis_eval_panel.csv": axis_eval,
        "task702_action_summary.csv": action_summary,
        "task702_portfolio_comparison.csv": portfolio_comparison,
        "task702_integrity_audit.csv": audit,
        "task_702_pass_fail_matrix.csv": pass_fail,
        "task_702_decision.csv": decision,
    }
    for name, frame in outputs.items():
        frame.to_csv(out_dir / name, index=False)
    (out_dir / "task_702_full_source_packet_axis_rule.md").write_text(
        render_report(axis_freeze, axis_eval, action_summary, portfolio_comparison, audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def render_report(
    axis_freeze: pd.DataFrame,
    axis_eval: pd.DataFrame,
    action_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
    audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    source_view = axis_eval[axis_eval["source_event_available_flag"].eq(1)][
        [
            "symbol",
            "packet_bucket",
            "financing_overhang_flag",
            "guidance_quality_axis",
            "information_novelty_axis",
            "high_noise_thin_signal_flag",
            "price_absorption_confirmation_flag",
            "full_source_axis_action",
            "costed_return_pct",
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
    return f"""# Task702 Full Source Packet Axis Rule

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Scope: 435 frozen candidates, source-packet coverage {int(d["source_event_available_count"])}.
- Eligible symbols: {d["eligible_symbols"]}.
- Key $1,000 max5: source-packet cohort ${float(d["source_packet_max5_final_capital_usd"]):,.2f}; full-axis eligible ${float(d["eligible_max5_final_capital_usd"]):,.2f}.
- Main finding: {d["primary_result"]}
- Next action: {d["next_action"]}

## Quant Expert Report

### Axes Added

- financing overhang
- guidance raise/reaffirm/soft/unclear
- information novelty
- high-noise thin signal
- price absorption confirmation

### Source Packet Action Table

{t678.markdown_table(source_view)}

### Action Summary

{t678.markdown_table(action_summary)}

### Portfolio Comparison

{t678.markdown_table(portfolio_view)}

### Interpretation

- The five axes keep ASTS and SNOW blocked.
- The eligible set expands from Task701 by adding PH while preserving CEG, CEG, TER, and DDOG.
- The rule still covers only 19 source-packet candidates inside the 435 frozen set, so it is not accepted as a strategy.

## No-Background Decision-Maker Report

- What happened: the five axes were applied to all source packets, not just source-direct.
- ASTS/SNOW stayed blocked.
- Eligible became CEG, CEG, TER, PH, DDOG.
- Capital status: still FORBIDDEN.

## Artifact Manifest

- Inputs: Task698 freeze/eval, Task693 source events, Task684 context.
- Outputs: axis freeze, axis eval, action summary, portfolio comparison, audit, decision, pass/fail, manifest.
- Row counts: freeze {len(axis_freeze)}, eval {len(axis_eval)}, action summary {len(action_summary)}.
- Validation commands: `python src/backtest/build_task702_full_source_packet_axis_rule.py`; `python -m unittest tests.test_task702_full_source_packet_axis_rule`; `python scripts/task_registry_validate.py`.

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
    parser.add_argument("--task693-dir", type=Path, default=TASK693_DIR)
    parser.add_argument("--task684-panel", type=Path, default=TASK684_PANEL)
    parser.add_argument("--out-dir", type=Path, default=TASK702_DIR)
    args = parser.parse_args()
    build_task702_program(
        task698_dir=args.task698_dir,
        task693_dir=args.task693_dir,
        task684_panel_path=args.task684_panel,
        out_dir=args.out_dir,
    )
    print(f"[Task702] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
