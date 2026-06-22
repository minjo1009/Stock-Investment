# Task 366 - Explicit Continuation Event Instrumentation & Multi-Event Replay Dataset

## Core Answers
1. Can continuation now be represented as multi-event sequences? YES
2. Do event timelines now show persistence / sequential adds / scaling progression / reduction progression? YES
3. How often do HEALTHY_EXPANSION sequences survive long enough to scale? 0.176471
4. Can continuation now evolve HEALTHY -> NEUTRAL / HEALTHY -> FRAGILE / FRAGILE -> INVALIDATE over time? YES
5. What data is still missing before realistic continuation compounding research becomes possible? explicit multi-event setup identity from source data

## Core Metrics
| metric_name | metric_value |
| --- | --- |
| continuation_count | 217 |
| multi_event_continuation_count | 217 |
| max_event_count | 6 |
| avg_event_count | 2.21198 |
| sequential_add_count | 3 |
| scaling_progression_count | 3 |
| reduction_progression_count | 2 |
| persist_duration_positive_count | 21 |
| healthy_start_scale_rate | 0.176471 |
| healthy_to_neutral_count | 0 |
| healthy_to_fragile_count | 5 |
| fragile_to_invalidation_count | 121 |
| max_cumulative_add_count | 1 |

## Setup Identity Summary
| setup_type | intraday_match_status | setup_count | row_count | symbol_count |
| --- | --- | --- | --- | --- |
| unmatched_shadow_only | unmatched_shadow_only | 160 | 160 | 12 |
| breakout_timestamp | matched_master_pending_bars | 57 | 57 | 11 |

## Intraday Event Summary
| event_type | intraday_match_status | event_count | continuation_count |
| --- | --- | --- | --- |
| SETUP | unmatched_shadow_only | 160 | 160 |
| INVALIDATION | unmatched_shadow_only | 158 | 158 |
| SETUP | matched_session_bars | 57 | 57 |
| INVALIDATION | matched_session_bars | 38 | 38 |
| ADD_ATTEMPT | matched_session_bars | 19 | 19 |
| PROBE_ENTRY | matched_session_bars | 19 | 19 |
| PERSISTENCE_CONFIRMED | matched_session_bars | 18 | 18 |
| ADD_CONFIRMED | matched_session_bars | 3 | 3 |
| SIZE_INCREASE | matched_session_bars | 3 | 3 |
| PROBE_ENTRY | unmatched_shadow_only | 2 | 2 |
| PERSISTENCE_CONFIRMED | unmatched_shadow_only | 1 | 1 |
| REDUCTION_TRIGGER | matched_session_bars | 1 | 1 |
| REDUCTION_TRIGGER | unmatched_shadow_only | 1 | 1 |

