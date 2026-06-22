# Task702 Full Source Packet Axis Rule

## Decision Summary

- Verdict: FULL_SOURCE_PACKET_AXIS_RULE_TEST_COMPLETE_RESEARCH_ONLY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Scope: 435 frozen candidates, source-packet coverage 19.
- Eligible symbols: CEG|CEG|TER|PH|DDOG.
- Key $1,000 max5: source-packet cohort $1,604.24; full-axis eligible $1,391.66.
- Main finding: Full source packet axes block ASTS/SNOW and keep CEG, CEG, TER, PH, DDOG in this diagnostic replay.
- Next action: Move the same source-axis parser upstream to all event-linked candidates, then retest against larger OOS cohorts.

## Quant Expert Report

### Axes Added

- financing overhang
- guidance raise/reaffirm/soft/unclear
- information novelty
- high-noise thin signal
- price absorption confirmation

### Source Packet Action Table

| symbol | packet_bucket | financing_overhang_flag | guidance_quality_axis | information_novelty_axis | high_noise_thin_signal_flag | price_absorption_confirmation_flag | full_source_axis_action | costed_return_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASTS | source_direct_supported | 1.0000 | financing_conflict | conflicted_by_financing | 0.0000 | 1 | CONFIRMATION_REQUIRED_FINANCING | -13.7771 |
| SOFI | source_packet_economic_terms_but_no_direct_bridge | 0.0000 | no_guidance_signal | not_enough_source_novelty | 1.0000 | 1 | RESEARCH_ONLY_LOW_NOVELTY | 65.3193 |
| RKLB | source_packet_economic_terms_but_no_direct_bridge | 0.0000 | reaffirm | not_new_reaffirmation | 1.0000 | 1 | CONFIRMATION_REQUIRED_GUIDANCE_WEAK | 48.9779 |
| BA | source_direct_supported | 0.0000 | reaffirm | not_new_reaffirmation | 0.0000 | 0 | CONFIRMATION_REQUIRED_GUIDANCE_WEAK | 9.2209 |
| PLTR | source_packet_economic_terms_but_no_direct_bridge | 0.0000 | no_guidance_signal | not_enough_source_novelty | 1.0000 | 0 | RESEARCH_ONLY_LOW_NOVELTY | 13.0789 |
| DDOG | source_packet_economic_terms_but_no_direct_bridge | 0.0000 | no_guidance_signal | not_enough_source_novelty | 1.0000 | 0 | RESEARCH_ONLY_LOW_NOVELTY | 2.1288 |
| CEG | source_direct_supported | 0.0000 | guidance_present_quality_unclear | new_thin_direct | 1.0000 | 1 | ELIGIBLE_RULE_CANDIDATE | 12.8341 |
| CEG | source_direct_supported | 0.0000 | guidance_present_quality_unclear | new_thin_direct | 0.0000 | 1 | ELIGIBLE_RULE_CANDIDATE | 16.3238 |
| RKLB | source_packet_economic_terms_but_no_direct_bridge | 0.0000 | no_guidance_signal | not_enough_source_novelty | 1.0000 | 0 | RESEARCH_ONLY_LOW_NOVELTY | 37.3748 |
| RTX | source_packet_economic_terms_but_no_direct_bridge | 0.0000 | no_guidance_signal | not_enough_source_novelty | 1.0000 | 0 | RESEARCH_ONLY_LOW_NOVELTY | 13.9187 |
| RKLB | source_packet_economic_terms_but_no_direct_bridge | 0.0000 | reaffirm | not_new_reaffirmation | 1.0000 | 1 | CONFIRMATION_REQUIRED_GUIDANCE_WEAK | 5.3234 |
| TER | source_direct_supported | 0.0000 | guidance_present_quality_unclear | new_multi_family_direct | 0.0000 | 1 | ELIGIBLE_RULE_CANDIDATE | 69.3120 |
| NET | source_packet_economic_terms_but_no_direct_bridge | 0.0000 | no_guidance_signal | not_enough_source_novelty | 1.0000 | 1 | RESEARCH_ONLY_LOW_NOVELTY | -16.0007 |
| SNOW | source_direct_supported | 0.0000 | reaffirm | not_new_reaffirmation | 1.0000 | 1 | CONFIRMATION_REQUIRED_GUIDANCE_WEAK | -23.6606 |
| SNOW | source_direct_supported | 0.0000 | reaffirm | not_new_reaffirmation | 1.0000 | 0 | CONFIRMATION_REQUIRED_GUIDANCE_WEAK | -25.5164 |
| PH | source_direct_supported | 0.0000 | guidance_present_quality_unclear | new_multi_family_direct | 1.0000 | 1 | ELIGIBLE_RULE_CANDIDATE | 19.0517 |
| RTX | source_packet_economic_terms_but_no_direct_bridge | 0.0000 | no_guidance_signal | not_enough_source_novelty | 1.0000 | 0 | RESEARCH_ONLY_LOW_NOVELTY | 3.6779 |
| GEV | source_packet_economic_terms_but_no_direct_bridge | 0.0000 | no_guidance_signal | not_enough_source_novelty | 1.0000 | 0 | RESEARCH_ONLY_LOW_NOVELTY | 14.8791 |
| DDOG | source_direct_supported | 0.0000 | no_guidance_signal | new_thin_direct | 1.0000 | 1 | ELIGIBLE_RULE_CANDIDATE | 62.3931 |

