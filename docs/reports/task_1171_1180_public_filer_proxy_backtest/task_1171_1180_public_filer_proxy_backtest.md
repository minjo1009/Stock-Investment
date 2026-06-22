# Task1171-1180 Public-Filer Proxy Backtest

## Decision Summary

- Verdict: `diagnostic_public_filer_proxy_backtest_executed_not_accepted`.
- Price pool symbols: 1501.
- Price downloaded symbols: 1501.
- Feature rows: 29397.
- Best variant: `public_filer_proxy_slot10_v1`.
- Best final equity: 355.6784.
- Best CAGR: -0.181516.
- Best MDD: -0.834243.
- QQQ final equity: 1847.0265.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

This is the first broad public-filer proxy replay after removing the custom 10x7 winner basket as the selection universe.

The replay uses:

- SEC public-filer as-of proxy membership.
- yfinance daily adjusted prices for a bounded 1,500-symbol download pool plus QQQ.
- Monthly decisions from 2021-01-31 through 2026-03-31.
- Trailing price momentum, trailing volatility, dollar-volume, and SEC filing-activity features.
- Slot caps 3, 5, and 10.

Limitations:

- This is not true exchange-listed PIT.
- The price universe is a bounded download pool, not all 8,129 public filers.
- Current ticker metadata remains a proxy limitation.
- No acceptance or deployment status changes.

## No-Background Decision-Maker Report

We finally moved away from the 70-name handpicked basket.

The model now chooses from a broad SEC public-filer universe proxy.

This is a real diagnostic backtest, but still not a final institution-grade acceptance test.

## Artifact Manifest

- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1171_price_download_pool.csv`
- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1172_yfinance_price_download_ledger.csv`
- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1173_price_coverage_gate.csv`
- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1174_public_filer_proxy_feature_panel.csv`
- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1175_policy_selections.csv`
- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1176_proxy_backtest_trades.csv`
- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1176_proxy_backtest_equity.csv`
- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1177_proxy_backtest_metrics.csv`
- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1180_public_filer_proxy_backtest_closeout.csv`
- `data/artifacts/task_1171_1180_public_filer_proxy_backtest/task1180_public_filer_proxy_backtest_closeout.json`
