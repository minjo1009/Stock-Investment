# Task699 Source Direct Catalyst Decomposition

## Decision Summary

- Verdict: SOURCE_DIRECT_CATALYST_DECOMPOSITION_COMPLETE_RESEARCH_ONLY.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Scope: Task698 source-direct rows only, count 9.
- Main finding: Source-direct must be split by economic structure and noise; direct evidence alone is not enough.
- Best structure bucket: company_thin_direct, average costed return 62.39%.
- Next action: Build a candidate rule that requires source-direct plus catalyst structure and noise controls, then test it on the frozen 435 set.

## Quant Expert Report

### Data source and scope

- Freeze input: Task698 full candidate freeze panel.
- Evidence input: Task693 source event v2 evidence.
- Evaluation input: Task698 full candidate eval panel.
- Scope is exactly the 9 source-direct candidates from Task698.

### Freeze before outcome

- `task699_source_direct_feature_freeze.csv` contains catalyst structure, direct signal families, policy/company mix, and noise ratio.
- Outcome columns are added only in `task699_source_direct_eval_comparison.csv`.
- No allocation or live/paper trading approval is created.

### Same-Criteria Evaluation

| symbol | split_name | catalyst_structure_bucket | quality_risk_bucket | direct_economic_signature | direct_event_count | noise_ratio | costed_return_pct | qqq_costed_return_pct | outcome_group |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| SNOW | validation | company_revenue_guidance | high_noise_thin_signal | revenue\|guidance | 1 | 0.9615 | -25.5164 | -2.0133 | failure_loss_gt_10pct |
| SNOW | validation | company_revenue_guidance | high_noise_thin_signal | revenue\|guidance | 1 | 0.9630 | -23.6606 | -3.0512 | failure_loss_gt_10pct |
| ASTS | train_design | company_contract_customer_order | cleaner_company_multi_signal | contract\|customer\|order_backlog\|revenue\|guidance | 4 | 0.4286 | -13.7771 | -9.7826 | failure_loss_gt_10pct |
| BA | train_design | policy_direct_only | thin_or_mixed_signal | contract\|customer\|order_backlog\|guidance\|supply_demand | 5 | 0.7059 | 9.2209 | 9.3650 | modest_or_flat |
| CEG | validation | company_guidance_supply | high_noise_thin_signal | guidance\|supply_demand | 1 | 0.7500 | 12.8341 | 10.8437 | solid_winner |
| CEG | validation | company_guidance_supply | thin_or_mixed_signal | guidance\|supply_demand | 1 | 0.6667 | 16.3238 | 11.5655 | solid_winner |
| PH | validation | company_contract_customer_order | high_noise_multi_signal | contract\|customer\|order_backlog\|revenue\|guidance\|margin\|supply_demand | 1 | 0.8182 | 19.0517 | 0.1980 | solid_winner |
| DDOG | recent_oos | company_thin_direct | high_noise_thin_signal | contract | 1 | 0.9600 | 62.3931 | 0.8352 | large_winner |
| TER | validation | company_contract_customer_order | cleaner_company_multi_signal | contract\|customer\|order_backlog\|guidance\|supply_demand | 3 | 0.5714 | 69.3120 | 6.8739 | large_winner |

### Signal Family Summary

| dimension | value | candidate_count | avg_costed_return_pct | win_rate | avg_excess_vs_qqq_costed_pct | large_winner_count | failure_count | symbols |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| catalyst_structure_bucket | company_thin_direct | 1 | 62.3931 | 1.0000 | 61.5579 | 1 | 0 | DDOG |
| catalyst_structure_bucket | company_contract_customer_order | 3 | 24.8622 | 0.6667 | 25.7658 | 1 | 1 | ASTS\|PH\|TER |
| catalyst_structure_bucket | company_guidance_supply | 2 | 14.5790 | 1.0000 | 3.3743 | 0 | 0 | CEG\|CEG |
| catalyst_structure_bucket | policy_direct_only | 1 | 9.2209 | 1.0000 | -0.1440 | 0 | 0 | BA |
| catalyst_structure_bucket | company_revenue_guidance | 2 | -24.5885 | 0.0000 | -22.0562 | 0 | 2 | SNOW\|SNOW |
| direct_economic_signature | contract | 1 | 62.3931 | 1.0000 | 61.5579 | 1 | 0 | DDOG |
| direct_economic_signature | contract\|customer\|order_backlog\|guidance\|supply_demand | 2 | 39.2665 | 1.0000 | 31.1470 | 1 | 0 | BA\|TER |
| direct_economic_signature | contract\|customer\|order_backlog\|revenue\|guidance\|margin\|supply_demand | 1 | 19.0517 | 1.0000 | 18.8537 | 0 | 0 | PH |
| direct_economic_signature | guidance\|supply_demand | 2 | 14.5790 | 1.0000 | 3.3743 | 0 | 0 | CEG\|CEG |
| direct_economic_signature | contract\|customer\|order_backlog\|revenue\|guidance | 1 | -13.7771 | 0.0000 | -3.9945 | 0 | 1 | ASTS |
| direct_economic_signature | revenue\|guidance | 2 | -24.5885 | 0.0000 | -22.0562 | 0 | 2 | SNOW\|SNOW |
| quality_risk_bucket | cleaner_company_multi_signal | 2 | 27.7674 | 0.5000 | 29.2218 | 1 | 1 | ASTS\|TER |
| quality_risk_bucket | high_noise_multi_signal | 1 | 19.0517 | 1.0000 | 18.8537 | 0 | 0 | PH |
| quality_risk_bucket | thin_or_mixed_signal | 2 | 12.7724 | 1.0000 | 2.3071 | 0 | 0 | BA\|CEG |
| quality_risk_bucket | high_noise_thin_signal | 4 | 6.5126 | 0.5000 | 4.8590 | 1 | 2 | SNOW\|SNOW\|CEG\|DDOG |

