# Task608F Entry-Reduce Logic Gap Review

## Decision Summary

- Verdict: FAIL_ENTRY_REDUCE_IS_OUTCOME_LABEL_NOT_LIVE_LOGIC
- Strategy acceptance status: NOT_ACCEPTED
- Deployment status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Key metrics: Task608DE OOS clean entries averaged +26.03% with 92.59% win rate; entry-reduce failed entries averaged -16.45% with 0.00% win rate.
- What changed: entry-reduce is now classified as a logic gap, not only a bad cohort.
- Next action: build live-detectable entry failure state diagnostics before any refinement or suppression claim.

## Quant Expert Report

- Data source and source readiness: Task608DE, Task524, Task501, Task508, and GPT review notes. GPT is review-only and not a source of truth.
- Exact join keys: no new matching was performed. This review consumes existing repo-native artifacts.
- Leakage audit: current `entry_reduce_failure_flag` is outcome-derived and remains blocked from assignment fields.
- Split/OOS metrics: Task608DE uses Task509 walk-forward OOS rows. Task524 simple suppression OOS did not pass.
- Failure decomposition: the largest failure clusters are `opening_drive`, `trend_persistence_near_high`, `aerospace_defense_space`, `data_devops_software`, BA, and RKLB, but simple category dropping failed OOS.
- Cost/slippage stress where PnL changed: unchanged from Task508/Task608. Any future reduce engine must be cost-stressed because it can increase turnover.
- Remaining blockers: no live-detectable pre-entry or post-entry reducer exists yet.

### Entry-Reduce Team Finding

The main weakness is semantic. In the current backtest chain, `entry_reduce_failure_flag` is not a trading decision.

- Task501 defines it as `int(net_return_from_entry <= -0.03)`.
- Task508 recomputes it after cost stress as adjusted `net_return_from_entry <= -0.03`.
- Therefore it is a loss label, not a pre-entry filter or live post-entry reduce rule.

This means the system knows which trades lost after the fact, but it has not proved those trades were detectable before or shortly after entry.

### Why Simple Suppression Failed

Task524 already tested simple families such as:

- drop opening-drive cases
- keep trend-persistence only
- drop volume-confirmed reclaim cases
- drop weaker theme-participation regimes

The result was `SUPPRESSION_FAIL_NEEDS_NEW_FEATURES`.

Reason: the problem is conditional, not categorical. Some `opening_drive` trades work. Some fail. The missing logic is the state transition that separates:

- opening drive into continuation
- opening drive into exhaustion

### Required Diagnostics Before Refinement

Task608F follow-through must build path diagnostics first:

- entry-to-MFE and entry-to-MAE path split
- first 15/30/60/120 minute return after entry
- VWAP hold or VWAP fail after entry
- opening-range high/low reclaim or rejection
- volume decay after breakout
- relative strength versus QQQ, SMH, sector ETF, or theme basket
- gap or drive extension versus ATR
- weak-quarter interaction, especially 2025Q1, 2025Q3, 2026Q1, and 2026Q2

### Live-Detectable Replacement Candidates

Future reducer logic should be built from live states such as:

- `opening_drive_exhaustion_state`
- `post_entry_relative_strength_fail`
- `volume_confirmation_decay`
- `near_high_rejection`
- `theme_confirmation_fail`
- `early_adverse_excursion_trigger`

These can be measured before or shortly after entry. The existing `entry_reduce_failure_flag` cannot.

## No-Background Decision-Maker Report

- What happened: entry-reduce looked like the biggest failure source, but the deeper issue is that it is currently a result label, not a live trading rule.
- Why it matters: we cannot improve the strategy by tuning a label. We need a real detector that catches bad entries before the full loss is known.
- Whether this changes capital/deployment readiness: no. Strategy remains NOT_ACCEPTED and DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Plain-language next step: build the early warning system first, then test whether reducing or exiting early improves OOS results.

## Artifact Manifest

- See `artifact_manifest.csv`.
