# Task 387 - Canonical Continuation OOS Split & Universe Overlay Validation

## Required Answers
- Did Task 387 use canonical stream only? `YES`
- Did Task 387 use symbol/session recovery? `NO`
- Did Task 387 relax thresholds or optimize strategy? `NO`
- anchor_date: `2025-01-01`
- anchored_oos_lifecycle_count: 81
- anchored_oos_sample_gate: `diagnostic_only`
- sequence_anomaly_count: 61

## Decision
| task_387_verdict | strategy_acceptance_status | anchor_date | canonical_lifecycle_count | anchored_oos_lifecycle_count | anchored_oos_path_group_count | anchored_oos_add_scale_present_flag | anchored_oos_sample_gate | sequence_anomaly_count | canonical_stream_only_flag | symbol_session_inference_used_flag | threshold_relaxation_flag | next_priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COMPLETE_PASS | NOT_VALIDATED_OOS_DIAGNOSTIC_ONLY | 2025-01-01 | 361 | 81 | 6 | 1 | diagnostic_only | 61 | 1 | 0 | 0 | sequence_anomaly_review_then_oos_overlay_deepening |

## Sample Adequacy
| canonical_split | lifecycle_count | path_group_count | max_path_count | min_adequate_path_count | sample_gate |
| --- | --- | --- | --- | --- | --- |
| anchored_oos | 81 | 6 | 29 | 29 | diagnostic_only |
| train | 280 | 6 | 81 | 22 | diagnostic_only |

## Sequence Anomaly Audit
| anomaly_type | count |
| --- | --- |
| transition_after_exit | 0 |
| same_timestamp_multiple_events | 61 |

## OOS Path Quality
| canonical_split | path_type | lifecycle_count | avg_return | median_return | positive_rate | strong_return_rate | loss_rate | avg_add_count | avg_scale_count | avg_reduce_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchored_oos | ENTRY_REDUCE_EXIT | 29 | -0.0635355 | -0.0749032 | 0 | 0 | 1 | 0 | 0 | 1 |
| anchored_oos | ENTRY_ADD_SCALE_REDUCE_EXIT | 17 | 0.102526 | 0.11329 | 0.882353 | 0.705882 | 0.117647 | 1 | 1 | 1 |
| anchored_oos | ENTRY_ADD_REDUCE_EXIT | 14 | -0.015502 | -0.0239242 | 0.428571 | 0 | 0.571429 | 1 | 0 | 1 |
| anchored_oos | ENTRY_ADD_SCALE_EXIT | 14 | 0.111157 | 0.0915082 | 1 | 0.785714 | 0 | 1 | 1 | 0 |
| anchored_oos | ENTRY_ADD_EXIT | 5 | 0.0338066 | 0.0424988 | 1 | 0 | 0 | 1 | 0 | 0 |
| anchored_oos | ENTRY_EXIT_ONLY | 2 | -0.0124175 | -0.0124175 | 0 | 0 | 1 | 0 | 0 | 0 |
| train | ENTRY_REDUCE_EXIT | 81 | -0.0661237 | -0.0802922 | 0.0617284 | 0 | 0.925926 | 0 | 0 | 1 |
| train | ENTRY_ADD_SCALE_REDUCE_EXIT | 80 | 0.0905094 | 0.0663623 | 0.85 | 0.525 | 0.15 | 1 | 1 | 1 |
| train | ENTRY_ADD_SCALE_EXIT | 44 | 0.119389 | 0.0910146 | 0.909091 | 0.795455 | 0 | 1 | 1 | 0 |
| train | ENTRY_ADD_REDUCE_EXIT | 41 | -0.0164555 | -0.0222667 | 0.292683 | 0 | 0.707317 | 1 | 0 | 1 |
| train | ENTRY_ADD_EXIT | 22 | 0.0343091 | 0.0330965 | 0.863636 | 0 | 0.0454545 | 1 | 0 | 0 |
| train | ENTRY_EXIT_ONLY | 12 | 0.0112241 | 0.0144668 | 0.583333 | 0 | 0.0833333 | 0 | 0 | 0 |

