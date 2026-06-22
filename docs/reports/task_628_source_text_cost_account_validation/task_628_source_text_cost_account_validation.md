# Task628 Source Text Cost Account Validation

## Decision Summary

- Verdict: `FAIL_SOURCE_TEXT_COST_ACCOUNT_EDGE_NOT_ACCEPTED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Recent OOS 50bp hold wins: 2/4 capacities

## Quant Expert Report

### 50bp Account Matrix

| Scope | Universe | Max Positions | Final $ | Return |
|---|---|---:|---:|---:|
| `full_panel` | `source_text_aerospace_risk_hold` | 5 | $2,800.58 | 180.06% |
| `full_panel` | `turboquant_original` | 5 | $4,158.91 | 315.89% |
| `full_panel` | `source_text_aerospace_risk_hold` | 10 | $2,930.51 | 193.05% |
| `full_panel` | `turboquant_original` | 10 | $3,229.78 | 222.98% |
| `full_panel` | `source_text_aerospace_risk_hold` | 20 | $2,876.15 | 187.62% |
| `full_panel` | `turboquant_original` | 20 | $2,924.57 | 192.46% |
| `full_panel` | `source_text_aerospace_risk_hold` | 50 | $2,171.11 | 117.11% |
| `full_panel` | `turboquant_original` | 50 | $2,423.35 | 142.33% |
| `recent_oos` | `source_text_aerospace_risk_hold` | 5 | $1,182.12 | 18.21% |
| `recent_oos` | `turboquant_original` | 5 | $1,313.22 | 31.32% |
| `recent_oos` | `source_text_aerospace_risk_hold` | 10 | $1,165.75 | 16.58% |
| `recent_oos` | `turboquant_original` | 10 | $1,044.35 | 4.43% |
| `recent_oos` | `source_text_aerospace_risk_hold` | 20 | $1,027.78 | 2.78% |
| `recent_oos` | `turboquant_original` | 20 | $1,043.58 | 4.36% |
| `recent_oos` | `source_text_aerospace_risk_hold` | 50 | $1,100.24 | 10.02% |
| `recent_oos` | `turboquant_original` | 50 | $1,057.44 | 5.74% |
| `validation` | `source_text_aerospace_risk_hold` | 5 | $1,225.81 | 22.58% |
| `validation` | `turboquant_original` | 5 | $1,225.81 | 22.58% |
| `validation` | `source_text_aerospace_risk_hold` | 10 | $1,126.85 | 12.68% |
| `validation` | `turboquant_original` | 10 | $1,151.47 | 15.15% |
| `validation` | `source_text_aerospace_risk_hold` | 20 | $1,226.66 | 22.67% |
| `validation` | `turboquant_original` | 20 | $1,225.36 | 22.54% |
| `validation` | `source_text_aerospace_risk_hold` | 50 | $1,140.96 | 14.10% |
| `validation` | `turboquant_original` | 50 | $1,128.52 | 12.85% |

## No-Background Decision-Maker Report

- Source-text aerospace risk hold survives the 50bp recent-OOS account check.
- Source-text aerospace risk hold does not pass the 50bp account gate yet.
- Recent OOS wins only two of four capacities, and full panel loses all four capacities.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `recent_oos_50bp_account_edge` | 0 | hold_wins=2/4; max5 hold=$1182.12 original=$1313.22; max10 hold=$1165.75 original=$1044.35; max20 hold=$1027.78 original=$1043.58; max50 hold=$1100.24 original=$1057.44 | source-text hold beats original in at least 3 of 4 recent-OOS capacities at 50bp |
| `validation_50bp_not_broken` | 1 | hold_wins=2/4; max5 hold=$1225.81 original=$1225.81; max10 hold=$1126.85 original=$1151.47; max20 hold=$1226.66 original=$1225.36; max50 hold=$1140.96 original=$1128.52 | source-text hold does not break validation account performance at 50bp |
| `full_panel_50bp_account_edge` | 0 | hold_wins=0/4; max5 hold=$2800.58 original=$4158.91; max10 hold=$2930.51 original=$3229.78; max20 hold=$2876.15 original=$2924.57; max50 hold=$2171.11 original=$2423.35 | source-text hold should be at least mixed or better on full panel at 50bp |
| `trading_promotion` | 0 | cost/account diagnostic only | requires parameter/split robustness and live-source readiness before strategy use |

## Artifact Manifest

### Inputs

- `docs/reports/task_627_source_text_theme_linkage_validation/task_627_trade_text_linkage_attachment.csv`
- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`

### Outputs

- `task_628_cost_account_matrix.csv`
- `task_628_pass_fail_matrix.csv`
- `task_628_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task628_source_text_cost_account_validation`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`