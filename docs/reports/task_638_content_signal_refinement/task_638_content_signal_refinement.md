# Task638 Content Signal Refinement

## Decision Summary

- Verdict: `PASS_RETURN_IMPROVEMENT_FAILS_SAME_RULE_VALIDATION_NOT_ACCEPTED`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Highest-return 50bp: `refined_best_combo` / `immediate` / `hold10` / `dynamic_10_20_30` = $6660.26 with -53.67% max drawdown
- Risk-controlled 50bp: `refined_best_combo` / `immediate` / `hold10` / `equal_max5` = $5618.37 with -30.04% max drawdown
- Risk-controlled improvement vs Task637: $470.07

## Quant Expert Report

This task tests five refinement axes: negative-event subtypes, positive catalyst strength, dynamic sizing, entry timing, and exit/holding-period variants.

### Source Audit

- Entries: 5265
- Entry period: 2024-01-02 to 2026-06-03
- Execution variant rows: 189102

### Top 50bp Account Candidates

| Universe | Timing | Exit | Sizing | Final $ | Accepted | DD |
|---|---|---|---|---:|---:|---:|
| `refined_best_combo` | `immediate` | `hold10` | `dynamic_10_20_30` | $6660.26 | 248 | -53.67% |
| `refined_best_combo` | `vwap_reclaim` | `hold10` | `dynamic_10_20_30` | $6660.26 | 248 | -53.67% |
| `refined_best_combo` | `delay15m` | `hold10` | `dynamic_10_20_30` | $6354.41 | 248 | -54.09% |
| `refined_best_combo` | `delay30m` | `hold10` | `dynamic_10_20_30` | $6116.76 | 248 | -54.24% |
| `positive_backlog_order` | `immediate` | `existing_exit` | `dynamic_10_20_40` | $5939.81 | 57 | -47.40% |
| `positive_high_quality` | `vwap_reclaim` | `existing_exit` | `dynamic_10_20_40` | $5939.81 | 57 | -47.40% |
| `positive_high_quality` | `immediate` | `existing_exit` | `dynamic_10_20_40` | $5939.81 | 57 | -47.40% |
| `positive_backlog_order` | `vwap_reclaim` | `existing_exit` | `dynamic_10_20_40` | $5939.81 | 57 | -47.40% |
| `positive_backlog_order` | `delay15m` | `existing_exit` | `dynamic_10_20_40` | $5771.84 | 57 | -47.64% |
| `positive_high_quality` | `delay15m` | `existing_exit` | `dynamic_10_20_40` | $5771.84 | 57 | -47.64% |
| `refined_best_combo` | `delay60m` | `hold10` | `dynamic_10_20_30` | $5731.42 | 248 | -54.38% |
| `positive_high_quality` | `delay30m` | `existing_exit` | `dynamic_10_20_40` | $5680.96 | 57 | -47.70% |

### OOS Account Candidates

| Split | Universe | Timing | Exit | Sizing | Final $ | QQQ $ |
|---|---|---|---|---|---:|---:|
| `recent_oos` | `content_guidance_margin` | `delay15m` | `hold5` | `dynamic_10_20_40` | $1647.33 | $1140.89 |
| `recent_oos` | `content_guidance_margin` | `delay60m` | `hold5` | `dynamic_10_20_40` | $1639.31 | $1140.89 |
| `recent_oos` | `content_guidance_margin` | `delay30m` | `hold5` | `dynamic_10_20_40` | $1630.67 | $1140.89 |
| `recent_oos` | `content_guidance_margin` | `delay15m` | `hold5` | `equal_max5` | $1628.22 | $1140.89 |
| `recent_oos` | `content_guidance_margin` | `immediate` | `hold5` | `dynamic_10_20_40` | $1617.68 | $1140.89 |
| `validation` | `negative_insider_sell` | `delay1d` | `hold20` | `dynamic_10_20_40` | $1481.53 | $1020.64 |
| `validation` | `negative_insider_sell` | `delay30m` | `hold20` | `dynamic_10_20_40` | $1459.94 | $1020.64 |
| `validation` | `negative_insider_sell` | `delay15m` | `hold20` | `dynamic_10_20_40` | $1459.28 | $1020.64 |
| `validation` | `negative_insider_sell` | `immediate` | `hold20` | `dynamic_10_20_40` | $1456.13 | $1020.64 |
| `validation` | `negative_insider_sell` | `vwap_reclaim` | `hold20` | `dynamic_10_20_40` | $1456.13 | $1020.64 |

