# Task675 Exposure Cluster Audit

## Decision Summary

- Verdict: `EXPOSURE_CLUSTER_AUDIT_BUILT_DIAGNOSTIC_ONLY`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

## Quant Expert Report

This task uses current entry-time data only. It does not use microstructure, future returns, future labels, symbol blacklist, or theme blacklist for assignment.

### Exposure Cluster

| candidate_name | mdd_peak_ts | mdd_trough_ts | max_drawdown_pct | audit_axis | axis_value | active_trade_count | avg_return_costed_pct_eval_only | assignment_used_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | dominant_driver | neutral_driver | 5 | 73.9016748273057 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | dominant_driver | credit | 3 | -19.538359562544088 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | dominant_driver | multi_driver | 3 | 1.0117900457246622 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | dominant_driver | dollar | 2 | 18.653085231035394 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | exposure_cluster_state | exposure_clean | 10 | 21.179004942532448 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | exposure_cluster_state | exposure_warning_cluster | 3 | 46.48159554093883 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | price_chart_acceptance_state | price_confirmed_basic | 7 | -2.673349914133867 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | price_chart_acceptance_state | price_confirmed_but_extended | 4 | 17.645820802265668 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | price_chart_acceptance_state | price_accepted_needs_confirmation | 1 | 41.7811595585902 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | price_chart_acceptance_state | price_fragile_or_unconfirmed | 1 | 257.5838426794252 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | relation_transmission_state | company_price_confirmed_macro_secondary | 4 | 27.98113286427582 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | relation_transmission_state | relation_reinforcing | 4 | -2.2979551620908896 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | relation_transmission_state | company_positive_confirmation_needed | 3 | 98.29667104716532 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | relation_transmission_state | relation_offsetting | 2 | -23.19394395104736 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | setup_quality_bucket | medium_quality_setup | 7 | 21.607742080968784 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | setup_quality_bucket | high_quality_setup | 5 | -11.520640239613138 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | setup_quality_bucket | fragile_setup | 1 | 257.5838426794252 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | theme_id | aerospace_defense_space | 5 | 73.9016748273057 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | theme_id | power_grid_electrification | 4 | -17.596723576500448 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | theme_id | cybersecurity | 2 | 18.653085231035394 | 0 |
| action_permission_research_block | 2024-12-05 00:00:00+00:00 | 2025-06-03 00:00:00+00:00 | -20.010033696148323 | theme_id | data_devops_software | 2 | 7.403592877771759 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | dominant_driver | liquidity | 4 | -18.58307210654833 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | dominant_driver | neutral_driver | 4 | 13.52892004092362 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | dominant_driver | multi_driver | 3 | -0.6276078688545641 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | dominant_driver | credit | 2 | 13.214976999711524 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | dominant_driver | rates | 2 | 15.108173335029385 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | exposure_cluster_state | exposure_concentrated | 8 | -10.754299712604695 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | exposure_cluster_state | exposure_clean | 6 | 6.116580276079773 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | exposure_cluster_state | exposure_warning_cluster | 1 | 83.88178484477822 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | price_chart_acceptance_state | price_confirmed_basic | 12 | 0.004943509999700188 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | price_chart_acceptance_state | price_confirmed_but_extended | 2 | 28.453905520865774 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | price_chart_acceptance_state | price_fragile_or_unconfirmed | 1 | -22.42026436130865 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | relation_transmission_state | relation_reinforcing | 5 | -6.123643082981395 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | relation_transmission_state | company_positive_confirmation_needed | 3 | -9.922034893694581 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | relation_transmission_state | relation_offsetting | 3 | 2.5736983732513985 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | relation_transmission_state | company_price_confirmed_macro_secondary | 2 | 36.87072850836575 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | relation_transmission_state | relation_sparse_research_only | 2 | 6.734318379962153 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | setup_quality_bucket | high_quality_setup | 8 | -1.3177745716118654 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | setup_quality_bucket | medium_quality_setup | 5 | 6.3240857226779825 | 0 |
| active_relation_cap3_reference | 2025-02-06 00:00:00+00:00 | 2025-06-02 00:00:00+00:00 | -30.524857842425657 | setup_quality_bucket | research_only_setup | 2 | 6.734318379962153 | 0 |

### Pass Fail

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| exposure_cluster_audit_built | 1 | rows=225 | MDD exposure cluster audit |
| assignment_not_used | 1 | assignment_used=0 | 0 assignment use |
| mdd_hindsight_not_promoted | 1 | audit only | no MDD-only cap promotion |

## No-Background Decision-Maker Report

이번 작업은 바로 실전 매매로 승격하지 않습니다.

상태를 더 쪼개고, 슬롯 경쟁과 동시 노출을 분리해서 다음 매매 룰 후보가 과최적화인지 확인하는 단계입니다.

## Artifact Manifest

- See `artifact_manifest.csv`.
