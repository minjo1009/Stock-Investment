# Task608K Failure Taxonomy V2 Conditional Treatment

## Decision Summary

- Verdict: PASS_TAXONOMY_V2_DIAGNOSTIC_NEEDS_RULE_LOCK
- Strategy acceptance status: NOT_ACCEPTED
- Deployment status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Reducer retry: CLOSED
- Taxonomy coverage: 100.00%
- Live-actionable coverage: 80.00%
- Best risk rule: wait15_early_adverse_abort_candidate (46.15% failure rate).
- Rule-lock ready: 0
- Best treatment: opening_trap_fast_adverse with delayed_entry_60m improves failed-row return by 2.67pp.
- Next action: Rule-lock only the best wait-window risk candidates with fold-forward clean-false-trigger limits and cost stress.

## Quant Expert Report

- Data source and source readiness: Task608J feature panel plus Task608G path diagnostics.
- Exact join keys: `lifecycle_id` only.
- Leakage audit: taxonomy and treatment-by-failed-type use failure labels for diagnosis only. Risk-rule candidate summary uses live/pre-entry or wait-window signals and marks deployment false.
- Split/OOS metrics: not accepted yet; next step must fold-forward lock rules.
- Failure decomposition:
- late_followthrough_failure: 7개, 평균 -14.20%
- opening_trap_vwap_loss: 7개, 평균 -14.89%
- opening_trap_range_rejection: 6개, 평균 -18.59%
- failed_continuation_demand_decay: 5개, 평균 -13.19%
- early_adverse_failure: 4개, 평균 -21.27%
- opening_trap_fast_adverse: 3개, 평균 -22.15%
- market_or_theme_drag: 2개, 평균 -11.16%
- late_breakout_exhaustion: 1개, 평균 -20.59%
- Conditional treatment on failed rows:
- opening_trap_fast_adverse: best delayed_entry_60m, 개선 2.67pp
- market_or_theme_drag: best delayed_entry_60m, 개선 1.02pp
- opening_trap_vwap_loss: best delayed_entry_60m, 개선 0.74pp
- failed_continuation_demand_decay: best delayed_entry_60m, 개선 0.24pp
- early_adverse_failure: best delayed_entry_15m, 개선 0.24pp
- opening_trap_range_rejection: best delayed_entry_60m, 개선 0.14pp
- Live/wait-window risk candidates:
- wait15_early_adverse_abort_candidate: trigger 13개, 실패율 46.15%, clean false 7개
- wait30_relative_strength_decay_candidate: trigger 7개, 실패율 42.86%, clean false 4개
- wait60_failed_continuation_candidate: trigger 60개, 실패율 40.00%, clean false 36개
- preentry_theme_confirmation_fail_candidate: trigger 5개, 실패율 40.00%, clean false 3개
- preentry_gap_exhaustion_candidate: trigger 3개, 실패율 33.33%, clean false 2개
- Remaining blockers: clean false triggers, cost stress, and fold-forward rule lock are still missing.

## No-Background Decision-Maker Report

- What happened: the 35 failures are now split more clearly.
- Why it matters: reducer is still not the next move; wait-window risk rules are the better candidate.
- Whether this changes capital/deployment readiness: no.
- Plain-language next step: test the best wait-window rule without using labels and cap clean false triggers.

## Artifact Manifest

- See `artifact_manifest.csv`.
