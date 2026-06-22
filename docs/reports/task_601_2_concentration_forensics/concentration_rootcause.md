# T601-2 Concentration Root Cause

## Problem

- top3 concentration equals 1.0, so the current funnel cannot support acceptance review.

## Evidence

- symbol_entropy=1.059385
- top1_share=0.416667
- top3_share=1.0
- gini_coefficient=0.483333

## Root Cause

- Universe Bias: CONFIRMED; top3 generated share=0.991498; symbols with generated candidates=5
- Ranking Bias: LIKELY; top3 ordered share=1.0; ordered symbols=3
- Cooldown Failure: CONFIRMED; cooldown_rate=0.0; repeated orders exist while cooldown blocks are absent.
- Risk Filter Bias: CONFIRMED_NON_DIVERSIFYING; Eligibility does not diversify symbols; generated candidates mostly pass as ELIGIBLE.
- Liquidity Bias: NOT_PROVEN; candidate_funnel_events has no liquidity field; concentration cannot be attributed to liquidity with current evidence.

## Fix Candidate

- T601-3 should decide whether cooldown, ranking, or portfolio selection changes are allowed.

## Acceptance Impact

- PASS_ROOT_CAUSE_IDENTIFIED: concentration=1.0 is explainable as universe/ranking/cooldown/risk-filter concentration, not liquidity evidence.
