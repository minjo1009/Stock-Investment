# Task651 Relation State Machine

## Decision Summary

- Verdict: `PASS_QQQ_FAIL_TASK639_RELATION_DIAGNOSTIC_NOT_ACCEPTED`
- Strategy acceptance: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Task651 $1000 final: $7341.22
- Task651 max drawdown: -24.90%
- QQQ final: $1606.83
- Task639 recomputed final: $7639.62

## Quant Expert Report

Task651 implements the Task650 relation-state design as deterministic gates and a rule-table resolver. It does not use labels, realized returns, future prices, QQQ performance, or entry-reduce outcomes in assignment.

### Source Audit

| execution_variant_rows | execution_lifecycle_count | macro_lifecycle_count | state_panel_rows | representative_trade_rows | company_source_gap_rows | macro_source_gap_rows | macro_latest_vintage_gap_rows | label_used_in_assignment_flag | return_used_in_assignment_flag | gpt_review_captured_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 189102 | 5265 | 735 | 189102 | 1621 | 102554 | 171282 | 189102 | 0 | 0 | 1 |

### $1000 Account Comparison

| comparison_name | split_name | initial_capital_usd | source_trade_count | accepted_trade_count | final_capital_usd | capital_return_pct | max_drawdown_pct | avg_net_return_pct | win_rate | entry_reduce_failure_rate | qqq_final_capital_usd | task639_full_final_capital_usd | task639_full_max_drawdown_pct | beats_task639_full_flag | beats_qqq_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| task651_relation_action_strategy | all | 1000.0 | 1621 | 54 | 7341.221691631648 | 634.1221691631648 | -24.903882842912406 | 26.43398519539194 | 0.6296296296296297 | 0.35185185185185186 | 1606.8278306897957 | 7639.620310821465 | -23.755747663170705 | 0 | 1 |
| task651_relation_action_strategy | validation | 1000.0 | 655 | 15 | 1075.384598236562 | 7.538459823656196 | -39.92929875243072 | 2.5122605564289224 | 0.5333333333333333 | 0.4 | 1049.908329847512 | 0.0 | 0.0 | 0 | 1 |
| task651_relation_action_strategy | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138664 | 53.19029143138665 | -32.32547997968237 | 25.78265294363888 | 0.5 | 0.1 | 1124.192829329964 | 0.0 | 0.0 | 0 | 1 |
| task639_recomputed_positive_contract_or_supply | all | 1000.0 | 1621 | 54 | 7639.620310821465 | 663.9620310821465 | -23.755747663170702 | nan | nan | 0.37037037037037035 | 1606.8278306897957 | 7639.620310821465 | -23.755747663170705 | 0 | 1 |
| task639_recomputed_positive_contract_or_supply | validation | 1000.0 | 655 | 15 | 1069.2312936091898 | 6.923129360918989 | -7.363321689343804 | nan | nan | 0.4 | 1049.908329847512 | 0.0 | 0.0 | 0 | 1 |
| task639_recomputed_positive_contract_or_supply | recent_oos | 1000.0 | 332 | 10 | 1531.9029143138666 | 53.19029143138667 | -0.811391994497368 | nan | nan | 0.2 | 1124.192829329964 | 0.0 | 0.0 | 0 | 1 |

### Action Performance

| split_name | action_bucket | trade_count | accepted_trade_count | final_capital_usd | max_drawdown_pct | avg_return_pct | win_rate | entry_reduce_failure_rate | qqq_final_capital_usd | beats_qqq_flag | task639_final_capital_usd | beats_task639_full_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| all | CONFIRMATION_REQUIRED | 2 | 2 | 1150.7317679512923 | 0.0 | 75.86588397564614 | 1.0 | 0.0 | 1269.2808877011787 | 0 | 7639.620310821465 | 0 |
| all | NORMAL_ENTRY | 1619 | 54 | 7341.221691631648 | -24.903882842912406 | 5.702885875107691 | 0.5435453983940705 | 0.39530574428659665 | 1606.8278306897957 | 1 | 7639.620310821465 | 0 |
| train_design | CONFIRMATION_REQUIRED | 2 | 2 | 1150.7317679512923 | 0.0 | 75.86588397564614 | 1.0 | 0.0 | 1269.2808877011787 | 0 | 0.0 | 0 |
| train_design | NORMAL_ENTRY | 632 | 30 | 4924.008692522782 | -24.903882842912406 | 4.837617821118225 | 0.5126582278481012 | 0.44145569620253167 | 1363.2945157314116 | 1 | 0.0 | 0 |
| validation | NORMAL_ENTRY | 655 | 15 | 1075.384598236562 | -39.92929875243072 | 5.486202935556607 | 0.5786259541984733 | 0.3511450381679389 | 1049.908329847512 | 1 | 0.0 | 0 |
| recent_oos | NORMAL_ENTRY | 332 | 10 | 1531.9029143138664 | -32.32547997968237 | 7.77751459657547 | 0.5331325301204819 | 0.39457831325301207 | 1124.192829329964 | 1 | 0.0 | 0 |

