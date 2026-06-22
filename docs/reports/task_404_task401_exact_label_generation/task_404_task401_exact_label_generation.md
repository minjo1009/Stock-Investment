# Task 404 - Task401 Exact Label Generation

## Required Answers
- Did we use inferred lifecycle matching? `NO`
- Are unlabeled rows treated as negative? `NO`

## Decision
task_404_verdict,evaluation_status,task401_allow_lifecycle_created_count,task401_allow_exact_label_count,task401_allow_exact_label_coverage_rate,task401_exact_label_coverage_sufficient,unlabeled_treated_as_negative_flag,symbol_date_price_time_fallback_used_flag,inferred_lifecycle_matching_used_flag,deployment_claim_flag,strategy_acceptance_status,next_priority
COMPLETE_PASS,TASK401_EXACT_LABEL_PATH_REPAIRED,60588,60519,0.9988611606258665,YES,0,0,0,0,NOT_DEPLOYMENT_READY,task405_refined_archetype_portfolio_rebuild

## Coverage
bucket,candidate_count,lifecycle_created_count,exact_label_count,unlabeled_lifecycle_count,non_lifecycle_candidate_count,exact_label_coverage_rate,unlabeled_treated_as_negative_flag,symbol_date_price_time_fallback_used_flag
ALLOW,60588,60588,60519,69,0,0.9988611606258665,0,0
REJECT,101428,0,0,0,101428,0.0,0,0
WATCH,44042,0,0,0,44042,0.0,0,0

## Label Quality
lifecycle_outcome_class,lifecycle_count,avg_net_return_from_entry
entry_reduce_failure,21061,-0.018179926684575413
add_only_weak,12512,0.0010997243072097525
add_scale_success,11371,0.024690023160481408
post_cost_false_positive,8051,-0.014762025312058493
post_cost_positive_no_add_scale,7524,0.0029085035864702055