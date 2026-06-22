# Task1848-1867 Source-Attached Policy Replay

## Decision Summary

- Verdict: `source_attached_policy_replay_complete_diagnostic_only`.
- Best policy: `source_attached_top3_v1`.
- Best final equity: 3097.4162.
- Best CAGR: 0.244914.
- Best MDD: -0.214878.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Data source and exact join keys:

- Base sleeve budget: `task1815_sleeve_risk_budget.csv`, joined by `trade_spec_id` and `decision_asof_ts`.
- Rates/liquidity: `task1835_rates_liquidity_decision_asof_panel.csv`, joined by exact `decision_asof_ts` with source time <= decision time.
- SEC financing/dilution: `task1842_sec_dilution_decision_asof_links.csv` and `task1837_financing_dilution_extractor_contract.csv`, joined by exact `trade_spec_id` and source packet id.
- Earnings revision: blocked by `task1838_earnings_revision_vendor_gate.csv`; no assignment effect.
- Replay return source: prior controlled winner-defense replay trades; no new price matching.

Leakage audit:

- Assignment uses only source states known as-of.
- PnL, drawdown, and future returns remain audit-only.
- Missing SEC or earnings source is source gap, not bearish evidence.

| Policy | Final | CAGR | MDD | Base Final | Base MDD | Delta Final | Delta MDD | Trades | Joint Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `source_attached_top3_v1` | 3097.4162 | 0.244914 | -0.214878 | 3944.5457 | -0.24476 | -847.1295 | 0.029882 | 144 | 0 |
| `source_attached_top5_v1` | 2286.7813 | 0.173831 | -0.161596 | 2822.4123 | -0.18777 | -535.631 | 0.026174 | 188 | 0 |

Split/OOS metrics:

| Policy | Window | Final | Return | MDD |
| --- | --- | ---: | ---: | ---: |
| `source_attached_top3_v1` | IS_2021_2023 | 1717.9844 | 0.717984 | -0.214878 |
| `source_attached_top3_v1` | OOS_2024_2026Q1 | 3097.4162 | 2.097416 | -0.130704 |
| `source_attached_top5_v1` | IS_2021_2023 | 1478.5297 | 0.47853 | -0.161596 |
| `source_attached_top5_v1` | OOS_2024_2026Q1 | 2286.7813 | 1.286781 | -0.089995 |

Cost/slippage stress:

| Policy | Cost bps | Stressed Final | Beats QQQ |
| --- | ---: | ---: | ---: |
| `source_attached_top3_v1` | 0 | 3097.4162 | 1 |
| `source_attached_top3_v1` | 25 | 2707.1418 | 1 |
| `source_attached_top3_v1` | 50 | 2316.8673 | 1 |
| `source_attached_top3_v1` | 100 | 1536.3184 | 0 |
| `source_attached_top5_v1` | 0 | 2286.7813 | 1 |
| `source_attached_top5_v1` | 25 | 1910.6058 | 1 |
| `source_attached_top5_v1` | 50 | 1534.4303 | 0 |
| `source_attached_top5_v1` | 100 | 782.0792 | 0 |

## No-Background Decision-Maker Report

1. Rates/liquidity와 SEC dilution source를 실제 판단에 붙였습니다.
2. Earnings revision은 vendor data가 없어서 판단에 안 넣었습니다.
3. 새 매칭이나 micro sizing은 만들지 않았습니다.
4. 결과가 좋아도 아직 승인 상태는 아닙니다.

## Artifact Manifest

- `task1848_expert_review.csv`
- `task1849_source_attach_input_manifest.csv`
- `task1850_rates_l2_meaning_panel.csv`
- `task1851_sec_financing_l2_meaning_panel.csv`
- `task1852_earnings_vendor_block_panel.csv`
- `task1853_l3_targeted_source_edges.csv`
- `task1854_l4_source_attached_thesis_cards.csv`
- `task1855_l5_source_attached_budget.csv`
- `task1856_frozen_policy_config.csv`
- `task1857_controlled_source_attached_replay_trades.csv/equity`
- `task1858_source_attached_replay_metrics.csv/split_oos/cost_stress`
- `task1859_failure_attribution.csv`
- `task1860_acceptance_gate.csv`
- `task1867_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1848_1867_source_attached_policy_replay_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```