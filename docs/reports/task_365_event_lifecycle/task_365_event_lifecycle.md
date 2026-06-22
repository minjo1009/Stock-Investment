# Task 365 - Event-Level Continuation Lifecycle Enrichment

## Core Answers
1. Can continuation now be represented as linked event chains rather than isolated rows? NO
2. Do healthy continuation sequences now show probe / add / persistence / scale behavior? NO
3. How often does HEALTHY_EXPANSION evolve into FRAGILE_CROWDING? 0.0
4. Can continuation persistence now be measured across time? NO
5. What data is still missing before realistic continuation compounding research becomes possible? explicit multi-event setup identity

## Chain Summary Metrics
| metric_name | metric_value |
| --- | --- |
| avg_event_chain_length | 1 |
| avg_adds_per_chain | 0 |
| probe_to_add_rate | 0 |
| add_to_scale_rate | 0 |
| persist_duration | 0 |
| healthy_to_fragile_transition_rate | 0 |
| avg_size_growth | 0.144055 |
| invalidation_rate | 0.903226 |
| chains_with_persist | 0 |

## Event Chains
| continuation_id | symbol | session_date | event_index | event_type | timestamp | trade_id | signal_id | replay_state | participation_quality_label | state_label | size_multiplier | add_activated | transition_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL|2021-06-14 | AAPL | 2021-06-14 | 1 | INVALIDATE | 2021-06-14 00:00:00+00:00 | AAPL|2021-06-14|2021-06-14|128.460007 | 3 | EXITED | FRAGILE_CROWDING | DISLOCATION | 0.07 | False | dislocation_exit |
| AAPL|2021-08-16 | AAPL | 2021-08-16 | 1 | PROBE_ENTRY | 2021-08-16 00:00:00+00:00 | AAPL|2021-08-16|2021-08-16|148.039993 | 1539 | PROBE | HEALTHY_EXPANSION | NORMAL | 1 | False | initial_live_probe |
| AAPL|2021-08-31 | AAPL | 2021-08-31 | 1 | INVALIDATE | 2021-08-31 00:00:00+00:00 | AAPL|2021-08-31|2021-08-31|150.860001 | 1542 | EXITED | HEALTHY_EXPANSION | DISLOCATION | 0.07 | False | dislocation_exit |
| AAPL|2021-11-18 | AAPL | 2021-11-18 | 1 | PROBE_ENTRY | 2021-11-18 00:00:00+00:00 | AAPL|2021-11-18|2021-11-18|155.000000 | 25 | PROBE | HEALTHY_EXPANSION | ELEVATED | 0.75 | True | initial_live_probe |
| AAPL|2022-08-17 | AAPL | 2022-08-17 | 1 | INVALIDATE | 2022-08-17 00:00:00+00:00 | AAPL|2022-08-17|2022-08-17|173.710007 | 38 | EXITED | FRAGILE_CROWDING | DISLOCATION | 0.07 | False | dislocation_exit |
| AAPL|2023-07-21 | AAPL | 2023-07-21 | 1 | INVALIDATE | 2023-07-21 00:00:00+00:00 | AAPL|2023-07-21|2023-07-21|194.479996 | 1616 | EXITED | NEUTRAL_PARTICIPATION | DISLOCATION | 0.07 | False | dislocation_exit |
| AAPL|2023-11-07 | AAPL | 2023-11-07 | 1 | INVALIDATE | 2023-11-07 00:00:00+00:00 | AAPL|2023-11-07|2023-11-07|179.429993 | 86 | EXITED | NEUTRAL_PARTICIPATION | DISLOCATION | 0.07 | False | dislocation_exit |
| AAPL|2023-12-05 | AAPL | 2023-12-05 | 1 | INVALIDATE | 2023-12-05 00:00:00+00:00 | AAPL|2023-12-05|2023-12-05|192.089996 | 1637 | EXITED | FRAGILE_CROWDING | DISLOCATION | 0.07 | False | dislocation_exit |
| AAPL|2024-01-18 | AAPL | 2024-01-18 | 1 | INVALIDATE | 2024-01-18 00:00:00+00:00 | AAPL|2024-01-18|2024-01-18|187.050003 | 287 | EXITED | NEUTRAL_PARTICIPATION | DISLOCATION | 0.07 | False | dislocation_exit |
| AAPL|2024-03-21 | AAPL | 2024-03-21 | 1 | INVALIDATE | 2024-03-21 00:00:00+00:00 | AAPL|2024-03-21|2024-03-21|174.380005 | 1651 | EXITED | FRAGILE_CROWDING | DISLOCATION | 0.07 | False | dislocation_exit |
| AAPL|2024-06-10 | AAPL | 2024-06-10 | 1 | INVALIDATE | 2024-06-10 00:00:00+00:00 | AAPL|2024-06-10|2024-06-10|196.940002 | 102 | EXITED | NEUTRAL_PARTICIPATION | DISLOCATION | 0.07 | False | dislocation_exit |
| AAPL|2025-06-30 | AAPL | 2025-06-30 | 1 | PROBE_ENTRY | 2025-06-30 00:00:00+00:00 | AAPL|2025-06-30|2025-06-30|203.669998 | 343 | PROBE | NEUTRAL_PARTICIPATION | NORMAL | 1 | False | initial_live_probe |
| AAPL|2025-07-01 | AAPL | 2025-07-01 | 1 | INVALIDATE | 2025-07-01 00:00:00+00:00 | AAPL|2025-07-01|2025-07-01|206.240005 | 1707 | EXITED | NEUTRAL_PARTICIPATION | DISLOCATION | 0.07 | False | dislocation_exit |
| AAPL|2026-04-17 | AAPL | 2026-04-17 | 1 | INVALIDATE | 2026-04-17 00:00:00+00:00 | AAPL|2026-04-17|2026-04-17|262.160004 | 1748 | EXITED | FRAGILE_CROWDING | DISLOCATION | 0.07 | False | dislocation_exit |
| AMD|2021-06-17 | AMD | 2021-06-17 | 1 | INVALIDATE | 2021-06-17 00:00:00+00:00 | AMD|2021-06-17|2021-06-17|82.650002 | 0 | EXITED | FRAGILE_CROWDING | DISLOCATION | 0.07 | False | dislocation_exit |
| AMD|2021-07-27 | AMD | 2021-07-27 | 1 | INVALIDATE | 2021-07-27 00:00:00+00:00 | AMD|2021-07-27|2021-07-27|92.750000 | 5 | EXITED | NEUTRAL_PARTICIPATION | DISLOCATION | 0.07 | False | dislocation_exit |
| AMD|2021-07-28 | AMD | 2021-07-28 | 1 | INVALIDATE | 2021-07-28 00:00:00+00:00 | AMD|2021-07-28|2021-07-28|94.099998 | 8 | EXITED | HEALTHY_EXPANSION | DISLOCATION | 0.07 | False | dislocation_exit |
| AMD|2021-10-13 | AMD | 2021-10-13 | 1 | INVALIDATE | 2021-10-13 00:00:00+00:00 | AMD|2021-10-13|2021-10-13|107.949997 | 21 | EXITED | FRAGILE_CROWDING | DISLOCATION | 0.07 | False | dislocation_exit |
| AMD|2023-01-09 | AMD | 2023-01-09 | 1 | INVALIDATE | 2023-01-09 00:00:00+00:00 | AMD|2023-01-09|2023-01-09|66.879997 | 50 | EXITED | FRAGILE_CROWDING | DISLOCATION | 0.07 | False | dislocation_exit |
| AMD|2023-03-07 | AMD | 2023-03-07 | 1 | INVALIDATE | 2023-03-07 00:00:00+00:00 | AMD|2023-03-07|2023-03-07|81.790001 | 1598 | EXITED | FRAGILE_CROWDING | DISLOCATION | 0.07 | False | dislocation_exit |
| AMD|2023-06-13 | AMD | 2023-06-13 | 1 | INVALIDATE | 2023-06-13 00:00:00+00:00 | AMD|2023-06-13|2023-06-13|130.789993 | 458 | EXITED | NEUTRAL_PARTICIPATION | DISLOCATION | 0.07 | False | dislocation_exit |
| AMD|2023-12-07 | AMD | 2023-12-07 | 1 | INVALIDATE | 2023-12-07 00:00:00+00:00 | AMD|2023-12-07|2023-12-07|125.730003 | 87 | EXITED | NEUTRAL_PARTICIPATION | DISLOCATION | 0.07 | False | dislocation_exit |
| AMD|2024-01-16 | AMD | 2024-01-16 | 1 | INVALIDATE | 2024-01-16 00:00:00+00:00 | AMD|2024-01-16|2024-01-16|151.050003 | 94 | EXITED | FRAGILE_CROWDING | DISLOCATION | 0.07 | False | dislocation_exit |
| AMD|2024-05-16 | AMD | 2024-05-16 | 1 | INVALIDATE | 2024-05-16 00:00:00+00:00 | AMD|2024-05-16|2024-05-16|157.699997 | 1659 | EXITED | FRAGILE_CROWDING | DISLOCATION | 0.07 | False | dislocation_exit |
| AMD|2024-07-05 | AMD | 2024-07-05 | 1 | INVALIDATE | 2024-07-05 00:00:00+00:00 | AMD|2024-07-05|2024-07-05|166.449997 | 1886 | EXITED | NEUTRAL_PARTICIPATION | DISLOCATION | 0.07 | False | dislocation_exit |

