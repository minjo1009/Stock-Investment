# Task608L Early Adverse False Positive Decomposition

## Decision Summary

- Verdict: PASS_EARLY_ADVERSE_CLASSIFIER_CANDIDATE_NEEDS_RULE_LOCK
- Strategy acceptance status: NOT_ACCEPTED
- Deployment status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Rule-lock status: NOT_READY
- Reducer retry: CLOSED
- Baseline wait15 trigger: 13, failure 6, clean false 7, failure rate 46.15%.
- Best interaction: early_adverse__no_mfe_recovery_and_volume_decay, trigger 3, failure rate 66.67%, clean false 1.
- Best interaction fold evidence: positive folds 1, test triggers 1.
- Next action: If early-adverse interactions do not hold under stricter fold-forward, stop this branch and move late follow-through to exit/trailing review.

## Quant Expert Report

- Data source and source readiness: Task608K feature panel and taxonomy v2.
- Exact join keys: `lifecycle_id` only.
- Leakage audit: labels are used to evaluate true failure versus clean false, not to assign candidate flags.
- Split/OOS metrics: fold-forward interaction validation is included, but sample is small and not deployable.
- Failure decomposition: wait15 early adverse has 6 failures and 7 clean false rows.
- Cost/slippage stress where PnL changed: not applicable; no treatment is promoted.
- Remaining blockers: fold-forward stability and winner-destruction control.

True-vs-clean strongest differences:
- qqq_rs_decay_30m_flag: true-clean diff -0.1190
- persistent_vwap_fail_30_60m_flag: true-clean diff -0.0952
- opening_range_reclaim_fail_flag: true-clean diff -0.0952
- volume_decay_flag: true-clean diff 0.0952
- qqq_rs_decay_120m_flag: true-clean diff 0.0714

Interaction candidates:
- early_adverse__rs_decay_120m_and_volume_decay: trigger 4, fail 3, clean 1, fail rate 75.00%
- early_adverse__no_mfe_recovery_and_volume_decay: trigger 3, fail 2, clean 1, fail rate 66.67%
- early_adverse__persistent_vwap_fail_and_reclaim_fail: trigger 3, fail 2, clean 1, fail rate 66.67%
- early_adverse__volume_decay: trigger 8, fail 4, clean 4, fail rate 50.00%
- early_adverse__vwap_fail_and_no_mfe_recovery: trigger 4, fail 2, clean 2, fail rate 50.00%

Fold-forward summary:
- early_adverse__no_mfe_recovery_and_volume_decay: folds 2, test trigger 1, fail 1, clean 0, positive 1
- early_adverse__persistent_vwap_fail_and_reclaim_fail: folds 2, test trigger 1, fail 1, clean 0, positive 1
- early_adverse__vwap_fail_and_no_mfe_recovery: folds 2, test trigger 1, fail 1, clean 0, positive 1
- early_adverse__persistent_vwap_fail_30_60m: folds 2, test trigger 2, fail 1, clean 1, positive 1
- early_adverse__no_mfe_recovery_30m: folds 3, test trigger 3, fail 1, clean 2, positive 1

## No-Background Decision-Maker Report

- What happened: the early adverse bucket was split into true failures and clean false rows.
- Why it matters: the best interaction looks better in-sample, but fold-forward evidence is still too thin.
- Whether this changes capital/deployment readiness: no.
- Plain-language next step: do not lock the rule yet; either tighten and retest or stop this branch.

## Artifact Manifest

- See `artifact_manifest.csv`.
