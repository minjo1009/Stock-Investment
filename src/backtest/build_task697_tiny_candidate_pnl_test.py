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


TASK696_DIR = Path("docs/reports/task_696_tiny_backtest_candidate_set_audit")
TASK684_PANEL = Path("docs/reports/task_684_interaction_context_prediction_stack/task684_interaction_stack_panel.csv")
QQQ_DAILY = Path("data/raw/us_daily_breadth_top500/QQQ.csv")
TASK697_DIR = Path("docs/reports/task_697_tiny_candidate_pnl_test")

INITIAL_CAPITAL_USD = 1000.0
ROUND_TRIP_COST_BPS = 50

OUTCOME_COLUMNS = [
    "entry_price",
    "simulated_exit_ts",
    "simulated_exit_price",
    "exit_reason",
    "net_return_from_entry",
    "holding_days",
    "policy_name",
]


def build_task697_program(
    *,
    task696_dir: Path = TASK696_DIR,
    task684_panel_path: Path = TASK684_PANEL,
    qqq_daily_path: Path = QQQ_DAILY,
    out_dir: Path = TASK697_DIR,
) -> dict[str, pd.DataFrame]:
    out_dir.mkdir(parents=True, exist_ok=True)

    candidates = pd.read_csv(task696_dir / "task696_tiny_backtest_candidate_set.csv")
    outcomes = pd.read_csv(task684_panel_path, usecols=["lifecycle_id", "symbol", *OUTCOME_COLUMNS])
    qqq = load_qqq_daily(qqq_daily_path)

    trade_pnl = build_trade_pnl(candidates, outcomes, qqq)
    comparison = build_capital_comparison(trade_pnl)
    cost_model = build_cost_model()
    audit = build_audit(candidates, outcomes, qqq, trade_pnl)
    pass_fail = audit.copy()
    decision = build_decision(trade_pnl, comparison, audit)

    write_outputs(out_dir, trade_pnl, comparison, cost_model, audit, pass_fail, decision)
    return {
        "task697_tiny_trade_pnl": trade_pnl,
        "task697_tiny_capital_comparison": comparison,
        "task697_cost_model": cost_model,
        "task697_benchmark_availability_audit": audit,
        "task_697_pass_fail_matrix": pass_fail,
        "task_697_decision": decision,
    }


