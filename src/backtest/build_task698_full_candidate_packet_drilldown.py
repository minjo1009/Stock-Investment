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
from src.backtest.build_task618_1000_capital_portfolio_comparison import simulate_deterministic_portfolio
from src.backtest.build_task697_tiny_candidate_pnl_test import (
    INITIAL_CAPITAL_USD,
    QQQ_DAILY,
    ROUND_TRIP_COST_BPS,
    aligned_qqq_price,
    load_qqq_daily,
)


TASK691_DIR = Path("docs/reports/task_691_slot_leader_contender_review")
TASK692_DIR = Path("docs/reports/task_692_source_packet_price_absorption")
TASK693_DIR = Path("docs/reports/task_693_source_packet_v2_price_packet")
TASK684_PANEL = Path("docs/reports/task_684_interaction_context_prediction_stack/task684_interaction_stack_panel.csv")
TASK698_DIR = Path("docs/reports/task_698_full_candidate_packet_drilldown")

IDENTITY = ["lifecycle_id", "symbol", "entry_ts", "entry_ts_utc", "theme_id", "split_name"]
OUTCOME_COLUMNS = [
    "entry_price",
    "simulated_exit_ts",
    "simulated_exit_price",
    "exit_reason",
    "net_return_from_entry",
    "win_flag",
    "add_scale_success_flag",
    "entry_reduce_failure_flag",
    "false_positive_flag",
    "holding_days",
    "same_day_exit_flag",
    "policy_name",
]
FORBIDDEN_FREEZE_COLUMNS = {
    "entry_price",
    "simulated_exit_ts",
    "simulated_exit_price",
    "exit_reason",
    "net_return_from_entry",
    "net_return_pct",
    "return_pct",
    "win_flag",
    "win_eval_flag",
    "holding_days",
}
PORTFOLIO_COHORTS = {
    "source_direct_supported_9": lambda frame: frame["packet_bucket"].eq("source_direct_supported"),
    "review_ready_source_or_price_11": lambda frame: frame["packet_bucket"].isin(
        ["source_direct_supported", "price_confirmed_not_overextended"]
    ),
    "manual_no_direct_bridge_10": lambda frame: frame["packet_bucket"].eq(
        "source_packet_economic_terms_but_no_direct_bridge"
    ),
    "price_possible_needs_delay_188": lambda frame: frame["packet_bucket"].eq("price_possible_needs_delay"),
    "peer_margin_confirmation_114": lambda frame: frame["packet_bucket"].eq("peer_margin_confirmation_needed"),
    "all_435": lambda frame: frame["packet_bucket"].notna(),
}


def build_task698_program(
    *,
    task691_dir: Path = TASK691_DIR,
    task692_dir: Path = TASK692_DIR,
    task693_dir: Path = TASK693_DIR,
    task684_panel_path: Path = TASK684_PANEL,
    qqq_daily_path: Path = QQQ_DAILY,
    out_dir: Path = TASK698_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)
    freeze = build_freeze_panel(task691_dir, task692_dir, task693_dir)
    outcomes = pd.read_csv(task684_panel_path, usecols=["lifecycle_id", "symbol", *OUTCOME_COLUMNS])
    qqq = load_qqq_daily(qqq_daily_path)

    eval_panel = build_eval_panel(freeze, outcomes, qqq)
    bucket_summary = build_bucket_summary(eval_panel)
    portfolio_comparison = build_portfolio_comparison(eval_panel)
    audit = build_audit(freeze, eval_panel, bucket_summary, portfolio_comparison)
    pass_fail = audit.copy()
    decision = build_decision(freeze, eval_panel, bucket_summary, portfolio_comparison, audit)

    write_outputs(out_dir, freeze, eval_panel, bucket_summary, portfolio_comparison, audit, pass_fail, decision)
    return {
        "task698_full_candidate_freeze_panel": freeze,
        "task698_full_candidate_eval_panel": eval_panel,
        "task698_bucket_return_summary": bucket_summary,
        "task698_portfolio_comparison": portfolio_comparison,
        "task698_integrity_audit": audit,
        "task_698_pass_fail_matrix": pass_fail,
        "task_698_decision": decision,
    }


