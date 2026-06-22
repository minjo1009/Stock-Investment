# Task1338-1357 Full Candidate Replacement Replay

## Decision Summary

- Verdict: `full_candidate_replacement_replay_executed_not_accepted`.
- Best policy: `full_candidate_l2l3_replace_top10_v1`.
- Best final equity: 1783.7653.
- Best CAGR: 0.118667.
- Best MDD: -0.290278.
- Strategy acceptance status: `NOT_ACCEPTED`.
- What changed: full-candidate L2/L3 source judgment now selects top 3/5/10 replacement portfolios inside each monthly cohort.
- Next action: diagnose replacement winners/losers before changing thresholds or adding dynamic exits.

## Quant Expert Report

Data source and readiness:

- Inputs are Task1318-1337 full-candidate source extractor outputs and Task1201 trade specs/price gates.
- Selection uses only same-month candidate cohort rows.
- No future PnL, realized return, exit price, or outcome labels are used for assignment.

Exact join keys:

- `candidate_source_id`
- `trade_spec_id`
- `decision_asof_ts`
- `symbol`

Policy metrics:

| Policy | Final | CAGR | MDD | Beats Slot Baseline | Beats QQQ | CAGR 30 | MDD -30 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `full_candidate_l2l3_replace_top10_v1` | 1783.7653 | 0.118667 | -0.290278 | 1 | 0 | 0 | 1 |
| `full_candidate_l2l3_replace_top3_v1` | 1578.7753 | 0.092516 | -0.426093 | 0 | 0 | 0 | 0 |
| `full_candidate_l2l3_replace_top5_v1` | 1505.6664 | 0.082525 | -0.388075 | 0 | 0 | 0 | 0 |

Leakage audit:

- L4 replacement scores use L2 composite interpretation, L1 source states, L3 evidence-edge counts, readiness state, and original candidate rank.
- L5 replay uses entry and exit prices only after selection.
- `assignment_uses_future_outcome` remains 0 in ranking and policy specs.

Remaining blockers:

- Analyst PIT source remains absent.
- Policy/news affected-entity extraction remains incomplete for all candidates.
- Dynamic exit and post-entry source receipt are not implemented in this replay.

## No-Background Decision-Maker Report

This is the first replay where the brain can actually replace weak candidates with stronger candidates from the same month.

It is still diagnostic.

The target was CAGR 30%+ and MDD around -30%.

## Artifact Manifest

- `task1338_policy_catalog.csv`
- `task1339_l4_replacement_rank_panel.csv`
- `task1340_l5_replacement_policy_specs.csv`
- `task1341_replay_trades.csv`
- `task1342_replay_equity.csv`
- `task1343_replay_metrics.csv`
- `task1344_interpretation_attribution.csv`
- `task1345_replacement_audit.csv`
- `task1346_acceptance_gate.csv`
- `task1357_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1338_1357_full_candidate_replacement_replay_validate.py`
- `python -m unittest tests.test_trader_brain_1338_1357_full_candidate_replacement_replay`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
