# Task T099-REVIEW - Breakout Decision

## 1. Summary
- task: T099-REVIEW
- status: PASS
- scope: DOCS_ONLY_NO_RERUN
- source_results_file: docs/reports/task_099/task_099_breakout_sensitivity_results.json
- source_results_status: WARNING

## 2. Acceptance Snapshot
- accepted_runs: [A_10, E_OFF, E_LIGHT]
- rejected_runs: [A_15, A_30, B_0.25_pct, B_0.50_pct, C_HIGH_TOUCH, D_OFF, D_LIGHT]
- hard_fail_runs: [B_0.50_pct]

## 3. Baseline Snapshot
- run_id: BASELINE
- generated_signals: 39
- executed_signals: 37
- pp20: 0.615385
- rp20: 0.082474
- sharpe: 0.884498
- mdd_pct: 3.831247
- return_pct: 31.990129

## 4. Accepted Candidate Comparison
| run_id | family | level | generated | executed | pp20 | rp20 | sharpe | mdd_pct | return_pct |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| A_10 | A | 10 | 45 | 43 | 0.666667 | 0.103093 | 1.198470 | 3.537458 | 51.545713 |
| E_OFF | E | OFF | 39 | 37 | 0.615385 | 0.082474 | 0.884498 | 3.831247 | 31.990129 |
| E_LIGHT | E | LIGHT | 39 | 37 | 0.615385 | 0.082474 | 0.884498 | 3.831247 | 31.990129 |

## 5. Final Recommendation
- best: A_10
  - rationale: highest improvement across density, quality proxy, return, Sharpe, and drawdown versus baseline among accepted runs.
- backups:
  - E_OFF (baseline-equivalent accepted fallback)
  - E_LIGHT (baseline-equivalent accepted fallback)
- next_action: proceed with single-factor winner review first; allow phase-2 combined tests only after that review.

## 6. Final Answer
Recommend `A_10` as the primary breakout candidate. Keep `E_OFF` and `E_LIGHT` as backup options.
