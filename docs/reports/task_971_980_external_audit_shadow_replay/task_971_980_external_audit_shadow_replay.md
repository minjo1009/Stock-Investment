# Task971-980 External Audit Shadow Replay

## Decision Summary

- Verdict: the pre-registered shadow ranking policy was replayed successfully, but it did not beat the Task941 slot10 baseline.
- Policy ID: `slot10_external_audit_shadow_rank_v1`.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Key result: `1000 -> 2238.21`, CAGR `16.638396%`, MDD `-30.394469%`.
- Benchmark: QQQ `1000 -> 1925.31`; the policy beat QQQ but missed the Task941 baseline.
- Task941 slot10 baseline: `1000 -> 2939.23`, CAGR `22.870268%`, MDD `-29.484953%`.

## Quant Expert Report

### External Review And Policy Freeze

Three read-only GPT/subagent audit panels reviewed the plan before replay:

- Institutional trader panel: conditionally approved one controlled replay if the policy was pre-registered and tie-breaks were frozen.
- Theme/macro/policy panel: approved theme/macro lens only as interpretation, not as buy/sell or direct ranking input.
- Quant/backend panel: approved replay only after policy pre-registration and validator coverage.

Frozen policy:

```text
Policy ID: slot10_external_audit_shadow_rank_v1
Input: Task969 shadow ranking rows
Cohort: entry_date
Eligibility: exclude only trader_action == hard_block
Current hard_block count: 0
Rank: shadow_rank_score descending
Tie-break 1: trader_action priority enter > monitor > wait
Tie-break 2: theme ascending
Tie-break 3: symbol ascending
Tie-break 4: trade_spec_id ascending
Select: top 10 per entry_date
Harness: Task941 cost, slippage, hold, exit, QQQ benchmark, and slot10 semantics
```

### Data Source And Source Readiness

Inputs:

- `data/artifacts/task_961_970_external_audit_redesign/task969_shadow_trader_ranking.csv`
- `data/artifacts/task_921_930_controlled_adapter_gate/task929_controlled_trade_specs.csv`
- Task941 slot10 baseline trades and summary
- Task880 canonical daily prices and QQQ calendar through the Task941 harness functions

This remains diagnostic-only. It does not create acceptance or deployment readiness.

### Exact Join Keys

- Selection input to trade spec: `trade_spec_id`.
- Market data: exact `symbol` and exact session date.
- No symbol/date/price/time proximity fallback was used.

### Leakage Audit

Selection consumed pre-existing shadow ranking rows. The policy and selection ledger explicitly forbid:

```text
future_return realized_return pnl post_entry_price_change outcome_rank
```

PnL and return appear only in replay result artifacts.

### Replay Metrics

| Metric | Task941 Slot10 | Task971-980 Shadow Replay |
| --- | ---: | ---: |
| Final equity | 2939.23 | 2238.21 |
| CAGR | 22.870268% | 16.638396% |
| MDD | -29.484953% | -30.394469% |
| Beats QQQ | 1 | 1 |
| Meets CAGR 30 | 0 | 0 |
| Meets MDD -30 | 1 | 0 |

### Split/OOS Metrics

| Split | Closed Trades | PnL | Return On Spent |
| --- | ---: | ---: | ---: |
| development_2021_2024 | 340 | 609.303197 | 1.658585% |
| oos_1_2025 | 90 | 603.059098 | 3.804091% |
| oos_2_2026_q1 | 20 | 25.844049 | 0.584492% |

### Failure Decomposition

- The policy improved over the prior hard-suppression failure, but still lost to Task941.
- Task941 and shadow replay both closed 450 trades.
- Overlap: 313 trades.
- Shadow-only: 137 trades.
- Baseline-only: 137 trades.
- The next diagnosis should compare baseline-only versus shadow-only contribution, especially drawdown and high-upside missed trades.

## No-Background Decision-Maker Report

The new external-audit policy was tested correctly.

It did not collapse like the prior hard filter. It beat QQQ. But it still underperformed the older Task941 slot10 baseline.

So the lesson is not “go back to hard filters.” The lesson is that the new trader-brain ranking is directionally safer than the failed suppression policy, but still not better than the simpler baseline.

Next step is to decompose the 137 baseline-only trades versus the 137 shadow-only trades.

## Artifact Manifest

### Outputs

- `data/artifacts/task_971_980_external_audit_shadow_replay/task971_expert_review_and_policy_freeze.csv`
- `data/artifacts/task_971_980_external_audit_shadow_replay/task972_pre_registered_policy.csv`
- `data/artifacts/task_971_980_external_audit_shadow_replay/task973_policy_selection_ledger.csv`
- `data/artifacts/task_971_980_external_audit_shadow_replay/task974_replay_entry_decision_ledger.csv`
- `data/artifacts/task_971_980_external_audit_shadow_replay/task975_replay_trades.csv`
- `data/artifacts/task_971_980_external_audit_shadow_replay/task976_replay_equity.csv`
- `data/artifacts/task_971_980_external_audit_shadow_replay/task977_skipped_orders.csv`
- `data/artifacts/task_971_980_external_audit_shadow_replay/task978_replay_summary.csv`
- `data/artifacts/task_971_980_external_audit_shadow_replay/task979_by_split.csv`
- `data/artifacts/task_971_980_external_audit_shadow_replay/task979_baseline_shadow_attribution.csv`
- `data/artifacts/task_971_980_external_audit_shadow_replay/task980_governance_closeout.csv`

### Row Counts

- Ranking input rows: 3689.
- Policy preselected rows: 630.
- Actual entered rows under live slot10: 450.
- Deferred by live slot cap: 180.
- Closed trades: 450.
- Skipped orders: 0.

### Validation Commands

- `python scripts/trader_brain_971_980_external_audit_shadow_replay.py`
- `python scripts/task_artifact_manifest.py --task-dir data/artifacts/task_971_980_external_audit_shadow_replay`
- `python scripts/trader_brain_971_980_external_audit_shadow_replay_validate.py`
- `python -m unittest tests.test_trader_brain_971_980_external_audit_shadow_replay`
- `python scripts/trader_brain_961_970_external_audit_redesign_validate.py`

Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
