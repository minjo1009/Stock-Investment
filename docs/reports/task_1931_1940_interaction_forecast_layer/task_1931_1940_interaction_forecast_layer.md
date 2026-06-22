# Task1931-1940 Interaction Forecast Layer

## Decision Summary

- Verdict: `interaction_forecast_layer_complete_diagnostic_only`.
- Policy: `interaction_forecast_top3_v1`.
- Final equity: 4044.9636.
- CAGR: 0.310991.
- MDD: -0.238745.
- Baseline: `sleeve_split_top3_v1` final 3944.5457, CAGR 0.304621, MDD -0.24476.
- Delta final equity: 100.4179.
- Joint diagnostic target met: 1.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Data source and exact join keys:

- Base book: `task1815_sleeve_risk_budget.csv`, keyed by `target_policy_variant_id`, `trade_spec_id`, and `decision_asof_ts`.
- Winner/source fields: `task1790_winner_defense_panel.csv`, joined by exact `trade_spec_id`.
- Rates/liquidity: `task1835_rates_liquidity_decision_asof_panel.csv`, joined by exact `decision_asof_ts`.
- SEC financing: `task1842_sec_dilution_decision_asof_links.csv` and `task1837_financing_dilution_extractor_contract.csv`, joined by exact `trade_spec_id` and `financing_source_packet_id`.
- Replay return source: prior controlled winner-defense replay trades. No new price matching or symbol/date fallback was used.

Leakage audit:

- Assignment fields are source-field-only.
- PnL, future return, and drawdown after entry are forbidden for assignment.
- Top5 gate is an eligibility audit only; no top5 replay was executed.
- Missing source is treated as a gap or lower confidence, not a negative label.

| Policy | Final | CAGR | MDD | Base Final | Base CAGR | Base MDD | Delta Final | Delta MDD | Joint Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `interaction_forecast_top3_v1` | 4044.9636 | 0.310991 | -0.238745 | 3944.5457 | 0.304621 | -0.24476 | 100.4179 | 0.006015 | 1 |

Split/OOS metrics:

| Window | Final | Return | MDD |
| --- | ---: | ---: | ---: |
| IS_2021_2023 | 2027.2875 | 1.027287 | -0.238745 |
| OOS_2024_2026Q1 | 4044.9636 | 3.044964 | -0.171314 |

Cost/slippage stress:

| Cost bps | Stressed Final | Beats QQQ |
| ---: | ---: | ---: |
| 0 | 4044.9636 | 1 |
| 25 | 3478.6687 | 1 |
| 50 | 2912.3738 | 1 |
| 100 | 1779.784 | 0 |

Remaining blockers:

- Analyst revision and true guidance surprise remain vendor/public-feed gated.
- Macro vintage is partially implemented from existing local rates/liquidity panels, not a full acceptance-grade ALFRED vintage stack.
- This diagnostic replay does not change strategy acceptance.

## No-Background Decision-Maker Report

1. Built the missing interaction layer.
2. It combines price acceptance, sector breadth, macro/liquidity, SEC financing specificity, quality, and expectation proxy.
3. The top3 diagnostic replay improved versus the sleeve baseline while keeping MDD inside target.
4. Top5 was not replayed. It was gated because broad expansion previously caused fragility.
5. This is still diagnostic, not accepted for capital.

## Artifact Manifest

- `task1931_interaction_primitive_schema.csv`
- `task1932_event_window_absorption_panel.csv`
- `task1933_sector_breadth_source_field.csv`
- `task1934_sec_financing_specificity_parser.csv`
- `task1935_l4_interaction_payoff_thesis_cards.csv`
- `task1936_source_independence_contract.csv`
- `task1937_negative_fixture_pack.csv`
- `task1938_interaction_top3_replay_trades.csv/equity/metrics/split_oos/cost_stress`
- `task1939_top5_expansion_gate.csv`
- `task1940_failure_attribution.csv`
- `task1940_acceptance_gate.csv`
- `task1940_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1931_1940_interaction_forecast_layer_validate.py`
- `python scripts/task_registry_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```