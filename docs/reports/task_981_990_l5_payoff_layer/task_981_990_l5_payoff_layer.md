# Task981-990 L5 Payoff Layer

## Decision Summary

Task981-990 implemented the L5 payoff/trading-judgment layer as a feature-only diagnostic layer.

Result:

- Verdict: `l5_payoff_layer_feature_only_complete_no_replay`
- Input rows: 3,689 Task969 shadow ranking rows
- L5 feature rows: 3,689 per panel
- Source context rows: 7
- Gap diagnostic rows: 274
- Replay executed: `0`
- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

This task does not claim strategy acceptance, model improvement, or deployment readiness. It creates the missing L5 bridge between thesis intelligence and trading judgment before any new replay policy is allowed.

## Quant Expert Report

### Objective

The prior Task971-980 replay showed that the project can form information-rich candidate theses, but it still lacks a trader-like payoff layer. Task981-990 therefore implements L5 as a controlled diagnostic layer with six components:

- `L5-A`: reflectedness and variant perception
- `L5-B`: payoff shape and convexity
- `L5-C`: motion and timing
- `L5-D`: best expression and substitution
- `L5-E`: portfolio construction and risk budget
- `L5-V`: validation and false-discovery guard

The layer is intentionally not wired into selection or replay. Its output must first be reviewed, then one policy must be pre-registered before any backtest.

### Source Context

Source context was gathered from institutional and academic materials:

- CFA Institute, Active Equity Investing: Portfolio Construction: https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/active-equity-investing-portfolio-construction
- CFA Institute, Unlocking Stock Market Success: Why You Should Embrace the Skew: https://rpc.cfainstitute.org/blogs/enterprising-investor/2024/unlocking-stock-market-success-why-you-should-embrace-the-skew
- Morgan Stanley Investment Management, Probabilities and Payoffs: https://www.morganstanley.com/im/publication/insights/articles/article_probabilitiesandpayoffs.pdf
- Asness, Moskowitz, and Pedersen, Value and Momentum Everywhere: https://pages.stern.nyu.edu/~lpederse/papers/ValMomEverywhere.pdf
- Harvey, Liu, and Zhu, ... and the Cross-Section of Expected Returns: https://www.nber.org/system/files/working_papers/w20592/w20592.pdf
- Bali, Cakici, and Whitelaw, Maxing out: Stocks as Lotteries and the Cross-Section of Expected Returns: https://pages.stern.nyu.edu/~rwhitela/papers/max%20jfe11.pdf

Local raw source capture:

- 5 sources downloaded into `data/raw/research/l5_payoff_layer/`
- Morgan Stanley PDF was web-verified but local PowerShell download returned HTTP 403 and is recorded as failed in `download_manifest.csv`

### Implementation

The implementation is in `scripts/trader_brain_981_990_l5_payoff_layer.py`.

Inputs:

- Task969 shadow ranking
- Task929 controlled trade specs
- Task880 canonical daily market data
- Task941 and Task975 replay trades only for post-replay gap decomposition
- L5 raw source download manifest

Leakage controls:

- Price features use only rows with `timestamp < entry_date`
- Feature panels do not include PnL, realized return, future return, outcome rank, or exit price
- `selection_use_allowed` is `0`
- `replay_executed` is `0`
- Gap PnL is stored only in `task989_baseline_shadow_gap_evaluation_only.csv`

### Panel Distributions

`L5-A` reflectedness:

- highly_reflected_momentum_proxy: 270
- insufficient_history: 228
- neutral_reflectedness_proxy: 1,707
- positive_relative_motion_proxy: 707
- under_pressure_reset_proxy: 777

`L5-B` payoff shape:

- insufficient_history: 54
- left_tail_or_broken_trend_proxy: 452
- linear_or_unclear_payoff_proxy: 2,578
- right_tail_contained_drawdown_proxy: 246
- right_tail_high_risk_proxy: 359

`L5-C` timing:

- insufficient_history: 228
- neutral_timing_proxy: 2,745
- positive_motion_timing_proxy: 515
- possibly_extended_timing_proxy: 85
- pullback_after_positive_trend_proxy: 116

`L5-D` best expression:

- theme_alternative_proxy: 3,059
- theme_leader_proxy: 630

`L5-E` risk budget:

- crowded_theme_review: 126
- normal_review: 3,563

`L5-V` validation:

- pass: 3,689

## No-Background Decision-Maker Report

The project did not need another immediate backtest. It needed the missing trader judgment layer that decides whether a thesis is tradable, timely, convex enough, expressed through the right symbol, and safe to test.

Task981-990 now provides that layer.

It is not yet a trading policy. It is a clean diagnostic bridge. The next step is to inspect the L5 panels, freeze one explicit policy, and only then run a controlled replay.

## Artifact Manifest

Primary artifacts:

- `data/artifacts/task_981_990_l5_payoff_layer/task981_l5_source_context_manifest.csv`
- `data/artifacts/task_981_990_l5_payoff_layer/task982_l5_layer_contract.csv`
- `data/artifacts/task_981_990_l5_payoff_layer/task983_l5a_reflectedness_panel.csv`
- `data/artifacts/task_981_990_l5_payoff_layer/task984_l5b_payoff_shape_panel.csv`
- `data/artifacts/task_981_990_l5_payoff_layer/task985_l5c_motion_timing_panel.csv`
- `data/artifacts/task_981_990_l5_payoff_layer/task986_l5d_best_expression_panel.csv`
- `data/artifacts/task_981_990_l5_payoff_layer/task987_l5e_portfolio_risk_budget_panel.csv`
- `data/artifacts/task_981_990_l5_payoff_layer/task988_l5v_validation_guard_panel.csv`
- `data/artifacts/task_981_990_l5_payoff_layer/task989_baseline_shadow_gap_evaluation_only.csv`
- `data/artifacts/task_981_990_l5_payoff_layer/task990_l5_payoff_layer_closeout.csv`
- `data/artifacts/task_981_990_l5_payoff_layer/task981_990_summary.csv`
- `data/artifacts/task_981_990_l5_payoff_layer/task981_990_summary.json`
- `data/artifacts/task_981_990_l5_payoff_layer/artifact_manifest.csv`

Validation commands:

```text
python scripts/trader_brain_981_990_l5_payoff_layer.py
python scripts/task_artifact_manifest.py --task-dir data/artifacts/task_981_990_l5_payoff_layer
python scripts/trader_brain_981_990_l5_payoff_layer_validate.py
python -m unittest tests.test_trader_brain_981_990_l5_payoff_layer
```

Validation authority:

- `REVIEW_ONLY_L5_PAYOFF_LAYER_NO_REPLAY`

Next action:

- Review L5 gap panels and pre-register one L5-informed replay policy before any new backtest.
