# Task 368 - Source-Truth Continuation Lineage Reconstruction

## Core Answers
1. How much continuation replay is now explicitly source-linked? 0.262673
2. Can continuation now be reconstructed as true multi-stage lineage? NO
3. Can add/scale progression now be linked to explicit setup lineage? YES
4. Can continuation persistence now be measured as true lineage evolution? YES
5. What is still missing before realistic continuation compounding research becomes possible? explicit setup identity from raw source data

## Replay Fidelity
| metric_name | metric_value |
| --- | --- |
| source_truth_lineage_share | 0.262673 |
| inferred_lineage_share | 0.737327 |
| multi_stage_lineage_share | 0.087558 |
| share_confidence_ge_0_80 | 0.262673 |
| share_add_or_scale_lineage | 0.013825 |
| replay_fidelity_score | 0.17788 |
| lineage_confidence_distribution::0.10-0.35 | 0.737327 |
| lineage_confidence_distribution::0.35-0.65 | 0 |
| lineage_confidence_distribution::0.65-0.80 | 0 |
| lineage_confidence_distribution::0.80-1.00 | 0.262673 |

## Setup Identity Summary
| setup_origin_type | setup_count | symbol_count | avg_setup_confidence |
| --- | --- | --- | --- |
| chronology_linked_setup | 160 | 12 | 0.6 |
| trade_linked_setup | 57 | 11 | 0.8 |

