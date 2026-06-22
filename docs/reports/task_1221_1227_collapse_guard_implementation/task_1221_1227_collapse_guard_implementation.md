# Task1221-1227 Collapse Guard Implementation

## Decision Summary

- Verdict: `collapse_guard_controlled_replay_executed_not_accepted`.
- Policy variant: `collapse_guard_slot5_v1`.
- Final equity: 1814.769.
- CAGR: 0.122408.
- MDD: -0.345109.
- Base slot5 final equity: 1970.36.
- Beats base slot5: 0.
- QQQ final equity: 1847.0265.
- Beats QQQ: 0.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This task implements the Task1211-1220 collapse guard as a diagnostic controlled comparison.

Implemented controls:

- Public-filer proxy listing and identity adapter.
- Distress panel using only decision-time price path, volatility, liquidity, and SEC event density fields.
- Product classifier that allows leverage but routes complex products to smaller and shorter handling.
- L3 relation edges that pass, condition, weaken, or route candidates.
- L4 collapse-aware candidate card fields.
- L5 risk-bucket sizing, drawdown exits, product-sleeve shortened holding, and reentry cooling.

Limitations:

- Raw text extraction for going concern and dilution is not yet implemented.
- True exchange historical PIT listing remains incomplete.
- This is diagnostic evidence only and cannot accept the strategy.

## No-Background Decision-Maker Report

We tested whether a collapse guard can reduce near-zero tail risk without banning leverage.

The result is diagnostic only.

## Artifact Manifest

- `task1221_listing_corporate_action_adapter.csv`
- `task1222_distress_evidence_panel.csv`
- `task1223_product_structure_classifier.csv`
- `task1224_l3_collapse_relation_edges.csv`
- `task1225_l4_collapse_candidate_cards.csv`
- `task1226_l5_collapse_guard_trade_specs.csv`
- `task1227_collapse_guard_replay_trades.csv`
- `task1227_collapse_guard_replay_equity.csv`
- `task1227_collapse_guard_metrics.csv`
- `task1227_collapse_guard_acceptance_gate.csv`
- `task1227_collapse_guard_closeout.csv/json`
- `artifact_manifest.csv`

Validation commands:

- `python scripts/trader_brain_1221_1227_collapse_guard_implementation_validate.py`
- `python -m unittest tests.test_trader_brain_1221_1227_collapse_guard_implementation`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
