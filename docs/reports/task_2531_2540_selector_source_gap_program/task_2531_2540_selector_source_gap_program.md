# Task2531-2540 Selector Source Gap Program

## Decision Summary

- Verdict: `selector_source_gap_program_built_no_replay_no_download`.
- Full universe rows: 3100.
- Selected KIS trade rows: 124.
- MDD-window trade rows: 14.
- Strict raw/as-of complete rows: 0.
- P0 source family count: 2.
- Download/API calls run: `0`.
- Backtest run: `0`.
- Selector changed: `0`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

The Task2521 guard test showed that portfolio-level de-risking can reduce MDD but tends to reduce return. The next bottleneck is selector source quality, not another sizing overlay.

Source family plan:

- `strict_raw_asof_certification` (P0): required before paper/live; cannot score if only proxy / current `blocked`.
- `financing_dilution_sec_events` (P0): dilution/survival/financing split and bad-trade exclusion / current `partly_free_strict_possible`.
- `liquidity_rates_regime` (P1): selection throttle before drawdown appears / current `proxy_possible`.
- `earnings_transcript_guidance` (P1): guidance tone/surprise/QA pressure filter / current `blocked_or_proxy`.
- `analyst_revision_rating_history` (P1): expectation gap and downgrade risk / current `blocked_or_proxy`.
- `contract_customer_confirmation` (P1): revenue validation quality / current `blocked_by_entity_mapping`.
- `sector_macro_regime_stress` (P2): avoid buying normal winners during hostile regime / current `proxy_possible`.
- `liquidity_spread_slippage` (P2): thin-edge fragility before entry / current `proxy_possible`.
- `policy_news_entity_mapping` (P2): external catalyst and budget-risk filter / current `blocked_by_mapping`.

Next acquisition queue:

- `strict_raw_asof_certification`: Build raw source packet ledger for all selected and candidate rows before any assignment scoring.
- `financing_dilution_sec_events`: Parse SEC forms and exhibits for offerings/ATM/S-3/S-1/424B/Form D/8-K dilution and survival context.
- `liquidity_rates_regime`: Attach PIT rates/liquidity regime before selection throttles; use official vintage/release timestamps where possible.
- `earnings_transcript_guidance`: Acquire transcript metadata/text where free/API permits; keep proxy until publication/receipt time certified.
- `analyst_revision_rating_history`: Determine entitlement for PIT analyst revisions; do not substitute latest recommendation as historical truth.
- `contract_customer_confirmation`: Create certified customer/contract confirmation packets only where accession/customer ID mapping is explicit.
- `liquidity_spread_slippage`: Attach ADV/volume/spread proxy before KIS guard backtests; fixed fee alone is insufficient.
- `sector_macro_regime_stress`: Attach PIT sector breadth/rates/vintage macro so stress guard can act before portfolio drawdown.

Admission rule:

- `strict_pass` can score assignment.
- `proxy_allowed` can annotate only.
- `blocked` blocks paper/live when required.
- `unknown` is neutral missing evidence.
- Missing source is never negative.

## No-Background Decision-Maker Report

Conclusion first: the next work is source acquisition, not another backtest.

The system currently does not have enough certified historical source to know whether the brain could have known the right facts at the decision time. We created the source gap ledger and acquisition queue so Task2541+ can fill the most important gaps without mixing missing data with negative signals.

## Artifact Manifest

- Artifacts: `data/artifacts/task_2531_2540_selector_source_gap_program/`.
- Validator: `python scripts/trader_brain_2531_2540_selector_source_gap_program_validate.py`.

Test results do not modify strategy acceptance status.
Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
