# Task649 Macro Context State Engine

## Decision Summary

- Verdict: `MACRO_SOURCES_ATTACHED_PROVISIONAL_STATE_ENGINE_NOT_PROMOTED`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- FRED macro series were attached to Task648 entries with conservative as-of lag.
- This is still provisional because latest-vintage values and exact release timestamp gaps remain.
- Chrome ChatGPT was used only as external design review, not as a data source.

## Quant Expert Report

Task649 adds employment, inflation, Fed/rates, dollar, oil, credit, and liquidity context to the trading context state engine.

The first-stage as-of rule is conservative:

- daily series: observation date + 1 day
- weekly series: observation date + 7 days
- monthly series: observation date + 45 days

This reduces obvious timing leakage but does not solve latest-vintage revision leakage. Promotion remains blocked.

### Macro Context Evaluation

| split_name | augmented_trading_context_state | augmented_action_bucket_diagnostic | entry_count | avg_net_return_pct | win_rate | entry_reduce_failure_rate |
| --- | --- | --- | --- | --- | --- | --- |
| recent_oos | source_gap_macro_mixed | NO_ACTION_SOURCE_GAP | 23 | -0.006406 | 0.391304 | 0.565217 |
| recent_oos | mixed_alignment_macro_mixed | NO_ACTION_CONTEXT_WEAK | 17 | 0.10428 | 0.411765 | 0.529412 |
| recent_oos | mixed_alignment_macro_mixed | NORMAL_ENTRY | 15 | -0.035354 | 0.2 | 0.666667 |
| recent_oos | mixed_alignment_macro_mixed | CONFIRMATION_REQUIRED | 11 | 0.049212 | 0.454545 | 0.454545 |
| recent_oos | mixed_alignment_macro_supportive | NORMAL_ENTRY | 10 | 0.157622 | 0.4 | 0.6 |
| recent_oos | source_gap_company_or_policy_missing_macro_supportive | NO_ACTION_SOURCE_GAP | 8 | 0.00975 | 0.375 | 0.5 |
| recent_oos | conflicted_alignment_macro_mixed | CONFIRMATION_REQUIRED | 7 | -0.182096 | 0.0 | 1.0 |
| recent_oos | conflicted_alignment_macro_mixed | SIZE_DOWN | 4 | -0.208206 | 0.0 | 1.0 |
| recent_oos | mixed_alignment_macro_supportive | CONFIRMATION_REQUIRED | 4 | 0.36734 | 1.0 | 0.0 |
| recent_oos | mixed_alignment_macro_mixed | SIZE_DOWN | 2 | -0.180377 | 0.0 | 1.0 |
| recent_oos | mixed_alignment_macro_supportive | DELAY_ENTRY | 2 | -0.050832 | 0.0 | 1.0 |
| recent_oos | mixed_alignment_macro_supportive | SIZE_DOWN | 2 | -0.108602 | 0.0 | 1.0 |
| recent_oos | supportive_alignment_macro_confirmed | FULL_ENTRY_CANDIDATE | 2 | 0.290749 | 0.5 | 0.5 |
| recent_oos | supportive_alignment_macro_mixed | FULL_ENTRY_CANDIDATE | 2 | -0.096373 | 0.0 | 0.5 |
| train_design | mixed_alignment_macro_mixed | NO_ACTION_CONTEXT_WEAK | 63 | 0.163362 | 0.84127 | 0.111111 |
| train_design | source_gap_macro_mixed | NO_ACTION_SOURCE_GAP | 56 | 0.246702 | 0.785714 | 0.196429 |
| train_design | source_gap_company_or_policy_missing_macro_supportive | NO_ACTION_SOURCE_GAP | 52 | 0.177228 | 0.730769 | 0.25 |
| train_design | mixed_alignment_macro_supportive | NORMAL_ENTRY | 43 | 0.035743 | 0.534884 | 0.465116 |
| train_design | mixed_alignment_macro_mixed | CONFIRMATION_REQUIRED | 35 | 0.195791 | 0.742857 | 0.228571 |
| train_design | supportive_alignment_macro_mixed | FULL_ENTRY_CANDIDATE | 30 | 0.227289 | 0.9 | 0.066667 |
| train_design | mixed_alignment_macro_mixed | NORMAL_ENTRY | 27 | 0.203471 | 0.703704 | 0.296296 |
| train_design | mixed_alignment_macro_mixed | SIZE_DOWN | 17 | 0.297941 | 0.823529 | 0.176471 |
| train_design | conflicted_alignment_macro_mixed | CONFIRMATION_REQUIRED | 7 | 0.266077 | 1.0 | 0.0 |
| train_design | supportive_alignment_macro_confirmed | FULL_ENTRY_CANDIDATE | 6 | 0.47993 | 0.666667 | 0.333333 |
| train_design | mixed_alignment_macro_supportive | SIZE_DOWN | 5 | 0.755873 | 1.0 | 0.0 |
| train_design | mixed_alignment_macro_supportive | CONFIRMATION_REQUIRED | 4 | 0.371978 | 1.0 | 0.0 |
| train_design | mixed_alignment_macro_supportive | DELAY_ENTRY | 4 | -0.07975 | 0.5 | 0.5 |
| train_design | conflicted_alignment_macro_mixed | DELAY_ENTRY | 3 | 1.128968 | 1.0 | 0.0 |
| train_design | conflicted_alignment_macro_mixed | SIZE_DOWN | 3 | 0.103643 | 1.0 | 0.0 |
| train_design | macro_conflicted_alignment | SIZE_DOWN | 3 | 0.727727 | 1.0 | 0.0 |
| train_design | mixed_alignment_macro_mixed | DELAY_ENTRY | 3 | 0.112883 | 1.0 | 0.0 |
| train_design | risk_off_override_macro_confirmed | BLOCK_HOLD | 2 | -0.183982 | 0.0 | 1.0 |
| train_design | risk_off_override_macro_mixed | BLOCK_HOLD | 1 | 0.085116 | 1.0 | 0.0 |
| validation | source_gap_company_or_policy_missing_macro_supportive | NO_ACTION_SOURCE_GAP | 60 | 0.119587 | 0.616667 | 0.333333 |
| validation | mixed_alignment_macro_mixed | NO_ACTION_CONTEXT_WEAK | 41 | 0.088257 | 0.585366 | 0.390244 |
| validation | source_gap_macro_mixed | NO_ACTION_SOURCE_GAP | 41 | 0.078006 | 0.609756 | 0.390244 |
| validation | mixed_alignment_macro_supportive | NORMAL_ENTRY | 33 | 0.20205 | 0.848485 | 0.151515 |
| validation | mixed_alignment_macro_mixed | SIZE_DOWN | 21 | 0.01691 | 0.428571 | 0.428571 |
| validation | mixed_alignment_macro_supportive | SIZE_DOWN | 13 | -0.031622 | 0.538462 | 0.461538 |
| validation | mixed_alignment_macro_mixed | CONFIRMATION_REQUIRED | 11 | 0.061527 | 0.727273 | 0.272727 |
| validation | supportive_alignment_macro_mixed | FULL_ENTRY_CANDIDATE | 10 | 0.081208 | 0.6 | 0.3 |
| validation | supportive_alignment_macro_confirmed | FULL_ENTRY_CANDIDATE | 8 | 0.183101 | 0.75 | 0.25 |
| validation | mixed_alignment_macro_supportive | CONFIRMATION_REQUIRED | 6 | 0.254458 | 1.0 | 0.0 |
| validation | mixed_alignment_macro_mixed | NORMAL_ENTRY | 4 | -0.060915 | 0.5 | 0.5 |
| validation | risk_off_override_macro_mixed | BLOCK_HOLD | 4 | 0.114019 | 1.0 | 0.0 |
| validation | conflicted_alignment_macro_mixed | CONFIRMATION_REQUIRED | 3 | 0.219111 | 0.666667 | 0.333333 |
| validation | conflicted_alignment_macro_mixed | DELAY_ENTRY | 2 | -0.209622 | 0.0 | 1.0 |
| validation | conflicted_alignment_macro_mixed | SIZE_DOWN | 2 | -0.06982 | 0.0 | 1.0 |
| validation | mixed_alignment_macro_supportive | DELAY_ENTRY | 2 | -0.008691 | 0.5 | 0.5 |
| validation | mixed_alignment_macro_mixed | DELAY_ENTRY | 1 | -0.139584 | 0.0 | 1.0 |