## Event Transitions
| continuation_id | event_index | event_type | replay_state_transition | transition_reason |
| --- | --- | --- | --- | --- |
| AAPL|2021-06-14 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AAPL|2021-08-16 | 1 | PROBE_ENTRY | NONE->PROBE | initial_live_probe |
| AAPL|2021-08-31 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AAPL|2021-11-18 | 1 | PROBE_ENTRY | NONE->PROBE | initial_live_probe |
| AAPL|2022-08-17 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AAPL|2023-07-21 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AAPL|2023-11-07 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AAPL|2023-12-05 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AAPL|2024-01-18 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AAPL|2024-03-21 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AAPL|2024-06-10 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AAPL|2025-06-30 | 1 | PROBE_ENTRY | NONE->PROBE | initial_live_probe |
| AAPL|2025-07-01 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AAPL|2026-04-17 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AMD|2021-06-17 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AMD|2021-07-27 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AMD|2021-07-28 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AMD|2021-10-13 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AMD|2023-01-09 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AMD|2023-03-07 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AMD|2023-06-13 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AMD|2023-12-07 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AMD|2024-01-16 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AMD|2024-05-16 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |
| AMD|2024-07-05 | 1 | INVALIDATE | NONE->EXITED | dislocation_exit |

## Quality Evolution
| continuation_id | event_index | participation_quality_label | expansion_score | fragility_score | participation_quality_transition |
| --- | --- | --- | --- | --- | --- |
| AAPL|2021-06-14 | 1 | FRAGILE_CROWDING | 0.443485 | 0.567863 | NONE->FRAGILE_CROWDING |
| AAPL|2021-08-16 | 1 | HEALTHY_EXPANSION | 0.587636 | 0.440831 | NONE->HEALTHY_EXPANSION |
| AAPL|2021-08-31 | 1 | HEALTHY_EXPANSION | 0.622028 | 0.36727 | NONE->HEALTHY_EXPANSION |
| AAPL|2021-11-18 | 1 | HEALTHY_EXPANSION | 0.661095 | 0.378514 | NONE->HEALTHY_EXPANSION |
| AAPL|2022-08-17 | 1 | FRAGILE_CROWDING | 0.438007 | 0.554163 | NONE->FRAGILE_CROWDING |
| AAPL|2023-07-21 | 1 | NEUTRAL_PARTICIPATION | 0.452177 | 0.480765 | NONE->NEUTRAL_PARTICIPATION |
| AAPL|2023-11-07 | 1 | NEUTRAL_PARTICIPATION | 0.478474 | 0.517838 | NONE->NEUTRAL_PARTICIPATION |
| AAPL|2023-12-05 | 1 | FRAGILE_CROWDING | 0.401025 | 0.525965 | NONE->FRAGILE_CROWDING |
| AAPL|2024-01-18 | 1 | NEUTRAL_PARTICIPATION | 0.493861 | 0.54131 | NONE->NEUTRAL_PARTICIPATION |
| AAPL|2024-03-21 | 1 | FRAGILE_CROWDING | 0.404623 | 0.530857 | NONE->FRAGILE_CROWDING |
| AAPL|2024-06-10 | 1 | NEUTRAL_PARTICIPATION | 0.463153 | 0.533971 | NONE->NEUTRAL_PARTICIPATION |
| AAPL|2025-06-30 | 1 | NEUTRAL_PARTICIPATION | 0.451898 | 0.506344 | NONE->NEUTRAL_PARTICIPATION |
| AAPL|2025-07-01 | 1 | NEUTRAL_PARTICIPATION | 0.469744 | 0.472526 | NONE->NEUTRAL_PARTICIPATION |
| AAPL|2026-04-17 | 1 | FRAGILE_CROWDING | 0.405141 | 0.57808 | NONE->FRAGILE_CROWDING |
| AMD|2021-06-17 | 1 | FRAGILE_CROWDING | 0.409175 | 0.615608 | NONE->FRAGILE_CROWDING |
| AMD|2021-07-27 | 1 | NEUTRAL_PARTICIPATION | 0.547957 | 0.489188 | NONE->NEUTRAL_PARTICIPATION |
| AMD|2021-07-28 | 1 | HEALTHY_EXPANSION | 0.579976 | 0.434181 | NONE->HEALTHY_EXPANSION |
| AMD|2021-10-13 | 1 | FRAGILE_CROWDING | 0.313263 | 0.682438 | NONE->FRAGILE_CROWDING |
| AMD|2023-01-09 | 1 | FRAGILE_CROWDING | 0.339313 | 0.656228 | NONE->FRAGILE_CROWDING |
| AMD|2023-03-07 | 1 | FRAGILE_CROWDING | 0.349412 | 0.651031 | NONE->FRAGILE_CROWDING |
| AMD|2023-06-13 | 1 | NEUTRAL_PARTICIPATION | 0.453079 | 0.493159 | NONE->NEUTRAL_PARTICIPATION |
| AMD|2023-12-07 | 1 | NEUTRAL_PARTICIPATION | 0.513485 | 0.48217 | NONE->NEUTRAL_PARTICIPATION |
| AMD|2024-01-16 | 1 | FRAGILE_CROWDING | 0.448721 | 0.552419 | NONE->FRAGILE_CROWDING |
| AMD|2024-05-16 | 1 | FRAGILE_CROWDING | 0.411152 | 0.567262 | NONE->FRAGILE_CROWDING |
| AMD|2024-07-05 | 1 | NEUTRAL_PARTICIPATION | 0.47093 | 0.464365 | NONE->NEUTRAL_PARTICIPATION |