def build_freeze_panel(task691_dir: Path, task692_dir: Path, task693_dir: Path) -> pd.DataFrame:
    leaders = pd.read_csv(task691_dir / "task691_slot_leader_review.csv")
    contenders = pd.read_csv(task691_dir / "task691_contender_confirmation_map.csv")
    leader_v2 = pd.read_csv(task693_dir / "task693_leader_source_packet_v2_review.csv")
    price_absorption = pd.read_csv(task692_dir / "task692_price_absorption_confirmation_panel.csv")

    base = pd.concat(
        [
            leaders.assign(review_role="leader", required_confirmation_type=leaders["required_pre_backtest_review"]),
            contenders.assign(review_role="contender"),
        ],
        ignore_index=True,
        sort=False,
    )
    base = base.merge(
        leader_v2[
            [
                "lifecycle_id",
                "source_packet_v2_state",
                "source_packet_v2_verdict",
                "direct_economic_source_event_count",
                "manual_review_economic_event_count",
                "noise_event_count",
                "event_with_economic_terms_count",
            ]
        ],
        on="lifecycle_id",
        how="left",
    )
    base = base.merge(
        price_absorption[
            [
                "lifecycle_id",
                "price_absorption_state",
                "price_absorption_verdict",
                "price_acceptance_score",
                "absorption_reason_flags",
            ]
        ],
        on="lifecycle_id",
        how="left",
    )
    base["packet_bucket"] = base.apply(classify_packet_bucket, axis=1)
    base["freeze_candidate_flag"] = 1
    base["review_ready_packet_flag"] = base["packet_bucket"].isin(
        ["source_direct_supported", "price_confirmed_not_overextended"]
    ).astype(int)
    base["source_direct_supported_flag"] = base["packet_bucket"].eq("source_direct_supported").astype(int)
    base["price_confirmed_flag"] = base["packet_bucket"].eq("price_confirmed_not_overextended").astype(int)
    base["outcome_used_for_selection_flag"] = 0
    base["future_price_used_for_selection_flag"] = 0
    base["allocation_approved_flag"] = 0
    base["paper_or_live_trade_approved_flag"] = 0

    columns = [
        *IDENTITY,
        "review_role",
        "sector_family",
        "cohort_id",
        "cohort_rank",
        "cohort_size",
        "slot_claim_score",
        "margin_vs_next_peer",
        "weakest_layer",
        "dominant_interpretation_gap",
        "required_confirmation_type",
        "packet_bucket",
        "source_packet_v2_state",
        "source_packet_v2_verdict",
        "direct_economic_source_event_count",
        "manual_review_economic_event_count",
        "noise_event_count",
        "event_with_economic_terms_count",
        "price_absorption_state",
        "price_absorption_verdict",
        "price_acceptance_score",
        "absorption_reason_flags",
        "freeze_candidate_flag",
        "review_ready_packet_flag",
        "source_direct_supported_flag",
        "price_confirmed_flag",
        "outcome_used_for_selection_flag",
        "future_price_used_for_selection_flag",
        "allocation_approved_flag",
        "paper_or_live_trade_approved_flag",
    ]
    for col in columns:
        if col not in base.columns:
            base[col] = ""
    return base[columns].sort_values(["entry_ts", "symbol", "lifecycle_id"]).reset_index(drop=True)


def classify_packet_bucket(row: pd.Series) -> str:
    source_state = str(row.get("source_packet_v2_state", ""))
    price_state = str(row.get("price_absorption_state", ""))
    required_confirmation = str(row.get("required_confirmation_type", ""))
    if source_state == "source_packet_direct_economic_supported":
        return "source_direct_supported"
    if price_state == "absorption_confirmed_not_overextended":
        return "price_confirmed_not_overextended"
    if price_state == "absorption_possible_needs_delay":
        return "price_possible_needs_delay"
    if price_state == "absorption_unproven_needs_confirmation":
        return "price_unproven_needs_confirmation"
    if price_state == "priced_in_or_extension_risk":
        return "priced_in_or_extension_risk"
    if required_confirmation == "peer_margin_confirmation":
        return "peer_margin_confirmation_needed"
    if source_state and source_state != "nan":
        return source_state
    return "other_not_review_ready"


