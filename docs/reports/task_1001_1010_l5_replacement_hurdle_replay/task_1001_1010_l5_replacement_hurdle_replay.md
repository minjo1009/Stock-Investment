# Task1001-1010 L5-R Replacement Hurdle Replay

## Decision Summary

Task1001-1010 implemented and replayed `L5-R Replacement Hurdle`.

The design fixed the core Task991-1000 error: L5 no longer replaces the whole book. Task941 slot10 is preserved as the default book, and L5 can replace only a small number of same-entry-date incumbent trades when a strict hurdle is met.

Result:

- Policy: `slot10_l5_replacement_hurdle_v1`
- Initial capital: 1,000
- Final equity: 2,662.53
- CAGR: 20.571348%
- Max drawdown: -32.449510%
- QQQ beat: yes
- Task941 slot10 beat: no
- 30% CAGR target: no
- -30% MDD target: no
- Replacement count: 36
- Replacement budget cap: 45
- Task941 overlap: 414 / 450

Decision:

The L5-R structure is better than Task991-1000, but the policy is not accepted. It still fails to beat Task941 slot10 and misses both the 30% CAGR target and the -30% MDD target.

Standing status remains:

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

## Quant Expert Report

### Source-Backed Design

The L5-R design is based on portfolio construction and implementation-cost sources:

- CFA Institute states that portfolio construction must balance predicted return against risk and implementation impediments, including risk budgeting, concentration, turnover, liquidity, slippage, drawdown, VaR/CVaR, and position-level risk contribution.
- CFA Research and Policy Center's implementation-shortfall article supports turnover-constrained rebalancing and prioritizing only the trades with the highest expected impact.
- AQR's momentum implementation paper shows that turnover and trading costs can be manageable, but only when implementation is handled deliberately rather than by naïve full turnover.
- Perold-style implementation shortfall literature frames the gap between an ideal paper portfolio and actual implemented portfolio after explicit, impact, and opportunity costs.
- Transfer-coefficient literature supports the idea that a signal must survive portfolio constraints before it becomes portfolio value.

Local source capture:

- `data/raw/research/l5_replacement_hurdle/download_manifest.csv`
- 5 / 5 sources downloaded.

Sources:

- CFA Active Equity Portfolio Construction: https://www.cfainstitute.org/insights/professional-learning/refresher-readings/2026/active-equity-investing-portfolio-construction
- CFA Implementation Shortfalls Hamstring Factor Strategies: https://rpc.cfainstitute.org/blogs/enterprising-investor/2024/implementation-shortfalls-hamstring-factor-strategies
- AQR / Portfolio Construction Forum, Implementing Momentum: https://obj.portfolioconstructionforum.edu.au/articles_perspectives/Portfolio-Construction-Forum_AR_Implementing-momentum-what-have-we-learned.pdf
- Transfer Coefficient paper copy: https://people.duke.edu/~charvey/Teaching/BA491_2005/Transfer_coefficient.pdf
- Portfolio management under transaction costs: https://www.diva-portal.org/smash/get/diva2%3A144069/FULLTEXT01.pdf

### GPT/Subagent Audit

Two read-only audits were used.

Trader/portfolio audit:

- Keep Task941 slot10 as the book of record.
- Do not use Task991 L5 ranking as the new baseline.
- Replacement must be one-to-one and same entry-date.
- Replacement budget must be <= 10% of trades.
- Avoid outcome-derived tuning.

Backend/quant audit:

- Join only by `trade_spec_id`.
- Preserve `adapter_input_id`, `candidate_bundle_id`, `source_graph_id`, `decision_asof_ts`.
- No forbidden outcome columns in selection.
- `selected_baseline_kept + selected_replacement == 450`.
- `replacement_count <= 45`.
- `max_replacements_per_entry_date <= 1`.
- Evaluation-only bucket/tail PnL cannot feed selection.

### Policy Definition

Policy:

`slot10_l5_replacement_hurdle_v1`

Rules:

1. Start from Task941 slot10 actual trades.
2. Same entry-date cohort only.
3. Keep all baseline trades by default.
4. Challenger must pass:
   - `feature_time_state == pass`
   - not `hard_block`
   - not `crowded_theme_review`
   - not `left_tail_or_broken_trend_proxy`
   - not `possibly_extended_timing_proxy`
   - L5 score at least 18 points above the weakest incumbent for that entry date
