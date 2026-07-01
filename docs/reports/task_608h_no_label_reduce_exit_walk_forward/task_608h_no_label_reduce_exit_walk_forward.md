# Task608H No-Label Reduce/Exit Walk-Forward

## Decision Summary

- Verdict: FAIL_NO_LABEL_REDUCE_SIM_DID_NOT_IMPROVE_WITH_COST
- Strategy acceptance status: NOT_ACCEPTED
- Deployment status: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
- Best 50bp scenario: top1_reduce_50_cost50bp
- Best 50bp delta avg net: -1.76 pct points.
- Best 50bp entry-reduce delta: 0.00%.
- What changed: state/path candidates are now applied fold-forward without using test labels.
- Next action: Do not refine this reducer yet; investigate why fold-forward candidates mostly hit clean trades and add stronger live features.

## Quant Expert Report

- Data source and source readiness: Task509 OOS rows plus Task608G live path features.
- Exact join keys: existing `lifecycle_id` only; no symbol/date/price/time lifecycle fallback.
- Leakage audit: candidates are selected from prior quarters and applied to the next quarter. Test-quarter labels are not used for assignment.
- Split/OOS metrics: fold-forward by quarter from Task509 rows.
- Failure decomposition: see `walk_forward_reduce_rule_selection.csv`, `walk_forward_reduce_simulation_panel.csv`, and `walk_forward_reduce_quality.csv`.
- Cost/slippage stress where PnL changed: scenarios include 0bp, 50bp, and 100bp extra reduce/exit costs.
- Remaining blockers: pass here is still not strategy acceptance; it only promotes a candidate family to rule-lock testing.

Baseline fold mean avg net: 15.55%
Baseline fold mean entry-reduce: 33.56%

Top scenarios:
- top1_reduce_50_cost0bp: delta avg -1.74 pct points, entry-reduce delta 0.00%, positive folds 83.33%, triggers 6
- top5_reduce_50_cost0bp: delta avg -2.05 pct points, entry-reduce delta 0.00%, positive folds 83.33%, triggers 14
- top3_reduce_50_cost0bp: delta avg -2.07 pct points, entry-reduce delta 0.00%, positive folds 83.33%, triggers 11
- top1_full_exit_cost0bp: delta avg -3.48 pct points, entry-reduce delta 0.00%, positive folds 83.33%, triggers 6
- top5_full_exit_cost0bp: delta avg -4.11 pct points, entry-reduce delta -3.57%, positive folds 83.33%, triggers 14
- top3_full_exit_cost0bp: delta avg -4.15 pct points, entry-reduce delta -1.19%, positive folds 83.33%, triggers 11
- top1_reduce_50_cost50bp: delta avg -1.76 pct points, entry-reduce delta 0.00%, positive folds 83.33%, triggers 6
- top5_reduce_50_cost50bp: delta avg -2.09 pct points, entry-reduce delta 0.00%, positive folds 83.33%, triggers 14

## No-Background Decision-Maker Report

- What happened: we tested whether early warning signs can improve the next quarter without looking at that quarter's labels.
- Why it matters: this is the first real check that entry-reduce can become a live rule instead of a hindsight label.
- Whether this changes capital/deployment readiness: no. It stays research only.
- Plain-language next step: only if this passes under cost, lock the rule family and stress it harder.

## Artifact Manifest

- See `artifact_manifest.csv`.