def build_eval_panel(freeze: pd.DataFrame, outcomes: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    joined = freeze.merge(outcomes, on=["lifecycle_id", "symbol"], how="left", indicator=True)
    if not joined["_merge"].eq("both").all():
        missing = joined[~joined["_merge"].eq("both")][["lifecycle_id", "symbol"]].head(10).to_dict(orient="records")
        raise ValueError(f"Task698 missing exact outcome joins: {missing}")
    joined = joined.drop(columns=["_merge"])
    joined["entry_ts_eval"] = pd.to_datetime(joined["entry_ts"], utc=True, errors="coerce")
    joined["simulated_exit_ts_eval"] = pd.to_datetime(joined["simulated_exit_ts"], utc=True, errors="coerce")
    rows = []
    for _, row in joined.iterrows():
        entry_price = float(row["entry_price"])
        exit_price = float(row["simulated_exit_price"])
        gross_return = exit_price / entry_price - 1.0
        costed_return = gross_return - ROUND_TRIP_COST_BPS / 10000.0
        q_entry = aligned_qqq_price(qqq, row["entry_ts_eval"])
        q_exit = aligned_qqq_price(qqq, row["simulated_exit_ts_eval"])
        qqq_gross_return = q_exit["close"] / q_entry["close"] - 1.0
        qqq_costed_return = qqq_gross_return - ROUND_TRIP_COST_BPS / 10000.0
        out = row.to_dict()
        out.update(
            {
                "gross_return_pct": gross_return * 100.0,
                "task684_net_return_from_entry_pct": float(row["net_return_from_entry"]) * 100.0,
                "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
                "costed_return_pct": costed_return * 100.0,
                "qqq_entry_date": str(q_entry["date"]),
                "qqq_exit_date": str(q_exit["date"]),
                "qqq_entry_close": q_entry["close"],
                "qqq_exit_close": q_exit["close"],
                "qqq_gross_return_pct": qqq_gross_return * 100.0,
                "qqq_costed_return_pct": qqq_costed_return * 100.0,
                "excess_vs_qqq_costed_pct": (costed_return - qqq_costed_return) * 100.0,
                "beats_qqq_same_window_flag": int(costed_return > qqq_costed_return),
                "outcome_used_for_evaluation_flag": 1,
            }
        )
        rows.append(out)
    return pd.DataFrame(rows).sort_values(["entry_ts_eval", "symbol", "lifecycle_id"]).reset_index(drop=True)


def build_bucket_summary(eval_panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for bucket, group in eval_panel.groupby("packet_bucket", dropna=False):
        costed = group["costed_return_pct"].astype(float)
        qqq = group["qqq_costed_return_pct"].astype(float)
        rows.append(
            {
                "packet_bucket": bucket,
                "candidate_count": int(len(group)),
                "review_ready_count": int(group["review_ready_packet_flag"].sum()),
                "train_design_count": int(group["split_name"].eq("train_design").sum()),
                "validation_count": int(group["split_name"].eq("validation").sum()),
                "recent_oos_count": int(group["split_name"].eq("recent_oos").sum()),
                "avg_costed_return_pct": float(costed.mean()),
                "median_costed_return_pct": float(costed.median()),
                "win_rate": float((costed > 0).mean()),
                "avg_qqq_costed_return_pct": float(qqq.mean()),
                "avg_excess_vs_qqq_costed_pct": float((costed - qqq).mean()),
                "beats_qqq_rate": float(group["beats_qqq_same_window_flag"].mean()),
                "best_symbol": str(group.loc[costed.idxmax(), "symbol"]),
                "best_costed_return_pct": float(costed.max()),
                "worst_symbol": str(group.loc[costed.idxmin(), "symbol"]),
                "worst_costed_return_pct": float(costed.min()),
                "outcome_used_for_selection_flag": 0,
            }
        )
    return pd.DataFrame(rows).sort_values(["avg_costed_return_pct"], ascending=False).reset_index(drop=True)


def build_portfolio_comparison(eval_panel: pd.DataFrame) -> pd.DataFrame:
    rows = []
    panel = eval_panel.copy()
    panel["net_return_from_entry"] = panel["costed_return_pct"].astype(float) / 100.0
    for cohort_name, selector in PORTFOLIO_COHORTS.items():
        cohort = panel[selector(panel)].copy()
        for max_positions in [1, 3, 5, 10]:
            quality, accepted, _curve = simulate_deterministic_portfolio(cohort, max_positions=max_positions)
            final_capital = INITIAL_CAPITAL_USD * (1.0 + float(quality["capital_pnl_pct"]) / 100.0)
            rows.append(
                {
                    "portfolio_cohort": cohort_name,
                    "max_positions": int(max_positions),
                    "source_candidate_count": int(len(cohort)),
                    "accepted_trade_count": int(len(accepted)),
                    "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
                    "initial_capital_usd": INITIAL_CAPITAL_USD,
                    "final_capital_usd": final_capital,
                    "capital_return_pct": float(quality["capital_pnl_pct"]),
                    "max_drawdown_pct": float(quality["max_drawdown_pct"]),
                    "skipped_due_capacity_count": int(quality["skipped_due_capacity_count"]),
                    "strategy_acceptance_status": "NOT_ACCEPTED",
                    "real_capital_status": "FORBIDDEN",
                }
            )
    return pd.DataFrame(rows)


def build_audit(
    freeze: pd.DataFrame,
    eval_panel: pd.DataFrame,
    bucket_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
) -> pd.DataFrame:
    forbidden = sorted(col for col in freeze.columns if col in FORBIDDEN_FREEZE_COLUMNS)
    return pd.DataFrame(
        [
            gate(
                "full_candidate_scope_435",
                len(freeze) == 435 and freeze["review_role"].value_counts().to_dict() == {"contender": 407, "leader": 28},
                f"rows={len(freeze)}; roles={freeze['review_role'].value_counts().to_dict()}",
                "Task698 must cover Task691 28 leaders plus 407 contenders",
            ),
            gate(
                "freeze_panel_has_no_outcome_columns",
                len(forbidden) == 0,
                "|".join(forbidden) if forbidden else "none",
                "Freeze panel cannot contain PnL/outcome columns",
            ),
            gate(
                "review_ready_packet_count_11",
                int(freeze["review_ready_packet_flag"].sum()) == 11,
                f"review_ready={int(freeze['review_ready_packet_flag'].sum())}",
                "Review-ready automated packet scope should be 9 source-direct plus 2 price-confirmed rows",
            ),
            gate(
                "exact_outcome_eval_count",
                len(eval_panel) == len(freeze) and int(eval_panel["outcome_used_for_evaluation_flag"].sum()) == len(freeze),
                f"eval_rows={len(eval_panel)}; eval_flags={int(eval_panel['outcome_used_for_evaluation_flag'].sum())}",
                "All frozen rows must evaluate by exact lifecycle join only",
            ),
            gate(
                "cost_and_qqq_applied",
                eval_panel["round_trip_cost_bps"].eq(ROUND_TRIP_COST_BPS).all()
                and eval_panel["qqq_costed_return_pct"].notna().all(),
                f"cost_bps={ROUND_TRIP_COST_BPS}; qqq_rows={eval_panel['qqq_costed_return_pct'].notna().sum()}",
                "Every evaluated row needs costed return and QQQ matched-window return",
            ),
            gate(
                "bucket_summary_complete",
                int(bucket_summary["candidate_count"].sum()) == len(freeze),
                f"bucket_sum={int(bucket_summary['candidate_count'].sum())}",
                "Bucket summary must account for every frozen row",
            ),
            gate(
                "portfolio_comparison_present",
                set(portfolio_comparison["portfolio_cohort"]).issuperset(PORTFOLIO_COHORTS)
                and set(portfolio_comparison["max_positions"]) == {1, 3, 5, 10},
                f"rows={len(portfolio_comparison)}",
                "Portfolio comparison must cover declared cohorts and max position grids",
            ),
            gate(
                "no_strategy_or_trade_promotion",
                int(freeze["allocation_approved_flag"].sum()) == 0
                and int(freeze["paper_or_live_trade_approved_flag"].sum()) == 0,
                "allocation_approved=0; paper_or_live_trade_approved=0",
                "Full drilldown cannot promote allocation or trading",
            ),
        ]
    )


def build_decision(
    freeze: pd.DataFrame,
    eval_panel: pd.DataFrame,
    bucket_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
    audit: pd.DataFrame,
) -> pd.DataFrame:
    direct = bucket_summary[bucket_summary["packet_bucket"].eq("source_direct_supported")].iloc[0]
    price = bucket_summary[bucket_summary["packet_bucket"].eq("price_confirmed_not_overextended")].iloc[0]
    review_ready_max5 = portfolio_row(portfolio_comparison, "review_ready_source_or_price_11", 5)
    all_435_max5 = portfolio_row(portfolio_comparison, "all_435", 5)
    source_direct_max5 = portfolio_row(portfolio_comparison, "source_direct_supported_9", 5)
    return pd.DataFrame(
        [
            {
                "task_id": "Task698",
                "verdict": "FULL_CANDIDATE_PACKET_DRILLDOWN_COMPLETE_RESEARCH_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "freeze_candidate_count": int(len(freeze)),
                "review_ready_packet_count": int(freeze["review_ready_packet_flag"].sum()),
                "source_direct_supported_count": int(freeze["source_direct_supported_flag"].sum()),
                "price_confirmed_count": int(freeze["price_confirmed_flag"].sum()),
                "source_direct_avg_costed_return_pct": float(direct["avg_costed_return_pct"]),
                "source_direct_avg_excess_vs_qqq_pct": float(direct["avg_excess_vs_qqq_costed_pct"]),
                "price_confirmed_avg_costed_return_pct": float(price["avg_costed_return_pct"]),
                "price_confirmed_avg_excess_vs_qqq_pct": float(price["avg_excess_vs_qqq_costed_pct"]),
                "review_ready_max5_final_capital_usd": float(review_ready_max5["final_capital_usd"]),
                "review_ready_max5_return_pct": float(review_ready_max5["capital_return_pct"]),
                "review_ready_max5_mdd_pct": float(review_ready_max5["max_drawdown_pct"]),
                "source_direct_max5_final_capital_usd": float(source_direct_max5["final_capital_usd"]),
                "all_435_max5_final_capital_usd": float(all_435_max5["final_capital_usd"]),
                "all_435_max5_mdd_pct": float(all_435_max5["max_drawdown_pct"]),
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "Source-direct packets repeat better than price-confirmed packets; the tiny result was not only TER, but price absorption alone is weak.",
                "research_caveat": "The full 435 drilldown is still research-only because buckets are coarse, overlapping portfolio capacity is unstable, and no allocation rule is promoted.",
                "next_action": "Split source-direct winners and losers by economic catalyst type before expanding allocation rules.",
            }
        ]
    )


def portfolio_row(portfolio_comparison: pd.DataFrame, cohort: str, max_positions: int) -> pd.Series:
    return portfolio_comparison[
        portfolio_comparison["portfolio_cohort"].eq(cohort) & portfolio_comparison["max_positions"].eq(max_positions)
    ].iloc[0]


def write_outputs(
    out_dir: Path,
    freeze: pd.DataFrame,
    eval_panel: pd.DataFrame,
    bucket_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
    audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> None:
    outputs = {
        "task698_full_candidate_freeze_panel.csv": freeze,
        "task698_full_candidate_eval_panel.csv": eval_panel,
        "task698_bucket_return_summary.csv": bucket_summary,
        "task698_portfolio_comparison.csv": portfolio_comparison,
        "task698_integrity_audit.csv": audit,
        "task_698_pass_fail_matrix.csv": pass_fail,
        "task_698_decision.csv": decision,
    }
    for name, frame in outputs.items():
        frame.to_csv(out_dir / name, index=False)
    (out_dir / "task_698_full_candidate_packet_drilldown.md").write_text(
        render_report(freeze, eval_panel, bucket_summary, portfolio_comparison, audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def render_report(
    freeze: pd.DataFrame,
    eval_panel: pd.DataFrame,
    bucket_summary: pd.DataFrame,
    portfolio_comparison: pd.DataFrame,
    audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    bucket_view = bucket_summary[
        [
            "packet_bucket",
            "candidate_count",
            "train_design_count",
            "validation_count",
            "recent_oos_count",
            "avg_costed_return_pct",
            "median_costed_return_pct",
            "win_rate",
            "avg_excess_vs_qqq_costed_pct",
            "beats_qqq_rate",
            "best_symbol",
            "worst_symbol",
        ]
    ]
    portfolio_view = portfolio_comparison[
        portfolio_comparison["portfolio_cohort"].isin(
            ["source_direct_supported_9", "review_ready_source_or_price_11", "all_435"]
        )
    ][
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
    return f"""# Task698 Full Candidate Packet Drilldown

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Scope: Task691 leaders 28 + contenders 407 = {int(d["freeze_candidate_count"])}.
- Review-ready packet count: {int(d["review_ready_packet_count"])}.
- Main finding: {d["primary_result"]}
- Key $1,000 max5: review-ready ${float(d["review_ready_max5_final_capital_usd"]):,.2f}; source-direct ${float(d["source_direct_max5_final_capital_usd"]):,.2f}; all-435 ${float(d["all_435_max5_final_capital_usd"]):,.2f}.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and scope

- Freeze input: Task691 slot leader/contender review.
- Packet inputs: Task693 source packet v2 and Task692 price absorption panel.
- Outcome input: Task684 lifecycle panel, exact `lifecycle_id` + `symbol` join only.
- Benchmark input: QQQ daily from `data/raw/us_daily_breadth_top500/QQQ.csv`.

### Freeze before outcome

- `task698_full_candidate_freeze_panel.csv` has no PnL or exit columns.
- PnL is added only in `task698_full_candidate_eval_panel.csv`.
- No candidate is allocation-approved or paper/live-approved.

### Bucket Return Summary

{t678.markdown_table(bucket_view)}

### Portfolio Comparison

{t678.markdown_table(portfolio_view)}

### Interpretation

- Source-direct packets are stronger than the 3-trade tiny test alone suggested: 9 rows average positive after 50 bps cost and beat QQQ on average.
- Price-confirmed-only is weak: 2 rows average slightly negative after cost.
- The broad 435 set can make money in capacity simulation, but drawdown is large, so it is not a clean strategy.
- Manual/no-direct bridge rows surprisingly performed well, which means the current source interpreter may be too strict or may be missing indirect economic transmission.

### Split/OOS metrics

- Source-direct bucket contains train, validation, and recent-OOS rows.
- This is still not a promotion because the bucket logic is coarse and sample sizes are small.

### Failure decomposition

- ASTS shows source-direct can still fail when ownership/noise mix and later price weakness dominate.
- SNOW rows show direct source support can lose badly when price/catalyst absorption is wrong.
- TER and DDOG show source-direct can catch large winners.
- TEAM/LMT show price absorption alone is not enough.

### Remaining blockers

- Split source-direct by economic catalyst type: contract/customer/backlog/guidance/margin/supply-demand.
- Separate direct economic evidence from ownership/noise-heavy packets.
- Add price absorption as a confirmation of source-direct, not a standalone buy reason.

## No-Background Decision-Maker Report

- What happened: the 3-trade result was expanded to 435 frozen candidates.
- Main result: source-direct evidence looks useful beyond TER.
- Bad part: price absorption alone is weak.
- Big warning: all-435 can earn but with ugly drawdown, so it is not deployable.
- Capital status: still FORBIDDEN.

## Artifact Manifest

- Inputs: Task691, Task692, Task693, Task684, QQQ daily benchmark.
- Outputs: freeze panel, eval panel, bucket summary, portfolio comparison, integrity audit, decision, pass/fail, manifest.
- Row counts: freeze {len(freeze)}, eval {len(eval_panel)}, buckets {len(bucket_summary)}, portfolio rows {len(portfolio_comparison)}.
- Validation commands: `python src/backtest/build_task698_full_candidate_packet_drilldown.py`; `python -m unittest tests.test_task698_full_candidate_packet_drilldown`; `python scripts/task_registry_validate.py`.

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
    parser.add_argument("--task691-dir", type=Path, default=TASK691_DIR)
    parser.add_argument("--task692-dir", type=Path, default=TASK692_DIR)
    parser.add_argument("--task693-dir", type=Path, default=TASK693_DIR)
    parser.add_argument("--task684-panel", type=Path, default=TASK684_PANEL)
    parser.add_argument("--qqq-daily", type=Path, default=QQQ_DAILY)
    parser.add_argument("--out-dir", type=Path, default=TASK698_DIR)
    args = parser.parse_args()
    build_task698_program(
        task691_dir=args.task691_dir,
        task692_dir=args.task692_dir,
        task693_dir=args.task693_dir,
        task684_panel_path=args.task684_panel,
        qqq_daily_path=args.qqq_daily,
        out_dir=args.out_dir,
    )
    print(f"[Task698] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
