# Task881-890 GPT Institutional Review Synthesis

## Decision Summary

- Verdict: review captured and incorporated.
- Authority: critique only, not source-of-truth.
- Strategy acceptance status: `NOT_ACCEPTED`.
- Deployment readiness: `DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY`.
- Real capital: `FORBIDDEN`.

## Review Findings Incorporated

1. Universe hindsight risk:
   - The 10x7 universe is now described as `fixed_research_universe_diagnostic_only`.
   - It must not be called PIT top500 or a historical tradable universe without as-of inclusion evidence.

2. Policy freeze risk:
   - Task887 now requires policy version, rebalance clock, exit/hold rule, exposure caps, cost model, slippage model, contradiction handling, and source-gap handling before OOS.

3. `reduce` state risk:
   - `reduce` now requires an existing open position.
   - Flat-state reduce cannot create a synthetic sell.

4. Source-time leakage risk:
   - Prep artifacts now expose source-time status rows.
   - Missing historical evidence remains `source_gap` or `not_ready`.
   - Future source/edge/bundle/trade-spec negative fixtures are rejected.

5. Overclaim risk:
   - Task880 remains plumbing evidence only.
   - Task881-890 prep PASS does not mean replay permission.

## Required Closeout Language

```text
This replay is diagnostic historical evidence only.
It does not change strategy acceptance.
It does not establish deployment readiness.
It does not permit real capital.
Task880-890 results are not broker truth.
GPT/institutional review is critique only, not source-of-truth.
Strategy: NOT_ACCEPTED
Deployment: DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY
Real Capital: FORBIDDEN
```

## Artifact Manifest

- Inputs: GPT/institutional review notifications from Task881-890 implementation turn.
- Outputs: this synthesis report and strengthened Task882, Task887, Task889, Task890 contracts.
- Validation command: `python scripts/trader_brain_881_890_historical_brain_backtest_validate.py`.
