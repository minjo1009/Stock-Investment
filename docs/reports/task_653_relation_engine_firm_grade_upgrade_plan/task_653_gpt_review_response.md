# Task653 GPT Review Response Summary

GPT agreed that the relation engine idea is not invalid, but the current implementation is not firm-grade.

Main review points:

- Data coverage is the first failure. Macro context covers only 735 lifecycles while execution covers 5265. Only 495 lifecycles overlap. This means the relation engine is being asked to judge many rows where macro context is not actually available.
- Source gaps must not be treated as tradable states. Missing macro should not upgrade, downgrade, block, or size a trade.
- The code needs row-level join contracts. Aggregate source gap counts are not enough.
- The engine needs a baseline preservation audit. Every Task639 candidate must be traced into kept, upgraded, reduced, delayed, blocked, research-only, or no-action buckets.
- Taxonomy labels are too strong. Names like reinforcing and strong_company_positive sound tradable, but their measured performance does not justify full-entry authority.
- Latest-vintage macro gaps must be diagnostic only and cannot be used for promotion.
- The next step should not be more source types. The next step should be coverage scope, join audit, baseline preservation, taxonomy permission split, action transition audit, and promotion eligibility.

GPT recommended Task654 deliverables:

- coverage_scope_report.csv
- join_contract_audit.csv
- baseline_preservation_audit.csv
- taxonomy_definition_vs_performance.csv
- action_transition_matrix.csv
- promotion_eligibility_report.csv

GPT pass criteria:

- Task639 baseline is reproduced.
- Macro, company, and source gaps do not contaminate action logic.
- Latest-vintage macro gaps cannot promote a rule.
- Task639 candidate damage path is explained.
- Taxonomy names are separated from action permissions.

GPT fail criteria:

- Missing macro is used as a relation.
- Source gaps create actions.
- Latest-vintage gaps enter promotion.
- Task639 candidates are blocked or reduced without an audit trail.
- Strong-sounding state names grant full entry without empirical validation.