## Lineage Summary
| continuation_id | setup_id | symbol | lineage_confidence | lineage_quality | lineage_break_reason | source_truth_flag | event_count | distinct_lineage_event_type_count | final_add_depth | final_scale_depth | max_cumulative_size_multiplier | birth_timestamp | last_timestamp | persistence_duration_minutes | persistence_depth | fragility_transition_depth | invalidation_depth |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | AAPL | 1 | source_truth | timestamp_gap_break | True | 4 | 4 | 0 | 0 | 1 | 2021-08-16 14:30:00+00:00 | 2021-08-16 15:35:00+00:00 | 65 | 1 | 0 | 0 |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | AAPL | 1 | source_truth | timestamp_gap_break | True | 6 | 6 | 1 | 1 | 0.75 | 2021-11-18 14:30:00+00:00 | 2021-11-18 17:25:00+00:00 | 175 | 1 | 0 | 0 |
| AAPL|2023-11-07|setup_001|cont_001 | AAPL|2023-11-07|setup_001 | AAPL | 1 | source_truth | terminal_replay_break | True | 2 | 2 | 0 | 0 | 0 | 2023-11-07 14:35:00+00:00 | 2023-11-07 14:35:00+00:00 | 0 | 0 | 0 | 1 |
| AAPL|2024-01-18|setup_001|cont_001 | AAPL|2024-01-18|setup_001 | AAPL | 1 | source_truth | timestamp_gap_break | True | 2 | 2 | 0 | 0 | 0 | 2024-01-18 14:55:00+00:00 | 2024-01-18 14:55:00+00:00 | 0 | 0 | 0 | 1 |
| AAPL|2025-06-30|setup_001|cont_001 | AAPL|2025-06-30|setup_001 | AAPL | 1 | source_truth | timestamp_gap_break | True | 4 | 4 | 0 | 0 | 1 | 2025-06-30 14:30:00+00:00 | 2025-06-30 19:10:00+00:00 | 280 | 1 | 0 | 0 |
| AMD|2021-07-27|setup_001|cont_001 | AMD|2021-07-27|setup_001 | AMD | 1 | source_truth | timestamp_gap_break | True | 2 | 2 | 0 | 0 | 0 | 2021-07-27 20:20:00+00:00 | 2021-07-27 20:20:00+00:00 | 0 | 0 | 0 | 1 |
| AMD|2021-07-28|setup_001|cont_001 | AMD|2021-07-28|setup_001 | AMD | 1 | source_truth | timestamp_gap_break | True | 2 | 2 | 0 | 0 | 0 | 2021-07-28 14:30:00+00:00 | 2021-07-28 14:30:00+00:00 | 0 | 0 | 0 | 1 |
| AMD|2023-01-09|setup_001|cont_001 | AMD|2023-01-09|setup_001 | AMD | 1 | source_truth | terminal_replay_break | True | 2 | 2 | 0 | 0 | 0 | 2023-01-09 14:40:00+00:00 | 2023-01-09 14:40:00+00:00 | 0 | 0 | 0 | 1 |
| AMD|2023-03-07|setup_001|cont_001 | AMD|2023-03-07|setup_001 | AMD | 1 | source_truth | terminal_replay_break | True | 2 | 2 | 0 | 0 | 0 | 2023-03-07 14:35:00+00:00 | 2023-03-07 14:35:00+00:00 | 0 | 0 | 0 | 1 |
| AMD|2023-12-07|setup_001|cont_001 | AMD|2023-12-07|setup_001 | AMD | 1 | source_truth | timestamp_gap_break | True | 2 | 2 | 0 | 0 | 0 | 2023-12-07 17:15:00+00:00 | 2023-12-07 17:15:00+00:00 | 0 | 0 | 0 | 1 |
| AMD|2024-10-04|setup_001|cont_001 | AMD|2024-10-04|setup_001 | AMD | 1 | source_truth | timestamp_gap_break | True | 2 | 2 | 0 | 0 | 0 | 2024-10-04 17:05:00+00:00 | 2024-10-04 17:05:00+00:00 | 0 | 0 | 0 | 1 |
| AMD|2024-10-29|setup_001|cont_001 | AMD|2024-10-29|setup_001 | AMD | 1 | source_truth | timestamp_gap_break | True | 2 | 2 | 0 | 0 | 0 | 2024-10-29 16:35:00+00:00 | 2024-10-29 16:35:00+00:00 | 0 | 0 | 0 | 1 |
| AMD|2026-01-15|setup_001|cont_001 | AMD|2026-01-15|setup_001 | AMD | 1 | source_truth | terminal_replay_break | True | 2 | 2 | 0 | 0 | 0 | 2026-01-15 14:40:00+00:00 | 2026-01-15 14:40:00+00:00 | 0 | 0 | 0 | 1 |
| AMZN|2024-02-01|setup_001|cont_001 | AMZN|2024-02-01|setup_001 | AMZN | 1 | source_truth | terminal_replay_break | True | 2 | 2 | 0 | 0 | 0 | 2024-02-01 14:35:00+00:00 | 2024-02-01 14:35:00+00:00 | 0 | 0 | 0 | 1 |
| AMZN|2025-06-05|setup_001|cont_001 | AMZN|2025-06-05|setup_001 | AMZN | 1 | source_truth | none | True | 4 | 4 | 0 | 0 | 1 | 2025-06-05 14:30:00+00:00 | 2025-06-05 14:45:00+00:00 | 15 | 1 | 0 | 0 |
| AVGO|2024-12-06|setup_001|cont_001 | AVGO|2024-12-06|setup_001 | AVGO | 1 | source_truth | timestamp_gap_break | True | 2 | 2 | 0 | 0 | 0 | 2024-12-06 16:55:00+00:00 | 2024-12-06 16:55:00+00:00 | 0 | 0 | 0 | 1 |
| COST|2021-10-29|setup_001|cont_001 | COST|2021-10-29|setup_001 | COST | 1 | source_truth | timestamp_gap_break | True | 4 | 4 | 0 | 0 | 0.75 | 2021-10-29 14:30:00+00:00 | 2021-10-29 15:15:00+00:00 | 45 | 1 | 0 | 0 |
| COST|2022-03-03|setup_001|cont_001 | COST|2022-03-03|setup_001 | COST | 1 | source_truth | terminal_replay_break | True | 2 | 2 | 0 | 0 | 0 | 2022-03-03 14:35:00+00:00 | 2022-03-03 14:35:00+00:00 | 0 | 0 | 0 | 1 |
| COST|2022-03-07|setup_001|cont_001 | COST|2022-03-07|setup_001 | COST | 1 | source_truth | timestamp_gap_break | True | 2 | 2 | 0 | 0 | 0 | 2022-03-07 15:35:00+00:00 | 2022-03-07 15:35:00+00:00 | 0 | 0 | 0 | 1 |
| COST|2022-06-02|setup_001|cont_001 | COST|2022-06-02|setup_001 | COST | 1 | source_truth | timestamp_gap_break | True | 2 | 2 | 0 | 0 | 0 | 2022-06-02 16:35:00+00:00 | 2022-06-02 16:35:00+00:00 | 0 | 0 | 0 | 1 |
| COST|2022-08-16|setup_001|cont_001 | COST|2022-08-16|setup_001 | COST | 1 | source_truth | none | True | 4 | 4 | 0 | 0 | 1 | 2022-08-16 14:30:00+00:00 | 2022-08-16 14:55:00+00:00 | 25 | 1 | 0 | 0 |
| COST|2023-05-26|setup_001|cont_001 | COST|2023-05-26|setup_001 | COST | 1 | source_truth | timestamp_gap_break | True | 6 | 6 | 1 | 1 | 0.4 | 2023-05-26 14:30:00+00:00 | 2023-05-26 17:40:00+00:00 | 190 | 1 | 0 | 0 |
| COST|2023-09-28|setup_001|cont_001 | COST|2023-09-28|setup_001 | COST | 1 | source_truth | timestamp_gap_break | True | 2 | 2 | 0 | 0 | 0 | 2023-09-28 14:55:00+00:00 | 2023-09-28 14:55:00+00:00 | 0 | 0 | 0 | 1 |
| COST|2023-11-06|setup_001|cont_001 | COST|2023-11-06|setup_001 | COST | 1 | source_truth | terminal_replay_break | True | 2 | 2 | 0 | 0 | 0 | 2023-11-06 14:45:00+00:00 | 2023-11-06 14:45:00+00:00 | 0 | 0 | 0 | 1 |
| COST|2024-11-07|setup_001|cont_001 | COST|2024-11-07|setup_001 | COST | 1 | source_truth | terminal_replay_break | True | 2 | 2 | 0 | 0 | 0 | 2024-11-07 14:50:00+00:00 | 2024-11-07 14:50:00+00:00 | 0 | 0 | 0 | 1 |

