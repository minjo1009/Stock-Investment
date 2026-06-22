# Task 352 - Relative Convexity Reframing of Continuation Regimes

- decision: REGIME_DEPENDENT_CONTINUATION_ALPHA
- top_regime_id: market_breadth_state=broad|broad_participation_state=narrow_participation
- top_continuation_quality_score: 0.742647

## Final Interpretation
1. Positive continuation exists: `True`
2. Offensive convex continuation exists: `True`
3. Structural continuation survives: `False`
4. Best regimes are economically useful: `True`
5. Result classification: `REGIME_DEPENDENT_CONTINUATION_ALPHA`

## Top Relative Regimes
| regime_id | axes | buckets | trade_count | expectancy | positive_tail_ratio | convex_payoff_score | cost_adjusted_expectancy | rolling_robustness | participation_durability | structural_share | artifact_dependence | top_decile_contribution | positive_skew_proxy | rolling_tail_survival | cost_adjusted_expectancy_pct | positive_tail_ratio_pct | rolling_robustness_pct | rolling_tail_survival_pct | structural_share_pct | participation_durability_pct | top_decile_contribution_pct | continuation_quality_score | candidate_type |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| market_breadth_state=broad|broad_participation_state=narrow_participation | market_breadth_state|broad_participation_state | broad|narrow_participation | 552 | 0.914634 | 0.298093 | 0.55204 | 0.764634 | 1 | 0.062042 | 0.18757 | 0.81243 | 0.361931 | 3.77014 | 0.25 | 1 | 0.617647 | 0.955882 | 0.911765 | 0.294118 | 0.588235 | 0.970588 | 0.742647 | interaction |
| volatility_state=low_vol|liquidity_state=liquidity_contracting | volatility_state|liquidity_state | low_vol|liquidity_contracting | 480 | 0.854124 | 0.335185 | 0.496101 | 0.704124 | 0.75 | 0.045274 | 0.227167 | 0.772833 | 0.355154 | 3.31915 | 0.25 | 0.911765 | 0.941176 | 0.602941 | 0.911765 | 0.558824 | 0.441176 | 0.911765 | 0.736765 | interaction |
| liquidity_state=liquidity_contracting | liquidity_state | liquidity_contracting | 970 | 0.665474 | 0.301806 | 0.474413 | 0.515474 | 0.75 | 0.086197 | 0.309892 | 0.690108 | 0.342601 | 2.97417 | 0.25 | 0.647059 | 0.705882 | 0.602941 | 0.911765 | 0.882353 | 0.647059 | 0.5 | 0.720588 | single_axis |
| market_breadth_state=broad | market_breadth_state | broad | 737 | 0.865468 | 0.293728 | 0.54856 | 0.715468 | 1 | 0.069938 | 0.199035 | 0.800965 | 0.348764 | 3.60962 | 0.25 | 0.941176 | 0.470588 | 0.955882 | 0.911765 | 0.323529 | 0.617647 | 0.735294 | 0.714706 | single_axis |
| session_timing_bucket=first_30m|execution_quality_bucket=strong | session_timing_bucket|execution_quality_bucket | first_30m|strong | 83 | 0.839567 | 0.327283 | 0.424407 | 0.689567 | 0.5 | 0.009187 | 0.348735 | 0.651265 | 0.361597 | 4.27427 | 0.25 | 0.882353 | 0.897059 | 0.25 | 0.911765 | 0.926471 | 0.205882 | 0.941176 | 0.702206 | interaction |

## Top Utility
| selection_bucket | regime_id | trade_count | annual_trade_frequency | cost_adjusted_expectancy | rolling_robustness | structural_share | tail_profile_strength | economic_usefulness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| top3_single_axis | session_timing_bucket=first_30m | 92 | 23.7645 | 0.573321 | 0.5 | 0.348735 | high | moderate |
| top5_overall | market_breadth_state=broad|broad_participation_state=narrow_participation | 552 | 113.78 | 0.764634 | 1 | 0.18757 | moderate | moderate |
| top5_overall | market_breadth_state=broad | 737 | 151.913 | 0.715468 | 1 | 0.199035 | low | moderate |
| top5_overall | volatility_state=low_vol|liquidity_state=liquidity_contracting | 480 | 99.2752 | 0.704124 | 0.75 | 0.227167 | high | moderate |
| top5_overall | session_timing_bucket=first_30m|execution_quality_bucket=strong | 83 | 21.4397 | 0.689567 | 0.5 | 0.348735 | high | moderate |
| top5_overall | liquidity_state=liquidity_contracting | 970 | 199.714 | 0.515474 | 0.75 | 0.309892 | moderate | moderate |

## Positive vs Convex vs Structural
| regime_id | candidate_type | trade_count | cost_adjusted_expectancy | rolling_robustness | positive_tail_ratio | top_decile_contribution | structural_share | continuation_quality_score | positive_drift_continuation | offensive_convex_continuation | structural_continuation |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| market_breadth_state=broad|broad_participation_state=narrow_participation | interaction | 552 | 0.764634 | 1 | 0.298093 | 0.361931 | 0.18757 | 0.742647 | True | True | False |
| volatility_state=low_vol|liquidity_state=liquidity_contracting | interaction | 480 | 0.704124 | 0.75 | 0.335185 | 0.355154 | 0.227167 | 0.736765 | True | True | False |
| liquidity_state=liquidity_contracting | single_axis | 970 | 0.515474 | 0.75 | 0.301806 | 0.342601 | 0.309892 | 0.720588 | True | False | False |
| market_breadth_state=broad | single_axis | 737 | 0.715468 | 1 | 0.293728 | 0.348764 | 0.199035 | 0.714706 | True | False | False |
| session_timing_bucket=first_30m|execution_quality_bucket=strong | interaction | 83 | 0.689567 | 0.5 | 0.327283 | 0.361597 | 0.348735 | 0.702206 | True | True | False |

## Artifact-Adjusted Structural Scores
| regime_id | scenario | trade_count | expectancy | positive_tail_ratio | convex_payoff_score | structural_share | temporary_phase_share | outside_peak_expectancy |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| market_breadth_state=broad|broad_participation_state=narrow_participation | structural_only | 171 | 0.26427 | 0.27192 | 0.260643 | 0.18757 | 0.81243 | 0.257683 |
| volatility_state=low_vol|liquidity_state=liquidity_contracting | structural_only | 222 | 0.186304 | 0.259699 | 0.251095 | 0.227167 | 0.772833 | 0.481738 |
| liquidity_state=liquidity_contracting | structural_only | 494 | 0.225269 | 0.263558 | 0.282012 | 0.309892 | 0.690108 | 0.128529 |
| market_breadth_state=broad | structural_only | 255 | 0.25435 | 0.279314 | 0.342581 | 0.199035 | 0.800965 | 0.342153 |
| session_timing_bucket=first_30m|execution_quality_bucket=strong | structural_only | 40 | 0.521414 | 0.291586 | 0.314522 | 0.348735 | 0.651265 | 0.230525 |