### Failure vs Winner Contrast

| contrast_group | candidate_count | symbols | avg_costed_return_pct | avg_direct_signal_family_count | avg_noise_ratio | common_structure_buckets | diagnostic |
| --- | --- | --- | --- | --- | --- | --- | --- |
| failures_asts_snow | 3 | SNOW\|SNOW\|ASTS | -20.9847 | 3.0000 | 0.7844 | company_revenue_guidance\|company_contract_customer_order | Failures had direct company events but suffered from high noise or thin revenue/guidance-only structures. |
| large_winners_ter_ddog | 2 | DDOG\|TER | 65.8526 | 3.0000 | 0.7657 | company_thin_direct\|company_contract_customer_order | Large winners combined direct evidence with either contract/order/guidance mix or a cleaner single hard catalyst. |
| middle_ba_ceg_ph | 4 | BA\|CEG\|CEG\|PH | 14.3576 | 4.0000 | 0.7352 | company_guidance_supply\|policy_direct_only\|company_contract_customer_order | Middle group had positive but less explosive catalyst translation. |

### Interpretation

- Source-direct is not one thing. It splits into company contract/order structures, company guidance/supply structures, thin revenue/guidance structures, and policy-assisted structures.
- ASTS and SNOW failed despite direct evidence. Their issue is not absence of evidence; it is evidence quality, noise mix, and weak price/economic translation.
- TER and DDOG won because the direct evidence translated into a cleaner economic structure or a hard catalyst.
- Price and source should be combined later, but source-direct alone should first pass structure and noise controls.

### Split/OOS metrics

- The 9 rows include train-design, validation, and recent-OOS cases.
- This task is diagnostic only because the sample is small and uses outcome only after freeze.

### Remaining blockers

- Build the next rule on frozen features only.
- Do not promote direct evidence alone.
- Require catalyst structure plus noise control before any allocation test.

## No-Background Decision-Maker Report

- What happened: source-direct 9개를 같은 기준으로 다시 깠습니다.
- Result: source-direct 안에서도 좋은 놈과 나쁜 놈이 갈립니다.
- Simple answer: 직접 호재만으로는 부족합니다. 직접 호재 + 경제 구조 + 잡음 통제가 필요합니다.
- Capital status: still FORBIDDEN.

## Artifact Manifest

- Inputs: Task693 source event evidence, Task698 freeze/eval panels.
- Outputs: source-direct feature freeze, eval comparison, signal family summary, failure/success contrast, audit, decision, pass/fail, manifest.
- Row counts: freeze 9, eval 9, summary 15, contrast 3.
- Validation commands: `python src/backtest/build_task699_source_direct_catalyst_decomposition.py`; `python -m unittest tests.test_task699_source_direct_catalyst_decomposition`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| source_direct_scope_9 | PRIMARY_PASS | 1 | rows=9; symbols=ASTS,BA,CEG,DDOG,PH,SNOW,TER | Task699 scope must be the 9 Task698 source-direct rows |
| freeze_has_no_outcomes | PRIMARY_PASS | 1 | none | Source-direct feature freeze cannot include outcome columns |
| direct_family_features_present | PRIMARY_PASS | 1 | feature_rows=9 | Every source-direct row needs economic family and risk buckets |
| eval_exact_rows | PRIMARY_PASS | 1 | eval_rows=9 | Every frozen source-direct row must have one evaluation row |
| failure_success_contrast_present | PRIMARY_PASS | 1 | failures_asts_snow\|large_winners_ter_ddog\|middle_ba_ceg_ph | Contrast must compare failures, large winners, and middle cases |
| no_strategy_or_trade_promotion | PRIMARY_PASS | 1 | allocation_approved=0; paper_or_live_trade_approved=0 | Task699 is diagnostic only |
