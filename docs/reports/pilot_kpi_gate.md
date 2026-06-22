# Pilot Entry KPI Gate

## Purpose
- 실계좌 초소액 파일럿 진입 허용 여부를 정량 기준으로 고정한다.
- 본 문서는 전략 변경 없이 운영 게이트를 정의하는 통제 문서다.

## Evidence Inputs
- Task 050: Full Backtest (5Y+)
- Task 050-1A: Symbol/Regime Exclusion Candidate Review
- Task 050-1B: Sector Filter Feasibility Review
- Task 050-2: Cost/Slippage Sensitivity
- Task 050-2A: Realistic KIS Cost Stress (fee 0.25%)

## Gate Definitions

### 1) Backtest Gate (Required)
- Scenario 4 (fee 0.25%, slippage 0.10%):
  - `PF >= 1.25`
  - `Net PnL > 0`
  - `Sharpe >= 1.0`
- Scenario 5 (fee 0.25%, slippage 0.20%):
  - `PF >= 1.10`
  - `Net PnL > 0`
- Scenario 6 (fee 0.25%, slippage 0.30%):
  - `PF >= 1.05`
- Max Drawdown:
  - `MDD <= Net PnL * 0.40` or pre-defined absolute max-loss cap (whichever is stricter).

### 2) Regime Gate
- BULL: `Net PnL > 0`
- BEAR: `Net PnL >= -20% of BULL Net PnL` (or stricter absolute floor).

### 3) Stability Gate (Engine/Execution)
- Reconciliation critical mismatch: `0`
- Idempotency failure: `0`
- Position calculation error: `0`
- Loop stability: `N` consecutive successful runs (initial default: `N=30`).

### 4) Operational Constraints (Pilot)
- 1 trade risk `<= 0.5%` of account equity.
- Concurrent positions: `1`
- Daily max entries: `1~2`
- Order type: `LIMIT only`
- Kill Switch: immediate stop must be verified.

### 5) Stop Conditions (Immediate Halt)
- Live cumulative PF `< 1.0`
- Cumulative loss `>= pre-defined loss limit`
- Average live slippage exceeds backtest assumption by `+X%` threshold
- Any reconciliation error

## Status Definition
- PASS: all gates satisfied -> pilot allowed.
- WARNING: near-threshold / partial satisfaction -> ultra-small constrained pilot only.
- FAIL: one or more required gates not satisfied -> pilot not allowed.

## Practical Decision Rule
- Pre-pilot go/no-go uses Backtest + Regime + Stability + Operational gate bundle.
- During pilot, Stop Conditions override all other signals and trigger immediate halt.

## Current Decision Mapping (Task 050-2A Reference)
- Scenario 4: PASS band
- Scenario 5: WARNING band
- Scenario 6: WARNING band
- Decision: WARNING default posture -> ultra-small constrained pilot only.