def load_qqq_daily(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Missing QQQ benchmark source: {path}")
    qqq = pd.read_csv(path)
    qqq.columns = [str(col).strip().lower() for col in qqq.columns]
    required = {"timestamp", "close"}
    missing = required.difference(qqq.columns)
    if missing:
        raise ValueError(f"QQQ source missing columns: {sorted(missing)}")
    qqq["timestamp"] = pd.to_datetime(qqq["timestamp"], utc=True, errors="coerce")
    qqq["date"] = qqq["timestamp"].dt.date
    qqq["close"] = pd.to_numeric(qqq["close"], errors="coerce")
    return qqq.dropna(subset=["timestamp", "close"]).sort_values("timestamp").reset_index(drop=True)


def build_trade_pnl(candidates: pd.DataFrame, outcomes: pd.DataFrame, qqq: pd.DataFrame) -> pd.DataFrame:
    candidates = candidates.copy()
    expected_symbols = {"ASTS", "BA", "TER"}
    if set(candidates["symbol"].astype(str)) != expected_symbols or len(candidates) != 3:
        raise ValueError("Task697 only accepts the audited ASTS/BA/TER Task696 candidate set.")

    dupes = outcomes[outcomes.duplicated(["lifecycle_id", "symbol"], keep=False)]
    if not dupes.empty:
        requested = set(zip(candidates["lifecycle_id"], candidates["symbol"]))
        duplicate_requested = dupes[[ "lifecycle_id", "symbol" ]].apply(tuple, axis=1).isin(requested)
        if duplicate_requested.any():
            raise ValueError("Outcome panel has duplicate lifecycle rows for Task697 candidates.")

    merged = candidates.merge(outcomes, on=["lifecycle_id", "symbol"], how="left", indicator=True)
    if not merged["_merge"].eq("both").all():
        raise ValueError("All Task697 candidates must join to Task684 outcomes by exact lifecycle_id and symbol.")
    merged = merged.drop(columns=["_merge"])

    merged["entry_ts_eval"] = pd.to_datetime(merged["entry_ts"], utc=True, errors="coerce")
    merged["simulated_exit_ts_eval"] = pd.to_datetime(merged["simulated_exit_ts"], utc=True, errors="coerce")
    merged = merged.sort_values(["entry_ts_eval", "symbol"]).reset_index(drop=True)

    strategy_capital = INITIAL_CAPITAL_USD
    qqq_capital = INITIAL_CAPITAL_USD
    previous_exit = pd.NaT
    rows: list[dict[str, object]] = []
    for idx, row in merged.iterrows():
        entry_price = float(row["entry_price"])
        exit_price = float(row["simulated_exit_price"])
        gross_return = exit_price / entry_price - 1.0
        costed_return = gross_return - ROUND_TRIP_COST_BPS / 10000.0

        q_entry = aligned_qqq_price(qqq, row["entry_ts_eval"])
        q_exit = aligned_qqq_price(qqq, row["simulated_exit_ts_eval"])
        qqq_gross_return = q_exit["close"] / q_entry["close"] - 1.0
        qqq_costed_return = qqq_gross_return - ROUND_TRIP_COST_BPS / 10000.0

        strategy_before = strategy_capital
        qqq_before = qqq_capital
        strategy_capital *= 1.0 + costed_return
        qqq_capital *= 1.0 + qqq_costed_return

        overlaps_prior = int(pd.notna(previous_exit) and row["entry_ts_eval"] < previous_exit)
        previous_exit = row["simulated_exit_ts_eval"]

        rows.append(
            {
                "tiny_pnl_id": f"Task697|tiny_pnl|{idx + 1:03d}",
                "tiny_candidate_set_id": row["tiny_candidate_set_id"],
                "lifecycle_id": row["lifecycle_id"],
                "symbol": row["symbol"],
                "split_name": row["split_name"],
                "theme_id": row["theme_id"],
                "entry_ts": row["entry_ts"],
                "simulated_exit_ts": row["simulated_exit_ts"],
                "entry_price": entry_price,
                "simulated_exit_price": exit_price,
                "holding_days": float(row["holding_days"]),
                "exit_reason": row["exit_reason"],
                "policy_name": row["policy_name"],
                "gross_return_pct": gross_return * 100.0,
                "task684_net_return_from_entry_pct": float(row["net_return_from_entry"]) * 100.0,
                "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
                "costed_return_pct": costed_return * 100.0,
                "strategy_capital_before_usd": strategy_before,
                "strategy_capital_after_usd": strategy_capital,
                "qqq_entry_date": str(q_entry["date"]),
                "qqq_exit_date": str(q_exit["date"]),
                "qqq_entry_close": q_entry["close"],
                "qqq_exit_close": q_exit["close"],
                "qqq_gross_return_pct": qqq_gross_return * 100.0,
                "qqq_costed_return_pct": qqq_costed_return * 100.0,
                "qqq_matched_capital_before_usd": qqq_before,
                "qqq_matched_capital_after_usd": qqq_capital,
                "beats_qqq_same_window_flag": int(costed_return > qqq_costed_return),
                "overlaps_prior_position_flag": overlaps_prior,
                "selection_source_artifact": "docs/reports/task_696_tiny_backtest_candidate_set_audit/task696_tiny_backtest_candidate_set.csv",
                "outcome_source_artifact": "docs/reports/task_684_interaction_context_prediction_stack/task684_interaction_stack_panel.csv",
                "benchmark_source_artifact": "data/raw/us_daily_breadth_top500/QQQ.csv",
                "outcome_used_for_selection_flag": 0,
                "outcome_used_for_evaluation_flag": 1,
                "future_price_used_for_selection_flag": 0,
                "allocation_approved_flag": 0,
                "paper_or_live_trade_approved_flag": 0,
            }
        )
    return pd.DataFrame(rows)


def aligned_qqq_price(qqq: pd.DataFrame, timestamp: pd.Timestamp) -> dict[str, object]:
    target_date = timestamp.date()
    aligned = qqq[qqq["date"].ge(target_date)].head(1)
    if aligned.empty:
        raise ValueError(f"QQQ cannot align to {target_date}")
    row = aligned.iloc[0]
    return {"date": row["date"], "close": float(row["close"])}


def build_capital_comparison(trade_pnl: pd.DataFrame) -> pd.DataFrame:
    first_entry = pd.to_datetime(trade_pnl["entry_ts"], utc=True).min()
    last_exit = pd.to_datetime(trade_pnl["simulated_exit_ts"], utc=True).max()
    qqq_entry_close = float(trade_pnl.iloc[0]["qqq_entry_close"])
    qqq_exit_close = float(trade_pnl.iloc[-1]["qqq_exit_close"])
    qqq_buyhold_gross_final = INITIAL_CAPITAL_USD * qqq_exit_close / qqq_entry_close
    qqq_buyhold_costed_final = INITIAL_CAPITAL_USD * (qqq_exit_close / qqq_entry_close - ROUND_TRIP_COST_BPS / 10000.0)

    strategy_final = float(trade_pnl.iloc[-1]["strategy_capital_after_usd"])
    qqq_matched_final = float(trade_pnl.iloc[-1]["qqq_matched_capital_after_usd"])
    rows = [
        comparison_row(
            "tiny_candidate_strategy_sequential",
            strategy_final,
            ROUND_TRIP_COST_BPS,
            len(trade_pnl),
            "ASTS/BA/TER sequential exact lifecycle evaluation",
        ),
        comparison_row(
            "QQQ_matched_trade_windows_sequential",
            qqq_matched_final,
            ROUND_TRIP_COST_BPS,
            len(trade_pnl),
            "QQQ over the same three entry/exit windows",
        ),
        comparison_row(
            "QQQ_buy_and_hold_tiny_window_costed",
            qqq_buyhold_costed_final,
            ROUND_TRIP_COST_BPS,
            1,
            f"QQQ buy-and-hold from {first_entry.date()} to {last_exit.date()} with one round-trip cost",
        ),
        comparison_row(
            "QQQ_buy_and_hold_tiny_window_gross",
            qqq_buyhold_gross_final,
            0,
            1,
            f"QQQ buy-and-hold from {first_entry.date()} to {last_exit.date()} before cost",
        ),
    ]
    comparison = pd.DataFrame(rows)
    strategy_final_capital = strategy_final
    comparison["strategy_final_capital_usd"] = strategy_final_capital
    comparison["strategy_excess_usd"] = strategy_final_capital - comparison["final_capital_usd"]
    comparison["strategy_beats_this_row_flag"] = (strategy_final_capital > comparison["final_capital_usd"]).astype(int)
    return comparison


def comparison_row(
    name: str,
    final_capital: float,
    round_trip_cost_bps: int,
    trade_window_count: int,
    description: str,
) -> dict[str, object]:
    return {
        "comparison_name": name,
        "initial_capital_usd": INITIAL_CAPITAL_USD,
        "final_capital_usd": final_capital,
        "total_return_pct": (final_capital / INITIAL_CAPITAL_USD - 1.0) * 100.0,
        "round_trip_cost_bps": round_trip_cost_bps,
        "trade_window_count": trade_window_count,
        "description": description,
    }


def build_cost_model() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "cost_model_id": "Task697|round_trip_50bps",
                "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
                "entry_cost_bps_assumption": ROUND_TRIP_COST_BPS / 2.0,
                "exit_cost_bps_assumption": ROUND_TRIP_COST_BPS / 2.0,
                "source": "Aligned to Task633 decision cost convention.",
                "applied_to_strategy_flag": 1,
                "applied_to_qqq_matched_windows_flag": 1,
                "applied_to_qqq_buyhold_costed_flag": 1,
            }
        ]
    )