## Add/Scale Evolution
| continuation_id | setup_id | timestamp | event_id | lineage_event_type | add_depth | scale_depth | cumulative_size_multiplier | replay_state | has_add_attempt | has_add_confirmed | has_scale_up | add_linked_to_setup | scale_linked_to_add |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL|2021-06-14|setup_001|cont_001 | AAPL|2021-06-14|setup_001 | 2021-06-14 14:30:00+00:00 | AAPL|2021-06-14|setup_001|cont_001|event_001 | SETUP_DETECTED | 0 | 0 | 0 | EXITED | False | False | False | False | False |
| AAPL|2021-06-14|setup_001|cont_001 | AAPL|2021-06-14|setup_001 | 2021-06-14 14:30:00+00:00 | AAPL|2021-06-14|setup_001|cont_001|event_002 | INVALIDATION | 0 | 0 | 0 | EXITED | False | False | False | False | False |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | 2021-08-16 14:30:00+00:00 | AAPL|2021-08-16|setup_001|cont_001|event_002 | PROBE_ENTRY | 0 | 0 | 1 | PROBE | False | False | False | False | False |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | 2021-08-16 14:35:00+00:00 | AAPL|2021-08-16|setup_001|cont_001|event_003 | ADD_ATTEMPT | 0 | 0 | 1 | PROBE | True | False | False | False | False |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | 2021-08-16 14:45:00+00:00 | AAPL|2021-08-16|setup_001|cont_001|event_004 | PERSISTENCE_CONFIRMED | 0 | 0 | 1 | PROBE | True | False | False | False | False |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | 2021-08-16 15:35:00+00:00 | AAPL|2021-08-16|setup_001|cont_001|event_001 | SETUP_DETECTED | 0 | 0 | 0 | PROBE | True | False | False | False | False |
| AAPL|2021-08-31|setup_001|cont_001 | AAPL|2021-08-31|setup_001 | 2021-08-31 13:30:00+00:00 | AAPL|2021-08-31|setup_001|cont_001|event_001 | SETUP_DETECTED | 0 | 0 | 0 | EXITED | False | False | False | False | False |
| AAPL|2021-08-31|setup_001|cont_001 | AAPL|2021-08-31|setup_001 | 2021-08-31 13:30:00+00:00 | AAPL|2021-08-31|setup_001|cont_001|event_002 | INVALIDATION | 0 | 0 | 0 | EXITED | False | False | False | False | False |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:30:00+00:00 | AAPL|2021-11-18|setup_001|cont_001|event_002 | PROBE_ENTRY | 0 | 0 | 0.25 | PROBE | False | False | False | False | False |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:35:00+00:00 | AAPL|2021-11-18|setup_001|cont_001|event_003 | ADD_ATTEMPT | 0 | 0 | 0.25 | PROBE | True | False | False | False | False |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:40:00+00:00 | AAPL|2021-11-18|setup_001|cont_001|event_004 | ADD_CONFIRMED | 1 | 0 | 0.45 | PROBE | True | True | False | True | False |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:45:00+00:00 | AAPL|2021-11-18|setup_001|cont_001|event_005 | SIZE_INCREASE | 1 | 1 | 0.75 | PROBE | True | True | True | True | True |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:45:00+00:00 | AAPL|2021-11-18|setup_001|cont_001|event_006 | PERSISTENCE_CONFIRMED | 1 | 1 | 0.75 | PROBE | True | True | True | True | True |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 17:25:00+00:00 | AAPL|2021-11-18|setup_001|cont_001|event_001 | SETUP_DETECTED | 1 | 1 | 0 | PROBE | True | True | True | True | True |
| AAPL|2022-08-17|setup_001|cont_001 | AAPL|2022-08-17|setup_001 | 2022-08-17 14:30:00+00:00 | AAPL|2022-08-17|setup_001|cont_001|event_001 | SETUP_DETECTED | 0 | 0 | 0 | EXITED | False | False | False | False | False |
| AAPL|2022-08-17|setup_001|cont_001 | AAPL|2022-08-17|setup_001 | 2022-08-17 14:30:00+00:00 | AAPL|2022-08-17|setup_001|cont_001|event_002 | INVALIDATION | 0 | 0 | 0 | EXITED | False | False | False | False | False |
| AAPL|2023-07-21|setup_001|cont_001 | AAPL|2023-07-21|setup_001 | 2023-07-21 14:30:00+00:00 | AAPL|2023-07-21|setup_001|cont_001|event_001 | SETUP_DETECTED | 0 | 0 | 0 | EXITED | False | False | False | False | False |
| AAPL|2023-07-21|setup_001|cont_001 | AAPL|2023-07-21|setup_001 | 2023-07-21 14:30:00+00:00 | AAPL|2023-07-21|setup_001|cont_001|event_002 | INVALIDATION | 0 | 0 | 0 | EXITED | False | False | False | False | False |
| AAPL|2023-11-07|setup_001|cont_001 | AAPL|2023-11-07|setup_001 | 2023-11-07 14:30:00+00:00 | AAPL|2023-11-07|setup_001|cont_001|event_002 | INVALIDATION | 0 | 0 | 0 | EXITED | False | False | False | False | False |
| AAPL|2023-11-07|setup_001|cont_001 | AAPL|2023-11-07|setup_001 | 2023-11-07 14:35:00+00:00 | AAPL|2023-11-07|setup_001|cont_001|event_001 | SETUP_DETECTED | 0 | 0 | 0 | EXITED | False | False | False | False | False |
| AAPL|2023-12-05|setup_001|cont_001 | AAPL|2023-12-05|setup_001 | 2023-12-05 14:30:00+00:00 | AAPL|2023-12-05|setup_001|cont_001|event_001 | SETUP_DETECTED | 0 | 0 | 0 | EXITED | False | False | False | False | False |
| AAPL|2023-12-05|setup_001|cont_001 | AAPL|2023-12-05|setup_001 | 2023-12-05 14:30:00+00:00 | AAPL|2023-12-05|setup_001|cont_001|event_002 | INVALIDATION | 0 | 0 | 0 | EXITED | False | False | False | False | False |
| AAPL|2024-01-18|setup_001|cont_001 | AAPL|2024-01-18|setup_001 | 2024-01-18 14:30:00+00:00 | AAPL|2024-01-18|setup_001|cont_001|event_002 | INVALIDATION | 0 | 0 | 0 | EXITED | False | False | False | False | False |
| AAPL|2024-01-18|setup_001|cont_001 | AAPL|2024-01-18|setup_001 | 2024-01-18 14:55:00+00:00 | AAPL|2024-01-18|setup_001|cont_001|event_001 | SETUP_DETECTED | 0 | 0 | 0 | EXITED | False | False | False | False | False |
| AAPL|2024-03-21|setup_001|cont_001 | AAPL|2024-03-21|setup_001 | 2024-03-21 14:30:00+00:00 | AAPL|2024-03-21|setup_001|cont_001|event_001 | SETUP_DETECTED | 0 | 0 | 0 | EXITED | False | False | False | False | False |

