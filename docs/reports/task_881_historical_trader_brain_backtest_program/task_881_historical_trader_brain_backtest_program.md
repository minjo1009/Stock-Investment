# Task881 Historical Trader Brain Backtest Program

## Decision Summary

- Verdict: planned.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Objective: prepare a real Trader Brain historical backtest from 2021-01-01 through 2026-03-31.
- Universe: `data/raw/theme_universe_10x7.csv`, 10 themes x 7 symbols.
- Benchmark: QQQ.
- Initial capital: `$1,000`.
- Key correction: Task880 was a plumbing basket replay; Task881-890 must reconstruct brain-state decisions as-of each historical decision date.
- Next action: execute Task882 before any new backtest run.

## Quant Expert Report

This program exists because the Task880 replay bought all 70 symbols equally on one date. That proved data and replay plumbing, not the Trader Brain.

The required chain is:

```text
as-of historical sources
-> L1 source evidence
-> L2 primitive fact and economic meaning
-> L3 relationship graph state
-> L4 candidate bundle
-> L5 trader decision policy
-> historical trade spec
-> split/OOS/cost replay
-> artifact audit
```

No layer may use:

- future price;
- future label;
- future source publication;
- future membership changes;
- realized return;
- missing labels as negatives;
- symbol/date/price/time proximity fallback.

Program split:

- Development: 2021-01-01 through 2024-12-31.
- OOS-1: 2025-01-01 through 2025-12-31.
- OOS-2: 2026-01-01 through 2026-03-31.

Task sequence:

| task_id | title | owner | output |
| --- | --- | --- | --- |
| Task881 | Historical Trader Brain Backtest Program | Research Governance | parent plan |
| Task882 | Period Split Universe Contract | Research Governance | fixed period, split, universe, benchmark |
| Task883 | Historical Evidence Source-Time Panel | Data & Research | source-time panel contract |
| Task884 | Brain Layer State Reconstruction | Brain Layer Engineering | L1-L3 state reconstruction contract |
| Task885 | Relationship Graph Rolling Snapshot | Graph Engineering | rolling graph snapshot contract |
| Task886 | Candidate Bundle Generation Contract | Research Governance | historical candidate bundle rules |
| Task887 | Trader Decision Policy Contract | Trader Brain Policy | skip/reduce/activate/size rules |
| Task888 | Historical Trade-Spec Adapter Contract | Backtest Infra | as-of trade spec schema |
| Task889 | Replay Harness Config Data Gate | Backtest Infra | split/OOS/cost/slippage config |
| Task890 | Leakage OOS Cost Go/No-Go | Quant Review | run permission gate |

Subagent allocation:

- Data & Market Microstructure: Task882, Task883, Task889 data gate.
- Brain Layer Engineering: Task884.
- Graph Engineering: Task885.
- Trader/PM Policy Review: Task886, Task887.
- Backtest & Simulation Infra: Task888, Task889.
- Quant Risk Review: Task890.
- GPT/Chrome external review: review-only, no source-of-truth, no acceptance authority.

## No-Background Decision-Maker Report

We are not ready to run the real brain backtest yet. We are ready to define the ten gates that make the run meaningful. The key change is that the system must decide historically from what it knew at that time, not buy every symbol in the universe.

## Artifact Manifest

- Inputs: Task756-880 reports, `data/raw/theme_universe_10x7.csv`, Task836 adapter inputs, Task880 data artifacts.
- Outputs: Task881-890 reports, program steps, decision rows, validator.
- Validation command: `python scripts/trader_brain_881_890_historical_brain_backtest_validate.py`.

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