## Event Timelines
| continuation_id | setup_id | symbol | first_timestamp | last_timestamp | persistence_duration_minutes | event_count | event_types |
| --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL|2021-06-14|setup_001|cont_001 | AAPL|2021-06-14|setup_001 | AAPL | 2021-06-14 14:30:00+00:00 | 2021-06-14 14:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | AAPL | 2021-08-16 14:30:00+00:00 | 2021-08-16 15:35:00+00:00 | 65 | 4 | PROBE_ENTRY|ADD_ATTEMPT|PERSISTENCE_CONFIRMED|SETUP |
| AAPL|2021-08-31|setup_001|cont_001 | AAPL|2021-08-31|setup_001 | AAPL | 2021-08-31 13:30:00+00:00 | 2021-08-31 13:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | AAPL | 2021-11-18 14:30:00+00:00 | 2021-11-18 17:25:00+00:00 | 175 | 6 | PROBE_ENTRY|ADD_ATTEMPT|ADD_CONFIRMED|SIZE_INCREASE|PERSISTENCE_CONFIRMED|SETUP |
| AAPL|2022-08-17|setup_001|cont_001 | AAPL|2022-08-17|setup_001 | AAPL | 2022-08-17 14:30:00+00:00 | 2022-08-17 14:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |
| AAPL|2023-07-21|setup_001|cont_001 | AAPL|2023-07-21|setup_001 | AAPL | 2023-07-21 14:30:00+00:00 | 2023-07-21 14:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |
| AAPL|2023-11-07|setup_001|cont_001 | AAPL|2023-11-07|setup_001 | AAPL | 2023-11-07 14:30:00+00:00 | 2023-11-07 14:35:00+00:00 | 0 | 2 | INVALIDATION|SETUP |
| AAPL|2023-12-05|setup_001|cont_001 | AAPL|2023-12-05|setup_001 | AAPL | 2023-12-05 14:30:00+00:00 | 2023-12-05 14:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |
| AAPL|2024-01-18|setup_001|cont_001 | AAPL|2024-01-18|setup_001 | AAPL | 2024-01-18 14:30:00+00:00 | 2024-01-18 14:55:00+00:00 | 0 | 2 | INVALIDATION|SETUP |
| AAPL|2024-03-21|setup_001|cont_001 | AAPL|2024-03-21|setup_001 | AAPL | 2024-03-21 14:30:00+00:00 | 2024-03-21 14:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |
| AAPL|2024-06-10|setup_001|cont_001 | AAPL|2024-06-10|setup_001 | AAPL | 2024-06-10 14:30:00+00:00 | 2024-06-10 14:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |
| AAPL|2025-06-30|setup_001|cont_001 | AAPL|2025-06-30|setup_001 | AAPL | 2025-06-30 14:30:00+00:00 | 2025-06-30 19:10:00+00:00 | 280 | 4 | PROBE_ENTRY|ADD_ATTEMPT|PERSISTENCE_CONFIRMED|SETUP |
| AAPL|2025-07-01|setup_001|cont_001 | AAPL|2025-07-01|setup_001 | AAPL | 2025-07-01 13:30:00+00:00 | 2025-07-01 13:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |
| AAPL|2026-04-17|setup_001|cont_001 | AAPL|2026-04-17|setup_001 | AAPL | 2026-04-17 14:30:00+00:00 | 2026-04-17 14:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |
| AMD|2021-06-17|setup_001|cont_001 | AMD|2021-06-17|setup_001 | AMD | 2021-06-17 14:30:00+00:00 | 2021-06-17 14:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |
| AMD|2021-07-27|setup_001|cont_001 | AMD|2021-07-27|setup_001 | AMD | 2021-07-27 14:30:00+00:00 | 2021-07-27 20:20:00+00:00 | 0 | 2 | INVALIDATION|SETUP |
| AMD|2021-07-28|setup_001|cont_001 | AMD|2021-07-28|setup_001 | AMD | 2021-07-28 13:00:00+00:00 | 2021-07-28 14:30:00+00:00 | 0 | 2 | INVALIDATION|SETUP |
| AMD|2021-10-13|setup_001|cont_001 | AMD|2021-10-13|setup_001 | AMD | 2021-10-13 14:30:00+00:00 | 2021-10-13 14:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |
| AMD|2023-01-09|setup_001|cont_001 | AMD|2023-01-09|setup_001 | AMD | 2023-01-09 14:30:00+00:00 | 2023-01-09 14:40:00+00:00 | 0 | 2 | INVALIDATION|SETUP |
| AMD|2023-03-07|setup_001|cont_001 | AMD|2023-03-07|setup_001 | AMD | 2023-03-07 14:30:00+00:00 | 2023-03-07 14:35:00+00:00 | 0 | 2 | INVALIDATION|SETUP |
| AMD|2023-06-13|setup_001|cont_001 | AMD|2023-06-13|setup_001 | AMD | 2023-06-13 14:30:00+00:00 | 2023-06-13 14:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |
| AMD|2023-12-07|setup_001|cont_001 | AMD|2023-12-07|setup_001 | AMD | 2023-12-07 14:30:00+00:00 | 2023-12-07 17:15:00+00:00 | 0 | 2 | INVALIDATION|SETUP |
| AMD|2024-01-16|setup_001|cont_001 | AMD|2024-01-16|setup_001 | AMD | 2024-01-16 14:30:00+00:00 | 2024-01-16 14:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |
| AMD|2024-05-16|setup_001|cont_001 | AMD|2024-05-16|setup_001 | AMD | 2024-05-16 14:30:00+00:00 | 2024-05-16 14:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |
| AMD|2024-07-05|setup_001|cont_001 | AMD|2024-07-05|setup_001 | AMD | 2024-07-05 14:30:00+00:00 | 2024-07-05 14:30:00+00:00 | 0 | 2 | SETUP|INVALIDATION |

