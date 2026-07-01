# 1. Overview

## 1.1 Document Purpose

This document fixes a single, reproducible mapping contract between execution-layer data and backtest-layer models.
It is the Single Source of Truth for cross-layer data interpretation.

## 1.2 Scope

- In scope:
  - semantic mapping between execution/common data and backtest models
  - expected vs actual interpretation rules
  - PnL, slippage, holding-time definitions
  - status and edge-case interpretation
- Out of scope:
  - strategy logic changes
  - execution/backtest runtime implementation
  - UI implementation

## 1.3 Layers Using This Contract

- execution (`src/common/models.py` and persisted execution records)
- backtest (`src/backtest/models.py`)
- UI / analytics (read-only interpretation of unified `TradeResult` semantics)

# 2. Data Flow Mapping

Canonical lifecycle:

`Signal -> Intent -> Order -> Fill -> TradeResult`

## 2.1 Signal -> ExecutionIntent

Core mapping rules:

- `SignalEvent.reference_price -> ExecutionIntent.intended_price`
- `SignalEvent.symbol -> ExecutionIntent.symbol`
- `SignalEvent.side -> ExecutionIntent.side`
- `SignalEvent.strategy_id -> ExecutionIntent.strategy_id`
- `SignalEvent.signal_time -> ExecutionIntent.created_at` (or same-session creation timestamp)

Layer note:

- execution/common `SignalEvent.action` (`ENTER/EXIT/HOLD/SKIP`) maps to backtest `SignalEvent.signal_type` semantic group.
- `side="NONE"` in execution/common is non-tradable and must not produce an `ExecutionIntent`.

## 2.2 ExecutionIntent -> ExecutionResult

Core mapping rules:

- `ExecutionIntent.intended_price -> ExecutionResult.order_price`
- Broker/order outcome populates:
  - `ExecutionResult.fill_price`
  - `ExecutionResult.filled_quantity`
  - `ExecutionResult.status`

Interpretation:

- `order_price` is the intended submission price.
- `fill_price` is the realized execution price, nullable for unfilled orders.

## 2.3 ExecutionResult -> TradeResult

Entry-side contract:

```text
entry_price      = intended_price
entry_fill_price = fill_price
```

Exit-side contract:

- `exit_price` is strategy-intended exit price.
- `exit_fill_price` is realized exit fill price.

Population rule:

- `TradeResult` can exist before closure (open/unfilled lifecycle).
- `actual_pnl` remains `None` until both entry and exit fills needed for realized PnL are available.

# 3. Field Semantics Definition

## 3.1 Price Fields

- `entry_price`
  - strategy reference entry price (expected)
- `entry_fill_price`
  - actual filled entry price (nullable)
- `exit_price`
  - strategy reference exit price (expected)
- `exit_fill_price`
  - actual filled exit price (nullable)

## 3.2 PnL Definition

Expected PnL:

```text
expected_pnl = (expected_exit_price - entry_price) * quantity
```

Operational mapping:

- `expected_exit_price` is represented by `exit_price`.

Actual PnL:

```text
actual_pnl = (exit_fill_price - entry_fill_price) * quantity
```

Rules:

- If exit is not completed, `actual_pnl = None`.
- If either fill price required for realized PnL is missing, `actual_pnl = None`.

## 3.3 Slippage Definition

```text
slippage = entry_fill_price - entry_price
```

Interpretation:

- BUY:
  - `slippage > 0` is unfavorable
  - `slippage < 0` is favorable
- SELL:
  - `slippage < 0` is unfavorable
  - `slippage > 0` is favorable

If `entry_fill_price` is `None`, `slippage` is `None`.

## 3.4 Holding Time

```text
holding_time = exit_time - entry_time
```

Unit:

- canonical unit: `seconds` (float)
- UI may convert to minutes/hours/days for display only

## 3.5 Fill Semantics

```text
fill_price = None -> unfilled
```

Rules:

- Unfilled trades can still have a `TradeResult` record.
- For unfilled state, `actual_pnl = None`.

# 4. Status Mapping

Primary execution-to-trade status mapping:

- `SUBMITTED -> OPEN`
- `FILLED -> CLOSED` (entry or exit leg completion context applies)
- `CANCELLED -> CANCELLED`
- `FAILED -> FAILED`

Execution/common compatibility mapping:

- `NEW -> OPEN`
- `PARTIAL_FILLED -> OPEN` (partial state remains open)
- `REJECTED -> FAILED`

Rule:

- Unknown/unmapped broker state must not be guessed. Keep as layer-local raw status and map conservatively.

# 5. Edge Case Handling

## 5.1 Unfilled

- `TradeResult` creation is allowed.
- `entry_fill_price` or `exit_fill_price` may be `None`.
- `actual_pnl = None` until required fills exist.

## 5.2 Partial Fill

Initial simplification policy:

- treat using `filled_quantity` basis
- do not introduce advanced multi-fill aggregation semantics in this phase
- if partially filled and still open, trade remains `OPEN`

## 5.3 Gap

- `intended_price != fill_price` is valid and expected in live execution.
- This difference is represented through `slippage` under the formula in Section 3.3.

# 6. UI Requirements (Frontend Binding)

Required fields for trade-detail visualization:

- `entry_time`
- `entry_price`
- `entry_fill_price`
- `exit_time`
- `exit_price`
- `exit_fill_price`
- `breakout_level`
- `stop_price`
- `expected_pnl`
- `actual_pnl`
- `reason`

Binding note:

- `breakout_level`, `stop_price`, `reason` originate from signal-layer metadata and must be preserved through mapping context.

# 7. Invariants

Mandatory invariants:

```text
entry_fill_price != None -> corresponding order record must exist
actual_pnl is not None -> exit_fill_price is not None
holding_time >= 0
```

Additional invariants:

- `quantity >= 0`
- `slippage is not None -> entry_fill_price is not None`

# 8. Non-Goals

- This is not a strategy definition document.
- This is not an execution implementation document.
- This is not a backtest implementation document.
- This does not define UI layout/components.
