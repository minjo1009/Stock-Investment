# Task 328: Regime Failure Diagnosis

## Core Answer

- Main root cause: `oos_drift`.
- This report answers whether regime definitions are wrong, whether regime alone is too coarse, whether entry linkage is weak, and whether OOS drift is dominant.

## Regime Entry Linkage Diagnosis

| regime_state | linkage_strength_score | stability_score | oos_retention_score | train_expectancy_r | oos_expectancy_r | train_heterogeneity_score | dominant_archetype_share | diagnosis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| failed_recovery | 0.310767 | 0 | -45.9432 | 0.026847 | -1.23344 | 0.066667 | 0.340426 | strong_but_not_stable |
| high_vol_chop | 0.11192 | 0.037326 | -3.6196 | 0.256199 | -0.927339 | 0.3 | 0.639053 | structurally_misspecified |
| narrow_leadership_trend | 0.081573 | 0.420519 | 0 | 1.16448 | 0 | 0.333333 | 0.524823 | structurally_misspecified |
| risk_off_reversal | 0.044896 | 0.444195 | 2.38396 | 0.463633 | 1.10528 | 0.3 | 0.640625 | structurally_misspecified |
| rebound_chop | 0.019545 | 0.570018 | -0.591269 | 0.831317 | -0.491532 | 0.533333 | 0.69927 | weak_but_consistent |
| late_extension | 0.006566 | 0.543234 | -0.598536 | 0.666688 | -0.399037 | 0.566667 | 0.446296 | weak_and_noisy |

## Regime Drift

| regime_state | train_trade_count | oos_trade_count | trade_share_delta | expectancy_delta | path_mix_shift | feature_band_mix_shift | archetype_mix_shift | drift_type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| failed_recovery | 47 | 2 | -0.016544 | -1.26028 | 1 | 0.592199 | 1 | entry_linkage_drift |
| high_vol_chop | 169 | 10 | -0.045514 | -1.18354 | 0.91716 | 0.598619 | 1 | entry_linkage_drift |
| risk_off_reversal | 192 | 29 | 0.036049 | 0.64165 | 0.519756 | 0.260057 | 0.289332 | entry_linkage_drift |
| narrow_leadership_trend | 141 | 0 | -0.079481 | -1.16448 | 0.5 | 0.5 | 0.5 | entry_linkage_drift |
| late_extension | 540 | 71 | 0.048837 | -1.06573 | 0.407929 | 0.201348 | 0.252713 | entry_linkage_drift |
| rebound_chop | 685 | 89 | 0.056653 | -1.32285 | 0.373329 | 0.327237 | 0.245108 | entry_linkage_drift |

## Root Cause Ranking

| contribution_rank | root_cause | evidence_score | evidence_summary |
| --- | --- | --- | --- |
| 1 | oos_drift | 1 | train-to-OOS regime/path/archetype relationship shifts materially |
| 2 | regime_misspecification | 0.55 | low separation or structurally misspecified regimes dominate |
| 3 | combination_effect | 0.460417 | multiple failure modes contribute without a single dominant cause |
| 4 | within_regime_heterogeneity | 0.385057 | high internal variance and subbehavior concentration dominate regimes |
| 5 | weak_entry_feature_linkage | 0.374713 | regime does not convert into stable archetype-level expectancy separation |

## Final Conclusion

- Regime definition wrong? `50.00%` of regimes look structurally misspecified.
- Regime alone too coarse? `16.67%` of regimes look weak and noisy from internal heterogeneity.
- Entry feature linkage weak or unstable? `16.67%` of regimes lose linkage stability into OOS.
- Root causes are ranked above in descending evidence strength.