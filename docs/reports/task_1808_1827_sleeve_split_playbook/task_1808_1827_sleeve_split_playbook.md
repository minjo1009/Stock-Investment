# Task1808-1827 Sleeve Split Playbook

## Decision Summary

- Verdict: `sleeve_split_playbook_implemented_diagnostic_only`.
- Best policy: `sleeve_split_top3_v1`.
- Best final equity: 3944.5457.
- Best CAGR: 0.304621.
- Best MDD: -0.24476.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Data source and exact join keys:

- Source panel: `task1790_winner_defense_panel.csv`, joined by `target_policy_variant_id`, `trade_spec_id`, and `decision_asof_ts`.
- Source trades: `task1792_winner_defense_replay_trades.csv`, joined by `policy_variant_id` and `trade_spec_id`.
- Market regime: prior QQQ prices only, using rows on or before `decision_asof_ts`.

Leakage audit:

- Assignment uses pre-entry features, sleeve taxonomy, prior QQQ regime, and frozen playbook rules only.
- PnL, period PnL share, and drawdown contribution are audit-only fields.

| Policy | Final | CAGR | MDD | Base Final | Base MDD | Delta Final | Delta MDD | Trades | Joint Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `sleeve_split_top3_v1` | 3944.5457 | 0.304621 | -0.24476 | 3920.9554 | -0.314619 | 23.5903 | 0.069859 | 160 | 1 |
| `sleeve_split_top5_v1` | 2822.4123 | 0.222687 | -0.18777 | 2960.4142 | -0.247497 | -138.0019 | 0.059727 | 213 | 0 |

Split/OOS metrics:

| Policy | Window | Final | Return | MDD |
| --- | --- | ---: | ---: | ---: |
| `sleeve_split_top3_v1` | IS_2021_2023 | 1989.084 | 0.989084 | -0.24476 |
| `sleeve_split_top3_v1` | OOS_2024_2026Q1 | 3944.5457 | 2.944546 | -0.166941 |
| `sleeve_split_top5_v1` | IS_2021_2023 | 1645.3136 | 0.645314 | -0.18777 |
| `sleeve_split_top5_v1` | OOS_2024_2026Q1 | 2822.4123 | 1.822412 | -0.114375 |

Cost/slippage stress:

| Policy | Cost bps | Stressed Final | Beats QQQ |
| --- | ---: | ---: | ---: |
| `sleeve_split_top3_v1` | 0 | 3944.5457 | 1 |
| `sleeve_split_top3_v1` | 25 | 3392.3093 | 1 |
| `sleeve_split_top3_v1` | 50 | 2840.0729 | 1 |
| `sleeve_split_top3_v1` | 100 | 1735.6001 | 0 |
| `sleeve_split_top5_v1` | 0 | 2822.4123 | 1 |
| `sleeve_split_top5_v1` | 25 | 2296.3852 | 1 |
| `sleeve_split_top5_v1` | 50 | 1770.3581 | 0 |
| `sleeve_split_top5_v1` | 100 | 718.3039 | 0 |

Failure decomposition:

- `strategy_sleeve`: winner_compounder count=194 pnl= cagr= mdd=
- `strategy_sleeve`: cyclical_beta count=104 pnl= cagr= mdd=
- `strategy_sleeve`: speculative_event count=45 pnl= cagr= mdd=
- `strategy_sleeve`: defensive_quality count=34 pnl= cagr= mdd=
- `regime_state`: risk_on count=107 pnl= cagr= mdd=
- `regime_state`: neutral_to_positive count=99 pnl= cagr= mdd=
- `regime_state`: valuation_compression count=65 pnl= cagr= mdd=
- `regime_state`: broad_selloff count=55 pnl= cagr= mdd=
- `regime_state`: neutral_chop count=51 pnl= cagr= mdd=
- `sleeve_action`: hold count=143 pnl= cagr= mdd=
- `sleeve_action`: reduce count=60 pnl= cagr= mdd=
- `sleeve_action`: hold_or_trim count=54 pnl= cagr= mdd=
- `sleeve_action`: trim count=53 pnl= cagr= mdd=
- `sleeve_action`: add_or_hold count=50 pnl= cagr= mdd=
- `sleeve_action`: cap count=13 pnl= cagr= mdd=
- `sleeve_action`: no_entry count=4 pnl= cagr= mdd=
- `sleeve_action_reason`: base_winner_defense count=90 pnl= cagr= mdd=
- `sleeve_action_reason`: winner_macro_pressure count=54 pnl= cagr= mdd=
- `sleeve_action_reason`: cyclical_neutral_chop count=53 pnl= cagr= mdd=
- `sleeve_action_reason`: winner_regime_supported count=50 pnl= cagr= mdd=
- `sleeve_action_reason`: defensive_buffer_optional count=29 pnl= cagr= mdd=
- `sleeve_action_reason`: cyclical_regime_off count=29 pnl= cagr= mdd=
- `sleeve_action_reason`: speculative_risk_off_cap count=26 pnl= cagr= mdd=
- `sleeve_action_reason`: cyclical_regime_on count=19 pnl= cagr= mdd=
- `sleeve_action_reason`: speculative_event_cap count=13 pnl= cagr= mdd=
- `sleeve_action_reason`: issuer_specific_damage_cap count=5 pnl= cagr= mdd=
- `sleeve_action_reason`: defensive_buffer_on count=5 pnl= cagr= mdd=
- `sleeve_action_reason`: speculative_terminal_block count=4 pnl= cagr= mdd=
- `strategy_sleeve_pnl`: cyclical_beta count=104 pnl=358.3294 cagr= mdd=
- `strategy_sleeve_pnl`: defensive_quality count=34 pnl=253.955 cagr= mdd=
- `strategy_sleeve_pnl`: speculative_event count=41 pnl=140.2183 cagr= mdd=
- `strategy_sleeve_pnl`: winner_compounder count=194 pnl=4014.4552 cagr= mdd=
- `regime_state_pnl`: broad_selloff count=53 pnl=109.8285 cagr= mdd=
- `regime_state_pnl`: neutral_chop count=51 pnl=1082.0695 cagr= mdd=

## No-Background Decision-Maker Report

1. This task stops treating all candidates as one game.
2. It splits trades into winner, cyclical, speculative, and defensive sleeves.
3. Each sleeve receives a different playbook and risk budget.
4. The replay is still diagnostic and does not approve strategy.

## Artifact Manifest

- `task1808_trade_drawdown_attribution_ledger.csv`
- `task1809_sleeve_taxonomy_contract.csv`
- `task1810_regime_classifier_panel.csv`
- `task1811_l1_source_routing_contract.csv`
- `task1812_l2_sleeve_meaning_panel.csv`
- `task1813_l3_sleeve_relation_edges.csv`
- `task1814_l4_sleeve_thesis_cards.csv`
- `task1815_sleeve_risk_budget.csv`
- `task1816_l5_sleeve_action_rules.csv`
- `task1817_1820_sleeve_playbooks.csv`
- `task1821_frozen_policy_config.csv`
- `task1822_controlled_sleeve_replay_trades.csv/equity`
- `task1823_sleeve_replay_metrics.csv/split_oos/cost_stress`
- `task1824_failure_attribution.csv`
- `task1825_expert_audit.csv`
- `task1826_acceptance_gate.csv`
- `task1827_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1808_1827_sleeve_split_playbook_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```