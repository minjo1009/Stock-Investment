# Task683 GPT Panel Review

## Review Role

- External review-only panel: professional quant trader, event-driven PM, sector/macro PM, senior quant engineer, research-governance reviewer.
- GPT output is not source truth, market data, label, or assignment input.
- Scope was restricted to the same five engines only.

## Core Finding

Task682 v2 is a preservation engine, not yet a selection engine.

- It preserved active cap3 big winners.
- It did not improve final capital versus active cap3.
- Therefore, the five engines still do not produce enough pre-entry superiority evidence to admit better challengers.

## Five Engine Diagnosis

1. Leadership Lifecycle

- `participating_theme` is too large and behaves like a neutral warehouse.
- Firm-grade context needs phase strength, breadth confirmation, rotation risk, and reason codes.

2. Catalyst Quality

- Active cap3 contains many `catalyst_economic_quality=low` trades.
- Low catalyst may mean true weakness, but it may also mean price-led, relation-supported, theme-supported, or delayed absorption.
- Low must not become a hard reject without absorption context.

3. Archetype Candidate

- Active cap3 contains many `mixed_or_unclear_candidate` trades.
- This is the largest weakness.
- Mixed must be decomposed into price-led, catalyst-led, theme-led, relation-led, delayed absorption, conflicted-but-alive, and true-unclear.

4. Same Symbol Context

- Same-symbol downgrade must not be used as a direct negative rank.
- The same symbol can be a different setup on a different day.
- Same Symbol should be a conflict interpreter, not a ranker.

5. Cohort Slot Qualification

- v2 is too conservative.
- It protects incumbents but cannot admit better challengers.
- Slot replacement needs a context superiority packet comparing challenger versus incumbent inside the same `entry_ts` cohort.

## Required Development Contract

- Do not add a new global score.
- Do not add a new stage.
- Do not use return, labels, future price, symbol blacklist, or theme blacklist.
- Stay inside the same five engines.
- Add context contracts:
  - mixed context decomposition,
  - catalyst-low reinterpretation,
  - same-symbol conflict interpretation,
  - context superiority packet.

## Plain Conclusion

The next improvement is not another filter.

The next improvement is to explain the unclear buckets well enough that slot replacement can admit challengers without killing active cap3 winners.
