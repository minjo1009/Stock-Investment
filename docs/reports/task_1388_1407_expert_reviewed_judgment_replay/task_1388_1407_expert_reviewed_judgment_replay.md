# Task1388-1407 Expert Reviewed Judgment Replay

## Decision Summary

- Verdict: `expert_reviewed_judgment_replay_diagnostic_not_accepted`.
- Best policy: `expert_payoff_top5_v2`.
- Best final equity: 3353.5648.
- Best CAGR: 0.264229.
- Best MDD: -0.368694.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: expert-reviewed expectation gap, materiality denominator, source independence splitter, market absorption, L3 mechanism v2, L4 payoff rank v2, and L5 dynamic exit v2 were implemented.
- Next action: acquire true PIT analyst/estimate data and verified denominator feeds before treating expectation or materiality as real rather than proxy.

## Quant Expert Report

- Data source and source readiness: Task1318 candidate source evidence, Task1358 L2-L5 core recovery, public SEC/exhibit text, daily OHLCV, and Task1378 expert context packet.
- Exact join keys: `candidate_source_id`, `trade_spec_id`, `decision_asof_ts`.
- Leakage audit: L2-L4 assignment does not use future return, realized PnL, exit price, or post-entry price path. Market absorption rank windows end before decision as-of. Dynamic exits use post-entry receipt logic.
- Split/OOS metrics: train 2021-2023, validation 2024, OOS 2025-2026Q1 are frozen. OOS tuning remains blocked.
- Remaining blockers: true analyst PIT, verified revenue/market-cap/backlog denominators, customer-side confirmation, and policy affected-entity mapping.
- Cost/slippage stress: round-trip cost remains 20.0 bps.

Post-implementation expert audit:

- Trading audit: top10 improved and top5 became the final leader after denominator-gap materiality was corrected, but the system still lacks true PIT expectation data.
- Data audit: all analyst expectation rows remain `analyst_source_gap=1`, all denominator rows remain `denominator_source_gap`, and missing data is not treated as negative evidence.
- Backend audit: dynamic exit v2 expands from 6 to 174 ready exits, but most are price-path risk exits rather than true source-receipt exits. Future work must split `source_receipt_exit` from `price_path_risk_exit`.

Policy metrics:

| Policy | Final | CAGR | MDD | Beats Baseline | Beats QQQ | CAGR 30 | MDD -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `expert_hurdle_top10_v2` | 1461.1046 | 0.076241 | -0.325412 | 1 | 0 | 0 | 0 |
| `expert_payoff_top10_v2` | 2218.2 | 0.166926 | -0.303406 | 1 | 1 | 0 | 0 |
| `expert_payoff_top5_v2` | 3353.5648 | 0.264229 | -0.368694 | 1 | 1 | 0 | 0 |

## No-Background Decision-Maker Report

We replaced weak proxy fields with stricter expert-reviewed sidecar panels.

The replay result is still diagnostic only.

The strategy is not accepted.

## Artifact Manifest

- `task1388_formula_draft.csv`
- `task1389_expert_critique_matrix.csv`
- `task1389_revised_formula_spec.csv`
- `task1390_expectation_gap_panel.csv`
- `task1391_materiality_denominator_panel.csv`
- `task1392_source_independence_splitter.csv`
- `task1393_market_absorption_panel.csv`
- `task1394_l2_enriched_judgment_panel.csv`
- `task1394_l3_mechanism_edges_v2.csv`
- `task1395_l4_payoff_ranker_v2.csv`
- `task1396_l5_policy_specs_v2.csv`
- `task1396_dynamic_exit_receipts_v2.csv`
- `task1397_replay_trades.csv`
- `task1398_replay_equity.csv`
- `task1399_replay_metrics.csv`
- `task1400_replacement_pair_audit.csv`
- `task1401_split_freeze.csv`
- `task1402_validation_invariant_ledger.csv`
- `task1403_overfit_guard_ledger.csv`
- `task1404_acceptance_gate.csv`
- `task1407_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1388_1407_expert_reviewed_judgment_replay_validate.py`
- `python -m unittest tests.test_trader_brain_1388_1407_expert_reviewed_judgment_replay`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
