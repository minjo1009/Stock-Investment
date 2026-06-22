# Task696 Tiny Backtest Candidate Set Audit

## Decision Summary

- Verdict: TINY_BACKTEST_CANDIDATE_SET_BUILT_AUDITED_NO_PNL.
- Strategy acceptance status: NOT_ACCEPTED.
- Real capital status: FORBIDDEN.
- Key metrics: candidate set 3, symbols `ASTS|BA|TER`, PnL run flag 0.
- What changed: built an audited tiny backtest candidate set from eligible review candidates only.
- Next action: Run a small PnL test only against this audited candidate set, with costs and benchmark caveats.

## Quant Expert Report

### Data source and source readiness

Input is Task695 tiny eligibility draft. No raw source is added and no PnL simulation is run.

### Exact join keys

- Candidate rows preserve `lifecycle_id`, `symbol`, `entry_ts`, `entry_ts_utc`, `theme_id`, and `split_name`.
- No inferred lifecycle matching is used.

### Leakage audit

- No PnL, win/loss, simulated exit, future price, or holding-period columns are included.
- Conditional candidates are excluded.
- Allocation and paper/live trading approvals remain zero.

### Tiny Candidate Set

| symbol | entry_ts | theme_id | split_name | packet_type | slot_claim_score | remaining_risk | candidate_reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| ASTS | 2025-02-12 14:30:00+00:00 | aerospace_defense_space | train_design | source_supported_leader | 9.5000 | ownership_filing_mix | manual_pass_packet\|type=source_supported_leader\|state=source_packet_review_pass |
| BA | 2025-05-30 14:30:00+00:00 | aerospace_defense_space | train_design | source_supported_leader | 9.5000 | noise_heavy_packet\|ownership_filing_mix | manual_pass_packet\|type=source_supported_leader\|state=source_packet_review_pass |
| TER | 2025-09-10 14:30:00+00:00 | industrial_automation_robotics | validation | source_supported_leader | 9.5000 | ownership_filing_mix | manual_pass_packet\|type=source_supported_leader\|state=source_packet_review_pass |

### Split/OOS metrics

Not applicable. This task is not a return test.

### Failure decomposition

- Candidate set is very small and research-only.
- BA and TER still carry ownership-filing-mix residual risk from packet review.
- This file is only a clean input for a later small PnL test.

### Cost/slippage stress where PnL changed

Not applicable. No PnL changed.

### Remaining blockers

- Run a small PnL test only after this pre-PnL audit.
- Compare against cash and QQQ for the same timestamps if PnL is run.
- Keep real capital forbidden regardless of tiny test outcome until full gates pass.

## No-Background Decision-Maker Report

- What happened: ASTS, BA, and TER were isolated as the only tiny backtest candidates.
- Why it matters: PnL can be tested on a clean, audited set instead of a moving target.
- Whether this changes capital/deployment readiness: no. NOT_ACCEPTED and FORBIDDEN remain.
- Plain-language next step: run a tiny PnL test using only this file.

## Artifact Manifest

- Inputs: Task695 tiny eligibility draft.
- Outputs: tiny candidate set, candidate-set audit, decision, pass/fail, manifest.
- Row counts: candidate set 3, audit 8.
- Validation commands: `python src/backtest/build_task696_tiny_backtest_candidate_set_audit.py`; `python -m unittest tests.test_task696_tiny_backtest_candidate_set_audit`; `python scripts/task_registry_validate.py`.

## Pass/Fail Matrix

| gate_name | status | pass_flag | observed | required |
| --- | --- | --- | --- | --- |
| candidate_set_count | PRIMARY_PASS | 1 | rows=3 | tiny candidate set must contain exactly 3 rows |
| candidate_symbols_match | PRIMARY_PASS | 1 | symbols=ASTS,BA,TER | candidate symbols must be ASTS, BA, TER |
| candidate_set_from_eligible_only | PRIMARY_PASS | 1 | eligible_only={'eligible_review_candidate': 3}; flags=3 | only eligible_review_candidate rows can enter tiny candidate set |
| conditional_candidates_excluded | PRIMARY_PASS | 1 | conditional_count=8 | needs_extra_confirmation rows must stay out of candidate set |
| no_allocation_or_trade_approval | PRIMARY_PASS | 1 | allocation_approved_sum=0; trade_approved_sum=0 | candidate set cannot approve allocation or trading |
| pnl_not_run | PRIMARY_PASS | 1 | pnl_not_run_sum=3 | candidate set is pre-PnL only |
| no_outcome_columns_in_task696_outputs | PRIMARY_PASS | 1 | none | PnL/outcome columns excluded |
| no_strategy_promotion | PRIMARY_PASS | 1 | no PnL simulation or allocation rule promotion was run | candidate-set audit only |