### Refined Feature Stability

| Feature | Stable | Validation Lift | Recent Lift |
|---|---:|---:|---:|
| `content_guidance_margin` | 1 | 2.53 | 1.76 |
| `content_negative_score` | 1 | 0.25 | 1.55 |
| `content_supply_demand` | 1 | 1.34 | 2.46 |
| `negative_ceo_ir_disappointment` | 0 | nan | nan |
| `negative_core_reversal` | 0 | 1.89 | -1.82 |
| `negative_dilution_financing` | 0 | -9.61 | -7.29 |
| `negative_earnings_margin_damage` | 0 | -18.90 | nan |
| `negative_insider_sell` | 0 | -19.86 | -29.90 |
| `negative_regulation_sanction_tariff` | 0 | 2.67 | -1.22 |
| `positive_backlog_order` | 0 | 0.26 | -3.07 |
| `positive_contract_customer` | 0 | -4.37 | 2.63 |
| `positive_guidance_up` | 0 | -5.71 | nan |
| `positive_high_quality` | 0 | -0.45 | -3.07 |
| `positive_margin_supply_combo` | 0 | -4.51 | 5.45 |
| `refined_best_combo` | 0 | 1.72 | -2.91 |

## No-Background Decision-Maker Report

- We split bad-news and good-news content into smaller buckets.
- We tested bigger size only when the interpreted signal was stronger.
- We tested delayed entry, VWAP reclaim entry, and alternate exits.
- Best refinement improves the prior Task637 account result, but trading remains blocked until live-readable rules are locked.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `all_five_refinement_axes_tested` | 1 | timing=6; exits=6; sizing=3 | negative split positive split dynamic sizing timing and exit axes must be tested |
| `best_50bp_beats_task637` | 1 | best638=$6660.26; task637=$5148.31 | refinement should improve prior Task637 best result |
| `risk_controlled_50bp_beats_task637` | 1 | risk_best=$5618.37; dd=-30.04%; task637=$5148.31 | risk-controlled refinement should beat Task637 with max drawdown no worse than -35% |
| `best_50bp_beats_task617_max5` | 1 | best638=$6660.26; task617_max5=$3248.89 | refined candidate must beat existing Task617 max5 |
| `best_100bp_beats_task617_max5` | 1 | risk100=$5341.74; task617_max5=$3248.89 | refined candidate should survive 100bp cost stress |
| `same_rule_validation_oos_beats_qqq` | 0 | same_rule_validation=$863.73; qqq=$1020.64 | same risk-controlled full-period rule should beat validation QQQ |
| `same_rule_recent_oos_beats_qqq` | 1 | same_rule_recent=$1374.52; qqq=$1140.89 | same risk-controlled full-period rule should beat recent OOS QQQ |
| `best_oos_risk_controlled_accounts_beat_qqq` | 1 | validation_best=$1481.53; recent_best=$1628.22 | validation and recent OOS risk-controlled candidate accounts should beat same-period QQQ |
| `presence_fields_not_used` | 1 | presence fields not used | content interpretation only |
| `trading_promotion` | 0 | research candidate only | requires GPT review capture, live rule lock, latency/source readiness, and runtime paper shadow replay |

## Artifact Manifest

- `task_638_event_refinement_taxonomy.csv`
- `task_638_entry_refined_content_panel.csv`
- `task_638_refined_feature_audit.csv`
- `task_638_timing_exit_execution_panel.csv`
- `task_638_refinement_account_grid.csv`
- `task_638_refinement_oos_account_grid.csv`
- `task_638_source_audit.csv`
- `task_638_pass_fail_matrix.csv`
- `task_638_decision.csv`
- `task_638_gpt_review_packet.md`
- `task_638_gpt_capture_status.csv`
- `artifact_manifest.csv`
