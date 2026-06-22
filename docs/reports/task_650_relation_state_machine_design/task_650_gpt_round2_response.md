# Task650 GPT Round 2 Response

Captured via Chrome ChatGPT project tab.

## Summary

- Task650 should remain a design report.
- Task651 should implement the deterministic algorithm.
- The correct implementation is a sequential gate and relation resolver, not a score model.

## Implementable Gate Order

1. Source Integrity Gate.
2. Macro Context Gate.
3. Policy/Geopolitical Conflict Gate.
4. Sector/Theme Alignment Gate.
5. Company Catalyst Quality Gate.
6. Chart Confirmation Gate.
7. Relation Resolver.
8. Action Mapper.

## Output Contract

The future implementation should produce:

- entry_id
- source_gate_state
- macro_gate_state
- policy_geo_gate_state
- sector_gate_state
- company_gate_state
- chart_gate_state
- relation_state
- final_context_state
- action_bucket
- action_reason_codes
- research_only_flag

## Validation Requirements

- Split validation: train_design, validation, recent_oos, full_panel.
- Account validation: $1000 starting capital, same cost/slippage assumptions, same constraints.
- Benchmarks: QQQ and Task639.
- Relation-level and action-level performance tables.
- Sparse cells must remain research-only.
- Leakage audit must confirm no labels, returns, future prices, or future source revisions enter assignment.

## Pass Forward Conditions

- Gate definitions complete.
- Relation taxonomy complete.
- Action taxonomy complete.
- Forbidden inputs explicit.
- Sparse-cell policy explicit.
- Validation tables specified.

## Discard Conditions

- Train-only success.
- Recent-only success with validation/full collapse.
- Sparse sample cells.
- Any release/vintage gap used as if resolved.
- Source gaps treated as positive or negative.
- Macro-only entry.
- Global chart confirmation filter.

## What Not To Implement Yet

- Complex score models.
- Machine-learning classifier.
- Automatic regime-switch optimizer.
- Strong macro_hostile rules from six observations.
- Deployment/live trading logic.
