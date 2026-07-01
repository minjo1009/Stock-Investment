# Task616 TurboQuant Intelligence Chart Fusion Backtest

## Decision Summary

- Verdict: `PASS_TURBOQUANT_FUSION_DIAGNOSTIC_FAIL_TRADING_PROMOTION`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Baseline: 89 entries, 9.32% avg return, 39.33% failure rate.
- Fusion accepted: 67 entries, 14.16% avg return, +4.83pp vs baseline.
- Fusion failure rate: 34.33% (-5.00pp vs baseline).
- Quarter check: 4/7 positive quarters.
- Next action: exact delayed-entry/confirmation replay with cost.

## Quant Expert Report

### Data Source And Source Readiness

- Input is Task614 `entry_p0_intelligence_linkage.csv`: chart/path features plus P0/P1 intelligence event flags.
- Task615 keeps the event store alive during runtime; Task616 uses the historical linked panel for backtest only.
- GPT/plugin outputs are not used as source facts or assignments.

### Exact Join Keys

- Intelligence events were already linked by Task614 using timestamp/date, symbol/theme tags, and no lifecycle fallback.
- Task616 only reads exact `lifecycle_id` rows from the linked panel.

### Leakage Audit

- Assignment features exclude `entry_reduce_failure_flag`, `net_return_from_entry`, and taxonomy labels.
- Labels and returns are used only after assignment for evaluation.

### Scenario Summary

| Scenario | Action | Selected | Failure Rate | Avg Return | Return Delta |
|---|---|---:|---:|---:|---:|
| `turbo_fusion_accept_h60_i70_riskoff` | `accept_filter` | 67 | 34.33% | 14.16% | 4.83pp |
| `turbo_fusion_accept_h80_i70_riskoff` | `accept_filter` | 62 | 33.87% | 13.19% | 3.87pp |
| `intelligence_support_ge_0_70_only` | `accept_filter` | 71 | 36.62% | 12.67% | 3.35pp |
| `chart_riskoff_only` | `accept_filter` | 83 | 36.14% | 10.99% | 1.67pp |
| `chart_health_ge_0_60_only` | `accept_filter` | 88 | 38.64% | 9.66% | 0.34pp |
| `baseline_all_entries` | `all` | 89 | 39.33% | 9.32% | 0.00pp |
| `turbo_fusion_review_chart_risk_and_i70` | `risk_filter` | 3 | 66.67% | -9.38% | -18.71pp |

### Quarter Stability

| Quarter | Entries | Accepted | Base Return | Accepted Return | Positive |
|---|---:|---:|---:|---:|---:|
| `2024Q4` | 5 | 3 | 57.82% | 80.12% | 1 |
| `2025Q1` | 16 | 4 | -13.51% | -15.59% | 0 |
| `2025Q2` | 10 | 10 | 45.32% | 45.32% | 0 |
| `2025Q3` | 13 | 13 | 3.66% | 3.66% | 0 |
| `2025Q4` | 19 | 17 | 8.82% | 10.39% | 1 |
| `2026Q1` | 12 | 7 | 2.96% | 3.28% | 1 |
| `2026Q2` | 14 | 13 | 3.81% | 5.40% | 1 |

### Architecture

| Layer | Status | Role |
|---|---|---|
| `G0 source_store` | `CONNECTED_DIAGNOSTIC` | collect political, geopolitical, institution, and IR proxy events before linkage |
| `G1 chart_health` | `CONNECTED_DIAGNOSTIC` | keep simple chart continuation quality score |
| `G2 chart_risk_guard` | `CONNECTED_DIAGNOSTIC` | wait-window risk guard for review or size-down testing |
| `G3 intelligence_support` | `CONNECTED_DIAGNOSTIC` | use source context as confirmation, not as direct trading truth |
| `G4 fusion_action` | `BACKTEST_ONLY` | accept, review, or reject candidates in backtest only |
| `G5 promotion_gate` | `ENFORCED` | block strategy promotion until evidence is stronger |

### Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `source_chart_fusion_connected` | 1 | attached_source_groups=4; fusion_selected=67 | >=3 source groups and >0 fusion selected rows |
| `diagnostic_performance_candidate` | 1 | selected=67; return_delta=4.83pp; failure_delta=-5.00pp | selected>=50; return_delta>=3pp; failure_delta<=-3pp |
| `quarter_stability` | 1 | positive_quarters=4/7 | >=4 positive quarters across >=6 quarters |
| `leakage_guard` | 1 | label_used=0; gpt_or_plugin_source=0 | must be 0 |
| `trading_promotion` | 0 | diagnostic fusion uses simulated original entry returns; no delayed-entry fill, cost, or full OOS replay yet | requires exact delayed-entry/exit replay, cost/slippage, source audit, and live readiness |

## No-Background Decision-Maker Report

- Direction is right: chart plus intelligence beats chart-only diagnostic baseline in this panel.
- It is not ready for real trading: the replay still uses original simulated entry returns.
- Keep it as a TurboQuant backtest candidate, then rerun with delayed-entry fills and costs.

## Artifact Manifest

### Inputs

- `docs/reports/task_614_p0_intelligence_source_attachment/entry_p0_intelligence_linkage.csv`

### Outputs

- `turboquant_fusion_entry_panel.csv`
- `turboquant_fusion_scenario_summary.csv`
- `turboquant_fusion_quarter_summary.csv`
- `turboquant_fusion_architecture.csv`
- `task_616_pass_fail_matrix.csv`
- `task_616_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task616_turboquant_intelligence_chart_fusion_backtest`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`