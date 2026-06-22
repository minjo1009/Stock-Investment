# Task 402R - Decision Labelability Audit

## Required Answers
- Did we use inferred lifecycle matching? `NO`
- Are unlabeled rows treated as negative? `NO`

## Decision
task_402r_verdict,evaluation_status,task401_label_coverage_sufficient,task401_exact_label_coverage_rate,exact_lifecycle_id_overlap_count,population_mismatch_status,unlabeled_treated_as_negative_flag,symbol_date_price_time_fallback_used_flag,inferred_lifecycle_matching_used_flag,strategy_acceptance_status,next_priority
COMPLETE_PASS,DECISION_LABELABILITY_AUDIT_COMPLETE,NO,0.0,0,NO_EXACT_OVERLAP,0,0,0,NOT_DEPLOYMENT_READY,task403_multi_archetype_portfolio_discovery_on_exact_labeled_population

## Population Consistency
task401_entry_candidate_count,task401_lifecycle_created_count,label_source_lifecycle_count,exact_lifecycle_id_overlap_count,task401_exact_label_coverage_rate,task401_label_coverage_sufficient,population_mismatch_status,join_key_used,symbol_date_price_time_fallback_used_flag,unlabeled_treated_as_negative_flag
206058,60588,20749,0,0.0,NO,NO_EXACT_OVERLAP,lifecycle_id_exact_only,0,0

## Labelability By Bucket
bucket,candidate_count,lifecycle_created_count,non_lifecycle_candidate_count,exact_label_count,unlabeled_lifecycle_count,label_coverage_rate,unlabeled_treated_as_negative_flag,inferred_lifecycle_matching_used_flag
ALLOW,60588,60588,0,0,60588,0.0,0,0
REJECT,101428,0,101428,0,0,0.0,0,0
WATCH,44042,0,44042,0,0,0.0,0,0