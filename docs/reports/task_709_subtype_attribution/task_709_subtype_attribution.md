# Task709 Subtype Attribution

## Decision Summary

- Verdict: SUBTYPE_ATTRIBUTION_COMPLETE_DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- What changed: Subtype performance and MDD exposure are evaluated after freeze, but no rule is changed from this diagnostic.
- Next action: Use attribution to design audited rule candidates only after winner preservation review..

## Quant Expert Report

- Data source and source readiness: current Task636/672/684/689/703/704 artifacts only.
- Exact join keys: `lifecycle_id`, `symbol`, `theme_id`, `entry_ts`, `split_name` where applicable.
- Leakage audit: outcome/future-price assignment flags are kept at zero before evaluation.
- Split/OOS metrics: included where PnL is evaluated; otherwise not applicable.
- Failure decomposition: see CSV artifacts in this directory.
- Cost/slippage stress where PnL changed: included for Task708; otherwise not applicable.
- Remaining blockers: strategy remains NOT_ACCEPTED and real capital remains FORBIDDEN.

## No-Background Decision-Maker Report

- What happened: Subtype performance and MDD exposure are evaluated after freeze, but no rule is changed from this diagnostic.
- Why it matters: the project separates source risk, context, action tiers, evaluation, and governance instead of fixing rules after seeing returns.
- Whether this changes capital/deployment readiness: no.
- Plain-language next step: inspect the diagnostics before changing thresholds.

## Artifact Manifest

- Inputs: upstream governed task artifacts.
- Outputs: task709_subtype_performance.csv, task709_mdd_subtype_exposure.csv, task709_winner_loser_examples.csv, task_709_decision.csv, task_709_pass_fail_matrix.csv.
- Row counts: task709_subtype_performance.csv=19; task709_mdd_subtype_exposure.csv=12; task709_winner_loser_examples.csv=100; task_709_decision.csv=1; task_709_pass_fail_matrix.csv=4.
- Validation commands: see task registry.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| performance_rows_present | PRIMARY_PASS | 1 | rows=19 | >0 |
| mdd_exposure_present | PRIMARY_PASS | 1 | rows=12 | >0 |
| examples_present | PRIMARY_PASS | 1 | rows=100 | >0 |
| diagnostic_only | PRIMARY_PASS | 1 | no rule mutation | diagnostic only |
