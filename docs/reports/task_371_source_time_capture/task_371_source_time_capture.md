# Task 371 - Paper Runtime Source Capture Rollout & Coverage Expansion

## Core Findings
- source_rows_recorded: 18
- lifecycles_recorded: 5
- full_lifecycle_sample_count: 1
- blocked_invalidation_sample_count: 3
- filled_add_sample_count: 1
- persistence_sample_count: 1
- weakening_sample_count: 1
- terminal_sample_count: 4
- identifier_linkage_completeness: 0.555556
- source_captured_share: 0.833333

## Capture Fidelity
| metric_name | metric_value |
| --- | --- |
| source_rows_recorded | 18 |
| lifecycles_recorded | 5 |
| full_lifecycle_sample_count | 1 |
| blocked_invalidation_sample_count | 3 |
| filled_add_sample_count | 1 |
| persistence_sample_count | 1 |
| weakening_sample_count | 1 |
| terminal_sample_count | 4 |
| identifier_linkage_completeness | 0.555556 |
| source_captured_share | 0.833333 |

## Setup Summary
| setup_origin | setup_count | symbol_count | explicit_signal_count |
| --- | --- | --- | --- |
| explicit_signal_identity | 4 | 4 | 4 |

## Recent Source Runs
| trade_run_id | event_count | lifecycle_count | symbol_count | first_timestamp | last_timestamp |
| --- | --- | --- | --- | --- | --- |
| harness-run-restart-b | 2 | 1 | 1 | 2026-01-10 15:05:00+00:00 | 2026-01-10 15:06:00+00:00 |
| harness-run-restart-a | 2 | 1 | 1 | 2026-01-10 15:01:00+00:00 | 2026-01-10 15:01:00+00:00 |
| harness-run-full | 9 | 1 | 1 | 2026-01-10 14:34:00+00:00 | 2026-01-10 15:00:00+00:00 |
| harness-run-fill | 3 | 1 | 1 | 2026-01-10 14:31:00+00:00 | 2026-01-10 14:33:00+00:00 |
| harness-run-blocked | 2 | 1 | 1 | 2026-01-10 14:30:00+00:00 | 2026-01-10 14:30:00+00:00 |

## Lifecycle Completeness
| lifecycle_id | setup_id | symbol | event_count | has_probe | has_add_confirmed | has_size_increase | has_persistence | has_weakening | has_terminal | is_full_lifecycle | source_captured_rows | derived_rows |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MSFT|2026-01-10|harness-full-signal|life_001 | MSFT|2026-01-10|harness-full-signal | MSFT | 9 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 6 | 3 |
| NVDA|2026-01-10|harness-fill-signal|life_001 | NVDA|2026-01-10|harness-fill-signal | NVDA | 3 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 3 | 0 |
| AAPL|2026-01-10|harness-block-signal|life_001 | AAPL|2026-01-10|harness-block-signal | AAPL | 2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 0 |
| AMD|2026-01-10|harness-restart-signal|life_001 | AMD|2026-01-10|harness-restart-signal | AMD | 2 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 0 |
| AMD|2026-01-10|harness-restart-signal|life_002 | AMD|2026-01-10|harness-restart-signal | AMD | 2 | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 0 |

## Identifier Linkage
| field_name | non_null_count | row_count | completeness |
| --- | --- | --- | --- |
| signal_event_id | 18 | 18 | 1 |
| risk_decision_id | 18 | 18 | 1 |
| order_intent_id | 5 | 18 | 0.277778 |
| order_id | 5 | 18 | 0.277778 |
| fill_id | 4 | 18 | 0.222222 |
| reconciliation_id | 2 | 18 | 0.111111 |
| trade_run_id | 18 | 18 | 1 |

## Coverage Gaps
| gap_name | gap_flag | observed_value |
| --- | --- | --- |
| missing_source_rows | 0 | 18 |
| missing_full_lifecycle_sample | 0 | 1 |
| missing_persistence_sample | 0 | 1 |
| missing_weakening_sample | 0 | 1 |
| missing_terminal_sample | 0 | 4 |