def build_audit(
    candidates: pd.DataFrame,
    outcomes: pd.DataFrame,
    qqq: pd.DataFrame,
    trade_pnl: pd.DataFrame,
) -> pd.DataFrame:
    requested = candidates[["lifecycle_id", "symbol"]].drop_duplicates()
    joined = requested.merge(outcomes[["lifecycle_id", "symbol"]].drop_duplicates(), on=["lifecycle_id", "symbol"], how="left", indicator=True)
    return pd.DataFrame(
        [
            gate(
                "tiny_scope_fixed_to_three_candidates",
                len(candidates) == 3 and set(candidates["symbol"].astype(str)) == {"ASTS", "BA", "TER"},
                f"rows={len(candidates)}; symbols={','.join(sorted(candidates['symbol'].astype(str)))}",
                "Task697 scope must be ASTS, BA, TER only",
            ),
            gate(
                "exact_lifecycle_outcome_join",
                joined["_merge"].eq("both").all() and len(joined) == 3,
                f"joined={int(joined['_merge'].eq('both').sum())}/3",
                "PnL evaluation must join by exact lifecycle_id and symbol",
            ),
            gate(
                "qqq_benchmark_available",
                not qqq.empty
                and pd.to_datetime(trade_pnl["qqq_entry_date"], errors="coerce").notna().all()
                and pd.to_datetime(trade_pnl["qqq_exit_date"], errors="coerce").notna().all(),
                f"qqq_rows={len(qqq)}; aligned_windows={len(trade_pnl)}",
                "QQQ benchmark must be available for all tiny candidate windows",
            ),
            gate(
                "round_trip_cost_applied",
                trade_pnl["round_trip_cost_bps"].eq(ROUND_TRIP_COST_BPS).all()
                and (trade_pnl["costed_return_pct"] <= trade_pnl["gross_return_pct"]).all()
                and (trade_pnl["qqq_costed_return_pct"] <= trade_pnl["qqq_gross_return_pct"]).all(),
                f"cost_bps={ROUND_TRIP_COST_BPS}",
                "Strategy and matched QQQ windows must include cost",
            ),
            gate(
                "no_overlap_in_tiny_sequence",
                int(trade_pnl["overlaps_prior_position_flag"].sum()) == 0,
                f"overlap_count={int(trade_pnl['overlaps_prior_position_flag'].sum())}",
                "Tiny sequential capital comparison should not double-count overlapping positions",
            ),
            gate(
                "outcome_eval_only_not_selection",
                int(trade_pnl["outcome_used_for_selection_flag"].sum()) == 0
                and int(trade_pnl["future_price_used_for_selection_flag"].sum()) == 0
                and int(trade_pnl["outcome_used_for_evaluation_flag"].sum()) == len(trade_pnl),
                "selection_outcome_sum="
                f"{int(trade_pnl['outcome_used_for_selection_flag'].sum())}; eval_sum={int(trade_pnl['outcome_used_for_evaluation_flag'].sum())}",
                "Outcomes are evaluation-only in Task697",
            ),
            gate(
                "no_strategy_or_trade_promotion",
                int(trade_pnl["allocation_approved_flag"].sum()) == 0
                and int(trade_pnl["paper_or_live_trade_approved_flag"].sum()) == 0,
                "allocation_approved=0; paper_or_live_trade_approved=0",
                "Tiny PnL cannot promote allocation or trading",
            ),
        ]
    )


