# T601-2 Top Symbol Report

## Problem

- Filled candidates are concentrated in the top three symbols.

## Evidence

- AMD: generated=219, ranked=219, eligible=219, ordered=10, filled=10
- AMZN: generated=70, ranked=70, eligible=70, ordered=9, filled=9
- MSFT: generated=644, ranked=644, eligible=644, ordered=5, filled=5
- NVDA: generated=7, ranked=7, eligible=7, ordered=0, filled=0
- GOOGL: generated=1, ranked=1, eligible=1, ordered=0, filled=0

## Root Cause

- Generated and ordered candidate flow is already concentrated before fills occur.

## Fix Candidate

- Reserve cooldown, ranking, and portfolio selection changes for T601-3; do not implement them in T601-2.

## Acceptance Impact

- top3_share=1.0; concentration is explained but not fixed.
