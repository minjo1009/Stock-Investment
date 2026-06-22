# Task620B Proactive Prescription Logic

## Decision Summary

- Verdict: `LOCK_PROACTIVE_AEROSPACE_RISK_OFF_CANDIDATE_NOT_ACCEPTED`
- Strategy acceptance status: `NOT_ACCEPTED`
- Real capital: `FORBIDDEN`
- Primary proactive rule: `AEROSPACE_SPACE_RISK_OFF_GATE`
- Primary pre-entry action: `BLOCK_UNTIL_SOURCE_RETYPED`
- This is a proactive rule candidate, not an accepted trading rule.

## Quant Expert Report

### Proactive Rulebook

| Rule | Action | Condition Columns | Validation Use |
|---|---|---|---|
| `AEROSPACE_SPACE_RISK_OFF_GATE` | `BLOCK_UNTIL_SOURCE_RETYPED` | `theme_id|political_statement_pre7d_flag|geopolitical_event_pre7d_flag|institution_ownership_pre30d_flag` | `diagnostic_candidate_only` |
| `AEROSPACE_HOT_LEADER_ZERO_EXPOSURE` | `ENTRY_BLOCK` | `theme_id|theme_regime_state_v4|theme_ret20_prev` | `diagnostic_candidate_only` |
| `HOT_THEME_MIDDAY_CONFIRMATION_REQUIRED` | `DELAY_ENTRY_OR_REQUIRE_CONFIRMATION` | `timing_state|theme_ret20_prev` | `needs_delayed_entry_replay` |
| `BROAD_EVENT_NO_IR_GLOBAL_FILTER` | `DO_NOT_USE_GLOBAL_FILTER` | `political_statement_pre7d_flag|geopolitical_event_pre7d_flag|institution_ownership_pre30d_flag|ceo_ir_proxy_pre14d_flag` | `rejected_as_global_filter` |
| `OVEREXTENDED_THEME_LEADER_SIZE_DOWN` | `SIZE_DOWN` | `theme_regime_state_v4|theme_ret20_prev` | `size_down_candidate_only` |

### Rule Evaluation

| Rule | Split | Trigger N | Trigger Avg | Kept Avg | Kept Entry-Reduce | Clean Winners Rejected |
|---|---|---:|---:|---:|---:|---:|
| `AEROSPACE_SPACE_RISK_OFF_GATE` | `train_design` | 64 | 20.73% | 20.48% | 23.33% | 56 |
| `AEROSPACE_SPACE_RISK_OFF_GATE` | `validation` | 60 | 0.12% | 12.46% | 29.21% | 27 |
| `AEROSPACE_SPACE_RISK_OFF_GATE` | `recent_oos` | 29 | -18.49% | 9.65% | 46.25% | 0 |
| `AEROSPACE_HOT_LEADER_ZERO_EXPOSURE` | `train_design` | 23 | 15.59% | 20.86% | 21.70% | 19 |
| `AEROSPACE_HOT_LEADER_ZERO_EXPOSURE` | `validation` | 47 | -1.21% | 12.00% | 29.30% | 18 |
| `AEROSPACE_HOT_LEADER_ZERO_EXPOSURE` | `recent_oos` | 25 | -18.95% | 8.45% | 48.81% | 0 |
| `HOT_THEME_MIDDAY_CONFIRMATION_REQUIRED` | `train_design` | 65 | 12.48% | 22.28% | 19.06% | 44 |
| `HOT_THEME_MIDDAY_CONFIRMATION_REQUIRED` | `validation` | 21 | 2.90% | 10.22% | 32.78% | 10 |
| `HOT_THEME_MIDDAY_CONFIRMATION_REQUIRED` | `recent_oos` | 15 | -20.50% | 5.78% | 54.26% | 0 |
| `BROAD_EVENT_NO_IR_GLOBAL_FILTER` | `train_design` | 122 | 13.08% | 24.28% | 27.27% | 108 |
| `BROAD_EVENT_NO_IR_GLOBAL_FILTER` | `validation` | 144 | 11.68% | 7.13% | 34.75% | 91 |
| `BROAD_EVENT_NO_IR_GLOBAL_FILTER` | `recent_oos` | 71 | 2.72% | 1.13% | 52.63% | 23 |
| `OVEREXTENDED_THEME_LEADER_SIZE_DOWN` | `train_design` | 78 | 7.77% | 24.01% | 16.43% | 45 |
| `OVEREXTENDED_THEME_LEADER_SIZE_DOWN` | `validation` | 35 | -2.55% | 11.51% | 30.40% | 13 |
| `OVEREXTENDED_THEME_LEADER_SIZE_DOWN` | `recent_oos` | 24 | -17.14% | 7.62% | 50.59% | 1 |

