# Task 369 - Explicit Continuation Event Capture Architecture

## Core Answers
1. How much continuation lifecycle is now explicitly capturable rather than reconstructed? 0.329167
2. Can the system now represent continuation as explicit lifecycle events with stable ids? YES
3. Can add/scale/persistence now be attached to explicit lifecycle identity? YES
4. How much of the current architecture still depends on derived or replay fallback identity? derived=0.670833, replay_fallback=0.0, explicit_lifecycle_identity=1.0
5. What is still missing before true real-time continuation compounding research becomes possible? explicit setup identity from raw source data

## Capture Fidelity
| metric_name | metric_value |
| --- | --- |
| explicit_event_capture_share | 0.329167 |
| derived_event_capture_share | 0.670833 |
| replay_fallback_share | 0 |
| explicit_setup_identity_share | 0 |
| explicit_lifecycle_identity_share | 1 |
| parent_linkage_share | 0 |
| multi_stage_capture_share | 0.087558 |
| capture_fidelity_score | 0.254181 |

## Event Source Summary
| event_source | event_count | lifecycle_count | event_share |
| --- | --- | --- | --- |
| SESSION_DERIVED | 322 | 160 | 0.670833 |
| SOURCE_CAPTURED | 158 | 57 | 0.329167 |

## Identity Origin Summary
| identity_origin | lifecycle_count | root_lifecycle_count | avg_identity_confidence |
| --- | --- | --- | --- |
| explicit_session_identity | 160 | 160 | 0.8 |
| explicit_trade_identity | 57 | 57 | 0.9 |

