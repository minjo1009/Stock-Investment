# Task658 GPT Review Packet

GPT was asked to review the current relation engine as a firm-grade professional quant/PM reviewer.

Important constraints:

- GPT is review-only and not a data source.
- Do not recommend simply collecting more data.
- Focus on why the current logic is not firm-grade with current information.
- Focus on whether industry/theme-specific rules are required.

Evidence sent:

- Task639 baseline: positive contract/customer OR content supply/demand, delay1d, existing exit, equal max5, $1000 to $7639.62, max drawdown -23.76 percent.
- Task655: release-time repaired macro context attached to 100 percent of Task639 core rows, vintage-perfect as-of deferred.
- Task656: macro can only be soft modifier; no standalone entry, hard block, full-entry promotion, or size boost.
- Task657: soft macro wrappers failed to beat Task639.
- Task657 best non-baseline: soft_pressure_hold10, $7625.35, max drawdown -23.16 percent.
- Task657 macro diagnostics:
  - macro_mixed: 848 rows, avg +7.58 percent, win 58.7 percent.
  - macro_supportive: 720 rows, avg +3.06 percent, win 48.9 percent.
  - macro_pressure: 53 rows, avg +14.00 percent, win 60.4 percent.
- Current code uses one global pressure/support count and applies the same skip/delay/hold wrapper across all themes.

Questions:

1. Why is the current relationship engine not firm-grade beyond needing more data?
2. Why might macro pressure outperform macro supportive in this strategy?
3. What concrete firm-grade relation examples should be emulated?
4. Should rules be industry/theme-specific?
5. What should Task658/659 implement next with current data only?
6. What should be explicitly avoided?
