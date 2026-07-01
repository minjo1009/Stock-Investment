# Task608I GPT Entry-Reduce Firm-Grade Upgrade Discussion

## Decision Summary

- Verdict: REFRAME_REDUCER_TO_FAILURE_TAXONOMY_AND_ENTRY_QUALIFICATION
- Strategy acceptance status: NOT_ACCEPTED
- Deployment status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Key metrics: Task608H best 50bp fold-forward reducer was `top1_reduce_50_cost50bp`, with avg net delta -1.76 pct points and entry-reduce delta 0.00%.
- What changed: reducer refinement is downgraded. The next firm-grade path is failure taxonomy, entry qualification, delayed entry, staged entry, and continuation confirmation.
- Next action: build Task608J failure taxonomy before testing more reducer rules.

## Quant Expert Report

- Data source and source readiness: Task608DE, Task608F, Task608G, Task608H, and GPT review notes. GPT is review-only and not a source of truth.
- Exact join keys: no new matching was performed. This task consumes existing repo-native artifacts only.
- Leakage audit: current `entry_reduce_failure_flag` remains an outcome label and cannot enter assignment logic. Task608H candidate selection was fold-forward but failed.
- Split/OOS metrics: Task608H showed fold-forward reduce/exit candidates did not improve with 50bp extra cost.
- Failure decomposition: current failure population is probably not one failure class. The 35 entry-reduce failures should be split into mechanism-level clusters.
- Cost/slippage stress where PnL changed: Task608H tested 0bp, 50bp, and 100bp extra costs. Best 50bp scenario still reduced avg net by -1.76 pct points.
- Remaining blockers: no firm-grade live reducer exists. Existing path features are not sufficient to avoid clean false alarms.

## Entry-Reduce Team Discussion

### Why Task608H Failed

The diagnostic candidates were useful for explanation, but not stable enough for prediction.

- Some features are post-entry path features, so they explain deterioration after entry but do not prove a profitable live rule.
- Trigger sample size is too small. The best fold-forward candidate triggered only 6 trades.
- The failure class is likely mixed. `entry_reduce_failure` may include gap exhaustion, opening trap, news fade, late breakout, sector rotation, and symbol-specific failed leadership.
- The clean false alarm problem is severe. In Task608H, the top 50bp candidate triggered 6 trades and all 6 were clean false alarms.

### Missing Live Features

The next dataset should add features that explain why a clean-looking continuation setup is actually fragile:

- liquidity location: premarket high, premarket VWAP, overnight range, prior session high/low
- breakout quality: breakout age, bars since breakout, extension from first expansion, distance from opening range high
- relative positioning: sector ETF, theme basket, and leader relative strength, not only QQQ
- market participation: breadth thrust, advance/decline, new highs/new lows, intraday index confirmation
- prior-day context: prior-day range expansion, gap percentile, prior-day volume anomaly, close location

### Direction Change

Reducer remains research-only, but it should not be the next P1 path.

Priority should become:

1. Failure taxonomy
2. Entry qualification
3. Delayed entry
4. Staged entry
5. Continuation confirmation
6. Reducer retry

## No-Background Decision-Maker Report

- What happened: GPT and the entry-reduce review agreed that the current reducer path is not good enough.
- Why it matters: the model is cutting good trades when tested fairly. That means the problem is not solved by tuning reduce rules.
- Whether this changes capital/deployment readiness: no. Status remains NOT_ACCEPTED and DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Plain-language next step: first split the losing trades into different failure types, then build better entry-quality checks.

## Artifact Manifest

- See `artifact_manifest.csv`.
