# Task682 GPT Review

## Review Role

- External review-only professional quant trader, portfolio manager, and senior quant engineer.
- GPT output is not used as source truth, market data, label, or assignment input.
- Scope was restricted to the five requested engines only. No new data proposal was accepted.

## Core Finding

Task682 had the correct outer structure, but the first implementation was still closer to label compression than a prediction stack.

Weak areas:

- Catalyst Quality said almost everything was high or medium, so it did not separate good, conflicted, and weak information.
- Archetype Candidate missed theme rotation and steady trend structures.
- Same Symbol Context did not truly compare same-symbol context variants.
- Cohort Slot Qualification acted like a sorted ranking table instead of a replacement review.

## Required Five-Engine Fix

1. Leadership Lifecycle Panel

- Reduce the oversized `participating_theme` bucket.
- Separate emerging, persistent, late, fading, and neutral states using theme return, breadth, volume, rank, and market state.
- Leadership should support archetype confidence, not become a standalone buy rule.

2. Catalyst Quality Matrix

- Add low, conflicted, overhang, and unclear catalyst states.
- Use positive dimensions, direct bearish counts, negative subtype counts, refined strength, and source/asof quality.
- Catalyst should not be a simple "good news exists" flag.

3. Archetype Candidate Engine

- Keep it as an entry-time upside-structure classifier, not a winner label.
- Use reason-code accumulation across leadership, catalyst, price acceptance, relation support/pressure, trend, near-high, range position, and volume.
- Theme rotation and steady trend candidates must be reachable states.

4. Same Symbol Context Matrix

- Compare current symbol context to prior same-symbol context signatures.
- Do not blacklist symbols or use symbol-level realized PnL.
- Explain whether the same symbol is an upgrade, downgrade, repeat, new context, or unclear variant.

5. Cohort Slot Qualification

- Do not use global rank.
- Compare candidates only within the same `entry_ts` cohort.
- Use active cap3 as the baseline slot set for displacement review.
- A challenger may replace an incumbent only if it has source safety, archetype advantage, price/leadership advantage, catalyst non-deterioration, concentration non-deterioration, and the incumbent has a clear pre-entry vulnerability.
- `priority_rank` remains a final tie-breaker, not the primary ranking rule.

## Post-Fix Interpretation

The rewritten v2 preserved active cap3 big winners, but it did not improve final capital versus active cap3.

Plain conclusion:

- Damage control improved.
- Prediction improvement is still not proven.
- The five engines are now closer to the correct shape, but still research-only until they improve return without removing active cap3 winners or degrading OOS behavior.
