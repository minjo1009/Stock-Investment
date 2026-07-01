# Task617 TurboQuant Fresh Strategy Backtest

## Decision Summary

- Verdict: `PASS_FRESH_TURBOQUANT_DIAGNOSTIC_FAIL_PORTFOLIO_CAPACITY_AND_RECENT_OOS`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Fresh baseline candidates: 5265, avg return 5.82%, entry-reduce failure 40.82%.
- Fresh TurboQuant trades: 633, avg return 13.39%, delta 7.57pp.
- GPT review status: `CAPTURED_NEW_ALLOWED_TAB`
- Next action: GPT review capture, cost/slippage, and parameter-neighborhood robustness.

## Quant Expert Report

### Data Source And Source Readiness

- This is a fresh raw-generated backtest, not a refilter of the 89-entry Task608K/Task614 panel.
- Candidates are generated from raw daily bars and raw intraday bars.
- Task614/Task615 event store is attached before strategy scoring.

### Exact Join Keys

- Candidate id is rebuilt as `TASK617|symbol|entry_timestamp`.
- Intelligence events are joined by event timestamp/date known before entry, symbol/theme tags, and source lane.
- No symbol/date/price/time proximity lifecycle fallback is used.

### Leakage Audit

- Entry assignment does not use returns, exit labels, taxonomy labels, win flags, or entry-reduce labels.
- GPT output is not used as a data source or score input.

### Scenario Summary

| Scenario | Count | Avg Return | Win | Entry-Reduce |
|---|---:|---:|---:|---:|
| `fresh_baseline_all_candidates` | 5265 | 5.82% | 53.43% | 40.82% |
| `fresh_turboquant_strategy` | 633 | 13.39% | 63.03% | 32.23% |

### Split Summary

| Split | Count | Avg Return | Win | Entry-Reduce | Positive |
|---|---:|---:|---:|---:|---:|
| `train_design` | 320 | 19.60% | 74.06% | 22.50% | 1 |
| `validation` | 210 | 9.08% | 60.95% | 32.38% | 1 |
| `recent_oos` | 103 | 2.85% | 33.01% | 62.14% | 0 |

### Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `fresh_candidate_generation` | 1 | baseline_candidates=5265 | >=300 fresh raw-generated candidates |
| `fresh_strategy_diagnostic_performance` | 1 | strategy_count=633; strategy_avg=13.39%; baseline_avg=5.82%; strategy_entry_reduce=32.23%; baseline_entry_reduce=40.82% | count>=50; avg return >= baseline+2pp; entry_reduce <= baseline |
| `split_stability` | 1 | positive_splits=2/3 | >=2 positive splits across >=3 splits |
| `gpt_review` | 1 | CAPTURED_NEW_ALLOWED_TAB | captured via allowed 1. coding/investment ChatGPT tab |
| `trading_promotion` | 0 | fresh diagnostic backtest only; cost, slippage, broker truth, and GPT review are not complete | must pass before live or real capital |

## No-Background Decision-Maker Report

- This time it is a new backtest.
- It rebuilds candidates from raw bars, then attaches intelligence, then trades the new TurboQuant rule.
- The result is useful, but GPT review and trading promotion are still blocked.

## Artifact Manifest

### Inputs

- `data/raw/theme_universe_10x7.csv`
- `data/raw/us_daily_breadth_top500/`
- `data/raw/us_intraday/`
- `data/artifacts/task_614_p0_intelligence_source_attachment/p0_intelligence_event_store.csv`

### Outputs

- `fresh_daily_candidate_panel.csv`
- `fresh_intraday_confirmed_entry_panel.csv`
- `fresh_intelligence_linked_entry_panel.csv`
- `fresh_turboquant_scored_entry_panel.csv`
- `fresh_baseline_all_candidate_backtest_panel.csv`
- `fresh_turboquant_strategy_backtest_panel.csv`
- `fresh_turboquant_scenario_summary.csv`
- `fresh_turboquant_split_summary.csv`
- `task_617_pass_fail_matrix.csv`
- `task_617_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task617_turboquant_fresh_strategy_backtest`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`