## OOS Transition Quality
| canonical_split | transition | transition_count | lifecycle_count | avg_return | positive_rate |
| --- | --- | --- | --- | --- | --- |
| anchored_oos | REDUCE->EXIT | 52 | 52 | -0.010265 | 0.307692 |
| anchored_oos | ENTRY->ADD | 43 | 43 | 0.0723587 | 0.837209 |
| anchored_oos | ENTRY->REDUCE | 36 | 36 | -0.0473003 | 0.111111 |
| anchored_oos | ADD->SCALE | 30 | 30 | 0.10739 | 0.933333 |
| anchored_oos | SCALE->EXIT | 16 | 16 | 0.112712 | 1 |
| anchored_oos | SCALE->REDUCE | 15 | 15 | 0.0997167 | 0.866667 |
| anchored_oos | ADD->EXIT | 11 | 11 | 0.0126367 | 0.727273 |
| anchored_oos | ADD->REDUCE | 9 | 9 | -0.0121725 | 0.444444 |
| anchored_oos | REDUCE->ADD | 7 | 7 | 0.0199602 | 0.571429 |
| anchored_oos | ENTRY->EXIT | 2 | 2 | -0.0124175 | 0 |
| anchored_oos | REDUCE->SCALE | 1 | 1 | 0.0774467 | 1 |
| train | REDUCE->EXIT | 170 | 170 | -0.00399663 | 0.347059 |
| train | ENTRY->ADD | 161 | 161 | 0.0679719 | 0.726708 |
| train | ADD->SCALE | 119 | 119 | 0.10046 | 0.87395 |
| train | ENTRY->REDUCE | 107 | 107 | -0.0358277 | 0.252336 |
| train | SCALE->EXIT | 61 | 61 | 0.106572 | 0.95082 |
| train | SCALE->REDUCE | 59 | 59 | 0.0934814 | 0.847458 |
| train | ADD->REDUCE | 36 | 36 | -0.0122635 | 0.222222 |
| train | ADD->EXIT | 30 | 30 | 0.0305479 | 0.9 |
| train | REDUCE->ADD | 26 | 26 | 0.0573907 | 0.846154 |
| train | ENTRY->EXIT | 8 | 8 | 0.0112241 | 0.875 |
| train | REDUCE->SCALE | 5 | 5 | 0.0926899 | 0.8 |

## Bucket Overlay Quality
| canonical_split | persistence_universe_bucket | lifecycle_count | avg_return | median_return | positive_rate | strong_return_rate | loss_rate | avg_add_count | avg_scale_count | avg_reduce_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| anchored_oos | canonical_continuation_engine | 81 | 0.0170837 | -0.00414199 | 0.493827 | 0.283951 | 0.506173 | 0.617284 | 0.382716 | 0.740741 |
| train | canonical_continuation_engine | 280 | 0.0253818 | 0.0176796 | 0.539286 | 0.275 | 0.421429 | 0.667857 | 0.442857 | 0.721429 |

