# Task 349 - Cross-Regime Persistence & Failure Anatomy

- decision: TEMPORARY_MARKET_PHASE_ARTIFACT
- persistent_structure_share: 0.211791
- temporary_phase_share: 0.788209
- weak_dimension_count: 1
- shadow_pass_count: 4

## Final Interpretation
1. Structural or phase-dependent: phase-dependent
2. Survives regime transitions: no
3. Breakout logic or liquidity/volatility proxy: still strongly influenced by liquidity/volatility conditions
4. Winner selection or failure avoidance: failure avoidance
5. Tactical sleeve deployability: not shadow-ready yet
6. What remains before shadow: regime-transition survival, concentration control, slippage drift monitoring, and execution-quality persistence.

## Persistence Scorecard
| dimension | score_0_to_3 |
| --- | --- |
| regime_robustness | 3 |
| time_robustness | 0 |
| cost_robustness | 3 |
| sector_robustness | 2 |
| execution_robustness | 3 |
| concentration_fragility | 0 |
| decay_sensitivity | 0 |

## Top Failure Types
| failure_type | trade_count | expectancy | share_of_failures | mean_slippage_sensitive_loss_proxy |
| --- | --- | --- | --- | --- |
| crowded_continuation_failure | 67 | -0.323272 | 0.770115 | -0.473272 |
| gap_exhaustion | 4 | -1.08464 | 0.045977 | -1.23464 |
| failed_breakout_retest | 3 | 1.7647 | 0.034483 | 1.6147 |
| opening_imbalance_failure | 2 | -1.23344 | 0.022989 | -1.38344 |
| immediate_rejection | 0 |  | 0 |  |