### Policy Variants

| Policy | Split | Rejected | Kept | Kept Avg | Kept Entry-Reduce |
|---|---|---:|---:|---:|---:|
| `PROACTIVE_V1_AEROSPACE_RISK_OFF` | `train_design` | 64 | 300 | 20.48% | 23.33% |
| `PROACTIVE_V1_AEROSPACE_RISK_OFF` | `validation` | 60 | 202 | 12.46% | 29.21% |
| `PROACTIVE_V1_AEROSPACE_RISK_OFF` | `recent_oos` | 29 | 80 | 9.65% | 46.25% |
| `PROACTIVE_V2_AEROSPACE_HOT_ONLY` | `train_design` | 23 | 341 | 20.86% | 21.70% |
| `PROACTIVE_V2_AEROSPACE_HOT_ONLY` | `validation` | 47 | 215 | 12.00% | 29.30% |
| `PROACTIVE_V2_AEROSPACE_HOT_ONLY` | `recent_oos` | 25 | 84 | 8.45% | 48.81% |
| `PROACTIVE_V3_AERO_RISK_OFF_PLUS_HOT_MIDDAY_CONFIRM` | `train_design` | 115 | 249 | 23.05% | 20.08% |
| `PROACTIVE_V3_AERO_RISK_OFF_PLUS_HOT_MIDDAY_CONFIRM` | `validation` | 62 | 200 | 12.43% | 29.50% |
| `PROACTIVE_V3_AERO_RISK_OFF_PLUS_HOT_MIDDAY_CONFIRM` | `recent_oos` | 30 | 79 | 9.98% | 45.57% |
| `REJECTED_GLOBAL_COMPANY_IR_REQUIREMENT` | `train_design` | 122 | 242 | 24.28% | 27.27% |
| `REJECTED_GLOBAL_COMPANY_IR_REQUIREMENT` | `validation` | 144 | 118 | 7.13% | 34.75% |
| `REJECTED_GLOBAL_COMPANY_IR_REQUIREMENT` | `recent_oos` | 71 | 38 | 1.13% | 52.63% |

## No-Background Decision-Maker Report

- The new logic is not 'it lost a lot, so delete it.'
- The new logic is a pre-entry risk-off rule: aerospace/space plus broad, non-discriminating event support is blocked until the source layer can prove a company-specific catalyst.
- A global 'must have recent IR' rule is rejected because it damages validation and recent OOS.
- Trailing-stop failures remain exit research, not entry logic.

## Pass/Fail Matrix

| Gate | Pass | Observed | Required |
|---|---:|---|---|
| `pre_entry_only_rule_columns` | 1 | none | no outcome, exit, or holding-period columns in rule conditions |
| `aerospace_risk_off_diagnostic_candidate` | 1 | recent_kept_avg=9.65%; recent_kept_er=46.25%; validation_kept_avg=12.46% | recent kept avg>=5%, recent kept entry_reduce<=50%, validation kept avg>=base |
| `global_ir_requirement_rejected` | 1 | recent_kept_avg=1.13%; validation_kept_avg=7.13% | global company-IR requirement should not be promoted if it damages both splits |
| `treatment_rule_acceptance` | 0 | diagnostic proactive rule candidates only | must pass split/OOS, cost/slippage, parameter, and source-retyping audits |

## Artifact Manifest

### Inputs

- `docs/reports/task_617_turboquant_fresh_strategy_backtest/fresh_turboquant_strategy_backtest_panel.csv`

### Outputs

- `task_620b_proactive_rulebook.csv`
- `task_620b_proactive_rule_evaluation.csv`
- `task_620b_policy_variant_evaluation.csv`
- `task_620b_pass_fail_matrix.csv`
- `task_620b_decision.csv`
- `artifact_manifest.csv`

### Validation Commands

- `python -m unittest tests.test_task620b_proactive_prescription_logic`
- `python scripts/task_registry_validate.py`
- `python scripts/operating_closeout_validate.py`