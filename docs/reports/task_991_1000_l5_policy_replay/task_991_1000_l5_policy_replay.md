# Task991-1000 L5 Policy Replay

## Decision Summary

Task991-1000 pre-registered and replayed one L5-informed policy:

- Policy: `slot10_l5_payoff_trader_rank_v1`
- Input rows: 3,689 Task969 ranking rows
- Policy preselected entries: 630
- Actual entered trades: 450
- Initial capital: 1,000
- Final equity: 2,412.62
- CAGR: 18.322401%
- Max drawdown: -45.494300%
- Beats QQQ: yes
- Beats Task941 slot10 baseline: no
- Meets 30% CAGR target: no
- Meets -30% MDD target: no

Decision:

`slot10_l5_payoff_trader_rank_v1` is not good enough. It is diagnostic evidence only and does not improve the project state.

Standing statuses remain:

- Strategy acceptance: `NOT_ACCEPTED`
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
- Real capital: `FORBIDDEN`

## Quant Expert Report

### Policy Definition

The policy used Task981-990 L5 panels to rank each entry-date cohort. It did not use realized return, PnL, future return, post-entry price change, outcome rank, or exit price.

Ranking components:

- Task969 shadow rank
- L5-A reflectedness
- L5-B payoff shape
- L5-C timing
- L5-D best expression and liquidity
- L5-E risk budget
- L5-V timestamp validation

The policy used slot cap 10 and the same cost/slippage assumptions as Task941.

### Result Versus Baseline

Task941 slot10 baseline:

- Final equity: 2,939.23
- CAGR: 22.870268%
- MDD: -29.484953%
- Closed trades: 450

Task991-1000 L5 policy:

- Final equity: 2,412.62
- CAGR: 18.322401%
- MDD: -45.494300%
- Closed trades: 450

The L5 policy was worse than Task941 on both return and drawdown.

### Structural Diagnosis

The policy changed too much of the book:

- Baseline trades: 450
- L5 policy trades: 450
- Overlap: 113
- L5-only: 337
- Baseline-only: 337

This means the policy behaved like a new strategy rather than a careful L5 refinement over the best known baseline.

Split result:

- development_2021_2024: 340 trades, PnL 779.983193
- oos_1_2025: 90 trades, PnL 768.229929
- oos_2_2026_q1: 20 trades, PnL -135.593529

Bucket diagnostics:

- `theme_leader_proxy` underperformed `theme_alternative_proxy`
- `crowded_theme_review` was negative
- `pullback_after_positive_trend_proxy` was stronger than broad positive momentum
- right-tail buckets helped but did not control drawdown

Largest loser examples include ZS, ASTS, TER, NET, AMD, and RKLB. ASTS also appears among the largest winners, which confirms that convex names require position/risk control rather than simple inclusion or exclusion.

### Failure Interpretation

The L5 feature layer is useful, but the first policy translation was too blunt:

1. It over-rotated away from the Task941 baseline.
2. It treated theme leadership as broadly positive, but theme leaders did not outperform alternatives in this replay.
3. It did not control right-tail drawdown enough.
4. It did not reduce late-period 2026Q1 weakness.
5. It still lacks a replacement hurdle: a new L5 pick must beat the displaced baseline pick, not merely score well in isolation.

## No-Background Decision-Maker Report

We ran the next step.

It failed.

The new L5 policy made money and beat QQQ, but it was worse than our current best baseline. It also had much worse drawdown.

The important learning is clear: L5 should not replace the whole selection stack. It must act as a replacement hurdle and risk governor on top of Task941, otherwise it changes too many trades at once.

## Artifact Manifest

Primary artifacts:

- `data/artifacts/task_991_1000_l5_policy_replay/task991_l5_expert_policy_freeze.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task992_pre_registered_l5_policy.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task993_l5_policy_selection_ledger.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task994_l5_replay_entry_decision_ledger.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task995_l5_replay_trades.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task996_l5_replay_equity.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task997_l5_skipped_orders.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task998_l5_replay_summary.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task998_l5_replay_summary.json`
- `data/artifacts/task_991_1000_l5_policy_replay/task999_l5_replay_by_split.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task999_l5_vs_task941_attribution.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task999_l5_bucket_attribution_evaluation_only.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task999_l5_tail_trades_evaluation_only.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task1000_l5_policy_source_manifest.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task1000_l5_policy_governance_closeout.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task991_1000_summary.csv`
- `data/artifacts/task_991_1000_l5_policy_replay/task991_1000_summary.json`
- `data/artifacts/task_991_1000_l5_policy_replay/artifact_manifest.csv`

Validation commands:

```text
python scripts/trader_brain_991_1000_l5_policy_replay.py
python scripts/task_artifact_manifest.py --task-dir data/artifacts/task_991_1000_l5_policy_replay
python scripts/trader_brain_991_1000_l5_policy_replay_validate.py
python -m unittest tests.test_trader_brain_991_1000_l5_policy_replay
```

Validation authority:

- `DIAGNOSTIC_L5_POLICY_REPLAY_ONLY`

Next action:

- Build a conservative L5 replacement-hurdle policy that starts from Task941 slot10 and only replaces a baseline pick when L5 evidence clears a strict margin and risk budget check.