### Relation Performance

| split_name | relation_state | trade_count | avg_return_pct | large_loss_rate | entry_reduce_failure_rate | win_rate |
| --- | --- | --- | --- | --- | --- | --- |
| all | offsetting | 2 | 75.86588397564614 | 0.0 | 0.0 | 1.0 |
| all | reinforcing | 206 | 1.8886608028977885 | 0.33495145631067963 | 0.49029126213592233 | 0.41262135922330095 |
| all | sizing_modifier | 1413 | 6.258958320171555 | 0.283793347487615 | 0.38145789101203115 | 0.5626326963906582 |
| train_design | offsetting | 2 | 75.86588397564614 | 0.0 | 0.0 | 1.0 |
| train_design | reinforcing | 64 | -5.2533019559017875 | 0.53125 | 0.609375 | 0.34375 |
| train_design | sizing_modifier | 568 | 5.974622866416253 | 0.34507042253521125 | 0.4225352112676056 | 0.5316901408450704 |
| validation | reinforcing | 54 | -1.012412436128197 | 0.3148148148148148 | 0.42592592592592593 | 0.3888888888888889 |
| validation | sizing_modifier | 601 | 6.07010514865308 | 0.24126455906821964 | 0.34442595673876875 | 0.5956738768718802 |
| recent_oos | reinforcing | 88 | 8.863019569608879 | 0.20454545454545456 | 0.4431818181818182 | 0.4772727272727273 |
| recent_oos | sizing_modifier | 244 | 7.386020999743749 | 0.2459016393442623 | 0.3770491803278688 | 0.5532786885245902 |

### Leakage Audit

| check_name | violation_count | pass_flag |
| --- | --- | --- |
| label_used_in_assignment | 0 | 1 |
| return_used_in_assignment | 0 | 1 |
| future_price_used_in_assignment | 0 | 1 |
| missing_source_used_as_direction | 0 | 1 |
| macro_release_gap_used_for_promotion | 0 | 1 |

## No-Background Decision-Maker Report

- 이제 좋은 뉴스만 보지 않고, 매크로/정책/섹터/회사/차트가 서로 밀어주는지 싸우는지 봅니다.
- 그래도 아직 실전 전략은 아닙니다.
- 매크로 원천은 최신수정치와 정확한 발표시각 문제가 남아 있어서 승격 금지입니다.
- 이번 결과는 관계엔진이 어디서 돈을 만들고 어디서 좋은 후보를 잘랐는지 보는 지도입니다.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| gpt_review_captured | 1 | captured=1 | GPT review-only implementation guidance must be captured |
| deterministic_relation_state_panel | 1 | rows=189102 | state panel must be nonempty |
| no_assignment_leakage | 1 | violations=0 | no label return future price or missing-source direction leakage |
| sparse_cells_marked | 1 | sparse_cells=0 | sparse cells must be marked research-only |
| macro_vintage_release_gap_blocks_promotion | 1 | promotion_blocked_rows=189102 | latest-vintage/release gap must block promotion |
| relation_account_beats_qqq_full | 1 | Task651=$7341.22; QQQ=$1606.83 | Task651 diagnostic account should beat full-period QQQ |
| relation_account_beats_task639_full | 0 | Task651=$7341.22; Task639_recomputed=$7639.62 | Task651 should beat recomputed Task639 to claim improvement |
| validation_beats_qqq | 1 | validation=$1075.38; qqq=$1049.91 | validation must beat same-period QQQ |
| recent_oos_beats_qqq | 1 | recent=$1531.90; qqq=$1124.19 | recent OOS must beat same-period QQQ |
| trading_promotion | 0 | diagnostic relation engine only | requires source-latency, release/vintage repair, paper-shadow replay, and live source readiness |

## Artifact Manifest

- `task_651_gate_state_panel.csv`
- `task_651_representative_execution_panel.csv`
- `task_651_action_performance.csv`
- `task_651_relation_performance.csv`
- `task_651_account_comparison.csv`
- `task_651_sparse_cell_report.csv`
- `task_651_false_block_reduce_review.csv`
- `task_651_leakage_audit.csv`
- `task_651_source_audit.csv`
- `task_651_pass_fail_matrix.csv`
- `task_651_decision.csv`
- `task_651_gpt_review_packet.md`
- `task_651_gpt_review_response.md`
- `task_651_gpt_result_review_response.md`
- `artifact_manifest.csv`