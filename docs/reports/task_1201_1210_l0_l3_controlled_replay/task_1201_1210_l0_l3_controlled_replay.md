# Task1201-1210 L0-L3 Controlled Replay

## Decision Summary

- Verdict: `diagnostic_l0_l3_controlled_replay_executed_not_accepted`.
- Best variant: `l0_l3_slot5_v1`.
- Best final equity: 1970.36.
- Best CAGR: 0.140442.
- Best MDD: -0.387434.
- Benchmark final equity: 1847.0265.
- Target CAGR >= 30%: failed.
- Target MDD >= -30%: failed.
- Benchmark QQQ: passed by best variant only.
- L4 cards: 3150.
- L5 trade specs: 3100.
- Replay trades: 1116.
- Diagnostic replay executed: 1.
- Selection promoted: 0.
- Strategy acceptance: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Next action: diagnose_l0_l3_replay_vs_task1171_and_strengthen_candidate_quality_or_risk_controls.

## Quant Expert Report

This task connects Task1191-1200 L0-L3 compressed candidates into a controlled diagnostic monthly replay.

Inputs:

- `task1200_replay_preregistration_gate.csv`
- `task1197_compressed_candidates.csv`
- `data/raw/yfinance/task_1171_1180_public_filer_proxy/daily/<SYMBOL>/<SYMBOL>_daily.csv`

Join keys:

- `decision_asof_ts`
- `symbol`
- `trade_spec_id`
- next decision date from the ordered decision calendar

Controls:

- Uses only pre-registered Task1200 candidate compression.
- Uses top50 L4 cards only.
- Runs slot 3, 5, and 10 variants.
- Uses equal-weight monthly holding periods.
- Applies 20 bps round-trip cost in the main replay.
- Keeps acceptance and real-capital status unchanged.

Replay metrics:

| Variant | Final equity | CAGR | MDD | Trades | Win rate | QQQ beat |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| `l0_l3_slot10_v1` | 1330.2749 | 0.056856 | -0.395714 | 620 | 0.512903 | no |
| `l0_l3_slot3_v1` | 1716.4529 | 0.11036 | -0.463951 | 186 | 0.505376 | no |
| `l0_l3_slot5_v1` | 1970.36 | 0.140442 | -0.387434 | 310 | 0.53871 | yes |

Leakage audit:

- L4 and L5 assignment rows carry `assignment_uses_future_outcome=0`.
- Price rows carry `future_price_used_for_assignment=0`.
- Outcomes remain evaluation-only and do not enter candidate assignment.
- QQQ is used as benchmark only.

Split/OOS metrics:

- Not performed in this task.
- This is a controlled diagnostic replay over the Task1171 broad public-filer proxy period.
- Split/OOS remains a blocker before any strategy acceptance claim.

Cost/slippage stress:

| Cost bps | Variant | Final equity | CAGR | MDD | QQQ beat |
| ---: | --- | ---: | ---: | ---: | --- |
| 0.0 | `l0_l3_slot10_v1` | 1505.3669 | 0.082483 | -0.355086 | no |
| 0.0 | `l0_l3_slot3_v1` | 1942.1107 | 0.137255 | -0.451278 | yes |
| 0.0 | `l0_l3_slot5_v1` | 2228.3867 | 0.167963 | -0.373113 | yes |
| 20.0 | `l0_l3_slot10_v1` | 1330.2749 | 0.056856 | -0.395714 | no |
| 20.0 | `l0_l3_slot3_v1` | 1716.4529 | 0.11036 | -0.463951 | no |
| 20.0 | `l0_l3_slot5_v1` | 1970.36 | 0.140442 | -0.387434 | yes |
| 50.0 | `l0_l3_slot10_v1` | 1104.5552 | 0.019456 | -0.452072 | no |
| 50.0 | `l0_l3_slot3_v1` | 1425.4945 | 0.071108 | -0.482463 | no |
| 50.0 | `l0_l3_slot5_v1` | 1637.4836 | 0.100273 | -0.410306 | no |
| 100.0 | `l0_l3_slot10_v1` | 809.1961 | -0.040193 | -0.534878 | no |
| 100.0 | `l0_l3_slot3_v1` | 1044.6627 | 0.008502 | -0.553115 | no |
| 100.0 | `l0_l3_slot5_v1` | 1201.4042 | 0.036194 | -0.49245 | no |

Failure decomposition:

- The new L0-L3 compression materially improves the Task1171 broad-universe collapse.
- It still fails the user's 30% CAGR target.
- It still fails the -30% MDD tolerance.
- Slot10 dilution suggests candidate rank quality decays after the strongest few names.
- Slot5 being best suggests the next layer should improve entry/exit/risk selection rather than simply widening holdings.

Remaining blockers:

- No split/OOS acceptance evidence.
- True exchange-listed PIT universe remains incomplete.
- L4/L5 entry, exit, replacement, and drawdown controls are still weak.
- No real-capital or deployment readiness change is allowed from this replay.

## No-Background Decision-Maker Report

We tested whether the new front brain actually helps when connected to trading.

It helped versus the broad-universe failure, but it is not strong enough yet.

The best version beat QQQ, but it did not reach the required return or drawdown standard.

The result is diagnostic only. It does not approve the strategy.

Deployment readiness stays `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.

Real capital stays `FORBIDDEN`.

## Artifact Manifest

Inputs:

- Task1191-1200 compressed candidates and preregistration gate.
- Task1171-1180 yfinance daily price files.

Outputs:

- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1201_preregistration_gate.csv`
- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1202_l4_candidate_cards.csv`
- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1203_l5_trade_specs.csv`
- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1204_price_gate.csv`
- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1205_slot_selections.csv`
- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1206_replay_trades.csv`
- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1206_replay_equity.csv`
- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1207_replay_metrics.csv`
- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1207_cost_sensitivity.csv`
- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1208_failure_attribution.csv`
- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1209_acceptance_gate.csv`
- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1210_l0_l3_controlled_replay_closeout.csv`
- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/task1210_l0_l3_controlled_replay_closeout.json`
- `data/artifacts/task_1201_1210_l0_l3_controlled_replay/artifact_manifest.csv`

Row counts:

- L4 cards: 3150
- L5 trade specs: 3100
- Slot selections: 1116
- Replay trades: 1116
- Cost sensitivity rows: 12

File sizes and hashes:

- `artifact_manifest.csv` records SHA-256 and file size for generated data artifacts.

Validation commands:

- `python scripts/trader_brain_1201_1210_l0_l3_controlled_replay_validate.py`
- `python -m unittest tests.test_trader_brain_1201_1210_l0_l3_controlled_replay`
- `python scripts/task_registry_validate.py --registry tasks/task_registry.csv --root .`

Validation authority:

- PASS means the Task1201-1210 diagnostic artifact contract is internally consistent.
- PASS does not mean strategy acceptance.
- PASS does not mean deployment readiness.
- PASS does not permit real capital.

```text
Test results do not modify strategy acceptance status.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```
