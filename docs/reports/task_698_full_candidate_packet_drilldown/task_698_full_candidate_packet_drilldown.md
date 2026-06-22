# Task698 Full Candidate Packet Drilldown

## Decision Summary

- Verdict: FULL_CANDIDATE_PACKET_DRILLDOWN_COMPLETE_RESEARCH_ONLY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Scope: Task691 leaders 28 + contenders 407 = 435.
- Review-ready packet count: 11.
- Main finding: Source-direct packets repeat better than price-confirmed packets; the tiny result was not only TER, but price absorption alone is weak.
- Key $1,000 max5: review-ready $1,254.82; source-direct $1,261.21; all-435 $4,142.03.
- Next action: Split source-direct winners and losers by economic catalyst type before expanding allocation rules.

## Quant Expert Report

### Data source and scope

- Freeze input: Task691 slot leader/contender review.
- Packet inputs: Task693 source packet v2 and Task692 price absorption panel.
- Outcome input: Task684 lifecycle panel, exact `lifecycle_id` + `symbol` join only.
- Benchmark input: QQQ daily from `data/raw/us_daily_breadth_top500/QQQ.csv`.

### Freeze before outcome

- `task698_full_candidate_freeze_panel.csv` has no PnL or exit columns.
- PnL is added only in `task698_full_candidate_eval_panel.csv`.
- No candidate is allocation-approved or paper/live-approved.

### Bucket Return Summary

| packet_bucket | candidate_count | train_design_count | validation_count | recent_oos_count | avg_costed_return_pct | median_costed_return_pct | win_rate | avg_excess_vs_qqq_costed_pct | beats_qqq_rate | best_symbol | worst_symbol |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| source_packet_economic_terms_but_no_direct_bridge | 10 | 2 | 7 | 1 | 18.8678 | 13.4988 | 0.9000 | 11.5028 | 0.6000 | SOFI | NET |
| source_direct_supported | 9 | 2 | 6 | 1 | 14.0202 | 12.8341 | 0.6667 | 11.2608 | 0.5556 | TER | SNOW |
| priced_in_or_extension_risk | 42 | 17 | 11 | 14 | 12.7665 | -0.7804 | 0.4762 | 8.2340 | 0.4524 | RKLB | SNOW |
| peer_margin_confirmation_needed | 114 | 54 | 40 | 20 | 12.4653 | 4.2842 | 0.6316 | 5.7087 | 0.4474 | ASTS | ASTS |
| price_unproven_needs_confirmation | 61 | 28 | 19 | 14 | 5.9345 | 2.6591 | 0.5410 | 2.8188 | 0.4262 | RKLB | VRT |
| price_possible_needs_delay | 188 | 70 | 75 | 43 | 5.8266 | 2.0246 | 0.5319 | 2.5108 | 0.4734 | ASTS | TEAM |
| other_not_review_ready | 9 | 5 | 2 | 2 | 4.9377 | -0.6881 | 0.4444 | -4.9063 | 0.2222 | RKLB | ASTS |
| price_confirmed_not_overextended | 2 | 1 | 0 | 1 | -0.8856 | -0.8856 | 0.5000 | 2.9557 | 0.5000 | LMT | TEAM |

### Portfolio Comparison

| portfolio_cohort | max_positions | source_candidate_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct |
| --- | --- | --- | --- | --- | --- | --- |
| source_direct_supported_9 | 1 | 9 | 4 | 2589.3081 | 158.9308 | -13.7771 |
| source_direct_supported_9 | 3 | 9 | 8 | 1361.3090 | 36.1309 | -13.5347 |
| source_direct_supported_9 | 5 | 9 | 9 | 1261.2129 | 26.1213 | -8.6953 |
| source_direct_supported_9 | 10 | 9 | 9 | 1128.4845 | 12.8484 | -4.6073 |
| review_ready_source_or_price_11 | 1 | 11 | 5 | 2923.7805 | 192.3780 | -10.2449 |
| review_ready_source_or_price_11 | 3 | 11 | 10 | 1349.6577 | 34.9658 | -13.5347 |
| review_ready_source_or_price_11 | 5 | 11 | 11 | 1254.8180 | 25.4818 | -8.6953 |
| review_ready_source_or_price_11 | 10 | 11 | 11 | 1126.0510 | 12.6051 | -4.6073 |
| all_435 | 1 | 435 | 10 | 6537.2324 | 553.7232 | -47.5562 |
| all_435 | 3 | 435 | 31 | 7622.9864 | 662.2986 | -42.5672 |
| all_435 | 5 | 435 | 51 | 4142.0332 | 314.2033 | -38.4647 |
| all_435 | 10 | 435 | 102 | 2776.1203 | 177.6120 | -38.2278 |

