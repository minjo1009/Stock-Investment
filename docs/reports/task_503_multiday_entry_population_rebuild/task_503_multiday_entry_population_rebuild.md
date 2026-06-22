# Task 503 - Multi-Day Entry Population Rebuild

## Decision Summary

- Goal achieved: 0
- Entry candidates: 5041
- Count / avg net / win / entry_reduce: 5041 / 8.621% / 59.1% / 35.1%
- Median holding days / same-day exit: 85.56 / 0.0%
- Inferred lifecycle matching used: NO
- Label used in assignment: NO

## Quant Expert Report

This task rebuilds the entry population from raw daily and intraday bars. Multi-day market/theme state and symbol setup are computed before the intraday confirmation bar; outcomes are generated only by the later multi-day policy simulation.

## No-Background Decision-Maker Report

기존 후보를 재활용하지 않고, 좋은 시장/테마와 종목의 중기 구조가 맞을 때 intraday 확인까지 받은 새 후보군을 만들었다. 이 후보군이 며칠 이상 보유해도 목표 수익/승률/손실률을 만족하는지 확인한다.