## Size Evolution
| continuation_id | event_index | event_type | size_multiplier | size_multiplier_delta | add_path_transition |
| --- | --- | --- | --- | --- | --- |
| AAPL|2021-06-14 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AAPL|2021-08-16 | 1 | PROBE_ENTRY | 1 | 1 | closed_to_closed |
| AAPL|2021-08-31 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AAPL|2021-11-18 | 1 | PROBE_ENTRY | 0.75 | 0.75 | closed_to_open |
| AAPL|2022-08-17 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AAPL|2023-07-21 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AAPL|2023-11-07 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AAPL|2023-12-05 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AAPL|2024-01-18 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AAPL|2024-03-21 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AAPL|2024-06-10 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AAPL|2025-06-30 | 1 | PROBE_ENTRY | 1 | 1 | closed_to_closed |
| AAPL|2025-07-01 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AAPL|2026-04-17 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AMD|2021-06-17 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AMD|2021-07-27 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AMD|2021-07-28 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AMD|2021-10-13 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AMD|2023-01-09 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AMD|2023-03-07 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AMD|2023-06-13 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AMD|2023-12-07 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AMD|2024-01-16 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AMD|2024-05-16 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |
| AMD|2024-07-05 | 1 | INVALIDATE | 0.07 | 0.07 | closed_to_closed |