## Canonical Events
| event_id | setup_id | lifecycle_id | parent_lifecycle_id | symbol | session_date | timestamp | event_type | event_source | state_label | participation_quality_label | expansion_score | fragility_score | continuation_risk_score | size_multiplier | add_depth | scale_depth | replay_state | event_index | raw_event_id | identity_origin | identity_confidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL|2021-06-14|setup_001|cont_001|evt_001 | AAPL|2021-06-14|setup_001 | AAPL|2021-06-14|setup_001|cont_001 | None | AAPL | 2021-06-14 | 2021-06-14 14:30:00+00:00 | SETUP_DETECTED | SESSION_DERIVED | DISLOCATION | FRAGILE_CROWDING | 0.443485 | 0.567863 | 0.9 | 0 | 0 | 0 | EXITED | 1 | AAPL|2021-06-14|setup_001|cont_001|event_001 | explicit_session_identity | 0.8 |
| AAPL|2021-06-14|setup_001|cont_001|evt_002 | AAPL|2021-06-14|setup_001 | AAPL|2021-06-14|setup_001|cont_001 | None | AAPL | 2021-06-14 | 2021-06-14 14:30:00+00:00 | INVALIDATION | SESSION_DERIVED | DISLOCATION | FRAGILE_CROWDING | 0.443485 | 0.567863 | 0.9 | 0 | 0 | 0 | EXITED | 2 | AAPL|2021-06-14|setup_001|cont_001|event_002 | explicit_session_identity | 0.8 |
| AAPL|2021-08-16|setup_001|cont_001|evt_001 | AAPL|2021-08-16|setup_001 | AAPL|2021-08-16|setup_001|cont_001 | None | AAPL | 2021-08-16 | 2021-08-16 14:30:00+00:00 | PROBE_ENTRY | SOURCE_CAPTURED | NORMAL | HEALTHY_EXPANSION | 0.587636 | 0.440831 | 0.2 | 1 | 0 | 0 | PROBE | 2 | AAPL|2021-08-16|setup_001|cont_001|event_002 | explicit_trade_identity | 0.9 |
| AAPL|2021-08-16|setup_001|cont_001|evt_002 | AAPL|2021-08-16|setup_001 | AAPL|2021-08-16|setup_001|cont_001 | None | AAPL | 2021-08-16 | 2021-08-16 14:35:00+00:00 | ADD_ATTEMPT | SOURCE_CAPTURED | NORMAL | HEALTHY_EXPANSION | 0.587636 | 0.440831 | 0.2 | 1 | 0 | 0 | PROBE | 3 | AAPL|2021-08-16|setup_001|cont_001|event_003 | explicit_trade_identity | 0.9 |
| AAPL|2021-08-16|setup_001|cont_001|evt_003 | AAPL|2021-08-16|setup_001 | AAPL|2021-08-16|setup_001|cont_001 | None | AAPL | 2021-08-16 | 2021-08-16 14:45:00+00:00 | PERSISTENCE_CONFIRMED | SOURCE_CAPTURED | NORMAL | HEALTHY_EXPANSION | 0.587636 | 0.440831 | 0.2 | 1 | 0 | 0 | PROBE | 4 | AAPL|2021-08-16|setup_001|cont_001|event_004 | explicit_trade_identity | 0.9 |
| AAPL|2021-08-16|setup_001|cont_001|evt_004 | AAPL|2021-08-16|setup_001 | AAPL|2021-08-16|setup_001|cont_001 | None | AAPL | 2021-08-16 | 2021-08-16 15:35:00+00:00 | SETUP_DETECTED | SOURCE_CAPTURED | NORMAL | HEALTHY_EXPANSION | 0.587636 | 0.440831 | 0.2 | 0 | 0 | 0 | PROBE | 1 | AAPL|2021-08-16|setup_001|cont_001|event_001 | explicit_trade_identity | 0.9 |
| AAPL|2021-08-31|setup_001|cont_001|evt_001 | AAPL|2021-08-31|setup_001 | AAPL|2021-08-31|setup_001|cont_001 | None | AAPL | 2021-08-31 | 2021-08-31 13:30:00+00:00 | SETUP_DETECTED | SESSION_DERIVED | DISLOCATION | HEALTHY_EXPANSION | 0.622028 | 0.36727 | 0.9 | 0 | 0 | 0 | EXITED | 1 | AAPL|2021-08-31|setup_001|cont_001|event_001 | explicit_session_identity | 0.8 |
| AAPL|2021-08-31|setup_001|cont_001|evt_002 | AAPL|2021-08-31|setup_001 | AAPL|2021-08-31|setup_001|cont_001 | None | AAPL | 2021-08-31 | 2021-08-31 13:30:00+00:00 | INVALIDATION | SESSION_DERIVED | DISLOCATION | HEALTHY_EXPANSION | 0.622028 | 0.36727 | 0.9 | 0 | 0 | 0 | EXITED | 2 | AAPL|2021-08-31|setup_001|cont_001|event_002 | explicit_session_identity | 0.8 |
| AAPL|2021-11-18|setup_001|cont_001|evt_001 | AAPL|2021-11-18|setup_001 | AAPL|2021-11-18|setup_001|cont_001 | None | AAPL | 2021-11-18 | 2021-11-18 14:30:00+00:00 | PROBE_ENTRY | SOURCE_CAPTURED | ELEVATED | HEALTHY_EXPANSION | 0.661095 | 0.378514 | 0.45 | 0.25 | 0 | 0 | PROBE | 2 | AAPL|2021-11-18|setup_001|cont_001|event_002 | explicit_trade_identity | 0.9 |
| AAPL|2021-11-18|setup_001|cont_001|evt_002 | AAPL|2021-11-18|setup_001 | AAPL|2021-11-18|setup_001|cont_001 | None | AAPL | 2021-11-18 | 2021-11-18 14:35:00+00:00 | ADD_ATTEMPT | SOURCE_CAPTURED | ELEVATED | HEALTHY_EXPANSION | 0.661095 | 0.378514 | 0.45 | 0.25 | 0 | 0 | PROBE | 3 | AAPL|2021-11-18|setup_001|cont_001|event_003 | explicit_trade_identity | 0.9 |
| AAPL|2021-11-18|setup_001|cont_001|evt_003 | AAPL|2021-11-18|setup_001 | AAPL|2021-11-18|setup_001|cont_001 | None | AAPL | 2021-11-18 | 2021-11-18 14:40:00+00:00 | ADD_CONFIRMED | SOURCE_CAPTURED | ELEVATED | HEALTHY_EXPANSION | 0.661095 | 0.378514 | 0.45 | 0.45 | 1 | 0 | PROBE | 4 | AAPL|2021-11-18|setup_001|cont_001|event_004 | explicit_trade_identity | 0.9 |
| AAPL|2021-11-18|setup_001|cont_001|evt_004 | AAPL|2021-11-18|setup_001 | AAPL|2021-11-18|setup_001|cont_001 | None | AAPL | 2021-11-18 | 2021-11-18 14:45:00+00:00 | SIZE_INCREASE | SOURCE_CAPTURED | ELEVATED | HEALTHY_EXPANSION | 0.661095 | 0.378514 | 0.45 | 0.75 | 1 | 1 | PROBE | 5 | AAPL|2021-11-18|setup_001|cont_001|event_005 | explicit_trade_identity | 0.9 |
| AAPL|2021-11-18|setup_001|cont_001|evt_005 | AAPL|2021-11-18|setup_001 | AAPL|2021-11-18|setup_001|cont_001 | None | AAPL | 2021-11-18 | 2021-11-18 14:45:00+00:00 | PERSISTENCE_CONFIRMED | SOURCE_CAPTURED | ELEVATED | HEALTHY_EXPANSION | 0.661095 | 0.378514 | 0.45 | 0.75 | 1 | 1 | PROBE | 6 | AAPL|2021-11-18|setup_001|cont_001|event_006 | explicit_trade_identity | 0.9 |
| AAPL|2021-11-18|setup_001|cont_001|evt_006 | AAPL|2021-11-18|setup_001 | AAPL|2021-11-18|setup_001|cont_001 | None | AAPL | 2021-11-18 | 2021-11-18 17:25:00+00:00 | SETUP_DETECTED | SOURCE_CAPTURED | ELEVATED | HEALTHY_EXPANSION | 0.661095 | 0.378514 | 0.45 | 0 | 1 | 1 | PROBE | 1 | AAPL|2021-11-18|setup_001|cont_001|event_001 | explicit_trade_identity | 0.9 |
| AAPL|2022-08-17|setup_001|cont_001|evt_001 | AAPL|2022-08-17|setup_001 | AAPL|2022-08-17|setup_001|cont_001 | None | AAPL | 2022-08-17 | 2022-08-17 14:30:00+00:00 | SETUP_DETECTED | SESSION_DERIVED | DISLOCATION | FRAGILE_CROWDING | 0.438007 | 0.554163 | 0.9 | 0 | 0 | 0 | EXITED | 1 | AAPL|2022-08-17|setup_001|cont_001|event_001 | explicit_session_identity | 0.8 |
| AAPL|2022-08-17|setup_001|cont_001|evt_002 | AAPL|2022-08-17|setup_001 | AAPL|2022-08-17|setup_001|cont_001 | None | AAPL | 2022-08-17 | 2022-08-17 14:30:00+00:00 | INVALIDATION | SESSION_DERIVED | DISLOCATION | FRAGILE_CROWDING | 0.438007 | 0.554163 | 0.9 | 0 | 0 | 0 | EXITED | 2 | AAPL|2022-08-17|setup_001|cont_001|event_002 | explicit_session_identity | 0.8 |
| AAPL|2023-07-21|setup_001|cont_001|evt_001 | AAPL|2023-07-21|setup_001 | AAPL|2023-07-21|setup_001|cont_001 | None | AAPL | 2023-07-21 | 2023-07-21 14:30:00+00:00 | SETUP_DETECTED | SESSION_DERIVED | DISLOCATION | NEUTRAL_PARTICIPATION | 0.452177 | 0.480765 | 0.9 | 0 | 0 | 0 | EXITED | 1 | AAPL|2023-07-21|setup_001|cont_001|event_001 | explicit_session_identity | 0.8 |
| AAPL|2023-07-21|setup_001|cont_001|evt_002 | AAPL|2023-07-21|setup_001 | AAPL|2023-07-21|setup_001|cont_001 | None | AAPL | 2023-07-21 | 2023-07-21 14:30:00+00:00 | INVALIDATION | SESSION_DERIVED | DISLOCATION | NEUTRAL_PARTICIPATION | 0.452177 | 0.480765 | 0.9 | 0 | 0 | 0 | EXITED | 2 | AAPL|2023-07-21|setup_001|cont_001|event_002 | explicit_session_identity | 0.8 |
| AAPL|2023-11-07|setup_001|cont_001|evt_001 | AAPL|2023-11-07|setup_001 | AAPL|2023-11-07|setup_001|cont_001 | None | AAPL | 2023-11-07 | 2023-11-07 14:30:00+00:00 | INVALIDATION | SOURCE_CAPTURED | DISLOCATION | NEUTRAL_PARTICIPATION | 0.478474 | 0.517838 | 0.9 | 0 | 0 | 0 | EXITED | 2 | AAPL|2023-11-07|setup_001|cont_001|event_002 | explicit_trade_identity | 0.9 |
| AAPL|2023-11-07|setup_001|cont_001|evt_002 | AAPL|2023-11-07|setup_001 | AAPL|2023-11-07|setup_001|cont_001 | None | AAPL | 2023-11-07 | 2023-11-07 14:35:00+00:00 | SETUP_DETECTED | SOURCE_CAPTURED | DISLOCATION | NEUTRAL_PARTICIPATION | 0.478474 | 0.517838 | 0.9 | 0 | 0 | 0 | EXITED | 1 | AAPL|2023-11-07|setup_001|cont_001|event_001 | explicit_trade_identity | 0.9 |
| AAPL|2023-12-05|setup_001|cont_001|evt_001 | AAPL|2023-12-05|setup_001 | AAPL|2023-12-05|setup_001|cont_001 | None | AAPL | 2023-12-05 | 2023-12-05 14:30:00+00:00 | SETUP_DETECTED | SESSION_DERIVED | DISLOCATION | FRAGILE_CROWDING | 0.401025 | 0.525965 | 0.9 | 0 | 0 | 0 | EXITED | 1 | AAPL|2023-12-05|setup_001|cont_001|event_001 | explicit_session_identity | 0.8 |
| AAPL|2023-12-05|setup_001|cont_001|evt_002 | AAPL|2023-12-05|setup_001 | AAPL|2023-12-05|setup_001|cont_001 | None | AAPL | 2023-12-05 | 2023-12-05 14:30:00+00:00 | INVALIDATION | SESSION_DERIVED | DISLOCATION | FRAGILE_CROWDING | 0.401025 | 0.525965 | 0.9 | 0 | 0 | 0 | EXITED | 2 | AAPL|2023-12-05|setup_001|cont_001|event_002 | explicit_session_identity | 0.8 |
| AAPL|2024-01-18|setup_001|cont_001|evt_001 | AAPL|2024-01-18|setup_001 | AAPL|2024-01-18|setup_001|cont_001 | None | AAPL | 2024-01-18 | 2024-01-18 14:30:00+00:00 | INVALIDATION | SOURCE_CAPTURED | DISLOCATION | NEUTRAL_PARTICIPATION | 0.493861 | 0.54131 | 0.9 | 0 | 0 | 0 | EXITED | 2 | AAPL|2024-01-18|setup_001|cont_001|event_002 | explicit_trade_identity | 0.9 |
| AAPL|2024-01-18|setup_001|cont_001|evt_002 | AAPL|2024-01-18|setup_001 | AAPL|2024-01-18|setup_001|cont_001 | None | AAPL | 2024-01-18 | 2024-01-18 14:55:00+00:00 | SETUP_DETECTED | SOURCE_CAPTURED | DISLOCATION | NEUTRAL_PARTICIPATION | 0.493861 | 0.54131 | 0.9 | 0 | 0 | 0 | EXITED | 1 | AAPL|2024-01-18|setup_001|cont_001|event_001 | explicit_trade_identity | 0.9 |
| AAPL|2024-03-21|setup_001|cont_001|evt_001 | AAPL|2024-03-21|setup_001 | AAPL|2024-03-21|setup_001|cont_001 | None | AAPL | 2024-03-21 | 2024-03-21 14:30:00+00:00 | SETUP_DETECTED | SESSION_DERIVED | DISLOCATION | FRAGILE_CROWDING | 0.404623 | 0.530857 | 0.9 | 0 | 0 | 0 | EXITED | 1 | AAPL|2024-03-21|setup_001|cont_001|event_001 | explicit_session_identity | 0.8 |

