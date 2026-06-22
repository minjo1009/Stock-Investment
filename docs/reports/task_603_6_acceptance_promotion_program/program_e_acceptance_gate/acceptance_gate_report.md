# T603-6 Program E Acceptance Gate Enforcement

## Problem
Manual promotion from `NOT_ACCEPTED` to `ACCEPTANCE_REVIEW` must be blocked unless the broker truth, entry risk snapshot, replay, and concentration gates pass.

## Evidence
- Status: FAIL
- broker_truth_sell_fills: 0
- snapshot_coverage: 1
- position_match_rate: 0.958333
- replay_completeness_score: MISSING
- top3_share: 0.75

Evidence sources:
- broker_truth_sell_fills: docs/reports/task_603_6_acceptance_promotion_program/program_a_broker_truth/broker_trade_lineage_summary.csv
- position_match_rate: docs/reports/task_602_4_order_replay_recovery/task_602_4_decision.csv
- snapshot_coverage: C:/Users/minjo/OneDrive/바탕 화면/외국주식 퀀트트레이딩/trading.db
- top3_share: docs/reports/task_601_4_concentration_stability/concentration_recent_window_metrics.csv

## Root Cause
The validator found these active blockers:
- broker_truth_sell_fills <= 0
- position_match_rate <= 99%

## Fix Candidate
Resolve only the failing acceptance blockers: broker truth SELL lineage, exact entry risk snapshot coverage, replay position match above 99%, and concentration below the top3 threshold. Do not modify strategy, entry logic, universe, factors, regime filters, or alpha logic.

## Acceptance Impact
`ACCEPTANCE_REVIEW` promotion is `FAIL`. Real capital remains `FORBIDDEN`; deployment remains `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
