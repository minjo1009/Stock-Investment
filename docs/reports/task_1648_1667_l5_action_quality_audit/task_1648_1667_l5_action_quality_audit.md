# Task1648-1667 L5 Action Quality Audit

## Decision Summary

- Verdict: `l5_action_quality_audit_implemented_not_accepted`.
- Best policy: `aq_combo_top3_v1`.
- Best final equity: 2485.1764.
- Best CAGR: 0.192908.
- Best MDD: -0.279259.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Quant Expert Report

Action quality scorecard:

| Policy | Action | Count | Precision | Avg Delta | Total Delta | Verdict |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| `l5_operating_top3_v1` | exit | 15 | 0.4 | -0.01979062 | -0.296859 | weak |
| `l5_operating_top3_v1` | hold | 82 | 0.743902 | 0.01442495 | 1.182846 | pass |
| `l5_operating_top3_v1` | no_reentry | 5 | 0.6 | -0.02048482 | -0.102424 | weak |
| `l5_operating_top3_v1` | reduce | 51 | 0.372549 | -0.0205843 | -1.049799 | weak |
| `l5_operating_top3_v1` | rerisk | 8 | 0.75 | -2.6506375 | -21.2051 | weak |
| `l5_operating_top5_v1` | exit | 17 | 0.352941 | -0.02492442 | -0.423715 | weak |
| `l5_operating_top5_v1` | hold | 109 | 0.715596 | 0.01146868 | 1.250086 | pass |
| `l5_operating_top5_v1` | no_reentry | 8 | 0.625 | -0.01986992 | -0.158959 | weak |
| `l5_operating_top5_v1` | reduce | 58 | 0.413793 | -0.01856844 | -1.07697 | weak |
| `l5_operating_top5_v1` | rerisk | 8 | 0.75 | -1.0007875 | -8.0063 | weak |

Replay metrics:

| Policy | Final | CAGR | MDD | Trades | Hold | Reduce | Exit | QQQ Beat | CAGR Target | MDD Target |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `aq_baseline_damage_top3_v1` | 2435.7835 | 0.188277 | -0.261782 | 148 | 82 | 51 | 15 | 1 | 0 | 1 |
| `aq_baseline_damage_top5_v1` | 1947.325 | 0.137846 | -0.231211 | 184 | 109 | 58 | 17 | 1 | 0 | 1 |
| `aq_combo_top3_v1` | 2485.1764 | 0.192908 | -0.279259 | 148 | 82 | 66 | 0 | 1 | 0 | 1 |
| `aq_combo_top5_v1` | 1945.4291 | 0.137631 | -0.249096 | 184 | 109 | 75 | 0 | 1 | 0 | 1 |
| `aq_reduce_guard_top3_v1` | 2485.1764 | 0.192908 | -0.279259 | 148 | 82 | 51 | 15 | 1 | 0 | 1 |
| `aq_reduce_guard_top5_v1` | 1945.4291 | 0.137631 | -0.249096 | 184 | 109 | 58 | 17 | 1 | 0 | 1 |
| `aq_source_demote_top3_v1` | 2435.7835 | 0.188277 | -0.261782 | 148 | 82 | 66 | 0 | 1 | 0 | 1 |
| `aq_source_demote_top5_v1` | 1947.325 | 0.137846 | -0.231211 | 184 | 109 | 75 | 0 | 1 | 0 | 1 |

Split/OOS diagnostics:

