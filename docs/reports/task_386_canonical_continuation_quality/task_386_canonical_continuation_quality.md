# Task 386 - Canonical Continuation Quality Evaluation

## Required Answers
- Did Task 386 use reconstruction/recovery? `NO`
- Did Task 386 use symbol/session matching? `NO`
- Did Task 386 relax thresholds or optimize strategy? `NO`
- canonical_lifecycle_count: 361
- add_scale_quality_measurable: `True`
- transition_quality_measurable: `True`
- bucket_quality_measurable: `True`

## Decision
| task_386_verdict | strategy_acceptance_status | canonical_lifecycle_count | path_group_count | transition_group_count | bucket_group_count | add_scale_quality_measurable_flag | bucket_quality_measurable_flag | transition_quality_measurable_flag | canonical_stream_only_flag | symbol_session_inference_used_flag | threshold_relaxation_flag | next_priority |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COMPLETE_PASS | NOT_VALIDATED_QUALITY_DIAGNOSTIC_ONLY | 361 | 6 | 13 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | canonical_quality_oos_split_and_universe_overlay |

## Boundary Audit
| canonical_stream_only_flag | symbol_session_inference_used_flag | recovery_scoring_used_flag | threshold_relaxation_flag | label_overwrite_flag | event_types_present | lifecycle_count |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | 0 | 0 | 0 | 0 | ADD|ENTRY|EXIT|REDUCE|SCALE | 361 |

## Path Quality
| path_type | lifecycle_count | avg_return | median_return | positive_rate | strong_return_rate | loss_rate | avg_quality_score | avg_add_count | avg_scale_count | avg_reduce_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ENTRY_REDUCE_EXIT | 110 | -0.0654351 | -0.0790677 | 0.0454545 | 0 | 0.945455 | -0.0748402 | 0 | 0 | 1 |
| ENTRY_ADD_SCALE_REDUCE_EXIT | 97 | 0.0926155 | 0.0700703 | 0.85567 | 0.556701 | 0.14433 | 0.132615 | 1 | 1 | 1 |
| ENTRY_ADD_SCALE_EXIT | 58 | 0.117254 | 0.0910146 | 0.931034 | 0.793103 | 0 | 0.159168 | 1 | 1 | 0 |
| ENTRY_ADD_REDUCE_EXIT | 55 | -0.0162128 | -0.0222667 | 0.327273 | 0 | 0.672727 | -0.00621282 | 1 | 0 | 1 |
| ENTRY_ADD_EXIT | 27 | 0.0342086 | 0.0355732 | 0.888889 | 0 | 0.037037 | 0.0516746 | 1 | 0 | 0 |
| ENTRY_EXIT_ONLY | 14 | 0.00649579 | 0.00956068 | 0.5 | 0 | 0.214286 | 0.00463985 | 0 | 0 | 0 |

## Transition Quality
| transition | transition_count | lifecycle_count | avg_return | positive_rate |
| --- | --- | --- | --- | --- |
| ENTRY->ADD | 204 | 204 | 0.0689246 | 0.75 |
| REDUCE->EXIT | 200 | 200 | -0.00856748 | 0.33 |
| ADD->SCALE | 146 | 146 | 0.102482 | 0.883562 |
| ENTRY->REDUCE | 135 | 135 | -0.0354487 | 0.22963 |
| SCALE->EXIT | 84 | 84 | 0.113026 | 0.952381 |
| SCALE->REDUCE | 62 | 62 | 0.0877087 | 0.83871 |
| ADD->EXIT | 48 | 48 | 0.0232546 | 0.791667 |
| ADD->REDUCE | 41 | 41 | -0.00950395 | 0.292683 |
| REDUCE->ADD | 33 | 33 | 0.0494509 | 0.787879 |
| EXIT->REDUCE | 24 | 24 | 0.027559 | 0.458333 |
| ENTRY->EXIT | 18 | 18 | -0.0380813 | 0.388889 |
| EXIT->SCALE | 5 | 5 | 0.0766564 | 1 |
| REDUCE->SCALE | 4 | 4 | 0.0949425 | 0.75 |