### Action Summary

| full_source_axis_action | candidate_count | source_event_count | symbols | avg_costed_return_pct | median_costed_return_pct | win_rate | avg_excess_vs_qqq_costed_pct | outcome_used_for_selection_flag | outcome_used_for_evaluation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ELIGIBLE_RULE_CANDIDATE | 5 | 5 | CEG\|CEG\|TER\|PH\|DDOG | 35.9830 | 19.0517 | 1.0000 | 29.9197 | 0 | 1 |
| RESEARCH_ONLY_LOW_NOVELTY | 8 | 8 | SOFI\|PLTR\|DDOG\|RKLB\|RTX\|NET\|RTX\|GEV | 16.7971 | 13.4988 | 0.8750 | 9.4662 | 0 | 1 |
| RESEARCH_ONLY_NO_SOURCE_PACKET | 416 | 0 | GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|GE\|ASTS\|ASTS\|ASTS\|ASTS\|ASTS\|ASTS\|ASTS\|ASTS\|ASTS\|ASTS\|RKLB\|ASTS\|ASTS\|CEG\|CEG\|CEG\|CEG\|CEG\|RTX\|TEAM\|DDOG\|DDOG\|CEG\|CEG\|GD\|RKLB\|RTX\|ARM | 8.3108 | 2.9441 | 0.5529 | 3.8518 | 0 | 1 |
| CONFIRMATION_REQUIRED_GUIDANCE_WEAK | 5 | 5 | RKLB\|BA\|RKLB\|SNOW\|SNOW | 2.8691 | 5.3234 | 0.6000 | -0.9916 | 0 | 1 |
| CONFIRMATION_REQUIRED_FINANCING | 1 | 1 | ASTS | -13.7771 | -13.7771 | 0.0000 | -3.9945 | 0 | 1 |

### Portfolio Comparison

| portfolio_cohort | max_positions | source_candidate_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct |
| --- | --- | --- | --- | --- | --- | --- |
| source_packet_available_19 | 1 | 19 | 5 | 1413.5697 | 41.3570 | -23.6606 |
| source_packet_available_19 | 3 | 19 | 12 | 2179.4811 | 117.9481 | -6.3616 |
| source_packet_available_19 | 5 | 19 | 15 | 1604.2358 | 60.4236 | -8.6121 |
| source_packet_available_19 | 10 | 19 | 19 | 1339.5711 | 33.9571 | -5.8481 |
| full_axis_eligible_5 | 1 | 5 | 3 | 2181.4423 | 118.1442 | 0.0000 |
| full_axis_eligible_5 | 3 | 5 | 5 | 1688.6446 | 68.8645 | 0.0000 |
| full_axis_eligible_5 | 5 | 5 | 5 | 1391.6590 | 39.1659 | 0.0000 |
| full_axis_eligible_5 | 10 | 5 | 5 | 1187.8375 | 18.7837 | 0.0000 |

### Interpretation

- The five axes keep ASTS and SNOW blocked.
- The eligible set expands from Task701 by adding PH while preserving CEG, CEG, TER, and DDOG.
- The rule still covers only 19 source-packet candidates inside the 435 frozen set, so it is not accepted as a strategy.

## No-Background Decision-Maker Report

- What happened: the five axes were applied to all source packets, not just source-direct.
- ASTS/SNOW stayed blocked.
- Eligible became CEG, CEG, TER, PH, DDOG.
- Capital status: still FORBIDDEN.

## Artifact Manifest

- Inputs: Task698 freeze/eval, Task693 source events, Task684 context.
- Outputs: axis freeze, axis eval, action summary, portfolio comparison, audit, decision, pass/fail, manifest.
- Row counts: freeze 435, eval 435, action summary 5.
- Validation commands: `python src/backtest/build_task702_full_source_packet_axis_rule.py`; `python -m unittest tests.test_task702_full_source_packet_axis_rule`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| freeze_scope_435 | PRIMARY_PASS | 1 | rows=435 | full Task698 freeze set |
| source_event_available_19 | PRIMARY_PASS | 1 | source_event_available=19 | all Task693 source packet rows should be covered |
| eligible_count_5 | PRIMARY_PASS | 1 | eligible=5 | expected eligible rows after full source packet axes |
| asts_snow_blocked | PRIMARY_PASS | 1 | ASTS/SNOW eligible count=0 | ASTS and SNOW should remain blocked |
| eval_rows_complete | PRIMARY_PASS | 1 | eval_rows=435 | evaluation attaches outcomes after freeze |
| portfolio_comparison_present | PRIMARY_PASS | 1 | full_axis_eligible_5\|source_packet_available_19 | portfolio comparison cohorts are present |
| no_strategy_or_trade_promotion | PRIMARY_PASS | 1 | allocation_approved=0; paper_or_live_trade_approved=0 | Task702 is research-only |
