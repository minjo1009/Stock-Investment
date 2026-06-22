# Task2281-2290 Post-Acquisition Parity

## Decision Summary

- Verdict: `post_acquisition_parity_insufficient_replay_blocked`.
- Replay gate rows: 63/3100.
- Replay allowed: `0`.
- User confirmation required: `1`.

## Quant Expert Report

- `symbol_endpoint_stock_filings`: 3038/3100 (0.98), pass 1.
- `symbol_endpoint_stock_recommendation`: 3084/3100 (0.994839), pass 1.
- `symbol_endpoint_earnings_history`: 230/3100 (0.074194), pass 0.
- `symbol_endpoint_financial_statement`: 2915/3100 (0.940323), pass 0.
- `asof_endpoint_stock_filings`: 1329/3100 (0.42871), pass 0.
- `asof_endpoint_stock_recommendation`: 214/3100 (0.069032), pass 0.
- `asof_endpoint_earnings_history`: 230/3100 (0.074194), pass 0.
- `asof_endpoint_financial_statement`: 2856/3100 (0.92129), pass 0.
- `source_family_parity_pass`: 230/3100 (0.074194), pass 0.
- `asof_source_family_parity_pass`: 9/3100 (0.002903), pass 0.
- `feature_schema_parity_pass`: 3100/3100 (1.0), pass 1.
- `replay_gate_candidate_pass`: 63/3100 (0.020323), pass 0.

## No-Background Decision-Maker Report

Conclusion first: this is still a parity gate, not a backtest. It tells whether the new acquisition is enough to ask for replay authorization.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2281_2290_post_acquisition_parity/`.
- Validator: `python scripts/trader_brain_2281_2290_post_acquisition_parity_validate.py`.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
