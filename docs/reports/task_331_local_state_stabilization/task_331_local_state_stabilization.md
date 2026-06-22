# Task 331: Local State Stabilization

## Core Answer

- Decision: `current_state_model_requires_broader_rebuild`.
- Recommended candidate: `local_A`.
- This report identifies which vulnerable states should be refined first and whether local stabilization can improve OOS robustness without rebuilding the whole state model.

## Top Vulnerable States

| proposed_state_model | oos_expectancy_r | expectancy_delta | contribution_to_oos_underperformance |
| --- | --- | --- | --- |
| extension_pressure:medium|trend_quality:neutral|participation_quality:narrow | -0.368241 | -1.19195 | 0.529062 |
| extension_pressure:medium|trend_quality:neutral|participation_quality:broad | -0.663856 | -1.78848 | 0.230469 |
| extension_pressure:medium|trend_quality:strong|participation_quality:broad | -1.91625 | -2.97172 | 0.099282 |
| extension_pressure:high|trend_quality:strong|participation_quality:mixed | -1.48334 | -1.54942 | 0.05916 |
| extension_pressure:medium|trend_quality:strong | -0.39446 | -0.360625 | 0.043029 |

## Candidate Comparison

| candidate | description | between_state_expectancy_dispersion | within_state_realized_r_variance_mean | within_state_path_entropy_mean | oos_linkage_retention | vulnerable_bucket_concentration | state_count | avg_train_trades_per_state | avg_oos_trades_per_state | sparsity_risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| current_task_329 | current Task 329 base model | 0.496093 | 3.3205 | 1.50612 | -0.472453 | 0.858813 | 18 | 98.5556 | 20.1 | 0.611111 |
| local_A | vulnerable bucket split only | 0.538274 | 3.61703 | 1.70854 | 1.39464 | 0.848507 | 23 | 88.7 | 25.125 | 0.826087 |
| local_B | vulnerable bucket split + local noise conditioning | 0.567262 | 3.67701 | 1.71789 | 1.26786 | 0.848507 | 25 | 80.6364 | 25.125 | 0.84 |
| local_C | local_B + sparse bucket merge | 0.448439 | 3.953 | 1.80377 | 1.1598 | 0.833467 | 18 | 104.353 | 25.125 | 0.611111 |

## Local Revision Plan

| revision_id | target_state | local_change | rationale | expected_benefit | priority |
| --- | --- | --- | --- | --- | --- |
| LR1 | extension_pressure:medium|trend_quality:neutral|participation_quality:broad | split_by_noise_pressure_state | best local split by entropy/variance/retention score | reduce internal contradiction inside vulnerable bucket | 1 |
| LR2 | extension_pressure:medium|trend_quality:neutral|participation_quality:narrow | split_by_noise_pressure_state | best local split by entropy/variance/retention score | reduce internal contradiction inside vulnerable bucket | 2 |
| LR3 | extension_pressure:medium|trend_quality:strong|participation_quality:broad | split_by_ret_20d_pre_band | best local split by entropy/variance/retention score | reduce internal contradiction inside vulnerable bucket | 3 |
| LR4 | extension_pressure:high|trend_quality:neutral|participation_quality:broad | merge_into_extension_pressure:high|trend_quality:neutral | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 4 |
| LR5 | extension_pressure:high|trend_quality:strong|participation_quality:broad | merge_into_extension_pressure:high|trend_quality:strong | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 5 |
| LR6 | extension_pressure:high|trend_quality:strong|participation_quality:mixed | merge_into_extension_pressure:high|trend_quality:strong | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 6 |
| LR7 | extension_pressure:low|trend_quality:neutral|participation_quality:broad | merge_into_extension_pressure:low|trend_quality:neutral | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 7 |
| LR8 | extension_pressure:low|trend_quality:neutral|participation_quality:mixed | merge_into_extension_pressure:low|trend_quality:neutral | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 8 |
| LR9 | extension_pressure:low|trend_quality:weak|participation_quality:narrow | merge_into_extension_pressure:low|trend_quality:weak | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 9 |
| LR10 | extension_pressure:medium|trend_quality:neutral|participation_quality:broad|local:noise_pressure_state=balanced|noise:balanced | merge_into_extension_pressure:medium|trend_quality:neutral|participation_quality:broad|local:noise_pressure_state=balanced | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 10 |
| LR11 | extension_pressure:medium|trend_quality:neutral|participation_quality:broad|local:noise_pressure_state=compressed|noise:compressed | merge_into_extension_pressure:medium|trend_quality:neutral|participation_quality:broad|local:noise_pressure_state=compressed | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 11 |
| LR12 | extension_pressure:medium|trend_quality:neutral|participation_quality:broad|local:noise_pressure_state=high_noise|noise:high_noise | merge_into_extension_pressure:medium|trend_quality:neutral|participation_quality:broad|local:noise_pressure_state=high_noise | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 12 |
| LR13 | extension_pressure:medium|trend_quality:neutral|participation_quality:narrow|local:noise_pressure_state=high_noise|noise:high_noise | merge_into_extension_pressure:medium|trend_quality:neutral|participation_quality:narrow|local:noise_pressure_state=high_noise | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 13 |
| LR14 | extension_pressure:medium|trend_quality:strong|participation_quality:broad|local:ret_20d_pre_band=high|noise:balanced | merge_into_extension_pressure:medium|trend_quality:strong|participation_quality:broad|local:ret_20d_pre_band=high | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 14 |
| LR15 | extension_pressure:medium|trend_quality:strong|participation_quality:broad|local:ret_20d_pre_band=high|noise:compressed | merge_into_extension_pressure:medium|trend_quality:strong|participation_quality:broad|local:ret_20d_pre_band=high | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 15 |
| LR16 | extension_pressure:medium|trend_quality:strong|participation_quality:broad|local:ret_20d_pre_band=high|noise:high_noise | merge_into_extension_pressure:medium|trend_quality:strong|participation_quality:broad|local:ret_20d_pre_band=high | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 16 |
| LR17 | extension_pressure:medium|trend_quality:weak|participation_quality:narrow | merge_into_extension_pressure:medium|trend_quality:weak | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 17 |
| LR18 | extension_pressure:medium|trend_quality:neutral|participation_quality:mixed | merge_into_extension_pressure:medium|trend_quality:neutral | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 18 |
| LR19 | extension_pressure:medium|trend_quality:strong|participation_quality:mixed | merge_into_extension_pressure:medium|trend_quality:strong | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 19 |
| LR20 | extension_pressure:high|trend_quality:neutral | merge_into_extension_pressure:high | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 20 |
| LR21 | extension_pressure:high | merge_into_extension_pressure:high | sparse local split with low separation benefit | reduce state explosion and sample sparsity | 21 |