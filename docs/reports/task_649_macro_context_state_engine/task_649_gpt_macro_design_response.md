# Task649 GPT Macro Design Response

Captured via Chrome ChatGPT project tab.

GPT role: external PM/CIO quant reviewer only.

## Summary

- Task649 should build an as-of macro context layer, not a macro alpha model.
- Macro should act only as a context modifier for company, policy, sector, and chart signals.
- Monthly indicators must not use observation date as release date.
- If an exact release calendar is missing, use a conservative lag and mark the state provisional.
- Macro supportive alone must never create a buy signal.

## Recommended Macro Layers

- Growth / employment: UNRATE, PAYEMS.
- Inflation: CPIAUCSL, PCEPI, PCEPILFE.
- Rates / curve: DFF or FEDFUNDS, DGS2, DGS10, T10Y2Y.
- Dollar: DTWEXBGS.
- Oil: DCOILWTICO.
- Credit: BAMLH0A0HYM2, BAA10Y.
- Liquidity: WALCL, RRPONTSYD or similar.

## Recommended State Buckets

- growth: improving, softening, stress, source_gap.
- inflation: easing, sticky, reaccelerating, source_gap.
- rates: supportive, pressure, curve_stress, source_gap.
- dollar: tailwind, pressure, source_gap.
- oil: tailwind, pressure, shock, source_gap.
- credit: easing, tightening, stress, source_gap.
- liquidity: supportive, tight, source_gap.

Combined macro state should stay simple:

- macro_supportive
- macro_mixed
- macro_pressure
- macro_stress
- macro_source_gap

## As-Of Rule

Each macro observation should carry:

- series_id
- observation_date
- value
- release_ts or conservative lag policy
- tradable_after_ts
- source_quality
- asof_valid_flag
- source_gap_flag

If no exact release calendar exists, do not pretend the release time is known. Use conservative lag and keep promotion blocked.

## Combination With Task648

Task648 state should not be overwritten. Use:

```text
Task648 provisional_trading_context_state
+ Task649 macro_context_modifier
= trading_context_state_v2
```

Examples:

- company positive + macro supportive: normal/full candidate if chart and source quality confirm.
- company positive + macro mixed: normal or confirmation required.
- company positive + macro pressure: size down or confirmation required.
- macro stress: block/hold only when other risk layers confirm.
- macro source gap: no macro upgrade and no macro penalty.

## Forbidden In First Implementation

- Using observation date as release date.
- Treating monthly indicators as known before release/tradable-after.
- Using macro supportive alone as an entry signal.
- Treating source gaps as positive or negative.
- Creating too many overfit macro regimes.
- Tuning thresholds from Task648 outcomes.
