# Task607 GPT Review Notes

## Review Status

`review_notes`

This note records a Chrome/ChatGPT review of the Task505/508/509/512 strategy evidence. GPT was used only as an external reviewer. It is not source-of-truth and did not change strategy acceptance.

## Prompt Scope

Provided bounded summary only:

- Current status: `NOT_ACCEPTED`, `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`, real capital `FORBIDDEN`.
- Task599 acceptance entry conditions.
- Task505 diagnostic metrics: 722.99% two-year simulated PnL, 103 trades, 29.800% avg net, 62.1% win, 35.9% entry_reduce, -18.99% max drawdown.
- Task508 cost stress: 663.02% after 100bp round-trip stress, still model-derived.
- Task509 walk-forward OOS: 7 folds, 89 test trades, 9.325% avg net, 56.2% win, 39.3% entry_reduce.
- Task512 audit: 0.687 avg degradation ratio, 3 negative/weak quarters, concentration flag, `HIGH` overfit risk.

## GPT Findings Accepted As Review Notes

| Severity | Finding | Repo-Native Interpretation |
|---|---|---|
| CRITICAL | Broker-truth SELL lifecycle is not verified. | T600-4 remains the first blocker: `broker_truth_sell_fills=0`, runtime exits are not broker truth. |
| CRITICAL | Exact replay acceptance is incomplete. | T602-4 order/fill/decision recovered, but position match is 0.958333 and full 99% gate remains blocked. |
| CRITICAL | Exact-ID review packet coverage is incomplete. | Strategy cannot be interpreted as firm-grade without fill and top-skipped-candidate packet coverage. |
| HIGH | Task512 overfit risk remains high. | Task505 is an interesting diagnostic hypothesis, not deployable edge. |
| HIGH | Quarter collapses require regime attribution. | 2025Q1, 2026Q1, and 2026Q2 failures need root-cause decomposition before more strategy work. |
| HIGH | Concentration risk may dominate returns. | Theme/symbol contribution must prove the result is not a narrow-name artifact. |
| MEDIUM | OOS sample is small for a large return claim. | Expanded walk-forward and confidence intervals are required after P0 blockers. |
| MEDIUM | Cost stress is model-derived. | Broker-truth slippage/partial-fill/queue evidence is still missing. |
| MEDIUM | Source-health durability is not proven. | 20-session source-health ledger remains required. |
| MEDIUM | Kill-switch behavior must be certified. | Real-money candidacy requires failure-mode risk control evidence. |

## GPT Findings Rejected Or Rewritten

- GPT proposed generic validation commands under `python tools/...`; these do not exist in this repo and were rejected.
- GPT owner names such as "Data Platform" and "Risk Engineering" were mapped back to repo teams: Data & Market Microstructure, Execution & Risk, Backtest & Simulation Infra, Research Governance, Chart Evidence, and Regime Research.
- GPT's recommendations are not accepted as strategy claims; they are converted only into backlog items in `firm_grade_upgrade_backlog.csv`.

## Forbidden Output Detected

No explicit forbidden strategy approval was detected. The GPT response preserved review-only status and did not claim deployability.

## Next Action

Use the backlog in `firm_grade_upgrade_backlog.csv`. Do not re-run strategy optimization or new alpha experiments until P0 blocker discipline is satisfied.

