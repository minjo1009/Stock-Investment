# Task 323 Structural Breakout Robustness Audit

## Scope
- Ranked scenarios audited: top 20 by label -> Sharpe -> expectancy -> CAGR -> trade count.
- Full-period ranking uses the same scenario universe as Task 322, rerun with unique scenario identifiers.

## Top Scenario
- full-period best: `RANGE_COMPRESSION|HIGH_TOUCH|BREAKOUT_LEVEL_WITH_SLIPPAGE|ATR_STOP|DISABLE_ENTRY_BAR_STOP|atr2.0|hold20|liq20000000|lb10|w0.15`
- OOS top1: `PIVOT_HIGH|HIGH_TOUCH|BREAKOUT_LEVEL_WITH_SLIPPAGE|ATR_STOP|DISABLE_ENTRY_BAR_STOP|atr1.5|hold10|liq20000000|age20`
- full-period best holds in OOS: `False`

## Fill Assumption Snapshot
- median open > planned entry ratio (top 20): 0.4308
- median open > actual entry ratio (top 20): 0.0000
- median fill_at_open ratio (top 20): 0.4308
- median rejected_by_gap_over_entry / triggered ratio (top 20): 0.0016

## Symbol Exclusion Snapshot
- median CAGR after best-symbol exclusion: 18.3902
- median CAGR after worst-symbol exclusion: 18.3902

## Artifacts
- `all_scenarios_ranked.csv`
- `top20_summary.csv`
- `top20_symbol_contribution.csv`
- `top20_symbol_exclusion_impact.csv`
- `top20_fill_assumption_audit.csv`
- `liquidity_sensitivity.csv`
- `same_bar_stop_comparison.csv`
- `parameter_cluster_summary.csv`
- `top20_trade_overlap_matrix.csv`
- `in_sample_ranked.csv`
- `out_of_sample_ranked.csv`
- `walk_forward_summary.csv`
