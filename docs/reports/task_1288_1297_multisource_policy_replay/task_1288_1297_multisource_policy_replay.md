# Task1288-1297 Multi-Source Policy Replay

## Decision Summary

- Verdict: `multisource_policy_replay_executed_not_accepted`.
- Best policy: `multisource_source_complete_slot5_v1`.
- Best final equity: 2063.4905.
- Best CAGR: 0.150693.
- Best MDD: -0.322357.
- Strategy acceptance status: `NOT_ACCEPTED`.

## Quant Expert Report

Four diagnostic policies were replayed after attaching SEC exhibit-derived IR/CEO and contract/order extractors.

| Policy | Final | CAGR | MDD | Beats Task1228 | Beats QQQ |
| --- | ---: | ---: | ---: | ---: | ---: |
| `multisource_hard_event_only_slot5_v1` | 2049.8827 | 0.149219 | -0.353479 | 1 | 1 |
| `multisource_quality_haircut_slot5_v1` | 2060.7947 | 0.150401 | -0.341448 | 1 | 1 |
| `multisource_shadow_only_slot5_v1` | 2019.1196 | 0.145856 | -0.367558 | 0 | 1 |
| `multisource_source_complete_slot5_v1` | 2063.4905 | 0.150693 | -0.322357 | 1 | 1 |

Leakage audit:

- Source features come from prior-known SEC accession evidence and Task1228 decision-time features.
- Assignment does not use future return, PnL, or outcome labels.
- Post-entry prices are used only by the inherited L5 exit simulation.

Remaining blockers:

- Analyst expectation PIT source remains absent.
- Full earnings-call transcript Q&A remains absent.
- Contract/customer-side confirmation remains absent.

## No-Background Decision-Maker Report

We tested whether the newly attached multi-source evidence improves the replay.

This is still diagnostic and does not approve the strategy.

## Artifact Manifest

- `task1288_policy_catalog.csv`
- `task1289_policy_specs.csv`
- `task1290_replay_trades.csv`
- `task1291_replay_equity.csv`
- `task1292_replay_metrics.csv`
- `task1293_multisource_attribution.csv`
- `task1294_acceptance_gate.csv`
- `task1297_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1288_1297_multisource_policy_replay_validate.py`
- `python -m unittest tests.test_trader_brain_1288_1297_multisource_policy_replay`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