| Policy | Window | Final | Return | MDD |
| --- | --- | ---: | ---: | ---: |
| `aq_baseline_damage_top3_v1` | IS_2021_2023 | 1585.433 | 0.585433 | -0.261782 |
| `aq_baseline_damage_top3_v1` | OOS_2024_2026Q1 | 2435.7835 | 1.435783 | -0.137709 |
| `aq_baseline_damage_top5_v1` | IS_2021_2023 | 1322.6695 | 0.322669 | -0.231211 |
| `aq_baseline_damage_top5_v1` | OOS_2024_2026Q1 | 1947.325 | 0.947325 | -0.083789 |
| `aq_combo_top3_v1` | IS_2021_2023 | 1550.9355 | 0.550936 | -0.279259 |
| `aq_combo_top3_v1` | OOS_2024_2026Q1 | 2485.1764 | 1.485176 | -0.143808 |
| `aq_combo_top5_v1` | IS_2021_2023 | 1288.7538 | 0.288754 | -0.249096 |
| `aq_combo_top5_v1` | OOS_2024_2026Q1 | 1945.4291 | 0.945429 | -0.087611 |
| `aq_reduce_guard_top3_v1` | IS_2021_2023 | 1550.9355 | 0.550936 | -0.279259 |
| `aq_reduce_guard_top3_v1` | OOS_2024_2026Q1 | 2485.1764 | 1.485176 | -0.143808 |
| `aq_reduce_guard_top5_v1` | IS_2021_2023 | 1288.7538 | 0.288754 | -0.249096 |
| `aq_reduce_guard_top5_v1` | OOS_2024_2026Q1 | 1945.4291 | 0.945429 | -0.087611 |
| `aq_source_demote_top3_v1` | IS_2021_2023 | 1585.433 | 0.585433 | -0.261782 |
| `aq_source_demote_top3_v1` | OOS_2024_2026Q1 | 2435.7835 | 1.435783 | -0.137709 |
| `aq_source_demote_top5_v1` | IS_2021_2023 | 1322.6695 | 0.322669 | -0.231211 |
| `aq_source_demote_top5_v1` | OOS_2024_2026Q1 | 1947.325 | 0.947325 | -0.083789 |

## No-Background Decision-Maker Report

1. L5 actions were separated into hold, reduce, exit, no-reentry, and rerisk.
2. Each action was scored against a counterfactual before combined replay.
3. Reduce and rerisk are the weak actions; hold remains the useful action.
4. The action-quality replay did not solve the 30pct CAGR and minus30pct MDD target together.
5. The next fix is action precision, not another broad CAGR/MDD toggle.

## Failure / Blocker Summary

- `weak_action_precision`: policy=l5_operating_top3_v1 action=exit precision=0.4 cagr= mdd=
- `weak_action_precision`: policy=l5_operating_top3_v1 action=no_reentry precision=0.6 cagr= mdd=
- `weak_action_precision`: policy=l5_operating_top3_v1 action=reduce precision=0.372549 cagr= mdd=
- `weak_action_precision`: policy=l5_operating_top3_v1 action=rerisk precision=0.75 cagr= mdd=
- `weak_action_precision`: policy=l5_operating_top5_v1 action=exit precision=0.352941 cagr= mdd=
- `weak_action_precision`: policy=l5_operating_top5_v1 action=no_reentry precision=0.625 cagr= mdd=
- `weak_action_precision`: policy=l5_operating_top5_v1 action=reduce precision=0.413793 cagr= mdd=
- `weak_action_precision`: policy=l5_operating_top5_v1 action=rerisk precision=0.75 cagr= mdd=
- `target_failure`: policy=aq_baseline_damage_top3_v1 action= precision= cagr=0.188277 mdd=-0.261782
- `target_failure`: policy=aq_baseline_damage_top5_v1 action= precision= cagr=0.137846 mdd=-0.231211
- `target_failure`: policy=aq_combo_top3_v1 action= precision= cagr=0.192908 mdd=-0.279259
- `target_failure`: policy=aq_combo_top5_v1 action= precision= cagr=0.137631 mdd=-0.249096
- `target_failure`: policy=aq_reduce_guard_top3_v1 action= precision= cagr=0.192908 mdd=-0.279259
- `target_failure`: policy=aq_reduce_guard_top5_v1 action= precision= cagr=0.137631 mdd=-0.249096
- `target_failure`: policy=aq_source_demote_top3_v1 action= precision= cagr=0.188277 mdd=-0.261782
- `target_failure`: policy=aq_source_demote_top5_v1 action= precision= cagr=0.137846 mdd=-0.231211

## Artifact Manifest

- `task1648_expert_review.csv`
- `task1649_action_contract.csv`
- `task1650_action_ledger.csv`
- `task1651_action_scorecard.csv`
- `task1652_action_rulebook.csv`
- `task1653_action_rule_revisions.csv`
- `task1654_action_quality_replay_trades.csv/equity`
- `task1655_action_quality_replay_metrics.csv`
- `task1656_split_oos_metrics.csv`
- `task1657_failure_attribution.csv`
- `task1666_acceptance_gate.csv`
- `task1667_closeout.csv/json`

Validation commands:

- `python scripts/trader_brain_1648_1667_l5_action_quality_audit_validate.py`

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```