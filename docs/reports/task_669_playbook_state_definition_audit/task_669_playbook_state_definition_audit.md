# Task669 Playbook State Definition Audit

## Decision Summary

- Verdict: `PLAYBOOK_STATE_DEFINITION_AUDIT_REDEFINITION_REQUIRED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Mixed states: `6`
- Redefinition candidates: `6`

## Quant Expert Report

Task669 audits whether Task668 playbook names represent coherent states. It does not add a new trading rule.

### State Purity Audit

| playbook_id | candidate_count | candidate_share | unique_market_states | unique_theme_states | unique_relation_states | unique_catalyst_tiers | unique_price_states | top_component_count | top_component_share | mixed_state_flag | sparse_sample_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| normal_participation | 811 | 0.500308451573103 | 3 | 5 | 4 | 4 | 1 | 139 | 0.17139334155363747 | 1 | 0 |
| confirmation_required | 291 | 0.17951881554595928 | 3 | 6 | 4 | 4 | 2 | 42 | 0.14432989690721648 | 1 | 0 |
| rotation_selective | 271 | 0.16718075262183837 | 3 | 3 | 3 | 2 | 1 | 49 | 0.18081180811808117 | 1 | 0 |
| research_only_sparse | 156 | 0.09623689080814313 | 3 | 5 | 1 | 3 | 2 | 24 | 0.15384615384615385 | 1 | 0 |
| defensive_research_only | 59 | 0.03639728562615669 | 1 | 1 | 4 | 3 | 2 | 50 | 0.847457627118644 | 1 | 0 |
| narrow_leader_selective | 6 | 0.003701418877236274 | 2 | 1 | 2 | 2 | 1 | 1 | 0.16666666666666666 | 1 | 1 |
| aggressive_leadership | 27 | 0.016656384947563233 | 1 | 2 | 1 | 2 | 1 | 15 | 0.5555555555555556 | 0 | 1 |

### Performance Audit

| candidate_name | split_scope | playbook_id | trade_count | avg_return_pct | win_rate | entry_reduce_failure_rate | avg_size_multiplier | high_return_state_flag | high_failure_state_flag | sparse_performance_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | all | narrow_leader_selective | 2 | 148.81295552164278 | 1.0 | 0.0 | 1.0 | 1 | 0 | 1 |
| active_relation_cap3_reference | all | confirmation_required | 12 | 67.24337833470747 | 0.75 | 0.25 | 1.0 | 1 | 0 | 0 |
| active_relation_cap3_reference | all | normal_participation | 20 | 23.63617411227888 | 0.65 | 0.3 | 1.0 | 0 | 0 | 0 |
| active_relation_cap3_reference | all | rotation_selective | 7 | 16.283858578058958 | 0.5714285714285714 | 0.4285714285714285 | 1.0 | 0 | 1 | 0 |
| active_relation_cap3_reference | all | research_only_sparse | 5 | 7.337208306057525 | 0.6 | 0.4 | 1.0 | 0 | 1 | 0 |
| active_relation_cap3_reference | all | defensive_research_only | 5 | 2.153745820710992 | 0.4 | 0.6 | 1.0 | 0 | 1 | 0 |

### MDD State Audit

| candidate_name | audit_group | group_value | active_trade_count | avg_return_costed_pct | avg_size_multiplier | negative_mdd_exposure_flag |
| --- | --- | --- | --- | --- | --- | --- |
| active_relation_cap3_reference | mechanism_relation_state | mechanism_reinforcing_company_positive | 5 | -6.123643082981395 | 1.0 | 1 |
| active_relation_cap3_reference | mechanism_relation_state | company_positive_needs_confirmation | 3 | -9.92203489369458 | 1.0 | 1 |
| active_relation_cap3_reference | mechanism_relation_state | mechanism_offsetting_company_positive | 3 | 2.5736983732513985 | 1.0 | 0 |
| active_relation_cap3_reference | mechanism_relation_state | company_quality_price_confirmed | 2 | 36.87072850836575 | 1.0 | 0 |
| active_relation_cap3_reference | mechanism_relation_state | sparse_mechanism_cell | 2 | 6.734318379962153 | 1.0 | 0 |
| active_relation_cap3_reference | playbook_id | rotation_selective | 5 | 11.64069469339794 | 1.0 | 0 |
| active_relation_cap3_reference | playbook_id | normal_participation | 4 | -19.700507478601057 | 1.0 | 1 |
| active_relation_cap3_reference | playbook_id | confirmation_required | 2 | 30.69326664723683 | 1.0 | 0 |
| active_relation_cap3_reference | playbook_id | defensive_research_only | 2 | -9.854872403282071 | 1.0 | 1 |
| active_relation_cap3_reference | playbook_id | research_only_sparse | 2 | 6.734318379962153 | 1.0 | 0 |
| active_relation_cap3_reference | theme_id | data_devops_software | 4 | -6.075771991968086 | 1.0 | 1 |
| active_relation_cap3_reference | theme_id | power_grid_electrification | 4 | 14.161575167370454 | 1.0 | 0 |
| active_relation_cap3_reference | theme_id | biotech_glp1_healthcare | 3 | -9.873846868298244 | 1.0 | 1 |
| active_relation_cap3_reference | theme_id | cybersecurity | 3 | -17.352196047024556 | 1.0 | 1 |
| active_relation_cap3_reference | theme_id | aerospace_defense_space | 1 | 83.88178484477822 | 1.0 | 0 |
| active_relation_cap3_reference | theme_state | neutral_participation | 5 | -11.055406655992064 | 1.0 | 1 |
| active_relation_cap3_reference | theme_state | leadership_fading | 4 | 10.41919712197738 | 1.0 | 0 |
| active_relation_cap3_reference | theme_state | re_acceleration | 4 | 17.085950323759103 | 1.0 | 0 |
| active_relation_cap3_reference | theme_state | defensive_rotation | 2 | -10.09834385128316 | 1.0 | 1 |

### Playbook Catalyst Matrix

| playbook_id | catalyst_quality_tier | mechanism_relation_state | theme_state | trade_count | avg_return_pct | win_rate | entry_reduce_failure_rate |
| --- | --- | --- | --- | --- | --- | --- | --- |
| confirmation_required | medium_catalyst | company_positive_needs_confirmation | neutral_participation | 2 | 234.0974797323181 | 1.0 | 0.0 |
| confirmation_required | strong_catalyst | company_quality_price_confirmed | leadership_fading | 2 | 118.78166477590003 | 1.0 | 0.0 |
| confirmation_required | very_strong_catalyst | mechanism_reinforcing_company_positive | leadership_fading | 2 | 17.33482850233459 | 0.5 | 0.5 |
| confirmation_required | medium_catalyst | company_positive_needs_confirmation | leadership_fading | 1 | 3.00291980243113 | 1.0 | 0.0 |
| confirmation_required | strong_catalyst | mechanism_offsetting_company_positive | leadership_fading | 1 | -22.49525155030457 | 0.0 | 1.0 |
| confirmation_required | strong_catalyst | mechanism_reinforcing_company_positive | leadership_fading | 1 | 4.36050668850632 | 1.0 | 0.0 |
| confirmation_required | very_strong_catalyst | company_quality_price_confirmed | leadership_fading | 1 | 83.88178484477822 | 1.0 | 0.0 |
| confirmation_required | very_strong_catalyst | mechanism_offsetting_company_positive | leadership_fading | 1 | -12.54472898563392 | 0.0 | 1.0 |
| confirmation_required | weak_catalyst | company_positive_needs_confirmation | leadership_fading | 1 | 10.2873631956071 | 1.0 | 0.0 |
| defensive_research_only | medium_catalyst | company_positive_needs_confirmation | leadership_fading | 4 | -7.45709691191854 | 0.25 | 0.75 |
| defensive_research_only | medium_catalyst | mechanism_offsetting_company_positive | leadership_fading | 1 | 40.59711675122911 | 1.0 | 0.0 |
| narrow_leader_selective | strong_catalyst | company_quality_price_confirmed | narrow_leadership | 1 | 154.71978612194286 | 1.0 | 0.0 |
| narrow_leader_selective | very_strong_catalyst | company_quality_price_confirmed | narrow_leadership | 1 | 142.90612492134272 | 1.0 | 0.0 |
| normal_participation | strong_catalyst | mechanism_reinforcing_company_positive | neutral_participation | 8 | 16.487955876272814 | 0.625 | 0.25 |
| normal_participation | very_strong_catalyst | mechanism_reinforcing_company_positive | neutral_participation | 5 | 4.891601001914722 | 0.6 | 0.4 |
| normal_participation | medium_catalyst | company_positive_needs_confirmation | neutral_participation | 4 | 84.35253508166447 | 1.0 | 0.0 |
| normal_participation | medium_catalyst | company_positive_needs_confirmation | defensive_rotation | 2 | -0.1681684581785456 | 0.5 | 0.5 |
| normal_participation | very_strong_catalyst | company_quality_price_confirmed | neutral_participation | 1 | -20.711973184479298 | 0.0 | 1.0 |
| research_only_sparse | medium_catalyst | sparse_mechanism_cell | neutral_participation | 1 | -22.42026436130865 | 0.0 | 1.0 |
| research_only_sparse | strong_catalyst | sparse_mechanism_cell | leadership_expanding | 1 | 41.60409204561185 | 1.0 | 0.0 |

### Redefinition Candidates

| playbook_id | redefinition_required_flag | reason | promotion_allowed_flag | recommended_next_check |
| --- | --- | --- | --- | --- |
| confirmation_required | 1 | mixed_components+name_may_understate_positive_payoff | 0 | split by catalyst quality, relation state, theme leadership state, and MDD exposure before any action mapping |
| defensive_research_only | 1 | mixed_components+high_entry_reduce_failure+negative_mdd_exposure | 0 | split by catalyst quality, relation state, theme leadership state, and MDD exposure before any action mapping |
| narrow_leader_selective | 1 | mixed_components+name_may_understate_positive_payoff | 0 | split by catalyst quality, relation state, theme leadership state, and MDD exposure before any action mapping |
| normal_participation | 1 | mixed_components+negative_mdd_exposure | 0 | split by catalyst quality, relation state, theme leadership state, and MDD exposure before any action mapping |
| research_only_sparse | 1 | mixed_components+high_entry_reduce_failure | 0 | split by catalyst quality, relation state, theme leadership state, and MDD exposure before any action mapping |
| rotation_selective | 1 | mixed_components+high_entry_reduce_failure | 0 | split by catalyst quality, relation state, theme leadership state, and MDD exposure before any action mapping |

## No-Background Decision-Maker Report

현재 playbook 이름들이 아직 충분히 깨끗하지 않습니다.

`confirmation_required`만 문제가 아니라 `normal_participation`, `rotation_selective`, `research_only_sparse`도 여러 상태가 섞여 있습니다.

그래서 지금 단계에서 새 매매룰을 더 붙이면 과최적화 위험이 큽니다. 먼저 상태 정의를 다시 쪼개야 합니다.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| component_mix_built | 1 | rows=134 | playbook component mix exists |
| state_purity_audit_built | 1 | rows=7 | state purity audit exists |
| performance_audit_built | 1 | rows=6 | playbook performance audit exists |
| mdd_state_audit_built | 1 | rows=19 | MDD state audit exists |
| catalyst_matrix_built | 1 | rows=28 | playbook catalyst matrix exists |
| redefinition_required | 1 | states=6 | mixed or misleading states are identified |
| strategy_accepted | 0 | research diagnostic only | requires accepted strategy gates and live readiness |

## Artifact Manifest

- `task669_state_component_mix.csv`
- `task669_state_purity_audit.csv`
- `task669_state_performance_audit.csv`
- `task669_mdd_state_audit.csv`
- `task669_playbook_catalyst_matrix.csv`
- `task669_redefinition_candidates.csv`
- `task_669_gpt_review_packet.md`
- `task_669_gpt_review_response.md`
- `task_669_decision.csv`
- `task_669_pass_fail_matrix.csv`
- `artifact_manifest.csv`