## Lifecycle Identity
| lifecycle_id | setup_id | symbol | session_date | lifecycle_start_ts | lifecycle_end_ts | identity_origin | identity_confidence | parent_lifecycle_id | is_root_lifecycle | lifecycle_rank_within_setup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL|2021-06-14|setup_001|cont_001 | AAPL|2021-06-14|setup_001 | AAPL | 2021-06-14 | 2021-06-14 14:30:00+00:00 | 2021-06-14 14:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |
| AAPL|2021-08-16|setup_001|cont_001 | AAPL|2021-08-16|setup_001 | AAPL | 2021-08-16 | 2021-08-16 14:30:00+00:00 | 2021-08-16 15:35:00+00:00 | explicit_trade_identity | 0.9 | None | True | 1 |
| AAPL|2021-08-31|setup_001|cont_001 | AAPL|2021-08-31|setup_001 | AAPL | 2021-08-31 | 2021-08-31 13:30:00+00:00 | 2021-08-31 13:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |
| AAPL|2021-11-18|setup_001|cont_001 | AAPL|2021-11-18|setup_001 | AAPL | 2021-11-18 | 2021-11-18 14:30:00+00:00 | 2021-11-18 17:25:00+00:00 | explicit_trade_identity | 0.9 | None | True | 1 |
| AAPL|2022-08-17|setup_001|cont_001 | AAPL|2022-08-17|setup_001 | AAPL | 2022-08-17 | 2022-08-17 14:30:00+00:00 | 2022-08-17 14:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |
| AAPL|2023-07-21|setup_001|cont_001 | AAPL|2023-07-21|setup_001 | AAPL | 2023-07-21 | 2023-07-21 14:30:00+00:00 | 2023-07-21 14:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |
| AAPL|2023-11-07|setup_001|cont_001 | AAPL|2023-11-07|setup_001 | AAPL | 2023-11-07 | 2023-11-07 14:30:00+00:00 | 2023-11-07 14:35:00+00:00 | explicit_trade_identity | 0.9 | None | True | 1 |
| AAPL|2023-12-05|setup_001|cont_001 | AAPL|2023-12-05|setup_001 | AAPL | 2023-12-05 | 2023-12-05 14:30:00+00:00 | 2023-12-05 14:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |
| AAPL|2024-01-18|setup_001|cont_001 | AAPL|2024-01-18|setup_001 | AAPL | 2024-01-18 | 2024-01-18 14:30:00+00:00 | 2024-01-18 14:55:00+00:00 | explicit_trade_identity | 0.9 | None | True | 1 |
| AAPL|2024-03-21|setup_001|cont_001 | AAPL|2024-03-21|setup_001 | AAPL | 2024-03-21 | 2024-03-21 14:30:00+00:00 | 2024-03-21 14:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |
| AAPL|2024-06-10|setup_001|cont_001 | AAPL|2024-06-10|setup_001 | AAPL | 2024-06-10 | 2024-06-10 14:30:00+00:00 | 2024-06-10 14:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |
| AAPL|2025-06-30|setup_001|cont_001 | AAPL|2025-06-30|setup_001 | AAPL | 2025-06-30 | 2025-06-30 14:30:00+00:00 | 2025-06-30 19:10:00+00:00 | explicit_trade_identity | 0.9 | None | True | 1 |
| AAPL|2025-07-01|setup_001|cont_001 | AAPL|2025-07-01|setup_001 | AAPL | 2025-07-01 | 2025-07-01 13:30:00+00:00 | 2025-07-01 13:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |
| AAPL|2026-04-17|setup_001|cont_001 | AAPL|2026-04-17|setup_001 | AAPL | 2026-04-17 | 2026-04-17 14:30:00+00:00 | 2026-04-17 14:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |
| AMD|2021-06-17|setup_001|cont_001 | AMD|2021-06-17|setup_001 | AMD | 2021-06-17 | 2021-06-17 14:30:00+00:00 | 2021-06-17 14:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |
| AMD|2021-07-27|setup_001|cont_001 | AMD|2021-07-27|setup_001 | AMD | 2021-07-27 | 2021-07-27 14:30:00+00:00 | 2021-07-27 20:20:00+00:00 | explicit_trade_identity | 0.9 | None | True | 1 |
| AMD|2021-07-28|setup_001|cont_001 | AMD|2021-07-28|setup_001 | AMD | 2021-07-28 | 2021-07-28 13:00:00+00:00 | 2021-07-28 14:30:00+00:00 | explicit_trade_identity | 0.9 | None | True | 1 |
| AMD|2021-10-13|setup_001|cont_001 | AMD|2021-10-13|setup_001 | AMD | 2021-10-13 | 2021-10-13 14:30:00+00:00 | 2021-10-13 14:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |
| AMD|2023-01-09|setup_001|cont_001 | AMD|2023-01-09|setup_001 | AMD | 2023-01-09 | 2023-01-09 14:30:00+00:00 | 2023-01-09 14:40:00+00:00 | explicit_trade_identity | 0.9 | None | True | 1 |
| AMD|2023-03-07|setup_001|cont_001 | AMD|2023-03-07|setup_001 | AMD | 2023-03-07 | 2023-03-07 14:30:00+00:00 | 2023-03-07 14:35:00+00:00 | explicit_trade_identity | 0.9 | None | True | 1 |
| AMD|2023-06-13|setup_001|cont_001 | AMD|2023-06-13|setup_001 | AMD | 2023-06-13 | 2023-06-13 14:30:00+00:00 | 2023-06-13 14:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |
| AMD|2023-12-07|setup_001|cont_001 | AMD|2023-12-07|setup_001 | AMD | 2023-12-07 | 2023-12-07 14:30:00+00:00 | 2023-12-07 17:15:00+00:00 | explicit_trade_identity | 0.9 | None | True | 1 |
| AMD|2024-01-16|setup_001|cont_001 | AMD|2024-01-16|setup_001 | AMD | 2024-01-16 | 2024-01-16 14:30:00+00:00 | 2024-01-16 14:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |
| AMD|2024-05-16|setup_001|cont_001 | AMD|2024-05-16|setup_001 | AMD | 2024-05-16 | 2024-05-16 14:30:00+00:00 | 2024-05-16 14:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |
| AMD|2024-07-05|setup_001|cont_001 | AMD|2024-07-05|setup_001 | AMD | 2024-07-05 | 2024-07-05 14:30:00+00:00 | 2024-07-05 14:30:00+00:00 | explicit_session_identity | 0.8 | None | True | 1 |

