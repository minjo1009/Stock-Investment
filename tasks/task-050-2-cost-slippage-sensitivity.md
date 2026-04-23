# Task 050-2: Cost / Slippage Sensitivity Scenario

## Goal
- Validate strategy robustness under increasing market frictions (fee + slippage).

## Scope
- Added scenario-based sensitivity analysis CLI using full-backtest rerun path.
- Compared KPI drift against baseline and identified collapse point where PF < 1.
- Included regime-level and symbol-level change views by scenario.

## Main Files
- `src/backtest/analysis_cost_sensitivity.py`

## Status
- DONE