## Exposure Evolution
| continuation_id | setup_id | timestamp | replay_state | current_size_multiplier | cumulative_add_count | persistence_duration_minutes | participation_quality_label | expansion_score | fragility_score | event_type | event_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL|2021-06-14|setup_001|cont_001 | AAPL|2021-06-14|setup_001 | 2021-06-14 14:30:00+00:00 | EXITED | 0 | 0 | 0 | FRAGILE_CROWDING | 0.443485 | 0.567863 | SETUP | AAPL|2021-06-14|setup_001|cont_001|event_001 |
| AAPL|2021-06-14|setup_001|cont_001 | AAPL|2021-06-14|setup_001 | 2021-06-14 14:30:00+00:00 | EXITED | 0 | 0 | 0 | FRAGILE_CROWDING | 0.443485 | 0.567863 | INVALIDATION | AAPL|2021-06-14|setup_001|cont_001|event_002 |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | 2021-08-16 14:30:00+00:00 | PROBE | 1 | 0 | 0 | HEALTHY_EXPANSION | 0.587636 | 0.440831 | PROBE_ENTRY | AAPL|2021-08-16|setup_001|cont_001|event_002 |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | 2021-08-16 14:35:00+00:00 | PROBE | 1 | 0 | 5 | HEALTHY_EXPANSION | 0.587636 | 0.440831 | ADD_ATTEMPT | AAPL|2021-08-16|setup_001|cont_001|event_003 |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | 2021-08-16 14:45:00+00:00 | PROBE | 1 | 0 | 15 | HEALTHY_EXPANSION | 0.587636 | 0.440831 | PERSISTENCE_CONFIRMED | AAPL|2021-08-16|setup_001|cont_001|event_004 |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | 2021-08-16 15:35:00+00:00 | PROBE | 0 | 0 | 65 | HEALTHY_EXPANSION | 0.587636 | 0.440831 | SETUP | AAPL|2021-08-16|setup_001|cont_001|event_001 |
| AAPL|2021-08-31|setup_001|cont_001 | AAPL|2021-08-31|setup_001 | 2021-08-31 13:30:00+00:00 | EXITED | 0 | 0 | 0 | HEALTHY_EXPANSION | 0.622028 | 0.36727 | SETUP | AAPL|2021-08-31|setup_001|cont_001|event_001 |
| AAPL|2021-08-31|setup_001|cont_001 | AAPL|2021-08-31|setup_001 | 2021-08-31 13:30:00+00:00 | EXITED | 0 | 0 | 0 | FRAGILE_CROWDING | 0.622028 | 0.36727 | INVALIDATION | AAPL|2021-08-31|setup_001|cont_001|event_002 |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:30:00+00:00 | PROBE | 0.25 | 0 | 0 | HEALTHY_EXPANSION | 0.661095 | 0.378514 | PROBE_ENTRY | AAPL|2021-11-18|setup_001|cont_001|event_002 |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:35:00+00:00 | PROBE | 0.25 | 0 | 5 | HEALTHY_EXPANSION | 0.661095 | 0.378514 | ADD_ATTEMPT | AAPL|2021-11-18|setup_001|cont_001|event_003 |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:40:00+00:00 | PROBE | 0.45 | 1 | 10 | HEALTHY_EXPANSION | 0.661095 | 0.378514 | ADD_CONFIRMED | AAPL|2021-11-18|setup_001|cont_001|event_004 |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:45:00+00:00 | PROBE | 0.75 | 1 | 15 | HEALTHY_EXPANSION | 0.661095 | 0.378514 | SIZE_INCREASE | AAPL|2021-11-18|setup_001|cont_001|event_005 |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 14:45:00+00:00 | PROBE | 0.75 | 1 | 15 | HEALTHY_EXPANSION | 0.661095 | 0.378514 | PERSISTENCE_CONFIRMED | AAPL|2021-11-18|setup_001|cont_001|event_006 |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | 2021-11-18 17:25:00+00:00 | PROBE | 0 | 1 | 175 | HEALTHY_EXPANSION | 0.661095 | 0.378514 | SETUP | AAPL|2021-11-18|setup_001|cont_001|event_001 |
| AAPL|2022-08-17|setup_001|cont_001 | AAPL|2022-08-17|setup_001 | 2022-08-17 14:30:00+00:00 | EXITED | 0 | 0 | 0 | FRAGILE_CROWDING | 0.438007 | 0.554163 | SETUP | AAPL|2022-08-17|setup_001|cont_001|event_001 |
| AAPL|2022-08-17|setup_001|cont_001 | AAPL|2022-08-17|setup_001 | 2022-08-17 14:30:00+00:00 | EXITED | 0 | 0 | 0 | FRAGILE_CROWDING | 0.438007 | 0.554163 | INVALIDATION | AAPL|2022-08-17|setup_001|cont_001|event_002 |
| AAPL|2023-07-21|setup_001|cont_001 | AAPL|2023-07-21|setup_001 | 2023-07-21 14:30:00+00:00 | EXITED | 0 | 0 | 0 | NEUTRAL_PARTICIPATION | 0.452177 | 0.480765 | SETUP | AAPL|2023-07-21|setup_001|cont_001|event_001 |
| AAPL|2023-07-21|setup_001|cont_001 | AAPL|2023-07-21|setup_001 | 2023-07-21 14:30:00+00:00 | EXITED | 0 | 0 | 0 | FRAGILE_CROWDING | 0.452177 | 0.480765 | INVALIDATION | AAPL|2023-07-21|setup_001|cont_001|event_002 |
| AAPL|2023-11-07|setup_001|cont_001 | AAPL|2023-11-07|setup_001 | 2023-11-07 14:30:00+00:00 | EXITED | 0 | 0 | 0 | FRAGILE_CROWDING | 0.478474 | 0.517838 | INVALIDATION | AAPL|2023-11-07|setup_001|cont_001|event_002 |
| AAPL|2023-11-07|setup_001|cont_001 | AAPL|2023-11-07|setup_001 | 2023-11-07 14:35:00+00:00 | EXITED | 0 | 0 | 0 | NEUTRAL_PARTICIPATION | 0.478474 | 0.517838 | SETUP | AAPL|2023-11-07|setup_001|cont_001|event_001 |
| AAPL|2023-12-05|setup_001|cont_001 | AAPL|2023-12-05|setup_001 | 2023-12-05 14:30:00+00:00 | EXITED | 0 | 0 | 0 | FRAGILE_CROWDING | 0.401025 | 0.525965 | SETUP | AAPL|2023-12-05|setup_001|cont_001|event_001 |
| AAPL|2023-12-05|setup_001|cont_001 | AAPL|2023-12-05|setup_001 | 2023-12-05 14:30:00+00:00 | EXITED | 0 | 0 | 0 | FRAGILE_CROWDING | 0.401025 | 0.525965 | INVALIDATION | AAPL|2023-12-05|setup_001|cont_001|event_002 |
| AAPL|2024-01-18|setup_001|cont_001 | AAPL|2024-01-18|setup_001 | 2024-01-18 14:30:00+00:00 | EXITED | 0 | 0 | 0 | FRAGILE_CROWDING | 0.493861 | 0.54131 | INVALIDATION | AAPL|2024-01-18|setup_001|cont_001|event_002 |
| AAPL|2024-01-18|setup_001|cont_001 | AAPL|2024-01-18|setup_001 | 2024-01-18 14:55:00+00:00 | EXITED | 0 | 0 | 0 | NEUTRAL_PARTICIPATION | 0.493861 | 0.54131 | SETUP | AAPL|2024-01-18|setup_001|cont_001|event_001 |
| AAPL|2024-03-21|setup_001|cont_001 | AAPL|2024-03-21|setup_001 | 2024-03-21 14:30:00+00:00 | EXITED | 0 | 0 | 0 | FRAGILE_CROWDING | 0.404623 | 0.530857 | SETUP | AAPL|2024-03-21|setup_001|cont_001|event_001 |