# Task951-960 Conviction Risk Filter Replay

## Decision Summary

- Verdict: implemented and executed, but did not improve the Task941-950 slot-10 baseline.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- User target: CAGR 30% or higher, MDD around -30% or better.
- Baseline to beat: Task941-950 slot 10.
- Baseline result: 1,000 -> 2,939.23, CAGR 22.870268%, MDD -29.484953%.
- Tested policies:
  - `theme_cap4_slot10_v1`
  - `momentum_rank_cash_slot10_v1`
  - `cash_qqq_hurdle_slot10_v1`
  - `regime_theme_slot10_v1`
  - `trader_veto_slot10_v1`
- Best tested policy: `theme_cap4_slot10_v1`.
- Best tested policy result: 1,000 -> 2,213.96, CAGR 16.395981%, MDD -44.410247%.
- Target status: no tested policy beats baseline, reaches CAGR 30%, or preserves MDD tolerance.
- Decision: reject these filters for promotion. Keep Task941-950 slot 10 as the current diagnostic baseline.

## Quant Expert Report

Subagent review summary:

- Institutional panel: slot cap is directionally right, but the project is still diagnostic and not desk-adoptable.
- Quant/risk panel: keep 10 slots as the baseline; do not move narrower just to look selective.
- Governance/backend panel: keep this work diagnostic-only, preserve lineage and status boundaries.

The implemented chain is:

```text
Task941 feature panel
-> prior-session price context
-> QQQ hurdle / theme cap / regime throttle / drawdown throttle policy tests
-> diagnostic replay
-> baseline comparison
-> governance closeout
```

Allowed ex-ante features:

- Existing L3/L4 conviction fields.
- Prior-session symbol momentum.
- Prior-session QQQ momentum.
- Prior-session relative momentum versus QQQ.
- Prior-session QQQ regime state.
- Drawdown state from replay equity available before new entry.

Forbidden inputs remain blocked:

```text
future_return
realized_return
PnL
price_change after entry
outcome-derived score or rank
symbol/date/price/time proximity fallback
```

Policy result:

```text
theme_cap4_slot10_v1:        1000 -> 2213.96, CAGR 16.395981%, MDD -44.410247%
momentum_rank_cash_slot10_v1: see task959 summary
cash_qqq_hurdle_slot10_v1:   1000 -> 2095.36, CAGR 15.178148%, MDD -43.586708%
regime_theme_slot10_v1:      1000 -> 1602.75, CAGR 9.429791%, MDD -43.030984%
trader_veto_slot10_v1:       1000 -> 1720.90, CAGR 10.926860%, MDD -48.222628%
```

Interpretation:

- Naive price momentum and QQQ hurdle filters removed too many useful entries.
- Theme caps reduced concentration but also removed much of the edge.
- Regime and drawdown throttles did not protect drawdown enough and reduced return materially.
- The current project cannot reach CAGR 30 by simple veto layering on top of Task941-950.
- The missing layer is not another broad filter. It is stronger source-backed conviction and thesis freshness.

## No-Background Decision-Maker Report

This pass failed in a useful way.

We tried to make the brain more trader-like by adding cash, QQQ hurdle, regime, theme cap, and drawdown throttle rules. The rules were leak-safe, but they made performance worse.

So the answer is not “tighten random filters.” The answer is that the brain still lacks real conviction quality. It needs better source-backed thesis freshness, duplicate thesis suppression, and independent evidence quality before risk filters can help.

## Artifact Manifest

- Script: `scripts/trader_brain_951_960_conviction_risk_filter_replay.py`.
- Validator: `scripts/trader_brain_951_960_conviction_risk_filter_replay_validate.py`.
- Test: `tests/test_trader_brain_951_960_conviction_risk_filter_replay.py`.
- Target gap summary: `data/artifacts/task_951_960_conviction_risk_filter_replay/task951_failure_and_target_gap.csv`.
- Feature panel: `data/artifacts/task_951_960_conviction_risk_filter_replay/task952_conviction_price_context_panel.csv`.
- Decision ledger: `data/artifacts/task_951_960_conviction_risk_filter_replay/task953_cash_qqq_regime_decision_ledger.csv`.
- Source manifest: `data/artifacts/task_951_960_conviction_risk_filter_replay/task956_conviction_risk_source_manifest.csv`.
- Skipped orders: `data/artifacts/task_951_960_conviction_risk_filter_replay/task957_conviction_risk_skipped_orders.csv`.
- Equity curves: `data/artifacts/task_951_960_conviction_risk_filter_replay/task958_conviction_risk_equity_curves.csv`.
- Trades: `data/artifacts/task_951_960_conviction_risk_filter_replay/task959_conviction_risk_replay_trades.csv`.
- Replay summary: `data/artifacts/task_951_960_conviction_risk_filter_replay/task959_conviction_risk_replay_summary.csv`.
- Governance closeout: `data/artifacts/task_951_960_conviction_risk_filter_replay/task960_conviction_risk_governance_closeout.csv`.
- Validation command: `python scripts/trader_brain_951_960_conviction_risk_filter_replay_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
