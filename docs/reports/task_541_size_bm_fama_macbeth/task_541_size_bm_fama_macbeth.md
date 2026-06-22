# Task 541 Size Book-to-Market Fama-MacBeth Diagnostic

## Decision Summary

- Strategy acceptance: SIZE_BM_FAMA_MACBETH_DIAGNOSTIC_READY_SOURCE_GRADE_LIMITED
- Task503 size coverage: 59.29%
- Task503 book-to-market coverage: 54.63%
- Fama-MacBeth size/BM run: 1
- Deployment-ready: NO

## Quant Expert Report

Task541 builds actual diagnostic size and book-to-market factors from SEC companyfacts book equity, SEC-derived shares, and previous daily close market cap.
Daily close market cap is joined strictly from dates before the intraday entry date; same-day daily close is not used as an entry-time feature.
Book equity is joined by SEC filed date, not by fiscal period end alone, which preserves as-of discipline.
Fama-MacBeth proxy coefficients are diagnostic: size t-stat proxy -1.80, book-to-market t-stat proxy 1.50.
The Fama-MacBeth-style result is a validation layer only. It is not an entry trigger and remains source-grade limited versus CRSP/Compustat.

## No-Background Decision-Maker Report

We added real size and book-to-market diagnostics to the factor-premium check instead of assuming those values.
This helps distinguish whether strategy returns are just exposure to large/small or value/growth effects, but it does not make the strategy deployable.
Coverage is explicit: size 59.29%, book-to-market 54.63%. Missing values are not filled with guesses.

## Artifact Manifest

See `artifact_manifest.csv`.