### Macro Source Audit

| series_id | category | frequency | fetched_flag | feature_rows | first_observation | last_observation | conservative_lag_days | latest_vintage_only_flag | exact_release_timestamp_available_flag | promotion_blocker_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| UNRATE | employment | monthly | 1 | 45 | 2022-08-01 | 2026-05-01 | 45 | 1 | 0 | 1 |
| PAYEMS | employment | monthly | 1 | 46 | 2022-08-01 | 2026-05-01 | 45 | 1 | 0 | 1 |
| CPIAUCSL | inflation | monthly | 1 | 44 | 2022-08-01 | 2026-04-01 | 45 | 1 | 0 | 1 |
| PCEPI | inflation | monthly | 1 | 45 | 2022-08-01 | 2026-04-01 | 45 | 1 | 0 | 1 |
| PCEPILFE | inflation | monthly | 1 | 45 | 2022-08-01 | 2026-04-01 | 45 | 1 | 0 | 1 |
| DFF | fed_rates | daily | 1 | 1367 | 2022-08-16 | 2026-05-13 | 1 | 1 | 0 | 1 |
| DGS2 | fed_rates | daily | 1 | 935 | 2022-08-16 | 2026-05-13 | 1 | 1 | 0 | 1 |
| DGS10 | fed_rates | daily | 1 | 935 | 2022-08-16 | 2026-05-13 | 1 | 1 | 0 | 1 |
| T10Y2Y | fed_rates | daily | 1 | 935 | 2022-08-16 | 2026-05-13 | 1 | 1 | 0 | 1 |
| DTWEXBGS | dollar | daily | 1 | 936 | 2022-08-16 | 2026-05-13 | 1 | 1 | 0 | 1 |
| DCOILWTICO | oil | daily | 1 | 933 | 2022-08-16 | 2026-05-13 | 1 | 1 | 0 | 1 |
| BAMLH0A0HYM2 | credit | daily | 1 | 770 | 2023-06-06 | 2026-05-13 | 1 | 1 | 0 | 1 |
| BAA10Y | credit | daily | 1 | 933 | 2022-08-16 | 2026-05-13 | 1 | 1 | 0 | 1 |
| WALCL | liquidity | weekly | 1 | 196 | 2022-08-17 | 2026-05-13 | 7 | 1 | 0 | 1 |
| RRPONTSYD | liquidity | daily | 1 | 933 | 2022-08-16 | 2026-05-13 | 1 | 1 | 0 | 1 |