## Source Event Sample
| source_event_id | lifecycle_id | setup_id | parent_lifecycle_id | signal_event_id | risk_decision_id | order_intent_id | order_id | fill_id | reconciliation_id | trade_run_id | symbol | session_date | event_type | event_source | event_timestamp | state_label | participation_quality_label | expansion_score | fragility_score | continuation_risk_score | size_multiplier | add_depth | scale_depth | persistence_depth | details_json | created_at |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AAPL|2026-01-10|harness-block-signal|life_001|evt_001 | AAPL|2026-01-10|harness-block-signal|life_001 | AAPL|2026-01-10|harness-block-signal | None | harness-block-signal | harness-block-risk | None | None | None | None | harness-run-blocked | AAPL | 2026-01-10 | SETUP_DETECTED | SOURCE_CAPTURED | 2026-01-10 14:30:00+00:00 | BLOCKED_SIGNAL | FRAGILE_CROWDING | 0 | 1 | 1 | 0 | 0 | 0 | 0 | {"stage": "signal_risk"} | 2026-01-10T14:30:00Z |
| AAPL|2026-01-10|harness-block-signal|life_001|evt_002 | AAPL|2026-01-10|harness-block-signal|life_001 | AAPL|2026-01-10|harness-block-signal | None | harness-block-signal | harness-block-risk | None | None | None | None | harness-run-blocked | AAPL | 2026-01-10 | INVALIDATION | SOURCE_CAPTURED | 2026-01-10 14:30:00+00:00 | BLOCKED_SIGNAL | FRAGILE_CROWDING | 0 | 1 | 1 | 0 | 0 | 0 | 0 | {"reason": "harness_immediate_block"} | 2026-01-10T14:30:00Z |
| NVDA|2026-01-10|harness-fill-signal|life_001|evt_001 | NVDA|2026-01-10|harness-fill-signal|life_001 | NVDA|2026-01-10|harness-fill-signal | None | harness-fill-signal | harness-fill-risk | None | None | None | None | harness-run-fill | NVDA | 2026-01-10 | SETUP_DETECTED | SOURCE_CAPTURED | 2026-01-10 14:31:00+00:00 | SETUP | HEALTHY_EXPANSION | 0.7 | 0.1 | 0.1 | 0 | 0 | 0 | 0 | {"stage": "setup_only"} | 2026-01-10T14:31:00Z |
| NVDA|2026-01-10|harness-fill-signal|life_001|evt_002 | NVDA|2026-01-10|harness-fill-signal|life_001 | NVDA|2026-01-10|harness-fill-signal | None | harness-fill-signal | harness-fill-risk | None | None | None | None | harness-run-fill | NVDA | 2026-01-10 | PROBE_ENTRY | SOURCE_CAPTURED | 2026-01-10 14:32:00+00:00 | PROBE | HEALTHY_EXPANSION | 0.7 | 0.1 | 0.1 | 0 | 0 | 0 | 0 | {"stage": "probe_only"} | 2026-01-10T14:32:00Z |
| NVDA|2026-01-10|harness-fill-signal|life_001|evt_003 | NVDA|2026-01-10|harness-fill-signal|life_001 | NVDA|2026-01-10|harness-fill-signal | None | harness-fill-signal | harness-fill-risk | harness-intent-fill | harness-order-fill | harness-fill-fill | None | harness-run-fill | NVDA | 2026-01-10 | SIZE_INCREASE | SOURCE_CAPTURED | 2026-01-10 14:33:00+00:00 | FILL | HEALTHY_EXPANSION | 0.7 | 0.1 | 0.1 | 1 | 0 | 1 | 0 | {"position_quantity_after": 1.0, "position_quantity_before": 0.0} | 2026-01-10T14:33:00Z |
| MSFT|2026-01-10|harness-full-signal|life_001|evt_001 | MSFT|2026-01-10|harness-full-signal|life_001 | MSFT|2026-01-10|harness-full-signal | None | harness-full-signal | harness-full-risk | None | None | None | None | harness-run-full | MSFT | 2026-01-10 | SETUP_DETECTED | SOURCE_CAPTURED | 2026-01-10 14:34:00+00:00 | SETUP | HEALTHY_EXPANSION | 0.85 | 0.15 | 0.15 | 0 | 0 | 0 | 0 | {"stage": "signal_risk"} | 2026-01-10T14:34:00Z |
| MSFT|2026-01-10|harness-full-signal|life_001|evt_002 | MSFT|2026-01-10|harness-full-signal|life_001 | MSFT|2026-01-10|harness-full-signal | None | harness-full-signal | harness-full-risk | None | None | None | None | harness-run-full | MSFT | 2026-01-10 | PROBE_ENTRY | SOURCE_CAPTURED | 2026-01-10 14:34:00+00:00 | SETUP | HEALTHY_EXPANSION | 0.85 | 0.15 | 0.15 | 1 | 0 | 0 | 0 | {"stage": "probe"} | 2026-01-10T14:34:00Z |
| MSFT|2026-01-10|harness-full-signal|life_001|evt_003 | MSFT|2026-01-10|harness-full-signal|life_001 | MSFT|2026-01-10|harness-full-signal | None | harness-full-signal | harness-full-risk | harness-intent-full | harness-order-full | None | None | harness-run-full | MSFT | 2026-01-10 | ADD_ATTEMPT | SOURCE_CAPTURED | 2026-01-10 14:35:00+00:00 | ADD_ATTEMPT | HEALTHY_EXPANSION | 0.85 | 0.15 | 0.15 | 1 | 0 | 0 | 0 | {"position_quantity_before": 1.0} | 2026-01-10T14:35:00Z |
| MSFT|2026-01-10|harness-full-signal|life_001|evt_004 | MSFT|2026-01-10|harness-full-signal|life_001 | MSFT|2026-01-10|harness-full-signal | None | harness-full-signal | harness-full-risk | harness-intent-full | harness-order-full | harness-fill-full | None | harness-run-full | MSFT | 2026-01-10 | ADD_CONFIRMED | SOURCE_CAPTURED | 2026-01-10 14:36:00+00:00 | ADD_FILL | HEALTHY_EXPANSION | 0.85 | 0.15 | 0.15 | 3 | 1 | 0 | 0 | {"position_quantity_after": 3.0, "position_quantity_before": 1.0} | 2026-01-10T14:36:00Z |
| MSFT|2026-01-10|harness-full-signal|life_001|evt_005 | MSFT|2026-01-10|harness-full-signal|life_001 | MSFT|2026-01-10|harness-full-signal | None | harness-full-signal | harness-full-risk | harness-intent-full | harness-order-full | harness-fill-full | None | harness-run-full | MSFT | 2026-01-10 | SIZE_INCREASE | SOURCE_CAPTURED | 2026-01-10 14:36:00+00:00 | ADD_FILL | HEALTHY_EXPANSION | 0.85 | 0.15 | 0.15 | 3 | 1 | 1 | 0 | {"position_quantity_after": 3.0, "position_quantity_before": 1.0} | 2026-01-10T14:36:00Z |
| MSFT|2026-01-10|harness-full-signal|life_001|evt_006 | MSFT|2026-01-10|harness-full-signal|life_001 | MSFT|2026-01-10|harness-full-signal | None | harness-full-signal | harness-full-risk | None | None | None | None | harness-run-full | MSFT | 2026-01-10 | PERSISTENCE_CONFIRMED | SESSION_DERIVED | 2026-01-10 14:55:00+00:00 | PERSIST | HEALTHY_EXPANSION | 0.8 | 0.2 | 0.2 | 3 | 1 | 1 | 1 | {"elapsed_minutes": 21.0, "persistence_minutes": 15} | 2026-01-10T14:55:00Z |
| MSFT|2026-01-10|harness-full-signal|life_001|evt_007 | MSFT|2026-01-10|harness-full-signal|life_001 | MSFT|2026-01-10|harness-full-signal | None | harness-full-signal | harness-full-risk | None | None | None | None | harness-run-full | MSFT | 2026-01-10 | FRAGILITY_WARNING | SESSION_DERIVED | 2026-01-10 14:58:00+00:00 | WEAKEN | FRAGILE_CROWDING | 0.3 | 0.8 | 0.8 | 2 | 1 | 1 | 1 | {"stage": "weakening"} | 2026-01-10T14:58:00Z |
| MSFT|2026-01-10|harness-full-signal|life_001|evt_008 | MSFT|2026-01-10|harness-full-signal|life_001 | MSFT|2026-01-10|harness-full-signal | None | harness-full-signal | harness-full-risk | None | None | None | None | harness-run-full | MSFT | 2026-01-10 | REDUCTION_TRIGGER | SESSION_DERIVED | 2026-01-10 14:59:00+00:00 | REDUCE | FRAGILE_CROWDING | 0.2 | 0.9 | 0.9 | 1 | 1 | 1 | 1 | {"stage": "weakening"} | 2026-01-10T14:59:00Z |
| MSFT|2026-01-10|harness-full-signal|life_001|evt_009 | MSFT|2026-01-10|harness-full-signal|life_001 | MSFT|2026-01-10|harness-full-signal | None | harness-full-signal | harness-full-risk | harness-intent-full | harness-order-full | harness-fill-full | harness-recon-full | harness-run-full | MSFT | 2026-01-10 | EXIT_TRIGGER | SOURCE_CAPTURED | 2026-01-10 15:00:00+00:00 | EXIT | FRAGILE_CROWDING | 0.2 | 0.9 | 0.9 | 0 | 1 | 1 | 1 | {"reason": "harness_exit"} | 2026-01-10T15:00:00Z |
| AMD|2026-01-10|harness-restart-signal|life_001|evt_001 | AMD|2026-01-10|harness-restart-signal|life_001 | AMD|2026-01-10|harness-restart-signal | None | harness-restart-signal | harness-restart-risk | None | None | None | None | harness-run-restart-a | AMD | 2026-01-10 | SETUP_DETECTED | SOURCE_CAPTURED | 2026-01-10 15:01:00+00:00 | RESTART_BLOCK | FRAGILE_CROWDING | 0 | 1 | 1 | 0 | 0 | 0 | 0 | {"stage": "signal_risk"} | 2026-01-10T15:01:00Z |
| AMD|2026-01-10|harness-restart-signal|life_001|evt_002 | AMD|2026-01-10|harness-restart-signal|life_001 | AMD|2026-01-10|harness-restart-signal | None | harness-restart-signal | harness-restart-risk | None | None | None | None | harness-run-restart-a | AMD | 2026-01-10 | INVALIDATION | SOURCE_CAPTURED | 2026-01-10 15:01:00+00:00 | RESTART_BLOCK | FRAGILE_CROWDING | 0 | 1 | 1 | 0 | 0 | 0 | 0 | {"reason": "restart_seed"} | 2026-01-10T15:01:00Z |
| AMD|2026-01-10|harness-restart-signal|life_002|evt_001 | AMD|2026-01-10|harness-restart-signal|life_002 | AMD|2026-01-10|harness-restart-signal | AMD|2026-01-10|harness-restart-signal|life_001 | harness-restart-signal | harness-restart-risk | None | None | None | None | harness-run-restart-b | AMD | 2026-01-10 | PROBE_ENTRY | SOURCE_CAPTURED | 2026-01-10 15:05:00+00:00 | RESTART_PROBE | HEALTHY_EXPANSION | 0.6 | 0.2 | 0.2 | 1 | 0 | 0 | 0 | {"stage": "probe_only"} | 2026-01-10T15:05:00Z |
| AMD|2026-01-10|harness-restart-signal|life_002|evt_002 | AMD|2026-01-10|harness-restart-signal|life_002 | AMD|2026-01-10|harness-restart-signal | AMD|2026-01-10|harness-restart-signal|life_001 | harness-restart-signal | harness-restart-risk | None | None | None | harness-recon-restart | harness-run-restart-b | AMD | 2026-01-10 | INVALIDATION | SOURCE_CAPTURED | 2026-01-10 15:06:00+00:00 | RESTART_END | FRAGILE_CROWDING | 0.1 | 0.9 | 0.9 | 0 | 0 | 0 | 0 | {"reason": "harness_restart_end"} | 2026-01-10T15:06:00Z |