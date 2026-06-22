# Task608D/E Failure Regime And Entry-Reduce Attribution

## Decision Summary

- Verdict: FAIL_FAILURE_ENTRY_REDUCE_NOT_FIRM_GRADE
- Task608D: PASS_FAILURE_REGIME_MAP_IDENTIFIED_NOT_RESOLVED
- Task608E: FAIL_ENTRY_REDUCE_FAILURE_MATERIAL
- Baseline OOS: count 89, avg 9.32%, win 56.18%, entry-reduce 39.33%.
- Clean entries: count 54, avg 26.03%, win 92.59%.
- Entry-reduce failed entries: count 35, avg -16.45%, win 0.00%.
- Worst quarter: 2025Q1 avg -13.51%, entry-reduce 75.00%.
- Largest entry-reduce drag quarter: 2025Q1 drag -22.24 pct points.
- What changed: the break is now attributed to entry-reduce failure concentration, not theme/symbol/parameter dependency alone.
- Next action: Task608F should test entry-reduce suppression, separated clean-entry policy, and OOS capital impact.

## Quant Expert Report

- Data source and source readiness: Task509 walk-forward OOS assignment panel only; no new raw market source or live broker source was introduced.
- Exact join keys: existing `lifecycle_id` rows are used as-is; no inferred lifecycle matching, symbol/date/price/time fallback, or label repair was used.
- Leakage audit: labels/outcomes are evaluation-only. No outcome field enters assignment or filtering logic in this diagnostic.
- Split/OOS metrics: all rows are Task509 walk-forward OOS assignment rows.
- Failure decomposition: `quarter_failure_map.csv` marks hard-break and weak quarters. `entry_reduce_by_quarter.csv` measures clean versus failed-entry drag by quarter.
- Cost/slippage stress: unchanged from Task508/Task608; this task isolates OOS failure attribution only.
- Remaining blockers: entry-reduce failure is material and must be suppressed, isolated, or rejected before strategy acceptance can change.

Top weak-quarter state rows:
- timing_state=opening_drive: count 38, entry-reduce failed 20, avg -2.86%
- symbol_multiday_setup_state=trend_persistence_near_high: count 35, entry-reduce failed 14, avg 2.39%
- theme_id=aerospace_defense_space: count 24, entry-reduce failed 13, avg -4.44%
- theme_regime_state_v4=persistent_theme_leader: count 24, entry-reduce failed 12, avg -0.93%
- theme_regime_state_v4=theme_participation: count 25, entry-reduce failed 12, avg 0.25%
- symbol_multiday_setup_state=volume_confirmed_reclaim: count 11, entry-reduce failed 9, avg -14.08%

## No-Background Decision-Maker Report

- What happened: the strategy mostly breaks when failed entries become common.
- Why it matters: good entries still made money, but failed entries were large enough to pull full quarters down.
- Whether this changes capital/deployment readiness: no. Status remains NOT_ACCEPTED and DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Plain-language next step: test a version that blocks or separates entry-reduce situations, then rerun OOS capital metrics.

## Artifact Manifest

- See `artifact_manifest.csv`.