## Exit Reasons
| exit_reason | chain_count |
| --- | --- |
| dislocation_exit | 196 |
|  | 21 |

## Chain Summary
| continuation_id | symbol | session_date | first_setup_timestamp | probe_timestamp | first_add_timestamp | first_scale_timestamp | first_reduce_timestamp | exit_timestamp | persistence_duration_events | event_count | max_size_multiplier | avg_size_multiplier | healthy_event_count | fragile_event_count | invalidated | exit_reason |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL|2021-06-14 | AAPL | 2021-06-14 | NaT | NaT | NaT | NaT | NaT | 2021-06-14 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 1 | True | dislocation_exit |
| AAPL|2021-08-16 | AAPL | 2021-08-16 | NaT | 2021-08-16 00:00:00+00:00 | NaT | NaT | NaT | NaT | 0 | 1 | 1 | 1 | 1 | 0 | False |  |
| AAPL|2021-08-31 | AAPL | 2021-08-31 | NaT | NaT | NaT | NaT | NaT | 2021-08-31 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 1 | 0 | True | dislocation_exit |
| AAPL|2021-11-18 | AAPL | 2021-11-18 | NaT | 2021-11-18 00:00:00+00:00 | NaT | NaT | NaT | NaT | 0 | 1 | 0.75 | 0.75 | 1 | 0 | False |  |
| AAPL|2022-08-17 | AAPL | 2022-08-17 | NaT | NaT | NaT | NaT | NaT | 2022-08-17 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 1 | True | dislocation_exit |
| AAPL|2023-07-21 | AAPL | 2023-07-21 | NaT | NaT | NaT | NaT | NaT | 2023-07-21 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 0 | True | dislocation_exit |
| AAPL|2023-11-07 | AAPL | 2023-11-07 | NaT | NaT | NaT | NaT | NaT | 2023-11-07 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 0 | True | dislocation_exit |
| AAPL|2023-12-05 | AAPL | 2023-12-05 | NaT | NaT | NaT | NaT | NaT | 2023-12-05 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 1 | True | dislocation_exit |
| AAPL|2024-01-18 | AAPL | 2024-01-18 | NaT | NaT | NaT | NaT | NaT | 2024-01-18 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 0 | True | dislocation_exit |
| AAPL|2024-03-21 | AAPL | 2024-03-21 | NaT | NaT | NaT | NaT | NaT | 2024-03-21 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 1 | True | dislocation_exit |
| AAPL|2024-06-10 | AAPL | 2024-06-10 | NaT | NaT | NaT | NaT | NaT | 2024-06-10 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 0 | True | dislocation_exit |
| AAPL|2025-06-30 | AAPL | 2025-06-30 | NaT | 2025-06-30 00:00:00+00:00 | NaT | NaT | NaT | NaT | 0 | 1 | 1 | 1 | 0 | 0 | False |  |
| AAPL|2025-07-01 | AAPL | 2025-07-01 | NaT | NaT | NaT | NaT | NaT | 2025-07-01 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 0 | True | dislocation_exit |
| AAPL|2026-04-17 | AAPL | 2026-04-17 | NaT | NaT | NaT | NaT | NaT | 2026-04-17 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 1 | True | dislocation_exit |
| AMD|2021-06-17 | AMD | 2021-06-17 | NaT | NaT | NaT | NaT | NaT | 2021-06-17 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 1 | True | dislocation_exit |
| AMD|2021-07-27 | AMD | 2021-07-27 | NaT | NaT | NaT | NaT | NaT | 2021-07-27 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 0 | True | dislocation_exit |
| AMD|2021-07-28 | AMD | 2021-07-28 | NaT | NaT | NaT | NaT | NaT | 2021-07-28 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 1 | 0 | True | dislocation_exit |
| AMD|2021-10-13 | AMD | 2021-10-13 | NaT | NaT | NaT | NaT | NaT | 2021-10-13 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 1 | True | dislocation_exit |
| AMD|2023-01-09 | AMD | 2023-01-09 | NaT | NaT | NaT | NaT | NaT | 2023-01-09 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 1 | True | dislocation_exit |
| AMD|2023-03-07 | AMD | 2023-03-07 | NaT | NaT | NaT | NaT | NaT | 2023-03-07 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 1 | True | dislocation_exit |
| AMD|2023-06-13 | AMD | 2023-06-13 | NaT | NaT | NaT | NaT | NaT | 2023-06-13 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 0 | True | dislocation_exit |
| AMD|2023-12-07 | AMD | 2023-12-07 | NaT | NaT | NaT | NaT | NaT | 2023-12-07 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 0 | True | dislocation_exit |
| AMD|2024-01-16 | AMD | 2024-01-16 | NaT | NaT | NaT | NaT | NaT | 2024-01-16 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 1 | True | dislocation_exit |
| AMD|2024-05-16 | AMD | 2024-05-16 | NaT | NaT | NaT | NaT | NaT | 2024-05-16 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 1 | True | dislocation_exit |
| AMD|2024-07-05 | AMD | 2024-07-05 | NaT | NaT | NaT | NaT | NaT | 2024-07-05 00:00:00+00:00 | 0 | 1 | 0.07 | 0.07 | 0 | 0 | True | dislocation_exit |