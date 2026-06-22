# T600-2 Lifecycle Test Matrix

## Problem

- Current broker-truth lifecycle has 24 BUY fills, 0 SELL fills, and 24 OPEN positions.

## Evidence

- STOP 발생 수: 0
- TP 발생 수: 0
- TIMEOUT 발생 수: 23
- OPEN 잔존 수: 1

## Root Cause

- Exit rules were not generating lifecycle-closing SELL events before T600-2.

## Fix Candidate

- Use hard stop, take profit, and max hold as an exit-only generator; keep entry strategy unchanged.

## Acceptance Impact

- Diagnostic generated SELL fills=23.
- Strategy acceptance remains NOT_ACCEPTED until broker-truth SELL fills exist.
