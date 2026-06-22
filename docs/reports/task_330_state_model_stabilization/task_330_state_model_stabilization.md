# Task 330: State Model Stabilization

## Core Answer

- Current bottleneck: `OOS linkage instability concentrated in vulnerable strong-trend buckets`.
- Decision: `keep_current_task_329_state_model_as_is`.
- Recommended candidate: `candidate_B`.

## Top Vulnerable Buckets

| proposed_state_model | oos_expectancy_r | expectancy_delta | contribution_to_oos_underperformance |
| --- | --- | --- | --- |
| extension_pressure:medium|trend_quality:neutral|participation_quality:narrow | -0.368241 | -1.19195 | 0.529062 |
| extension_pressure:medium|trend_quality:neutral|participation_quality:broad | -0.663856 | -1.78848 | 0.230469 |
| extension_pressure:medium|trend_quality:strong|participation_quality:broad | -1.91625 | -2.97172 | 0.099282 |

## Best Candidate Comparison

| candidate | description | between_state_expectancy_dispersion | within_state_realized_r_variance_mean | within_state_path_entropy_mean | oos_linkage_retention | vulnerable_bucket_concentration | state_count | avg_train_trades_per_state | avg_oos_trades_per_state | sparsity_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| candidate_B | stronger structural split | 0.684402 | 3.09448 | 1.41192 | 0.528067 | 0.860271 | 21 | 84.4762 | 18.2727 | 0.666667 |
| candidate_A | minimal stabilization revision | 0.478667 | 3.86854 | 1.59806 | 0.300814 | 0.850858 | 18 | 98.5556 | 18.2727 | 0.611111 |
| candidate_C | optional axis reintroduction | 0.524934 | 3.00853 | 1.57898 | 0.053269 | 0.630312 | 29 | 61.1724 | 13.4 | 0.689655 |

## Recommended Structural Revisions

| revision_id | change_type | rationale | expected_benefit | complexity | priority |
| --- | --- | --- | --- | --- | --- |
| R1 | split_vulnerable_strong_trend_state | top vulnerable bucket=extension_pressure:medium|trend_quality:neutral|participation_quality:narrow | reduce OOS linkage failure inside strong-trend states | medium | 1 |
| R2 | reintroduce_secondary_failure_axis | best omitted axis signal=noise_pressure | improve failure-mode isolation without rebuilding the full state model | medium | 2 |
| R3 | merge_sparse_low_value_states | best refined candidate=candidate_B | reduce sparsity risk while preserving payoff separation | low | 3 |