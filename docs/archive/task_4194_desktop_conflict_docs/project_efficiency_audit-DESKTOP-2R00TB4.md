# Project Efficiency Audit

## Executive Summary

- Total tracked workspace files scanned: 309,471
- Total scanned size: 84.9GB
- docs/reports directories: 784
- src/backtest Python files: 437

The project is currently carrying research history, canonical infrastructure, generated CSV panels, markdown reports, and task-specific builders in the same working tree. The main inefficiency is not one bad file; it is the lack of lifecycle rules for artifacts and task code.

## Main Inefficiencies

1. Task-specific code is mixed with reusable engine code in `src/backtest`.
2. Large generated CSV artifacts live under `docs/reports`, making reports both documentation and data storage.
3. Each task creates a bespoke builder/analysis pair, so repeated report-writing, split-quality, leakage-audit, and grid-search logic is copied.
4. Markdown reports are not tiered. There is no clear separation between executive summary, quant audit, and raw artifact manifest.
5. Subagent handoff is mostly conversational. There is no stable local task packet format that says input/output/write-scope/validation.

## Recommended Architecture

### 1. Keep Canonical Code Small

Create a narrow reusable layer:

- `src/backtest/core/`: lifecycle, split, metric, cost-stress, leakage-audit utilities
- `src/backtest/experiments/`: task-specific experiment specs only
- `src/backtest/reports/`: report renderers shared by all tasks
- `src/data/`: raw source collectors and source contracts

Task files should become thin spec files, not full bespoke pipelines.

### 2. Split Artifact Storage

- Keep markdown and small decision CSVs in `docs/reports`.
- Move large panels to `data/artifacts/<task_id>/` or `data/derived/<task_id>/`.
- Keep only manifests and relative artifact links in reports.
- Add an archive policy: old non-canonical task panels can be compressed or moved to `archive/reports` after a milestone.

### 3. Standardize Report Shape

Every new task report should have exactly these sections:

- `Decision Summary`: pass/fail, status, next action
- `Quant Expert Report`: exact metrics, leakage, OOS/split, failure decomposition
- `No-Background Decision-Maker Report`: simple implication and risk
- `Artifact Manifest`: generated files, source inputs, row counts, hashes if applicable

### 4. Standardize Subagent Packets

Use one handoff template per delegated task:

- Objective
- Read scope
- Write scope
- Inputs
- Required outputs
- Forbidden actions
- Validation command

This prevents parallel agents from duplicating exploration or writing over each other.

### 5. Introduce Task Registry

Create a machine-readable registry:

- `tasks/task_registry.csv`: task_id, status, canonical_flag, parent_task, key_report, key_artifacts, validation_command
- Mark old tasks as `archived`, current canonical tasks as `active`, and failed branches as `superseded`.

## Size Summary By Top Directory

```csv
top_dir,file_count,size_bytes,size_human
data,178620,78413220040,73.0GB
docs,4959,6160646334,5.7GB
.git,61675,4242340688,4.0GB
frontend,8787,924398585,881.6MB
frontend_data,6,404139539,385.4MB
apps,40391,350066653,333.8MB
.cache,11084,293145218,279.6MB
참고 Context,1203,187529146,178.8MB
downloads,1,36501504,34.8MB
trading-DESKTOP-2R00TB4-2.db,1,24633344,23.5MB
trading.db,1,24608768,23.5MB
trading-DESKTOP-2R00TB4.db,1,24293376,23.2MB
trading-DESKTOP-TFM86SG-2.db,1,23314432,22.2MB
src,1224,19508673,18.6MB
trading-DESKTOP-TFM86SG.db,1,11382784,10.9MB
graphify-out,5,8479844,8.1MB
scripts,494,7859795,7.5MB
tests,872,4327995,4.1MB
tasks,58,1420222,1.4MB
logs,32,996943,973.6KB
```

## Largest Report Directories

```csv
report_dir,file_count,size_bytes,md_count,csv_count,size_human
task_406_deterministic_decision_rebuild,8,1303544131,1,7,1.2GB
task_401_forward_live_canonical_multifactor_decision_layer,14,1214096900,1,13,1.1GB
task_661_mechanism_relation_engine,13,484825362,1,12,462.4MB
task_659_theme_specific_relation_engine,13,401733960,1,12,383.1MB
task_407_raw_native_vectorized_rebuild,10,355051642,1,6,338.6MB
task_652_relation_overlay_stability,11,329486556,2,9,314.2MB
task_657_soft_macro_relation_backtest,10,327079038,1,9,311.9MB
task_638_content_signal_refinement,15,310173978,3,11,295.8MB
task_487_regime_phase_target_validation,12,107723034,1,11,102.7MB
task_651_relation_state_machine,16,99822599,4,12,95.2MB
task_480_symbol_structure_continuation_diagnostics,15,96575546,1,13,92.1MB
task_654_relation_engine_audit_upgrade,11,63843431,1,10,60.9MB
task_644_firm_grade_conditional_wrapper,12,62378134,3,7,59.5MB
task_633_qqq_benchmark_full_period_refresh,36,57356841,3,33,54.7MB
task_655_macro_asof_release_repair,8,51476066,1,7,49.1MB
task_396_forward_live_cost_constrained_validation,10,36399499,1,9,34.7MB
task_492_microstructure_source_collection,7,32975896,1,6,31.4MB
task_558_pullback_acceptance_true_failure_test,7,29909772,1,6,28.5MB
task_545_factor_adjusted_failure_state_suppression,8,28922419,1,7,27.6MB
task_643_entry_risk_tier_turnover_backtest,12,26298245,2,9,25.1MB
task_617_turboquant_fresh_strategy_backtest,16,25757011,1,15,24.6MB
task_741_economic_denominator_meaning_layer,16,25464504,2,12,24.3MB
task_544_factor_adjusted_sample_expansion_quarter_failure,9,25414897,1,8,24.2MB
task_399_intraday_universe_history_expansion,60,19179885,8,44,18.3MB
task_404_task401_exact_label_generation,6,18414006,1,5,17.6MB
task_738_semantic_enrichment_requirements,18,18198755,2,13,17.4MB
task_740_engineering_high_resolver_completion,17,16308513,2,12,15.6MB
task_632_temporal_strict_full_period_backtest,14,16036568,2,12,15.3MB
task_718_winner_structure_interaction_brain,10,15992960,1,9,15.3MB
task_732_source_circuit_interpreters,13,14983697,2,9,14.3MB
```

## Backtest Code Classification

```csv
kind,file_count,size_bytes,size_human
core_or_shared,45,583836,570.2KB
legacy_analysis_or_builder,161,2867058,2.7MB
task_specific,231,4288996,4.1MB
```

## Immediate Low-Risk Actions

1. Add a report/artifact manifest standard and apply it from the next task onward.
2. Add `tasks/task_registry.csv` before moving files.
3. Extract shared metrics/leakage/cost-stress helpers from recent Task489-493 code.
4. Move only large generated panels first; do not delete historical reports.
5. Keep Task492/493/495 as current canonical microstructure path; mark older reconstruction/recovery tasks as historical.

## Do Not Do Yet

- Do not bulk-delete `docs/reports`.
- Do not rename task IDs without a registry.
- Do not move raw data until collectors and report references are updated.
- Do not refactor old task files before extracting current canonical utilities.