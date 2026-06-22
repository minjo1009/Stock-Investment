# Task2251-2280 Plus8000 Full Source Acquisition

## Decision Summary

- Verdict: `plus8000_full_source_acquisition_completed_with_provider_blocks`.
- Candidate rows: 3100.
- API call rows: 2420.
- Usable call rows: 753.
- Blocked or retry rows: 1667.
- Normalized source rows: 4588915.
- Feature rows: 3100.
- Non-gap feature rows: 2983.
- Financial rows after SEC fallback: 2827.
- Replay allowed: `0`.

## Quant Expert Report

The task attempts full source acquisition for the +8000 data standard across the 3,100-candidate pool. FMP financial endpoints are still attempted, but SEC companyfacts is used as an official fallback for financial statement fields when FMP is blocked.

Coverage:

- `alpha_vantage` / `earnings_history` / `entitlement_blocked`: 270.
- `finnhub` / `stock_filings` / `usable`: 235.
- `finnhub` / `stock_recommendation` / `usable`: 235.
- `fmp` / `balance_sheet` / `entitlement_blocked`: 50.
- `fmp` / `balance_sheet` / `quota_or_rate_blocked`: 230.
- `fmp` / `cash_flow` / `entitlement_blocked`: 50.
- `fmp` / `cash_flow` / `quota_or_rate_blocked`: 230.
- `fmp` / `earnings` / `entitlement_blocked`: 50.
- `fmp` / `earnings` / `quota_or_rate_blocked`: 230.
- `fmp` / `grades_historical` / `entitlement_blocked`: 46.
- `fmp` / `grades_historical` / `quota_or_rate_blocked`: 231.
- `fmp` / `grades_historical` / `usable`: 3.
- `fmp` / `income_statement` / `entitlement_blocked`: 50.
- `fmp` / `income_statement` / `http_error`: 1.
- `fmp` / `income_statement` / `quota_or_rate_blocked`: 229.
- `sec` / `companyfacts` / `usable`: 280.
- `combined` / `nonzero_filing_total` / `feature_coverage`: 1329.
- `combined` / `nonzero_earnings_surprise` / `feature_coverage`: 154.
- `combined` / `nonzero_financials` / `feature_coverage`: 2827.
- `combined` / `nonzero_rating_score` / `feature_coverage`: 214.
- `combined` / `api_proxy_not_source_gap` / `feature_coverage`: 2983.

Retry or blocked queue:

- `alpha_vantage` / `earnings_history` / `entitlement_blocked`: 270.
- `fmp` / `balance_sheet` / `entitlement_blocked`: 50.
- `fmp` / `balance_sheet` / `quota_or_rate_blocked`: 230.
- `fmp` / `cash_flow` / `entitlement_blocked`: 50.
- `fmp` / `cash_flow` / `quota_or_rate_blocked`: 230.
- `fmp` / `earnings` / `entitlement_blocked`: 50.
- `fmp` / `earnings` / `quota_or_rate_blocked`: 230.
- `fmp` / `grades_historical` / `entitlement_blocked`: 46.
- `fmp` / `grades_historical` / `quota_or_rate_blocked`: 231.
- `fmp` / `income_statement` / `entitlement_blocked`: 50.
- `fmp` / `income_statement` / `http_error`: 1.
- `fmp` / `income_statement` / `quota_or_rate_blocked`: 229.

## No-Background Decision-Maker Report

Conclusion first: the acquisition pass actually downloads/reuses raw sources and computes a full 3,100-row feature panel. Replay remains blocked until the new parity audit is rerun and explicitly authorized.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2251_2280_plus8000_full_source_acquisition/`.
- Raw sources: `data/raw/task_2251_2280_plus8000_full_source_acquisition/`.
- Validator: `python scripts/trader_brain_2251_2280_plus8000_full_source_acquisition_validate.py`.

Sources consulted for endpoint fallback: FMP official developer docs for stable and legacy endpoint families; SEC companyfacts official endpoint is used as a free official fallback for financial statements.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
