# Task1618-1647 Expectation-Payoff-Re-risk Bridge

## Decision Summary

- Verdict: `expectation_payoff_rerisk_bridge_implemented_not_accepted`.
- Best policy: `rerisk_none_top3_v1`.
- Best final equity: 2729.4893.
- Best CAGR: 0.214781.
- Best MDD: -0.333316.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Main replay metrics:

| Policy | Final | CAGR | MDD | Rerisk Trades | Rerisk PnL | QQQ Beat | MDD Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `rerisk_confirmed_top3_v1` | 2631.1929 | 0.206178 | -0.333316 | 3 | -27.6548 | 1 | 0 |
| `rerisk_confirmed_top5_v1` | 2089.687 | 0.153509 | -0.27778 | 3 | -12.255 | 1 | 1 |
| `rerisk_none_top3_v1` | 2729.4893 | 0.214781 | -0.333316 | 0 | 0.0 | 1 | 0 |
| `rerisk_none_top5_v1` | 2135.6857 | 0.158386 | -0.27778 | 0 | 0.0 | 1 | 1 |
| `rerisk_partial_top3_v1` | 2709.1817 | 0.213024 | -0.333316 | 5 | 6.4497 | 1 | 0 |
| `rerisk_partial_top5_v1` | 2126.1415 | 0.157381 | -0.27778 | 5 | 4.2487 | 1 | 1 |

Split/OOS diagnostics:

| Policy | Window | Final | Return | MDD |
| --- | --- | ---: | ---: | ---: |
| `rerisk_confirmed_top3_v1` | IS_2021_2023 | 1721.6514 | 0.721651 | -0.333316 |
| `rerisk_confirmed_top3_v1` | OOS_2024_2026Q1 | 1528.296 | 0.528296 | -0.205951 |
| `rerisk_confirmed_top5_v1` | IS_2021_2023 | 1425.7146 | 0.425715 | -0.27778 |
| `rerisk_confirmed_top5_v1` | OOS_2024_2026Q1 | 1465.7119 | 0.465712 | -0.126769 |
| `rerisk_none_top3_v1` | IS_2021_2023 | 1712.8012 | 0.712801 | -0.333316 |
| `rerisk_none_top3_v1` | OOS_2024_2026Q1 | 1593.5821 | 0.593582 | -0.157862 |
| `rerisk_none_top5_v1` | IS_2021_2023 | 1421.3467 | 0.421347 | -0.27778 |
| `rerisk_none_top5_v1` | OOS_2024_2026Q1 | 1502.5792 | 0.502579 | -0.096106 |
| `rerisk_partial_top3_v1` | IS_2021_2023 | 1728.6473 | 0.728647 | -0.333316 |
| `rerisk_partial_top3_v1` | OOS_2024_2026Q1 | 1567.2264 | 0.567226 | -0.181906 |
| `rerisk_partial_top5_v1` | IS_2021_2023 | 1429.2846 | 0.429285 | -0.27778 |
| `rerisk_partial_top5_v1` | OOS_2024_2026Q1 | 1487.5563 | 0.487556 | -0.111437 |

Cost stress metrics:

| Policy | Cost bps | Final | CAGR | MDD | QQQ Beat |
| --- | ---: | ---: | ---: | ---: | ---: |
| `rerisk_confirmed_top3_v1` | 50.0 | 2323.419 | 0.177452 | -0.345255 | 1 |
| `rerisk_confirmed_top5_v1` | 50.0 | 1900.4924 | 0.132491 | -0.286961 | 1 |
| `rerisk_none_top3_v1` | 50.0 | 2416.7824 | 0.186475 | -0.345255 | 1 |
| `rerisk_none_top5_v1` | 50.0 | 1945.3327 | 0.13762 | -0.286961 | 1 |
| `rerisk_partial_top3_v1` | 50.0 | 2393.7866 | 0.184279 | -0.345255 | 1 |
| `rerisk_partial_top5_v1` | 50.0 | 1934.2828 | 0.136365 | -0.286961 | 1 |
| `rerisk_confirmed_top3_v1` | 100.0 | 1887.143 | 0.130946 | -0.364748 | 1 |
| `rerisk_confirmed_top5_v1` | 100.0 | 1621.8069 | 0.098224 | -0.302051 | 0 |
| `rerisk_none_top3_v1` | 100.0 | 1971.9716 | 0.140622 | -0.364748 | 1 |
| `rerisk_none_top5_v1` | 100.0 | 1664.3809 | 0.103752 | -0.302051 | 0 |
| `rerisk_partial_top3_v1` | 100.0 | 1946.3581 | 0.137737 | -0.364748 | 1 |
| `rerisk_partial_top5_v1` | 100.0 | 1651.5565 | 0.102099 | -0.302051 | 0 |

