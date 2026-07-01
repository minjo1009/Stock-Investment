# Project Efficiency Audit

## Executive Summary

- Total tracked workspace files scanned: 5,732
- Total scanned size: 5.7GB
- docs/reports directories: 185
- src/backtest Python files: 228

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
docs,1436,3329361922,3.1GB
data,731,2597708628,2.4GB
참고 Context,1204,187535294,178.8MB
graphify-out,286,17396188,16.6MB
src,764,9977950,9.5MB
trading.db,1,9547776,9.1MB
tests,323,2017914,1.9MB
.git,862,1414057,1.3MB
scripts,26,114230,111.6KB
tasks,58,91849,89.7KB
context,9,40402,39.5KB
skills,3,12724,12.4KB
phases,3,11212,10.9KB
prompts,2,6374,6.2KB
README.md,1,6247,6.1KB
.github,6,5475,5.3KB
AGENTS.md,1,1940,1.9KB
templates,2,1418,1.4KB
logs,9,827,827.0B
.kis_token_cache.json,1,489,489.0B
```

## Largest Report Directories

```csv
report_dir,file_count,size_bytes,md_count,csv_count,size_human
task_406_deterministic_decision_rebuild,8,1303544131,1,7,1.2GB
task_401_forward_live_canonical_multifactor_decision_layer,14,1214096900,1,13,1.1GB
task_407_raw_native_vectorized_rebuild,10,355051642,1,6,338.6MB
task_487_regime_phase_target_validation,12,107723034,1,11,102.7MB
task_480_symbol_structure_continuation_diagnostics,15,96575546,1,13,92.1MB
task_396_forward_live_cost_constrained_validation,10,36399499,1,9,34.7MB
task_492_microstructure_source_collection,7,32975896,1,6,31.4MB
task_399_intraday_universe_history_expansion,60,19179885,8,44,18.3MB
task_404_task401_exact_label_generation,6,18414006,1,5,17.6MB
task_333_behavior_clustered_state_model,12,9241879,1,11,8.8MB
task_482_continuous_market_theme_regime_engine,23,8336791,1,21,8.0MB
task_400_forward_live_entry_quality_filter_discovery,9,7916011,1,8,7.5MB
task_488_regime_only_target_recovery,8,7525400,1,7,7.2MB
task_395_forward_live_regime_detectability,9,7505755,1,7,7.2MB
task_327_path_conditioned_entry,14,6112821,1,13,5.8MB
task_392_macro_vol_theme_regime_overlay,13,5838447,1,12,5.6MB
task_393_regime_gated_canonical_continuation_validation,8,5487296,1,7,5.2MB
task_388_theme_10x7_intraday_canonical_continuation_long_history,6,5178850,1,5,4.9MB
task_483_firm_grade_market_theme_regime_upgrade,25,4963446,2,22,4.7MB
task_484_continuation_payoff_regime_engine,13,4832168,1,10,4.6MB
task_493_microstructure_enhanced_continuation_grid,12,4757298,1,11,4.5MB
task_324_exit_size_rule_integration,10,4380652,1,9,4.2MB
task_491_intraday_continuation_grid_development,10,4166877,1,9,4.0MB
task_322_structural_breakout,7,3459579,2,5,3.3MB
task_490r_firm_grade_intraday_continuation_validation,10,3227179,1,9,3.1MB
task_391_intraday_canonical_oos_validation,8,2992229,1,7,2.9MB
task_385_canonical_continuation_engine,27,2277459,4,23,2.2MB
task_398_portfolio_path_equity_curve_simulation,7,2233929,1,6,2.1MB
task_325_regime_entry_rebuild,14,2211580,1,13,2.1MB
task_397_forward_live_strict_false_positive_decomposition,8,2181833,1,7,2.1MB
```

## Backtest Code Classification

```csv
kind,file_count,size_bytes,size_human
core_or_shared,29,319952,312.5KB
legacy_analysis_or_builder,161,2867058,2.7MB
task_specific,38,426854,416.8KB
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