## Lifecycle Snapshots
| lifecycle_id | timestamp | replay_state | size_multiplier | add_depth | scale_depth | persistence_depth | weakening_flag | invalidated_flag | event_id |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL|2021-06-14|setup_001|cont_001 | 2021-06-14 14:30:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | False | AAPL|2021-06-14|setup_001|cont_001|evt_001 |
| AAPL|2021-06-14|setup_001|cont_001 | 2021-06-14 14:30:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | True | AAPL|2021-06-14|setup_001|cont_001|evt_002 |
| AAPL|2021-08-16|setup_001|cont_001 | 2021-08-16 14:30:00+00:00 | PROBE | 1 | 0 | 0 | 0 | False | False | AAPL|2021-08-16|setup_001|cont_001|evt_001 |
| AAPL|2021-08-16|setup_001|cont_001 | 2021-08-16 14:35:00+00:00 | PROBE | 1 | 0 | 0 | 0 | False | False | AAPL|2021-08-16|setup_001|cont_001|evt_002 |
| AAPL|2021-08-16|setup_001|cont_001 | 2021-08-16 14:45:00+00:00 | PROBE | 1 | 0 | 0 | 1 | False | False | AAPL|2021-08-16|setup_001|cont_001|evt_003 |
| AAPL|2021-08-16|setup_001|cont_001 | 2021-08-16 15:35:00+00:00 | PROBE | 0 | 0 | 0 | 1 | False | False | AAPL|2021-08-16|setup_001|cont_001|evt_004 |
| AAPL|2021-08-31|setup_001|cont_001 | 2021-08-31 13:30:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | False | AAPL|2021-08-31|setup_001|cont_001|evt_001 |
| AAPL|2021-08-31|setup_001|cont_001 | 2021-08-31 13:30:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | True | AAPL|2021-08-31|setup_001|cont_001|evt_002 |
| AAPL|2021-11-18|setup_001|cont_001 | 2021-11-18 14:30:00+00:00 | PROBE | 0.25 | 0 | 0 | 0 | False | False | AAPL|2021-11-18|setup_001|cont_001|evt_001 |
| AAPL|2021-11-18|setup_001|cont_001 | 2021-11-18 14:35:00+00:00 | PROBE | 0.25 | 0 | 0 | 0 | False | False | AAPL|2021-11-18|setup_001|cont_001|evt_002 |
| AAPL|2021-11-18|setup_001|cont_001 | 2021-11-18 14:40:00+00:00 | PROBE | 0.45 | 1 | 0 | 0 | False | False | AAPL|2021-11-18|setup_001|cont_001|evt_003 |
| AAPL|2021-11-18|setup_001|cont_001 | 2021-11-18 14:45:00+00:00 | PROBE | 0.75 | 1 | 1 | 0 | False | False | AAPL|2021-11-18|setup_001|cont_001|evt_004 |
| AAPL|2021-11-18|setup_001|cont_001 | 2021-11-18 14:45:00+00:00 | PROBE | 0.75 | 1 | 1 | 1 | False | False | AAPL|2021-11-18|setup_001|cont_001|evt_005 |
| AAPL|2021-11-18|setup_001|cont_001 | 2021-11-18 17:25:00+00:00 | PROBE | 0 | 1 | 1 | 1 | False | False | AAPL|2021-11-18|setup_001|cont_001|evt_006 |
| AAPL|2022-08-17|setup_001|cont_001 | 2022-08-17 14:30:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | False | AAPL|2022-08-17|setup_001|cont_001|evt_001 |
| AAPL|2022-08-17|setup_001|cont_001 | 2022-08-17 14:30:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | True | AAPL|2022-08-17|setup_001|cont_001|evt_002 |
| AAPL|2023-07-21|setup_001|cont_001 | 2023-07-21 14:30:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | False | AAPL|2023-07-21|setup_001|cont_001|evt_001 |
| AAPL|2023-07-21|setup_001|cont_001 | 2023-07-21 14:30:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | True | AAPL|2023-07-21|setup_001|cont_001|evt_002 |
| AAPL|2023-11-07|setup_001|cont_001 | 2023-11-07 14:30:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | True | AAPL|2023-11-07|setup_001|cont_001|evt_001 |
| AAPL|2023-11-07|setup_001|cont_001 | 2023-11-07 14:35:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | True | AAPL|2023-11-07|setup_001|cont_001|evt_002 |
| AAPL|2023-12-05|setup_001|cont_001 | 2023-12-05 14:30:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | False | AAPL|2023-12-05|setup_001|cont_001|evt_001 |
| AAPL|2023-12-05|setup_001|cont_001 | 2023-12-05 14:30:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | True | AAPL|2023-12-05|setup_001|cont_001|evt_002 |
| AAPL|2024-01-18|setup_001|cont_001 | 2024-01-18 14:30:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | True | AAPL|2024-01-18|setup_001|cont_001|evt_001 |
| AAPL|2024-01-18|setup_001|cont_001 | 2024-01-18 14:55:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | True | AAPL|2024-01-18|setup_001|cont_001|evt_002 |
| AAPL|2024-03-21|setup_001|cont_001 | 2024-03-21 14:30:00+00:00 | EXITED | 0 | 0 | 0 | 0 | False | False | AAPL|2024-03-21|setup_001|cont_001|evt_001 |