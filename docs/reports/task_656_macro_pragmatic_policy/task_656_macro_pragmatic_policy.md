# Task656 Macro Pragmatic Policy

## Decision Summary

- Verdict: `PRAGMATIC_RELEASE_TIME_MACRO_POLICY_READY_FOR_SOFT_RELATION_BACKTEST`
- Strategy acceptance status: `NOT_ACCEPTED`
- Deployment status: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`
- Task639 pragmatic macro eligible rate: 1.0000.
- What changed: vintage-perfect ALFRED work is deferred by policy; release-time repaired macro can be used for soft backtest research.
- Next action: test relation engine with macro as soft modifier only.

## Quant Expert Report

Task656 changes the research standard from strict vintage-perfect macro assignment to a pragmatic release-time-valid policy. This is not a deployment approval.

### Data Source And Source Readiness

| scope | row_count | lifecycle_count | release_timestamp_repaired_rate | latest_vintage_gap_rate | strict_assignment_eligible_rate | pragmatic_macro_eligible_rows | pragmatic_macro_eligible_rate | strict_vintage_required_flag | macro_usage_permission |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| execution_all_variants | 189102 | 5265 | 1.0 | 1.0 | 0.0 | 189102 | 1.0 | 0 | soft_modifier_allowed |
| execution_delay1d_existing | 5047 | 5047 | 1.0 | 1.0 | 0.0 | 5047 | 1.0 | 0 | soft_modifier_allowed |
| task639_core_delay1d_existing | 1621 | 1621 | 1.0 | 1.0 | 0.0 | 1621 | 1.0 | 0 | soft_modifier_allowed |

### Exact Join Keys

Task655 context remains keyed by lifecycle, entry timestamp, timing mode, and exit mode. Release-time validity stays mandatory.

### Leakage Audit

The policy explicitly does not claim vintage-perfect as-of values. Therefore macro can only be a soft modifier in backtests.

### Failure Decomposition

| policy_item | required_flag | decision | reason |
| --- | --- | --- | --- |
| release_time_required | 1 | required_for_any_macro_use | Macro must not be used before it could be known intraday. |
| exact_release_calendar_required | 0 | defer_for_now_use_standard_release_time_rules | Official per-observation release calendars are useful but too slow for the current iteration. |
| vintage_asof_required | 0 | defer_for_now_accept_latest_vintage_caveat | Revision-perfect ALFRED work is intentionally deferred by user decision. |
| macro_allowed_usage | 1 | soft_modifier_only | Macro can shape confirmation, delay, and risk context but cannot be a standalone entry or hard blocker. |
| macro_forbidden_usage | 1 | no_standalone_entry_no_full_entry_no_hard_block_no_size_boost | Latest-vintage caveat means macro cannot carry strong trading authority. |

### Remaining Blockers

| relation_use | permission | reason |
| --- | --- | --- |
| standalone_entry | BLOCKED | Macro is context, not entry alpha. |
| full_entry_promotion | BLOCKED | Latest-vintage caveat blocks strong action. |
| hard_block | BLOCKED | Macro can be wrong or revised; company/chart evidence must carry hard block. |
| size_boost | BLOCKED | No leverage or boost from latest-vintage macro. |
| confirmation_required | ALLOWED_FOR_BACKTEST | Soft modifier can require cleaner entry confirmation. |
| delay_entry | ALLOWED_FOR_BACKTEST | Soft modifier can test delayed entry around macro pressure. |
| reduced_size | ALLOWED_FOR_BACKTEST | Soft risk trim is allowed only if it preserves Task639 baseline and OOS gates. |
| research_tagging | ALLOWED | Context tags are allowed for diagnostics. |

## No-Background Decision-Maker Report

We will not chase the perfect old unrevised macro value right now.

We keep the important part: the macro number must already have been released before the trade.

Because revised-value risk remains, macro gets limited power. It can help us be more careful, but it cannot force a buy, hard block a trade, or boost size.

## Pass/Fail Matrix

| gate | pass_flag | observed_value | required_value |
| --- | --- | --- | --- |
| release_time_required | 1 | required=1 | release time must remain required |
| vintage_requirement_deferred | 1 | required=0 | vintage-as-of is intentionally deferred |
| task639_pragmatic_macro_coverage | 1 | rate=1.0000 | >=0.95 |
| strict_assignment_not_claimed | 1 | strict_rate=0.0000 | must not pretend vintage-perfect assignment |
| trading_promotion | 0 | policy enables backtest research only | strategy still needs relation backtest and OOS acceptance |

## Artifact Manifest

- `task_656_macro_pragmatic_policy.csv`
- `task_656_pragmatic_coverage.csv`
- `task_656_relation_permission_matrix.csv`
- `task_656_pass_fail_matrix.csv`
- `task_656_decision.csv`
- `artifact_manifest.csv`