## OOS Panel Sample
| lifecycle_id | event_count | add_event_count | scale_event_count | reduce_event_count | exit_event_count | canonical_sequence_valid_flag | canonical_persistence_quality_flag | continuation_duration_minutes | symbol | entry_ts | exit_ts | bars_held | add_flag | scale_flag | reduce_flag | exit_reason | return_from_entry | persistence_universe_bucket | current_split | positive_return_flag | strong_return_flag | loss_flag | path_type | continuation_quality_score | entry_ts_dt | canonical_split |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LIFECYCLE|AAPL|2021-06-14|CONT-0001 | 4 | 1 | 1 | 0 | 1 | 1 | 1 | 41760 | AAPL | 2021-06-14T14:30:00+00:00 | 2021-07-13T14:30:00+00:00 | 20 | 1 | 1 | 0 | time_exit | 0.116186 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_EXIT | 0.166186 | 2021-06-14 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2021-07-14|CONT-0002 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 40320 | AAPL | 2021-07-14T14:30:00+00:00 | 2021-08-11T14:30:00+00:00 | 20 | 0 | 0 | 1 | time_exit | -0.0220583 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.0320583 | 2021-07-14 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2021-08-16|CONT-0003 | 4 | 1 | 0 | 1 | 1 | 1 | 1 | 41760 | AAPL | 2021-08-16T14:30:00+00:00 | 2021-09-14T14:30:00+00:00 | 20 | 1 | 0 | 1 | time_exit | -0.0198518 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_ADD_REDUCE_EXIT | -0.00985177 | 2021-08-16 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2021-10-19|CONT-0004 | 2 | 0 | 0 | 0 | 1 | 1 | 1 | 40320 | AAPL | 2021-10-19T14:30:00+00:00 | 2021-11-16T14:30:00+00:00 | 20 | 0 | 0 | 0 | time_exit | 0.0150578 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_EXIT_ONLY | 0.0150578 | 2021-10-19 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2021-11-17|CONT-0005 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 41760 | AAPL | 2021-11-17T14:30:00+00:00 | 2021-12-16T14:30:00+00:00 | 20 | 1 | 1 | 1 | time_exit | 0.122288 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.162288 | 2021-11-17 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2022-03-23|CONT-0006 | 4 | 1 | 0 | 1 | 1 | 1 | 1 | 41760 | AAPL | 2022-03-23T14:30:00+00:00 | 2022-04-21T14:30:00+00:00 | 20 | 1 | 0 | 1 | time_exit | -0.0222667 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_ADD_REDUCE_EXIT | -0.0122667 | 2022-03-23 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2022-07-14|CONT-0007 | 4 | 1 | 1 | 0 | 1 | 1 | 1 | 40320 | AAPL | 2022-07-14T14:30:00+00:00 | 2022-08-11T14:30:00+00:00 | 20 | 1 | 1 | 0 | time_exit | 0.134842 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_EXIT | 0.184842 | 2022-07-14 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2022-08-12|CONT-0008 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 25920 | AAPL | 2022-08-12T14:30:00+00:00 | 2022-08-30T14:30:00+00:00 | 12 | 0 | 0 | 1 | drawdown_exit | -0.0766415 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.0866415 | 2022-08-12 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2022-10-28|CONT-0009 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 8640 | AAPL | 2022-10-28T14:30:00+00:00 | 2022-11-03T14:30:00+00:00 | 4 | 0 | 0 | 1 | drawdown_exit | -0.108257 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.118257 | 2022-10-28 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2023-01-23|CONT-0010 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 41760 | AAPL | 2023-01-23T14:30:00+00:00 | 2023-02-21T14:30:00+00:00 | 20 | 1 | 1 | 1 | time_exit | 0.0522287 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0922287 | 2023-01-23 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2023-03-20|CONT-0011 | 3 | 1 | 0 | 0 | 1 | 1 | 1 | 41760 | AAPL | 2023-03-20T14:30:00+00:00 | 2023-04-18T14:30:00+00:00 | 20 | 1 | 0 | 0 | time_exit | 0.0576239 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_EXIT | 0.0776239 | 2023-03-20 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2023-04-19|CONT-0012 | 3 | 1 | 0 | 0 | 1 | 1 | 1 | 40320 | AAPL | 2023-04-19T14:30:00+00:00 | 2023-05-17T14:30:00+00:00 | 20 | 1 | 0 | 0 | time_exit | 0.0301855 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_EXIT | 0.0501855 | 2023-04-19 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2023-05-18|CONT-0013 | 4 | 1 | 1 | 0 | 1 | 1 | 1 | 41760 | AAPL | 2023-05-18T14:30:00+00:00 | 2023-06-16T14:30:00+00:00 | 20 | 1 | 1 | 0 | time_exit | 0.0563839 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_EXIT | 0.106384 | 2023-05-18 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2023-06-22|CONT-0014 | 3 | 1 | 0 | 0 | 1 | 1 | 1 | 41760 | AAPL | 2023-06-22T14:30:00+00:00 | 2023-07-21T14:30:00+00:00 | 20 | 1 | 0 | 0 | time_exit | 0.0264171 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_EXIT | 0.0464171 | 2023-06-22 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2023-09-01|CONT-0015 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 17280 | AAPL | 2023-09-01T14:30:00+00:00 | 2023-09-13T14:30:00+00:00 | 7 | 0 | 0 | 1 | drawdown_exit | -0.0804919 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.0904919 | 2023-09-01 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2023-10-11|CONT-0016 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 40320 | AAPL | 2023-10-11T14:30:00+00:00 | 2023-11-08T14:30:00+00:00 | 20 | 0 | 0 | 1 | time_exit | 0.0171857 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_REDUCE_EXIT | 0.00718574 | 2023-10-11 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2023-11-10|CONT-0017 | 3 | 1 | 0 | 0 | 1 | 1 | 1 | 44640 | AAPL | 2023-11-10T14:30:00+00:00 | 2023-12-11T14:30:00+00:00 | 20 | 1 | 0 | 0 | time_exit | 0.0363734 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_EXIT | 0.0563734 | 2023-11-10 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2023-12-13|CONT-0018 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 31680 | AAPL | 2023-12-13T14:30:00+00:00 | 2024-01-04T14:30:00+00:00 | 14 | 0 | 0 | 1 | drawdown_exit | -0.081077 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.091077 | 2023-12-13 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2024-05-03|CONT-0019 | 3 | 1 | 0 | 0 | 1 | 1 | 1 | 44640 | AAPL | 2024-05-03T14:30:00+00:00 | 2024-06-03T14:30:00+00:00 | 20 | 1 | 0 | 0 | time_exit | 0.0580761 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_EXIT | 0.0780761 | 2024-05-03 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2024-06-05|CONT-0020 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 43200 | AAPL | 2024-06-05T14:30:00+00:00 | 2024-07-05T14:30:00+00:00 | 20 | 1 | 1 | 1 | time_exit | 0.155562 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.195562 | 2024-06-05 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2024-07-08|CONT-0021 | 4 | 1 | 0 | 1 | 1 | 1 | 1 | 40320 | AAPL | 2024-07-08T14:30:00+00:00 | 2024-08-05T14:30:00+00:00 | 20 | 1 | 0 | 1 | drawdown_exit | -0.0814239 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_ADD_REDUCE_EXIT | -0.0714239 | 2024-07-08 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2024-10-15|CONT-0022 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 40320 | AAPL | 2024-10-15T14:30:00+00:00 | 2024-11-12T14:30:00+00:00 | 20 | 0 | 0 | 1 | time_exit | -0.0411375 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.0511375 | 2024-10-15 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2024-11-26|CONT-0023 | 4 | 1 | 1 | 0 | 1 | 1 | 1 | 43200 | AAPL | 2024-11-26T14:30:00+00:00 | 2024-12-26T14:30:00+00:00 | 20 | 1 | 1 | 0 | time_exit | 0.101931 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_EXIT | 0.151931 | 2024-11-26 14:30:00+00:00 | train |
| LIFECYCLE|AAPL|2025-07-01|CONT-0024 | 3 | 1 | 0 | 0 | 1 | 1 | 1 | 41760 | AAPL | 2025-07-01T14:30:00+00:00 | 2025-07-30T14:30:00+00:00 | 20 | 1 | 0 | 0 | time_exit | 0.00591856 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_EXIT | 0.0259186 | 2025-07-01 14:30:00+00:00 | anchored_oos |
| LIFECYCLE|AAPL|2025-08-07|CONT-0025 | 4 | 1 | 1 | 0 | 1 | 1 | 1 | 41760 | AAPL | 2025-08-07T14:30:00+00:00 | 2025-09-05T14:30:00+00:00 | 20 | 1 | 1 | 0 | time_exit | 0.0893515 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_EXIT | 0.139351 | 2025-08-07 14:30:00+00:00 | anchored_oos |
| LIFECYCLE|AAPL|2025-09-19|CONT-0026 | 4 | 1 | 0 | 1 | 1 | 1 | 1 | 40320 | AAPL | 2025-09-19T14:30:00+00:00 | 2025-10-17T14:30:00+00:00 | 20 | 1 | 0 | 1 | time_exit | 0.0276578 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_REDUCE_EXIT | 0.0376578 | 2025-09-19 14:30:00+00:00 | anchored_oos |
| LIFECYCLE|AAPL|2025-10-20|CONT-0027 | 3 | 1 | 0 | 0 | 1 | 1 | 1 | 40320 | AAPL | 2025-10-20T14:30:00+00:00 | 2025-11-17T14:30:00+00:00 | 20 | 1 | 0 | 0 | time_exit | 0.0199054 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_EXIT | 0.0399054 | 2025-10-20 14:30:00+00:00 | anchored_oos |
| LIFECYCLE|AAPL|2025-12-01|CONT-0028 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 41760 | AAPL | 2025-12-01T14:30:00+00:00 | 2025-12-30T14:30:00+00:00 | 20 | 0 | 0 | 1 | time_exit | -0.0353939 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.0453939 | 2025-12-01 14:30:00+00:00 | anchored_oos |
| LIFECYCLE|AAPL|2026-02-04|CONT-0029 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 12960 | AAPL | 2026-02-04T14:30:00+00:00 | 2026-02-13T14:30:00+00:00 | 7 | 0 | 0 | 1 | drawdown_exit | -0.0749032 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.0849032 | 2026-02-04 14:30:00+00:00 | anchored_oos |
| LIFECYCLE|AAPL|2026-04-15|CONT-0030 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |  |  |  |  |  |  |  |  |  | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 0 | ENTRY_EXIT_ONLY | 0 | NaT | train |
| LIFECYCLE|AMD|2021-06-17|CONT-0001 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 40320 | AMD | 2021-06-17T14:30:00+00:00 | 2021-07-15T14:30:00+00:00 | 19 | 1 | 1 | 1 | drawdown_exit | 0.0280275 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0680275 | 2021-06-17 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2021-07-28|CONT-0002 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 17280 | AMD | 2021-07-28T14:30:00+00:00 | 2021-08-09T14:30:00+00:00 | 8 | 1 | 1 | 1 | drawdown_exit | 0.0985398 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.13854 | 2021-07-28 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2021-10-13|CONT-0003 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 40320 | AMD | 2021-10-13T14:30:00+00:00 | 2021-11-10T14:30:00+00:00 | 20 | 1 | 1 | 1 | time_exit | 0.28133 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.32133 | 2021-10-13 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2021-11-29|CONT-0004 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 5760 | AMD | 2021-11-29T14:30:00+00:00 | 2021-12-03T14:30:00+00:00 | 4 | 0 | 0 | 1 | drawdown_exit | -0.110555 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.120555 | 2021-11-29 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2022-03-29|CONT-0005 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 2880 | AMD | 2022-03-29T14:30:00+00:00 | 2022-03-31T14:30:00+00:00 | 2 | 0 | 0 | 1 | drawdown_exit | -0.112716 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.122716 | 2022-03-29 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2022-05-17|CONT-0006 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 4320 | AMD | 2022-05-17T14:30:00+00:00 | 2022-05-20T14:30:00+00:00 | 3 | 0 | 0 | 1 | drawdown_exit | -0.0875378 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.0975378 | 2022-05-17 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2022-06-02|CONT-0007 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 10080 | AMD | 2022-06-02T14:30:00+00:00 | 2022-06-09T14:30:00+00:00 | 5 | 0 | 0 | 1 | drawdown_exit | -0.0901556 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.100156 | 2022-06-02 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2022-07-20|CONT-0008 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 28800 | AMD | 2022-07-20T14:30:00+00:00 | 2022-08-09T14:30:00+00:00 | 14 | 1 | 1 | 1 | drawdown_exit | 0.0683216 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.108322 | 2022-07-20 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2022-11-10|CONT-0009 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 37440 | AMD | 2022-11-10T14:30:00+00:00 | 2022-12-06T14:30:00+00:00 | 17 | 1 | 1 | 1 | drawdown_exit | 0.0262888 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0662888 | 2022-11-10 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2023-01-23|CONT-0010 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 34560 | AMD | 2023-01-23T14:30:00+00:00 | 2023-02-16T14:30:00+00:00 | 18 | 1 | 1 | 1 | drawdown_exit | 0.0463871 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0863871 | 2023-01-23 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2023-03-15|CONT-0011 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 41760 | AMD | 2023-03-15T14:30:00+00:00 | 2023-04-13T14:30:00+00:00 | 20 | 1 | 1 | 1 | drawdown_exit | 0.0268733 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0668733 | 2023-03-15 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2023-05-10|CONT-0012 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 41760 | AMD | 2023-05-10T14:30:00+00:00 | 2023-06-08T14:30:00+00:00 | 20 | 1 | 1 | 1 | time_exit | 0.247681 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.287681 | 2023-05-10 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2023-11-03|CONT-0013 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 44640 | AMD | 2023-11-03T14:30:00+00:00 | 2023-12-04T14:30:00+00:00 | 20 | 1 | 1 | 1 | time_exit | 0.0563029 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0963029 | 2023-11-03 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2023-12-07|CONT-0014 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 38880 | AMD | 2023-12-07T14:30:00+00:00 | 2024-01-03T14:30:00+00:00 | 17 | 1 | 1 | 1 | drawdown_exit | 0.0541405 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0941405 | 2023-12-07 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2024-01-16|CONT-0015 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 40320 | AMD | 2024-01-16T14:30:00+00:00 | 2024-02-13T14:30:00+00:00 | 20 | 1 | 1 | 1 | time_exit | 0.0806349 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.120635 | 2024-01-16 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2024-02-29|CONT-0016 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 20160 | AMD | 2024-02-29T14:30:00+00:00 | 2024-03-14T14:30:00+00:00 | 10 | 1 | 1 | 1 | drawdown_exit | -0.0284112 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0115888 | 2024-02-29 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2024-05-16|CONT-0017 | 4 | 1 | 0 | 1 | 1 | 1 | 1 | 41760 | AMD | 2024-05-16T14:30:00+00:00 | 2024-06-14T14:30:00+00:00 | 20 | 1 | 0 | 1 | time_exit | -0.0183864 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_ADD_REDUCE_EXIT | -0.00838636 | 2024-05-16 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2024-07-05|CONT-0018 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 17280 | AMD | 2024-07-05T14:30:00+00:00 | 2024-07-17T14:30:00+00:00 | 8 | 1 | 1 | 1 | drawdown_exit | -0.0725422 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_ADD_SCALE_REDUCE_EXIT | -0.0325422 | 2024-07-05 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2024-09-25|CONT-0019 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 28800 | AMD | 2024-09-25T14:30:00+00:00 | 2024-10-15T14:30:00+00:00 | 14 | 1 | 1 | 1 | drawdown_exit | -0.0332058 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.00679419 | 2024-09-25 14:30:00+00:00 | train |
| LIFECYCLE|AMD|2025-03-24|CONT-0020 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 5760 | AMD | 2025-03-24T14:30:00+00:00 | 2025-03-28T14:30:00+00:00 | 4 | 0 | 0 | 1 | drawdown_exit | -0.0933684 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.103368 | 2025-03-24 14:30:00+00:00 | anchored_oos |