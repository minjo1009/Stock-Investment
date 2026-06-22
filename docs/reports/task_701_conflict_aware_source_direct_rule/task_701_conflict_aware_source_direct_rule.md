# Task701 Conflict-Aware Source Direct Rule

## Decision Summary

- Verdict: CONFLICT_AWARE_SOURCE_DIRECT_RULE_TEST_COMPLETE_RESEARCH_ONLY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Scope: full Task698 freeze 435 rows, source-direct 9 rows.
- Eligible symbols: CEG|CEG|TER|DDOG.
- Key $1,000 max5: original source-direct $1,261.21; conflict-aware eligible $1,346.30.
- Main finding: Conflict-aware source-direct rule blocks ASTS/SNOW and keeps CEG, CEG, DDOG, TER in this diagnostic replay.
- Next action: Run the same axes across all source packets, not just current source-direct rows, before any broader allocation test.

## Quant Expert Report

### Rule Design

- Block immediate eligibility when `financing_overhang_flag=1`.
- Block immediate eligibility when `guidance_reaffirm_flag=1`.
- High-noise thin signals require price absorption confirmation.
- Every eligible source-direct row must have price acceptance score >= 6, volume ratio >= 1, and a confirmed price chart state.

### Source Direct Action Table

| symbol | split_name | financing_overhang_flag | guidance_reaffirm_flag | high_noise_thin_signal_flag | price_absorption_confirmation_flag | conflict_aware_action | costed_return_pct | qqq_costed_return_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ASTS | train_design | 1.0000 | 0.0000 | 0 | 1 | CONFIRMATION_REQUIRED_FINANCING | -13.7771 | -9.7826 |
| BA | train_design | 0.0000 | 1.0000 | 0 | 0 | CONFIRMATION_REQUIRED_REAFFIRM | 9.2209 | 9.3650 |
| CEG | validation | 0.0000 | 0.0000 | 1 | 1 | ELIGIBLE_RULE_CANDIDATE | 12.8341 | 10.8437 |
| CEG | validation | 0.0000 | 0.0000 | 0 | 1 | ELIGIBLE_RULE_CANDIDATE | 16.3238 | 11.5655 |
| TER | validation | 0.0000 | 0.0000 | 0 | 1 | ELIGIBLE_RULE_CANDIDATE | 69.3120 | 6.8739 |
| SNOW | validation | 0.0000 | 1.0000 | 1 | 1 | CONFIRMATION_REQUIRED_REAFFIRM | -23.6606 | -3.0512 |
| SNOW | validation | 0.0000 | 1.0000 | 1 | 0 | CONFIRMATION_REQUIRED_REAFFIRM | -25.5164 | -2.0133 |
| PH | validation | 0.0000 | 1.0000 | 1 | 1 | CONFIRMATION_REQUIRED_REAFFIRM | 19.0517 | 0.1980 |
| DDOG | recent_oos | 0.0000 | 0.0000 | 1 | 1 | ELIGIBLE_RULE_CANDIDATE | 62.3931 | 0.8352 |

### Action Summary

| conflict_aware_action | candidate_count | symbols | avg_costed_return_pct | median_costed_return_pct | win_rate | avg_excess_vs_qqq_costed_pct | outcome_used_for_selection_flag | outcome_used_for_evaluation_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ELIGIBLE_RULE_CANDIDATE | 4 | CEG\|CEG\|TER\|DDOG | 40.2158 | 39.3585 | 1.0000 | 32.6862 | 0 | 1 |
| CONFIRMATION_REQUIRED_REAFFIRM | 4 | BA\|SNOW\|SNOW\|PH | -5.2261 | -7.2198 | 0.5000 | -6.3507 | 0 | 1 |
| CONFIRMATION_REQUIRED_FINANCING | 1 | ASTS | -13.7771 | -13.7771 | 0.0000 | -3.9945 | 0 | 1 |

### Portfolio Comparison

| portfolio_cohort | max_positions | source_candidate_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct |
| --- | --- | --- | --- | --- | --- | --- |
| source_direct_original_9 | 1 | 9 | 4 | 2589.3081 | 158.9308 | -13.7771 |
| source_direct_original_9 | 3 | 9 | 8 | 1361.3090 | 36.1309 | -13.5347 |
| source_direct_original_9 | 5 | 9 | 9 | 1261.2129 | 26.1213 | -8.6953 |
| source_direct_original_9 | 10 | 9 | 9 | 1128.4845 | 12.8484 | -4.6073 |
| conflict_aware_eligible_4 | 1 | 4 | 2 | 1832.3482 | 83.2348 | 0.0000 |
| conflict_aware_eligible_4 | 3 | 4 | 4 | 1604.4750 | 60.4475 | 0.0000 |
| conflict_aware_eligible_4 | 5 | 4 | 4 | 1346.3014 | 34.6301 | 0.0000 |
| conflict_aware_eligible_4 | 10 | 4 | 4 | 1167.0069 | 16.7007 | 0.0000 |

### Interpretation

- The rule blocks the exact two failure types found in Task700: ASTS financing overhang and SNOW reaffirm/high-noise thin signal.
- It keeps CEG, CEG, DDOG, and TER.
- This improves the diagnostic source-direct subset, but it is still too small and too post-diagnosis to promote.

## No-Background Decision-Maker Report

- What happened: source-direct no longer means automatic eligible.
- ASTS is blocked by financing overhang.
- SNOW is blocked by reaffirm/high-noise logic.
- CEG/DDOG/TER remain eligible in this small replay.
- Capital status: still FORBIDDEN.

## Artifact Manifest

- Inputs: Task698 freeze/eval, Task699 source-direct features, Task693 source evidence, Task684 context.
- Outputs: rule freeze, rule eval, action summary, portfolio comparison, audit, decision, pass/fail, manifest.
- Row counts: freeze 435, eval 435, action summary 3.
- Validation commands: `python src/backtest/build_task701_conflict_aware_source_direct_rule.py`; `python -m unittest tests.test_task701_conflict_aware_source_direct_rule`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| freeze_scope_435 | PRIMARY_PASS | 1 | rows=435 | Task701 rule is applied to the full Task698 frozen 435 rows |
| source_direct_action_scope_9 | PRIMARY_PASS | 1 | source_direct=9 | Source-direct action scope remains 9 |
| eligible_count_4 | PRIMARY_PASS | 1 | eligible=4 | Conflict-aware eligible rows should be CEG, CEG, DDOG, TER |
| asts_snow_blocked | PRIMARY_PASS | 1 | ASTS/SNOW eligible count=0 | ASTS and SNOW should require confirmation, not immediate eligibility |
| eval_rows_complete | PRIMARY_PASS | 1 | eval_rows=435 | All frozen rows must be evaluation-joined after selection |
| portfolio_comparison_present | PRIMARY_PASS | 1 | conflict_aware_eligible_4\|source_direct_original_9 | Portfolio comparison must include original source-direct and conflict-aware eligible cohorts |
| no_strategy_or_trade_promotion | PRIMARY_PASS | 1 | allocation_approved=0; paper_or_live_trade_approved=0 | Task701 is still research-only |