### Pass/Fail Matrix

| gate | pass_flag | observed | required |
| --- | --- | --- | --- |
| macro_sources_fetched | 1 | fetched=15/15 | all configured macro series fetched |
| macro_attached_to_entries | 1 | rows=735 | at least one entry has macro state |
| no_label_or_outcome_assignment | 1 | macro/state assignment does not read returns or labels | labels and outcomes evaluation-only |
| vintage_gap_reported | 1 | latest FRED vintage only | latest-vintage limitation must be explicit |
| release_calendar_gap_reported | 1 | conservative lag instead of exact release timestamp | exact release gap must be explicit |
| trading_promotion | 0 | macro context diagnostic only | requires ALFRED/vintage or exact release calendar, split/account/cost validation, live source readiness |

## No-Background Decision-Maker Report

- We added real macro sources: jobs, inflation, Fed/rates, dollar, oil, credit, and liquidity.
- We attached them to each candidate only after a conservative tradable-after delay.
- This makes the context engine smarter, but it is not final yet.
- The remaining issue is that FRED CSV gives latest revised values, not perfect historical vintage truth.
- So this is a better diagnostic engine, not a tradable approval.

## Artifact Manifest

- `task_649_macro_augmented_context_panel.csv`
- `task_649_macro_context_evaluation.csv`
- `task_649_macro_source_audit.csv`
- `task_649_pass_fail_matrix.csv`
- `task_649_decision.csv`
- `task_649_gpt_macro_design_packet.txt`
- `task_649_gpt_macro_design_response.md`
- `artifact_manifest.csv`
