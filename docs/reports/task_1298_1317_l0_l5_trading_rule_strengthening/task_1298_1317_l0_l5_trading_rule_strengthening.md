# Task1298-1317 L0-L5 Trading Rule Strengthening

## Decision Summary

- Verdict: `diagnostic_l0_l5_trading_rules_implemented_not_accepted`.
- Best policy: `l0_l5_trader_rulebook_slot5_v1`.
- Best final equity: 2299.3691.
- Best CAGR: 0.175081.
- Best MDD: -0.371127.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: L0-L5 rules now convert source quality into trading judgment, rank routes, and L5 sizing.
- Next action: extend multisource extractors from selected 310 rows to all 3100 candidate rows before true candidate replacement.

## Quant Expert Report

Data source and readiness:

- SEC EDGAR submission and exhibit evidence remains the main company source.
- Federal Register policy evidence and market price/volume acceptance remain attached as shadow source families.
- Analyst PIT source and full exchange-listed PIT universe remain explicit gaps.

Exact join keys:

- `selection_id`
- `trade_spec_id`
- `decision_asof_ts`
- `symbol`

Leakage audit:

- Assignment uses L0 readiness, L1 source-quality states, L2 interpretation states, L3 relation actions, and original candidate rank.
- Assignment does not use future return, PnL, labels, adjusted exit price, or post-entry price path.
- Post-entry prices are used only by the inherited diagnostic replay engine.

Policy metrics:

| Policy | Final | CAGR | MDD | Beats Task1288 Best | Beats QQQ |
| --- | ---: | ---: | ---: | ---: | ---: |
| `l0_l5_conviction_tilt_slot5_v1` | 2251.6289 | 0.170313 | -0.362422 | 1 | 1 |
| `l0_l5_quality_hurdle_slot5_v1` | 2170.3686 | 0.162008 | -0.343478 | 1 | 1 |
| `l0_l5_shadow_slot5_v1` | 2019.1196 | 0.145856 | -0.367558 | 0 | 1 |
| `l0_l5_trader_rulebook_slot5_v1` | 2299.3691 | 0.175081 | -0.371127 | 1 | 1 |

Remaining blockers:

- Full candidate replacement is still blocked because enhanced multisource extractors cover selected slot5 rows, not the full 3100-candidate pool.
- Analyst expectation PIT feed is still absent.
- Dynamic sell/hold rules need post-entry source receipt timestamps.

## No-Background Decision-Maker Report

We strengthened the brain from source evidence to actual trading rules.

The system now says:

1. Strong source + market confirmation means larger or normal size.
2. Weak/incomplete evidence means smaller size or cash.
3. Survival-risk evidence caps size instead of blindly buying.
4. It still cannot choose a better replacement outside the current selected five until every candidate has the same source extraction.

This does not approve the strategy.

## Artifact Manifest

- `task1298_expert_source_context.csv`
- `task1299_l0_l5_strengthening_plan.csv`
- `task1299_l0_l5_layer_rulebook.csv`
- `task1300_l0_coverage_gate.csv`
- `task1301_l1_signal_quality_scores.csv`
- `task1302_l2_trading_judgment_scores.csv`
- `task1303_l3_rule_action_edges.csv`
- `task1304_l4_rank_route_panel.csv`
- `task1305_l5_rule_policy_specs.csv`
- `task1306_replay_trades.csv`
- `task1307_replay_equity.csv`
- `task1308_replay_metrics.csv`
- `task1309_layer_gap_ledger.csv`
- `task1310_acceptance_gate.csv`
- `task1316_expert_audit_findings.csv`
- `task1317_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1298_1317_l0_l5_trading_rule_strengthening_validate.py`
- `python -m unittest tests.test_trader_brain_1298_1317_l0_l5_trading_rule_strengthening`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
