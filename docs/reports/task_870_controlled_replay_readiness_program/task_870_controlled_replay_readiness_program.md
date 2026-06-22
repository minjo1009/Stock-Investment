# Task870 Controlled Replay Readiness Program

## Decision Summary

- Verdict: executed for the explicit harness universe.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.
- Problem being fixed: Task860 exposed that data certification alone is not enough; adapter inputs still lack controlled trade-spec fields.
- What changed: Task870-Task879 now have a task-scoped full data acquisition and diagnostic controlled replay implementation.
- Next action: decompose the weak diagnostic replay result before changing any trade-spec rule.

## Quant Expert Report

Task828-839 intentionally created a dry adapter input with no symbol, side, entry, exit, sizing, PnL, order id, score, or rank. That was correct for a research-only safety gate.

Task860 showed the next missing layer:

```text
candidate bundle
-> dry adapter input
-> controlled trade-spec
-> certified market data gate
-> controlled replay
```

The executed program has two parallel tracks:

- data readiness: calendar, corporate actions, daily/15m normalization, gate validator;
- trade-spec readiness: explicit symbol universe, side policy, entry/exit policy, position policy, and no-leakage authority.

Execution result:

- Explicit harness symbols: 16.
- Daily bars: all 16 symbols acquired from 2021-01-04 through 2026-06-12.
- Recent 15m bars: all 16 symbols acquired from 2026-03-19 through 2026-06-12.
- Canonical daily status: 16 ok.
- Canonical 15m status: 16 ok.
- Corporate action status: 16 ok.
- Market data gate: `READY_FOR_CONTROLLED_REPLAY_PLAN`.
- Controlled trade specs: 22 rows.
- Diagnostic replay trades: 22 rows.
- Initial capital: `$1,000`.
- Diagnostic strategy final capital: `$997.69`.
- QQQ reference final capital: `$2,406.19`.
- Strategy acceptance remains `NOT_ACCEPTED`.

## Program Steps

| task_id | title | purpose | output |
| --- | --- | --- | --- |
| Task870 | Controlled Replay Readiness Program | parent program | this report |
| Task871 | Adapter Trade-Spec Authority Contract | define who may add symbol/side/entry/exit/position_size | trade-spec authority contract |
| Task872 | Explicit Harness Universe Contract | define symbols eligible for the first replay | explicit universe and bundle-to-symbol map |
| Task873 | Exchange Calendar Certification | certify 2021-current US session calendar | calendar manifest |
| Task874 | Corporate Action Adjustment Proof | attach split/dividend/adjustment proof | corporate action readiness manifest |
| Task875 | Daily Canonical Normalization Plan | normalize daily candidate data into replay-safe shape | daily canonicalization plan |
| Task876 | Intraday 15m Canonical Normalization Plan | normalize 15m data and regular-hours policy | intraday canonicalization plan |
| Task877 | Market Data Gate Promotion Validator | define promotion rules from partial-no-replay to ready | validator contract |
| Task878 | Controlled Trade-Spec Builder Plan | build replay rows from adapter inputs without hidden inference | builder plan |
| Task879 | First Controlled Replay Retry Plan | retry replay only if Task877 and Task878 pass | retry plan |

## No-Background Decision-Maker Report

The earlier data work was not wasted. It found the data blockers. Task870-879 now closes the first bridge by acquiring the full explicit harness universe and creating controlled trade-spec rows without hidden symbol or side inference.

## Artifact Manifest

- Inputs: Task850-869 reports and artifacts; Task836 dry adapter inputs; Task872 explicit universe.
- Outputs: Task870-879 design reports, registry rows, full data acquisition audit, canonical daily/15m panels, controlled trade specs, diagnostic replay summary.
- Full data artifacts: `data/artifacts/task_870_879_full_controlled_replay/`.
- Raw task-scoped downloads: `data/raw/yfinance/task_870_879_full_market_data/`.
- Validation commands:
  - `python scripts/trader_brain_870_879_full_replay_validate.py`
  - `python scripts/trader_brain_870_879_readiness_program_validate.py`
  - `python scripts/task_registry_validate.py --registry tasks/task_registry.csv --root .`

Test results do not modify strategy acceptance status.

Strategy: `NOT_ACCEPTED`
Deployment: `DATA_INFRASTRUCTURE_ONLY_NOT_DEPLOYMENT_READY`
Real Capital: `FORBIDDEN`