## Persistence Timeline
| continuation_id | setup_id | timestamp | lineage_event_type | birth_timestamp | last_timestamp | persistence_duration_minutes | persistence_depth | fragility_transition_depth | invalidation_depth |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL|2021-06-14|setup_001|cont_001 | AAPL|2021-06-14|setup_001 | 2021-06-14 14:30:00+00:00 | INVALIDATION | 2021-06-14 14:30:00+00:00 | 2021-06-14 14:30:00+00:00 | 0 | 0 | 0 | 2 |
| AAPL|2021-06-14|setup_001|cont_001 | AAPL|2021-06-14|setup_001 | 2021-06-14 14:30:00+00:00 | SETUP_DETECTED | 2021-06-14 14:30:00+00:00 | 2021-06-14 14:30:00+00:00 | 0 | 0 | 0 | 0 |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | 2021-08-16 14:30:00+00:00 | PROBE_ENTRY | 2021-08-16 14:30:00+00:00 | 2021-08-16 15:35:00+00:00 | 0 | 0 | 0 | 0 |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | 2021-08-16 14:35:00+00:00 | ADD_ATTEMPT | 2021-08-16 14:30:00+00:00 | 2021-08-16 15:35:00+00:00 | 5 | 0 | 0 | 0 |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | 2021-08-16 14:45:00+00:00 | PERSISTENCE_CONFIRMED | 2021-08-16 14:30:00+00:00 | 2021-08-16 15:35:00+00:00 | 15 | 1 | 0 | 0 |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | 2021-08-16 15:35:00+00:00 | SETUP_DETECTED | 2021-08-16 14:30:00+00:00 | 2021-08-16 15:35:00+00:00 | 65 | 1 | 0 | 0 |
| AAPL|2021-08-31|setup_001|cont_001 | AAPL|2021-08-31|setup_001 | 2021-08-31 13:30:00+00:00 | INVALIDATION | 2021-08-31 13:30:00+00:00 | 2021-08-31 13:30:00+00:00 | 0 | 0 | 0 | 2 |
| AAPL|2021-08-31|setup_001|cont_001 | AAPL|2021-08-31|setup_001 | 2021-08-31 13:30:00+00:00 | SETUP_DETECTED | 2021-08-31 13:30:00+00:00 | 2021-08-31 13:30:00+00:00 | 0 | 0 | 0 | 0 |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:30:00+00:00 | PROBE_ENTRY | 2021-11-18 14:30:00+00:00 | 2021-11-18 17:25:00+00:00 | 0 | 0 | 0 | 0 |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:35:00+00:00 | ADD_ATTEMPT | 2021-11-18 14:30:00+00:00 | 2021-11-18 17:25:00+00:00 | 5 | 0 | 0 | 0 |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:40:00+00:00 | ADD_CONFIRMED | 2021-11-18 14:30:00+00:00 | 2021-11-18 17:25:00+00:00 | 10 | 0 | 0 | 0 |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:45:00+00:00 | PERSISTENCE_CONFIRMED | 2021-11-18 14:30:00+00:00 | 2021-11-18 17:25:00+00:00 | 15 | 1 | 0 | 0 |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:45:00+00:00 | SIZE_INCREASE | 2021-11-18 14:30:00+00:00 | 2021-11-18 17:25:00+00:00 | 15 | 0 | 0 | 0 |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 17:25:00+00:00 | SETUP_DETECTED | 2021-11-18 14:30:00+00:00 | 2021-11-18 17:25:00+00:00 | 175 | 1 | 0 | 0 |
| AAPL|2022-08-17|setup_001|cont_001 | AAPL|2022-08-17|setup_001 | 2022-08-17 14:30:00+00:00 | INVALIDATION | 2022-08-17 14:30:00+00:00 | 2022-08-17 14:30:00+00:00 | 0 | 0 | 0 | 2 |
| AAPL|2022-08-17|setup_001|cont_001 | AAPL|2022-08-17|setup_001 | 2022-08-17 14:30:00+00:00 | SETUP_DETECTED | 2022-08-17 14:30:00+00:00 | 2022-08-17 14:30:00+00:00 | 0 | 0 | 0 | 0 |
| AAPL|2023-07-21|setup_001|cont_001 | AAPL|2023-07-21|setup_001 | 2023-07-21 14:30:00+00:00 | INVALIDATION | 2023-07-21 14:30:00+00:00 | 2023-07-21 14:30:00+00:00 | 0 | 0 | 0 | 2 |
| AAPL|2023-07-21|setup_001|cont_001 | AAPL|2023-07-21|setup_001 | 2023-07-21 14:30:00+00:00 | SETUP_DETECTED | 2023-07-21 14:30:00+00:00 | 2023-07-21 14:30:00+00:00 | 0 | 0 | 0 | 0 |
| AAPL|2023-11-07|setup_001|cont_001 | AAPL|2023-11-07|setup_001 | 2023-11-07 14:30:00+00:00 | INVALIDATION | 2023-11-07 14:35:00+00:00 | 2023-11-07 14:35:00+00:00 | 0 | 0 | 0 | 1 |
| AAPL|2023-11-07|setup_001|cont_001 | AAPL|2023-11-07|setup_001 | 2023-11-07 14:35:00+00:00 | SETUP_DETECTED | 2023-11-07 14:35:00+00:00 | 2023-11-07 14:35:00+00:00 | 0 | 0 | 0 | 1 |
| AAPL|2023-12-05|setup_001|cont_001 | AAPL|2023-12-05|setup_001 | 2023-12-05 14:30:00+00:00 | INVALIDATION | 2023-12-05 14:30:00+00:00 | 2023-12-05 14:30:00+00:00 | 0 | 0 | 0 | 2 |
| AAPL|2023-12-05|setup_001|cont_001 | AAPL|2023-12-05|setup_001 | 2023-12-05 14:30:00+00:00 | SETUP_DETECTED | 2023-12-05 14:30:00+00:00 | 2023-12-05 14:30:00+00:00 | 0 | 0 | 0 | 0 |
| AAPL|2024-01-18|setup_001|cont_001 | AAPL|2024-01-18|setup_001 | 2024-01-18 14:30:00+00:00 | INVALIDATION | 2024-01-18 14:55:00+00:00 | 2024-01-18 14:55:00+00:00 | 0 | 0 | 0 | 1 |
| AAPL|2024-01-18|setup_001|cont_001 | AAPL|2024-01-18|setup_001 | 2024-01-18 14:55:00+00:00 | SETUP_DETECTED | 2024-01-18 14:55:00+00:00 | 2024-01-18 14:55:00+00:00 | 0 | 0 | 0 | 1 |
| AAPL|2024-03-21|setup_001|cont_001 | AAPL|2024-03-21|setup_001 | 2024-03-21 14:30:00+00:00 | INVALIDATION | 2024-03-21 14:30:00+00:00 | 2024-03-21 14:30:00+00:00 | 0 | 0 | 0 | 2 |