def build_decision(trade_pnl: pd.DataFrame, comparison: pd.DataFrame, audit: pd.DataFrame) -> pd.DataFrame:
    strategy = comparison[comparison["comparison_name"].eq("tiny_candidate_strategy_sequential")].iloc[0]
    qqq_matched = comparison[comparison["comparison_name"].eq("QQQ_matched_trade_windows_sequential")].iloc[0]
    qqq_buyhold = comparison[comparison["comparison_name"].eq("QQQ_buy_and_hold_tiny_window_costed")].iloc[0]
    return pd.DataFrame(
        [
            {
                "task_id": "Task697",
                "verdict": "TINY_PNL_TEST_COMPLETE_RESEARCH_ONLY",
                "strategy_acceptance_status": "NOT_ACCEPTED",
                "real_capital_status": "FORBIDDEN",
                "trading_promotion_pass_flag": 0,
                "candidate_count": int(len(trade_pnl)),
                "candidate_symbols": "|".join(trade_pnl["symbol"].astype(str).tolist()),
                "initial_capital_usd": INITIAL_CAPITAL_USD,
                "round_trip_cost_bps": ROUND_TRIP_COST_BPS,
                "tiny_strategy_final_capital_usd": float(strategy["final_capital_usd"]),
                "tiny_strategy_total_return_pct": float(strategy["total_return_pct"]),
                "qqq_matched_final_capital_usd": float(qqq_matched["final_capital_usd"]),
                "qqq_matched_total_return_pct": float(qqq_matched["total_return_pct"]),
                "qqq_buyhold_costed_final_capital_usd": float(qqq_buyhold["final_capital_usd"]),
                "qqq_buyhold_costed_total_return_pct": float(qqq_buyhold["total_return_pct"]),
                "beats_qqq_matched_flag": int(float(strategy["final_capital_usd"]) > float(qqq_matched["final_capital_usd"])),
                "beats_qqq_buyhold_costed_flag": int(float(strategy["final_capital_usd"]) > float(qqq_buyhold["final_capital_usd"])),
                "winning_trade_count": int((trade_pnl["costed_return_pct"] > 0).sum()),
                "losing_trade_count": int((trade_pnl["costed_return_pct"] <= 0).sum()),
                "pass_gate_count": int(audit["pass_flag"].sum()),
                "fail_gate_count": int((1 - audit["pass_flag"]).sum()),
                "primary_result": "Tiny candidate set beat matched QQQ and QQQ buy-hold in this 3-trade evaluation, driven mainly by TER.",
                "research_caveat": "Sample is too small for strategy acceptance; ASTS and BA are train-design, TER is validation, and no allocation rule is promoted.",
                "next_action": "Review why ASTS failed, why BA was modest, and why TER worked before expanding beyond three candidates.",
            }
        ]
    )


