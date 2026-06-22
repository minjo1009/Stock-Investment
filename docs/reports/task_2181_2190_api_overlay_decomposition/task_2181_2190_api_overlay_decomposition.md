# Task2181-2190 API Overlay Decomposition

## Decision Summary

- Verdict: `api_overlay_decomposition_complete_diagnostic_only`.
- New policy: `api_loop3_guarded_risk_cap_top2_v1`.
- Previous policy: `free_api_proxy_top5_to_top2_convex_v1`.
- Final equity delta: 649.2609.
- Same trades: 116.
- Added trades: 0.
- Dropped trades: 0.
- New MDD: -0.339808.
- Previous MDD: -0.334944.
- MDD delta: -0.004864.
- New MDD window: 2022-01-31T21:00:00+00:00 to 2022-08-31T21:00:00+00:00.

## Quant Expert Report

API overlay improved final equity by changing both selection and sizing. The key audit result is not just that return improved, but that MDD worsened slightly. Therefore the next rule should not add more generic boost. It should protect the MDD window without deleting the positive overlay months.

PnL delta by API state:

- api_event_context_supportive: 484.1242
- api_financing_or_dilution_risk: 151.8735
- api_no_asof_packet_neutral: 25.3459
- api_context_light: -12.0829

PnL delta by symbol:

- CIEN: 239.4308
- AVGO: 135.3615
- AEIS: 119.5692
- ALNY: 32.0938
- CEG: 26.3694
- ADPT: 25.1319
- CDNA: 19.4482
- AZO: 16.2796
- C: 15.709
- AA: 15.5964

Worst incremental delta months:

- 2026-02-28T21:00:00+00:00: incremental delta -52.0945, period pnl delta -52.0944
- 2025-06-30T21:00:00+00:00: incremental delta -26.5073, period pnl delta -26.5073
- 2025-01-31T21:00:00+00:00: incremental delta -21.7876, period pnl delta -21.7876
- 2022-03-31T21:00:00+00:00: incremental delta -16.4816, period pnl delta -16.4816
- 2025-07-31T21:00:00+00:00: incremental delta -15.887, period pnl delta -15.887

## No-Background Decision-Maker Report

Conclusion first: API overlay made money, but it also made the worst drawdown a little worse. The next fix should target the drawdown-window trades, not the whole strategy.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2181_2190_api_overlay_decomposition/`.
- Validator: `python scripts/trader_brain_2181_2190_api_overlay_decomposition_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
