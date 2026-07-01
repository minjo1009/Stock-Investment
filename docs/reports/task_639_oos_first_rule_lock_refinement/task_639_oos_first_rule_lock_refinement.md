# Task639 OOS-First Rule Lock Refinement

## Decision Summary

- Verdict: `PASS_SAME_RULE_RETURN_UP_DRAWDOWN_DOWN_CANDIDATE_NOT_ACCEPTED`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Best same-rule candidate: `positive_contract_or_supply` / `delay1d` / `existing_exit` / `equal_max5`
- $1000 final at 50bp: $7639.62
- Max drawdown: -23.76%
- Validation: $1069.23 vs QQQ $1049.91
- Recent OOS: $1531.90 vs QQQ $1124.19

## Quant Expert Report

Task639 follows GPT review guidance: reject full-period-only optimization, avoid regime switching, avoid new semantic scores, and search only among same-rule OOS pass candidates.

### Source Audit

- Candidate configs: 270
- Same-rule pass candidates: 21
- GPT review captured: 1

### Top Same-Rule Pass Candidates

| Rule | Timing | Exit | Sizing | Full $ | DD | Validation $ | Recent $ |
|---|---|---|---|---:|---:|---:|---:|
| `positive_contract_or_supply` | `delay1d` | `existing_exit` | `equal_max5` | $7639.62 | -23.76% | $1069.23 | $1531.90 |
| `same_rule_three_cluster_any` | `delay1d` | `existing_exit` | `equal_max5` | $5420.66 | -31.06% | $1240.47 | $1302.71 |
| `positive_contract_or_supply` | `delay15m` | `existing_exit` | `equal_max5` | $5110.74 | -30.64% | $1142.81 | $1438.45 |
| `positive_contract_or_supply` | `vwap_reclaim` | `existing_exit` | `equal_max5` | $5097.15 | -29.63% | $1153.60 | $1439.79 |
| `positive_contract_or_supply` | `immediate` | `existing_exit` | `equal_max5` | $5097.15 | -29.63% | $1153.60 | $1439.79 |
| `positive_contract_or_supply` | `delay30m` | `existing_exit` | `equal_max5` | $5059.56 | -31.07% | $1134.11 | $1435.43 |
| `positive_contract_or_supply` | `delay60m` | `existing_exit` | `equal_max5` | $4945.62 | -32.39% | $1129.00 | $1437.06 |
| `positive_contract_customer` | `vwap_reclaim` | `existing_exit` | `equal_max5` | $3900.51 | -19.26% | $1133.35 | $1439.79 |
| `positive_contract_customer` | `immediate` | `existing_exit` | `equal_max5` | $3900.51 | -19.26% | $1133.35 | $1439.79 |
| `positive_contract_customer` | `delay15m` | `existing_exit` | `equal_max5` | $3873.37 | -18.82% | $1129.07 | $1438.45 |
| `positive_contract_customer` | `delay30m` | `existing_exit` | `equal_max5` | $3834.85 | -18.31% | $1129.05 | $1435.43 |
| `positive_contract_customer` | `delay60m` | `existing_exit` | `equal_max5` | $3735.83 | -18.53% | $1121.66 | $1437.06 |

## No-Background Decision-Maker Report

- We found a better version: more return than Task637/638, and much less drawdown than Task638 high-return.
- The best rule is simple: positive contract/customer OR supply/demand, enter next day, use existing exit, equal max5.
- It passes validation and recent OOS with the same locked rule.
- It is still not approved for real trading until live source timing and paper-shadow replay pass.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `gpt_review_captured` | 1 | captured=1 | GPT review must be captured as review-only artifact |
| `same_rule_oos_pass_candidates_found` | 1 | pass_candidates=21 | at least one same-rule candidate must beat validation and recent OOS QQQ |
| `best_same_rule_beats_task637` | 1 | best=$7639.62; task637=$5148.31 | best same-rule candidate should beat Task637 full-period result |
| `best_same_rule_beats_task638_high_return` | 1 | best=$7639.62; task638_high=$6660.26 | best same-rule candidate should beat Task638 highest-return result |
| `drawdown_better_than_task638_high_return` | 1 | best_dd=-23.76%; task638_high_dd=-53.67% | best same-rule candidate should reduce the Task638 high-return drawdown |
| `drawdown_better_than_task638_risk_controlled` | 1 | best_dd=-23.76%; task638_risk_dd=-30.04% | best same-rule candidate should reduce the Task638 risk-controlled drawdown |
| `same_rule_validation_beats_qqq` | 1 | validation=$1069.23; qqq=$1049.91 | same rule must beat validation QQQ |
| `same_rule_recent_beats_qqq` | 1 | recent=$1531.90; qqq=$1124.19 | same rule must beat recent OOS QQQ |
| `no_new_semantic_or_regime_switch` | 1 | new semantic score=0; regime switch=0 | Task639 must only refine previously validated same-rule candidates |
| `trading_promotion` | 0 | research candidate only | requires live-readable rule lock, source latency audit, and paper-shadow replay |

## Artifact Manifest

- `task_639_oos_first_candidate_grid.csv`
- `task_639_same_rule_pass_candidates.csv`
- `task_639_source_audit.csv`
- `task_639_pass_fail_matrix.csv`
- `task_639_decision.csv`
- `artifact_manifest.csv`