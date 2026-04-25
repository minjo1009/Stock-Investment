# Task T099 - Breakout Sensitivity Test Plan (Prep)

## 1) Scope and Guardrails
- Purpose: design a rigorous sensitivity experiment for the T098.5 bottleneck (`BREAKOUT`) without changing core strategy logic in production code.
- Scope: analysis/docs/spec only.
- Data inputs:
  - `data/raw/us_daily`
  - `docs/reports/task_098/task_098_signal_density_diagnosis.json`
  - `docs/reports/task_098_5/task_098_5_signal_funnel.json`
  - `docs/reports/task_097/task_097_execution_density_capital_efficiency.json`
  - `docs/reports/task_096/task_096_revalidation.json`
  - `docs/reports/task_093/task_093_capital_backtest.json`

## 2) Working Hypotheses from T098.5
- H1: Breakout gate is the primary bottleneck (largest pre-execution elimination share).
- H2: Relaxing breakout strictness can increase signal density and improve recall proxy.
- H3: Uncontrolled relaxation may reduce quality (precision proxy, PF, Sharpe) and raise MDD.
- H4: Risk overlay is not the dominant blocker (low absolute blocked count); pre-overlay filtering dominates.
- H5: Test design must isolate each factor independently (one-change-at-a-time).

## 3) Independence Rule (Mandatory)
- One-change-at-a-time relative to baseline.
- For each test family (A/B/C/D/E), modify exactly one factor while freezing all others at baseline.
- No combined-factor runs in Phase 1.
- Combined runs are allowed only in Phase 2 and only after single-factor acceptance gates are met.

## 4) Baseline Definition
- Baseline anchor: configuration represented by T093/T096/T098 lineage (current adopted setup).
- Baseline outputs to capture:
  - funnel counts (0..7),
  - signal density and execution ratio,
  - filtered winners/losers,
  - PF / Sharpe / MDD.
- Baseline reproducibility check:
  - Stage ratios and blocked-trade profile must match existing reports within tolerance.

## 5) A/B/C/D/E Sensitivity Matrix
| Family | Factor | Levels | Fixed Controls | Primary Risk |
|---|---|---|---|---|
| A | Breakout window | `10`, `15`, `20 (baseline)`, `30` | threshold, trigger mode, structure filter, volume gate fixed | over-triggering (short windows) or under-triggering (long windows) |
| B | Breakout threshold | `0.0% (baseline)`, `0.25%`, `0.5%` above breakout reference | window, trigger mode, structure filter, volume gate fixed | quality erosion for low threshold; sparsity for high threshold |
| C | Trigger mode | `HIGH_TOUCH` vs `CLOSE_CONFIRM (baseline)` | window, threshold, structure filter, volume gate fixed | intrabar noise vs delayed confirmation |
| D | Structure filter | `OFF`, `LIGHT`, `BASELINE` | window, threshold, trigger mode, volume gate fixed | trend-quality leakage or over-filtering |
| E | Volume gate | `OFF`, `LIGHT`, `BASELINE` | window, threshold, trigger mode, structure filter fixed | micro-liquidity noise or unnecessary opportunity loss |

Notes:
- Level labels are protocol-level definitions; implementation mapping must be explicit in T099 execution artifact.
- If a family cannot be realized without logic edits, it is marked `DEFERRED` with reason.

## 6) Scenarios
- S0: Full-period, selected universe (primary decision scenario).
- S1: Full-period, default universe counterfactual (attribution only; not direct deployment).
- S2: Regime/time slices (at minimum: early/mid/late split) for stability of directionality.
- S3: Cost stress (baseline cost and high-cost variant) for robustness.
- S4: Capacity stress proxy (if available): same rules, constrained slots/capital.

## 7) Metrics and Definitions
- Signal density:
  - `candidate_rate = stage5 / stage1`
  - `generated_rate = stage6 / stage1`
  - `executed_rate = stage7 / stage1`
- Precision proxy:
  - `PP20 = winners_20 / generated_signals`, winner if 20-bar forward return > 0.
  - Also report `PP10`.
- Recall proxy:
  - `RP20 = captured_winners_20 / total_reference_winners_20`
  - Reference set = baseline analyzable opportunities (fixed window) for comparability.
- Filtered winners/losers:
  - for each filter, count and net forward-return impact of removed signals (`5/10/20` bars).
- Portfolio impacts:
  - `Profit Factor`, `Sharpe`, `Max Drawdown`, `Return %`, `trade_count`.
- Stability metrics:
  - direction consistency across time slices,
  - variance of metric deltas vs baseline.

## 8) Acceptance / Rejection Logic
- Family-level candidate acceptance (single-factor):
  1. Signal density improves meaningfully:
     - `generated_signals >= baseline * 1.25` OR `stage6-stage7 loss does not worsen`.
  2. Quality is preserved:
     - `PP20` drop <= 10% relative.
  3. Portfolio risk-adjusted performance is non-inferior:
     - `Sharpe >= baseline - 0.05`
     - `MDD <= baseline + 1.0 pct-pt`
  4. Filtered winners penalty is controlled:
     - no evidence of large additional winner filtering vs baseline in the same horizon bucket.
- Reject if any hard-fail condition:
  - `Sharpe < baseline - 0.10`
  - `MDD > baseline + 2.0 pct-pt`
  - severe instability (direction flips in majority of time slices).

## 9) Execution Order and Stop Criteria
1. Baseline reproduction and schema validation.
2. Family A sweep (window), rank by density-quality frontier.
3. Family B sweep (threshold).
4. Family C sweep (trigger mode).
5. Family D sweep (structure filter).
6. Family E sweep (volume gate).
7. Phase 2 combined tests only for accepted single-factor winners.

Stop criteria:
- Stop a family early if first two non-baseline levels both hard-fail.
- Stop full protocol if baseline cannot be reproduced or data integrity checks fail.
- Pause for review before Phase 2 if no family passes acceptance.

## 10) Validation Commands (Protocol)
Use these when T099 runner artifacts exist:

```bash
# 1) Run baseline reproduction
python -m src.backtest.analysis_breakout_sensitivity_099 --profile baseline

# 2) Run one family at a time (independence rule enforced)
python -m src.backtest.analysis_breakout_sensitivity_099 --family A
python -m src.backtest.analysis_breakout_sensitivity_099 --family B
python -m src.backtest.analysis_breakout_sensitivity_099 --family C
python -m src.backtest.analysis_breakout_sensitivity_099 --family D
python -m src.backtest.analysis_breakout_sensitivity_099 --family E

# 3) Validate output schema
python -m unittest tests.test_analysis_breakout_sensitivity_099 -v
```

## 11) Output Schema (Decision-Oriented)
Primary artifact recommendation:
- `docs/reports/task_099/task_099_breakout_sensitivity_results.json`
- `docs/reports/task_099/task_099_breakout_sensitivity_results.md`

Required JSON fields:
- `baseline`
- `matrix`
- `runs[]` with per-run:
  - `config_delta`
  - `independence_ok`
  - `signal_density`
  - `quality_proxy`
  - `portfolio_metrics`
  - `decision` (`PASS|WARNING|FAIL`)
  - `reasons[]`
- `accepted_candidates[]`
- `rejected_candidates[]`
- `next_phase_recommendation`

## 12) Final Protocol Rule
- This plan is a decision protocol, not a tuning action.
- No production strategy parameters are changed in this prep task.
