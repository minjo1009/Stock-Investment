# Task941-950 Slot-Capped Selection Replay

## Decision Summary

- Verdict: implemented and executed slot-capped diagnostic selection replay.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- User target: CAGR 30% or higher, MDD around -30% or better.
- Tested slot caps: 3, 5, and 10 concurrent holdings.
- Input trade specs: 3,689.
- Selection rule: ex-ante L3/L4 features only, no future return, realized return, PnL, price-change, score, or rank from outcome.
- Best balanced result: slot cap 10.
- Slot 10 result: 1,000 -> 2,939.23.
- Slot 10 CAGR: 22.870268%.
- Slot 10 MDD: -29.484953%.
- Slot 10 QQQ comparison: beats QQQ 1,925.31.
- Target status: QQQ beat yes, MDD yes, CAGR 30 no.
- Next action: improve ex-ante selection strength before any acceptance claim.

## Quant Expert Report

The implemented chain is:

```text
Task929 controlled trade specs
-> Task941 ex-ante selection feature panel
-> Task942 slot-capped selection ledger
-> Task943 slot-capped replay trades
-> Task944 slot-capped equity curves
-> Task946 slot-cap comparison
-> Task950 governance closeout
```

Selection features use only current brain artifacts:

- Candidate thesis type.
- Supporting source family count.
- Supporting relation count.
- Positive relation primitive count.
- Source-gap relation count.
- Negative/noise relation count.
- Unresolved source gap count.
- Contradiction state.

Forbidden selection inputs:

```text
future_return
realized_return
pnl
price_change
outcome-derived rank or score
```

Slot results:

```text
slot 3:  1000 -> 2431.97, CAGR 18.503092%, MDD -50.402583%, beats QQQ yes
slot 5:  1000 -> 2212.44, CAGR 16.380672%, MDD -33.215906%, beats QQQ yes
slot 10: 1000 -> 2939.23, CAGR 22.870268%, MDD -29.484953%, beats QQQ yes
```

Split result:

```text
slot 3 OOS-2 2026Q1: +0.245335% return on spent
slot 5 OOS-2 2026Q1: +0.116142% return on spent
slot 10 OOS-2 2026Q1: +0.018062% return on spent
```

Interpretation:

- Slot cap materially improves the broad long-only replay.
- Slot 10 is currently the best balance because it beats QQQ and keeps MDD inside the approximate -30% tolerance.
- Slot 3 concentrates too hard and breaches the drawdown tolerance.
- Slot 5 also breaches the drawdown tolerance.
- None of the tested caps reaches the 30% CAGR target.

## No-Background Decision-Maker Report

This was the right direction.

Buying everything was too broad. Limiting holdings to 3, 5, or 10 improves the strategy. The best current version is 10 holdings. It beats QQQ and keeps drawdown near the stated tolerance.

But it still does not reach the real target. The best CAGR is 22.87%, not 30%+. So the next work should not celebrate this as done. It should strengthen the selection rule so the brain rejects more weak candidates for better reasons.

## Artifact Manifest

- Script: `scripts/trader_brain_941_950_slot_capped_selection_replay.py`.
- Validator: `scripts/trader_brain_941_950_slot_capped_selection_replay_validate.py`.
- Test: `tests/test_trader_brain_941_950_slot_capped_selection_replay.py`.
- Feature panel: `data/artifacts/task_941_950_slot_capped_selection_replay/task941_selection_feature_panel.csv`.
- Selection ledger: `data/artifacts/task_941_950_slot_capped_selection_replay/task942_slot_capped_selection_ledger.csv`.
- Trades: `data/artifacts/task_941_950_slot_capped_selection_replay/task943_slot_capped_replay_trades.csv`.
- Equity curves: `data/artifacts/task_941_950_slot_capped_selection_replay/task944_slot_capped_equity_curves.csv`.
- Skipped orders: `data/artifacts/task_941_950_slot_capped_selection_replay/task945_slot_capped_skipped_orders.csv`.
- Summary: `data/artifacts/task_941_950_slot_capped_selection_replay/task946_slot_capped_summary.csv`.
- Split summary: `data/artifacts/task_941_950_slot_capped_selection_replay/task947_slot_capped_by_split.csv`.
- Source manifest: `data/artifacts/task_941_950_slot_capped_selection_replay/task948_slot_capped_source_manifest.csv`.
- Governance closeout: `data/artifacts/task_941_950_slot_capped_selection_replay/task950_slot_capped_governance_closeout.csv`.
- Validation command: `python scripts/trader_brain_941_950_slot_capped_selection_replay_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