## No-Background Decision-Maker Report

1. The planned bridge was implemented as code, panels, replay, and audit artifacts.
2. True PIT analyst surprise remains unavailable, so expectation logic is proxy-labeled.
3. Re-risk requires source/payoff/alpha eligibility plus runtime post-reduce absorption recovery.
4. Re-risk events fired, but staged re-risk did not beat the no-rerisk diagnostic baseline.
5. This is a trading-judgment diagnosis, not strategy acceptance.

## Failure / Blocker Summary

- `rerisk_block_reason`: source=0;damage=0;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=3.5 count=24 pnl=
- `rerisk_block_reason`: source=0;damage=0;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=15.0 count=22 pnl=
- `rerisk_block_reason`: source=0;damage=0;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=1.5 count=16 pnl=
- `rerisk_block_reason`: source=0;damage=0;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=14.0 count=15 pnl=
- `rerisk_block_reason`: source=1;damage=0;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=1.5 count=13 pnl=
- `rerisk_block_reason`: source=0;damage=0;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=13.0 count=12 pnl=
- `rerisk_block_reason`: source=1;damage=1;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=15.0 count=12 pnl=
- `rerisk_block_reason`: source=0;damage=0;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=12.5 count=11 pnl=
- `rerisk_block_reason`: source=0;damage=0;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=3.0 count=11 pnl=
- `rerisk_block_reason`: source=0;damage=0;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=2.0 count=11 pnl=
- `rerisk_block_reason`: source=1;damage=1;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=14.0 count=9 pnl=
- `rerisk_block_reason`: source=1;damage=1;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=1.5 count=9 pnl=
- `rerisk_block_reason`: source=0;damage=0;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=-0.5 count=9 pnl=
- `rerisk_block_reason`: source=1;damage=0;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=3.5 count=8 pnl=
- `rerisk_block_reason`: source=1;damage=1;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=12.5 count=7 pnl=
- `rerisk_block_reason`: source=1;damage=1;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=3.5 count=6 pnl=
- `rerisk_block_reason`: source=1;damage=0;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=3.0 count=6 pnl=
- `rerisk_block_reason`: source=0;damage=0;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=4.0 count=5 pnl=
- `rerisk_block_reason`: source=0;damage=0;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=0.0 count=5 pnl=
- `rerisk_block_reason`: source=1;damage=1;pre_absorb=0;runtime_absorb=required;payoff=1;alpha=10.5 count=4 pnl=

## Artifact Manifest

- `task1618_expert_implementation_review.csv`
- `task1619_data_availability_contract.csv`
- `task1620_tradable_surprise_panel.csv`
- `task1621_payoff_window_panel.csv`
- `task1622_absorption_quality_panel.csv`
- `task1623_l3_payoff_mechanism_edges.csv`
- `task1624_l4_payoff_thesis_cards.csv`
- `task1625_l5_rerisk_state_panel.csv`
- `task1626_negative_fixtures.csv`
- `task1627_preregistered_policy_specs.csv`
- `task1628_rerisk_replay_trades.csv/equity/events`
- `task1629_rerisk_replay_metrics.csv`
- `task1630_split_oos_metrics.csv`
- `task1632_cost_stress_metrics.csv`
- `task1633_failure_attribution.csv`
- `task1646_acceptance_gate.csv`
- `task1647_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1618_1647_expectation_payoff_rerisk_bridge_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```