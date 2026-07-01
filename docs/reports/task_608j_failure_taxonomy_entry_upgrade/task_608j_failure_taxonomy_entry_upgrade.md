# Task608J Failure Taxonomy And Entry Upgrade

## Decision Summary

- Verdict: FAIL_ENTRY_UPGRADE_NOT_FIRM_GRADE_YET
- Strategy acceptance status: NOT_ACCEPTED
- Deployment status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Taxonomy coverage: 62.86%
- Best delayed entry: delayed_entry_60m delta 0.17 pct points.
- Best staged entry: staged_25_25_50_0_30_60m delta 0.10 pct points.
- Best confirmation entry: confirmation_entry_15m delta -0.65 pct points.
- What changed: entry-reduce is now split into failure types, and entry alternatives are tested before reducer retry.
- Next action: Promote only positive entry-upgrade families to fold-forward OOS rule-lock testing with costs.

## Quant Expert Report

- Data source and source readiness: Task509 OOS rows, Task608G path panel, `data/raw/us_intraday`, and `data/raw/us_daily_breadth_top500`.
- Exact join keys: existing `lifecycle_id`; intraday/daily features use exact symbol and timestamp/date windows.
- Leakage audit: taxonomy uses outcomes for evaluation. Entry qualification uses pre-entry features; delayed/staged/confirmation tests use observable wait/confirmation paths and do not use labels for assignment.
- Split/OOS metrics: entry qualification is fold-forward by quarter. Delayed/staged/confirmation are diagnostic simulations and must be fold-forward rule-locked before acceptance.
- Failure decomposition: see `failure_taxonomy_panel.csv` and `failure_taxonomy_quality.csv`.
- Cost/slippage stress where PnL changed: not applied in Task608J; any promoted family must be cost-stressed next.
- Remaining blockers: positive diagnostic deltas are not deployment claims.
- GPT reviewer note: Chrome ChatGPT review agrees this remains `NOT_ACCEPTED`; see `gpt_review_notes.md`.

Failure taxonomy:
- opening_trap: count 15, share 42.86%, avg -17.84%
- unclassified_mixed_failure: count 13, share 37.14%, avg -14.99%
- gap_exhaustion_or_event_fade_proxy: count 5, share 14.29%, avg -16.41%
- late_breakout_exhaustion: count 1, share 2.86%, avg -20.59%
- sector_or_theme_rotation: count 1, share 2.86%, avg -10.42%

Entry qualification fold-forward leaders:
- 2025Q4 block_prior_day_extension_near_premarket_high: accepted avg 10.64%, blocked 5, clean false blocks 4
- 2025Q4 block_overextended_from_open: accepted avg 9.18%, blocked 1, clean false blocks 1
- 2025Q3 block_prior_day_extension_near_premarket_high: accepted avg 3.66%, blocked 0, clean false blocks 0
- 2025Q3 block_overextended_from_open: accepted avg 3.66%, blocked 0, clean false blocks 0
- 2026Q1 block_overextended_from_open: accepted avg 2.30%, blocked 1, clean false blocks 1

Delayed entry:
- delayed_entry_60m: avg 9.49%, delta 0.17 pct points, entry-reduce 40.45%
- delayed_entry_15m: avg 9.45%, delta 0.12 pct points, entry-reduce 40.45%
- delayed_entry_30m: avg 9.40%, delta 0.08 pct points, entry-reduce 40.45%
- baseline_entry: avg 9.32%, delta 0.00 pct points, entry-reduce 39.33%

Staged entry:
- staged_25_25_50_0_30_60m: avg 9.42%, delta 0.10 pct points, entry-reduce 40.45%
- staged_50_50_0_60m: avg 9.40%, delta 0.08 pct points, entry-reduce 40.45%
- staged_33_33_33_0_30_60m: avg 9.40%, delta 0.07 pct points, entry-reduce 40.45%

Continuation confirmation:
- confirmation_entry_15m: avg 5.74%, delta -0.65 pct points, entry-reduce 44.44%
- confirmation_entry_30m: avg 4.79%, delta -0.96 pct points, entry-reduce 46.15%
- confirmation_entry_60m: avg 8.01%, delta -1.19 pct points, entry-reduce 41.46%

## No-Background Decision-Maker Report

- What happened: we stopped treating all losses as one blob and tested entry alternatives before trying another reducer.
- Why it matters: if delayed or staged entry works better, the problem is entry timing/qualification rather than reduce-after-entry.
- Whether this changes capital/deployment readiness: no. It remains research only.
- Plain-language next step: take only the best positive family and run a stricter fold-forward cost test.

## Artifact Manifest

- See `artifact_manifest.csv`.
