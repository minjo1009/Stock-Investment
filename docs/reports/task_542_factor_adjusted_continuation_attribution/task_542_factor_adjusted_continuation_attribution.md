# Task 542 Factor-Adjusted Continuation Edge Attribution

## Decision Summary

- Strategy acceptance: FACTOR_ADJUSTED_ATTRIBUTION_DIAGNOSTIC_ONLY
- Candidate sets evaluated: 3
- Factor-adjustment coverage: 82.03%
- True continuation alpha candidates: 0
- Deployment-ready: NO

## Quant Expert Report

Task542 fits a broad exact-lifecycle factor model using Fama-French cumulative factors plus Task541 size and book-to-market diagnostics.
The fitted factor model is then used only as an attribution lens on Task505/529/530 continuation candidates.
task505_selected_two_year_strategy: raw 29.80%, factor-adjusted residual 14.68%, coverage 83.50%, status mixed_factor_adjusted_evidence.
task529_trend_closepos_only_097: raw 17.28%, factor-adjusted residual 4.70%, coverage 80.70%, status mixed_factor_adjusted_evidence.
task530_paper_shadow_candidate: raw 17.28%, factor-adjusted residual 4.70%, coverage 80.70%, status mixed_factor_adjusted_evidence.
This is not a trading trigger and remains source-grade limited because size/BM coverage is incomplete and SEC-derived rather than CRSP/Compustat-grade.

## No-Background Decision-Maker Report

We checked whether the continuation candidates still look good after removing broad factor exposure.
A positive residual means the candidate may contain continuation-specific edge beyond market/size/value style exposure.
This still does not approve deployment; it tells us where the next validation should focus.

## Artifact Manifest

See `artifact_manifest.csv`.
