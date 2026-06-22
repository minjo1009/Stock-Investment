# Task697 Tiny Candidate PnL Test

## Decision Summary

- Verdict: TINY_PNL_TEST_COMPLETE_RESEARCH_ONLY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Scope: ASTS, BA, TER only from Task696.
- Cost model: round-trip 50 bps.
- $1,000 result: strategy $1,594.47; matched QQQ $1,054.48; QQQ buy-hold costed $1,175.24.
- What changed: PnL was evaluated for the audited tiny candidate set only.
- Next action: Review why ASTS failed, why BA was modest, and why TER worked before expanding beyond three candidates.

## Quant Expert Report

### Data source and scope

- Candidate input: Task696 pre-PnL candidate set.
- Outcome input: Task684 lifecycle panel, exact `lifecycle_id` + `symbol` join only.
- Benchmark input: `data/raw/us_daily_breadth_top500/QQQ.csv`.
- No inferred lifecycle matching, no symbol/date fallback, and no candidate expansion.

### Cost and benchmark method

| cost_model_id | round_trip_cost_bps | entry_cost_bps_assumption | exit_cost_bps_assumption | source | applied_to_strategy_flag | applied_to_qqq_matched_windows_flag | applied_to_qqq_buyhold_costed_flag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Task697\|round_trip_50bps | 50 | 25.0000 | 25.0000 | Aligned to Task633 decision cost convention. | 1 | 1 | 1 |

Matched QQQ uses the same three candidate entry/exit windows. A separate QQQ buy-and-hold row covers the first tiny entry date through the last tiny exit date.

### Trade PnL

| symbol | split_name | entry_ts | simulated_exit_ts | gross_return_pct | costed_return_pct | qqq_costed_return_pct | strategy_capital_after_usd | qqq_matched_capital_after_usd |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASTS | train_design | 2025-02-12 14:30:00+00:00 | 2025-03-20 00:00:00+00:00 | -13.2771 | -13.7771 | -9.7826 | 862.2287 | 902.1740 |
| BA | train_design | 2025-05-30 14:30:00+00:00 | 2025-08-25 00:00:00+00:00 | 9.7209 | 9.2209 | 9.3650 | 941.7343 | 986.6623 |
| TER | validation | 2025-09-10 14:30:00+00:00 | 2025-12-03 00:00:00+00:00 | 69.8120 | 69.3120 | 6.8739 | 1594.4690 | 1054.4841 |

### Capital Comparison

| comparison_name | initial_capital_usd | final_capital_usd | total_return_pct | round_trip_cost_bps | strategy_excess_usd | strategy_beats_this_row_flag |
| --- | --- | --- | --- | --- | --- | --- |
| tiny_candidate_strategy_sequential | 1000.0000 | 1594.4690 | 59.4469 | 50 | 0.0000 | 0 |
| QQQ_matched_trade_windows_sequential | 1000.0000 | 1054.4841 | 5.4484 | 50 | 539.9850 | 1 |
| QQQ_buy_and_hold_tiny_window_costed | 1000.0000 | 1175.2386 | 17.5239 | 50 | 419.2305 | 1 |
| QQQ_buy_and_hold_tiny_window_gross | 1000.0000 | 1180.2386 | 18.0239 | 0 | 414.2305 | 1 |

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
- Result: $1,000 became $1,594.47.
- QQQ matched windows became $1,054.48.
- Meaning: promising, but too small to approve as a strategy.
- Capital status: still FORBIDDEN.

## Artifact Manifest

- Inputs: Task696 candidate set, Task684 lifecycle outcomes, QQQ daily benchmark.
- Outputs: trade PnL, capital comparison, cost model, benchmark audit, decision, pass/fail, manifest.
- Row counts: trade PnL 3, comparison 4, audit 7.
- Validation commands: `python src/backtest/build_task697_tiny_candidate_pnl_test.py`; `python -m unittest tests.test_task697_tiny_candidate_pnl_test`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| tiny_scope_fixed_to_three_candidates | PRIMARY_PASS | 1 | rows=3; symbols=ASTS,BA,TER | Task697 scope must be ASTS, BA, TER only |
| exact_lifecycle_outcome_join | PRIMARY_PASS | 1 | joined=3/3 | PnL evaluation must join by exact lifecycle_id and symbol |
| qqq_benchmark_available | PRIMARY_PASS | 1 | qqq_rows=1256; aligned_windows=3 | QQQ benchmark must be available for all tiny candidate windows |
| round_trip_cost_applied | PRIMARY_PASS | 1 | cost_bps=50 | Strategy and matched QQQ windows must include cost |
| no_overlap_in_tiny_sequence | PRIMARY_PASS | 1 | overlap_count=0 | Tiny sequential capital comparison should not double-count overlapping positions |
| outcome_eval_only_not_selection | PRIMARY_PASS | 1 | selection_outcome_sum=0; eval_sum=3 | Outcomes are evaluation-only in Task697 |
| no_strategy_or_trade_promotion | PRIMARY_PASS | 1 | allocation_approved=0; paper_or_live_trade_approved=0 | Tiny PnL cannot promote allocation or trading |
