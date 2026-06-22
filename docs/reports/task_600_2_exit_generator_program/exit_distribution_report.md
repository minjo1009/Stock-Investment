# T600-2 Exit Distribution Report

## Problem

- No realized PnL distribution exists when all positions remain OPEN.

## Evidence

- TIMEOUT: count=23, avg_pnl=2.046622, median_pnl=0.32

## Root Cause

- Max hold generated TIMEOUT exits because ATR-based STOP/TAKE_PROFIT source was stale or unavailable for current entries.

## Fix Candidate

- Wire the exit generator to live paper execution only after PM approval; do not alter entry logic.

## Acceptance Impact

- Generated realized PnL populated rows=23.
- This proves exit logic can close positions diagnostically, not that broker-truth acceptance has passed.