5. Replace at most one incumbent per entry date.
6. Total replacement budget must stay <= 10% of the 450-trade baseline.

### Results

Task941 slot10 baseline:

- Final equity: 2,939.23
- CAGR: 22.870268%
- MDD: -29.484953%
- Closed trades: 450

Task991 full L5 ranking:

- Final equity: 2,412.62
- CAGR: 18.322401%
- MDD: -45.494300%
- Closed trades: 450
- Overlap: 113

Task1001-1010 L5-R:

- Final equity: 2,662.53
- CAGR: 20.571348%
- MDD: -32.449510%
- Closed trades: 450
- Overlap: 414
- Replacements: 36

Split result:

- development_2021_2024: 340 trades, PnL 871.500104
- oos_1_2025: 90 trades, PnL 801.801575
- oos_2_2026_q1: 20 trades, PnL -10.772803

### Interpretation

L5-R fixed the structural problem:

- Task991 changed 337 trades.
- Task1001 changed 36 trades.
- Drawdown improved from -45.49% to -32.45%.
- Final equity improved from 2,412.62 to 2,662.53.

But it did not solve the trading-performance problem:

- It still underperformed Task941 by 276.70 final equity points.
- CAGR is still 2.30 percentage points below Task941.
- MDD is still about 2.96 percentage points worse than Task941.
- It is far below the user target of 30% CAGR.

The next bottleneck is no longer replacement discipline. The next bottleneck is whether L5 score itself is calibrated enough to identify replacements that truly beat the incumbent.

## No-Background Decision-Maker Report

We fixed the stupid part.

The system no longer throws away most of the good baseline. It kept 414 of 450 Task941 trades and replaced only 36.

That made the result much better than the previous L5 attempt.

But it still did not beat the current best baseline.

So the conclusion is:

- L5-R structure: useful
- Current L5 replacement signal: not strong enough
- Strategy: still not accepted

## Artifact Manifest

Primary artifacts:

- `data/artifacts/task_1001_1010_l5_replacement_hurdle_replay/task1001_l5r_source_context_manifest.csv`
- `data/artifacts/task_1001_1010_l5_replacement_hurdle_replay/task1002_l5r_expert_policy_freeze.csv`
- `data/artifacts/task_1001_1010_l5_replacement_hurdle_replay/task1003_pre_registered_l5r_policy.csv`
- `data/artifacts/task_1001_1010_l5_replacement_hurdle_replay/task1004_l5r_replacement_selection_ledger.csv`
- `data/artifacts/task_1001_1010_l5_replacement_hurdle_replay/task1005_l5r_replay_entry_decision_ledger.csv`
- `data/artifacts/task_1001_1010_l5_replacement_hurdle_replay/task1006_l5r_replay_trades.csv`
- `data/artifacts/task_1001_1010_l5_replacement_hurdle_replay/task1007_l5r_replay_equity.csv`
- `data/artifacts/task_1001_1010_l5_replacement_hurdle_replay/task1008_l5r_replay_summary.csv`
- `data/artifacts/task_1001_1010_l5_replacement_hurdle_replay/task1009_l5r_vs_task941_attribution.csv`
- `data/artifacts/task_1001_1010_l5_replacement_hurdle_replay/task1010_l5r_governance_closeout.csv`
- `data/artifacts/task_1001_1010_l5_replacement_hurdle_replay/artifact_manifest.csv`

Validation commands:

```text
python scripts/trader_brain_1001_1010_l5_replacement_hurdle_replay.py
python scripts/task_artifact_manifest.py --task-dir data/artifacts/task_1001_1010_l5_replacement_hurdle_replay
python scripts/trader_brain_1001_1010_l5_replacement_hurdle_replay_validate.py
python -m unittest tests.test_trader_brain_1001_1010_l5_replacement_hurdle_replay
python scripts/trader_brain_941_950_slot_capped_selection_replay_validate.py
```

Validation authority:

- `DIAGNOSTIC_L5_REPLACEMENT_HURDLE_REPLAY_ONLY`

Next action:

- Do not add another broad layer.
- Diagnose the 36 replacements directly.
- Build a replacement-signal calibration task that compares rejected challengers, accepted challengers, and displaced incumbents without using future outcomes as selection input.
