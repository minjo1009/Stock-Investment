# Task653 Relation Engine Firm-Grade Upgrade Plan

## Decision Summary

- Verdict: `RELATION_ENGINE_UPGRADE_PLAN_READY_IMPLEMENTATION_BLOCKED_TO_TASK654`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Key metrics:
  - Task639 baseline: $1000 to $7639.62, max drawdown -23.76 percent.
  - Task651 relation action: $1000 to $7341.22, max drawdown -24.90 percent.
  - Execution lifecycles: 5265.
  - Macro lifecycles: 735.
  - Direct overlap: 495.
  - Execution lifecycles missing macro: 4770.
  - Task639 core macro source gap: 1363 of 1621 trades.
- What changed: no trading rule changed. This task locks the diagnosis and next implementation contract.
- Next action: implement Task654 with coverage scope, join contract, baseline preservation, taxonomy permission, action transition, and promotion eligibility audits.

## Quant Expert Report

### Data Source And Source Readiness

The current relation engine is not ready for trading authority because source coverage is sparse and uneven.

Task638 execution covers 5265 lifecycles from 2024-01-02 to 2026-06-04. Task649 macro context covers 735 lifecycles from 2024-02-07 to 2026-05-08. Only 495 lifecycles overlap directly. This means most execution candidates do not have valid macro context attached.

Task651 then evaluates relation state on a 189102-row execution panel. In that panel, macro source gap appears in 171282 rows and latest-vintage macro gap appears in all 189102 rows. Task639 core is better on company content because company source gap is zero, but still has macro source gap in 1363 of 1621 trades.

Decision: do not add new source types yet. First repair the scope contract and prove which rows are assignable.

### Exact Join Keys

Task654 must write row-level join fields before any relation state can affect action:

- `macro_join_key`
- `company_join_key`
- `macro_join_status`
- `company_join_status`
- `asof_valid_flag`
- `latest_vintage_gap_flag`
- `used_for_assignment_flag`
- `used_for_diagnostic_only_flag`

Required rule: source gaps and latest-vintage gaps cannot upgrade, downgrade, block, delay, or size a trade.

### Leakage Audit

Task653 did not create a new trading rule. GPT was used only as review guidance and not as a source of truth. Labels and future returns remain evaluation-only.

Task654 must preserve this rule:

- no labels in assignment logic
- no future returns in assignment logic
- no source gaps as signals
- no promotion from latest-vintage macro fields

### Split/OOS Metrics

Current evidence says relation logic is weaker than Task639:

- Task639: $7639.62 final capital, -23.76 percent max drawdown.
- Task651: $7341.22 final capital, -24.90 percent max drawdown.
- Task652: no relation overlay beats Task639.

This means the relation engine must stay diagnostic until Task654 proves it preserves or improves Task639 across full period, validation, recent OOS, costs, and source audit.

### Failure Decomposition

The failures are not one problem. They are three separate problems.

1. Data problem: macro context is available for only part of the execution universe.
2. Code problem: current outputs do not show enough row-level join authority and baseline damage path.
3. Logic problem: taxonomy names sound strong but do not match empirical strength.

Examples:

- `reinforcing` has lower average return and win rate than `sizing_modifier`.
- `strong_company_positive` is weaker than `moderate_company_positive`.
- `macro_known_mixed_supportive` and simple chart overlays do not beat Task639.

### Cost/Slippage Stress

No new PnL rule was promoted in Task653. Cost and slippage stress are therefore not applicable for this planning task. Task654 must use the same $1000 account comparison and cost settings used by Task639/Task651/Task652.

### Remaining Blockers

- Coverage scope not separated into valid and gap universes.
- Row-level join contract missing.
- Baseline preservation audit missing.
- Taxonomy names and action permissions coupled too tightly.
- Latest-vintage macro gap blocks promotion.
- Single simulator comparison contract needs to be enforced.

## No-Background Decision-Maker Report

The relation engine is not bad because the idea is bad. It is weak because it is judging too many trades without enough attached context.

Simple version:

- We have many trades.
- We have macro context for only some of them.
- The code currently mixes those worlds too easily.
- The logic gives strong-sounding names too much power.

So the next move is not to add more data categories yet. The next move is to prove, row by row, where the engine actually has enough information to judge. Until that is fixed, Task639 remains the baseline and relation state remains research only.

This does not change capital readiness. Strategy remains `NOT_ACCEPTED`, and real capital remains `FORBIDDEN`.

## Artifact Manifest

Inputs:

- `docs/reports/task_651_relation_state_machine/task_651_source_audit.csv`
- `docs/reports/task_651_relation_state_machine/task_651_relation_performance.csv`
- `docs/reports/task_651_relation_state_machine/task_651_action_performance.csv`
- `docs/reports/task_651_relation_state_machine/task_651_account_comparison.csv`
- `docs/reports/task_652_relation_overlay_stability/task_652_relation_overlay_stability.md`

Outputs:

- `task_653_data_audit.csv`
- `task_653_code_audit.csv`
- `task_653_logic_audit.csv`
- `task_653_task654_spec.csv`
- `task_653_gpt_review_packet.md`
- `task_653_gpt_review_response.md`
- `task_653_decision.csv`
- `task_653_relation_engine_firm_grade_upgrade_plan.md`
- `artifact_manifest.csv`

Validation commands:

- `python scripts/task_artifact_manifest.py --task-dir docs/reports/task_653_relation_engine_firm_grade_upgrade_plan`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`
- `python scripts/governance_completion_audit.py`