### Interpretation

- Source-direct packets are stronger than the 3-trade tiny test alone suggested: 9 rows average positive after 50 bps cost and beat QQQ on average.
- Price-confirmed-only is weak: 2 rows average slightly negative after cost.
- The broad 435 set can make money in capacity simulation, but drawdown is large, so it is not a clean strategy.
- Manual/no-direct bridge rows surprisingly performed well, which means the current source interpreter may be too strict or may be missing indirect economic transmission.

### Split/OOS metrics

- Source-direct bucket contains train, validation, and recent-OOS rows.
- This is still not a promotion because the bucket logic is coarse and sample sizes are small.

### Failure decomposition

- ASTS shows source-direct can still fail when ownership/noise mix and later price weakness dominate.
- SNOW rows show direct source support can lose badly when price/catalyst absorption is wrong.
- TER and DDOG show source-direct can catch large winners.
- TEAM/LMT show price absorption alone is not enough.

### Remaining blockers

- Split source-direct by economic catalyst type: contract/customer/backlog/guidance/margin/supply-demand.
- Separate direct economic evidence from ownership/noise-heavy packets.
- Add price absorption as a confirmation of source-direct, not a standalone buy reason.

## No-Background Decision-Maker Report

- What happened: the 3-trade result was expanded to 435 frozen candidates.
- Main result: source-direct evidence looks useful beyond TER.
- Bad part: price absorption alone is weak.
- Big warning: all-435 can earn but with ugly drawdown, so it is not deployable.
- Capital status: still FORBIDDEN.

## Artifact Manifest

- Inputs: Task691, Task692, Task693, Task684, QQQ daily benchmark.
- Outputs: freeze panel, eval panel, bucket summary, portfolio comparison, integrity audit, decision, pass/fail, manifest.
- Row counts: freeze 435, eval 435, buckets 8, portfolio rows 24.
- Validation commands: `python src/backtest/build_task698_full_candidate_packet_drilldown.py`; `python -m unittest tests.test_task698_full_candidate_packet_drilldown`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| full_candidate_scope_435 | PRIMARY_PASS | 1 | rows=435; roles={'contender': 407, 'leader': 28} | Task698 must cover Task691 28 leaders plus 407 contenders |
| freeze_panel_has_no_outcome_columns | PRIMARY_PASS | 1 | none | Freeze panel cannot contain PnL/outcome columns |
| review_ready_packet_count_11 | PRIMARY_PASS | 1 | review_ready=11 | Review-ready automated packet scope should be 9 source-direct plus 2 price-confirmed rows |
| exact_outcome_eval_count | PRIMARY_PASS | 1 | eval_rows=435; eval_flags=435 | All frozen rows must evaluate by exact lifecycle join only |
| cost_and_qqq_applied | PRIMARY_PASS | 1 | cost_bps=50; qqq_rows=435 | Every evaluated row needs costed return and QQQ matched-window return |
| bucket_summary_complete | PRIMARY_PASS | 1 | bucket_sum=435 | Bucket summary must account for every frozen row |
| portfolio_comparison_present | PRIMARY_PASS | 1 | rows=24 | Portfolio comparison must cover declared cohorts and max position grids |
| no_strategy_or_trade_promotion | PRIMARY_PASS | 1 | allocation_approved=0; paper_or_live_trade_approved=0 | Full drilldown cannot promote allocation or trading |
