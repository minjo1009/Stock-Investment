# Task608 Strategy Backtest Firm-Grade Review

## Decision Summary

- Verdict: RESEARCH_CANDIDATE_NOT_FIRM_GRADE
- Strategy acceptance status: NOT_ACCEPTED
- Two-year PnL: 722.99%
- Walk-forward avg net: 9.32%
- OOS degradation: 0.687
- Concentration risk flag: 1
- What changed: Task505/508/509/512 were rerun and GPT review notes were converted into repo-native diagnostics/backlog.
- Next action: Run Task608A Theme Dependency Audit and Task608B Symbol Dependency Audit before any new alpha experiment.

## Quant Expert Report

- Data source and source readiness: uses existing Task503/505/508/509/512 artifacts; GPT is review-only and not a data source.
- Exact join keys: inherited from Task503/505 lifecycle rows; inferred lifecycle matching remains 0.
- Leakage audit: label/outcome fields are not allowed in assignment. New backlog items are diagnostics or robustness controls, not new alpha labels.
- Split/OOS metrics: walk-forward folds=7, trades=89, avg=9.32%, win=56.18%, entry_reduce=39.33%.
- Failure decomposition: worst walk-forward fold=2025Q1 at -21.26% capital PnL; weak/collapse quarters=3.
- Cost/slippage stress: 100bp=663.02%, 200bp=606.82%; cost is not the main current blocker.
- Remaining blockers: concentration, OOS degradation, entry-reduce failure, weak-fold map, and parameter-neighborhood stability.

### GPT Review Notes

- P0 research_candidate_not_deployment_candidate: GPT review classified the strategy as a research candidate with possible signal, but the selected rulebook is materially over-optimized for the current sample.
- P0 theme_dependency_must_be_tested: Run leave-one-theme-out because only four themes are active and top_theme_share is high.
- P0 symbol_dependency_must_be_tested: Run leave-top-symbols-out to prove this is not a small set of lucky names.
- P0 parameter_neighborhood_stability_required: A single best grid cell is not enough. Neighboring cells must mostly remain positive OOS.
- P1 entry_reduce_failure_is_too_high: Entry-reduce failure around the selected and walk-forward samples is high enough to require attribution before any refinement claim.
- P1 regime_failure_map_required: Failing folds should be mapped as failure environments, not used to invent new hindsight rules.

### Repo-Native Backlog

- P0 Task608A: Theme Dependency Audit - pass: all leave-one-theme-out OOS runs positive and worst degradation < 40%
- P0 Task608B: Symbol Dependency Audit - pass: OOS avg return remains > 50% of baseline and max drawdown does not worsen materially
- P0 Task608C: Parameter Neighborhood Stability - pass: >= 70% neighboring cells positive OOS and degradation < 50%
- P1 Task608D: Regime Failure Map - pass: failure regimes are identifiable without new labels or hindsight assignment
- P1 Task608E: Entry Reduce Attribution - pass: alpha primarily comes from clean entries and entry_reduce_failure falls below 30%
- P1 Task608F: Ensemble Rulebook Validation - pass: OOS degradation < 50%, weak/collapse quarters <= 1, concentration_risk_flag = 0

## No-Background Decision-Maker Report

- What happened: the backtest still looks interesting, but the professional review says it is not sturdy enough yet.
- Why it matters: big headline PnL is less important than whether it survives OOS, theme removal, symbol removal, and nearby parameter tests.
- Whether this changes capital/deployment readiness: no. Strategy remains NOT_ACCEPTED and deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
- Plain-language next step: prove the edge is not coming from one theme, a few symbols, or one lucky parameter cell.

## Artifact Manifest

- See `artifact_manifest.csv`.
