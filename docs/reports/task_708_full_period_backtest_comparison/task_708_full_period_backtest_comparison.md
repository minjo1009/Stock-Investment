# Task708 Full Period Backtest Comparison

## Decision Summary

- Verdict: TIERED_SOURCE_RISK_BACKTEST_COMPLETE_RESEARCH_ONLY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: Tiered action cohorts are compared against all candidates, event-linked candidates, Task703 eligible, and QQQ with $1,000 capital.
- Next action: Use subtype attribution and winner preservation before any rule promotion discussion..

## Quant Expert Report

- Data source and source readiness: current Task636/672/684/689/703/704 artifacts only.
- Exact join keys: `lifecycle_id`, `symbol`, `theme_id`, `entry_ts`, `split_name` where applicable.
- Leakage audit: outcome/future-price assignment flags are kept at zero before evaluation.
- Split/OOS metrics: included where PnL is evaluated; otherwise not applicable.
- Failure decomposition: see CSV artifacts in this directory.
- Cost/slippage stress where PnL changed: included for Task708; otherwise not applicable.
- Remaining blockers: strategy remains NOT_ACCEPTED and real capital remains FORBIDDEN.

## No-Background Decision-Maker Report

- What happened: Tiered action cohorts are compared against all candidates, event-linked candidates, Task703 eligible, and QQQ with $1,000 capital.
- Why it matters: the project separates source risk, context, action tiers, evaluation, and governance instead of fixing rules after seeing returns.
- Whether this changes capital/deployment readiness: no.
- Plain-language next step: inspect the diagnostics before changing thresholds.

## Artifact Manifest

- Inputs: upstream governed task artifacts.
- Outputs: task708_eval_panel.csv, task708_portfolio_comparison.csv, task708_accepted_trades.csv, task708_equity_curves.csv, task708_split_summary.csv, task708_cost_stress_summary.csv, task_708_decision.csv, task_708_pass_fail_matrix.csv.
- Row counts: task708_eval_panel.csv=5265; task708_portfolio_comparison.csv=19; task708_accepted_trades.csv=1894; task708_equity_curves.csv=3788; task708_split_summary.csv=16; task708_cost_stress_summary.csv=54; task_708_decision.csv=1; task_708_pass_fail_matrix.csv=5.
- Validation commands: see task registry.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| eval_scope_5265 | PRIMARY_PASS | 1 | rows=5265 | 5265 |
| event_linked_scope_2445 | PRIMARY_PASS | 1 | event=2445 | 2445 |
| tiered_candidates_nonzero | PRIMARY_PASS | 1 | trade_candidates=1951 | >0 |
| portfolio_cohorts_present | PRIMARY_PASS | 1 | cohorts=7 | >=7 |
| no_assignment_leakage | PRIMARY_PASS | 1 | assignment leakage=0 | 0 |
