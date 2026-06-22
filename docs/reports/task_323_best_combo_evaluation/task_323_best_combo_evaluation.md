# Task 323 Production Upgrade
## Executive Summary
- Evaluation end date: 2026-04-29
- Anchored OOS window: 2025-11-01 ~ 2026-04-29
- Mixed top-3 count: 3
- Primary status: 추가 검증 1순위 (보류)
- Primary candidate: `RANGE_COMPRESSION|HIGH_TOUCH|BREAKOUT_LEVEL_WITH_SLIPPAGE|STRUCTURE_LOW_STOP|DISABLE_ENTRY_BAR_STOP|atr1.5|hold20|liq20000000|lb10|w0.15`
## Summary Table
| Hypothesis | Result | Confidence | Key Evidence |
| --- | --- | --- | --- |
| regime filter too coarse | True | 보통 | worst regime `true_early_trend` loser share 1.00, expectancy -1.405R; best regime `risk_off` expectancy 0.873R |
| breakout is late-chase | True | 보통 | gate hits 2, follow-through hits 4 |
| losses driven by tail events | False | 낮음 | worst decile loss share 0.24 |
| losses concentrated in specific sectors | True | 보통 | leading loser sector `software/internet` total R -14.13, win rate 0.00 |
## Final Rule Set
| Type | Rule |
| --- | --- |
| Block | if regime in {true_early_trend, failed_recovery} and sector in {semis, software/internet} and (crowding_proxy or rs_percentile_20d in high band): block |
| Allow | if regime in {strong_trend, extended, risk_off} and not crowded and entry extension band <= mid and semis concentration < high: allow |
| Size | if mixed_ft_high_mae then reduce_next_open_day3 |
| Exit | if weak_ft5_or_high_retrace5 then exit_next_open_day5 |
| System Flow | Pre-entry: regime/cross-section gate -> Entry: allow/size -> Post-entry: day3/day5 validation -> Exit/Reduce next open |
## System Flow
| Step | Logic |
| --- | --- |
| Pre-entry filter | regime state + sector concentration + crowding + entry extension bands |
| Entry decision | allow, block, or reduce based on rule candidate stack |
| Post-entry validation | Day1~3 and Day3~5 EOD windows, execute at next trading day open |
| Exit logic | weak FT plus high retrace or crowded weak-regime failure triggers exit/reduce |
## Key Drivers
| Category | Top Feature |
| --- | --- |
| Regime | regime_state |
| Entry | ret_20d_pre |
| Post-entry | adverse_excursion_5d_pct |
| Cross-section | sector_bucket |
## Failure Map
| Condition | Effect |
| --- | --- |
| regime | worst regime `true_early_trend` loser share 1.00, expectancy -1.405R; best regime `risk_off` expectancy 0.873R |
| sector | leading loser sector `software/internet` total R -14.13, win rate 0.00 |
| entry | gate hits 2, follow-through hits 4 |
| post-entry | weak_ft_high_retrace |
## Success Map
| Condition | Effect |
| --- | --- |
| regime | best regime `risk_off` supports positive expectancy |
| sector | best regime-sector combos lean on `tech, semis` |
| entry | winners show better early continuation than losers across FT/retrace comparisons |
| post-entry | hold bias when FT_3d band is strong and retrace_3d band is low/mid |
## Separation Layer
| Feature | Threshold | Impact |
| --- | --- | --- |
| regime_state | avoid true_early_trend / failed_recovery / rebound_chop | importance 2.279, stability 0.500 |
| adverse_excursion_5d_pct | upper/lower pooled band | importance 0.945, stability 1.000 |
| sector_bucket | semis and software/internet risk bucket | importance 0.928, stability 0.250 |
| follow_through_5d_pct | upper/lower pooled band | importance 0.910, stability 1.000 |
| follow_through_3d_pct | weak/mixed/strong band | importance 0.835, stability 1.000 |
## Actionable Rules
### Block Rules
- `if regime in {true_early_trend, failed_recovery} and sector in {semis, software/internet} and (crowding_proxy or rs_percentile_20d in high band): block` -> expectancy delta 0.055, drawdown delta 4.216, robustness `low`
- `if regime == rebound_chop and vol_expansion_ratio in high band and breakout_strength_pct in weak band: block` -> expectancy delta -0.029, drawdown delta -0.280, robustness `low`
### Allow Rules
- `if regime in {strong_trend, extended, risk_off} and not crowded and entry extension band <= mid and semis concentration < high: allow` -> expectancy delta nan, robustness `low`
### Size Rules
- `if mixed_ft_high_mae then reduce_next_open_day3` -> expectancy delta 0.094, drawdown delta 6.011, robustness `medium`
- `if regime in {true_early_trend, extended} and (semis concentration high or crowded): reduce size` -> expectancy delta 0.026, drawdown delta 3.044, robustness `low`
### Exit Rules
- `if weak_ft5_or_high_retrace5 then exit_next_open_day5` -> expectancy delta 0.106, drawdown delta 6.987, robustness `medium`
- `if weak_ft_crowded_bad_regime then exit_next_open_day3` -> expectancy delta 0.053, drawdown delta 3.500, robustness `medium`
- `if weak_ft_high_retrace then exit_next_open_day3` -> expectancy delta 0.005, drawdown delta 0.310, robustness `medium`
## Pseudocode
```python
if regime in BAD_REGIMES:
    block
elif sector_concentration > high_band:
    reduce_or_block
elif entry_quality < acceptable_band:
    skip
else:
    enter
if ft_3d_band == "weak" and retrace_3d_band == "high":
    exit_next_open
elif ft_3d_band == "mixed":
    reduce_next_open
else:
    hold
```
## Supporting Notes
- Worst month (ALL losers): `2026-02`
- Largest losing symbol (ALL losers): `GOOGL`
- Largest losing entry type (ALL losers): `planned_breakout_fill`
- `signal_to_entry_delay_bars` is constant `0` and treated as non-informative.
- This report converts current findings into implementable structural logic. It does not optimize parameters or introduce a new strategy.
