# Task 329: Breakout State Model Redesign

## Core Answer

- Decision: `fully_replaced`.
- Proposed structural axes: `trend_quality, extension_pressure, participation_quality`.
- The new state model is judged by payoff separation, internal homogeneity, and OOS retention rather than descriptive intuition.

## State Axes

| axis_name | definition | input_features | state_values | expected_payoff_implication | selected_for_final_state_model | selection_score |
| --- | --- | --- | --- | --- | --- | --- |
| trend_quality | trend persistence and trend support under the breakout | ret_20d_pre|dist_to_sma200_pct | weak|neutral|strong | strong trend should improve continuation and reduce false starts | True | -4.91507 |
| extension_pressure | how late and stretched the breakout is before entry | dist_to_sma200_pct|breakout_strength_pct | low|medium|high | high extension should increase retrace and crowded failure risk | True | -4.83229 |
| participation_quality | breadth and participation behind the move | sector_breadth | narrow|mixed|broad | broad participation should improve follow-through stability | True | -5.83715 |
| noise_pressure | noise and whipsaw pressure around breakout launch | vol_contraction_ratio | compressed|balanced|high_noise | high noise should raise volatile noise and weak continuation odds | False | -6.29688 |
| reversal_pressure | mean-reversion or rebound pressure likely to break continuation | ret_20d_pre|regime_state | low|medium|high | high reversal pressure should increase failed continuation states | False | -6.52536 |

## Framework Comparison

| framework | between_state_expectancy_dispersion | within_state_realized_r_variance_mean | within_state_path_entropy_mean | oos_linkage_retention | drift_sensitivity |
| --- | --- | --- | --- | --- | --- |
| old_regime | 0.373234 | 3.35362 | 1.87694 | -8.06147 | 0.633502 |
| new_state_model | 0.496093 | 3.3205 | 1.50612 | -0.472453 | 0.611588 |

## Final Conclusion

- This report answers what should replace the current regime framework and why the proposed state model is more appropriate for breakout payoff separation.
- The recommended next step is `state validation` first, then `state-conditioned application` only if this redesign retains OOS structure.