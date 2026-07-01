# Task618 $1000 Capital Portfolio Comparison

## Decision Summary

- Verdict: `PASS_TURBOQUANT_1000_CAPITAL_ALL_CAPACITY_DIAGNOSTIC`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Starting capital: $1,000.00
- Best result: `turboquant` at max 5 positions -> $4,310.96.
- Unlimited total return is not treated as account return because it assumes unlimited capital and unlimited overlapping positions.

## Quant Expert Report

### Portfolio Summary

| Max Positions | Universe | Final $ | Return | Trades Used | Skipped | Max DD |
|---:|---|---:|---:|---:|---:|---:|
| 5 | `all_candidates` | $1,068.09 | 6.81% | 58 | 4983 | -43.26% |
| 5 | `turboquant` | $4,310.96 | 331.10% | 44 | 691 | -9.61% |
| 10 | `all_candidates` | $2,164.06 | 116.41% | 111 | 4930 | -26.44% |
| 10 | `turboquant` | $3,347.30 | 234.73% | 86 | 649 | -8.04% |
| 20 | `all_candidates` | $2,298.19 | 129.82% | 226 | 4815 | -24.72% |
| 20 | `turboquant` | $3,022.45 | 202.24% | 159 | 576 | -12.91% |
| 50 | `all_candidates` | $2,358.84 | 135.88% | 563 | 4478 | -20.81% |
| 50 | `turboquant` | $2,491.94 | 149.19% | 333 | 402 | -15.58% |

### Capacity Winners

| Max Positions | Winner | Winner Final $ | Other Final $ | Edge $ |
|---:|---|---:|---:|---:|
| 5 | `turboquant` | $4,310.96 | $1,068.09 | $3,242.88 |
| 10 | `turboquant` | $3,347.30 | $2,164.06 | $1,183.24 |
| 20 | `turboquant` | $3,022.45 | $2,298.19 | $724.26 |
| 50 | `turboquant` | $2,491.94 | $2,358.84 | $133.10 |

### Source And Leakage Audit

- Source: `docs/reports/task_617_turboquant_fresh_strategy_backtest`
- Baseline candidates: 5041
- TurboQuant candidates: 735
- Entry window: 2024-01-02 14:30:00+00:00 to 2026-05-08 18:15:00+00:00
- Same-timestamp entries are ordered deterministically by `entry_ts` then `lifecycle_id` before capacity simulation.
- No GPT/plugin output is used as a source or score input.
- Labels/outcomes are not used in assignment logic.

## No-Background Decision-Maker Report

- With a $1000 account, TurboQuant wins at max positions 5, 10, 20, and 50.
- The all-candidate universe has many more candidates, but most cannot be entered under the same account capacity.
- In this comparison, TurboQuant is better on final account dollars, not only average return.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `same_initial_capital` | 1 | $1000.00 | $1000 same starting capital |
| `same_capacity_grid` | 1 | 5,10,20,50 | 5,10,20,50 |
| `turboquant_same_capital_capacity_edge` | 1 | 5=turboquant; 10=turboquant; 20=turboquant; 50=turboquant | turboquant wins every tested max-position capacity |
| `trading_promotion` | 0 | PASS_TURBOQUANT_1000_CAPITAL_ALL_CAPACITY_DIAGNOSTIC | cost/slippage, recent OOS, and live-source gates must pass |

## Artifact Manifest

### Inputs

- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_baseline_all_candidate_backtest_panel.csv`
- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`

### Outputs

- `task_618_1000_capital_portfolio_summary.csv`
- `task_618_capacity_winner_summary.csv`
- `task_618_1000_capital_equity_curve.csv`
- `task_618_source_audit.csv`
- `task_618_pass_fail_matrix.csv`
- `task_618_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task618_1000_capital_portfolio_comparison`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`