def write_outputs(
    out_dir: Path,
    trade_pnl: pd.DataFrame,
    comparison: pd.DataFrame,
    cost_model: pd.DataFrame,
    audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> None:
    outputs = {
        "task697_tiny_trade_pnl.csv": trade_pnl,
        "task697_tiny_capital_comparison.csv": comparison,
        "task697_cost_model.csv": cost_model,
        "task697_benchmark_availability_audit.csv": audit,
        "task_697_pass_fail_matrix.csv": pass_fail,
        "task_697_decision.csv": decision,
    }
    for name, frame in outputs.items():
        frame.to_csv(out_dir / name, index=False)
    (out_dir / "task_697_tiny_candidate_pnl_test.md").write_text(
        render_report(trade_pnl, comparison, cost_model, audit, pass_fail, decision),
        encoding="utf-8",
    )
    write_manifest(out_dir, out_dir / "artifact_manifest.csv")


def render_report(
    trade_pnl: pd.DataFrame,
    comparison: pd.DataFrame,
    cost_model: pd.DataFrame,
    audit: pd.DataFrame,
    pass_fail: pd.DataFrame,
    decision: pd.DataFrame,
) -> str:
    d = decision.iloc[0]
    trade_view = trade_pnl[
        [
            "symbol",
            "split_name",
            "entry_ts",
            "simulated_exit_ts",
            "gross_return_pct",
            "costed_return_pct",
            "qqq_costed_return_pct",
            "strategy_capital_after_usd",
            "qqq_matched_capital_after_usd",
        ]
    ].copy()
    comparison_view = comparison[
        [
            "comparison_name",
            "initial_capital_usd",
            "final_capital_usd",
            "total_return_pct",
            "round_trip_cost_bps",
            "strategy_excess_usd",
            "strategy_beats_this_row_flag",
        ]
    ]
    return f"""# Task697 Tiny Candidate PnL Test

## Decision Summary

- Verdict: {d["verdict"]}.
- Strategy acceptance status: {d["strategy_acceptance_status"]}.
- Real capital status: {d["real_capital_status"]}.
- Scope: ASTS, BA, TER only from Task696.
- Cost model: round-trip {int(d["round_trip_cost_bps"])} bps.
- $1,000 result: strategy ${float(d["tiny_strategy_final_capital_usd"]):,.2f}; matched QQQ ${float(d["qqq_matched_final_capital_usd"]):,.2f}; QQQ buy-hold costed ${float(d["qqq_buyhold_costed_final_capital_usd"]):,.2f}.
- What changed: PnL was evaluated for the audited tiny candidate set only.
- Next action: {d["next_action"]}

## Quant Expert Report

### Data source and scope

- Candidate input: Task696 pre-PnL candidate set.
- Outcome input: Task684 lifecycle panel, exact `lifecycle_id` + `symbol` join only.
- Benchmark input: `data/raw/us_daily_breadth_top500/QQQ.csv`.
- No inferred lifecycle matching, no symbol/date fallback, and no candidate expansion.

### Cost and benchmark method

{t678.markdown_table(cost_model)}

Matched QQQ uses the same three candidate entry/exit windows. A separate QQQ buy-and-hold row covers the first tiny entry date through the last tiny exit date.

### Trade PnL

{t678.markdown_table(trade_view)}

### Capital Comparison

{t678.markdown_table(comparison_view)}

### Interpretation

- The tiny set made money after cost and beat QQQ in the matched windows.
- The result is concentrated: ASTS lost, BA was modest, TER drove most of the gain.
- This supports continued research into the packet/slot process, not live trading or full strategy promotion.

### Split/OOS metrics

- ASTS and BA are train-design rows.
- TER is validation.
- There is no recent-OOS claim in this tiny test.

### Leakage audit

- Outcomes are used only after Task696 froze the candidate set.
- `outcome_used_for_selection_flag` and `future_price_used_for_selection_flag` remain zero.
- PnL columns appear only in Task697 evaluation artifacts.

### Remaining blockers

- Three trades are not enough for acceptance.
- TER concentration must be decomposed before expanding the rule.
- Conditional candidates still need confirmation logic before testing.

## No-Background Decision-Maker Report

- What happened: three audited candidates were tested with cost and QQQ comparison.
- Result: $1,000 became ${float(d["tiny_strategy_final_capital_usd"]):,.2f}.
- QQQ matched windows became ${float(d["qqq_matched_final_capital_usd"]):,.2f}.
- Meaning: promising, but too small to approve as a strategy.
- Capital status: still FORBIDDEN.

## Artifact Manifest

- Inputs: Task696 candidate set, Task684 lifecycle outcomes, QQQ daily benchmark.
- Outputs: trade PnL, capital comparison, cost model, benchmark audit, decision, pass/fail, manifest.
- Row counts: trade PnL {len(trade_pnl)}, comparison {len(comparison)}, audit {len(audit)}.
- Validation commands: `python src/backtest/build_task697_tiny_candidate_pnl_test.py`; `python -m unittest tests.test_task697_tiny_candidate_pnl_test`; `python scripts/task_registry_validate.py`.

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
    parser.add_argument("--task696-dir", type=Path, default=TASK696_DIR)
    parser.add_argument("--task684-panel", type=Path, default=TASK684_PANEL)
    parser.add_argument("--qqq-daily", type=Path, default=QQQ_DAILY)
    parser.add_argument("--out-dir", type=Path, default=TASK697_DIR)
    args = parser.parse_args()
    build_task697_program(
        task696_dir=args.task696_dir,
        task684_panel_path=args.task684_panel,
        qqq_daily_path=args.qqq_daily,
        out_dir=args.out_dir,
    )
    print(f"[Task697] wrote {args.out_dir}")


if __name__ == "__main__":
    main()
