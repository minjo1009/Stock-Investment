# Task1408-1427 Ruler Acquisition Replay

## Decision Summary

- Verdict: `ruler_acquisition_replay_diagnostic_not_accepted`.
- Best policy: `ruler_top3_v1`.
- Best final equity: 3715.5432.
- Best CAGR: 0.289589.
- Best MDD: -0.326342.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: scale, expectation, absorption, and exit rulers were split into explicit panels; SEC companyfacts denominators were used only when filed by the decision date; source-receipt exits and price-path exits were separated.
- Next action: broaden verified denominator coverage, acquire true PIT analyst estimates, and attach non-SEC historical source receipts.

## Quant Expert Report

- Data source and source readiness: Task1201 candidates/trade specs, Task1318 full candidate SEC/exhibit sources, Task1388 enriched judgment panels, SEC companyfacts raw files, and daily OHLCV.
- Exact join keys: `candidate_source_id`, `trade_spec_id`, `decision_asof_ts`.
- Leakage audit: denominator facts require filed date at or before decision. L2-L4 assignment does not use future PnL, exit price, or post-entry price path. Price-path exits are labeled as L5 diagnostic execution logic, not L2-L4 assignment evidence.
- Expert audit result: GPT/subagent roles are review-only; source-of-truth remains local artifacts and source timestamps.
- Cost/slippage stress: round-trip cost remains 20.0 bps.

Policy metrics:

| Policy | Final | CAGR | MDD | Trades | Source Exit | Price Exit | Beats Baseline | Beats QQQ | CAGR 30 | MDD -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `ruler_top10_v1` | 1341.1749 | 0.058528 | -0.327347 | 620 | 166 | 26 | 1 | 0 | 0 | 0 |
| `ruler_top3_v1` | 3715.5432 | 0.289589 | -0.326342 | 186 | 50 | 5 | 1 | 1 | 0 | 0 |
| `ruler_top5_v1` | 2419.2781 | 0.186712 | -0.302634 | 310 | 91 | 11 | 1 | 1 | 0 | 0 |

## No-Background Decision-Maker Report

눈금자는 일부 확보됐다.

하지만 아직 완성은 아니다.

좋은 점수의 근거가 더 구체화됐고, 매도 사유도 source exit과 price exit으로 갈라졌다.

그래도 전략은 아직 승인되지 않았다.

## Artifact Manifest

- `task1408_ruler_expert_review_packet.csv`
- `task1409_scale_ruler_schema.csv`
- `task1410_companyfacts_denominator_panel.csv`
- `task1411_market_cap_proxy_panel.csv`
- `task1412_event_value_panel.csv`
- `task1413_materiality_ruler_panel.csv`
- `task1414_expectation_ruler_schema.csv`
- `task1415_public_guidance_revision_panel.csv`
- `task1416_analyst_pit_audit.csv`
- `task1417_expectation_ruler_panel.csv`
- `task1418_market_absorption_enhanced_panel.csv`
- `task1419_absorption_ruler_panel.csv`
- `task1420_exit_ruler_schema.csv`
- `task1421_source_receipt_exit_panel.csv`
- `task1422_price_path_risk_exit_panel.csv`
- `task1423_hold_extend_receipt_panel.csv`
- `task1424_integrated_ruler_panel.csv`
- `task1425_payoff_ranker_v3.csv`
- `task1426_policy_specs.csv`
- `task1426_replay_trades.csv`
- `task1426_replay_equity.csv`
- `task1426_replay_metrics.csv`
- `task1427_expert_post_audit.csv`
- `task1427_acceptance_gate.csv`
- `task1427_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1408_1427_ruler_acquisition_replay_validate.py`
- `python -m unittest tests.test_trader_brain_1408_1427_ruler_acquisition_replay`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