## Bucket Quality
| persistence_universe_bucket | lifecycle_count | avg_return | median_return | positive_rate | strong_return_rate | loss_rate | avg_quality_score | avg_add_count | avg_scale_count | avg_reduce_count |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| canonical_continuation_engine | 361 | 0.0234614 | 0.0154242 | 0.529086 | 0.277008 | 0.440443 | 0.0414999 | 0.65651 | 0.429363 | 0.725762 |

## Lifecycle Quality Sample
| lifecycle_id | event_count | add_event_count | scale_event_count | reduce_event_count | exit_event_count | canonical_sequence_valid_flag | canonical_persistence_quality_flag | continuation_duration_minutes | symbol | entry_ts | exit_ts | bars_held | add_flag | scale_flag | reduce_flag | exit_reason | return_from_entry | persistence_universe_bucket | current_split | positive_return_flag | strong_return_flag | loss_flag | path_type | continuation_quality_score |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| LIFECYCLE|AAPL|2021-06-14|CONT-0001 | 4 | 1 | 1 | 0 | 1 | 1 | 1 | 41760 | AAPL | 2021-06-14T14:30:00+00:00 | 2021-07-13T14:30:00+00:00 | 20 | 1 | 1 | 0 | time_exit | 0.116186 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_EXIT | 0.166186 |
| LIFECYCLE|AAPL|2021-07-14|CONT-0002 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 40320 | AAPL | 2021-07-14T14:30:00+00:00 | 2021-08-11T14:30:00+00:00 | 20 | 0 | 0 | 1 | time_exit | -0.0220583 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.0320583 |
| LIFECYCLE|AAPL|2021-08-16|CONT-0003 | 4 | 1 | 0 | 1 | 1 | 1 | 1 | 41760 | AAPL | 2021-08-16T14:30:00+00:00 | 2021-09-14T14:30:00+00:00 | 20 | 1 | 0 | 1 | time_exit | -0.0198518 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_ADD_REDUCE_EXIT | -0.00985177 |
| LIFECYCLE|AAPL|2021-10-19|CONT-0004 | 2 | 0 | 0 | 0 | 1 | 1 | 1 | 40320 | AAPL | 2021-10-19T14:30:00+00:00 | 2021-11-16T14:30:00+00:00 | 20 | 0 | 0 | 0 | time_exit | 0.0150578 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_EXIT_ONLY | 0.0150578 |
| LIFECYCLE|AAPL|2021-11-17|CONT-0005 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 41760 | AAPL | 2021-11-17T14:30:00+00:00 | 2021-12-16T14:30:00+00:00 | 20 | 1 | 1 | 1 | time_exit | 0.122288 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.162288 |
| LIFECYCLE|AAPL|2022-03-23|CONT-0006 | 4 | 1 | 0 | 1 | 1 | 1 | 1 | 41760 | AAPL | 2022-03-23T14:30:00+00:00 | 2022-04-21T14:30:00+00:00 | 20 | 1 | 0 | 1 | time_exit | -0.0222667 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_ADD_REDUCE_EXIT | -0.0122667 |
| LIFECYCLE|AAPL|2022-07-14|CONT-0007 | 4 | 1 | 1 | 0 | 1 | 1 | 1 | 40320 | AAPL | 2022-07-14T14:30:00+00:00 | 2022-08-11T14:30:00+00:00 | 20 | 1 | 1 | 0 | time_exit | 0.134842 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_EXIT | 0.184842 |
| LIFECYCLE|AAPL|2022-08-12|CONT-0008 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 25920 | AAPL | 2022-08-12T14:30:00+00:00 | 2022-08-30T14:30:00+00:00 | 12 | 0 | 0 | 1 | drawdown_exit | -0.0766415 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.0866415 |
| LIFECYCLE|AAPL|2022-10-28|CONT-0009 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 8640 | AAPL | 2022-10-28T14:30:00+00:00 | 2022-11-03T14:30:00+00:00 | 4 | 0 | 0 | 1 | drawdown_exit | -0.108257 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.118257 |
| LIFECYCLE|AAPL|2023-01-23|CONT-0010 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 41760 | AAPL | 2023-01-23T14:30:00+00:00 | 2023-02-21T14:30:00+00:00 | 20 | 1 | 1 | 1 | time_exit | 0.0522287 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0922287 |
| LIFECYCLE|AAPL|2023-03-20|CONT-0011 | 3 | 1 | 0 | 0 | 1 | 1 | 1 | 41760 | AAPL | 2023-03-20T14:30:00+00:00 | 2023-04-18T14:30:00+00:00 | 20 | 1 | 0 | 0 | time_exit | 0.0576239 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_EXIT | 0.0776239 |
| LIFECYCLE|AAPL|2023-04-19|CONT-0012 | 3 | 1 | 0 | 0 | 1 | 1 | 1 | 40320 | AAPL | 2023-04-19T14:30:00+00:00 | 2023-05-17T14:30:00+00:00 | 20 | 1 | 0 | 0 | time_exit | 0.0301855 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_EXIT | 0.0501855 |
| LIFECYCLE|AAPL|2023-05-18|CONT-0013 | 4 | 1 | 1 | 0 | 1 | 1 | 1 | 41760 | AAPL | 2023-05-18T14:30:00+00:00 | 2023-06-16T14:30:00+00:00 | 20 | 1 | 1 | 0 | time_exit | 0.0563839 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_EXIT | 0.106384 |
| LIFECYCLE|AAPL|2023-06-22|CONT-0014 | 3 | 1 | 0 | 0 | 1 | 1 | 1 | 41760 | AAPL | 2023-06-22T14:30:00+00:00 | 2023-07-21T14:30:00+00:00 | 20 | 1 | 0 | 0 | time_exit | 0.0264171 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_EXIT | 0.0464171 |
| LIFECYCLE|AAPL|2023-09-01|CONT-0015 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 17280 | AAPL | 2023-09-01T14:30:00+00:00 | 2023-09-13T14:30:00+00:00 | 7 | 0 | 0 | 1 | drawdown_exit | -0.0804919 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.0904919 |
| LIFECYCLE|AAPL|2023-10-11|CONT-0016 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 40320 | AAPL | 2023-10-11T14:30:00+00:00 | 2023-11-08T14:30:00+00:00 | 20 | 0 | 0 | 1 | time_exit | 0.0171857 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_REDUCE_EXIT | 0.00718574 |
| LIFECYCLE|AAPL|2023-11-10|CONT-0017 | 3 | 1 | 0 | 0 | 1 | 1 | 1 | 44640 | AAPL | 2023-11-10T14:30:00+00:00 | 2023-12-11T14:30:00+00:00 | 20 | 1 | 0 | 0 | time_exit | 0.0363734 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_EXIT | 0.0563734 |
| LIFECYCLE|AAPL|2023-12-13|CONT-0018 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 31680 | AAPL | 2023-12-13T14:30:00+00:00 | 2024-01-04T14:30:00+00:00 | 14 | 0 | 0 | 1 | drawdown_exit | -0.081077 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.091077 |
| LIFECYCLE|AAPL|2024-05-03|CONT-0019 | 3 | 1 | 0 | 0 | 1 | 1 | 1 | 44640 | AAPL | 2024-05-03T14:30:00+00:00 | 2024-06-03T14:30:00+00:00 | 20 | 1 | 0 | 0 | time_exit | 0.0580761 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_EXIT | 0.0780761 |
| LIFECYCLE|AAPL|2024-06-05|CONT-0020 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 43200 | AAPL | 2024-06-05T14:30:00+00:00 | 2024-07-05T14:30:00+00:00 | 20 | 1 | 1 | 1 | time_exit | 0.155562 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.195562 |
| LIFECYCLE|AAPL|2024-07-08|CONT-0021 | 4 | 1 | 0 | 1 | 1 | 1 | 1 | 40320 | AAPL | 2024-07-08T14:30:00+00:00 | 2024-08-05T14:30:00+00:00 | 20 | 1 | 0 | 1 | drawdown_exit | -0.0814239 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_ADD_REDUCE_EXIT | -0.0714239 |
| LIFECYCLE|AAPL|2024-10-15|CONT-0022 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 40320 | AAPL | 2024-10-15T14:30:00+00:00 | 2024-11-12T14:30:00+00:00 | 20 | 0 | 0 | 1 | time_exit | -0.0411375 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.0511375 |
| LIFECYCLE|AAPL|2024-11-26|CONT-0023 | 4 | 1 | 1 | 0 | 1 | 1 | 1 | 43200 | AAPL | 2024-11-26T14:30:00+00:00 | 2024-12-26T14:30:00+00:00 | 20 | 1 | 1 | 0 | time_exit | 0.101931 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_EXIT | 0.151931 |
| LIFECYCLE|AAPL|2025-07-01|CONT-0024 | 3 | 1 | 0 | 0 | 1 | 1 | 1 | 41760 | AAPL | 2025-07-01T14:30:00+00:00 | 2025-07-30T14:30:00+00:00 | 20 | 1 | 0 | 0 | time_exit | 0.00591856 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_EXIT | 0.0259186 |
| LIFECYCLE|AAPL|2025-08-07|CONT-0025 | 4 | 1 | 1 | 0 | 1 | 1 | 1 | 41760 | AAPL | 2025-08-07T14:30:00+00:00 | 2025-09-05T14:30:00+00:00 | 20 | 1 | 1 | 0 | time_exit | 0.0893515 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_EXIT | 0.139351 |
| LIFECYCLE|AAPL|2025-09-19|CONT-0026 | 4 | 1 | 0 | 1 | 1 | 1 | 1 | 40320 | AAPL | 2025-09-19T14:30:00+00:00 | 2025-10-17T14:30:00+00:00 | 20 | 1 | 0 | 1 | time_exit | 0.0276578 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_REDUCE_EXIT | 0.0376578 |
| LIFECYCLE|AAPL|2025-10-20|CONT-0027 | 3 | 1 | 0 | 0 | 1 | 1 | 1 | 40320 | AAPL | 2025-10-20T14:30:00+00:00 | 2025-11-17T14:30:00+00:00 | 20 | 1 | 0 | 0 | time_exit | 0.0199054 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_EXIT | 0.0399054 |
| LIFECYCLE|AAPL|2025-12-01|CONT-0028 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 41760 | AAPL | 2025-12-01T14:30:00+00:00 | 2025-12-30T14:30:00+00:00 | 20 | 0 | 0 | 1 | time_exit | -0.0353939 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.0453939 |
| LIFECYCLE|AAPL|2026-02-04|CONT-0029 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 12960 | AAPL | 2026-02-04T14:30:00+00:00 | 2026-02-13T14:30:00+00:00 | 7 | 0 | 0 | 1 | drawdown_exit | -0.0749032 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.0849032 |
| LIFECYCLE|AAPL|2026-04-15|CONT-0030 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 |  |  |  |  |  |  |  |  |  | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 0 | ENTRY_EXIT_ONLY | 0 |
| LIFECYCLE|AMD|2021-06-17|CONT-0001 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 40320 | AMD | 2021-06-17T14:30:00+00:00 | 2021-07-15T14:30:00+00:00 | 19 | 1 | 1 | 1 | drawdown_exit | 0.0280275 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0680275 |
| LIFECYCLE|AMD|2021-07-28|CONT-0002 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 17280 | AMD | 2021-07-28T14:30:00+00:00 | 2021-08-09T14:30:00+00:00 | 8 | 1 | 1 | 1 | drawdown_exit | 0.0985398 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.13854 |
| LIFECYCLE|AMD|2021-10-13|CONT-0003 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 40320 | AMD | 2021-10-13T14:30:00+00:00 | 2021-11-10T14:30:00+00:00 | 20 | 1 | 1 | 1 | time_exit | 0.28133 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.32133 |
| LIFECYCLE|AMD|2021-11-29|CONT-0004 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 5760 | AMD | 2021-11-29T14:30:00+00:00 | 2021-12-03T14:30:00+00:00 | 4 | 0 | 0 | 1 | drawdown_exit | -0.110555 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.120555 |
| LIFECYCLE|AMD|2022-03-29|CONT-0005 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 2880 | AMD | 2022-03-29T14:30:00+00:00 | 2022-03-31T14:30:00+00:00 | 2 | 0 | 0 | 1 | drawdown_exit | -0.112716 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.122716 |
| LIFECYCLE|AMD|2022-05-17|CONT-0006 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 4320 | AMD | 2022-05-17T14:30:00+00:00 | 2022-05-20T14:30:00+00:00 | 3 | 0 | 0 | 1 | drawdown_exit | -0.0875378 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.0975378 |
| LIFECYCLE|AMD|2022-06-02|CONT-0007 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 10080 | AMD | 2022-06-02T14:30:00+00:00 | 2022-06-09T14:30:00+00:00 | 5 | 0 | 0 | 1 | drawdown_exit | -0.0901556 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.100156 |
| LIFECYCLE|AMD|2022-07-20|CONT-0008 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 28800 | AMD | 2022-07-20T14:30:00+00:00 | 2022-08-09T14:30:00+00:00 | 14 | 1 | 1 | 1 | drawdown_exit | 0.0683216 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.108322 |
| LIFECYCLE|AMD|2022-11-10|CONT-0009 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 37440 | AMD | 2022-11-10T14:30:00+00:00 | 2022-12-06T14:30:00+00:00 | 17 | 1 | 1 | 1 | drawdown_exit | 0.0262888 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0662888 |
| LIFECYCLE|AMD|2023-01-23|CONT-0010 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 34560 | AMD | 2023-01-23T14:30:00+00:00 | 2023-02-16T14:30:00+00:00 | 18 | 1 | 1 | 1 | drawdown_exit | 0.0463871 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0863871 |
| LIFECYCLE|AMD|2023-03-15|CONT-0011 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 41760 | AMD | 2023-03-15T14:30:00+00:00 | 2023-04-13T14:30:00+00:00 | 20 | 1 | 1 | 1 | drawdown_exit | 0.0268733 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0668733 |
| LIFECYCLE|AMD|2023-05-10|CONT-0012 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 41760 | AMD | 2023-05-10T14:30:00+00:00 | 2023-06-08T14:30:00+00:00 | 20 | 1 | 1 | 1 | time_exit | 0.247681 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.287681 |
| LIFECYCLE|AMD|2023-11-03|CONT-0013 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 44640 | AMD | 2023-11-03T14:30:00+00:00 | 2023-12-04T14:30:00+00:00 | 20 | 1 | 1 | 1 | time_exit | 0.0563029 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0963029 |
| LIFECYCLE|AMD|2023-12-07|CONT-0014 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 38880 | AMD | 2023-12-07T14:30:00+00:00 | 2024-01-03T14:30:00+00:00 | 17 | 1 | 1 | 1 | drawdown_exit | 0.0541405 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 0 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0941405 |
| LIFECYCLE|AMD|2024-01-16|CONT-0015 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 40320 | AMD | 2024-01-16T14:30:00+00:00 | 2024-02-13T14:30:00+00:00 | 20 | 1 | 1 | 1 | time_exit | 0.0806349 | canonical_continuation_engine | offline_task385_continuation_engine | 1 | 1 | 0 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.120635 |
| LIFECYCLE|AMD|2024-02-29|CONT-0016 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 20160 | AMD | 2024-02-29T14:30:00+00:00 | 2024-03-14T14:30:00+00:00 | 10 | 1 | 1 | 1 | drawdown_exit | -0.0284112 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.0115888 |
| LIFECYCLE|AMD|2024-05-16|CONT-0017 | 4 | 1 | 0 | 1 | 1 | 1 | 1 | 41760 | AMD | 2024-05-16T14:30:00+00:00 | 2024-06-14T14:30:00+00:00 | 20 | 1 | 0 | 1 | time_exit | -0.0183864 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_ADD_REDUCE_EXIT | -0.00838636 |
| LIFECYCLE|AMD|2024-07-05|CONT-0018 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 17280 | AMD | 2024-07-05T14:30:00+00:00 | 2024-07-17T14:30:00+00:00 | 8 | 1 | 1 | 1 | drawdown_exit | -0.0725422 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_ADD_SCALE_REDUCE_EXIT | -0.0325422 |
| LIFECYCLE|AMD|2024-09-25|CONT-0019 | 5 | 1 | 1 | 1 | 1 | 1 | 1 | 28800 | AMD | 2024-09-25T14:30:00+00:00 | 2024-10-15T14:30:00+00:00 | 14 | 1 | 1 | 1 | drawdown_exit | -0.0332058 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_ADD_SCALE_REDUCE_EXIT | 0.00679419 |
| LIFECYCLE|AMD|2025-03-24|CONT-0020 | 3 | 0 | 0 | 1 | 1 | 1 | 1 | 5760 | AMD | 2025-03-24T14:30:00+00:00 | 2025-03-28T14:30:00+00:00 | 4 | 0 | 0 | 1 | drawdown_exit | -0.0933684 | canonical_continuation_engine | offline_task385_continuation_engine | 0 | 0 | 1 | ENTRY_REDUCE_EXIT | -0.103368 |