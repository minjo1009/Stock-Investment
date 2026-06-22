## Problem

- Runtime paper positions need exit fills and CLOSED lifecycle fields before acceptance review can inspect realized trades.

## Evidence

- runtime_paper_sell_fills=23
- closed_positions=23
- broker_api_called=False; real_capital_orders=0
- matching_policy=EXACT_POSITION_ID_AND_ENTRY_ORDER_FILL_ID_ONLY

## Root Cause

- T600-1 had BUY-only lifecycle rows, and T600-2 generated diagnostic exits without writing runtime paper SELL records.

## Fix Candidate

- Use STOP, TAKE_PROFIT, and TIMEOUT triggers to create paper/runtime SELL order, fill, and execution-event rows linked by exact lifecycle IDs.

## Acceptance Impact

- This creates controlled paper runtime evidence only.
- Strategy remains NOT_ACCEPTED and deployment remains DIAGNOSTIC_ONLY_NOT_DEPLOYMENT_READY.
